from pydantic import BaseModel


class AIRecognitionResult(BaseModel):
    employee_id: int | None = None
    confidence: float = 0.0
    matched: bool
    liveness: bool
    error_code: str | None = None
    message: str | None = None


class AIRecognitionCandidate(BaseModel):
    employee_id: int
    embedding: list[float]