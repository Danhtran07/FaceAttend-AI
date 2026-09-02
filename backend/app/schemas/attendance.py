from datetime import date, datetime, timezone
from enum import Enum
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, field_serializer

VIETNAM_TZ = ZoneInfo("Asia/Ho_Chi_Minh")


def to_vietnam_time(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(VIETNAM_TZ)


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