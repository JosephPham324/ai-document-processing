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


def get_embedding_provider(settings: Settings | None = None) -> EmbeddingProvider:
    """Returns singleton configured embedding provider (OpenAI, Gemini, or Mock)."""
    global _embedding_instance
    if _embedding_instance is None:
        cfg = settings or get_settings()
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


def get_llm_provider(settings: Settings | None = None) -> LLMProvider:
    """Returns singleton configured LLM provider (OpenAI, Gemini, or Mock)."""
    global _llm_instance
    if _llm_instance is None:
        cfg = settings or get_settings()
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
