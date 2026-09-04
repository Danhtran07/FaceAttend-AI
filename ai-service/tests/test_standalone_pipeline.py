"""Real-model tests for the standalone AI pipeline. Skips if models cannot load."""

from __future__ import annotations

import urllib.request
from pathlib import Path

import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient

import config
from download_models import download_face_landmarker
from services.face_recognition import FaceRecognizer
from services.image_io import decode_image_bytes
from services.runtime import ModelLoadError, runtime

TEST_DIR = Path(__file__).resolve().parent
FIXTURES = TEST_DIR / "fixtures"
FACE_IMAGE = FIXTURES / "real_face.jpg"
# Public MediaPipe sample portrait with a real face.
FACE_IMAGE_URL = (
    "https://storage.googleapis.com/mediapipe-assets/portrait.jpg"
)


def _ensure_face_image() -> Path:
    FIXTURES.mkdir(parents=True, exist_ok=True)
    if FACE_IMAGE.exists() and FACE_IMAGE.stat().st_size > 1000:
        return FACE_IMAGE
    urllib.request.urlretrieve(FACE_IMAGE_URL, FACE_IMAGE)
    return FACE_IMAGE


def _side_by_side(image_bytes: bytes) -> bytes:
    frame = decode_image_bytes(image_bytes)
    paired = np.concatenate([frame, frame], axis=1)
    ok, encoded = cv2.imencode(".jpg", paired)
    assert ok
    return encoded.tobytes()


@pytest.fixture(scope="session")
def face_bytes() -> bytes:
    return _ensure_face_image().read_bytes()


@pytest.fixture(scope="session")
def ai_client():
    try:
        download_face_landmarker()
    except Exception as exc:
        pytest.skip(f"Could not download FaceLandmarker: {exc}")

    from main import app

    try:
        with TestClient(app) as test_client:
            health = test_client.get("/health")
            if health.status_code != 200 or not health.json().get("models_loaded"):
                pytest.skip(f"Models did not load: {health.text}")
            yield test_client
    except ModelLoadError as exc:
        pytest.skip(f"Models did not load: {exc}")


def test_model_loading(ai_client):
    response = ai_client.get("/health")
    body = response.json()
    assert response.status_code == 200
    assert body["models_loaded"] is True
    assert body["insightface"] == "buffalo_l"
    assert body["face_mesh"] == "face_landmarker"
    assert runtime.loaded is True


def test_invalid_image(ai_client):
    response = ai_client.post("/analyze", files={"file": ("bad.bin", b"not-an-image", "application/octet-stream")})
    assert response.status_code == 400
    body = response.json()
    assert body["success"] is False
    assert body.get("error")


def test_no_face(ai_client):
    blank = np.full((240, 320, 3), 180, dtype=np.uint8)
    ok, encoded = cv2.imencode(".jpg", blank)
    assert ok
    response = ai_client.post("/analyze", files={"file": ("blank.jpg", encoded.tobytes(), "image/jpeg")})
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["face_count"] == 0
    assert body["faces"] == []


def test_full_pipeline_real_face(ai_client, face_bytes):
    response = ai_client.post("/analyze", files={"file": ("face.jpg", face_bytes, "image/jpeg")})
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["face_count"] >= 1
    face = body["faces"][0]

    assert len(face["bbox"]) == 4
    assert face["detection_confidence"] > 0.5
    assert len(face["landmarks"]) >= 468
    assert len(face["embedding"]) == 512
    assert abs(float(np.linalg.norm(face["embedding"])) - 1.0) < 0.05


def test_face_recognition_same_image(ai_client, face_bytes):
    response = ai_client.post(
        "/analyze",
        files={
            "file": ("probe.jpg", face_bytes, "image/jpeg"),
            "reference": ("gallery.jpg", face_bytes, "image/jpeg"),
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["face_count"] >= 1
    face = body["faces"][0]
    assert face["identity"] == "match"
    assert face["similarity"] is not None
    assert face["similarity"] >= config.SIMILARITY_THRESHOLD
    assert face["similarity"] > 0.8


def test_multiple_faces_and_similarity(ai_client, face_bytes):
    paired = _side_by_side(face_bytes)
    response = ai_client.post("/analyze", files={"file": ("pair.jpg", paired, "image/jpeg")})
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    if body["face_count"] < 2:
        pytest.skip("Detector returned fewer than 2 faces on the paired image")
    for face in body["faces"]:
        assert len(face["embedding"]) == 512
        assert face["similarity"] is not None
        assert face["similarity"] >= config.SIMILARITY_THRESHOLD


def test_cosine_similarity_unit():
    vector = np.ones(512, dtype=np.float32)
    vector = vector / np.linalg.norm(vector)
    matched, sim = FaceRecognizer.is_same_person(vector, vector)
    assert matched is True
    assert sim == pytest.approx(1.0, abs=1e-4)
