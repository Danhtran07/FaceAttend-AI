from __future__ import annotations

import numpy as np

from app.core.config import Settings, get_settings
from app.core.errors import AIServiceError, ErrorCode
from app.services.face_engine import FaceDetectionResult, FaceEngine, get_face_engine


class FaceEmbeddingService:
    """Convert an aligned face into an ArcFace embedding.

    Uses InsightFace's ArcFace recognition model. Does not train a model,
    does not invent vectors, and does not persist embeddings.
    Backend is responsible for storing the returned embedding.
    """

    DTYPE = np.float32

    def __init__(self, engine: FaceEngine | None = None, settings: Settings | None = None):
        self.engine = engine or get_face_engine()
        self.settings = settings or get_settings()

    def generate_embedding(self, aligned_face: np.ndarray) -> np.ndarray:
        self._validate_aligned_face(aligned_face)
        raw = self.engine.extract_embedding(aligned_face)
        vector = self.normalize(raw)
        self._validate_vector(vector)
        return vector

    def generate_embedding_list(self, aligned_face: np.ndarray) -> list[float]:
        return self.generate_embedding(aligned_face).astype(float).tolist()

    def normalize(self, embedding: np.ndarray) -> np.ndarray:
        vector = np.asarray(embedding, dtype=self.DTYPE).flatten()
        if vector.size == 0:
            raise AIServiceError(
                ErrorCode.MODEL_ERROR,
                "ArcFace returned an empty embedding",
                status_code=500,
            )
        if not np.isfinite(vector).all():
            raise AIServiceError(
                ErrorCode.MODEL_ERROR,
                "ArcFace returned a non-finite embedding",
                status_code=500,
            )
        norm = float(np.linalg.norm(vector))
        if norm == 0:
            raise AIServiceError(
                ErrorCode.MODEL_ERROR,
                "ArcFace returned a zero embedding",
                status_code=500,
            )
        return vector / np.float32(norm)

    def _validate_aligned_face(self, aligned_face: np.ndarray) -> None:
        if aligned_face is None or not isinstance(aligned_face, np.ndarray):
            raise AIServiceError(
                ErrorCode.INVALID_IMAGE,
                "Aligned face is empty or invalid",
                status_code=400,
            )
        if aligned_face.size == 0:
            raise AIServiceError(
                ErrorCode.INVALID_IMAGE,
                "Aligned face is empty",
                status_code=400,
            )
        if aligned_face.ndim != 3 or aligned_face.shape[2] != 3:
            raise AIServiceError(
                ErrorCode.INVALID_IMAGE,
                "Aligned face must be a 3-channel image",
                details={"shape": list(np.shape(aligned_face))},
                status_code=400,
            )

        expected = int(self.settings.aligned_face_size)
        height, width = aligned_face.shape[:2]
        if height != expected or width != expected:
            raise AIServiceError(
                ErrorCode.INVALID_IMAGE,
                "Aligned face size does not match ArcFace input",
                details={
                    "expected": [expected, expected, 3],
                    "actual": list(aligned_face.shape),
                },
                status_code=400,
            )

    def dimension(self) -> int:
        cached = getattr(self.engine, "_model_embedding_dim", None)
        if isinstance(cached, int) and cached > 0:
            return cached
        return int(self.settings.embedding_dim)

    def _validate_vector(self, vector: np.ndarray) -> None:
        expected_dim = self.dimension()
        if vector.ndim != 1:
            raise AIServiceError(
                ErrorCode.MODEL_ERROR,
                "Embedding must be a 1-D vector",
                details={"shape": list(vector.shape)},
                status_code=500,
            )
        if expected_dim > 0 and vector.shape[0] != expected_dim:
            raise AIServiceError(
                ErrorCode.MODEL_ERROR,
                "Embedding dimension does not match the recognition model",
                details={"expected": expected_dim, "actual": int(vector.shape[0])},
                status_code=500,
            )
        if vector.dtype != self.DTYPE:
            raise AIServiceError(
                ErrorCode.MODEL_ERROR,
                "Embedding dtype must be float32",
                details={"dtype": str(vector.dtype)},
                status_code=500,
            )


class FaceEmbedder:
    """Pipeline adapter: aligned face → FaceEmbeddingService."""

    def __init__(self, engine: FaceEngine | None = None, settings: Settings | None = None):
        self.engine = engine or get_face_engine()
        self.settings = settings or get_settings()
        self.service = FaceEmbeddingService(engine=self.engine, settings=self.settings)

    def embed(self, image: np.ndarray, face: FaceDetectionResult) -> list[float]:
        aligned = face.aligned_face
        if aligned is None:
            if face.landmarks is None:
                raise AIServiceError(
                    ErrorCode.MODEL_ERROR,
                    "Cannot compute embedding without an aligned face",
                    status_code=500,
                )
            aligned = self.engine._align_face(image, face.landmarks)
            face.aligned_face = aligned

        vector = self.service.generate_embedding(aligned)
        face.embedding = vector
        return vector.astype(float).tolist()
