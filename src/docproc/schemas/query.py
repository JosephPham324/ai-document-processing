"""Pydantic schemas for the Query endpoint."""

from typing import Any, Literal

from pydantic import BaseModel, Field

from docproc.schemas.retrieval import RetrievedChunk
from docproc.schemas.tools import ExtractedField, ToolExecutionRecord, ValidationResultItem


class QueryRequest(BaseModel):
    """User query request payload."""

    query: str = Field(
        ...,
        min_length=1,
        max_length=4000,
        description="User question or instruction regarding uploaded documents.",
    )
    document_ids: list[str] | None = Field(
        None,
        description="Optional list of document IDs to restrict retrieval scope.",
    )
    top_k: int = Field(
        5,
        ge=1,
        le=20,
        description="Maximum number of relevant chunks to retrieve (1-20).",
    )
    relevance_threshold: float | None = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Optional similarity cutoff threshold (0.0 to 1.0, defaults to server config).",
    )
    llm_provider: Literal["mock", "openai", "gemini"] | None = Field(
        None,
        description="Optional client-selected LLM provider (BYOK mode).",
    )
    api_key: str | None = Field(
        None,
        description="Optional client-provided ephemeral API key (never stored).",
    )
    model: str | None = Field(
        None,
        description="Optional specific model override (e.g. gpt-4o-mini, gemini-1.5-flash).",
    )


class WorkflowTrace(BaseModel):
    """Audit trace of workflow execution."""

    steps_completed: list[str] = Field(
        default_factory=list,
        description="Ordered list of executed workflow stages",
    )
    tool_calls: list[ToolExecutionRecord] = Field(
        default_factory=list,
        description="Records of all allowlisted tool executions",
    )
    duration_ms: int = Field(..., description="Total workflow execution time in milliseconds")


class QueryResponse(BaseModel):
    """Grounded, citation-backed query response conforming to API contract."""

    request_id: str = Field(..., description="Unique request identifier")
    status: Literal["completed", "completed_with_warnings", "no_evidence", "failed"] = Field(
        ..., description="Overall workflow completion status"
    )
    summary: str = Field(..., description="Grounded natural language summary of findings")
    extracted_data: dict[str, ExtractedField] = Field(
        default_factory=dict,
        description="Extracted key-value entities with provenance sources",
    )
    validation_results: list[ValidationResultItem] = Field(
        default_factory=list,
        description="Outcomes of evaluated business rules and policies",
    )
    sources: list[RetrievedChunk] = Field(
        default_factory=list,
        description="Retrieved document chunks providing evidence for the response",
    )
    workflow: WorkflowTrace
    error: dict[str, Any] | None = Field(
        None,
        description="Structured error details if query failed",
    )
