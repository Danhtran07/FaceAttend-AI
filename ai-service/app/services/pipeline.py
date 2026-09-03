from __future__ import annotations

from app.core.schemas import (
    FaceDetectionResponse,
    FaceEnrollResponse,
    FaceRecognizeResponse,
    MatchCandidate,
    RegisteredEmbedding,
)
from app.services.enrollment import EnrollmentService
from app.services.face_aligner import FaceAligner
from app.services.face_detector import FaceDetector
from app.services.face_embedder import FaceEmbedder
from app.services.face_matcher import FaceMatcher
from app.services.recognition import RecognitionService
from app.utils.image import decode_base64_image


class FacePipeline:
    """Shared Detection → Alignment → Embedding → Matching pipeline.

    Enrollment and recognition reuse the same Detector / Alignment / Embedding.
    Matching uses Backend-supplied candidates only. No database access.
    """

    def __init__(
        self,
        detector: FaceDetector | None = None,
        aligner: FaceAligner | None = None,
        embedder: FaceEmbedder | None = None,
        matcher: FaceMatcher | None = None,
        recognition: RecognitionService | None = None,
        enrollment: EnrollmentService | None = None,
    ):
        self.detector = detector or FaceDetector()
        self.aligner = aligner or FaceAligner()
        self.embedder = embedder or FaceEmbedder()
        self.matcher = matcher or FaceMatcher()
        self.recognition = recognition
        self.enrollment = enrollment

    def detect_faces(self, image_data: str) -> FaceDetectionResponse:
        image = decode_base64_image(image_data)
        faces = self.detector.detect(image)
        return FaceDetectionResponse(faces=faces)

    def enroll(self, image_data: str) -> FaceEnrollResponse:
        if self.enrollment is not None:
            return self.enrollment.enroll(image_data)

        service = EnrollmentService(
            engine=self.detector.engine,
            detector=self.detector,
            aligner=self.aligner,
            embedder=self.embedder,
            settings=self.embedder.settings,
        )
        return service.enroll(image_data)

    def recognize(
        self,
        image_data: str,
        registered_embeddings: list[RegisteredEmbedding] | list[MatchCandidate],
        threshold: float | None = None,
    ) -> FaceRecognizeResponse:
        candidates = [
            item
            if isinstance(item, MatchCandidate)
            else MatchCandidate(employee_id=item.employee_id, embedding=item.embedding)
            for item in registered_embeddings
        ]

        if self.recognition is not None:
            return self.recognition.recognize(image_data, candidates, threshold=threshold)

        service = RecognitionService(
            engine=self.detector.engine,
            detector=self.detector,
            aligner=self.aligner,
            embedder=self.embedder,
            matching=self.matcher.service,
            settings=self.matcher.service.settings,
        )
        return service.recognize(image_data, candidates, threshold=threshold)
