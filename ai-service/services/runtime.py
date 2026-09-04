"""Load InsightFace buffalo_l and MediaPipe FaceLandmarker once at startup."""

from __future__ import annotations

import logging
from pathlib import Path

from insightface.app import FaceAnalysis
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision

import config

logger = logging.getLogger("ai_service")


class ModelLoadError(RuntimeError):
    pass


class AIRuntime:
    def __init__(self) -> None:
        self.face_analysis: FaceAnalysis | None = None
        self.landmarker = None
        self.loaded = False

    def load(self) -> None:
        if self.loaded:
            return
        self._load_insightface()
        self._load_face_landmarker()
        self.loaded = True
        logger.info(
            "Models loaded: insightface=%s mesh=%s",
            config.INSIGHTFACE_MODEL_NAME,
            config.MEDIAPIPE_MODEL_PATH.name,
        )

    def _load_insightface(self) -> None:
        try:
            root = config.insightface_root()
            Path(root).mkdir(parents=True, exist_ok=True)
            app = FaceAnalysis(
                name=config.INSIGHTFACE_MODEL_NAME,
                root=root,
                providers=["CPUExecutionProvider"],
            )
            app.prepare(ctx_id=-1, det_size=config.DETECTION_SIZE)
            self.face_analysis = app
        except Exception as exc:
            raise ModelLoadError(f"Failed to load InsightFace {config.INSIGHTFACE_MODEL_NAME}: {exc}") from exc

    def _load_face_landmarker(self) -> None:
        model_path = config.MEDIAPIPE_MODEL_PATH
        if not model_path.exists():
            raise ModelLoadError(
                f"MediaPipe FaceLandmarker model not found at {model_path}. "
                "Run: python download_models.py"
            )
        try:
            options = mp_vision.FaceLandmarkerOptions(
                base_options=mp_python.BaseOptions(model_asset_path=str(model_path)),
                output_face_blendshapes=False,
                output_facial_transformation_matrixes=False,
                num_faces=config.MAX_FACES,
                min_face_detection_confidence=0.5,
                min_face_presence_confidence=0.5,
                min_tracking_confidence=0.5,
            )
            self.landmarker = mp_vision.FaceLandmarker.create_from_options(options)
        except Exception as exc:
            raise ModelLoadError(f"Failed to load MediaPipe FaceLandmarker: {exc}") from exc

    def close(self) -> None:
        if self.landmarker is not None:
            self.landmarker.close()
            self.landmarker = None
        self.face_analysis = None
        self.loaded = False


runtime = AIRuntime()
