import pytest
from fastapi import HTTPException

from app.api.routes.employees import _validate_enrollment_quality
from app.api.routes.employees import _cosine_similarity


def test_enrollment_requires_at_least_three_valid_frames():
    with pytest.raises(HTTPException) as exc:
        _validate_enrollment_quality([[0.1, 0.2], [0.3, 0.4]])

    assert exc.value.status_code == 400
    assert "At least 3 valid face frames" in str(exc.value.detail)


def test_enrollment_accepts_three_or_more_valid_frames():
    _validate_enrollment_quality([
        [0.1, 0.2],
        [0.3, 0.4],
        [0.5, 0.6],
    ])


def test_duplicate_face_similarity_detects_same_embedding():
    assert _cosine_similarity([1.0, 0.0], [0.99, 0.01]) > 0.99


def test_different_face_similarity_does_not_trigger_duplicate_threshold():
    assert _cosine_similarity([1.0, 0.0], [0.0, 1.0]) < 0.75
