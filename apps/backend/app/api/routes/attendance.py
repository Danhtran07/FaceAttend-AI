from datetime import time

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user
from app.core.database import get_db
from app.models.attendance import Attendance, AttendanceStatus
from app.models.employee import Employee
from app.models.user import User, UserRole
from app.schemas.attendance import (
    AttendanceCreate,
    AttendanceResponse,
    AttendanceUpdate,
)


router = APIRouter(
    prefix="/api/attendance",
    tags=["Attendance"],
)


def _compute_status(check_in, check_out=None, explicit_status=None):
    if explicit_status is not None:
        return explicit_status

    if check_in is None:
        return AttendanceStatus.ABSENT

    if check_in.time() > time(8, 30):
        return AttendanceStatus.LATE

    return AttendanceStatus.PRESENT


def _get_employee_for_current_user(db: Session, current_user: User):
    return (
        db.query(Employee)
        .filter(Employee.user_id == current_user.id)
        .first()
    )


@router.get(
    "",
    response_model=list[AttendanceResponse],
)
def get_attendance(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == UserRole.EMPLOYEE:
        employee = _get_employee_for_current_user(db, current_user)
        if employee is None:
            return []
        return (
            db.query(Attendance)
            .filter(Attendance.employee_id == employee.id)
            .all()
        )

    return db.query(Attendance).all()


@router.get(
    "/{attendance_id}",
    response_model=AttendanceResponse,
)
def get_attendance_record(
    attendance_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    attendance = (
        db.query(Attendance)
        .filter(Attendance.id == attendance_id)
        .first()
    )

    if attendance is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attendance record not found",
        )

    if current_user.role == UserRole.EMPLOYEE:
        employee = _get_employee_for_current_user(db, current_user)
        if employee is None or attendance.employee_id != employee.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own attendance records",
            )

    return attendance


@router.post(
    "",
    response_model=AttendanceResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_attendance(
    payload: AttendanceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    employee = (
        db.query(Employee)
        .filter(Employee.id == payload.employee_id)
        .first()
    )

    if employee is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found",
        )

    if current_user.role == UserRole.EMPLOYEE:
        current_employee = _get_employee_for_current_user(db, current_user)
        if current_employee is None or payload.employee_id != current_employee.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only create attendance for your own employee record",
            )

    existing_attendance = (
        db.query(Attendance)
        .filter(
            Attendance.employee_id == payload.employee_id,
            Attendance.date == payload.date,
        )
        .first()
    )

    if existing_attendance is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Attendance record already exists for this employee and date",
        )

    if payload.check_out is not None and payload.check_in is not None:
        if payload.check_out < payload.check_in:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="check_out must be after check_in",
            )

    computed_status = _compute_status(
        payload.check_in,
        payload.check_out,
        payload.status,
    )

    attendance = Attendance(
        employee_id=payload.employee_id,
        date=payload.date,
        check_in=payload.check_in,
        check_out=payload.check_out,
        status=computed_status,
    )

    db.add(attendance)

    try:
        db.commit()
        db.refresh(attendance)
    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Attendance record already exists for this employee and date",
        )

    return attendance


@router.put(
    "/{attendance_id}",
    response_model=AttendanceResponse,
)
def update_attendance(
    attendance_id: int,
    payload: AttendanceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    attendance = (
        db.query(Attendance)
        .filter(Attendance.id == attendance_id)
        .first()
    )

    if attendance is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attendance record not found",
        )

    if current_user.role == UserRole.EMPLOYEE:
        employee = _get_employee_for_current_user(db, current_user)
        if employee is None or attendance.employee_id != employee.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own attendance records",
            )

    update_data = payload.model_dump(exclude_unset=True)

    if "check_in" in update_data:
        attendance.check_in = update_data["check_in"]

    if "check_out" in update_data and update_data["check_out"] is not None:
        if attendance.check_in is not None and update_data["check_out"] < attendance.check_in:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="check_out must be after check_in",
            )
        attendance.check_out = update_data["check_out"]

    if "status" in update_data and update_data["status"] is not None:
        attendance.status = update_data["status"]
    else:
        attendance.status = _compute_status(
            attendance.check_in,
            attendance.check_out,
        )

    db.commit()
    db.refresh(attendance)

    return attendance


@router.delete(
    "/{attendance_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_attendance(
    attendance_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    attendance = (
        db.query(Attendance)
        .filter(Attendance.id == attendance_id)
        .first()
    )

    if attendance is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attendance record not found",
        )

    if current_user.role == UserRole.EMPLOYEE:
        employee = _get_employee_for_current_user(db, current_user)
        if employee is None or attendance.employee_id != employee.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own attendance records",
            )

    db.delete(attendance)
    db.commit()

    return None