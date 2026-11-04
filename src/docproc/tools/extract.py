"""Structured field extraction tool."""

import re
from typing import Any

from docproc.schemas.tools import (
    ChunkContext,
    ExtractedField,
    ExtractStructuredFieldsInput,
    ExtractStructuredFieldsOutput,
)
from docproc.tools.base import BaseTool


def extract_field_from_text(
    field_name: str,
    chunks: list[ChunkContext],
    hint: str | None = None,
) -> ExtractedField:
    """Extracts a specific entity/field from candidate evidence chunks with source attribution."""
    clean_field = field_name.lower().replace(" ", "_")
    found_values: list[tuple[Any, str | None, str]] = []  # (value, unit, source_id)

    # Regex patterns for common business entities
    patterns: list[tuple[re.Pattern, str | None]] = []

    if "vendor" in clean_field or "supplier" in clean_field:
        patterns.append(
            (
                re.compile(
                    r"(?:vendor|supplier|company)(?:\s+name)?[:\s\-]+([A-Za-z0-9\s,\.]{3,40}?)(?:\n|\.|$)",
                    re.IGNORECASE,
                ),
                None,
            )
        )
    elif (
        "amount" in clean_field
        or "total" in clean_field
        or "price" in clean_field
        or "cost" in clean_field
    ):
        patterns.append(
            (
                re.compile(
                    r"(?:total|amount|cost|price|quote)[:\s\-]+(?:\$|USD\s*)?([0-9,]+(?:\.[0-9]{2})?)\s*(USD|EUR|GBP)?",
                    re.IGNORECASE,
                ),
                "USD",
            )
        )
        patterns.append((re.compile(r"\$([0-9,]+(?:\.[0-9]{2})?)", re.IGNORECASE), "USD"))
    elif "term" in clean_field or "payment" in clean_field:
        patterns.append(
            (
                re.compile(r"(?:payment\s+terms?|terms?)[:\s\-]+(.*?)(?:\n|\.|$)", re.IGNORECASE),
                None,
            )
        )
        patterns.append(
            (re.compile(r"(?:net\s+\d+\s+days|within\s+\d+\s+days)", re.IGNORECASE), None)
        )
    else:
        # Generic key: value pattern (requires separator like : or - or =)
        escaped = re.escape(field_name.replace("_", " "))
        patterns.append(
            (re.compile(rf"(?:{escaped})\s*[:\-=]\s*(.*?)(?:\n|\.|$)", re.IGNORECASE), None)
        )

    for chunk in chunks:
        text = chunk.excerpt
        for pat, default_unit in patterns:
            match = pat.search(text)
            if match:
                raw_val = match.group(1).strip()
                unit = default_unit
                if match.lastindex and match.lastindex >= 2 and match.group(2):
                    unit = match.group(2).strip()

                # Clean numeric amounts
                if "amount" in clean_field or "price" in clean_field or "total" in clean_field:
                    num_str = raw_val.replace(",", "").replace("$", "").strip()
                    try:
                        val = float(num_str) if "." in num_str else int(num_str)
                    except ValueError:
                        val = raw_val
                else:
                    val = raw_val

                found_values.append((val, unit, chunk.source_id))
                break

    if not found_values:
        return ExtractedField(
            value=None,
            unit=None,
            status="not_found",
            sources=[],
        )

    # Check for conflicts across chunks
    distinct_values = {v[0] for v in found_values}
    if len(distinct_values) > 1:
        # Multiple conflicting values found
        conflicting_sources = list(dict.fromkeys(v[2] for v in found_values))
        return ExtractedField(
            value=list(distinct_values),
            unit=found_values[0][1],
            status="conflict",
            sources=conflicting_sources,
        )

    first_val, unit, src_id = found_values[0]
    return ExtractedField(
        value=first_val,
        unit=unit,
        status="found",
        sources=[src_id],
    )


class ExtractStructuredFieldsTool(BaseTool):
    """Extracts typed entities and fields from retrieved evidence chunks with provenance."""

    name = "extract_structured_fields"
    description = (
        "Extracts structured key-value entities (vendor names, amounts, payment terms) "
        "from retrieved evidence chunks and links each value to its source citation ID."
    )
    input_schema = ExtractStructuredFieldsInput
    output_schema = ExtractStructuredFieldsOutput

    async def run(self, args: ExtractStructuredFieldsInput) -> ExtractStructuredFieldsOutput:
        extracted: dict[str, ExtractedField] = {}
        hints = args.field_hints or {}

        for field in args.fields:
            hint = hints.get(field)
            res = extract_field_from_text(field, args.chunks, hint=hint)
            extracted[field] = res

        return ExtractStructuredFieldsOutput(
            extracted_data=extracted,
            status="completed",
            error=None,
        )
