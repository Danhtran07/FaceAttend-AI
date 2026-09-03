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
        face_api.enrollment_service,
        "enroll",
        lambda image: FaceEnrollResponse(
            success=True,
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
    assert data["embedding"] == [1.0, 0.0, 0.0, 0.0]


def test_enroll_api_no_face_error_format(client, sample_image_b64, monkeypatch):
    from app.api import face as face_api
    from app.core.errors import AIServiceError, ErrorCode

    def raise_no_face(*args, **kwargs):
        raise AIServiceError(ErrorCode.NO_FACE, status_code=400)

    monkeypatch.setattr(face_api.enrollment_service, "enroll", raise_no_face)

    response = client.post("/face/enroll", json={"image": sample_image_b64})
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert data["embedding"] is None
    assert data["error_code"] == ErrorCode.NO_FACE.value
    assert data["error"]["code"] == ErrorCode.NO_FACE.value


def test_recognize_api_known(client, sample_image_b64, monkeypatch):
    from app.api import face as face_api
    from app.core.schemas import FaceRecognizeResponse

    monkeypatch.setattr(
        face_api.recognition_service,
        "recognize",
        lambda image, candidates, threshold=None: FaceRecognizeResponse(
            recognized=True,
            employee_id=123,
            confidence=0.92,
        ),
    )

    response = client.post(
        "/face/recognize",
        json={
            "image": sample_image_b64,
            "candidates": [
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


def test_recognize_api_unknown(client, sample_image_b64, monkeypatch):
    from app.api import face as face_api
    from app.core.errors import AIServiceError, ErrorCode

    def raise_unknown(*args, **kwargs):
        raise AIServiceError(
            ErrorCode.UNKNOWN_FACE,
            details={
                "recognized": False,
                "employee_id": None,
                "confidence": 0.31,
            },
            status_code=404,
        )

    monkeypatch.setattr(face_api.recognition_service, "recognize", raise_unknown)

    response = client.post(
        "/face/recognize",
        json={
            "image": sample_image_b64,
            "candidates": [
                {"employee_id": 1, "embedding": [0.0, 1.0, 0.0, 0.0]}
            ],
        },
    )
    assert response.status_code == 404
    data = response.json()
    assert data["error"]["code"] == ErrorCode.UNKNOWN_FACE.value
    assert data["error"]["details"]["recognized"] is False
    assert data["error"]["details"]["employee_id"] is None
    assert data["error"]["details"]["confidence"] == 0.31


def test_recognize_api_invalid_image(client, invalid_image_b64):
    response = client.post(
        "/face/recognize",
        json={"image": invalid_image_b64, "candidates": []},
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == ErrorCode.INVALID_IMAGE.value


def test_invalid_image_error(client, invalid_image_b64):
    response = client.post("/face/detect", json={"image": invalid_image_b64})
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == ErrorCode.INVALID_IMAGE.value
