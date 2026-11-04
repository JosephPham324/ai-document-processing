"""Document parsers for PDF, TXT, and Markdown files."""

import logging
from dataclasses import dataclass

import pymupdf as fitz

logger = logging.getLogger(__name__)


class ParsingError(Exception):
    """Raised when parsing document bytes fails."""

    def __init__(self, message: str, code: str = "PARSING_FAILED") -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass
class ParsedPage:
    """Represents text extracted from a single document page."""

    page_number: int | None
    text: str


@dataclass
class ParsedDocument:
    """Standardized parsed document representation."""

    filename: str
    content_type: str
    page_count: int | None
    pages: list[ParsedPage]

    @property
    def total_text_length(self) -> int:
        return sum(len(p.text) for p in self.pages)


def parse_pdf(file_bytes: bytes, filename: str) -> ParsedDocument:
    """Extracts text from PDF bytes using PyMuPDF, preserving 1-based page numbers."""
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
    except Exception as exc:
        raise ParsingError(
            f"Failed to open PDF '{filename}': {exc}", code="INVALID_PDF_FORMAT"
        ) from exc

    pages: list[ParsedPage] = []
    try:
        page_count = len(doc)
        for page_idx in range(page_count):
            page = doc.load_page(page_idx)
            page_text = page.get_text("text").strip()
            # Retain page even if empty, but store clean text
            pages.append(ParsedPage(page_number=page_idx + 1, text=page_text))
    except Exception as exc:
        raise ParsingError(
            f"Error extracting text from PDF '{filename}': {exc}", code="PDF_EXTRACTION_ERROR"
        ) from exc
    finally:
        doc.close()

    if not any(len(p.text) > 0 for p in pages):
        raise ParsingError(
            f"PDF '{filename}' contains no extractable text.", code="EMPTY_DOCUMENT_TEXT"
        )

    return ParsedDocument(
        filename=filename,
        content_type="application/pdf",
        page_count=len(pages),
        pages=pages,
    )


def parse_text(
    file_bytes: bytes, filename: str, content_type: str = "text/plain"
) -> ParsedDocument:
    """Parses plain text or Markdown files."""
    try:
        text = file_bytes.decode("utf-8")
    except UnicodeDecodeError:
        try:
            text = file_bytes.decode("latin-1")
        except Exception as exc:
            raise ParsingError(
                f"Failed to decode text file '{filename}': {exc}", code="TEXT_DECODE_ERROR"
            ) from exc

    clean_text = text.strip()
    if not clean_text:
        raise ParsingError(f"Document '{filename}' is empty.", code="EMPTY_DOCUMENT_TEXT")

    return ParsedDocument(
        filename=filename,
        content_type=content_type,
        page_count=1,
        pages=[ParsedPage(page_number=1, text=clean_text)],
    )


def parse_document(file_bytes: bytes, filename: str, content_type: str) -> ParsedDocument:
    """Dispatches document parsing based on declared content type or file extension."""
    ct_lower = content_type.lower()
    fn_lower = filename.lower()

    if ct_lower == "application/pdf" or fn_lower.endswith(".pdf"):
        return parse_pdf(file_bytes, filename)
    elif ct_lower == "text/markdown" or fn_lower.endswith((".md", ".markdown")):
        return parse_text(file_bytes, filename, content_type="text/markdown")
    elif ct_lower == "text/plain" or fn_lower.endswith(".txt"):
        return parse_text(file_bytes, filename, content_type="text/plain")
    else:
        raise ParsingError(
            f"Unsupported content type '{content_type}' for file '{filename}'",
            code="UNSUPPORTED_MEDIA_TYPE",
        )
