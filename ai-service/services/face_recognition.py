"""Cosine similarity / identity from ArcFace embeddings. Adapted from face-biometrics-api."""

from __future__ import annotations

import numpy as np

import config


class FaceRecognizer:
    @staticmethod
    def cosine_similarity(emb1: np.ndarray, emb2: np.ndarray) -> float:
        """Both embeddings are L2-normalized so dot product = cosine similarity."""
        return float(np.dot(emb1, emb2))

    @staticmethod
    def is_same_person(emb1: np.ndarray, emb2: np.ndarray) -> tuple[bool, float]:
        sim = FaceRecognizer.cosine_similarity(emb1, emb2)
        return sim >= config.SIMILARITY_THRESHOLD, round(sim, 4)

    def best_match(
        self,
        query: np.ndarray,
        gallery: list[tuple[str, np.ndarray]],
    ) -> tuple[str | None, float | None]:
        if not gallery:
            return None, None

        best_id: str | None = None
        best_embedding: np.ndarray | None = None
        best_sim = -1.0
        for identity, embedding in gallery:
            sim = self.cosine_similarity(query, embedding)
            if sim > best_sim:
                best_sim = sim
                best_id = identity
                best_embedding = embedding

        if best_embedding is None:
            return None, None

        matched, rounded = self.is_same_person(query, best_embedding)
        return (best_id if matched else None), rounded
