"""Tests for health and readiness endpoints."""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(async_client: AsyncClient) -> None:
    """Verifies that /health returns HTTP 200 with status: ok."""
    response = await async_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data == {"status": "ok"}
    assert "X-Request-ID" in response.headers


@pytest.mark.asyncio
async def test_ready_check_when_database_is_ready(async_client: AsyncClient) -> None:
    """Verifies that /ready returns HTTP 200 when database connectivity succeeds."""
    with patch("docproc.api.routers.health.check_db_ready", new_callable=AsyncMock) as mock_check:
        mock_check.return_value = True
        response = await async_client.get("/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert data["dependencies"]["database"] == "ok"
        assert data["dependencies"]["embedding_provider"] == "ok"


@pytest.mark.asyncio
async def test_ready_check_when_database_is_unavailable(async_client: AsyncClient) -> None:
    """Verifies that /ready returns HTTP 503 when database connectivity fails."""
    with patch("docproc.api.routers.health.check_db_ready", new_callable=AsyncMock) as mock_check:
        mock_check.return_value = False
        response = await async_client.get("/ready")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "not_ready"
        assert data["dependencies"]["database"] == "unavailable"
