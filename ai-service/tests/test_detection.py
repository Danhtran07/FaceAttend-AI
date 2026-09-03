import numpy as np
import pytest

from app.core.config import Settings
from app.core.errors import AIServiceError, ErrorCode
from app.services.face_detector import FaceDetector
from app.services.face_engine import FaceDetectionResult, FaceEngine
from app.services.pipeline import FacePipeline
from app.utils.image import decode_base64_image


class DetectEngine(FaceEngine):
    def __init__(self, faces, settings=None):
        super().__init__(settings or Settings(embedding_dim=4, min_face_size=20, min_blur_variance=10.0))
        self._faces = faces

    def detect(self, image):
        return list(self._faces)


def _face(bbox, score=0.95):
    landmarks = np.array(
        [[70, 80], [130, 80], [100, 110], [80, 130], [120, 130]],
        dtype=np.float32,
    )
    return FaceDetectionResult(bbox=bbox, confidence=score, landmarks=landmarks)


def test_detection_one_face(settings, sample_image_b64):
    engine = DetectEngine([_face([60, 50, 140, 150], 0.98)], settings)
    pipeline = FacePipeline(detector=FaceDetector(engine=engine, settings=settings))
    result = pipeline.detect_faces(sample_image_b64)
    assert result.success is True
    assert len(result.faces) == 1
    assert result.faces[0].confidence == pytest.approx(0.98)


def test_detection_multiple_faces(settings):
    engine = DetectEngine(
        [
            _face([60, 50, 140, 150], 0.95),
            _face([10, 10, 50, 50], 0.85),
        ],
        settings,
    )
    detector = FaceDetector(engine=engine, settings=settings)
    image = np.zeros((200, 200, 3), dtype=np.uint8)
    faces = detector.detect(image)
    assert len(faces) == 2
    with pytest.raises(AIServiceError) as exc_info:
        detector.require_single_face(image)
    assert exc_info.value.code == ErrorCode.MULTIPLE_FACES


def test_detection_no_face(settings):
    detector = FaceDetector(engine=DetectEngine([], settings), settings=settings)
    with pytest.raises(AIServiceError) as exc_info:
        detector.require_single_face(np.zeros((200, 200, 3), dtype=np.uint8))
    assert exc_info.value.code == ErrorCode.NO_FACE


def test_detection_invalid_image(invalid_image_b64):
    with pytest.raises(AIServiceError) as exc_info:
        decode_base64_image(invalid_image_b64)
    assert exc_info.value.code == ErrorCode.INVALID_IMAGE
