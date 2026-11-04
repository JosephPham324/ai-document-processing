"""Unit tests for allowlisted tools and tool registry."""

import pytest

from docproc.schemas.tools import (
    CalculateNumericInput,
    ChunkContext,
    CompareDocumentValuesInput,
    DocumentValueItem,
    ExtractStructuredFieldsInput,
    ValidateFieldsInput,
    ValidationRuleRequest,
)
from docproc.tools.calculate import CalculateNumericTool
from docproc.tools.compare import CompareDocumentValuesTool
from docproc.tools.extract import ExtractStructuredFieldsTool
from docproc.tools.registry import execute_tool
from docproc.tools.validate import ValidateFieldsTool

# -------------------------------------------------------------
# 1. CalculateNumericTool Tests (Deterministic Math)
# -------------------------------------------------------------


@pytest.mark.asyncio
async def test_calculate_numeric_operations() -> None:
    tool = CalculateNumericTool()

    # Addition
    res_add = await tool.run(CalculateNumericInput(operation="add", operands=[100, 25, 5]))
    assert res_add.status == "completed"
    assert res_add.result == 130
    assert "100 + 25 + 5 = 130" in res_add.formula_expressed

    # Subtraction
    res_sub = await tool.run(CalculateNumericInput(operation="subtract", operands=[100, 30]))
    assert res_sub.status == "completed"
    assert res_sub.result == 70

    # Multiplication
    res_mul = await tool.run(
        CalculateNumericInput(operation="multiply", operands=[125000, 0.15], unit="USD")
    )
    assert res_mul.status == "completed"
    assert res_mul.result == 18750
    assert res_mul.unit == "USD"

    # Division
    res_div = await tool.run(CalculateNumericInput(operation="divide", operands=[100, 4]))
    assert res_div.status == "completed"
    assert res_div.result == 25

    # Division by zero
    res_div_zero = await tool.run(CalculateNumericInput(operation="divide", operands=[100, 0]))
    assert res_div_zero.status == "failed"
    assert "Division by zero" in str(res_div_zero.error)

    # Percentage difference
    res_pct = await tool.run(
        CalculateNumericInput(operation="percentage_difference", operands=[100, 120])
    )
    assert res_pct.status == "completed"
    assert res_pct.result == 20.0


# -------------------------------------------------------------
# 2. ExtractStructuredFieldsTool Tests
# -------------------------------------------------------------


@pytest.mark.asyncio
async def test_extract_structured_fields() -> None:
    tool = ExtractStructuredFieldsTool()
    chunks = [
        ChunkContext(
            source_id="src_quote_p1",
            excerpt="Quotation from Vendor: Acme Solutions Ltd.\nTotal Quote Amount: $125,000 USD",
            document_name="quote.pdf",
            page=1,
        ),
        ChunkContext(
            source_id="src_quote_p2",
            excerpt="Payment terms: Payment within 15 days upon receipt of invoice.",
            document_name="quote.pdf",
            page=2,
        ),
    ]

    inp = ExtractStructuredFieldsInput(
        fields=["vendor_name", "amount", "payment_terms", "unmentioned_field"],
        chunks=chunks,
    )
    output = await tool.run(inp)
    assert output.status == "completed"

    data = output.extracted_data
    # Vendor
    assert data["vendor_name"].status == "found"
    assert "Acme Solutions" in str(data["vendor_name"].value)
    assert "src_quote_p1" in data["vendor_name"].sources

    # Amount
    assert data["amount"].status == "found"
    assert data["amount"].value == 125000
    assert data["amount"].unit == "USD"
    assert "src_quote_p1" in data["amount"].sources

    # Terms
    assert data["payment_terms"].status == "found"
    assert "within 15 days" in str(data["payment_terms"].value)
    assert "src_quote_p2" in data["payment_terms"].sources

    # Unmentioned field
    assert data["unmentioned_field"].status == "not_found"
    assert data["unmentioned_field"].sources == []


@pytest.mark.asyncio
async def test_extract_structured_fields_conflicts() -> None:
    tool = ExtractStructuredFieldsTool()
    chunks = [
        ChunkContext(source_id="src_doc1", excerpt="Total Amount: $50,000"),
        ChunkContext(source_id="src_doc2", excerpt="Total Amount: $75,000"),
    ]
    inp = ExtractStructuredFieldsInput(fields=["amount"], chunks=chunks)
    output = await tool.run(inp)

    amt = output.extracted_data["amount"]
    assert amt.status == "conflict"
    assert "src_doc1" in amt.sources
    assert "src_doc2" in amt.sources


