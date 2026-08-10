"""Application exceptions and a consistent API error envelope.

Every error surfaces to the client as:

    {"error": {"code": "<CODE>", "message": "<safe message>", "request_id": "<id>"}}

Details (stack traces, internal context) are never exposed to clients.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, cast

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging import logger


class AppError(Exception):
    """Base class for application-level errors.

    - ``code``: stable machine-readable error code (e.g. ``VAULT_ACCESS_DENIED``).
    - ``status_code``: HTTP status to return.
    - ``message``: safe, user-facing message (never includes internals).
    """

    code: str = "INTERNAL_ERROR"
    status_code: int = 500

    def __init__(self, message: str, *, code: str | None = None, status_code: int | None = None):
        super().__init__(message)
        self.message = message
        if code is not None:
            self.code = code
        if status_code is not None:
            self.status_code = status_code


class NotFoundError(AppError):
    code = "NOT_FOUND"
    status_code = 404


class ConflictError(AppError):
    code = "CONFLICT"
    status_code = 409


class ValidationAppError(AppError):
    code = "VALIDATION_ERROR"
    status_code = 422


class UnauthorizedError(AppError):
    code = "UNAUTHORIZED"
    status_code = 401


class ForbiddenError(AppError):
    code = "FORBIDDEN"
    status_code = 403


class RateLimitError(AppError):
    code = "RATE_LIMITED"
    status_code = 429


def _error_body(request_id: str, code: str, message: str) -> dict[str, Any]:
    return {"error": {"code": code, "message": message, "request_id": request_id}}


def _request_id(request: Request) -> str:
    return request.headers.get("X-Request-ID", "")


def _handle_app_error(request: Request, exc: AppError) -> JSONResponse:
    logger.warning(
        "app_error",
        code=exc.code,
        status_code=exc.status_code,
        path=request.url.path,
        request_id=_request_id(request),
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_body(_request_id(request), exc.code, exc.message),
    )


def _handle_http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    logger.warning(
        "http_error",
        status_code=exc.status_code,
        path=request.url.path,
        request_id=_request_id(request),
    )
    message = str(exc.detail) if exc.detail else "Request failed"
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_body(_request_id(request), f"HTTP_{exc.status_code}", message),
    )


def _handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    logger.info(
        "validation_error",
        path=request.url.path,
        request_id=_request_id(request),
        errors=exc.errors(),
    )
    first = exc.errors()[0] if exc.errors() else {}
    loc = ".".join(str(part) for part in first.get("loc", []))
    message = f"Invalid input: {first.get('msg', 'validation failed')} (at {loc})"
    return JSONResponse(
        status_code=422,
        content=_error_body(_request_id(request), "VALIDATION_ERROR", message),
    )


def _handle_unexpected(request: Request, exc: Exception) -> JSONResponse:
    logger.exception(
        "unhandled_error",
        path=request.url.path,
        request_id=_request_id(request),
        error=type(exc).__name__,
    )
    return JSONResponse(
        status_code=500,
        content=_error_body(_request_id(request), "INTERNAL_ERROR", "An unexpected error occurred"),
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Attach all exception handlers to the FastAPI application.

    Handlers are cast to Starlette's ``ExceptionHandler`` signature so mypy accepts
    narrowed handler types.
    """
    handler_type = Callable[[Request, Exception], JSONResponse]

    app.add_exception_handler(AppError, cast(handler_type, _handle_app_error))
    app.add_exception_handler(StarletteHTTPException, cast(handler_type, _handle_http_error))
    app.add_exception_handler(RequestValidationError, cast(handler_type, _handle_validation_error))
    app.add_exception_handler(Exception, cast(handler_type, _handle_unexpected))
