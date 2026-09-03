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
    from app.core.errors import NoFaceError

    monkeypatch.setattr(
        face_api.enrollment_service,
        "enroll",
        lambda image: (_ for _ in ()).throw(NoFaceError()),
    )

    response = client.post("/face/enroll", json={"image": sample_image_b64})
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert data["error_code"] == ErrorCode.NO_FACE.value
    assert data["message"]
    assert "error" not in data or "code" not in data.get("error", {})


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
    from app.core.errors import UnknownFaceError

    monkeypatch.setattr(
        face_api.recognition_service,
        "recognize",
        lambda *a, **k: (_ for _ in ()).throw(
            UnknownFaceError(
                details={
                    "recognized": False,
                    "employee_id": None,
                    "confidence": 0.31,
                }
            )
        ),
    )

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
    assert data["error_code"] == ErrorCode.UNKNOWN_FACE.value
    assert data["details"]["recognized"] is False
    assert data["details"]["employee_id"] is None
    assert data["details"]["confidence"] == 0.31


def test_recognize_api_invalid_image(client, invalid_image_b64):
    response = client.post(
        "/face/recognize",
        json={"image": invalid_image_b64, "candidates": []},
    )
    assert response.status_code == 400
    assert response.json()["error_code"] == ErrorCode.INVALID_IMAGE.value


def test_invalid_image_error(client, invalid_image_b64):
    response = client.post("/face/detect", json={"image": invalid_image_b64})
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert data["error_code"] == ErrorCode.INVALID_IMAGE.value
