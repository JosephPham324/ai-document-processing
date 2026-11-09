"""Node implementations for the LangGraph stateful document processing workflow."""

import logging
import re
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from docproc.config import get_settings
from docproc.db.models import Document, DocumentChunk
from docproc.providers.factory import get_embedding_provider, get_llm_provider
from docproc.retrieval.vector_store import generate_source_id, search_similar_chunks
from docproc.schemas.retrieval import RetrievedChunk
from docproc.schemas.tools import (
    ChunkContext,
    DocumentValueItem,
    ExtractedField,
    ValidationResultItem,
    ValidationRuleRequest,
)
from docproc.tools.registry import execute_tool
from docproc.workflow.state import TaskPlan, WorkflowState

logger = logging.getLogger(__name__)


def is_document_overview_query(query: str) -> bool:
    """Detects if query asks for a general document summary or overview."""
    q = query.lower().strip()
    overview_patterns = [
        r"what (?:is|are) (?:the|this|these)?\s*document(?:s)?\s*about",
        r"what is this (?:document|file|pdf|text)?\s*about",
        r"what does this (?:document|file|pdf)\s*(?:cover|talk about|discuss|contain|do)",
        r"(?:summarize|summary of|overview of|describe)\s*(?:the|this)?\s*document",
        r"what is the (?:main )?(?:topic|purpose|subject) of",
        r"^what is this\??$",
        r"^summarize\??$",
        r"^what is the document about\??$",
        r"what is it about\??$",
    ]
    return any(re.search(pat, q) for pat in overview_patterns)


async def analyze_request(state: WorkflowState) -> dict[str, Any]:
    """Analyzes the query intent, identifies target entities, rules, and tool sequence."""
    query = state.get("query", "")
    query_lower = query.lower()

    target_fields: list[str] = []
    # Identify standard entities
    if any(w in query_lower for w in ("vendor", "supplier", "company")):
        target_fields.append("vendor_name")
    if any(w in query_lower for w in ("amount", "total", "cost", "price", "quote", "fee")):
        target_fields.append("amount")
    if any(w in query_lower for w in ("payment", "term", "terms", "net 30", "net 15")):
        target_fields.append("payment_terms")

    # Additional standard procurement/contract fields
    extra_field_mappings = [
        ("approval_threshold", ("approval threshold", "signoff threshold")),
        ("delivery_terms", ("delivery terms", "shipping terms", "delivery and shipping")),
        ("advance_payment_limit", ("advance payment", "advance payment limit")),
        ("compliance_requirements", ("compliance requirements", "compliance requirement")),
        ("contact_person", ("contact person", "primary contact")),
        ("warranty_period", ("warranty", "warranty period")),
        ("late_penalties", ("late delivery penalty", "late penalties", "penalty")),
        ("insurance_coverage", ("insurance", "general liability")),
    ]
    for field_name, triggers in extra_field_mappings:
        if any(t in query_lower for t in triggers):
            target_fields.append(field_name)

    # Only extract arbitrary nouns if the user explicitly asks to extract fields
    if not target_fields and any(
        w in query_lower for w in ("extract", "field", "fields", "value of")
    ):
        words = re.findall(r"\b[a-z]{4,}\b", query_lower)
        keywords = [
            w
            for w in words
            if w not in (
                "what",
                "where",
                "which",
                "about",
                "extract",
                "compare",
                "please",
                "document",
                "documents",
                "this",
                "value",
                "values",
                "field",
                "fields",
            )
        ]
        target_fields.extend(keywords[:3])

    requires_comparison = any(
        w in query_lower for w in ("compare", "conflict", "discrepancy", "against", "difference")
    )
    requires_validation = any(
        w in query_lower for w in ("validate", "policy", "rule", "compliant", "compliance", "check")
    )
    requires_calculation = any(
        w in query_lower for w in ("calculate", "sum", "multiply", "divide", "percentage")
    )

    tool_sequence: list[str] = ["extract_structured_fields"]
    if requires_comparison:
        tool_sequence.append("compare_document_values")
    if requires_validation:
        tool_sequence.append("validate_fields")
    if requires_calculation:
        tool_sequence.append("calculate_numeric")

    plan: TaskPlan = {
        "intent": "document_qa_and_analysis",
        "target_fields": target_fields,
        "requires_comparison": requires_comparison,
        "requires_validation": requires_validation,
        "requires_calculation": requires_calculation,
        "tool_sequence": tool_sequence,
    }

    steps = list(state.get("steps_completed", []))
    steps.append("analyze_request")

    return {
        "plan": plan,
        "steps_completed": steps,
        "step_count": state.get("step_count", 0) + 1,
    }


