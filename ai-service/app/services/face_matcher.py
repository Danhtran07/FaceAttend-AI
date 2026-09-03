from __future__ import annotations

import numpy as np

from app.core.config import Settings, get_settings
from app.core.errors import AIServiceError, ErrorCode
from app.core.schemas import RegisteredEmbedding


class FaceMatcher:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()

    def match(
        self,
        query_embedding: list[float],
        registered_embeddings: list[RegisteredEmbedding],
        threshold: float | None = None,
    ) -> tuple[bool, int | None, float]:
        if not registered_embeddings:
            return False, None, 0.0

        threshold = threshold if threshold is not None else self.settings.recognition_threshold
        query = self._normalize(np.asarray(query_embedding, dtype=np.float32))

        best_employee_id: int | None = None
        best_similarity = -1.0

        for item in registered_embeddings:
            candidate = self._normalize(np.asarray(item.embedding, dtype=np.float32))
            if candidate.shape != query.shape:
                raise AIServiceError(
                    ErrorCode.MODEL_ERROR,
                    "Registered embedding dimension mismatch",
                    details={
                        "employee_id": item.employee_id,
                        "expected": query.shape[0],
                        "actual": candidate.shape[0],
                    },
                    status_code=400,
                )

            similarity = float(np.dot(query, candidate))
            if similarity > best_similarity:
                best_similarity = similarity
                best_employee_id = item.employee_id

        if best_similarity >= threshold and best_employee_id is not None:
            return True, best_employee_id, best_similarity

        return False, None, max(best_similarity, 0.0)

    @staticmethod
    def _normalize(vector: np.ndarray) -> np.ndarray:
        norm = np.linalg.norm(vector)
        if norm == 0:
            return vector
        return vector / norm
