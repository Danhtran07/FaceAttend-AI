from fastapi import FastAPI

from app.api.routes.attendance import router as attendance_router
from app.api.routes.auth import router as auth_router
from app.api.routes.employees import router as employees_router
from app.api.routes.health import router as health_router
from app.api.routes.users import router as users_router


app = FastAPI(title="FaceAttend Backend")


app.include_router(health_router)
app.include_router(auth_router)
app.include_router(employees_router)
app.include_router(users_router)
app.include_router(attendance_router)