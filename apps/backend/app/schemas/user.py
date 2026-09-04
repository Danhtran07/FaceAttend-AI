from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from app.core.timezone import to_vietnam_time
from app.models.user import UserRole


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8)
    role: UserRole = UserRole.EMPLOYEE


class UserUpdate(BaseModel):
    username: str | None = Field(
        default=None,
        min_length=3,
        max_length=50,
    )
    password: str | None = Field(
        default=None,
        min_length=8,
    )
    role: UserRole | None = None


class UserResponse(BaseModel):
    id: int
    username: str
    role: UserRole
    created_at: datetime
    updated_at: datetime

    @field_serializer("created_at", "updated_at")
    def serialize_datetime(self, value: datetime | None, _info):
        return to_vietnam_time(value)

    model_config = ConfigDict(from_attributes=True)