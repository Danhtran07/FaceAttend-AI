"""Face detection via InsightFace buffalo_l (RetinaFace). Adapted from face-biometrics-api."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

import config
from services.runtime import runtime


@dataclass
class DetectedFace:
    bbox: list[int]
    detection_confidence: float
    kps: np.ndarray | None = None
    insightface_face: Any = field(default=None, repr=False)


class FaceDetector:
    def detect(self, frame: np.ndarray) -> list[DetectedFace]:
        app = runtime.face_analysis
        if app is None:
            raise RuntimeError("InsightFace model is not loaded")

        try:
            faces = app.get(frame)
        except Exception as exc:
            raise RuntimeError(f"Face detection failed: {exc}") from exc

        results: list[DetectedFace] = []
        for face in faces:
            score = float(getattr(face, "det_score", 0.0))
            if score < config.DETECTION_THRESHOLD:
                continue
            bbox = [int(v) for v in np.asarray(face.bbox).astype(int).tolist()]
            kps = getattr(face, "kps", None)
            results.append(
                DetectedFace(
                    bbox=bbox,
                    detection_confidence=score,
                    kps=kps,
                    insightface_face=face,
                )
            )
        results.sort(key=lambda item: item.detection_confidence, reverse=True)
        return results
