"""Unit tests for document parsers (PDF, TXT, Markdown)."""

import pymupdf as fitz
import pytest

from docproc.ingestion.parsers import (
    ParsingError,
    parse_document,
    parse_pdf,
    parse_text,
)


def create_in_memory_pdf(pages_text: list[str]) -> bytes:
    """Helper to generate a multi-page PDF in memory using PyMuPDF."""
    doc = fitz.open()
    for text in pages_text:
        page = doc.new_page()
        page.insert_text((50, 72), text)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def test_parse_multi_page_pdf() -> None:
    """Verifies that PDF parser retains exact 1-based page numbers across pages."""
    pages_content = [
        "Procurement Policy 2026. Page 1 content regarding vendor compliance.",
        "Payment terms must be net 30 days from invoice date. Page 2 details.",
        "Approval thresholds: Orders over $100,000 require CFO signoff. Page 3.",
    ]
    pdf_bytes = create_in_memory_pdf(pages_content)
    parsed = parse_pdf(pdf_bytes, "policy.pdf")

    assert parsed.filename == "policy.pdf"
    assert parsed.content_type == "application/pdf"
    assert parsed.page_count == 3
    assert len(parsed.pages) == 3

    assert parsed.pages[0].page_number == 1
    assert "Procurement Policy" in parsed.pages[0].text

    assert parsed.pages[1].page_number == 2
    assert "net 30 days" in parsed.pages[1].text

    assert parsed.pages[2].page_number == 3
    assert "CFO signoff" in parsed.pages[2].text


def test_parse_corrupt_pdf() -> None:
    """Verifies that corrupted PDF bytes raise a structured ParsingError."""
    corrupt_bytes = b"NOT_A_REAL_PDF_HEADER_123456"
    with pytest.raises(ParsingError) as exc_info:
        parse_pdf(corrupt_bytes, "corrupt.pdf")
    assert exc_info.value.code == "INVALID_PDF_FORMAT"


def test_parse_text_file() -> None:
    """Verifies plain text parsing."""
    raw = b"Vendor Agreement\nPayment is due within 15 days."
    parsed = parse_text(raw, "agreement.txt", content_type="text/plain")

    assert parsed.filename == "agreement.txt"
    assert parsed.page_count == 1
    assert len(parsed.pages) == 1
    assert parsed.pages[0].page_number == 1
    assert "within 15 days" in parsed.pages[0].text


def test_parse_markdown_file() -> None:
    """Verifies Markdown parsing via parse_document dispatcher."""
    raw = b"# Architecture Notes\n\n- Component 1: RAG\n- Component 2: LangGraph"
    parsed = parse_document(raw, "notes.md", content_type="text/markdown")

    assert parsed.content_type == "text/markdown"
    assert parsed.page_count == 1
    assert "Component 1: RAG" in parsed.pages[0].text


def test_parse_empty_document_raises() -> None:
    """Verifies that empty documents raise a ParsingError."""
    with pytest.raises(ParsingError) as exc_info:
        parse_text(b"   \n\t  ", "empty.txt")
    assert exc_info.value.code == "EMPTY_DOCUMENT_TEXT"
