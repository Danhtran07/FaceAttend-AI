from enum import Enum
from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse


class ErrorCode(str, Enum):
    NO_FACE = "NO_FACE"
    MULTIPLE_FACES = "MULTIPLE_FACES"
    UNKNOWN_FACE = "UNKNOWN_FACE"
    INVALID_IMAGE = "INVALID_IMAGE"
    INVALID_EMBEDDING = "INVALID_EMBEDDING"
    LOW_QUALITY = "LOW_QUALITY"
    MODEL_ERROR = "MODEL_ERROR"


class AIServiceError(Exception):
    def __init__(
        self,
        code: ErrorCode,
        message: str | None = None,
        details: dict[str, Any] | None = None,
        status_code: int = 400,
    ):
        self.code = code
        self.message = message or ERROR_MESSAGES[code]
        self.details = details or {}
        self.status_code = status_code
        super().__init__(self.message)


ERROR_MESSAGES = {
    ErrorCode.NO_FACE: "No face detected in the image",
    ErrorCode.MULTIPLE_FACES: "Multiple faces detected in the image",
    ErrorCode.UNKNOWN_FACE: "Face not recognized among registered employees",
    ErrorCode.INVALID_IMAGE: "Invalid or unreadable image",
    ErrorCode.INVALID_EMBEDDING: "Invalid face embedding vector",
    ErrorCode.LOW_QUALITY: "Image quality is too low for reliable recognition",
    ErrorCode.MODEL_ERROR: "AI model processing failed",
}


def build_error_response(
    code: ErrorCode,
    message: str | None = None,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "success": False,
        "error": {
            "code": code.value,
            "message": message or ERROR_MESSAGES[code],
            "details": details or {},
        },
    }


async def ai_service_error_handler(_request: Request, exc: AIServiceError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=build_error_response(exc.code, exc.message, exc.details),
    )
