import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from face_recognition_engine import FaceAnalysisResult, FaceRecognitionEngine
from models import BackendRecognitionResponse, LegacyRecognizeRequest


def test_backend_request_accepts_liveness_session_and_response_contract():
    request = LegacyRecognizeRequest(
        image="aGVsbG8=",
        liveness_session_id="session-123",
    )
    response = BackendRecognitionResponse(
        matched=True,
        employee_id=123,
        confidence=0.964,
        liveness=True,
    )

    assert request.liveness_session_id == "session-123"
    assert response.model_dump() == {
        "matched": True,
        "employee_id": 123,
        "confidence": 0.964,
        "liveness": True,
        "success": True,
        "recognized": None,
        "error_code": None,
        "message": None,
    }


def test_recognition_engine_reports_multiple_detected_faces():
    class FakeFace:
        def __init__(self, score: float):
            self.det_score = score
            self.bbox = np.array([10, 10, 100, 100], dtype=np.float32)
            self.gender = 1
            self.age = 30
            self.normed_embedding = np.ones(512, dtype=np.float32)

    class FakeInsightFace:
        def get(self, _frame):
            return [FakeFace(0.95), FakeFace(0.90)]

    success, encoded = cv2.imencode(
        ".jpg",
        np.zeros((120, 120, 3), dtype=np.uint8),
    )
    assert success

    engine = FaceRecognitionEngine.__new__(FaceRecognitionEngine)
    engine.app = FakeInsightFace()
    result = engine.analyze(encoded.tobytes())

    assert isinstance(result, FaceAnalysisResult)
    assert result.face_detected is True
    assert result.face_count == 2


def test_recognition_engine_distinguishes_invalid_image_bytes():
    engine = FaceRecognitionEngine.__new__(FaceRecognitionEngine)
    result = engine.analyze(b"not-an-image")

    assert result.image_valid is False
    assert result.face_detected is False