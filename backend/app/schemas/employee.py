from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_serializer

from app.core.timezone import to_vietnam_time


class EmployeeBase(BaseModel):
    employee_code: str
    full_name: str
    email: str
    department: str | None = None


class EmployeeCreate(EmployeeBase):
    user_id: int


class EmployeeUpdate(BaseModel):
    employee_code: str | None = None
    full_name: str | None = None
    email: str | None = None
    department: str | None = None


class EmployeeResponse(EmployeeBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    @field_serializer("created_at", "updated_at")
    def serialize_datetime(self, value: datetime | None, _info):
        return to_vietnam_time(value)

    model_config = ConfigDict(from_attributes=True)