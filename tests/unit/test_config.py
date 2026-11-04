"""Unit tests for application configuration."""

from docproc.config import Settings, get_settings


def test_settings_defaults() -> None:
    """Verifies default configuration values align with requirements."""
    settings = get_settings()
    assert settings.MAX_FILE_SIZE_BYTES == 20 * 1024 * 1024
    assert settings.DEFAULT_TOP_K == 5
    assert settings.MAX_TOP_K == 20
    assert settings.MAX_WORKFLOW_STEPS == 10
    assert settings.MAX_TOOL_CALLS == 6
    assert settings.TOOL_TIMEOUT_SECONDS == 15
    assert "application/pdf" in settings.ALLOWED_CONTENT_TYPES
    assert "text/plain" in settings.ALLOWED_CONTENT_TYPES
    assert "text/markdown" in settings.ALLOWED_CONTENT_TYPES


def test_custom_settings_override() -> None:
    """Verifies that custom settings can be instantiated with custom values."""
    custom = Settings(MAX_TOP_K=15, LOG_LEVEL="DEBUG")
    assert custom.MAX_TOP_K == 15
    assert custom.LOG_LEVEL == "DEBUG"
