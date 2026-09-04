"""Download MediaPipe FaceLandmarker into models/ (InsightFace caches on first load)."""

from __future__ import annotations

import urllib.request
from pathlib import Path

import config


def download_face_landmarker() -> Path:
    config.MODELS_DIR.mkdir(parents=True, exist_ok=True)
    dest = config.MEDIAPIPE_MODEL_PATH
    if dest.exists() and dest.stat().st_size > 1_000_000:
        print(f"FaceLandmarker already present: {dest}")
        return dest
    print(f"Downloading MediaPipe FaceLandmarker -> {dest}")
    urllib.request.urlretrieve(config.MEDIAPIPE_MODEL_URL, dest)
    print(f"Saved {dest} ({dest.stat().st_size} bytes)")
    return dest


if __name__ == "__main__":
    download_face_landmarker()
    print("InsightFace buffalo_l is downloaded on first FaceAnalysis() call (CPU).")
