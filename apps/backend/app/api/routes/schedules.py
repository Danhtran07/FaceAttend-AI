from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user
from app.core.database import get_db
from app.models.employee import Employee
from app.models.schedule_assignment import ScheduleAssignment
from app.models.schedule_rule import ScheduleRule
from app.models.shift import Shift
from app.models.user import User, UserRole
from app.models.work_schedule import WorkSchedule
from app.schemas.schedule import (
    EmployeeScheduleResponse,
    ScheduleAssignmentCreate,
    ScheduleAssignmentResponse,
    ScheduleResponse,
    ShiftResponse,
    ShiftCreate,
    ShiftEmployeeResponse,
    WorkScheduleCreate,
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


@router.post("/api/shifts", response_model=ShiftResponse, status_code=status.HTTP_201_CREATED)
def create_shift(
    payload: ShiftCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_admin(current_user)
    if db.query(Shift).filter(Shift.code == payload.code).first() is not None:
        raise HTTPException(status_code=409, detail="Shift code already exists")

    shift = Shift(**payload.model_dump())
    db.add(shift)
    db.commit()
    db.refresh(shift)
    return shift


@router.get("/api/schedules", response_model=list[ScheduleResponse])
def get_schedules(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_admin(current_user)
    return db.query(WorkSchedule).order_by(WorkSchedule.name).all()


@router.post("/api/schedules", response_model=ScheduleResponse, status_code=status.HTTP_201_CREATED)
def create_schedule(
    payload: WorkScheduleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_admin(current_user)
    if db.query(WorkSchedule).filter(WorkSchedule.code == payload.code).first() is not None:
        raise HTTPException(status_code=409, detail="Schedule code already exists")

    day_numbers = [rule.day_of_week for rule in payload.rules]
    if any(day < 1 or day > 7 for day in day_numbers):
        raise HTTPException(status_code=422, detail="day_of_week must be between 1 and 7")
    if len(day_numbers) != len(set(day_numbers)):
        raise HTTPException(status_code=422, detail="Each schedule day can only be configured once")

    shift_ids = {rule.shift_id for rule in payload.rules}
    shifts = db.query(Shift).filter(Shift.id.in_(shift_ids)).all()
    if len(shifts) != len(shift_ids):
        raise HTTPException(status_code=404, detail="One or more shifts were not found")

    schedule = WorkSchedule(
        name=payload.name,
        code=payload.code,
        description=payload.description,
        is_active=payload.is_active,
    )
    db.add(schedule)
    db.flush()
    db.add_all(
        ScheduleRule(
            schedule_id=schedule.id,
            day_of_week=rule.day_of_week,
            shift_id=rule.shift_id,
        )
        for rule in payload.rules
    )
    db.commit()
    db.refresh(schedule)
    return schedule


@router.post(
    "/api/schedule-assignments",
    response_model=ScheduleAssignmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_schedule_assignment(
    payload: ScheduleAssignmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_admin(current_user)
    if payload.effective_to is not None and payload.effective_to < payload.effective_from:
        raise HTTPException(status_code=422, detail="effective_to must be on or after effective_from")

    employee = db.query(Employee).filter(Employee.id == payload.employee_id).first()
    if employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    schedule = db.query(WorkSchedule).filter(WorkSchedule.id == payload.schedule_id).first()
    if schedule is None:
        raise HTTPException(status_code=404, detail="Schedule not found")

    overlapping = (
        db.query(ScheduleAssignment)
        .filter(
            ScheduleAssignment.employee_id == payload.employee_id,
            ScheduleAssignment.is_active.is_(True),
            ScheduleAssignment.effective_from <= (payload.effective_to or date.max),
            (
                ScheduleAssignment.effective_to.is_(None)
                | (ScheduleAssignment.effective_to >= payload.effective_from)
            ),
        )
        .first()
    )
    if overlapping is not None:
        raise HTTPException(status_code=409, detail="Employee already has an overlapping active schedule")

    assignment = ScheduleAssignment(**payload.model_dump())
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return ScheduleAssignmentResponse(
        id=assignment.id,
        employee_id=employee.id,
        employee_code=employee.employee_code,
        employee_name=employee.full_name,
        schedule_id=schedule.id,
        schedule_name=schedule.name,
        effective_from=assignment.effective_from,
        effective_to=assignment.effective_to,
        is_active=assignment.is_active,
    )


@router.get(
    "/api/shifts/{shift_id}/employees",
    response_model=list[ShiftEmployeeResponse],
)
def get_shift_employees(
    shift_id: int,
    target_date: date = Query(default_factory=date.today),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_admin(current_user)
    if db.query(Shift).filter(Shift.id == shift_id).first() is None:
        raise HTTPException(status_code=404, detail="Shift not found")

    rows = (
        db.query(ScheduleAssignment, Employee, WorkSchedule)
        .join(Employee, Employee.id == ScheduleAssignment.employee_id)
        .join(WorkSchedule, WorkSchedule.id == ScheduleAssignment.schedule_id)
        .join(
            ScheduleRule,
            ScheduleRule.schedule_id == WorkSchedule.id,
        )
        .filter(
            ScheduleRule.shift_id == shift_id,
            ScheduleRule.day_of_week == target_date.isoweekday(),
            ScheduleAssignment.is_active.is_(True),
            WorkSchedule.is_active.is_(True),
            ScheduleAssignment.effective_from <= target_date,
            (
                ScheduleAssignment.effective_to.is_(None)
                | (ScheduleAssignment.effective_to >= target_date)
            ),
        )
        .all()
    )
    return [
        ShiftEmployeeResponse(
            employee_id=employee.id,
            employee_code=employee.employee_code,
            employee_name=employee.full_name,
            schedule_id=schedule.id,
            schedule_name=schedule.name,
            assignment_id=assignment.id,
        )
        for assignment, employee, schedule in rows
    ]


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