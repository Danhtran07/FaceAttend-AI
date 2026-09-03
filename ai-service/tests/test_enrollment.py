import numpy as np
import pytest

from app.core.config import Settings
from app.core.errors import AIServiceError, ErrorCode
from app.services.enrollment import EnrollmentService
from app.services.face_aligner import FaceAligner
from app.services.face_detector import FaceDetector
from app.services.face_embedder import FaceEmbedder
from app.services.face_engine import FaceDetectionResult, FaceEngine


class EnrollEngine(FaceEngine):
    def __init__(self, faces=None, settings=None):
        super().__init__(
            settings
            or Settings(
                embedding_dim=4,
                min_face_size=20,
                min_blur_variance=10.0,
                aligned_face_size=112,
            )
        )
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
def enroll_settings():
    return Settings(
        embedding_dim=4,
        min_face_size=20,
        min_blur_variance=10.0,
        aligned_face_size=112,
    )


def _service(faces, settings):
    engine = EnrollEngine(faces=faces, settings=settings)
    return EnrollmentService(
        engine=engine,
        detector=FaceDetector(engine=engine, settings=settings),
        aligner=FaceAligner(engine=engine, settings=settings),
        embedder=FaceEmbedder(engine=engine, settings=settings),
        settings=settings,
    )


def test_enroll_valid_face(enroll_settings, sample_image_b64):
    service = _service(None, enroll_settings)
    result = service.enroll(sample_image_b64)

    assert result.success is True
    assert isinstance(result.embedding, list)
    assert len(result.embedding) == 4
    assert result.dimension == 4
    assert result.confidence == pytest.approx(0.98)


def test_enroll_no_face(enroll_settings, sample_image_b64):
    service = _service([], enroll_settings)
    with pytest.raises(AIServiceError) as exc_info:
        service.enroll(sample_image_b64)
    assert exc_info.value.code == ErrorCode.NO_FACE


def test_enroll_multiple_faces(enroll_settings, sample_image_b64):
    landmarks = np.array(
        [[70, 80], [130, 80], [100, 110], [80, 130], [120, 130]],
        dtype=np.float32,
    )
    faces = [
        FaceDetectionResult(bbox=[60, 50, 140, 150], confidence=0.95, landmarks=landmarks),
        FaceDetectionResult(bbox=[10, 10, 50, 50], confidence=0.85, landmarks=landmarks),
    ]
    service = _service(faces, enroll_settings)
    with pytest.raises(AIServiceError) as exc_info:
        service.enroll(sample_image_b64)
    assert exc_info.value.code == ErrorCode.MULTIPLE_FACES


def test_enroll_invalid_image(enroll_settings, invalid_image_b64):
    service = _service(None, enroll_settings)
    with pytest.raises(AIServiceError) as exc_info:
        service.enroll(invalid_image_b64)
    assert exc_info.value.code == ErrorCode.INVALID_IMAGE


def test_enroll_embedding_output_shape(enroll_settings, sample_image_b64):
    service = _service(None, enroll_settings)
    result = service.enroll(sample_image_b64)
    assert all(isinstance(value, float) for value in result.embedding)
