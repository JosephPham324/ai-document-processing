FROM python:3.12-slim AS builder

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Install uv
COPY --from=ghcr.io/astral-sh/uv:0.11.24 /uv /bin/uv

# Install system dependencies (e.g. for PyMuPDF or asyncpg if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy pyproject.toml and lockfile
COPY pyproject.toml uv.lock* ./

# Install dependencies into virtual environment
RUN uv sync --frozen --no-dev --no-install-project || uv sync --no-dev --no-install-project

# Copy application source
COPY src/ ./src/
COPY alembic/ ./alembic/
COPY alembic.ini ./

# Final runtime stage
FROM python:3.12-slim AS runtime

WORKDIR /app

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

# Copy venv and application from builder
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app /app

EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && uvicorn docproc.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
