"""Concurrency and load isolation tests."""

import asyncio
import io

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
async def test_ten_concurrent_queries_no_state_leakage(async_client: AsyncClient) -> None:
    """Verifies that 10 concurrent requests execute without cross-request state leakage or corruption."""
    # Ingest baseline document
    doc_content = create_in_memory_pdf(
        [
            "Contract A: Vendor Name: Global Logistics Corp. Total amount: $80,000 USD. Terms: Net 30.",
        ]
    )
    up_res = await async_client.post(
        "/documents",
        files={"file": ("contract_a.pdf", io.BytesIO(doc_content), "application/pdf")},
    )
    assert up_res.status_code == 201
    doc_id = up_res.json()["document_id"]

    # Dispatch 10 concurrent queries with distinct request IDs
    async def make_query(idx: int):
        custom_header = {"X-Request-ID": f"req_concurrency_{idx}"}
        payload = {
            "query": f"Extract vendor name and amount for task {idx}.",
            "document_ids": [doc_id],
            "top_k": 3,
        }
        res = await async_client.post("/query", json=payload, headers=custom_header)
        return idx, res

    tasks = [make_query(i) for i in range(10)]
    results = await asyncio.gather(*tasks)

    seen_request_ids = set()
    for idx, resp in results:
        assert resp.status_code == 200
        data = resp.json()
        req_id = data["request_id"]
        assert req_id == f"req_concurrency_{idx}"
        assert req_id not in seen_request_ids
        seen_request_ids.add(req_id)

        # Verify response structure is intact
        assert "extracted_data" in data
        assert "sources" in data
        assert data["workflow"]["duration_ms"] >= 0

    assert len(seen_request_ids) == 10
