"""Live Google Gemini provider adapter for embeddings and completions."""

import logging
from typing import Any

import httpx

from docproc.api.error_handlers import ProviderTimeoutException, ProviderUnavailableException
from docproc.providers.base import EmbeddingProvider, LLMProvider

logger = logging.getLogger(__name__)


class GeminiEmbeddingProvider(EmbeddingProvider):
    """Generates embeddings using Google Gemini's embedContent endpoint."""

    def __init__(
        self,
        api_key: str,
        model: str = "text-embedding-004",
        dimension: int = 768,
        timeout_seconds: float = 15.0,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.dimension = dimension
        self.timeout_seconds = timeout_seconds
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        url = f"{self.base_url}/{self.model}:batchEmbedContents?key={self.api_key}"
        requests = [
            {"model": f"models/{self.model}", "content": {"parts": [{"text": t}]}} for t in texts
        ]
        payload = {"requests": requests}

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                res = await client.post(url, json=payload)
                if res.status_code != 200:
                    raise ProviderUnavailableException(
                        "gemini", f"Gemini HTTP {res.status_code}: {res.text}"
                    )
                data = res.json()
                return [item["values"] for item in data["embeddings"]]
        except httpx.TimeoutException as exc:
            raise ProviderTimeoutException("gemini") from exc
        except Exception as exc:
            if isinstance(exc, (ProviderUnavailableException, ProviderTimeoutException)):
                raise
            raise ProviderUnavailableException("gemini", str(exc)) from exc

    async def embed_query(self, text: str) -> list[float]:
        vectors = await self.embed_documents([text])
        return vectors[0]


class GeminiLLMProvider(LLMProvider):
    """Generates text using Google Gemini's generateContent endpoint."""

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-1.5-flash",
        timeout_seconds: float = 20.0,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"

    async def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        url = f"{self.base_url}/{self.model}:generateContent?key={self.api_key}"
        contents: list[dict[str, Any]] = []
        if system_prompt:
            contents.append(
                {"role": "user", "parts": [{"text": f"SYSTEM INSTRUCTIONS:\n{system_prompt}"}]}
            )
            contents.append(
                {
                    "role": "model",
                    "parts": [{"text": "Understood. I will follow these instructions."}],
                }
            )
        contents.append({"role": "user", "parts": [{"text": prompt}]})

        payload = {"contents": contents}

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                res = await client.post(url, json=payload)
                if res.status_code != 200:
                    raise ProviderUnavailableException(
                        "gemini", f"Gemini HTTP {res.status_code}: {res.text}"
                    )
                data = res.json()
                candidates = data.get("candidates", [])
                if not candidates:
                    return ""
                parts = candidates[0].get("content", {}).get("parts", [])
                return "".join(p.get("text", "") for p in parts)
        except httpx.TimeoutException as exc:
            raise ProviderTimeoutException("gemini") from exc
        except Exception as exc:
            if isinstance(exc, (ProviderUnavailableException, ProviderTimeoutException)):
                raise
            raise ProviderUnavailableException("gemini", str(exc)) from exc
