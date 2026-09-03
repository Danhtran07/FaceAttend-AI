import pytest

from app.core.errors import (
    ErrorCode,
    InvalidEmbeddingError,
    InvalidImageError,
    InvalidRequestError,
    LowQualityError,
    ModelError,
    MultipleFacesError,
    NoFaceError,
    UnknownFaceError,
    build_error_response,
    sanitize_details,
)


def _assert_standard_error(data: dict, code: ErrorCode):
    assert data["success"] is False
    assert data["error_code"] == code.value
    assert isinstance(data["message"], str) and data["message"]
    assert "traceback" not in str(data).lower()
    assert "stack" not in str(data).lower()
    assert set(data.keys()) >= {"success", "error_code", "message", "details"}


def test_build_error_response_shape():
    payload = build_error_response(ErrorCode.NO_FACE)
    _assert_standard_error(payload, ErrorCode.NO_FACE)
    assert payload["details"] is None


def test_sanitize_details_strips_secrets_and_embeddings():
    cleaned = sanitize_details(
        {
            "face_count": 2,
            "password": "secret",
            "jwt": "abc",
            "embedding": [0.1] * 512,
            "image": "base64...",
        }
    )
    assert cleaned == {"face_count": 2}


def test_api_no_face(client, sample_image_b64, monkeypatch):
    from app.api import face as face_api

    monkeypatch.setattr(
        face_api.enrollment_service,
        "enroll",
        lambda image: (_ for _ in ()).throw(NoFaceError()),
    )
    response = client.post("/face/enroll", json={"image": sample_image_b64})
    assert response.status_code == 400
    _assert_standard_error(response.json(), ErrorCode.NO_FACE)


def test_api_multiple_faces(client, sample_image_b64, monkeypatch):
    from app.api import face as face_api

    monkeypatch.setattr(
        face_api.enrollment_service,
        "enroll",
        lambda image: (_ for _ in ()).throw(MultipleFacesError(details={"face_count": 2})),
    )
    response = client.post("/face/enroll", json={"image": sample_image_b64})
    assert response.status_code == 400
    data = response.json()
    _assert_standard_error(data, ErrorCode.MULTIPLE_FACES)
    assert data["details"]["face_count"] == 2


def test_api_unknown_face(client, sample_image_b64, monkeypatch):
    from app.api import face as face_api

    monkeypatch.setattr(
        face_api.recognition_service,
        "recognize",
        lambda *a, **k: (_ for _ in ()).throw(
            UnknownFaceError(details={"recognized": False, "employee_id": None, "confidence": 0.31})
        ),
    )
    response = client.post(
        "/face/recognize",
        json={"image": sample_image_b64, "candidates": [{"employee_id": 1, "embedding": [0.0] * 4}]},
    )
    assert response.status_code == 404
    data = response.json()
    _assert_standard_error(data, ErrorCode.UNKNOWN_FACE)
    assert data["details"]["confidence"] == 0.31


def test_api_invalid_image(client, invalid_image_b64):
    response = client.post("/face/enroll", json={"image": invalid_image_b64})
    assert response.status_code == 400
    _assert_standard_error(response.json(), ErrorCode.INVALID_IMAGE)


def test_api_low_quality(client, sample_image_b64, monkeypatch):
    from app.api import face as face_api

    monkeypatch.setattr(
        face_api.enrollment_service,
        "enroll",
        lambda image: (_ for _ in ()).throw(LowQualityError()),
    )
    response = client.post("/face/enroll", json={"image": sample_image_b64})
    assert response.status_code == 400
    _assert_standard_error(response.json(), ErrorCode.LOW_QUALITY)


def test_api_model_error(client, sample_image_b64, monkeypatch):
    from app.api import face as face_api

    monkeypatch.setattr(
        face_api.recognition_service,
        "recognize",
        lambda *a, **k: (_ for _ in ()).throw(ModelError()),
    )
    response = client.post(
        "/face/recognize",
        json={"image": sample_image_b64, "candidates": []},
    )
    assert response.status_code == 500
    _assert_standard_error(response.json(), ErrorCode.MODEL_ERROR)


def test_api_invalid_embedding(client, sample_image_b64, monkeypatch):
    from app.api import face as face_api

    monkeypatch.setattr(
        face_api.recognition_service,
        "recognize",
        lambda *a, **k: (_ for _ in ()).throw(InvalidEmbeddingError()),
    )
    response = client.post(
        "/face/recognize",
        json={"image": sample_image_b64, "candidates": [{"employee_id": 1, "embedding": [1.0]}]},
    )
    assert response.status_code == 400
    _assert_standard_error(response.json(), ErrorCode.INVALID_EMBEDDING)


def test_api_invalid_request(client):
    response = client.post("/face/enroll", json={})
    assert response.status_code == 422
    _assert_standard_error(response.json(), ErrorCode.INVALID_REQUEST)


def test_typed_exceptions_codes():
    assert NoFaceError().code == ErrorCode.NO_FACE
    assert MultipleFacesError().code == ErrorCode.MULTIPLE_FACES
    assert UnknownFaceError().code == ErrorCode.UNKNOWN_FACE
    assert InvalidImageError().code == ErrorCode.INVALID_IMAGE
    assert LowQualityError().code == ErrorCode.LOW_QUALITY
    assert ModelError().code == ErrorCode.MODEL_ERROR
    assert InvalidEmbeddingError().code == ErrorCode.INVALID_EMBEDDING
    assert InvalidRequestError().code == ErrorCode.INVALID_REQUEST


def test_decode_invalid_still_invalid_image():
    from app.utils.image import decode_base64_image

    with pytest.raises(InvalidImageError):
        decode_base64_image("%%%invalid%%%")
