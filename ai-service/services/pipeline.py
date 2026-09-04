"""Image → Detection → Face Mesh → Embedding → Recognition."""

from __future__ import annotations

import numpy as np

from schemas.face import AnalyzeResponse, FaceResult
from services.face_detection import DetectedFace, FaceDetector
from services.face_embedding import FaceEmbedder
from services.face_mesh import FaceMesh, FaceMeshResult
from services.face_recognition import FaceRecognizer
from services.image_io import decode_image_bytes
from services.runtime import runtime


def _iou(a: list[float], b: list[float]) -> float:
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    inter = max(0.0, ix2 - ix1) * max(0.0, iy2 - iy1)
    if inter <= 0:
        return 0.0
    area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
    union = area_a + area_b - inter
    return inter / union if union > 0 else 0.0


def _match_mesh(face: DetectedFace, meshes: list[FaceMeshResult]) -> list[list[float]]:
    if not meshes:
        return []
    best: FaceMeshResult | None = None
    best_iou = 0.0
    face_bbox = [float(v) for v in face.bbox]
    for mesh in meshes:
        score = _iou(face_bbox, mesh.bbox)
        if score > best_iou:
            best_iou = score
            best = mesh
    if best is None or best_iou < 0.1:
        return []
    return best.landmarks


class FacePipeline:
    def __init__(self) -> None:
        self.detector = FaceDetector()
        self.mesh = FaceMesh()
        self.embedder = FaceEmbedder()
        self.recognizer = FaceRecognizer()

    def analyze(
        self,
        image_bytes: bytes,
        reference_bytes: bytes | None = None,
    ) -> AnalyzeResponse:
        if not runtime.loaded:
            raise RuntimeError("Models are not loaded")

        frame = decode_image_bytes(image_bytes)
        detections = self.detector.detect(frame)
        meshes = self.mesh.detect(frame)

        embeddings: list[np.ndarray] = []
        faces: list[FaceResult] = []
        for det in detections:
            embedding = self.embedder.embed(det)
            embeddings.append(embedding)
            faces.append(
                FaceResult(
                    bbox=det.bbox,
                    detection_confidence=round(det.detection_confidence, 6),
                    landmarks=_match_mesh(det, meshes),
                    embedding=embedding.astype(float).tolist(),
                    identity=None,
                    similarity=None,
                )
            )

        if reference_bytes:
            self._apply_reference(faces, embeddings, reference_bytes)
        elif len(embeddings) > 1:
            self._apply_in_image_similarity(faces, embeddings)

        return AnalyzeResponse(success=True, face_count=len(faces), faces=faces)

    def _apply_reference(
        self,
        faces: list[FaceResult],
        embeddings: list[np.ndarray],
        reference_bytes: bytes,
    ) -> None:
        ref_frame = decode_image_bytes(reference_bytes)
        ref_faces = self.detector.detect(ref_frame)
        if not ref_faces:
            return
        ref_embedding = self.embedder.embed(ref_faces[0])
        for i, embedding in enumerate(embeddings):
            matched, similarity = self.recognizer.is_same_person(embedding, ref_embedding)
            faces[i].similarity = similarity
            faces[i].identity = "match" if matched else "no_match"

    def _apply_in_image_similarity(
        self,
        faces: list[FaceResult],
        embeddings: list[np.ndarray],
    ) -> None:
        for i, embedding in enumerate(embeddings):
            gallery = [(str(j), other) for j, other in enumerate(embeddings) if j != i]
            identity, similarity = self.recognizer.best_match(embedding, gallery)
            faces[i].similarity = similarity
            faces[i].identity = f"face_{identity}" if identity is not None else None


_pipeline: FacePipeline | None = None


def get_pipeline() -> FacePipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = FacePipeline()
    return _pipeline
