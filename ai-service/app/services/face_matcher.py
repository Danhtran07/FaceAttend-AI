from __future__ import annotations

import numpy as np

from app.core.config import Settings, get_settings
from app.core.errors import InvalidEmbeddingError, UnknownFaceError
from app.core.schemas import MatchCandidate, MatchResult


class FaceMatchingService:
    """Compare a query embedding against Backend-supplied candidates.

    AI Service never loads embeddings from a database. Backend fetches
    vectors from PostgreSQL and passes them as ``candidates``.
    """

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()

    @property
    def threshold(self) -> float:
        return float(self.settings.face_match_threshold)

    def match(
        self,
        query_embedding: list[float] | np.ndarray,
        candidates: list[MatchCandidate],
        threshold: float | None = None,
    ) -> MatchResult:
        """Find the best cosine match and apply the threshold.

        Below threshold → recognized=false, employee_id=null (UNKNOWN_FACE).
        Never returns a below-threshold employee_id as a match.
        """
        query = self._validate_embedding(query_embedding, field="query_embedding")
        cut = self._resolve_threshold(threshold)

        if not candidates:
            return MatchResult(
                recognized=False,
                employee_id=None,
                confidence=0.0,
            )

        best_employee_id: int | None = None
        best_similarity = -1.0

        for item in candidates:
            candidate = self._validate_embedding(
                item.embedding,
                field=f"candidates[{item.employee_id}].embedding",
            )
            if candidate.shape != query.shape:
                raise InvalidEmbeddingError(
                    "Candidate embedding dimension mismatch",
                    details={
                        "employee_id": item.employee_id,
                        "expected": int(query.shape[0]),
                        "actual": int(candidate.shape[0]),
                    },
                )

            similarity = self.cosine_similarity(query, candidate)
            if similarity > best_similarity:
                best_similarity = similarity
                best_employee_id = item.employee_id

        confidence = float(max(best_similarity, 0.0))

        if best_similarity >= cut and best_employee_id is not None:
            return MatchResult(
                recognized=True,
                employee_id=best_employee_id,
                confidence=round(confidence, 4),
            )

        return MatchResult(
            recognized=False,
            employee_id=None,
            confidence=round(confidence, 4),
        )

    def match_or_unknown(
        self,
        query_embedding: list[float] | np.ndarray,
        candidates: list[MatchCandidate],
        threshold: float | None = None,
    ) -> MatchResult:
        """Same as ``match``, but raise UNKNOWN_FACE when not recognized."""
        result = self.match(query_embedding, candidates, threshold=threshold)
        if not result.recognized:
            raise UnknownFaceError(details={"best_similarity": result.confidence})
        return result

    @staticmethod
    def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
        return float(np.dot(a, b))

    def _resolve_threshold(self, threshold: float | None) -> float:
        value = self.threshold if threshold is None else float(threshold)
        if value < 0.0 or value > 1.0:
            raise InvalidEmbeddingError(
                "Match threshold must be between 0 and 1",
                details={"threshold": value},
            )
        return value

    def _validate_embedding(
        self,
        embedding: list[float] | np.ndarray | None,
        *,
        field: str,
    ) -> np.ndarray:
        if embedding is None:
            raise InvalidEmbeddingError(f"{field} is required")

        try:
            vector = np.asarray(embedding, dtype=np.float32).flatten()
        except Exception as exc:
            raise InvalidEmbeddingError(f"{field} is not a valid numeric embedding") from exc

        if vector.size == 0:
            raise InvalidEmbeddingError(f"{field} is empty")

        expected = int(self.settings.embedding_dim)
        if expected > 0 and vector.shape[0] != expected:
            raise InvalidEmbeddingError(
                f"{field} has unexpected dimension",
                details={"expected": expected, "actual": int(vector.shape[0])},
            )

        if not np.isfinite(vector).all():
            raise InvalidEmbeddingError(f"{field} contains NaN or Inf")

        return self._normalize(vector)

    @staticmethod
    def _normalize(vector: np.ndarray) -> np.ndarray:
        norm = float(np.linalg.norm(vector))
        if norm == 0:
            raise InvalidEmbeddingError("Embedding is a zero vector")
        return vector / np.float32(norm)


class FaceMatcher:
    """Pipeline adapter around FaceMatchingService (Backend-supplied candidates)."""

    def __init__(self, settings: Settings | None = None):
        self.service = FaceMatchingService(settings=settings)

    def match(
        self,
        query_embedding: list[float],
        registered_embeddings: list,
        threshold: float | None = None,
    ) -> tuple[bool, int | None, float]:
        candidates = [
            item
            if isinstance(item, MatchCandidate)
            else MatchCandidate(employee_id=item.employee_id, embedding=item.embedding)
            for item in registered_embeddings
        ]
        result = self.service.match(query_embedding, candidates, threshold=threshold)
        return result.recognized, result.employee_id, float(result.confidence or 0.0)
