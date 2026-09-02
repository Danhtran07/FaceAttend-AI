from fastapi import FastAPI

from app.api.face import router as face_router
from app.api.health import router as health_router
from app.core.errors import AIServiceError, ai_service_error_handler

app = FastAPI(
    title="FaceAttend AI Service",
    description="Face detection, alignment, embedding, and recognition service",
    version="1.0.0",
)

app.add_exception_handler(AIServiceError, ai_service_error_handler)

app.include_router(health_router)
app.include_router(face_router)
