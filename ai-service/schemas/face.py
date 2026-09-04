from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class FaceResult(BaseModel):
    bbox: list[int] = Field(description="[x1, y1, x2, y2] in pixels")
    detection_confidence: float
    landmarks: list[list[float]] = Field(
        default_factory=list,
        description="MediaPipe FaceLandmarker points as [x, y, z] (image-normalized)",
    )
    embedding: list[float] = Field(
        default_factory=list,
        description="L2-normalized ArcFace embedding from InsightFace buffalo_l",
    )
    identity: Optional[str] = None
    similarity: Optional[float] = None


class AnalyzeResponse(BaseModel):
    success: bool
    face_count: int = 0
    faces: list[FaceResult] = Field(default_factory=list)
    error: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    models_loaded: bool
    insightface: Optional[str] = None
    face_mesh: Optional[str] = None
    details: dict[str, Any] = Field(default_factory=dict)
