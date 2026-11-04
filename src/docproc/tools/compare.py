"""Cross-document value comparison tool."""

from docproc.schemas.tools import (
    CompareDocumentValuesInput,
    CompareDocumentValuesOutput,
)
from docproc.tools.base import BaseTool


def values_are_equal(v1: any, v2: any) -> bool:
    """Compares two values with type normalization."""
    if isinstance(v1, (int, float)) and isinstance(v2, (int, float)):
        return abs(float(v1) - float(v2)) < 1e-4

    # String comparison normalized
    s1 = str(v1).strip().lower()
    s2 = str(v2).strip().lower()
    return s1 == s2


class CompareDocumentValuesTool(BaseTool):
    """Compares factual fields across multiple documents to identify agreements or discrepancies."""

    name = "compare_document_values"
    description = (
        "Compares values of a specific field across two or more documents to check for concordance "
        "or detect conflicts and policy violations."
    )
    input_schema = CompareDocumentValuesInput
    output_schema = CompareDocumentValuesOutput

    async def run(self, args: CompareDocumentValuesInput) -> CompareDocumentValuesOutput:
        field = args.field_name
        items = args.items
        all_sources = [item.source_id for item in items]

        if len(items) < 2:
            return CompareDocumentValuesOutput(
                field_name=field,
                is_concordant=True,
                discrepancy_description=None,
                conflicting_sources=[],
                all_sources=all_sources,
                status="completed",
            )

        baseline = items[0]
        conflicts: list[tuple[str, any, str, any, str, str]] = []

        for item in items[1:]:
            if not values_are_equal(baseline.value, item.value):
                conflicts.append(
                    (
                        baseline.document_name,
                        baseline.value,
                        item.document_name,
                        item.value,
                        baseline.source_id,
                        item.source_id,
                    )
                )

        if not conflicts:
            return CompareDocumentValuesOutput(
                field_name=field,
                is_concordant=True,
                discrepancy_description=None,
                conflicting_sources=[],
                all_sources=all_sources,
                status="completed",
                error=None,
            )

        # Build conflict message citing both documents
        doc1, val1, doc2, val2, s1, s2 = conflicts[0]
        desc = (
            f"Discrepancy in '{field}': '{doc1}' specifies '{val1}', "
            f"whereas '{doc2}' specifies '{val2}'."
        )
        conflict_srcs = list(dict.fromkeys([s1, s2]))

        return CompareDocumentValuesOutput(
            field_name=field,
            is_concordant=False,
            discrepancy_description=desc,
            conflicting_sources=conflict_srcs,
            all_sources=all_sources,
            status="completed",
            error=None,
        )
