from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user
from app.core.database import get_db
from app.models.attendance import Attendance
from app.models.employee import Employee
from app.models.user import User
from app.schemas.attendance import (
    AttendanceCreate,
    AttendanceResponse,
    AttendanceUpdate,
)


router = APIRouter(
    prefix="/api/attendance",
    tags=["Attendance"],
)


@router.get(
    "",
    response_model=list[AttendanceResponse],
)
def get_attendance(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
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

    attendance = Attendance(
        employee_id=payload.employee_id,
        date=payload.date,
        check_in=payload.check_in,
        check_out=payload.check_out,
        status=payload.status,
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

    update_data = payload.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(attendance, field, value)

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

    db.delete(attendance)
    db.commit()

    return None