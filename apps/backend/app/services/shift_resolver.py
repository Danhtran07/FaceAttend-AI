from datetime import date

from sqlalchemy.orm import Session

from app.models.schedule_assignment import ScheduleAssignment
from app.models.schedule_rule import ScheduleRule
from app.models.shift import Shift


def resolve_shift(
    db: Session,
    employee_id: int,
    target_date: date,
) -> Shift | None:
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
        return None

    rule = (
        db.query(ScheduleRule)
        .filter(
            ScheduleRule.schedule_id == assignment.schedule_id,
            ScheduleRule.day_of_week == target_date.isoweekday(),
        )
        .first()
    )
    if rule is None or rule.shift is None or not rule.shift.is_active:
        return None

    return rule.shift