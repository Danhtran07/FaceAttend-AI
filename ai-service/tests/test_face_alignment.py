import numpy as np
import pytest

from app.core.config import Settings
from app.core.errors import AIServiceError, ErrorCode
from app.services.face_aligner import EXPECTED_LANDMARK_COUNT, FaceAlignmentService
from app.services.face_engine import FaceDetectionResult


@pytest.fixture
def alignment_service():
    return FaceAlignmentService(settings=Settings(aligned_face_size=112))


@pytest.fixture
def face_image():
    image = np.zeros((200, 200, 3), dtype=np.uint8)
    image[50:150, 60:140] = 180
    return image


@pytest.fixture
def valid_landmarks():
    return np.array(
        [
            [70.0, 80.0],
            [130.0, 80.0],
            [100.0, 110.0],
            [80.0, 130.0],
            [120.0, 130.0],
        ],
        dtype=np.float32,
    )


def test_align_valid_landmarks(alignment_service, face_image, valid_landmarks):
    aligned = alignment_service.align(face_image, valid_landmarks)

    assert aligned.ndim == 3
    assert aligned.shape == (112, 112, 3)
    assert aligned.dtype == np.uint8
    assert aligned.size > 0


def test_align_output_shape_follows_settings(face_image, valid_landmarks):
    service = FaceAlignmentService(settings=Settings(aligned_face_size=112))
    aligned = service.align(face_image, valid_landmarks)
    assert aligned.shape[0] == aligned.shape[1] == 112


def test_align_missing_landmarks(alignment_service, face_image):
    with pytest.raises(AIServiceError) as exc_info:
        alignment_service.align(face_image, None)

    assert exc_info.value.code == ErrorCode.MODEL_ERROR
    assert "missing" in exc_info.value.message.lower()


def test_align_empty_landmarks(alignment_service, face_image):
    with pytest.raises(AIServiceError) as exc_info:
        alignment_service.align(face_image, np.array([]))

    assert exc_info.value.code == ErrorCode.MODEL_ERROR


def test_align_invalid_landmark_count(alignment_service, face_image, valid_landmarks):
    with pytest.raises(AIServiceError) as exc_info:
        alignment_service.align(face_image, valid_landmarks[:3])

    assert exc_info.value.code == ErrorCode.INVALID_IMAGE
    assert exc_info.value.details["expected"] == EXPECTED_LANDMARK_COUNT
    assert exc_info.value.details["actual"] == 3


def test_align_invalid_landmark_values(alignment_service, face_image, valid_landmarks):
    invalid = valid_landmarks.copy()
    invalid[0] = np.nan

    with pytest.raises(AIServiceError) as exc_info:
        alignment_service.align(face_image, invalid)

    assert exc_info.value.code == ErrorCode.INVALID_IMAGE


def test_align_landmarks_out_of_bounds(alignment_service, face_image):
    landmarks = np.array(
        [
            [-50.0, -50.0],
            [500.0, -20.0],
            [800.0, 900.0],
            [-10.0, 400.0],
            [1000.0, 1000.0],
        ],
        dtype=np.float32,
    )

    with pytest.raises(AIServiceError) as exc_info:
        alignment_service.align(face_image, landmarks)

    assert exc_info.value.code == ErrorCode.INVALID_IMAGE


def test_align_invalid_face_none(alignment_service, valid_landmarks):
    with pytest.raises(AIServiceError) as exc_info:
        alignment_service.align(None, valid_landmarks)

    assert exc_info.value.code == ErrorCode.INVALID_IMAGE


def test_align_invalid_face_empty(alignment_service, valid_landmarks):
    with pytest.raises(AIServiceError) as exc_info:
        alignment_service.align(np.array([]), valid_landmarks)

    assert exc_info.value.code == ErrorCode.INVALID_IMAGE


def test_align_invalid_face_grayscale(alignment_service, valid_landmarks):
    gray = np.zeros((200, 200), dtype=np.uint8)

    with pytest.raises(AIServiceError) as exc_info:
        alignment_service.align(gray, valid_landmarks)

    assert exc_info.value.code == ErrorCode.INVALID_IMAGE


def test_align_detected_face_reuses_landmarks(alignment_service, face_image, valid_landmarks):
    face = FaceDetectionResult(
        bbox=[60.0, 50.0, 140.0, 150.0],
        confidence=0.98,
        landmarks=valid_landmarks,
    )

    aligned = alignment_service.align_detected_face(face_image, face)

    assert aligned.shape == (112, 112, 3)
    assert face.aligned_face is aligned
