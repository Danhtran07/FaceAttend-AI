from typing import Any

from pydantic import BaseModel, Field


class BoundingBox(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float

    def to_list(self) -> list[float]:
        return [self.x1, self.y1, self.x2, self.y2]


class DetectedFace(BaseModel):
    bbox: list[float] = Field(..., description="[x1, y1, x2, y2]")
    confidence: float


class FaceDetectionResponse(BaseModel):
    success: bool = True
    faces: list[DetectedFace]


class RegisteredEmbedding(BaseModel):
    employee_id: int
    embedding: list[float]


class MatchCandidate(BaseModel):
    """Embedding candidate supplied by Backend (from PostgreSQL)."""

    employee_id: int
    embedding: list[float]


class MatchResult(BaseModel):
    recognized: bool
    employee_id: int | None = None
    confidence: float | None = None


class FaceMatchRequest(BaseModel):
    """Backend → AI matching contract. AI never loads embeddings from DB."""

    query_embedding: list[float]
    candidates: list[MatchCandidate] = Field(default_factory=list)
    threshold: float | None = Field(None, ge=0.0, le=1.0)


class FaceMatchResponse(BaseModel):
    recognized: bool
    employee_id: int | None = None
    confidence: float | None = None


class FaceRecognizeRequest(BaseModel):
    image: str = Field(..., description="Base64-encoded image")
    registered_embeddings: list[RegisteredEmbedding] = Field(
        default_factory=list,
        description="Candidates fetched by Backend from PostgreSQL",
    )
    threshold: float | None = Field(None, ge=0.0, le=1.0)


class FaceRecognizeResponse(BaseModel):
    success: bool = True
    recognized: bool
    employee_id: int | None = None
    confidence: float | None = None
    face_count: int = 0


class FaceEnrollRequest(BaseModel):
    image: str = Field(..., description="Base64-encoded image")


class FaceEnrollResponse(BaseModel):
    success: bool = True
    embedding: list[float]
    dimension: int
    bbox: list[float]
    confidence: float


class FaceDetectRequest(BaseModel):
    image: str = Field(..., description="Base64-encoded image")


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    success: bool = False
    error: ErrorDetail
