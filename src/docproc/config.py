"""Application configuration using Pydantic Settings."""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Global configuration settings for Document Processing AI Agent."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # General
    ENVIRONMENT: Literal["development", "production", "testing"] = "development"
    LOG_LEVEL: str = "INFO"
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/docproc",
        description="Async PostgreSQL connection string",
    )
    TEST_DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/docproc_test",
        description="Async PostgreSQL connection string for tests",
    )
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    # Ingestion & Documents
    MAX_FILE_SIZE_BYTES: int = Field(default=20 * 1024 * 1024, description="20 MB limit")
    ALLOWED_CONTENT_TYPES: list[str] = [
        "application/pdf",
        "text/plain",
        "text/markdown",
    ]
    DEFAULT_CHUNK_SIZE: int = 500
    DEFAULT_CHUNK_OVERLAP: int = 50

    # Retrieval & RAG
    DEFAULT_TOP_K: int = 5
    MAX_TOP_K: int = 20
    RELEVANCE_THRESHOLD: float = 0.25

    # Workflow Guardrails
    MAX_WORKFLOW_STEPS: int = 10
    MAX_TOOL_CALLS: int = 6
    TOOL_TIMEOUT_SECONDS: int = 15
    PROVIDER_MAX_RETRIES: int = 2

    # Providers & Models
    LLM_PROVIDER: Literal["mock", "openai", "gemini"] = "mock"
    EMBEDDING_PROVIDER: Literal["mock", "openai", "gemini"] = "mock"
    EMBEDDING_DIMENSION: int = 1536

    OPENAI_API_KEY: str | None = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    GEMINI_API_KEY: str | None = None
    GEMINI_MODEL: str = "gemini-1.5-flash"


@lru_cache
def get_settings() -> Settings:
    """Returns cached settings instance."""
    return Settings()
