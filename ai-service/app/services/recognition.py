from __future__ import annotations

from app.core.config import Settings, get_settings
from app.core.errors import AIServiceError, ErrorCode
from app.core.schemas import FaceRecognizeResponse, MatchCandidate
from app.services.face_aligner import FaceAligner
from app.services.face_detector import FaceDetector
from app.services.face_embedder import FaceEmbedder
from app.services.face_engine import FaceEngine, get_face_engine
from app.services.face_matcher import FaceMatchingService
from app.utils.image import decode_base64_image


class RecognitionService:
    """Orchestrate check-in recognition: one image → one employee.

    Flow:
        Image → Validate → Detect → Face count (0/1/>1)
        → Align → Embed → Match (Backend candidates) → Result

    Models are loaded once via the shared FaceEngine singleton.
    AI Service never accesses the database; Backend supplies candidates.
    """

    def __init__(
        self,
        *,
        engine: FaceEngine | None = None,
        detector: FaceDetector | None = None,
        aligner: FaceAligner | None = None,
        embedder: FaceEmbedder | None = None,
        matching: FaceMatchingService | None = None,
        settings: Settings | None = None,
    ):
        self.settings = settings or get_settings()
        self.engine = engine or get_face_engine()
        self.detector = detector or FaceDetector(engine=self.engine, settings=self.settings)
        self.aligner = aligner or FaceAligner(engine=self.engine, settings=self.settings)
        self.embedder = embedder or FaceEmbedder(engine=self.engine, settings=self.settings)
        self.matching = matching or FaceMatchingService(settings=self.settings)

    def recognize(
        self,
        image_data: str,
        candidates: list[MatchCandidate],
        threshold: float | None = None,
    ) -> FaceRecognizeResponse:
        image = decode_base64_image(image_data)

        # Attendance rule: one check-in → one employee (no auto face pick).
        face = self.detector.require_single_face(image, check_quality=True)

        self.aligner.align(image, face)
        embedding = self.embedder.embed(image, face)

        result = self.matching.match(embedding, candidates, threshold=threshold)

        if not result.recognized:
            raise AIServiceError(
                ErrorCode.UNKNOWN_FACE,
                details={
                    "recognized": False,
                    "employee_id": None,
                    "confidence": result.confidence,
                },
                status_code=404,
            )

        return FaceRecognizeResponse(
            recognized=True,
            employee_id=result.employee_id,
            confidence=result.confidence,
        )
