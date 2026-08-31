from fastapi import FastAPI

from app.api.routes.auth import router as auth_router
from app.api.routes.health import router as health_router


app = FastAPI(title="FaceAttend Backend")

app.include_router(health_router)
app.include_router(auth_router)