"""Main FastAPI application factory and entrypoint."""

import logging
import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from docproc.api.error_handlers import register_error_handlers
from docproc.api.routers.documents import router as documents_router
from docproc.api.routers.health import router as health_router
from docproc.api.routers.query import router as query_router
from docproc.api.routers.ui import router as ui_router
from docproc.config import get_settings
from docproc.db.session import close_db

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("docproc")


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Middleware ensuring every request has a unique request_id for tracing."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        req_id = request.headers.get("X-Request-ID") or f"req_{uuid.uuid4().hex[:12]}"
        request.state.request_id = req_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = req_id
        return response


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan context manager handling startup and shutdown events."""
    settings = get_settings()
    logger.info(f"Starting Document Processing AI Agent [{settings.ENVIRONMENT}]")
    yield
    logger.info("Shutting down Document Processing AI Agent...")
    await close_db()
    logger.info("Database connections closed.")


def create_app() -> FastAPI:
    """Application factory for FastAPI service."""
    settings = get_settings()

    app = FastAPI(
        title="Document Processing AI Agent",
        description=(
            "Production-grade backend service accepting documents, retrieving evidence "
            "through RAG, orchestrating tools via LangGraph, and returning grounded answers."
        ),
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
        redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
    )

    # Add middlewares
    app.add_middleware(RequestIdMiddleware)

    # Register standardized error handlers
    register_error_handlers(app)

    # Include routers
    app.include_router(ui_router)
    app.include_router(health_router)
    app.include_router(documents_router)
    app.include_router(query_router)

    return app


app = create_app()
