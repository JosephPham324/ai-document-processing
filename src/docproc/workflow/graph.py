"""LangGraph StateGraph builder and workflow execution runner."""

import logging
import time
from typing import Any

from langgraph.graph import END, START, StateGraph
from sqlalchemy.ext.asyncio import AsyncSession

from docproc.config import get_settings
from docproc.schemas.query import QueryResponse, WorkflowTrace
from docproc.workflow.nodes import (
    analyze_request,
    execute_tools,
    retrieve_evidence,
    select_tools,
    synthesize_response,
    validate_results,
)
from docproc.workflow.state import WorkflowState

logger = logging.getLogger(__name__)


def should_continue_after_retrieval(state: WorkflowState) -> str:
    """Conditional router: skips tool execution if no evidence met relevance threshold."""
    if not state.get("has_sufficient_evidence", False):
        return "synthesize_response"
    return "select_tools"


def build_workflow_graph(session: AsyncSession) -> Any:
    """Constructs and compiles the stateful LangGraph execution graph."""
    graph = StateGraph(WorkflowState)

    # Wrap retrieve_evidence with session dependency
    async def _retrieve_evidence_node(state: WorkflowState) -> dict[str, Any]:
        return await retrieve_evidence(state, session)

    # Add workflow nodes
    graph.add_node("analyze_request", analyze_request)
    graph.add_node("retrieve_evidence", _retrieve_evidence_node)
    graph.add_node("select_tools", select_tools)
    graph.add_node("execute_tools", execute_tools)
    graph.add_node("validate_results", validate_results)
    graph.add_node("synthesize_response", synthesize_response)

    # Add edges
    graph.add_edge(START, "analyze_request")
    graph.add_edge("analyze_request", "retrieve_evidence")

    # Conditional branching on evidence presence
    graph.add_conditional_edges(
        "retrieve_evidence",
        should_continue_after_retrieval,
        {
            "select_tools": "select_tools",
            "synthesize_response": "synthesize_response",
        },
    )

    graph.add_edge("select_tools", "execute_tools")
    graph.add_edge("execute_tools", "validate_results")
    graph.add_edge("validate_results", "synthesize_response")
    graph.add_edge("synthesize_response", END)

    return graph.compile()


async def execute_query_workflow(
    query: str,
    document_ids: list[str] | None,
    top_k: int,
    session: AsyncSession,
    request_id: str,
    relevance_threshold: float | None = None,
    llm_provider: str | None = None,
    llm_api_key: str | None = None,
    llm_model: str | None = None,
) -> QueryResponse:
    """Executes end-to-end document processing workflow and returns validated QueryResponse."""
    settings = get_settings()
    start_time = time.perf_counter()
    effective_thresh = (
        relevance_threshold if relevance_threshold is not None else settings.RELEVANCE_THRESHOLD
    )

    initial_state: WorkflowState = {
        "request_id": request_id,
        "query": query,
        "document_ids": document_ids,
        "top_k": top_k,
        "relevance_threshold": effective_thresh,
        "llm_provider": llm_provider,
        "llm_api_key": llm_api_key,
        "llm_model": llm_model,
        "retrieved_chunks": [],
        "has_sufficient_evidence": False,
        "extracted_data": {},
        "validation_results": [],
        "comparison_results": [],
        "calculation_results": [],
        "pending_tools": [],
        "tool_calls": [],
        "steps_completed": [],
        "step_count": 0,
        "tool_call_count": 0,
        "max_steps": settings.MAX_WORKFLOW_STEPS,
        "max_tool_calls": settings.MAX_TOOL_CALLS,
        "status": "completed",
        "summary": "",
        "error": None,
        "start_time": start_time,
    }

    compiled_graph = build_workflow_graph(session)
    final_state = await compiled_graph.ainvoke(initial_state)

    elapsed_ms = int((time.perf_counter() - start_time) * 1000)

    # Filter sources to only chunks retrieved during this request
    sources = list(final_state.get("retrieved_chunks", []))
    valid_source_ids = {s.source_id for s in sources}

    # Ensure all extracted_data and validation_results cite valid sources
    extracted_data = dict(final_state.get("extracted_data", {}))
    for v in extracted_data.values():
        v.sources = [s for s in v.sources if s in valid_source_ids]

    validation_results = list(final_state.get("validation_results", []))
    for r in validation_results:
        r.sources = [s for s in r.sources if s in valid_source_ids]

    workflow_trace = WorkflowTrace(
        steps_completed=final_state.get("steps_completed", []),
        tool_calls=final_state.get("tool_calls", []),
        duration_ms=elapsed_ms,
    )

    return QueryResponse(
        request_id=request_id,
        status=final_state.get("status", "completed"),
        summary=final_state.get("summary", ""),
        extracted_data=extracted_data,
        validation_results=validation_results,
        sources=sources,
        workflow=workflow_trace,
        error=final_state.get("error"),
    )
