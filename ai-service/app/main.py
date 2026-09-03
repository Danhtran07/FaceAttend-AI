from fastapi import FastAPI

from app.api.face import router as face_router
from app.api.health import router as health_router
from app.core.errors import register_exception_handlers

app = FastAPI(
    title="FaceAttend AI Service",
    description="Face detection, alignment, embedding, and recognition service",
    version="1.0.0",
)

register_exception_handlers(app)

app.include_router(health_router)
app.include_router(face_router)
