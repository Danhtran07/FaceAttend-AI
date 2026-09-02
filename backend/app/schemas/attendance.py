from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict


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

    model_config = ConfigDict(from_attributes=True)