import numpy as np
import pytest

from app.core.errors import AIServiceError, ErrorCode
from app.services.face_engine import FaceDetectionResult
from app.services.face_detector import FaceDetector
from app.services.face_engine import FaceEngine
from app.core.config import Settings


class MultiFaceEngine(FaceEngine):
    def __init__(self):
        super().__init__(Settings(embedding_dim=4, min_face_size=20, min_blur_variance=10.0))

    def detect(self, image):
        landmarks = np.array(
            [[70, 80], [130, 80], [100, 110], [80, 130], [120, 130]],
            dtype=np.float32,
        )
        return [
            FaceDetectionResult(
                bbox=[60, 50, 140, 150],
                confidence=0.95,
                landmarks=landmarks,
                embedding=np.array([1, 0, 0, 0], dtype=np.float32),
            ),
            FaceDetectionResult(
                bbox=[10, 10, 50, 50],
                confidence=0.85,
                landmarks=landmarks,
                embedding=np.array([0, 1, 0, 0], dtype=np.float32),
            ),
        ]


class EmptyEngine(FaceEngine):
    def detect(self, image):
        return []


def test_detect_returns_faces(mock_engine, sample_image_b64, pipeline):
    result = pipeline.detect_faces(sample_image_b64)
    assert result.success is True
    assert len(result.faces) == 1
    assert len(result.faces[0].bbox) == 4
    assert result.faces[0].confidence == pytest.approx(0.98)


def test_enroll_returns_embedding(pipeline, sample_image_b64):
    result = pipeline.enroll(sample_image_b64)
    assert result.success is True
    assert len(result.embedding) == 4
    assert result.dimension == 4
    assert result.confidence == pytest.approx(0.98)


def test_recognize_known_employee(pipeline, sample_image_b64):
    from app.core.schemas import RegisteredEmbedding

    result = pipeline.recognize(
        sample_image_b64,
        [RegisteredEmbedding(employee_id=123, embedding=[1.0, 0.0, 0.0, 0.0])],
        threshold=0.5,
    )
    assert result.recognized is True
    assert result.employee_id == 123
    assert result.confidence == pytest.approx(1.0)


def test_recognize_unknown_employee(pipeline, sample_image_b64):
    from app.core.schemas import RegisteredEmbedding

    with pytest.raises(AIServiceError) as exc_info:
        pipeline.recognize(
            sample_image_b64,
            [RegisteredEmbedding(employee_id=999, embedding=[0.0, 1.0, 0.0, 0.0])],
            threshold=0.5,
        )

    assert exc_info.value.code == ErrorCode.UNKNOWN_FACE


def test_no_face_error(sample_image_b64, settings):
    detector = FaceDetector(engine=EmptyEngine(), settings=settings)
    with pytest.raises(AIServiceError) as exc_info:
        detector.require_single_face(np.zeros((200, 200, 3), dtype=np.uint8))
    assert exc_info.value.code == ErrorCode.NO_FACE


def test_multiple_faces_error(sample_image_b64, settings):
    detector = FaceDetector(engine=MultiFaceEngine(), settings=settings)
    with pytest.raises(AIServiceError) as exc_info:
        detector.require_single_face(np.zeros((200, 200, 3), dtype=np.uint8))
    assert exc_info.value.code == ErrorCode.MULTIPLE_FACES