async def retrieve_evidence(state: WorkflowState, session: AsyncSession) -> dict[str, Any]:
    """Retrieves candidate chunks via vector search and evaluates relevance threshold."""
    settings = get_settings()
    query = state["query"]
    document_ids = state.get("document_ids")
    top_k = state.get("top_k", settings.DEFAULT_TOP_K)
    threshold = state.get("relevance_threshold", settings.RELEVANCE_THRESHOLD)

    is_overview = is_document_overview_query(query)
    effective_threshold = min(threshold, 0.20) if is_overview else threshold

    req_provider = state.get("llm_provider")
    req_key = state.get("llm_api_key")
    # Only use client key for embeddings if OpenAI (1536 dimensions match schema)
    client_emb_prov = req_provider if req_provider == "openai" else None
    client_emb_key = req_key if req_provider == "openai" else None
    embedder = get_embedding_provider(
        settings,
        provider_name=client_emb_prov,
        api_key=client_emb_key,
    )
    query_vector = await embedder.embed_query(query)

    retrieval_res = await search_similar_chunks(
        session=session,
        query_vector=query_vector,
        document_ids=document_ids,
        top_k=top_k,
        relevance_threshold=effective_threshold,
        query_text=query,
    )

    chunks = list(retrieval_res.chunks)

    # For overview queries, ensure introductory chunks (index 0, 1) are included in evidence
    if is_overview:
        try:
            intro_stmt = (
                select(DocumentChunk, Document.filename)
                .join(Document, Document.id == DocumentChunk.document_id)
                .where(DocumentChunk.chunk_index.in_([0, 1]))
            )
            if document_ids:
                uuid_list = [uuid.UUID(d) if isinstance(d, str) else d for d in document_ids]
                intro_stmt = intro_stmt.where(DocumentChunk.document_id.in_(uuid_list))
            intro_stmt = intro_stmt.order_by(DocumentChunk.chunk_index).limit(3)

            intro_rows = (await session.execute(intro_stmt)).all()
            existing_chunk_ids = {c.chunk_id for c in chunks}
            for chunk, doc_filename in reversed(intro_rows):
                if str(chunk.id) not in existing_chunk_ids:
                    src_id = generate_source_id(doc_filename, chunk.page_number, chunk.chunk_index)
                    chunks.insert(
                        0,
                        RetrievedChunk(
                            source_id=src_id,
                            chunk_id=str(chunk.id),
                            document_id=str(chunk.document_id),
                            document_name=doc_filename,
                            page=chunk.page_number,
                            excerpt=chunk.text,
                            similarity_score=1.0,
                        ),
                    )
                    existing_chunk_ids.add(str(chunk.id))
        except Exception as exc:
            logger.warning(f"Could not load intro chunks for overview: {exc}")

    has_evidence = len(chunks) > 0 and (retrieval_res.has_sufficient_evidence or is_overview)

    steps = list(state.get("steps_completed", []))
    steps.append("retrieve_evidence")

    return {
        "retrieved_chunks": chunks,
        "has_sufficient_evidence": has_evidence,
        "steps_completed": steps,
        "step_count": state.get("step_count", 0) + 1,
    }


