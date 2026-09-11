from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user
from app.core.database import get_db
from app.models.employee import Employee
from app.models.schedule_assignment import ScheduleAssignment
from app.models.shift import Shift
from app.models.user import User, UserRole
from app.models.work_schedule import WorkSchedule
from app.schemas.schedule import (
    EmployeeScheduleResponse,
    ScheduleResponse,
    ShiftResponse,
)
from app.services.shift_resolver import resolve_shift


router = APIRouter(tags=["Schedules"])


def _require_admin(current_user: User) -> None:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can manage schedules",
        )


@router.get("/api/shifts", response_model=list[ShiftResponse])
def get_shifts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_admin(current_user)
    return db.query(Shift).order_by(Shift.start_time, Shift.name).all()


@router.get("/api/schedules", response_model=list[ScheduleResponse])
def get_schedules(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_admin(current_user)
    return db.query(WorkSchedule).order_by(WorkSchedule.name).all()


def _get_employee_schedule(
    db: Session,
    employee_id: int,
    target_date: date,
) -> EmployeeScheduleResponse:
    assignment = (
        db.query(ScheduleAssignment)
        .filter(
            ScheduleAssignment.employee_id == employee_id,
            ScheduleAssignment.is_active.is_(True),
            ScheduleAssignment.effective_from <= target_date,
            (
                ScheduleAssignment.effective_to.is_(None)
                | (ScheduleAssignment.effective_to >= target_date)
            ),
        )
        .order_by(ScheduleAssignment.effective_from.desc())
        .first()
    )
    if assignment is None or not assignment.schedule.is_active:
        return EmployeeScheduleResponse(
            employee_id=employee_id,
            target_date=target_date,
        )

    return EmployeeScheduleResponse(
        employee_id=employee_id,
        target_date=target_date,
        assignment_id=assignment.id,
        schedule=assignment.schedule,
        shift=resolve_shift(db, employee_id, target_date),
    )


@router.get(
    "/api/employees/{employee_id}/schedule",
    response_model=EmployeeScheduleResponse,
)
def get_employee_schedule(
    employee_id: int,
    target_date: date = Query(default_factory=date.today),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_admin(current_user)
    if db.query(Employee).filter(Employee.id == employee_id).first() is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    return _get_employee_schedule(db, employee_id, target_date)


@router.get(
    "/api/schedules/me",
    response_model=EmployeeScheduleResponse,
)
def get_my_schedule(
    target_date: date = Query(default_factory=date.today),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    if employee is None:
        raise HTTPException(status_code=404, detail="Employee profile not found")
    return _get_employee_schedule(db, employee.id, target_date)