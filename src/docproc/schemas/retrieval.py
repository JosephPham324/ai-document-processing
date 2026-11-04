"""Pydantic schemas for RAG retrieval and source citations."""

from pydantic import BaseModel, Field


class RetrievedChunk(BaseModel):
    """Retrieved document chunk with provenance metadata."""

    source_id: str = Field(..., description="Unique source citation identifier, e.g. src_quote_p2")
    chunk_id: str = Field(..., description="Chunk ID in database")
    document_id: str = Field(..., description="Parent document UUID")
    document_name: str = Field(..., description="Parent document filename")
    page: int | None = Field(None, description="1-based page number where available")
    excerpt: str = Field(..., description="Text excerpt from stored chunk")
    similarity_score: float = Field(..., description="Vector similarity score (0.0 - 1.0)")


class RetrievalResult(BaseModel):
    """Aggregate result from vector retrieval."""

    chunks: list[RetrievedChunk] = Field(default_factory=list)
    has_sufficient_evidence: bool = Field(
        ...,
        description="True if at least one chunk satisfies the relevance threshold",
    )
    query: str
    top_k: int
