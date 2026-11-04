"""Pydantic schemas for Document Ingestion API."""

from datetime import datetime

from pydantic import BaseModel, Field


class DocumentResponse(BaseModel):
    """Document ingestion and retrieval response model."""

    document_id: str = Field(..., description="Unique document ID (UUID string)")
    filename: str = Field(..., description="Original filename of uploaded document")
    content_type: str = Field(..., description="MIME content type")
    status: str = Field(..., description="Ingestion status: processing, completed, or failed")
    page_count: int | None = Field(None, description="Total number of pages (for PDF)")
    chunk_count: int | None = Field(None, description="Number of text chunks created")
    created_at: datetime = Field(..., description="Timestamp of document creation")
    error: dict[str, str] | None = Field(
        None,
        description="Structured error details if ingestion failed: {'code': ..., 'message': ...}",
    )


class DocumentListResponse(BaseModel):
    """Paginated list of documents."""

    items: list[DocumentResponse] = Field(default_factory=list)
    total: int = Field(default=0)
