from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import numpy as np

from app.core.config import Settings, get_settings
from app.core.errors import AIServiceError, ErrorCode

logger = logging.getLogger(__name__)


@dataclass
class FaceDetectionResult:
    bbox: list[float]
    confidence: float
    landmarks: np.ndarray | None = None
    aligned_face: np.ndarray | None = None
    embedding: np.ndarray | None = None


class FaceEngine:
    """InsightFace wrapper for SCRFD detection, alignment, and ArcFace embedding."""

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self._app: Any | None = None

    def _get_app(self) -> Any:
        if self._app is not None:
            return self._app

        try:
            from insightface.app import FaceAnalysis
        except ImportError as exc:
            raise AIServiceError(
                ErrorCode.MODEL_ERROR,
                "InsightFace is not installed",
                status_code=500,
            ) from exc

        try:
            app = FaceAnalysis(
                name=self.settings.model_name,
                providers=["CPUExecutionProvider"],
            )
            app.prepare(ctx_id=-1, det_size=(640, 640))
            self._app = app
            logger.info("Loaded InsightFace model: %s", self.settings.model_name)
        except Exception as exc:
            raise AIServiceError(
                ErrorCode.MODEL_ERROR,
                f"Failed to load InsightFace model: {exc}",
                status_code=500,
            ) from exc

        return self._app

    def detect(self, image: np.ndarray) -> list[FaceDetectionResult]:
        try:
            app = self._get_app()
            faces = app.get(image)
        except AIServiceError:
            raise
        except Exception as exc:
            raise AIServiceError(
                ErrorCode.MODEL_ERROR,
                f"Face detection failed: {exc}",
                status_code=500,
            ) from exc

        results: list[FaceDetectionResult] = []
        for face in faces:
            score = float(getattr(face, "det_score", 0.0))
            if score < self.settings.detection_threshold:
                continue

            bbox = face.bbox.astype(float).tolist()
            landmarks = getattr(face, "kps", None)
            embedding = getattr(face, "embedding", None)

            results.append(
                FaceDetectionResult(
                    bbox=bbox,
                    confidence=score,
                    landmarks=landmarks,
                    aligned_face=None,
                    embedding=embedding,
                )
            )

        results.sort(key=lambda item: item.confidence, reverse=True)
        return results

    def _align_face(self, image: np.ndarray, landmarks: np.ndarray) -> np.ndarray:
        from app.services.face_aligner import FaceAlignmentService

        return FaceAlignmentService(settings=self.settings).align(image, landmarks)

    def get_embedding(self, image: np.ndarray, face: FaceDetectionResult) -> np.ndarray:
        if face.embedding is not None:
            return self._normalize_embedding(face.embedding)

        if face.aligned_face is None:
            if face.landmarks is None:
                raise AIServiceError(
                    ErrorCode.MODEL_ERROR,
                    "Cannot compute embedding without landmarks",
                    status_code=500,
                )
            face.aligned_face = self._align_face(image, face.landmarks)

        try:
            app = self._get_app()
            rec_model = app.models.get("recognition")
            if rec_model is None:
                raise AIServiceError(
                    ErrorCode.MODEL_ERROR,
                    "Recognition model not available",
                    status_code=500,
                )
            embedding = rec_model.get_feat(face.aligned_face)
            return self._normalize_embedding(embedding)
        except AIServiceError:
            raise
        except Exception as exc:
            raise AIServiceError(
                ErrorCode.MODEL_ERROR,
                f"Embedding extraction failed: {exc}",
                status_code=500,
            ) from exc

    @staticmethod
    def _normalize_embedding(embedding: np.ndarray) -> np.ndarray:
        vector = np.asarray(embedding, dtype=np.float32).flatten()
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        return vector


_engine: FaceEngine | None = None


def get_face_engine() -> FaceEngine:
    global _engine
    if _engine is None:
        _engine = FaceEngine()
    return _engine


def reset_face_engine() -> None:
    global _engine
    _engine = None
