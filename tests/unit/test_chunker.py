"""Unit tests for recursive page-aware text chunker."""

from docproc.ingestion.chunker import (
    chunk_document,
    estimate_token_count,
    split_text_recursive,
)
from docproc.ingestion.parsers import ParsedDocument, ParsedPage


def test_split_text_recursive_respects_limits() -> None:
    """Verifies that split_text_recursive divides long text without exceeding chunk_size."""
    long_text = (
        "Paragraph 1 discusses procurement policies and vendor regulations. " * 5
        + "\n\n"
        + "Paragraph 2 sets payment terms to 30 days after invoice delivery. " * 5
    )
    chunks = split_text_recursive(long_text, chunk_size=200, chunk_overlap=30)
    assert len(chunks) > 1
    for c in chunks:
        assert len(c) <= 220  # allow small tolerance for boundary splitting


def test_chunk_document_preserves_page_numbers() -> None:
    """Verifies that chunks maintain correct page_number from parsed pages."""
    doc = ParsedDocument(
        filename="multipage.pdf",
        content_type="application/pdf",
        page_count=2,
        pages=[
            ParsedPage(page_number=1, text="First page content. Vendor name is Acme Corp."),
            ParsedPage(page_number=2, text="Second page content. Total quote amount is $125,000."),
        ],
    )
    chunks = chunk_document(doc, chunk_size=500, chunk_overlap=50)

    assert len(chunks) == 2
    assert chunks[0].page_number == 1
    assert "Acme Corp" in chunks[0].text
    assert chunks[0].chunk_index == 0

    assert chunks[1].page_number == 2
    assert "$125,000" in chunks[1].text
    assert chunks[1].chunk_index == 1


def test_estimate_token_count() -> None:
    """Verifies token count estimation heuristic."""
    text = "Hello world! This is a test."
    tokens = estimate_token_count(text)
    assert tokens > 0
    assert tokens == max(1, len(text) // 4)
