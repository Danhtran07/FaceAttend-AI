from datetime import date, datetime
from enum import Enum

from sqlalchemy import (
    Date,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Integer,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class AttendanceStatus(str, Enum):
    PRESENT = "PRESENT"
    LATE = "LATE"
    ABSENT = "ABSENT"


class Attendance(Base):
    __tablename__ = "attendance"

    __table_args__ = (
        UniqueConstraint(
            "employee_id",
            "date",
            name="uq_attendance_employee_date",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id"),
        nullable=False,
    )

    date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    check_in: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    check_out: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    status: Mapped[AttendanceStatus] = mapped_column(
        SQLEnum(
            AttendanceStatus,
            name="attendance_status",
        ),
        nullable=False,
        default=AttendanceStatus.ABSENT,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    employee: Mapped["Employee"] = relationship(
        "Employee",
        back_populates="attendance",
    )