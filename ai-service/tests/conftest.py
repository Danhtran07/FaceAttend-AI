import base64
from io import BytesIO

import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.core.config import Settings
from app.main import app
from app.services.face_engine import FaceDetectionResult, FaceEngine, reset_face_engine
from app.services.face_detector import FaceDetector
from app.services.face_aligner import FaceAligner
from app.services.face_embedder import FaceEmbedder
from app.services.face_matcher import FaceMatcher
from app.services.pipeline import FacePipeline


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def settings():
    return Settings(
        detection_threshold=0.5,
        recognition_threshold=0.5,
        min_face_size=20,
        min_blur_variance=10.0,
        embedding_dim=4,
        aligned_face_size=112,
    )


@pytest.fixture
def sample_image_b64():
    image = np.zeros((200, 200, 3), dtype=np.uint8)
    cv2.rectangle(image, (60, 50), (140, 150), (180, 150, 120), -1)
    cv2.circle(image, (90, 90), 8, (20, 20, 20), -1)
    cv2.circle(image, (110, 90), 8, (20, 20, 20), -1)
    cv2.ellipse(image, (100, 120), (20, 10), 0, 0, 180, (30, 30, 30), 2)
    return encode_image(image)


@pytest.fixture
def blank_image_b64():
    image = np.zeros((200, 200, 3), dtype=np.uint8)
    return encode_image(image)


@pytest.fixture
def invalid_image_b64():
    return base64.b64encode(b"not-an-image").decode("utf-8")


@pytest.fixture
def mock_face():
    landmarks = np.array(
        [
            [70.0, 80.0],
            [130.0, 80.0],
            [100.0, 110.0],
            [80.0, 130.0],
            [120.0, 130.0],
        ],
        dtype=np.float32,
    )
    return FaceDetectionResult(
        bbox=[60.0, 50.0, 140.0, 150.0],
        confidence=0.98,
        landmarks=landmarks,
        aligned_face=np.ones((112, 112, 3), dtype=np.uint8) * 128,
        embedding=np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32),
    )


@pytest.fixture
def mock_engine(mock_face):
    class MockEngine(FaceEngine):
        def __init__(self, faces=None):
            super().__init__(Settings(embedding_dim=4))
            self._faces = faces if faces is not None else [mock_face]

        def detect(self, image):
            return list(self._faces)

        def get_embedding(self, image, face):
            return self.extract_embedding(face.aligned_face)

        def extract_embedding(self, aligned_face):
            feature = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32)
            self._model_embedding_dim = int(feature.shape[0])
            return feature

        def model_embedding_dim(self):
            return 4

    return MockEngine()


@pytest.fixture
def pipeline(mock_engine, settings):
    detector = FaceDetector(engine=mock_engine, settings=settings)
    aligner = FaceAligner(engine=mock_engine)
    embedder = FaceEmbedder(engine=mock_engine, settings=settings)
    matcher = FaceMatcher(settings=settings)
    return FacePipeline(detector, aligner, embedder, matcher)


def encode_image(image: np.ndarray) -> str:
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    pil_image = Image.fromarray(rgb)
    buffer = BytesIO()
    pil_image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


@pytest.fixture(autouse=True)
def cleanup_engine():
    yield
    reset_face_engine()
