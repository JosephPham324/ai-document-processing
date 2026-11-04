"""Tests for standardized error envelopes."""

import pytest
from httpx import AsyncClient

from docproc.api.error_handlers import (
    DocumentNotFoundException,
    DuplicateDocumentException,
    FileTooLargeException,
    ProviderTimeoutException,
    ProviderUnavailableException,
    UnsupportedMediaTypeException,
    WorkflowLimitExceededException,
)
from docproc.main import app


@pytest.mark.asyncio
async def test_not_found_error_envelope(async_client: AsyncClient) -> None:
    """Verifies that an unknown endpoint returns the standard error envelope with request_id."""
    response = await async_client.get("/nonexistent-route")
    assert response.status_code == 404
    data = response.json()

    assert "error" in data
    error = data["error"]
    assert error["code"] == "NOT_FOUND"
    assert "message" in error
    assert "request_id" in error
    assert error["request_id"].startswith("req_")
    assert response.headers.get("X-Request-ID") == error["request_id"]


@pytest.mark.asyncio
async def test_app_exceptions_handling(async_client: AsyncClient) -> None:
    """Verifies that custom AppException subclasses format correctly."""

    # Temporary test route to trigger exceptions
    @app.get("/test-error/{error_type}")
    async def trigger_error(error_type: str):
        if error_type == "not_found":
            raise DocumentNotFoundException("doc_test_123")
        elif error_type == "unsupported":
            raise UnsupportedMediaTypeException("image/png", ["application/pdf"])
        elif error_type == "too_large":
            raise FileTooLargeException(25000000, 20971520)
        elif error_type == "duplicate":
            raise DuplicateDocumentException("doc_orig", "hash_abc")
        elif error_type == "provider_unavail":
            raise ProviderUnavailableException("openai")
        elif error_type == "provider_timeout":
            raise ProviderTimeoutException("gemini")
        elif error_type == "workflow_limit":
            raise WorkflowLimitExceededException("exceeded 10 steps")
        return {"status": "ok"}

    res = await async_client.get("/test-error/not_found")
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "DOCUMENT_NOT_FOUND"
    assert res.json()["error"]["details"]["document_id"] == "doc_test_123"

    res = await async_client.get("/test-error/unsupported")
    assert res.status_code == 415
    assert res.json()["error"]["code"] == "UNSUPPORTED_MEDIA_TYPE"

    res = await async_client.get("/test-error/too_large")
    assert res.status_code == 413
    assert res.json()["error"]["code"] == "FILE_TOO_LARGE"

    res = await async_client.get("/test-error/duplicate")
    assert res.status_code == 409
    assert res.json()["error"]["code"] == "DUPLICATE_DOCUMENT"

    res = await async_client.get("/test-error/provider_unavail")
    assert res.status_code == 503
    assert res.json()["error"]["code"] == "PROVIDER_UNAVAILABLE"

    res = await async_client.get("/test-error/provider_timeout")
    assert res.status_code == 504
    assert res.json()["error"]["code"] == "PROVIDER_TIMEOUT"

    res = await async_client.get("/test-error/workflow_limit")
    assert res.status_code == 422
    assert res.json()["error"]["code"] == "WORKFLOW_LIMIT_EXCEEDED"
