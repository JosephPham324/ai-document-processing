"""Integration test running the evaluation benchmark and verifying all quality gates."""

import pytest

from evaluation.run_benchmark import run_evaluation


@pytest.mark.asyncio
async def test_all_benchmark_quality_gates() -> None:
    """Verifies that all quantifiable project gates meet their declared targets."""
    results = await run_evaluation()

    assert results["num_questions"] == 20
    # Gate 1: Recall@5 >= 0.80
    assert results["recall_at_5"] >= 0.80, f"Recall@5 {results['recall_at_5']} < 0.80"

    # Gate 2: MRR@5 >= 0.70
    assert results["mrr_at_5"] >= 0.70, f"MRR@5 {results['mrr_at_5']} < 0.70"

    # Gate 3: Retrieval Latency p95 <= 1000 ms
    assert results["retrieval_latency_p95_ms"] <= 1000.0

    # Gate 4: Query Latency p95 <= 30000 ms
    assert results["query_latency_p95_ms"] <= 30000.0

    # Gate 5: Health Latency p95 <= 200 ms
    assert results["health_latency_p95_ms"] <= 200.0

    # Gate 6: Citation Precision >= 0.90
    assert results["citation_precision"] >= 0.90
