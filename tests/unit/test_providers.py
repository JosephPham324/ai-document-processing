"""Unit tests for live OpenAI and Gemini provider adapters."""

from unittest.mock import MagicMock, patch

import pytest

from docproc.providers.gemini_provider import GeminiEmbeddingProvider, GeminiLLMProvider
from docproc.providers.openai_provider import OpenAIEmbeddingProvider, OpenAILLMProvider


@pytest.mark.asyncio
async def test_openai_embedding_provider() -> None:
    provider = OpenAIEmbeddingProvider(api_key="test_key", dimension=1536)

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"data": [{"embedding": [0.1] * 1536}]}

    with patch("httpx.AsyncClient.post", return_value=mock_resp):
        vec = await provider.embed_query("test query")
        assert len(vec) == 1536
        assert vec[0] == 0.1


@pytest.mark.asyncio
async def test_openai_llm_provider() -> None:
    provider = OpenAILLMProvider(api_key="test_key", model="gpt-4o-mini")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": "Generated text response."}}]
    }

    with patch("httpx.AsyncClient.post", return_value=mock_resp):
        text = await provider.generate("Hello world")
        assert "Generated text response" in text


@pytest.mark.asyncio
async def test_gemini_embedding_provider() -> None:
    provider = GeminiEmbeddingProvider(api_key="test_key", dimension=768)

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"embeddings": [{"values": [0.05] * 768}]}

    with patch("httpx.AsyncClient.post", return_value=mock_resp):
        vec = await provider.embed_query("test query")
        assert len(vec) == 768
        assert vec[0] == 0.05


@pytest.mark.asyncio
async def test_gemini_llm_provider() -> None:
    provider = GeminiLLMProvider(api_key="test_key", model="gemini-1.5-flash")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "candidates": [{"content": {"parts": [{"text": "Gemini answer."}]}}]
    }

    with patch("httpx.AsyncClient.post", return_value=mock_resp):
        text = await provider.generate("Question", system_prompt="Be concise")
        assert "Gemini answer" in text
