"""MediaPipe FaceLandmarker (478 landmarks). Adapted from face-biometrics-api liveness_engine."""

from __future__ import annotations

from dataclasses import dataclass

import cv2
import mediapipe as mp
import numpy as np

from services.runtime import runtime


@dataclass
class FaceMeshResult:
    landmarks: list[list[float]]
    bbox: list[float]


class FaceMesh:
    def detect(self, frame: np.ndarray) -> list[FaceMeshResult]:
        landmarker = runtime.landmarker
        if landmarker is None:
            raise RuntimeError("MediaPipe FaceLandmarker is not loaded")

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        try:
            result = landmarker.detect(mp_image)
        except Exception as exc:
            raise RuntimeError(f"Face mesh failed: {exc}") from exc

        meshes: list[FaceMeshResult] = []
        if not result.face_landmarks:
            return meshes

        h, w = frame.shape[:2]
        for landmarks in result.face_landmarks:
            points = [[float(lm.x), float(lm.y), float(lm.z)] for lm in landmarks]
            xs = [lm.x * w for lm in landmarks]
            ys = [lm.y * h for lm in landmarks]
            bbox = [float(min(xs)), float(min(ys)), float(max(xs)), float(max(ys))]
            meshes.append(FaceMeshResult(landmarks=points, bbox=bbox))
        return meshes