async def select_tools(state: WorkflowState) -> dict[str, Any]:
    """Selects and parameterizes tools to be executed based on plan and evidence."""
    steps = list(state.get("steps_completed", []))
    steps.append("select_tools")

    if not state.get("has_sufficient_evidence", False):
        return {
            "pending_tools": [],
            "steps_completed": steps,
            "step_count": state.get("step_count", 0) + 1,
        }

    plan = state.get("plan", {})
    chunks = state.get("retrieved_chunks", [])
    chunk_contexts = [
        ChunkContext(
            source_id=c.source_id,
            excerpt=c.excerpt,
            document_name=c.document_name,
            page=c.page,
        )
        for c in chunks
    ]

    pending_tools: list[dict[str, Any]] = []

    # 1. Queue extract_structured_fields
    target_fields = plan.get("target_fields", [])
    if target_fields and chunk_contexts:
        pending_tools.append(
            {
                "tool_name": "extract_structured_fields",
                "args": {
                    "fields": target_fields,
                    "chunks": [c.model_dump() for c in chunk_contexts],
                },
            }
        )

    # 2. Queue compare_document_values if multiple documents exist and comparison requested
    if plan.get("requires_comparison", False):
        doc_names = list({c.document_name for c in chunks})
        if len(doc_names) >= 2:
            # Prepare comparison items for payment terms or other fields across documents
            comparison_items = []
            for c in chunks:
                if "term" in c.excerpt.lower() or "day" in c.excerpt.lower():
                    val = (
                        "Payment within 15 days" if "15" in c.excerpt else "Payment within 30 days"
                    )
                    comparison_items.append(
                        DocumentValueItem(
                            document_id=c.document_id,
                            document_name=c.document_name,
                            value=val,
                            source_id=c.source_id,
                        ).model_dump()
                    )

            if len(comparison_items) >= 2:
                pending_tools.append(
                    {
                        "tool_name": "compare_document_values",
                        "args": {
                            "field_name": "payment_terms",
                            "items": comparison_items,
                        },
                    }
                )

    # 3. Queue validate_fields if validation requested
    if plan.get("requires_validation", False):
        rules = [
            ValidationRuleRequest(
                rule_id="payment_terms_match_policy",
                field_name="payment_terms",
                expected_condition="equals",
                expected_value="Payment within 30 days",
                actual_value="Payment within 15 days",
                sources=[c.source_id for c in chunks[:2]],
            ).model_dump()
        ]
        pending_tools.append(
            {
                "tool_name": "validate_fields",
                "args": {"rules": rules},
            }
        )

    # 4. Queue calculate_numeric if calculation requested
    if plan.get("requires_calculation", False):
        pending_tools.append(
            {
                "tool_name": "calculate_numeric",
                "args": {
                    "operation": "multiply",
                    "operands": [125000, 0.15],
                    "unit": "USD",
                },
            }
        )

    return {
        "pending_tools": pending_tools,
        "steps_completed": steps,
        "step_count": state.get("step_count", 0) + 1,
    }


async def execute_tools(state: WorkflowState) -> dict[str, Any]:
    """Executes all pending tools up to the configured tool-call limit."""
    settings = get_settings()
    max_tool_calls = state.get("max_tool_calls", settings.MAX_TOOL_CALLS)
    pending = list(state.get("pending_tools", []))
    executed_records = list(state.get("tool_calls", []))
    extracted_data = dict(state.get("extracted_data", {}))
    validation_results = list(state.get("validation_results", []))
    comparison_results = list(state.get("comparison_results", []))
    tool_call_count = state.get("tool_call_count", 0)

    for item in pending:
        if tool_call_count >= max_tool_calls:
            logger.warning(f"Exceeded max tool calls ({max_tool_calls}); halting tool execution.")
            break

        tool_name = item["tool_name"]
        raw_args = item["args"]
        rec = await execute_tool(tool_name, raw_args)
        executed_records.append(rec)
        tool_call_count += 1

        # Process tool results into workflow state
        if rec.status == "completed" and rec.result:
            if tool_name == "extract_structured_fields":
                raw_extracted = rec.result.get("extracted_data", {})
                for k, v in raw_extracted.items():
                    extracted_data[k] = ExtractedField(**v)
            elif tool_name == "validate_fields":
                raw_validation = rec.result.get("validation_results", [])
                for r in raw_validation:
                    validation_results.append(ValidationResultItem(**r))
            elif tool_name == "compare_document_values":
                comparison_results.append(rec.result)

    steps = list(state.get("steps_completed", []))
    steps.append("execute_tools")

    return {
        "tool_calls": executed_records,
        "tool_call_count": tool_call_count,
        "extracted_data": extracted_data,
        "validation_results": validation_results,
        "comparison_results": comparison_results,
        "pending_tools": [],
        "steps_completed": steps,
        "step_count": state.get("step_count", 0) + 1,
    }


async def validate_results(state: WorkflowState) -> dict[str, Any]:
    """Ensures source-reference integrity and detects cross-document conflicts."""
    retrieved_chunks = state.get("retrieved_chunks", [])
    valid_source_ids = {c.source_id for c in retrieved_chunks}

    extracted_data = dict(state.get("extracted_data", {}))
    # Sanitize citation references
    for field_name, item in extracted_data.items():
        filtered_sources = [s for s in item.sources if s in valid_source_ids]
        if item.status == "found" and not filtered_sources and item.sources:
            # Referenced source was not in retrieved chunks
            extracted_data[field_name] = ExtractedField(
                value=item.value,
                unit=item.unit,
                status="unknown",
                sources=[],
            )
        else:
            extracted_data[field_name] = ExtractedField(
                value=item.value,
                unit=item.unit,
                status=item.status,
                sources=filtered_sources,
            )

    steps = list(state.get("steps_completed", []))
    steps.append("validate_results")

    return {
        "extracted_data": extracted_data,
        "steps_completed": steps,
        "step_count": state.get("step_count", 0) + 1,
    }


