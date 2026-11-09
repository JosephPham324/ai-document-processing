"""Query API router orchestrating RAG and LangGraph workflow."""

import logging
import uuid

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from docproc.api.error_handlers import DocumentNotFoundException, get_request_id
from docproc.db.models import Document
from docproc.db.session import get_db
from docproc.schemas.query import QueryRequest, QueryResponse
from docproc.workflow.graph import execute_query_workflow

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/query", tags=["Query & Analysis"])


@router.post(
    "",
    response_model=QueryResponse,
    status_code=status.HTTP_200_OK,
    summary="Query documents with RAG and LangGraph agent workflow",
    description=(
        "Retrieves relevant document chunks, executes allowlisted extraction, validation, "
        "and comparison tools through a stateful LangGraph workflow, and returns grounded answers with source references."
    ),
)
async def query_documents(
    payload: QueryRequest,
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> QueryResponse:
    req_id = get_request_id(request)

    # Validate document_ids if provided
    if payload.document_ids:
        for doc_id_str in payload.document_ids:
            try:
                doc_uuid = uuid.UUID(doc_id_str)
            except ValueError:
                raise DocumentNotFoundException(doc_id_str) from None

            stmt = select(Document.id).where(Document.id == doc_uuid)
            res = await session.execute(stmt)
            if not res.scalar_one_or_none():
                raise DocumentNotFoundException(doc_id_str)

    # Extract client credentials from headers or request payload (headers take precedence)
    client_provider = request.headers.get("X-LLM-Provider") or payload.llm_provider
    client_api_key = (
        request.headers.get("X-OpenAI-API-Key")
        or request.headers.get("X-Gemini-API-Key")
        or request.headers.get("X-API-Key")
        or payload.api_key
    )
    client_model = request.headers.get("X-LLM-Model") or payload.model

    # Auto-detect provider if key prefix is evident and provider wasn't explicitly supplied
    if client_api_key and not client_provider:
        if client_api_key.startswith("sk-"):
            client_provider = "openai"
        elif client_api_key.startswith("AIza"):
            client_provider = "gemini"

    # Run orchestrated workflow
    response = await execute_query_workflow(
        query=payload.query,
        document_ids=payload.document_ids,
        top_k=payload.top_k,
        session=session,
        request_id=req_id,
        relevance_threshold=payload.relevance_threshold,
        llm_provider=client_provider,
        llm_api_key=client_api_key,
        llm_model=client_model,
    )
    return response
