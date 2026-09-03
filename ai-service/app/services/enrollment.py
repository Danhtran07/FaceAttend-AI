from __future__ import annotations

from app.core.config import Settings, get_settings
from app.core.schemas import FaceEnrollResponse
from app.services.face_aligner import FaceAligner
from app.services.face_detector import FaceDetector
from app.services.face_embedder import FaceEmbedder
from app.services.face_engine import FaceEngine, get_face_engine
from app.utils.image import decode_base64_image


class EnrollmentService:
    """Process employee face enrollment images.

    Flow:
        Image → Detect → Exactly one face → Align → Embed → Return embedding

    Uses the same Detector / Alignment / Embedding stack as RecognitionService.
    Does not create employees, touch PostgreSQL, or persist embeddings.
    Backend stores the returned vector.
    """

    def __init__(
        self,
        *,
        engine: FaceEngine | None = None,
        detector: FaceDetector | None = None,
        aligner: FaceAligner | None = None,
        embedder: FaceEmbedder | None = None,
        settings: Settings | None = None,
    ):
        self.settings = settings or get_settings()
        self.engine = engine or get_face_engine()
        self.detector = detector or FaceDetector(engine=self.engine, settings=self.settings)
        self.aligner = aligner or FaceAligner(engine=self.engine, settings=self.settings)
        self.embedder = embedder or FaceEmbedder(engine=self.engine, settings=self.settings)

    def enroll(self, image_data: str) -> FaceEnrollResponse:
        image = decode_base64_image(image_data)

        # Enrollment rule: exactly one face (no auto face pick).
        face = self.detector.require_single_face(image, check_quality=True)

        self.aligner.align(image, face)
        embedding = self.embedder.embed(image, face)

        return FaceEnrollResponse(
            success=True,
            embedding=embedding,
            dimension=len(embedding),
            bbox=face.bbox,
            confidence=face.confidence,
        )
