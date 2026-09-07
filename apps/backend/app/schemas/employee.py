from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from app.core.timezone import to_vietnam_time


class EmployeeBase(BaseModel):
    full_name: str
    email: str
    department: str | None = None


class EmployeeCreate(EmployeeBase):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8)


class EmployeeUpdate(BaseModel):
    full_name: str | None = None
    email: str | None = None
    department: str | None = None


class EmployeeResponse(EmployeeBase):
    employee_code: str
    id: int
    user_id: int
    face_enrolled: bool
    created_at: datetime
    updated_at: datetime

    @field_serializer("created_at", "updated_at")
    def serialize_datetime(self, value: datetime | None, _info):
        return to_vietnam_time(value)

    model_config = ConfigDict(from_attributes=True)