"""Vector store service querying DocumentChunk embeddings via pgvector."""

import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from docproc.db.models import Document, DocumentChunk
from docproc.schemas.retrieval import RetrievalResult, RetrievedChunk

logger = logging.getLogger(__name__)


def generate_source_id(doc_name: str, page: int | None, chunk_idx: int) -> str:
    """Generates a stable, human-readable citation source ID, e.g. src_quote_p2_c0."""
    clean_name = "".join(c for c in doc_name if c.isalnum() or c in ("_", "-")).lower()
    prefix = clean_name[:12].strip("._-") or "doc"
    page_part = f"p{page}" if page is not None else "p1"
    return f"src_{prefix}_{page_part}_c{chunk_idx}"


async def search_similar_chunks(
    session: AsyncSession,
    query_vector: list[float],
    document_ids: list[str] | None = None,
    top_k: int = 5,
    relevance_threshold: float = 0.5,
    query_text: str = "",
) -> RetrievalResult:
    """Retrieves top-k document chunks closest to the query embedding using pgvector cosine distance."""
    # Convert query vector to cosine distance expression
    # pgvector provides cosine_distance operator `<=>`
    distance_expr = DocumentChunk.embedding.cosine_distance(query_vector).label("distance")

    stmt = (
        select(DocumentChunk, distance_expr, Document.filename)
        .join(Document, Document.id == DocumentChunk.document_id)
        .options(selectinload(DocumentChunk.document))
    )

    if document_ids:
        # Convert string UUIDs to uuid.UUID objects
        uuid_list = [uuid.UUID(d) if isinstance(d, str) else d for d in document_ids]
        stmt = stmt.where(DocumentChunk.document_id.in_(uuid_list))

    stmt = stmt.order_by("distance").limit(top_k)

    result = await session.execute(stmt)
    rows = result.all()

    retrieved: list[RetrievedChunk] = []
    has_sufficient_evidence = False

    for chunk, distance, doc_filename in rows:
        similarity = float(1.0 - distance)
        # Check against relevance threshold
        if similarity >= relevance_threshold:
            has_sufficient_evidence = True

        src_id = generate_source_id(doc_filename, chunk.page_number, chunk.chunk_index)
        retrieved.append(
            RetrievedChunk(
                source_id=src_id,
                chunk_id=str(chunk.id),
                document_id=str(chunk.document_id),
                document_name=doc_filename,
                page=chunk.page_number,
                excerpt=chunk.text,
                similarity_score=round(similarity, 4),
            )
        )

    # Filter out chunks that do not meet relevance threshold if thresholding is strictly applied
    qualified_chunks = [c for c in retrieved if c.similarity_score >= relevance_threshold]

    return RetrievalResult(
        chunks=qualified_chunks,
        has_sufficient_evidence=has_sufficient_evidence and len(qualified_chunks) > 0,
        query=query_text,
        top_k=top_k,
    )
