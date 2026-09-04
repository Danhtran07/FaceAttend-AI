"""Standalone face AI API. Models load once at startup. No Backend or Database."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

import config
from schemas.face import AnalyzeResponse, HealthResponse
from services.image_io import InvalidImageError
from services.pipeline import get_pipeline
from services.runtime import ModelLoadError, runtime

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("ai_service")


class LimitBodySize(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > config.MAX_UPLOAD_BYTES:
            return JSONResponse({"detail": "Request body too large (max 10 MB)."}, status_code=413)
        return await call_next(request)


@asynccontextmanager
async def lifespan(app: FastAPI):
    runtime.load()
    get_pipeline()
    logger.info("AI service ready")
    yield
    runtime.close()
    logger.info("AI service shut down")


app = FastAPI(
    title="FaceAttend AI Service",
    description="Standalone face detection, mesh, embedding, and recognition",
    version="1.0.0",
    lifespan=lifespan,
)
app.add_middleware(LimitBodySize)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(InvalidImageError)
async def invalid_image_handler(_request: Request, exc: InvalidImageError):
    return JSONResponse(
        status_code=400,
        content=AnalyzeResponse(success=False, error=str(exc)).model_dump(),
    )


@app.exception_handler(ModelLoadError)
async def model_load_handler(_request: Request, exc: ModelLoadError):
    return JSONResponse(
        status_code=500,
        content=AnalyzeResponse(success=False, error=str(exc)).model_dump(),
    )


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok" if runtime.loaded else "not_ready",
        models_loaded=runtime.loaded,
        insightface=config.INSIGHTFACE_MODEL_NAME if runtime.loaded else None,
        face_mesh="face_landmarker" if runtime.loaded else None,
        details={
            "detection_size": list(config.DETECTION_SIZE),
            "similarity_threshold": config.SIMILARITY_THRESHOLD,
            "cpu": True,
        },
    )


async def _read_upload(file: Optional[UploadFile]) -> bytes | None:
    if file is None:
        return None
    data = await file.read()
    return data or None


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(
    file: Optional[UploadFile] = File(default=None),
    image: Optional[UploadFile] = File(default=None),
    reference: Optional[UploadFile] = File(default=None),
    image_b64: Optional[str] = Form(default=None),
):
    """
    Run the full pipeline on one image.

    Send multipart field `file` or `image` (JPEG/PNG).
    Optional `reference` image enables 1:1 identity + cosine similarity.
    Multiple faces in one image are compared to each other.
    """
    image_bytes = await _read_upload(file) or await _read_upload(image)
    if image_bytes is None and image_b64:
        from services.image_io import decode_base64_image
        import cv2

        frame = decode_base64_image(image_b64)
        ok, encoded = cv2.imencode(".jpg", frame)
        if not ok:
            raise HTTPException(status_code=400, detail="Could not encode image")
        image_bytes = encoded.tobytes()

    if not image_bytes:
        raise HTTPException(
            status_code=422,
            detail="Provide an image via multipart field 'file' / 'image', or form field 'image_b64'.",
        )

    try:
        reference_bytes = await _read_upload(reference)
        return get_pipeline().analyze(image_bytes, reference_bytes=reference_bytes)
    except InvalidImageError:
        raise
    except Exception as exc:
        logger.exception("Pipeline failed")
        return AnalyzeResponse(success=False, error=f"Model error: {exc}")
