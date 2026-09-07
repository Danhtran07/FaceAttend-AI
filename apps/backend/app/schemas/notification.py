from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.models.notification import NotificationSeverity, NotificationType


class NotificationResponse(BaseModel):
    id: int
    notification_type: NotificationType
    severity: NotificationSeverity
    attendance_date: date
    title: str
    message: str
    action_label: str | None
    action_path: str | None
    is_read: bool
    created_at: datetime
    read_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class NotificationCountResponse(BaseModel):
    unread_count: int
