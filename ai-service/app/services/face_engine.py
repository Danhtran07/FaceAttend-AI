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

    def extract_embedding(self, aligned_face: np.ndarray) -> np.ndarray:
        """Run InsightFace ArcFace on an already aligned face. No persistence."""
        try:
            app = self._get_app()
            rec_model = app.models.get("recognition")
            if rec_model is None:
                raise AIServiceError(
                    ErrorCode.MODEL_ERROR,
                    "InsightFace ArcFace recognition model is not available",
                    status_code=500,
                )
            feature = rec_model.get_feat(aligned_face)
        except AIServiceError:
            raise
        except Exception as exc:
            raise AIServiceError(
                ErrorCode.MODEL_ERROR,
                f"ArcFace embedding extraction failed: {exc}",
                status_code=500,
            ) from exc

        vector = np.asarray(feature, dtype=np.float32).flatten()
        if vector.size == 0:
            raise AIServiceError(
                ErrorCode.MODEL_ERROR,
                "ArcFace returned an empty embedding",
                status_code=500,
            )
        self._model_embedding_dim = int(vector.shape[0])
        return vector

    def model_embedding_dim(self) -> int:
        """Embedding length reported by the InsightFace recognition model."""
        cached = getattr(self, "_model_embedding_dim", None)
        if isinstance(cached, int) and cached > 0:
            return cached

        try:
            app = self._get_app()
            rec_model = app.models.get("recognition")
            if rec_model is not None and hasattr(rec_model, "session"):
                output_shape = rec_model.session.get_outputs()[0].shape
                dim = output_shape[-1]
                if isinstance(dim, int) and dim > 0:
                    self._model_embedding_dim = dim
                    return dim
        except AIServiceError:
            raise
        except Exception:
            pass

        return int(self.settings.embedding_dim)

    def get_embedding(self, image: np.ndarray, face: FaceDetectionResult) -> np.ndarray:
        from app.services.face_embedder import FaceEmbeddingService

        if face.aligned_face is None:
            if face.landmarks is None:
                raise AIServiceError(
                    ErrorCode.MODEL_ERROR,
                    "Cannot compute embedding without an aligned face",
                    status_code=500,
                )
            face.aligned_face = self._align_face(image, face.landmarks)

        service = FaceEmbeddingService(engine=self, settings=self.settings)
        return service.generate_embedding(face.aligned_face)


_engine: FaceEngine | None = None


def get_face_engine() -> FaceEngine:
    global _engine
    if _engine is None:
        _engine = FaceEngine()
    return _engine


def reset_face_engine() -> None:
    global _engine
    _engine = None
