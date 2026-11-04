"""Deterministic mock embedding and LLM providers for testing."""

import hashlib
import math
import re
from typing import Any


class MockEmbeddingProvider:
    """Deterministic embedding provider that simulates semantic similarity via token hashing and L2 normalization."""

    def __init__(self, dimension: int = 1536) -> None:
        self.dimension = dimension

    def _compute_vector(self, text: str) -> list[float]:
        """Computes a deterministic unit-length vector for input text."""
        vector = [0.0] * self.dimension
        tokens = re.findall(r"\w+", text.lower())

        if not tokens:
            # Deterministic default vector for empty strings
            vector[0] = 1.0
            return vector

        # Accumulate token hash distributions
        for token in tokens:
            # Generate deterministic bucket from token
            h = int(hashlib.sha256(token.encode("utf-8")).hexdigest(), 16)
            idx = h % self.dimension
            # Spread energy to adjacent dimensions for slight fuzzy matching
            weight = 1.0 + (len(token) / 10.0)
            vector[idx] += weight
            vector[(idx + 7) % self.dimension] += weight * 0.5
            vector[(idx + 13) % self.dimension] += weight * 0.25

        # Normalize to unit length (L2 norm)
        norm = math.sqrt(sum(x * x for x in vector))
        if norm > 0:
            vector = [x / norm for x in vector]

        return vector

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Generates embeddings for a batch of documents."""
        return [self._compute_vector(t) for t in texts]

    async def embed_query(self, text: str) -> list[float]:
        """Generates embedding for query."""
        return self._compute_vector(text)


class MockLLMProvider:
    """Mock LLM provider returning structured synthetic responses or echo for tests."""

    def __init__(self, canned_responses: dict[str, Any] | None = None) -> None:
        self.canned_responses = canned_responses or {}

    async def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        for key, response in self.canned_responses.items():
            if key in prompt:
                return response
        return '{"summary": "Mock synthesis response", "status": "completed"}'
