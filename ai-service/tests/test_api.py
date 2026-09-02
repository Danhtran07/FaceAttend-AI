import base64

import pytest

from app.core.errors import ErrorCode


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["service"] == "ai-service"


def test_detect_api(client, sample_image_b64, monkeypatch):
    from app.api import face as face_api
    from app.core.schemas import DetectedFace, FaceDetectionResponse

    monkeypatch.setattr(
        face_api.pipeline,
        "detect_faces",
        lambda image: FaceDetectionResponse(
            faces=[DetectedFace(bbox=[10, 20, 30, 40], confidence=0.9)]
        ),
    )

    response = client.post("/face/detect", json={"image": sample_image_b64})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["faces"][0]["confidence"] == 0.9


def test_enroll_api(client, sample_image_b64, monkeypatch):
    from app.api import face as face_api
    from app.core.schemas import FaceEnrollResponse

    monkeypatch.setattr(
        face_api.pipeline,
        "enroll",
        lambda image: FaceEnrollResponse(
            embedding=[1.0, 0.0, 0.0, 0.0],
            dimension=4,
            bbox=[60, 50, 140, 150],
            confidence=0.98,
        ),
    )

    response = client.post("/face/enroll", json={"image": sample_image_b64})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["dimension"] == 4


def test_recognize_api(client, sample_image_b64, monkeypatch):
    from app.api import face as face_api
    from app.core.schemas import FaceRecognizeResponse

    monkeypatch.setattr(
        face_api.pipeline,
        "recognize",
        lambda image, registered, threshold=None: FaceRecognizeResponse(
            recognized=True,
            employee_id=123,
            confidence=0.92,
            face_count=1,
        ),
    )

    response = client.post(
        "/face/recognize",
        json={
            "image": sample_image_b64,
            "registered_embeddings": [
                {"employee_id": 123, "embedding": [1.0, 0.0, 0.0, 0.0]}
            ],
            "threshold": 0.5,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["recognized"] is True
    assert data["employee_id"] == 123
    assert data["confidence"] == 0.92


def test_invalid_image_error(client, invalid_image_b64):
    response = client.post("/face/detect", json={"image": invalid_image_b64})
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == ErrorCode.INVALID_IMAGE.value


def test_unknown_face_error_format(client, sample_image_b64, monkeypatch):
    from app.api import face as face_api
    from app.core.errors import AIServiceError, ErrorCode

    def raise_unknown(*args, **kwargs):
        raise AIServiceError(
            ErrorCode.UNKNOWN_FACE,
            details={"best_similarity": 0.12},
            status_code=404,
        )

    monkeypatch.setattr(face_api.pipeline, "recognize", raise_unknown)

    response = client.post(
        "/face/recognize",
        json={
            "image": sample_image_b64,
            "registered_embeddings": [
                {"employee_id": 1, "embedding": [0.0, 1.0, 0.0, 0.0]}
            ],
        },
    )
    assert response.status_code == 404
    data = response.json()
    assert data["error"]["code"] == ErrorCode.UNKNOWN_FACE.value
    assert data["error"]["details"]["best_similarity"] == 0.12
