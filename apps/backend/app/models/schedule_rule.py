from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ScheduleRule(Base):
    __tablename__ = "schedule_rules"
    __table_args__ = (
        UniqueConstraint("schedule_id", "day_of_week", name="uq_schedule_rule_schedule_day"),
        CheckConstraint("day_of_week >= 0 AND day_of_week <= 6", name="ck_schedule_rule_day"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    schedule_id: Mapped[int] = mapped_column(
        ForeignKey("work_schedules.id", ondelete="CASCADE"), nullable=False
    )
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)
    shift_id: Mapped[int] = mapped_column(
        ForeignKey("shifts.id", ondelete="RESTRICT"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    schedule: Mapped["WorkSchedule"] = relationship("WorkSchedule", back_populates="rules")
    shift: Mapped["Shift"] = relationship("Shift", back_populates="schedule_rules")