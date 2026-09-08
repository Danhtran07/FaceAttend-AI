from datetime import date, time

from pydantic import BaseModel, ConfigDict


class ShiftCreate(BaseModel):
    name: str
    code: str
    description: str | None = None
    start_time: time
    end_time: time
    break_start_time: time | None = None
    break_end_time: time | None = None
    late_tolerance_minutes: int = 15
    early_checkin_minutes: int = 30
    is_overnight: bool = False
    is_active: bool = True


class ScheduleRuleCreate(BaseModel):
    day_of_week: int
    shift_id: int


class WorkScheduleCreate(BaseModel):
    name: str
    code: str
    description: str | None = None
    is_active: bool = True
    rules: list[ScheduleRuleCreate]


class ScheduleAssignmentCreate(BaseModel):
    employee_id: int
    schedule_id: int
    effective_from: date
    effective_to: date | None = None
    is_active: bool = True


class ScheduleAssignmentResponse(BaseModel):
    id: int
    employee_id: int
    employee_code: str
    employee_name: str
    schedule_id: int
    schedule_name: str
    effective_from: date
    effective_to: date | None = None
    is_active: bool


class ShiftEmployeeResponse(BaseModel):
    employee_id: int
    employee_code: str
    employee_name: str
    schedule_id: int
    schedule_name: str
    assignment_id: int


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