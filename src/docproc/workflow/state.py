"""Typed state definition for the LangGraph stateful document agent workflow."""

from typing import Any, Literal, TypedDict

from docproc.schemas.retrieval import RetrievedChunk
from docproc.schemas.tools import ExtractedField, ToolExecutionRecord, ValidationResultItem


class TaskPlan(TypedDict, total=False):
    """Structured plan generated during analyze_request."""

    intent: str
    target_fields: list[str]
    requires_comparison: bool
    requires_validation: bool
    requires_calculation: bool
    tool_sequence: list[str]


class WorkflowState(TypedDict, total=False):
    """Complete workflow state passed across LangGraph nodes."""

    request_id: str
    query: str
    document_ids: list[str] | None
    top_k: int
    relevance_threshold: float

    # Execution plan & evidence
    plan: TaskPlan
    retrieved_chunks: list[RetrievedChunk]
    has_sufficient_evidence: bool

    # Extracted & validated state
    extracted_data: dict[str, ExtractedField]
    validation_results: list[ValidationResultItem]
    comparison_results: list[dict[str, Any]]
    calculation_results: list[dict[str, Any]]

    # Tool queue and audit records
    pending_tools: list[dict[str, Any]]
    tool_calls: list[ToolExecutionRecord]

    # Guardrails and observability
    steps_completed: list[str]
    step_count: int
    tool_call_count: int
    max_steps: int
    max_tool_calls: int

    # Final outputs
    status: Literal["completed", "completed_with_warnings", "no_evidence", "failed"]
    summary: str
    error: dict[str, Any] | None
    start_time: float
