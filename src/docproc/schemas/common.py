"""Common API schemas and standard error contracts."""

from typing import Any

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """Detailed error object conforming to API specification."""

    code: str = Field(..., description="Stable machine-readable error code")
    message: str = Field(..., description="Concise human-readable explanation")
    details: dict[str, Any] = Field(
        default_factory=dict, description="Additional context, safe for client"
    )
    request_id: str = Field(..., description="Unique request identifier")


class ErrorResponse(BaseModel):
    """Unified error envelope for all 4xx and 5xx responses."""

    error: ErrorDetail


class HealthResponse(BaseModel):
    """Health endpoint response."""

    status: str = Field(default="ok")


class ReadyResponse(BaseModel):
    """Readiness endpoint response."""

    status: str = Field(..., description="'ready' or 'not_ready'")
    dependencies: dict[str, str] = Field(
        ...,
        description="Health status of external dependencies e.g. database, embedding_provider",
    )
