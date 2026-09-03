import pytest

from app.core.config import Settings
from app.core.errors import AIServiceError, ErrorCode
from app.core.schemas import MatchCandidate
from app.services.face_matcher import FaceMatchingService


@pytest.fixture
def match_settings():
    return Settings(
        embedding_dim=4,
        face_match_threshold=0.5,
        recognition_threshold=0.5,
    )


@pytest.fixture
def matching_service(match_settings):
    return FaceMatchingService(settings=match_settings)


def _candidates():
    return [
        MatchCandidate(employee_id=123, embedding=[1.0, 0.0, 0.0, 0.0]),
        MatchCandidate(employee_id=456, embedding=[0.0, 1.0, 0.0, 0.0]),
        MatchCandidate(employee_id=789, embedding=[0.0, 0.0, 1.0, 0.0]),
    ]


def test_tc01_known_face(matching_service):
    result = matching_service.match(
        [1.0, 0.0, 0.0, 0.0],
        _candidates(),
        threshold=0.5,
    )

    assert result.recognized is True
    assert result.employee_id == 123
    assert result.confidence == pytest.approx(1.0)


def test_tc02_unknown_face(matching_service):
    result = matching_service.match(
        [0.0, 0.0, 0.0, 1.0],
        [
            MatchCandidate(employee_id=123, embedding=[1.0, 0.0, 0.0, 0.0]),
            MatchCandidate(employee_id=456, embedding=[0.0, 1.0, 0.0, 0.0]),
        ],
        threshold=0.5,
    )

    assert result.recognized is False
    assert result.employee_id is None
    assert result.confidence == pytest.approx(0.0)


def test_tc03_threshold_pass(matching_service):
    # Cosine of [1,0,0,0] and [0.8,0.6,0,0] after normalize ≈ 0.8
    result = matching_service.match(
        [1.0, 0.0, 0.0, 0.0],
        [MatchCandidate(employee_id=10, embedding=[0.8, 0.6, 0.0, 0.0])],
        threshold=0.7,
    )

    assert result.recognized is True
    assert result.employee_id == 10
    assert result.confidence == pytest.approx(0.8, abs=1e-4)


def test_tc04_threshold_fail(matching_service):
    result = matching_service.match(
        [1.0, 0.0, 0.0, 0.0],
        [MatchCandidate(employee_id=10, embedding=[0.8, 0.6, 0.0, 0.0])],
        threshold=0.9,
    )

    assert result.recognized is False
    assert result.employee_id is None
    assert result.confidence == pytest.approx(0.8, abs=1e-4)


def test_tc04_unknown_face_error(matching_service):
    with pytest.raises(AIServiceError) as exc_info:
        matching_service.match_or_unknown(
            [1.0, 0.0, 0.0, 0.0],
            [MatchCandidate(employee_id=10, embedding=[0.8, 0.6, 0.0, 0.0])],
            threshold=0.9,
        )

    assert exc_info.value.code == ErrorCode.UNKNOWN_FACE
    assert exc_info.value.details["best_similarity"] == pytest.approx(0.8, abs=1e-4)


def test_tc05_empty_candidates(matching_service):
    result = matching_service.match([1.0, 0.0, 0.0, 0.0], [])

    assert result.recognized is False
    assert result.employee_id is None
    assert result.confidence == 0.0


def test_tc06_invalid_embedding_empty(matching_service):
    with pytest.raises(AIServiceError) as exc_info:
        matching_service.match([], _candidates())
    assert exc_info.value.code == ErrorCode.INVALID_IMAGE


def test_tc06_invalid_embedding_nan(matching_service):
    with pytest.raises(AIServiceError) as exc_info:
        matching_service.match([1.0, float("nan"), 0.0, 0.0], _candidates())
    assert exc_info.value.code == ErrorCode.INVALID_IMAGE


def test_tc06_invalid_embedding_dimension(matching_service):
    with pytest.raises(AIServiceError) as exc_info:
        matching_service.match(
            [1.0, 0.0, 0.0, 0.0],
            [MatchCandidate(employee_id=1, embedding=[1.0, 0.0])],
        )
    assert exc_info.value.code == ErrorCode.INVALID_IMAGE


def test_tc07_best_match_selection(matching_service):
    result = matching_service.match(
        [0.1, 0.9, 0.0, 0.0],
        _candidates(),
        threshold=0.5,
    )

    assert result.recognized is True
    assert result.employee_id == 456
    assert result.confidence > 0.5


def test_uses_configurable_face_match_threshold():
    service = FaceMatchingService(
        settings=Settings(embedding_dim=4, face_match_threshold=0.95)
    )
    result = service.match(
        [1.0, 0.0, 0.0, 0.0],
        [MatchCandidate(employee_id=1, embedding=[0.8, 0.6, 0.0, 0.0])],
    )

    assert service.threshold == 0.95
    assert result.recognized is False
    assert result.employee_id is None
