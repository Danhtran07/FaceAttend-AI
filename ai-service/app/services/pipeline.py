from __future__ import annotations

import numpy as np

from app.core.errors import AIServiceError, ErrorCode
from app.core.schemas import (
    FaceDetectionResponse,
    FaceEnrollResponse,
    FaceRecognizeResponse,
    RegisteredEmbedding,
)
from app.services.face_aligner import FaceAligner
from app.services.face_detector import FaceDetector
from app.services.face_embedder import FaceEmbedder
from app.services.face_matcher import FaceMatcher
from app.utils.image import decode_base64_image


class FacePipeline:
    def __init__(
        self,
        detector: FaceDetector | None = None,
        aligner: FaceAligner | None = None,
        embedder: FaceEmbedder | None = None,
        matcher: FaceMatcher | None = None,
    ):
        self.detector = detector or FaceDetector()
        self.aligner = aligner or FaceAligner()
        self.embedder = embedder or FaceEmbedder()
        self.matcher = matcher or FaceMatcher()

    def detect_faces(self, image_data: str) -> FaceDetectionResponse:
        image = decode_base64_image(image_data)
        faces = self.detector.detect(image)
        return FaceDetectionResponse(faces=faces)

    def enroll(self, image_data: str) -> FaceEnrollResponse:
        image = decode_base64_image(image_data)
        face = self.detector.require_single_face(image, check_quality=True)
        self.aligner.align(image, face)
        embedding = self.embedder.embed(image, face)

        return FaceEnrollResponse(
            embedding=embedding,
            dimension=len(embedding),
            bbox=face.bbox,
            confidence=face.confidence,
        )

    def recognize(
        self,
        image_data: str,
        registered_embeddings: list[RegisteredEmbedding],
        threshold: float | None = None,
    ) -> FaceRecognizeResponse:
        image = decode_base64_image(image_data)
        face = self.detector.select_primary_face(image, check_quality=True)
        self.aligner.align(image, face)
        embedding = self.embedder.embed(image, face)

        recognized, employee_id, confidence = self.matcher.match(
            embedding,
            registered_embeddings,
            threshold=threshold,
        )

        if not recognized:
            raise AIServiceError(
                ErrorCode.UNKNOWN_FACE,
                details={"best_similarity": round(confidence, 4)},
                status_code=404,
            )

        return FaceRecognizeResponse(
            recognized=True,
            employee_id=employee_id,
            confidence=round(confidence, 4),
            face_count=1,
        )
