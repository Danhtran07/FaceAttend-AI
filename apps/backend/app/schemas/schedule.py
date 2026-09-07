from datetime import date, time

from pydantic import BaseModel, ConfigDict


class ShiftResponse(BaseModel):
    id: int
    name: str
    code: str
    description: str | None = None
    start_time: time
    end_time: time
    late_tolerance_minutes: int
    early_checkin_minutes: int
    is_overnight: bool
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class ScheduleRuleResponse(BaseModel):
    id: int
    day_of_week: int
    shift: ShiftResponse | None = None

    model_config = ConfigDict(from_attributes=True)


class ScheduleResponse(BaseModel):
    id: int
    name: str
    code: str
    description: str | None = None
    is_active: bool
    rules: list[ScheduleRuleResponse]

    model_config = ConfigDict(from_attributes=True)


class EmployeeScheduleResponse(BaseModel):
    employee_id: int
    target_date: date
    assignment_id: int | None = None
    schedule: ScheduleResponse | None = None
    shift: ShiftResponse | None = None