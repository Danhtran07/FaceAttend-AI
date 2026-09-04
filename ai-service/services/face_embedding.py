"""ArcFace embeddings from InsightFace buffalo_l. Adapted from face-biometrics-api."""

from __future__ import annotations

import numpy as np

from services.face_detection import DetectedFace


class FaceEmbedder:
    def embed(self, face: DetectedFace) -> np.ndarray:
        raw = face.insightface_face
        if raw is None:
            raise RuntimeError("Cannot extract embedding without an InsightFace detection")

        vector = getattr(raw, "normed_embedding", None)
        if vector is None:
            vector = getattr(raw, "embedding", None)
            if vector is None:
                raise RuntimeError("InsightFace did not return an ArcFace embedding")
            vector = np.asarray(vector, dtype=np.float32).flatten()
            norm = float(np.linalg.norm(vector))
            if norm == 0.0:
                raise RuntimeError("ArcFace returned a zero embedding")
            vector = vector / norm
        else:
            vector = np.asarray(vector, dtype=np.float32).flatten()

        if vector.size == 0:
            raise RuntimeError("ArcFace returned an empty embedding")
        return vector
