"""Pydantic schemas and typed contracts for allowlisted agent tools."""

from typing import Any, Literal

from pydantic import BaseModel, Field

# ---------------------------------------------------------
# Common Field & Validation Output Schemas (Match API query response)
# ---------------------------------------------------------


class ExtractedField(BaseModel):
    """Extracted factual field with provenance and status."""

    value: Any = Field(..., description="Extracted scalar value, entity, or description")
    unit: str | None = Field(None, description="Optional unit, e.g. USD, days, %")
    status: Literal["found", "not_found", "unknown", "conflict"] = Field(
        ..., description="Extraction outcome status"
    )
    sources: list[str] = Field(
        default_factory=list,
        description="List of source citation IDs supporting this extraction",
    )


class ValidationResultItem(BaseModel):
    """Validation rule result with cited sources."""

    rule_id: str = Field(..., description="Unique rule identifier")
    status: Literal["passed", "failed", "unknown", "not_applicable"] = Field(
        ..., description="Validation outcome status"
    )
    message: str = Field(..., description="Human-readable explanation of validation outcome")
    sources: list[str] = Field(
        default_factory=list,
        description="Source citation IDs referenced in rule verification",
    )


# ---------------------------------------------------------
# Tool 1: extract_structured_fields
# ---------------------------------------------------------


class ChunkContext(BaseModel):
    """Chunk excerpt supplied as evidence to extraction tool."""

    source_id: str
    excerpt: str
    document_name: str | None = None
    page: int | None = None


class ExtractStructuredFieldsInput(BaseModel):
    """Input parameters for extract_structured_fields."""

    fields: list[str] = Field(..., min_length=1, description="Field names to extract")
    chunks: list[ChunkContext] = Field(..., min_length=1, description="Evidence chunks to inspect")
    field_hints: dict[str, str] | None = Field(
        None, description="Optional hints for what to search for in each field"
    )


class ExtractStructuredFieldsOutput(BaseModel):
    """Output contract for extract_structured_fields."""

    extracted_data: dict[str, ExtractedField] = Field(default_factory=dict)
    status: Literal["completed", "failed", "partial"] = "completed"
    error: str | None = None


# ---------------------------------------------------------
# Tool 2: validate_fields
# ---------------------------------------------------------


class ValidationRuleRequest(BaseModel):
    """Specification of a rule to validate."""

    rule_id: str
    field_name: str
    expected_condition: Literal[
        "equals", "not_equals", "must_not_exceed", "must_at_least", "contains", "in_set"
    ] = Field(..., description="Logical assertion type")
    expected_value: Any
    actual_value: Any
    sources: list[str] = Field(default_factory=list)


class ValidateFieldsInput(BaseModel):
    """Input parameters for validate_fields."""

    rules: list[ValidationRuleRequest] = Field(
        ..., min_length=1, description="List of rules to verify"
    )


class ValidateFieldsOutput(BaseModel):
    """Output contract for validate_fields."""

    validation_results: list[ValidationResultItem] = Field(default_factory=list)
    status: Literal["completed", "failed"] = "completed"
    error: str | None = None


# ---------------------------------------------------------
# Tool 3: compare_document_values
# ---------------------------------------------------------


class DocumentValueItem(BaseModel):
    """A value extracted from a specific document for cross-document comparison."""

    document_id: str
    document_name: str
    value: Any
    source_id: str


class CompareDocumentValuesInput(BaseModel):
    """Input parameters for compare_document_values."""

    field_name: str = Field(..., description="Name of the property being compared")
    items: list[DocumentValueItem] = Field(
        ..., min_length=2, description="Values from at least 2 documents to compare"
    )


class CompareDocumentValuesOutput(BaseModel):
    """Output contract for compare_document_values."""

    field_name: str
    is_concordant: bool = Field(
        ..., description="True if values match or are compliant, False if conflicting"
    )
    discrepancy_description: str | None = None
    conflicting_sources: list[str] = Field(default_factory=list)
    all_sources: list[str] = Field(default_factory=list)
    status: Literal["completed", "failed"] = "completed"
    error: str | None = None


# ---------------------------------------------------------
# Tool 4: calculate_numeric
# ---------------------------------------------------------


class CalculateNumericInput(BaseModel):
    """Input parameters for calculate_numeric (deterministic math)."""

    operation: Literal[
        "add",
        "subtract",
        "multiply",
        "divide",
        "sum",
        "difference",
        "percentage_difference",
        "percentage_of",
    ] = Field(..., description="Deterministic arithmetic operation")
    operands: list[float] = Field(..., min_length=1, description="Numbers to operate on")
    unit: str | None = Field(None, description="Optional unit e.g. USD, %")


class CalculateNumericOutput(BaseModel):
    """Output contract for calculate_numeric."""

    result: float | None = None
    unit: str | None = None
    formula_expressed: str = Field(
        ..., description="Readable representation of formula, e.g. 100 + 25 = 125"
    )
    status: Literal["completed", "failed"] = "completed"
    error: str | None = None


# ---------------------------------------------------------
# Registry & Execution Tracking
# ---------------------------------------------------------


class ToolExecutionRecord(BaseModel):
    """Audit record of a tool call in the workflow."""

    tool_name: str
    status: Literal["completed", "failed"]
    duration_ms: int
    error: str | None = None
    result: dict[str, Any] | None = None
