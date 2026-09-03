from __future__ import annotations

import logging
from enum import Enum
from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("ai-service.errors")

SENSITIVE_DETAIL_KEYS = {
    "password",
    "token",
    "jwt",
    "secret",
    "authorization",
    "api_key",
    "apikey",
    "embedding",
    "embeddings",
    "image",
    "raw_image",
    "path",
    "traceback",
    "stack",
    "connection_string",
    "database_url",
}


class ErrorCode(str, Enum):
    NO_FACE = "NO_FACE"
    MULTIPLE_FACES = "MULTIPLE_FACES"
    UNKNOWN_FACE = "UNKNOWN_FACE"
    INVALID_IMAGE = "INVALID_IMAGE"
    LOW_QUALITY = "LOW_QUALITY"
    MODEL_ERROR = "MODEL_ERROR"
    INVALID_EMBEDDING = "INVALID_EMBEDDING"
    INVALID_REQUEST = "INVALID_REQUEST"


ERROR_MESSAGES = {
    ErrorCode.NO_FACE: "No face detected",
    ErrorCode.MULTIPLE_FACES: "Multiple faces detected",
    ErrorCode.UNKNOWN_FACE: "No matching employee",
    ErrorCode.INVALID_IMAGE: "Invalid image",
    ErrorCode.LOW_QUALITY: "Poor face quality",
    ErrorCode.MODEL_ERROR: "Model inference error",
    ErrorCode.INVALID_EMBEDDING: "Invalid embedding",
    ErrorCode.INVALID_REQUEST: "Invalid request",
}

DEFAULT_STATUS = {
    ErrorCode.NO_FACE: 400,
    ErrorCode.MULTIPLE_FACES: 400,
    ErrorCode.UNKNOWN_FACE: 404,
    ErrorCode.INVALID_IMAGE: 400,
    ErrorCode.LOW_QUALITY: 400,
    ErrorCode.MODEL_ERROR: 500,
    ErrorCode.INVALID_EMBEDDING: 400,
    ErrorCode.INVALID_REQUEST: 422,
}


class AIServiceError(Exception):
    """Base AI service error. Prefer typed subclasses in new code."""

    code: ErrorCode = ErrorCode.MODEL_ERROR

    def __init__(
        self,
        code: ErrorCode | None = None,
        message: str | None = None,
        details: dict[str, Any] | None = None,
        status_code: int | None = None,
    ):
        self.code = code or self.code
        self.message = message or ERROR_MESSAGES[self.code]
        self.details = details
        self.status_code = status_code or DEFAULT_STATUS[self.code]
        super().__init__(self.message)


class NoFaceError(AIServiceError):
    code = ErrorCode.NO_FACE

    def __init__(self, message: str | None = None, details: dict[str, Any] | None = None):
        super().__init__(ErrorCode.NO_FACE, message, details)


class MultipleFacesError(AIServiceError):
    code = ErrorCode.MULTIPLE_FACES

    def __init__(self, message: str | None = None, details: dict[str, Any] | None = None):
        super().__init__(ErrorCode.MULTIPLE_FACES, message, details)


class UnknownFaceError(AIServiceError):
    code = ErrorCode.UNKNOWN_FACE

    def __init__(self, message: str | None = None, details: dict[str, Any] | None = None):
        super().__init__(ErrorCode.UNKNOWN_FACE, message, details)


class InvalidImageError(AIServiceError):
    code = ErrorCode.INVALID_IMAGE

    def __init__(self, message: str | None = None, details: dict[str, Any] | None = None):
        super().__init__(ErrorCode.INVALID_IMAGE, message, details)


class LowQualityError(AIServiceError):
    code = ErrorCode.LOW_QUALITY

    def __init__(self, message: str | None = None, details: dict[str, Any] | None = None):
        super().__init__(ErrorCode.LOW_QUALITY, message, details)


class ModelError(AIServiceError):
    code = ErrorCode.MODEL_ERROR

    def __init__(self, message: str | None = None, details: dict[str, Any] | None = None):
        super().__init__(ErrorCode.MODEL_ERROR, message, details)


