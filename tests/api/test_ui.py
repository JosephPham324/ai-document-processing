"""Tests for the interactive serving web UI endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_serve_ui_root(async_client: AsyncClient) -> None:
    """Verifies that GET / returns the HTML dashboard UI."""
    response = await async_client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert "Document Intelligence AI Agent" in response.text
    assert "drop-zone" in response.text
    assert "query-input" in response.text


@pytest.mark.asyncio
async def test_serve_ui_dashboard_alias(async_client: AsyncClient) -> None:
    """Verifies that GET /dashboard returns the HTML dashboard UI."""
    response = await async_client.get("/dashboard")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert "Document Intelligence AI Agent" in response.text
