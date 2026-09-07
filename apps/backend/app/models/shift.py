from datetime import datetime, time

from sqlalchemy import Boolean, CheckConstraint, DateTime, Integer, String, Time, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Shift(Base):
    __tablename__ = "shifts"
    __table_args__ = (
        CheckConstraint(
            "late_tolerance_minutes >= 0",
            name="ck_shift_late_tolerance",
        ),
        CheckConstraint(
            "early_checkin_minutes >= 0",
            name="ck_shift_early_checkin",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    break_start_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    break_end_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    late_tolerance_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    early_checkin_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_overnight: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    schedule_rules: Mapped[list["ScheduleRule"]] = relationship(
        "ScheduleRule", back_populates="shift"
    )