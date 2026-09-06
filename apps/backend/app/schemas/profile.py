from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from app.core.timezone import to_vietnam_time


class ProfileUpdate(BaseModel):
    full_name: str | None = Field(default=None, max_length=100)
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=30)
    avatar_url: str | None = Field(default=None, max_length=500)
    bio: str | None = None


class ProfileResponse(ProfileUpdate):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    @field_serializer("created_at", "updated_at")
    def serialize_datetime(self, value: datetime | None, _info):
        return to_vietnam_time(value)

    model_config = ConfigDict(from_attributes=True)