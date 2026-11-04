"""Standardized error handlers and custom application exceptions."""

import logging
import uuid
from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from docproc.schemas.common import ErrorDetail, ErrorResponse

logger = logging.getLogger(__name__)


class AppException(HTTPException):
    """Base application exception with structured error code and details."""

    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(status_code=status_code, detail=message)
        self.code = code
        self.message = message
        self.details = details or {}


class DocumentNotFoundException(AppException):
    def __init__(self, document_id: str) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="DOCUMENT_NOT_FOUND",
            message=f"Document '{document_id}' was not found.",
            details={"document_id": document_id},
        )


class UnsupportedMediaTypeException(AppException):
    def __init__(self, content_type: str, allowed: list[str]) -> None:
        super().__init__(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            code="UNSUPPORTED_MEDIA_TYPE",
            message=f"Unsupported file type '{content_type}'. Allowed: {', '.join(allowed)}",
            details={"content_type": content_type, "allowed": allowed},
        )


class FileTooLargeException(AppException):
    def __init__(self, size_bytes: int, max_bytes: int) -> None:
        super().__init__(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            code="FILE_TOO_LARGE",
            message=f"File size {size_bytes} bytes exceeds maximum allowed {max_bytes} bytes.",
            details={"size_bytes": size_bytes, "max_bytes": max_bytes},
        )


class DuplicateDocumentException(AppException):
    def __init__(self, document_id: str, checksum: str) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            code="DUPLICATE_DOCUMENT",
            message="Document with identical content has already been uploaded.",
            details={"document_id": document_id, "checksum": checksum},
        )


class ProviderUnavailableException(AppException):
    def __init__(self, provider: str, details: str = "Service unavailable") -> None:
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            code="PROVIDER_UNAVAILABLE",
            message=f"Upstream provider '{provider}' is currently unavailable.",
            details={"provider": provider, "info": details},
        )


class ProviderTimeoutException(AppException):
    def __init__(self, provider: str) -> None:
        super().__init__(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            code="PROVIDER_TIMEOUT",
            message=f"Timed out waiting for upstream provider '{provider}'.",
            details={"provider": provider},
        )


class WorkflowLimitExceededException(AppException):
    def __init__(self, reason: str) -> None:
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            code="WORKFLOW_LIMIT_EXCEEDED",
            message=f"Workflow limits exceeded: {reason}",
            details={"reason": reason},
        )


def get_request_id(request: Request) -> str:
    """Retrieve request_id from state or header or generate a fallback."""
    if hasattr(request.state, "request_id") and request.state.request_id:
        return str(request.state.request_id)
    header_val = request.headers.get("X-Request-ID")
    return header_val or f"req_{uuid.uuid4().hex[:12]}"


def register_error_handlers(app: FastAPI) -> None:
    """Register custom exception handlers with FastAPI application."""

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        req_id = get_request_id(request)
        error_resp = ErrorResponse(
            error=ErrorDetail(
                code=exc.code,
                message=exc.message,
                details=exc.details,
                request_id=req_id,
            )
        )
        return JSONResponse(status_code=exc.status_code, content=error_resp.model_dump())

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        req_id = get_request_id(request)
        code = "HTTP_ERROR"
        if exc.status_code == 404:
            code = "NOT_FOUND"
        elif exc.status_code == 400:
            code = "BAD_REQUEST"
        elif exc.status_code == 401:
            code = "UNAUTHORIZED"
        elif exc.status_code == 403:
            code = "FORBIDDEN"

        error_resp = ErrorResponse(
            error=ErrorDetail(
                code=code,
                message=str(exc.detail),
                details={},
                request_id=req_id,
            )
        )
        return JSONResponse(status_code=exc.status_code, content=error_resp.model_dump())

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        req_id = get_request_id(request)
        sanitized_errors = []
        for err in exc.errors():
            loc = " -> ".join(str(p) for p in err.get("loc", []))
            sanitized_errors.append({"field": loc, "issue": err.get("msg")})

        error_resp = ErrorResponse(
            error=ErrorDetail(
                code="VALIDATION_ERROR",
                message="Request payload validation failed.",
                details={"errors": sanitized_errors},
                request_id=req_id,
            )
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content=error_resp.model_dump(),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        req_id = get_request_id(request)
        logger.error(f"Unhandled exception [request_id={req_id}]: {exc}", exc_info=True)
        error_resp = ErrorResponse(
            error=ErrorDetail(
                code="INTERNAL_SERVER_ERROR",
                message="An unexpected server error occurred. Please contact support.",
                details={},
                request_id=req_id,
            )
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_resp.model_dump(),
        )
