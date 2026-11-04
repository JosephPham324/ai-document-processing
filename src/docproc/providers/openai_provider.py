"""Live OpenAI provider adapter for embeddings and chat completions."""

import logging

import httpx

from docproc.api.error_handlers import ProviderTimeoutException, ProviderUnavailableException
from docproc.providers.base import EmbeddingProvider, LLMProvider

logger = logging.getLogger(__name__)


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """Generates embeddings using OpenAI's /v1/embeddings endpoint."""

    def __init__(
        self,
        api_key: str,
        model: str = "text-embedding-3-small",
        dimension: int = 1536,
        timeout_seconds: float = 15.0,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.dimension = dimension
        self.timeout_seconds = timeout_seconds
        self.base_url = "https://api.openai.com/v1"

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "input": texts,
            "dimensions": self.dimension,
        }
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                res = await client.post(
                    f"{self.base_url}/embeddings", json=payload, headers=headers
                )
                if res.status_code != 200:
                    raise ProviderUnavailableException(
                        "openai", f"OpenAI HTTP {res.status_code}: {res.text}"
                    )
                data = res.json()
                return [item["embedding"] for item in data["data"]]
        except httpx.TimeoutException as exc:
            raise ProviderTimeoutException("openai") from exc
        except Exception as exc:
            if isinstance(exc, (ProviderUnavailableException, ProviderTimeoutException)):
                raise
            raise ProviderUnavailableException("openai", str(exc)) from exc

    async def embed_query(self, text: str) -> list[float]:
        vectors = await self.embed_documents([text])
        return vectors[0]


class OpenAILLMProvider(LLMProvider):
    """Generates completions using OpenAI's /v1/chat/completions endpoint."""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        timeout_seconds: float = 20.0,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.base_url = "https://api.openai.com/v1"

    async def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.0,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                res = await client.post(
                    f"{self.base_url}/chat/completions", json=payload, headers=headers
                )
                if res.status_code != 200:
                    raise ProviderUnavailableException(
                        "openai", f"OpenAI HTTP {res.status_code}: {res.text}"
                    )
                data = res.json()
                return str(data["choices"][0]["message"]["content"])
        except httpx.TimeoutException as exc:
            raise ProviderTimeoutException("openai") from exc
        except Exception as exc:
            if isinstance(exc, (ProviderUnavailableException, ProviderTimeoutException)):
                raise
            raise ProviderUnavailableException("openai", str(exc)) from exc
