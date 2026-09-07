from datetime import datetime

from sqlalchemy import (
    ForeignKey,
    Integer,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.timezone import UTCDateTime


class ScheduleRule(Base):
    __tablename__ = "schedule_rules"
    __table_args__ = (
        UniqueConstraint(
            "schedule_id",
            "day_of_week",
            name="uq_schedule_rule_day",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    schedule_id: Mapped[int] = mapped_column(
        ForeignKey(
            "work_schedules.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    shift_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "shifts.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    day_of_week: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime(),
        server_default=func.now(),
        nullable=False,
    )

    schedule = relationship(
        "WorkSchedule",
        back_populates="rules",
    )

    shift = relationship(
        "Shift",
        back_populates="schedule_rules",
    )