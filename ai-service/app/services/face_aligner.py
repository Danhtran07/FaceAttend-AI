from __future__ import annotations

import numpy as np

from app.core.errors import AIServiceError, ErrorCode
from app.services.face_engine import FaceDetectionResult, FaceEngine, get_face_engine


class FaceAligner:
    def __init__(self, engine: FaceEngine | None = None):
        self.engine = engine or get_face_engine()

    def align(self, image: np.ndarray, face: FaceDetectionResult) -> np.ndarray:
        if face.landmarks is None:
            raise AIServiceError(
                ErrorCode.MODEL_ERROR,
                "Facial landmarks are not available for alignment",
                status_code=500,
            )

        if face.aligned_face is not None:
            return face.aligned_face

        aligned = self.engine._align_face(image, face.landmarks)
        face.aligned_face = aligned
        return aligned
