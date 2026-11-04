"""Unit tests for deterministic mock embedding provider."""

import math

import pytest

from docproc.providers.mock_provider import MockEmbeddingProvider


def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    dot = sum(a * b for a, b in zip(v1, v2, strict=True))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    return dot / (norm1 * norm2) if norm1 > 0 and norm2 > 0 else 0.0


@pytest.mark.asyncio
async def test_mock_embedding_provider_properties() -> None:
    provider = MockEmbeddingProvider(dimension=1536)

    # 1. Dimension and normalization
    vec = await provider.embed_query("payment terms within 30 days")
    assert len(vec) == 1536
    norm = math.sqrt(sum(x * x for x in vec))
    assert pytest.approx(norm, 1e-5) == 1.0

    # 2. Determinism
    vec2 = await provider.embed_query("payment terms within 30 days")
    assert vec == vec2

    # 3. Semantic similarity correlation
    related_vec = await provider.embed_query("payment terms policy 30 days invoice")
    unrelated_vec = await provider.embed_query("astronomy telescope solar flare galaxies")

    sim_related = cosine_similarity(vec, related_vec)
    sim_unrelated = cosine_similarity(vec, unrelated_vec)

    assert sim_related > sim_unrelated
    assert sim_related > 0.5
    assert sim_unrelated < 0.3
