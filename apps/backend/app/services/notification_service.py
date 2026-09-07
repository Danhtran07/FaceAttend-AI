from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.timezone import VIETNAM_TZ, to_vietnam_time
from app.models.attendance import Attendance
from app.models.employee import Employee
from app.models.notification import Notification, NotificationSeverity, NotificationType
from app.services.shift_resolver import resolve_shift


def _local_shift_time(target_date: date, value: time) -> datetime:
    return datetime.combine(target_date, value).replace(tzinfo=VIETNAM_TZ)


def _upsert_notification(db: Session, employee_id: int, target_date: date, notification_type: NotificationType, severity: NotificationSeverity, title: str, message: str, action_label: str | None = None, action_path: str | None = None) -> Notification:
    notification = db.query(Notification).filter(
        Notification.employee_id == employee_id,
        Notification.notification_type == notification_type,
        Notification.attendance_date == target_date,
    ).first()
    if notification is None:
        notification = Notification(
            employee_id=employee_id,
            notification_type=notification_type,
            severity=severity,
            attendance_date=target_date,
            title=title,
            message=message,
            action_label=action_label,
            action_path=action_path,
        )
        db.add(notification)
    elif notification.resolved_at is None:
        notification.severity = severity
        notification.title = title
        notification.message = message
        notification.action_label = action_label
        notification.action_path = action_path
    return notification


def resolve_notifications(db: Session, employee_id: int, target_date: date, notification_types: tuple[NotificationType, ...], now: datetime | None = None) -> None:
    resolved_at = now or datetime.now(timezone.utc)
    db.query(Notification).filter(
        Notification.employee_id == employee_id,
        Notification.attendance_date == target_date,
        Notification.notification_type.in_(notification_types),
        Notification.resolved_at.is_(None),
    ).update({Notification.resolved_at: resolved_at}, synchronize_session=False)


def sync_attendance_notifications(db: Session, employee: Employee, now: datetime | None = None) -> None:
    server_now = now or datetime.now(timezone.utc)
    local_now = to_vietnam_time(server_now)
    target_date = local_now.date()
    shift = resolve_shift(db, employee.id, target_date)
    if shift is None:
        return

    attendance = db.query(Attendance).filter(
        Attendance.employee_id == employee.id,
        Attendance.date == target_date,
    ).first()
    shift_start = _local_shift_time(target_date, shift.start_time)
    shift_end = _local_shift_time(target_date, shift.end_time)
    if shift.is_overnight and shift_end <= shift_start:
        shift_end += timedelta(days=1)

    if attendance and attendance.check_in:
        resolve_notifications(db, employee.id, target_date, (NotificationType.CHECK_IN_REMINDER, NotificationType.CHECK_IN_MISSING, NotificationType.LATE_CHECK_IN), server_now)
    elif local_now >= shift_start:
        elapsed_minutes = max(0, int((local_now - shift_start).total_seconds() // 60))
        if elapsed_minutes <= 5:
            _upsert_notification(db, employee.id, target_date, NotificationType.CHECK_IN_REMINDER, NotificationSeverity.INFO, "Check-in Reminder", "Your shift has started. Please check in to record your attendance.", "Check In", "/recognition")
        elif elapsed_minutes <= shift.late_tolerance_minutes:
            _upsert_notification(db, employee.id, target_date, NotificationType.CHECK_IN_MISSING, NotificationSeverity.WARNING, "You Haven't Checked In", f"Your shift started at {shift.start_time.strftime('%I:%M %p').lstrip('0')}, but you haven't checked in yet.", "Check In Now", "/recognition")
        else:
            _upsert_notification(db, employee.id, target_date, NotificationType.LATE_CHECK_IN, NotificationSeverity.WARNING, "Late Check-in", f"You are currently {elapsed_minutes} minutes late. Please check in to record your attendance.", "Check In Now", "/recognition")

    if attendance and attendance.check_in and attendance.check_out:
        resolve_notifications(db, employee.id, target_date, (NotificationType.CHECK_OUT_REMINDER, NotificationType.CHECK_OUT_MISSING), server_now)
    elif attendance and attendance.check_in and local_now >= shift_end:
        elapsed_minutes = int((local_now - shift_end).total_seconds() // 60)
        title = "You Haven't Checked Out" if elapsed_minutes <= 60 else "Forgot to Check Out?"
        message = f"Your shift ended at {shift.end_time.strftime('%I:%M %p').lstrip('0')}, but you haven't checked out yet." if elapsed_minutes <= 60 else "Your attendance for today is still incomplete. Please check out to complete your attendance record."
        _upsert_notification(db, employee.id, target_date, NotificationType.CHECK_OUT_MISSING, NotificationSeverity.URGENT, title, message, "Check Out", "/recognition")
    elif attendance and attendance.check_in and local_now >= shift_end - timedelta(minutes=30):
        _upsert_notification(db, employee.id, target_date, NotificationType.CHECK_OUT_REMINDER, NotificationSeverity.INFO, "Check-out Reminder", f"Your shift ends at {shift.end_time.strftime('%I:%M %p').lstrip('0')}. Don't forget to check out when you finish work.", "View Attendance", "/attendance")


def create_success_notification(db: Session, employee_id: int, target_date: date, notification_type: NotificationType, message: str, now: datetime | None = None) -> None:
    title = "Check-in Successful" if notification_type == NotificationType.CHECK_IN_SUCCESS else "Check-out Successful"
    _upsert_notification(db, employee_id, target_date, notification_type, NotificationSeverity.SUCCESS, title, message)
    if notification_type == NotificationType.CHECK_IN_SUCCESS:
        resolve_notifications(db, employee_id, target_date, (NotificationType.CHECK_IN_REMINDER, NotificationType.CHECK_IN_MISSING, NotificationType.LATE_CHECK_IN), now)
    else:
        resolve_notifications(db, employee_id, target_date, (NotificationType.CHECK_OUT_REMINDER, NotificationType.CHECK_OUT_MISSING), now)