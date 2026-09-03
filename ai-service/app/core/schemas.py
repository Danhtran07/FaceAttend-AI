from typing import Any

from pydantic import BaseModel, Field, model_validator


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
    """Recognition request: image + Backend-supplied reference embeddings."""

    image: str = Field(..., description="Base64-encoded image")
    candidates: list[MatchCandidate] = Field(
        default_factory=list,
        description="Reference embeddings fetched by Backend from PostgreSQL",
    )
    registered_embeddings: list[RegisteredEmbedding] | None = Field(
        default=None,
        description="Deprecated alias for candidates",
        exclude=True,
    )
    threshold: float | None = Field(None, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def merge_candidates(self) -> "FaceRecognizeRequest":
        if self.candidates:
            return self
        if self.registered_embeddings:
            self.candidates = [
                MatchCandidate(employee_id=item.employee_id, embedding=item.embedding)
                for item in self.registered_embeddings
            ]
        return self


class FaceRecognizeResponse(BaseModel):
    recognized: bool
    employee_id: int | None = None
    confidence: float | None = None


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
