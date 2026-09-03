from __future__ import annotations

import numpy as np

from app.core.config import Settings, get_settings
from app.core.errors import AIServiceError, ErrorCode
from app.services.face_engine import FaceDetectionResult, FaceEngine, get_face_engine


class FaceEmbedder:
    def __init__(self, engine: FaceEngine | None = None, settings: Settings | None = None):
        self.engine = engine or get_face_engine()
        self.settings = settings or get_settings()

    def embed(self, image: np.ndarray, face: FaceDetectionResult) -> list[float]:
        vector = self.engine.get_embedding(image, face)
        embedding = vector.astype(float).tolist()

        if len(embedding) != self.settings.embedding_dim:
            raise AIServiceError(
                ErrorCode.MODEL_ERROR,
                "Embedding dimension mismatch",
                details={
                    "expected": self.settings.embedding_dim,
                    "actual": len(embedding),
                },
                status_code=500,
            )

        return embedding
