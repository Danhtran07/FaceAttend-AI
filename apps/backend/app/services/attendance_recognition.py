from datetime import datetime, timezone

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.timezone import to_vietnam_time
from app.models.attendance import Attendance, AttendanceStatus
from app.models.employee import Employee
from app.models.notification import NotificationType
from app.schemas.ai import AIRecognitionResult
from app.services.attendance_policy import (
    calculate_attendance_metrics,
    calculate_attendance_status,
)
from app.services.shift_resolver import resolve_shift
from app.services.notification_service import create_success_notification


class RecognitionRejectedError(Exception):
    def __init__(self, detail: str, status_code: int) -> None:
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code


class AttendancePersistenceError(Exception):
    pass


def compute_attendance_status(
    db: Session,
    employee_id: int,
    check_in: datetime | None,
) -> AttendanceStatus:
    if check_in is None:
        return AttendanceStatus.ABSENT

    local_check_in = to_vietnam_time(check_in)
    shift = resolve_shift(db, employee_id, local_check_in.date())
    return calculate_attendance_status(check_in, shift)


def record_recognition_attendance(
    db: Session,
    recognition: AIRecognitionResult,
    now: datetime | None = None,
) -> Attendance:
    if not recognition.matched:
        raise RecognitionRejectedError("Face was not recognized", 422)
    if not recognition.liveness:
        raise RecognitionRejectedError("Liveness validation failed", 422)
    if recognition.employee_id is None:
        raise RecognitionRejectedError("Recognition did not identify an employee", 422)

    employee = (
        db.query(Employee)
        .filter(Employee.id == recognition.employee_id)
        .first()
    )
    if employee is None:
        raise RecognitionRejectedError("Employee not found", 404)

    server_now = now or datetime.now(timezone.utc)
    local_date = to_vietnam_time(server_now).date()
    shift = resolve_shift(db, employee.id, local_date)
    attendance_status = calculate_attendance_status(server_now, shift)
    metrics = calculate_attendance_metrics(server_now, None, shift)
    attendance = (
        db.query(Attendance)
        .filter(
            Attendance.employee_id == employee.id,
            Attendance.date == local_date,
        )
        .first()
    )

    notification_type: NotificationType
    notification_message: str
    if attendance is None:
        attendance = Attendance(
            employee_id=employee.id,
            shift_id=shift.id if shift is not None else None,
            date=local_date,
            check_in=server_now,
            status=attendance_status,
            late_minutes=metrics.late_minutes,
            early_leave_minutes=metrics.early_leave_minutes,
            working_minutes=metrics.working_minutes,
            overtime_minutes=metrics.overtime_minutes,
        )
        db.add(attendance)
        notification_type = NotificationType.CHECK_IN_SUCCESS
        notification_message = f"You checked in successfully at {to_vietnam_time(server_now).strftime('%I:%M %p').lstrip('0')}."
    elif attendance.check_out is None:
        attendance.check_out = server_now
        metrics = calculate_attendance_metrics(
            attendance.check_in,
            server_now,
            attendance.shift,
        )
        attendance.early_leave_minutes = metrics.early_leave_minutes
        attendance.working_minutes = metrics.working_minutes
        attendance.overtime_minutes = metrics.overtime_minutes
        notification_type = NotificationType.CHECK_OUT_SUCCESS
        notification_message = f"You checked out successfully at {to_vietnam_time(server_now).strftime('%I:%M %p').lstrip('0')}."
    else:
        raise RecognitionRejectedError("Attendance already completed for today", 409)

    create_success_notification(
        db,
        employee.id,
        local_date,
        notification_type,
        notification_message,
        server_now,
    )

    try:
        db.commit()
        db.refresh(attendance)
    except SQLAlchemyError as exc:
        db.rollback()
        raise AttendancePersistenceError("Failed to save attendance") from exc

    return attendance