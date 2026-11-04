"""Unit tests for vector search and citation generation."""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from docproc.db.models import Document, DocumentChunk
from docproc.retrieval.vector_store import generate_source_id, search_similar_chunks


def test_generate_source_id() -> None:
    """Verifies citation source ID generation is deterministic and clean."""
    src_id = generate_source_id("Vendor_Quotation_Acme.pdf", page=2, chunk_idx=3)
    assert src_id.startswith("src_")
    assert "p2_c3" in src_id

    src_id_none_page = generate_source_id("agreement.txt", page=None, chunk_idx=0)
    assert src_id_none_page.startswith("src_")
    assert "p1_c0" in src_id_none_page


@pytest.mark.asyncio
async def test_search_similar_chunks_with_mock_session() -> None:
    """Verifies that search_similar_chunks calculates similarity and filters by threshold."""
    doc_id = uuid.uuid4()
    doc = Document(id=doc_id, filename="Policy.pdf")

    # Chunk with distance 0.2 (similarity 0.8)
    chunk1 = DocumentChunk(
        id=uuid.uuid4(),
        document_id=doc_id,
        chunk_index=0,
        page_number=1,
        text="Payment terms are 30 days.",
        document=doc,
    )
    # Chunk with distance 0.7 (similarity 0.3)
    chunk2 = DocumentChunk(
        id=uuid.uuid4(),
        document_id=doc_id,
        chunk_index=1,
        page_number=2,
        text="Unrelated information.",
        document=doc,
    )

    mock_result = MagicMock()
    mock_result.all.return_value = [
        (chunk1, 0.2, "Policy.pdf"),
        (chunk2, 0.7, "Policy.pdf"),
    ]

    mock_session = AsyncMock()
    mock_session.execute.return_value = mock_result

    result = await search_similar_chunks(
        session=mock_session,
        query_vector=[0.1] * 1536,
        top_k=5,
        relevance_threshold=0.5,
        query_text="payment terms",
    )

    assert result.has_sufficient_evidence is True
    assert len(result.chunks) == 1  # Only chunk1 meets threshold >= 0.5
    assert result.chunks[0].chunk_id == str(chunk1.id)
    assert result.chunks[0].similarity_score == 0.8
    assert result.chunks[0].document_name == "Policy.pdf"
    assert result.chunks[0].page == 1
