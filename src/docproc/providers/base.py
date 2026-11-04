"""Protocols and interfaces for LLM and Embedding providers."""

from typing import Protocol, runtime_checkable


@runtime_checkable
class EmbeddingProvider(Protocol):
    """Protocol for embedding providers."""

    dimension: int

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Generates embeddings for a batch of document texts."""
        ...

    async def embed_query(self, text: str) -> list[float]:
        """Generates an embedding for a search query."""
        ...


@runtime_checkable
class LLMProvider(Protocol):
    """Protocol for LLM generation providers."""

    async def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        """Generates a text completion for given prompt."""
        ...
