from datetime import datetime

from pydantic import BaseModel, field_serializer

from app.core.timezone import to_vietnam_time


class LoginRequest(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    role: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse