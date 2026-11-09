"""Factory functions for initializing embedding and LLM providers."""

import logging

from docproc.config import Settings, get_settings
from docproc.providers.base import EmbeddingProvider, LLMProvider
from docproc.providers.gemini_provider import GeminiEmbeddingProvider, GeminiLLMProvider
from docproc.providers.mock_provider import MockEmbeddingProvider, MockLLMProvider
from docproc.providers.openai_provider import OpenAIEmbeddingProvider, OpenAILLMProvider

logger = logging.getLogger(__name__)

_embedding_instance: EmbeddingProvider | None = None
_llm_instance: LLMProvider | None = None


def reset_provider_singletons() -> None:
    """Resets cached provider singletons (useful in testing)."""
    global _embedding_instance, _llm_instance
    _embedding_instance = None
    _llm_instance = None


def get_embedding_provider(
    settings: Settings | None = None,
    provider_name: str | None = None,
    api_key: str | None = None,
) -> EmbeddingProvider:
    """Returns configured embedding provider (OpenAI, Gemini, or Mock).

    Supports client-provided per-request API keys (BYOK) when api_key is supplied,
    falling back to cached server singletons otherwise.
    """
    global _embedding_instance
    cfg = settings or get_settings()

    # If client passed an ephemeral API key, instantiate dynamically without mutating singleton
    if api_key or (provider_name and provider_name != cfg.EMBEDDING_PROVIDER):
        prov = (provider_name or cfg.EMBEDDING_PROVIDER).lower()
        if prov == "openai" and api_key:
            return OpenAIEmbeddingProvider(
                api_key=api_key,
                dimension=cfg.EMBEDDING_DIMENSION,
            )
        elif prov == "gemini" and api_key:
            return GeminiEmbeddingProvider(
                api_key=api_key,
                dimension=cfg.EMBEDDING_DIMENSION,
            )
        elif prov == "mock":
            return MockEmbeddingProvider(dimension=cfg.EMBEDDING_DIMENSION)

    if _embedding_instance is None:
        prov = cfg.EMBEDDING_PROVIDER.lower()
        if prov == "openai" and cfg.OPENAI_API_KEY:
            logger.info("Initializing live OpenAI embedding provider")
            _embedding_instance = OpenAIEmbeddingProvider(
                api_key=cfg.OPENAI_API_KEY,
                dimension=cfg.EMBEDDING_DIMENSION,
            )
        elif prov == "gemini" and cfg.GEMINI_API_KEY:
            logger.info("Initializing live Gemini embedding provider")
            _embedding_instance = GeminiEmbeddingProvider(
                api_key=cfg.GEMINI_API_KEY,
                dimension=cfg.EMBEDDING_DIMENSION,
            )
        else:
            logger.info("Using offline deterministic Mock embedding provider")
            _embedding_instance = MockEmbeddingProvider(dimension=cfg.EMBEDDING_DIMENSION)

    return _embedding_instance


def get_llm_provider(
    settings: Settings | None = None,
    provider_name: str | None = None,
    api_key: str | None = None,
    model: str | None = None,
) -> LLMProvider:
    """Returns configured LLM provider (OpenAI, Gemini, or Mock).

    Supports client-provided per-request API keys (BYOK) when api_key is supplied,
    falling back to cached server singletons otherwise.
    """
    global _llm_instance
    cfg = settings or get_settings()

    # If client passed an ephemeral API key, instantiate dynamically without mutating singleton
    if api_key or (provider_name and provider_name != cfg.LLM_PROVIDER):
        prov = (provider_name or cfg.LLM_PROVIDER).lower()
        if prov == "openai" and api_key:
            return OpenAILLMProvider(
                api_key=api_key,
                model=model or cfg.OPENAI_MODEL,
            )
        elif prov == "gemini" and api_key:
            return GeminiLLMProvider(
                api_key=api_key,
                model=model or cfg.GEMINI_MODEL,
            )
        elif prov == "mock":
            return MockLLMProvider()

    if _llm_instance is None:
        prov = cfg.LLM_PROVIDER.lower()
        if prov == "openai" and cfg.OPENAI_API_KEY:
            logger.info("Initializing live OpenAI LLM provider")
            _llm_instance = OpenAILLMProvider(
                api_key=cfg.OPENAI_API_KEY,
                model=cfg.OPENAI_MODEL,
            )
        elif prov == "gemini" and cfg.GEMINI_API_KEY:
            logger.info("Initializing live Gemini LLM provider")
            _llm_instance = GeminiLLMProvider(
                api_key=cfg.GEMINI_API_KEY,
                model=cfg.GEMINI_MODEL,
            )
        else:
            logger.info("Using offline deterministic Mock LLM provider")
            _llm_instance = MockLLMProvider()

    return _llm_instance
