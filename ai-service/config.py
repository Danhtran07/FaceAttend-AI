"""Standalone AI service settings. Independent of Backend and Database."""

from __future__ import annotations

import os
from pathlib import Path

SERVICE_ROOT = Path(__file__).resolve().parent
MODELS_DIR = SERVICE_ROOT / "models"
MEDIAPIPE_MODEL_PATH = MODELS_DIR / "face_landmarker.task"
INSIGHTFACE_LOCAL_ROOT = MODELS_DIR / "insightface"

# buffalo_l: RetinaFace detector + ArcFace embedding (from face-biometrics-api)
INSIGHTFACE_MODEL_NAME = os.getenv("INSIGHTFACE_MODEL_NAME", "buffalo_l")
DETECTION_SIZE = (640, 640)
DETECTION_THRESHOLD = float(os.getenv("DETECTION_THRESHOLD", "0.5"))
# Cosine similarity above this = same person (face-biometrics-api default)
SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", "0.45"))
MAX_FACES = int(os.getenv("MAX_FACES", "10"))
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
HOST = os.getenv("AI_SERVICE_HOST", "0.0.0.0")
PORT = int(os.getenv("AI_SERVICE_PORT", "8001"))

MEDIAPIPE_MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/"
    "face_landmarker/face_landmarker/float16/1/face_landmarker.task"
)


def insightface_root() -> str:
    """Prefer bundled models/, then the user cache used by InsightFace."""
    bundled = INSIGHTFACE_LOCAL_ROOT / "models" / INSIGHTFACE_MODEL_NAME
    if bundled.exists():
        return str(INSIGHTFACE_LOCAL_ROOT)
    home_cache = Path.home() / ".insightface" / "models" / INSIGHTFACE_MODEL_NAME
    if home_cache.exists():
        return str(Path.home() / ".insightface")
    INSIGHTFACE_LOCAL_ROOT.mkdir(parents=True, exist_ok=True)
    return str(INSIGHTFACE_LOCAL_ROOT)