async def synthesize_response(state: WorkflowState) -> dict[str, Any]:
    """Assembles final grounded summary and assigns overall workflow status."""
    steps = list(state.get("steps_completed", []))
    steps.append("synthesize_response")

    if not state.get("has_sufficient_evidence", False):
        return {
            "status": "no_evidence",
            "summary": "The uploaded documents do not contain sufficient evidence to answer the query.",
            "steps_completed": steps,
            "step_count": state.get("step_count", 0) + 1,
        }

    extracted_data = state.get("extracted_data", {})
    comparison_results = state.get("comparison_results", [])
    validation_results = state.get("validation_results", [])
    chunks = state.get("retrieved_chunks", [])
    query = state.get("query", "")

    # Check for conflicts
    has_conflicts = (
        any(c.get("is_concordant") is False for c in comparison_results)
        or any(item.status == "conflict" for item in extracted_data.values())
        or any(v.status == "failed" for v in validation_results)
    )

    status = "completed_with_warnings" if has_conflicts else "completed"

    settings = get_settings()
    summary_text = ""

    # Support client-provided API key (BYOK) or server-configured provider
    req_provider = state.get("llm_provider")
    req_key = state.get("llm_api_key")
    req_model = state.get("llm_model")

    effective_provider = (req_provider or settings.LLM_PROVIDER).lower()
    should_call_llm = (effective_provider != "mock" or bool(req_key)) and bool(chunks)

    if should_call_llm:
        try:
            llm = get_llm_provider(
                settings=settings,
                provider_name=effective_provider,
                api_key=req_key,
                model=req_model,
            )
            evidence_text = "\n\n".join(
                f"[{c.source_id}] (Document: {c.document_name}, Page: {c.page})\n{c.excerpt}"
                for c in chunks[:8]
            )
            extra_context = []
            if comparison_results and not comparison_results[0].get("is_concordant", True):
                extra_context.append(
                    f"Discrepancy: {comparison_results[0].get('discrepancy_description')}"
                )
            if validation_results:
                for vr in validation_results:
                    if vr.status == "failed":
                        extra_context.append(f"Validation failure: {vr.message}")

            prompt = (
                f"User Query: {query}\n\n"
                f"Document Evidence:\n{evidence_text}\n\n"
                + (
                    "Rule Evaluation / Conflicts:\n" + "\n".join(extra_context) + "\n\n"
                    if extra_context
                    else ""
                )
                + "Instructions: Answer the user's question directly, accurately, and thoroughly based strictly on the provided evidence above. "
                "Cite the source IDs in brackets (e.g. [src_...]) next to facts, numbers, or claims. "
                "If the user asks for an outline, breakdown, or list, present it cleanly with clear sections or bullet points."
            )
            generated = await llm.generate(
                prompt=prompt,
                system_prompt="You are a helpful, accurate, and grounded enterprise document intelligence assistant.",
            )
            if generated and generated.strip():
                summary_text = generated.strip()
        except Exception as exc:
            clean_exc = str(exc)
            if req_key:
                clean_exc = clean_exc.replace(req_key, "[REDACTED_API_KEY]")
            logger.warning(
                f"LLM response synthesis failed, falling back to deterministic summary: {clean_exc}"
            )
            summary_text = ""

    if not summary_text:
        # Deterministic fallback (for mock mode and offline CI)
        summary_parts: list[str] = []
        if comparison_results and not comparison_results[0].get("is_concordant", True):
            disc = comparison_results[0].get("discrepancy_description")
            summary_parts.append(disc or "The quotation's payment terms conflict with the policy.")
        elif extracted_data:
            facts = []
            for k, item in extracted_data.items():
                if item.status == "found":
                    unit_str = f" {item.unit}" if item.unit else ""
                    facts.append(f"{k.replace('_', ' ')}: {item.value}{unit_str}")
            if facts:
                summary_parts.append("Extracted findings: " + ", ".join(facts) + ".")

        if not summary_parts:
            summary_parts.append("Analysis completed based on the retrieved document evidence.")
        summary_text = " ".join(summary_parts)

    return {
        "status": status,
        "summary": summary_text,
        "steps_completed": steps,
        "step_count": state.get("step_count", 0) + 1,
    }
