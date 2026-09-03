import numpy as np
import pytest

from app.core.config import Settings
from app.core.errors import AIServiceError, ErrorCode
from app.services.face_embedder import FaceEmbeddingService
from app.services.face_engine import FaceEngine


class ArcFaceEngineStub(FaceEngine):
    """Test double that returns a deterministic ArcFace-sized feature vector.

    Production FaceEngine still calls InsightFace. This stub only isolates
    input validation and L2 post-processing.
    """

    def __init__(self, feature: np.ndarray, settings: Settings | None = None):
        super().__init__(settings or Settings())
        self._feature = feature

    def extract_embedding(self, aligned_face: np.ndarray) -> np.ndarray:
        return np.asarray(self._feature, dtype=np.float32)

    def model_embedding_dim(self) -> int:
        return int(np.asarray(self._feature).size)


def _aligned_face(size: int = 112) -> np.ndarray:
    image = np.zeros((size, size, 3), dtype=np.uint8)
    image[20:90, 20:90] = (40, 80, 160)
    return image


def test_invalid_aligned_face_none():
    service = FaceEmbeddingService(engine=ArcFaceEngineStub(np.ones(512, dtype=np.float32)))
    with pytest.raises(AIServiceError) as exc_info:
        service.generate_embedding(None)
    assert exc_info.value.code == ErrorCode.INVALID_IMAGE


def test_empty_aligned_face():
    service = FaceEmbeddingService(engine=ArcFaceEngineStub(np.ones(512, dtype=np.float32)))
    with pytest.raises(AIServiceError) as exc_info:
        service.generate_embedding(np.array([]))
    assert exc_info.value.code == ErrorCode.INVALID_IMAGE


def test_invalid_aligned_face_wrong_shape():
    service = FaceEmbeddingService(engine=ArcFaceEngineStub(np.ones(512, dtype=np.float32)))
    with pytest.raises(AIServiceError) as exc_info:
        service.generate_embedding(np.zeros((64, 64, 3), dtype=np.uint8))
    assert exc_info.value.code == ErrorCode.INVALID_IMAGE


def test_normalize_l2():
    service = FaceEmbeddingService(engine=ArcFaceEngineStub(np.ones(512, dtype=np.float32)))
    vector = service.normalize(np.array([3.0, 4.0], dtype=np.float32))
    assert vector.dtype == np.float32
    np.testing.assert_allclose(vector, np.array([0.6, 0.8], dtype=np.float32), rtol=1e-6)
    assert pytest.approx(1.0) == float(np.linalg.norm(vector))


def test_generate_embedding_shape_dtype_and_normalization():
    raw = np.arange(512, dtype=np.float32) + 1.0
    settings = Settings(embedding_dim=512, aligned_face_size=112)
    service = FaceEmbeddingService(engine=ArcFaceEngineStub(raw, settings), settings=settings)

    embedding = service.generate_embedding(_aligned_face())

    assert embedding.shape == (512,)
    assert embedding.dtype == np.float32
    assert service.dimension() == 512
    assert pytest.approx(1.0, abs=1e-5) == float(np.linalg.norm(embedding))
    assert np.isfinite(embedding).all()

    again = service.generate_embedding(_aligned_face())
    np.testing.assert_allclose(embedding, again)


def test_generate_embedding_list_json_shape():
    raw = np.ones(512, dtype=np.float32)
    settings = Settings(embedding_dim=512, aligned_face_size=112)
    service = FaceEmbeddingService(engine=ArcFaceEngineStub(raw, settings), settings=settings)

    payload = service.generate_embedding_list(_aligned_face())

    assert isinstance(payload, list)
    assert len(payload) == 512
    assert all(isinstance(value, float) for value in payload)


def test_insightface_arcface_on_aligned_face():
    try:
        engine = FaceEngine(Settings(model_name="buffalo_l", embedding_dim=512))
        engine._get_app()
    except Exception as exc:
        pytest.skip(f"InsightFace ArcFace model is not available: {exc}")

    service = FaceEmbeddingService(engine=engine, settings=engine.settings)
    embedding = service.generate_embedding(_aligned_face())

    assert embedding.shape == (512,)
    assert embedding.dtype == np.float32
    assert pytest.approx(1.0, abs=1e-4) == float(np.linalg.norm(embedding))
    assert not np.allclose(embedding, 0)
