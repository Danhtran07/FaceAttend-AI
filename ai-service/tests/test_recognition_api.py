import numpy as np
import pytest

from app.core.config import Settings
from app.core.errors import AIServiceError, ErrorCode
from app.core.schemas import MatchCandidate
from app.services.face_aligner import FaceAligner
from app.services.face_detector import FaceDetector
from app.services.face_embedder import FaceEmbedder
from app.services.face_engine import FaceDetectionResult, FaceEngine
from app.services.face_matcher import FaceMatchingService
from app.services.recognition import RecognitionService


class SingleFaceEngine(FaceEngine):
    def __init__(self, faces=None, settings=None):
        super().__init__(settings or Settings(embedding_dim=4, face_match_threshold=0.5))
        landmarks = np.array(
            [[70, 80], [130, 80], [100, 110], [80, 130], [120, 130]],
            dtype=np.float32,
        )
        default = FaceDetectionResult(
            bbox=[60.0, 50.0, 140.0, 150.0],
            confidence=0.98,
            landmarks=landmarks,
            aligned_face=np.ones((112, 112, 3), dtype=np.uint8) * 128,
            embedding=np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32),
        )
        self._faces = faces if faces is not None else [default]
        self._model_embedding_dim = 4

    def detect(self, image):
        return list(self._faces)

    def extract_embedding(self, aligned_face):
        feature = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32)
        self._model_embedding_dim = 4
        return feature


@pytest.fixture
def recognition_settings():
    return Settings(
        embedding_dim=4,
        face_match_threshold=0.5,
        min_face_size=20,
        min_blur_variance=10.0,
        aligned_face_size=112,
    )


@pytest.fixture
def recognition_service(recognition_settings):
    engine = SingleFaceEngine(settings=recognition_settings)
    return RecognitionService(
        engine=engine,
        detector=FaceDetector(engine=engine, settings=recognition_settings),
        aligner=FaceAligner(engine=engine, settings=recognition_settings),
        embedder=FaceEmbedder(engine=engine, settings=recognition_settings),
        matching=FaceMatchingService(settings=recognition_settings),
        settings=recognition_settings,
    )


def test_recognize_known_employee(recognition_service, sample_image_b64):
    result = recognition_service.recognize(
        sample_image_b64,
        [MatchCandidate(employee_id=123, embedding=[1.0, 0.0, 0.0, 0.0])],
        threshold=0.5,
    )
    assert result.recognized is True
    assert result.employee_id == 123
    assert result.confidence == pytest.approx(1.0)


def test_recognize_unknown_employee(recognition_service, sample_image_b64):
    with pytest.raises(AIServiceError) as exc_info:
        recognition_service.recognize(
            sample_image_b64,
            [MatchCandidate(employee_id=999, embedding=[0.0, 1.0, 0.0, 0.0])],
            threshold=0.5,
        )
    assert exc_info.value.code == ErrorCode.UNKNOWN_FACE
    assert exc_info.value.details["recognized"] is False
    assert exc_info.value.details["employee_id"] is None
    assert "confidence" in exc_info.value.details


def test_recognize_no_face(recognition_settings, sample_image_b64):
    engine = SingleFaceEngine(faces=[], settings=recognition_settings)
    service = RecognitionService(
        engine=engine,
        detector=FaceDetector(engine=engine, settings=recognition_settings),
        aligner=FaceAligner(engine=engine, settings=recognition_settings),
        embedder=FaceEmbedder(engine=engine, settings=recognition_settings),
        matching=FaceMatchingService(settings=recognition_settings),
        settings=recognition_settings,
    )
    with pytest.raises(AIServiceError) as exc_info:
        service.recognize(sample_image_b64, [])
    assert exc_info.value.code == ErrorCode.NO_FACE


def test_recognize_multiple_faces(recognition_settings, sample_image_b64):
    landmarks = np.array(
        [[70, 80], [130, 80], [100, 110], [80, 130], [120, 130]],
        dtype=np.float32,
    )
    faces = [
        FaceDetectionResult(bbox=[60, 50, 140, 150], confidence=0.95, landmarks=landmarks),
        FaceDetectionResult(bbox=[10, 10, 50, 50], confidence=0.85, landmarks=landmarks),
    ]
    engine = SingleFaceEngine(faces=faces, settings=recognition_settings)
    service = RecognitionService(
        engine=engine,
        detector=FaceDetector(engine=engine, settings=recognition_settings),
        aligner=FaceAligner(engine=engine, settings=recognition_settings),
        embedder=FaceEmbedder(engine=engine, settings=recognition_settings),
        matching=FaceMatchingService(settings=recognition_settings),
        settings=recognition_settings,
    )
    with pytest.raises(AIServiceError) as exc_info:
        service.recognize(sample_image_b64, [])
    assert exc_info.value.code == ErrorCode.MULTIPLE_FACES


def test_recognize_invalid_candidates(recognition_service, sample_image_b64):
    with pytest.raises(AIServiceError) as exc_info:
        recognition_service.recognize(
            sample_image_b64,
            [MatchCandidate(employee_id=1, embedding=[1.0, float("nan"), 0.0, 0.0])],
        )
    assert exc_info.value.code == ErrorCode.INVALID_EMBEDDING


def test_recognize_invalid_image(recognition_service, invalid_image_b64):
    with pytest.raises(AIServiceError) as exc_info:
        recognition_service.recognize(invalid_image_b64, [])
    assert exc_info.value.code == ErrorCode.INVALID_IMAGE
