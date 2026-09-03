from __future__ import annotations

import numpy as np

from app.core.config import Settings, get_settings
from app.core.errors import NoFaceError, MultipleFacesError, LowQualityError
from app.core.schemas import DetectedFace
from app.services.face_engine import FaceDetectionResult, FaceEngine, get_face_engine
from app.utils.image import compute_blur_variance, compute_face_size


class FaceDetector:
    def __init__(self, engine: FaceEngine | None = None, settings: Settings | None = None):
        self.engine = engine or get_face_engine()
        self.settings = settings or get_settings()

    def detect(self, image: np.ndarray) -> list[DetectedFace]:
        faces = self.engine.detect(image)
        return [
            DetectedFace(bbox=face.bbox, confidence=face.confidence)
            for face in faces
        ]

    def detect_raw(self, image: np.ndarray) -> list[FaceDetectionResult]:
        return self.engine.detect(image)

    def require_single_face(
        self,
        image: np.ndarray,
        *,
        check_quality: bool = True,
    ) -> FaceDetectionResult:
        faces = self.engine.detect(image)

        if not faces:
            raise NoFaceError()

        if len(faces) > 1:
            raise MultipleFacesError(details={"face_count": len(faces)})

        face = faces[0]
        if check_quality:
            self._validate_quality(image, face)

        return face

    def select_primary_face(
        self,
        image: np.ndarray,
        *,
        check_quality: bool = True,
    ) -> FaceDetectionResult:
        faces = self.engine.detect(image)

        if not faces:
            raise NoFaceError()

        if len(faces) > 1 and not self.settings.allow_multiple_faces_recognition:
            raise MultipleFacesError(details={"face_count": len(faces)})

        face = faces[0]
        if check_quality:
            self._validate_quality(image, face)

        return face

    def _validate_quality(self, image: np.ndarray, face: FaceDetectionResult) -> None:
        x1, y1, x2, y2 = [int(v) for v in face.bbox]
        height, width = image.shape[:2]
        x1 = max(0, x1)
        y1 = max(0, y1)
        x2 = min(width, x2)
        y2 = min(height, y2)

        face_crop = image[y1:y2, x1:x2]
        if face_crop.size == 0:
            raise LowQualityError("Face crop is empty")

        face_width = x2 - x1
        face_height = y2 - y1
        if min(face_width, face_height) < self.settings.min_face_size:
            raise LowQualityError(
                "Face is too small in the image",
                details={
                    "face_width": face_width,
                    "face_height": face_height,
                    "min_face_size": self.settings.min_face_size,
                },
            )

        blur_variance = compute_blur_variance(face_crop)
        if blur_variance < self.settings.min_blur_variance:
            raise LowQualityError(
                "Face image is too blurry",
                details={
                    "blur_variance": round(blur_variance, 2),
                    "min_blur_variance": self.settings.min_blur_variance,
                },
            )

        face_area_ratio = compute_face_size(face.bbox) / float(width * height)
        if face_area_ratio < 0.01:
            raise LowQualityError(
                "Face occupies too little of the image",
                details={"face_area_ratio": round(face_area_ratio, 4)},
            )
