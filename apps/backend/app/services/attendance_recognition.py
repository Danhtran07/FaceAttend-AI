from datetime import datetime, time, timezone

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.timezone import to_vietnam_time
from app.models.attendance import Attendance, AttendanceStatus
from app.models.employee import Employee
from app.schemas.ai import AIRecognitionResult


class RecognitionRejectedError(Exception):
    def __init__(self, detail: str, status_code: int) -> None:
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code


class AttendancePersistenceError(Exception):
    pass


def compute_attendance_status(check_in: datetime | None) -> AttendanceStatus:
    if check_in is None:
        return AttendanceStatus.ABSENT
    if to_vietnam_time(check_in).time() > time(8, 30):
        return AttendanceStatus.LATE
    return AttendanceStatus.PRESENT


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
    attendance = (
        db.query(Attendance)
        .filter(
            Attendance.employee_id == employee.id,
            Attendance.date == local_date,
        )
        .first()
    )

    if attendance is None:
        attendance = Attendance(
            employee_id=employee.id,
            date=local_date,
            check_in=server_now,
            status=compute_attendance_status(server_now),
        )
        db.add(attendance)
    elif attendance.check_out is None:
        attendance.check_out = server_now
    else:
        raise RecognitionRejectedError("Attendance already completed for today", 409)

    try:
        db.commit()
        db.refresh(attendance)
    except SQLAlchemyError as exc:
        db.rollback()
        raise AttendancePersistenceError("Failed to save attendance") from exc

    return attendance