# -------------------------------------------------------------
# 3. ValidateFieldsTool Tests
# -------------------------------------------------------------


@pytest.mark.asyncio
async def test_validate_fields_rules() -> None:
    tool = ValidateFieldsTool()
    rules = [
        ValidationRuleRequest(
            rule_id="terms_match_policy",
            field_name="payment_terms",
            expected_condition="equals",
            expected_value="30 days",
            actual_value="15 days",
            sources=["src_quote", "src_policy"],
        ),
        ValidationRuleRequest(
            rule_id="amount_within_limit",
            field_name="amount",
            expected_condition="must_not_exceed",
            expected_value=150000,
            actual_value=125000,
            sources=["src_quote"],
        ),
        ValidationRuleRequest(
            rule_id="amount_exceeds_limit",
            field_name="amount",
            expected_condition="must_not_exceed",
            expected_value=100000,
            actual_value=125000,
            sources=["src_quote"],
        ),
    ]

    output = await tool.run(ValidateFieldsInput(rules=rules))
    assert output.status == "completed"
    assert len(output.validation_results) == 3

    r1 = output.validation_results[0]
    assert r1.rule_id == "terms_match_policy"
    assert r1.status == "failed"
    assert "src_quote" in r1.sources

    r2 = output.validation_results[1]
    assert r2.rule_id == "amount_within_limit"
    assert r2.status == "passed"

    r3 = output.validation_results[2]
    assert r3.rule_id == "amount_exceeds_limit"
    assert r3.status == "failed"


# -------------------------------------------------------------
# 4. CompareDocumentValuesTool Tests
# -------------------------------------------------------------


@pytest.mark.asyncio
async def test_compare_document_values_concordant() -> None:
    tool = CompareDocumentValuesTool()
    inp = CompareDocumentValuesInput(
        field_name="project_name",
        items=[
            DocumentValueItem(
                document_id="doc_1",
                document_name="SOW.pdf",
                value="Apollo Project",
                source_id="src_sow",
            ),
            DocumentValueItem(
                document_id="doc_2",
                document_name="Quote.pdf",
                value="Apollo Project",
                source_id="src_quote",
            ),
        ],
    )
    out = await tool.run(inp)
    assert out.is_concordant is True
    assert out.discrepancy_description is None
    assert set(out.all_sources) == {"src_sow", "src_quote"}


@pytest.mark.asyncio
async def test_compare_document_values_discrepancy() -> None:
    tool = CompareDocumentValuesTool()
    inp = CompareDocumentValuesInput(
        field_name="payment_terms",
        items=[
            DocumentValueItem(
                document_id="doc_policy",
                document_name="Procurement Policy.pdf",
                value="30 days",
                source_id="src_policy_p4",
            ),
            DocumentValueItem(
                document_id="doc_quote",
                document_name="Vendor Quotation.pdf",
                value="15 days",
                source_id="src_quote_p2",
            ),
        ],
    )
    out = await tool.run(inp)
    assert out.is_concordant is False
    assert "Discrepancy" in out.discrepancy_description
    assert set(out.conflicting_sources) == {"src_policy_p4", "src_quote_p2"}


# -------------------------------------------------------------
# 5. Tool Registry Dispatch & Guardrail Tests
# -------------------------------------------------------------


@pytest.mark.asyncio
async def test_registry_allowlist_enforcement() -> None:
    """Verifies that unallowlisted tool calls are rejected before execution."""
    res = await execute_tool("system_shell_exec", {"cmd": "whoami"})
    assert res.status == "failed"
    assert "not in the allowlist" in res.error


@pytest.mark.asyncio
async def test_registry_schema_validation() -> None:
    """Verifies that invalid arguments return a structured tool error."""
    # calculate_numeric missing operands
    res = await execute_tool("calculate_numeric", {"operation": "add"})
    assert res.status == "failed"
    assert "Invalid arguments" in res.error


@pytest.mark.asyncio
async def test_registry_successful_execution() -> None:
    """Verifies valid tool execution produces a completed record with duration_ms."""
    res = await execute_tool(
        "calculate_numeric",
        {"operation": "multiply", "operands": [5, 20]},
    )
    assert res.status == "completed"
    assert res.duration_ms >= 0
    assert res.result["result"] == 100.0
