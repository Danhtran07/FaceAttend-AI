import pytest

from app.core.errors import AIServiceError, ErrorCode
from app.core.schemas import RegisteredEmbedding
from app.services.face_matcher import FaceMatcher


def test_match_registered_employee(settings):
    matcher = FaceMatcher(settings=settings)
    registered = [
        RegisteredEmbedding(employee_id=123, embedding=[1.0, 0.0, 0.0, 0.0]),
        RegisteredEmbedding(employee_id=456, embedding=[0.0, 1.0, 0.0, 0.0]),
    ]

    recognized, employee_id, confidence = matcher.match(
        [1.0, 0.0, 0.0, 0.0],
        registered,
        threshold=0.5,
    )

    assert recognized is True
    assert employee_id == 123
    assert confidence == pytest.approx(1.0)


def test_match_unknown_face(settings):
    matcher = FaceMatcher(settings=settings)
    registered = [
        RegisteredEmbedding(employee_id=123, embedding=[0.0, 1.0, 0.0, 0.0]),
    ]

    recognized, employee_id, confidence = matcher.match(
        [1.0, 0.0, 0.0, 0.0],
        registered,
        threshold=0.5,
    )

    assert recognized is False
    assert employee_id is None
    assert confidence == pytest.approx(0.0)


def test_match_empty_registry(settings):
    matcher = FaceMatcher(settings=settings)
    recognized, employee_id, confidence = matcher.match([1.0, 0.0, 0.0, 0.0], [])

    assert recognized is False
    assert employee_id is None
    assert confidence == 0.0


def test_match_dimension_mismatch(settings):
    matcher = FaceMatcher(settings=settings)
    registered = [RegisteredEmbedding(employee_id=1, embedding=[1.0, 0.0])]

    with pytest.raises(AIServiceError) as exc_info:
        matcher.match([1.0, 0.0, 0.0, 0.0], registered)

    assert exc_info.value.code == ErrorCode.MODEL_ERROR
