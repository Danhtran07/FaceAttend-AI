from datetime import datetime

from pydantic import BaseModel, ConfigDict


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

    model_config = ConfigDict(from_attributes=True)