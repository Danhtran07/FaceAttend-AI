from datetime import date, datetime
from enum import Enum

from sqlalchemy import Date, DateTime, Enum as SQLEnum, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.timezone import UTCDateTime


class NotificationSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    URGENT = "urgent"
    SUCCESS = "success"


class NotificationType(str, Enum):
    CHECK_IN_REMINDER = "CHECK_IN_REMINDER"
    CHECK_IN_MISSING = "CHECK_IN_MISSING"
    LATE_CHECK_IN = "LATE_CHECK_IN"
    CHECK_IN_SUCCESS = "CHECK_IN_SUCCESS"
    CHECK_OUT_REMINDER = "CHECK_OUT_REMINDER"
    CHECK_OUT_MISSING = "CHECK_OUT_MISSING"
    CHECK_OUT_SUCCESS = "CHECK_OUT_SUCCESS"
    LEAVE_APPROVED = "LEAVE_APPROVED"
    LEAVE_REJECTED = "LEAVE_REJECTED"
    OT_PENDING = "OT_PENDING"
    OT_APPROVED = "OT_APPROVED"
    OT_REJECTED = "OT_REJECTED"
    ATTENDANCE_ANOMALY = "ATTENDANCE_ANOMALY"


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (
        UniqueConstraint(
            "employee_id",
            "notification_type",
            "attendance_date",
            name="uq_notification_employee_type_date",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True)
    notification_type: Mapped[NotificationType] = mapped_column(SQLEnum(NotificationType, name="notification_type"), nullable=False)
    severity: Mapped[NotificationSeverity] = mapped_column(SQLEnum(NotificationSeverity, name="notification_severity"), nullable=False)
    attendance_date: Mapped[date] = mapped_column(Date, nullable=False)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    action_label: Mapped[str | None] = mapped_column(String(80), nullable=True)
    action_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_read: Mapped[bool] = mapped_column(default=False, server_default="false", nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), server_default=func.now(), nullable=False)
    read_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)

    employee: Mapped["Employee"] = relationship("Employee")