class InvalidEmbeddingError(AIServiceError):
    code = ErrorCode.INVALID_EMBEDDING

    def __init__(self, message: str | None = None, details: dict[str, Any] | None = None):
        super().__init__(ErrorCode.INVALID_EMBEDDING, message, details)


class InvalidRequestError(AIServiceError):
    code = ErrorCode.INVALID_REQUEST

    def __init__(self, message: str | None = None, details: dict[str, Any] | None = None):
        super().__init__(ErrorCode.INVALID_REQUEST, message, details)


def sanitize_details(details: dict[str, Any] | None) -> dict[str, Any] | None:
    """Drop secrets / large payloads before returning to clients."""
    if not details:
        return None

    cleaned: dict[str, Any] = {}
    for key, value in details.items():
        lowered = str(key).lower()
        if lowered in SENSITIVE_DETAIL_KEYS or any(s in lowered for s in ("password", "token", "secret", "jwt")):
            continue
        if isinstance(value, (list, tuple)) and len(value) > 32:
            cleaned[key] = f"<omitted len={len(value)}>"
            continue
        if isinstance(value, str) and len(value) > 256:
            cleaned[key] = value[:64] + "…"
            continue
        cleaned[key] = value
    return cleaned or None


def build_error_response(
    code: ErrorCode,
    message: str | None = None,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Standard AI error payload for Backend ↔ AI Service."""
    return {
        "success": False,
        "error_code": code.value,
        "message": message or ERROR_MESSAGES[code],
        "details": sanitize_details(details),
    }


def register_exception_handlers(app) -> None:
    """Attach centralized handlers once on the FastAPI app."""

    @app.exception_handler(AIServiceError)
    async def _ai_service_error_handler(request: Request, exc: AIServiceError) -> JSONResponse:
        logger.warning(
            "AIServiceError code=%s status=%s path=%s method=%s",
            exc.code.value,
            exc.status_code,
            request.url.path,
            request.method,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=build_error_response(exc.code, exc.message, exc.details),
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        safe_errors = []
        for item in exc.errors():
            safe_errors.append(
                {
                    "loc": [str(part) for part in item.get("loc", ()) if part != "body"],
                    "type": item.get("type"),
                    "msg": item.get("msg"),
                }
            )
        logger.warning(
            "INVALID_REQUEST path=%s method=%s issues=%s",
            request.url.path,
            request.method,
            len(safe_errors),
        )
        return JSONResponse(
            status_code=422,
            content=build_error_response(
                ErrorCode.INVALID_REQUEST,
                ERROR_MESSAGES[ErrorCode.INVALID_REQUEST],
                {"issues": safe_errors} if safe_errors else None,
            ),
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        logger.warning(
            "HTTPException status=%s path=%s method=%s",
            exc.status_code,
            request.url.path,
            request.method,
        )
        code = ErrorCode.INVALID_REQUEST if exc.status_code < 500 else ErrorCode.MODEL_ERROR
        message = ERROR_MESSAGES[code]
        if isinstance(exc.detail, str) and exc.detail and "traceback" not in exc.detail.lower():
            # Keep short public detail; never pass raw exception dumps.
            message = exc.detail[:200]
        return JSONResponse(
            status_code=exc.status_code,
            content=build_error_response(code, message, None),
        )

    @app.exception_handler(Exception)
    async def _unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception(
            "Unhandled error path=%s method=%s type=%s",
            request.url.path,
            request.method,
            type(exc).__name__,
        )
        return JSONResponse(
            status_code=500,
            content=build_error_response(
                ErrorCode.MODEL_ERROR,
                ERROR_MESSAGES[ErrorCode.MODEL_ERROR],
                None,
            ),
        )


# Backwards-compatible alias used by older imports / tests.
async def ai_service_error_handler(request: Request, exc: AIServiceError) -> JSONResponse:
    logger.warning(
        "AIServiceError code=%s status=%s path=%s method=%s",
        exc.code.value,
        exc.status_code,
        request.url.path,
        request.method,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=build_error_response(exc.code, exc.message, exc.details),
    )
