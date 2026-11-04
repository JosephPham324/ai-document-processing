"""Integration tests for the Query endpoint and LangGraph agent workflow."""

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
async def test_end_to_end_query_extraction_and_comparison(async_client: AsyncClient) -> None:
    """Verifies end-to-end workflow executing extraction and cross-document comparison with citations."""
    # 1. Ingest Quotation PDF
    quote_pdf = create_in_memory_pdf(
        [
            "Document Title: Quotation Acme. Page 1 info.",
            "Quotation Details:\nVendor Name: Example Vendor Ltd.\nTotal Quote Amount: $125,000 USD\nPayment terms: Payment within 15 days.",
        ]
    )
    quote_res = await async_client.post(
        "/documents",
        files={"file": ("Vendor Quotation.pdf", io.BytesIO(quote_pdf), "application/pdf")},
    )
    assert quote_res.status_code == 201
    quote_id = quote_res.json()["document_id"]

    # 2. Ingest Policy PDF
    policy_pdf = create_in_memory_pdf(
        [
            "Corporate Procurement Policy 2026. Page 1 introduction.",
            "Section 4: Standard payment terms shall be within 30 days from invoice receipt.",
        ]
    )
    policy_res = await async_client.post(
        "/documents",
        files={"file": ("Procurement Policy.pdf", io.BytesIO(policy_pdf), "application/pdf")},
    )
    assert policy_res.status_code == 201
    policy_id = policy_res.json()["document_id"]

    # 3. Query the agent
    query_payload = {
        "query": "Extract the vendor name and amount, then compare the payment terms against the policy.",
        "document_ids": [quote_id, policy_id],
        "top_k": 5,
    }
    response = await async_client.post("/query", json=query_payload)
    assert response.status_code == 200
    data = response.json()

    # 4. Verify API response shape and contracts
    assert data["request_id"].startswith("req_")
    assert data["status"] in ("completed", "completed_with_warnings")
    assert (
        "conflict" in data["summary"].lower()
        or "discrepancy" in data["summary"].lower()
        or "15" in data["summary"]
    )

    # Extracted data
    extracted = data["extracted_data"]
    assert "vendor_name" in extracted
    assert extracted["vendor_name"]["status"] == "found"
    assert "Example Vendor" in str(extracted["vendor_name"]["value"])
    assert len(extracted["vendor_name"]["sources"]) >= 1

    assert "amount" in extracted
    assert extracted["amount"]["status"] == "found"
    assert extracted["amount"]["value"] == 125000
    assert extracted["amount"]["unit"] == "USD"
    assert len(extracted["amount"]["sources"]) >= 1

    # Sources provenance integrity
    sources = data["sources"]
    assert len(sources) >= 2
    source_ids = {s["source_id"] for s in sources}
    # Verify every cited source resolves to a retrieved chunk
    for field in extracted.values():
        for src in field["sources"]:
            assert src in source_ids

    # Workflow trace
    workflow = data["workflow"]
    assert "analyze_request" in workflow["steps_completed"]
    assert "retrieve_evidence" in workflow["steps_completed"]
    assert "select_tools" in workflow["steps_completed"]
    assert "execute_tools" in workflow["steps_completed"]
    assert "synthesize_response" in workflow["steps_completed"]

    # Verify at least two distinct tools executed
    tool_names = [tc["tool_name"] for tc in workflow["tool_calls"]]
    assert "extract_structured_fields" in tool_names
    assert "compare_document_values" in tool_names or "validate_fields" in tool_names
    assert workflow["duration_ms"] >= 0


@pytest.mark.asyncio
async def test_query_no_evidence_handling(
    async_client: AsyncClient, mock_session: InMemoryAsyncSession
) -> None:
    """Verifies that an ungrounded query returns explicit no_evidence status."""
    # Empty database
    query_payload = {
        "query": "What is the orbital velocity of Neptune according to the policy?",
        "top_k": 5,
    }
    response = await async_client.post("/query", json=query_payload)
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "no_evidence"
    assert "not contain sufficient evidence" in data["summary"]
    assert data["sources"] == []
    # Verify tool execution was bypassed
    tool_names = [tc["tool_name"] for tc in data["workflow"]["tool_calls"]]
    assert len(tool_names) == 0


@pytest.mark.asyncio
async def test_query_unknown_document_id_returns_404(async_client: AsyncClient) -> None:
    """Verifies that querying an unknown document UUID returns HTTP 404."""
    unknown_uuid = "00000000-0000-0000-0000-000000000000"
    payload = {
        "query": "Extract the vendor name",
        "document_ids": [unknown_uuid],
    }
    response = await async_client.post("/query", json=payload)
    assert response.status_code == 404
    data = response.json()
    assert data["error"]["code"] == "DOCUMENT_NOT_FOUND"


@pytest.mark.asyncio
async def test_query_validation_errors(async_client: AsyncClient) -> None:
    """Verifies that invalid queries return HTTP 422 with the standard error envelope."""
    # Empty query
    res = await async_client.post("/query", json={"query": ""})
    assert res.status_code == 422
    assert res.json()["error"]["code"] == "VALIDATION_ERROR"

    # Query exceeding 4000 characters
    res_long = await async_client.post("/query", json={"query": "A" * 4001})
    assert res_long.status_code == 422
    assert res_long.json()["error"]["code"] == "VALIDATION_ERROR"
