"""Integration tests for document ingestion and management API."""

import io
from unittest.mock import patch

import pytest
from httpx import AsyncClient

from docproc.db.session import get_db
from docproc.main import app
from tests.mock_db import InMemoryAsyncSession
from tests.unit.test_parsers import create_in_memory_pdf


@pytest.fixture
def mock_session() -> InMemoryAsyncSession:
    return InMemoryAsyncSession()


@pytest.fixture(autouse=True)
def override_db(mock_session: InMemoryAsyncSession):
    async def _get_mock_db():
        yield mock_session

    app.dependency_overrides[get_db] = _get_mock_db
    yield
    app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_upload_text_document_success(async_client: AsyncClient) -> None:
    """Verifies that uploading a plain text file succeeds with HTTP 201 Created."""
    content = b"Vendor Agreement\nPayment terms must be net 30 days."
    files = {"file": ("vendor_agreement.txt", io.BytesIO(content), "text/plain")}

    response = await async_client.post("/documents", files=files)
    assert response.status_code == 201
    data = response.json()

    assert data["filename"] == "vendor_agreement.txt"
    assert data["content_type"] == "text/plain"
    assert data["status"] == "completed"
    assert data["chunk_count"] >= 1
    assert data["page_count"] == 1
    assert data["error"] is None
    assert "document_id" in data


@pytest.mark.asyncio
async def test_upload_pdf_document_success(async_client: AsyncClient) -> None:
    """Verifies uploading a multi-page PDF document extracts pages and chunks."""
    pdf_bytes = create_in_memory_pdf(
        [
            "Corporate Procurement Policy 2026. Page 1 introduction.",
            "Section 2: Payment terms must be 30 days. No advance payments over $50k.",
        ]
    )
    files = {"file": ("policy.pdf", io.BytesIO(pdf_bytes), "application/pdf")}

    response = await async_client.post("/documents", files=files)
    assert response.status_code == 201
    data = response.json()

    assert data["filename"] == "policy.pdf"
    assert data["page_count"] == 2
    assert data["chunk_count"] >= 2
    assert data["status"] == "completed"


@pytest.mark.asyncio
async def test_upload_unsupported_media_type_fails(async_client: AsyncClient) -> None:
    """Verifies that uploading an unsupported MIME type returns HTTP 415."""
    files = {"file": ("image.png", io.BytesIO(b"\x89PNG\r\n\x1a\n"), "image/png")}

    response = await async_client.post("/documents", files=files)
    assert response.status_code == 415
    data = response.json()
    assert data["error"]["code"] == "UNSUPPORTED_MEDIA_TYPE"


@pytest.mark.asyncio
async def test_upload_file_too_large_fails(async_client: AsyncClient) -> None:
    """Verifies that uploading a file larger than max size returns HTTP 413."""
    with patch("docproc.ingestion.service.get_settings") as mock_settings:
        from docproc.config import Settings

        # Set max file size to 50 bytes for test
        mock_settings.return_value = Settings(MAX_FILE_SIZE_BYTES=50)

        large_content = b"A" * 100
        files = {"file": ("large.txt", io.BytesIO(large_content), "text/plain")}
        response = await async_client.post("/documents", files=files)
        assert response.status_code == 413
        assert response.json()["error"]["code"] == "FILE_TOO_LARGE"


@pytest.mark.asyncio
async def test_get_and_delete_document(
    async_client: AsyncClient, mock_session: InMemoryAsyncSession
) -> None:
    """Verifies document lookup by ID and deletion."""
    # First upload
    content = b"Sample policy text for lookup and deletion."
    files = {"file": ("sample.txt", io.BytesIO(content), "text/plain")}
    create_res = await async_client.post("/documents", files=files)
    doc_id = create_res.json()["document_id"]

    # List documents
    list_res = await async_client.get("/documents")
    assert list_res.status_code == 200
    assert list_res.json()["total"] >= 1

    # Get single document
    get_res = await async_client.get(f"/documents/{doc_id}")
    assert get_res.status_code == 200
    assert get_res.json()["document_id"] == doc_id

    # Delete document
    del_res = await async_client.delete(f"/documents/{doc_id}")
    assert del_res.status_code == 204

    # Subsequent get should return 404
    get_after_del = await async_client.get(f"/documents/{doc_id}")
    assert get_after_del.status_code == 404
    assert get_after_del.json()["error"]["code"] == "DOCUMENT_NOT_FOUND"
