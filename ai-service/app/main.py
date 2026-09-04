from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.face import router as face_router
from app.api.health import router as health_router
from app.core.errors import register_exception_handlers

app = FastAPI(
    title="FaceAttend AI Service",
    description="Face detection, alignment, embedding, and recognition service",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(health_router)
app.include_router(face_router)
