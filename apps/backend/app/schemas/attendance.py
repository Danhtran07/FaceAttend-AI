from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, field_serializer

from app.core.timezone import to_vietnam_time


class AttendanceStatus(str, Enum):
    PRESENT = "PRESENT"
    LATE = "LATE"
    ABSENT = "ABSENT"


class AttendanceBase(BaseModel):
    employee_id: int
    date: date


class AttendanceCreate(AttendanceBase):
    status: AttendanceStatus | None = None
    check_in: datetime | None = None
    check_out: datetime | None = None


class AttendanceUpdate(BaseModel):
    check_in: datetime | None = None
    check_out: datetime | None = None
    status: AttendanceStatus | None = None


class AttendanceResponse(AttendanceBase):
    id: int
    check_in: datetime | None = None
    check_out: datetime | None = None
    status: AttendanceStatus
    created_at: datetime
    updated_at: datetime

    @field_serializer("check_in", "check_out", "created_at", "updated_at")
    def serialize_datetime(self, value: datetime | None, _info):
        return to_vietnam_time(value)

    model_config = ConfigDict(from_attributes=True)