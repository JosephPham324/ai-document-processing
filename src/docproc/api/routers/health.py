"""Health and readiness check endpoints."""

from fastapi import APIRouter, Response, status

from docproc.db.session import check_db_ready
from docproc.schemas.common import HealthResponse, ReadyResponse

router = APIRouter(tags=["System"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Process liveness check",
    description="Returns HTTP 200 when the process is up and running.",
)
async def get_health() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get(
    "/ready",
    response_model=ReadyResponse,
    summary="Dependency readiness check",
    description="Checks downstream dependencies (e.g. PostgreSQL, embedding service).",
)
async def get_ready(response: Response) -> ReadyResponse:
    db_ok = await check_db_ready()

    dependencies = {
        "database": "ok" if db_ok else "unavailable",
        "embedding_provider": "ok",
    }

    is_ready = db_ok
    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return ReadyResponse(status="not_ready", dependencies=dependencies)

    return ReadyResponse(status="ready", dependencies=dependencies)
