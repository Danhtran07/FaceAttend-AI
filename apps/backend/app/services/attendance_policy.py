from dataclasses import dataclass
from datetime import datetime, timedelta

from app.core.timezone import to_vietnam_time
from app.models.attendance import AttendanceStatus
from app.models.shift import Shift


@dataclass(frozen=True)
class AttendanceMetrics:
    late_minutes: int = 0
    early_leave_minutes: int = 0
    working_minutes: int = 0
    overtime_minutes: int = 0


def calculate_attendance_metrics(
    check_in: datetime | None,
    check_out: datetime | None,
    shift: Shift | None,
) -> AttendanceMetrics:
    if check_in is None:
        return AttendanceMetrics()

    local_check_in = to_vietnam_time(check_in)
    local_check_out = to_vietnam_time(check_out) if check_out is not None else None
    if shift is None:
        working_minutes = _elapsed_minutes(local_check_in, local_check_out)
        return AttendanceMetrics(working_minutes=working_minutes)

    shift_start = datetime.combine(local_check_in.date(), shift.start_time)
    shift_end = datetime.combine(local_check_in.date(), shift.end_time)
    if shift.is_overnight:
        shift_end += timedelta(days=1)

    late_threshold = shift_start + timedelta(minutes=shift.late_tolerance_minutes)
    late_minutes = _positive_minutes(local_check_in.replace(tzinfo=None) - late_threshold)

    if local_check_out is None:
        return AttendanceMetrics(late_minutes=late_minutes)

    local_check_out = local_check_out.replace(tzinfo=None)
    working_minutes = _elapsed_minutes(
        local_check_in.replace(tzinfo=None),
        local_check_out,
    )
    early_leave_minutes = _positive_minutes(shift_end - local_check_out)
    overtime_minutes = _positive_minutes(local_check_out - shift_end)

    return AttendanceMetrics(
        late_minutes=late_minutes,
        early_leave_minutes=early_leave_minutes,
        working_minutes=working_minutes,
        overtime_minutes=overtime_minutes,
    )


def _positive_minutes(delta: timedelta) -> int:
    return max(0, int(delta.total_seconds() // 60))


def _elapsed_minutes(
    start: datetime,
    end: datetime | None,
) -> int:
    if end is None:
        return 0
    return _positive_minutes(end - start)


def calculate_attendance_status(
    check_in: datetime | None,
    shift: Shift | None,
) -> AttendanceStatus:
    if check_in is None:
        return AttendanceStatus.ABSENT
    metrics = calculate_attendance_metrics(check_in, None, shift)
    if metrics.late_minutes > 0:
        return AttendanceStatus.LATE
    return AttendanceStatus.PRESENT