from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user
from app.core.database import get_db
from app.models.employee import Employee
from app.models.notification import Notification
from app.models.user import User, UserRole
from app.schemas.notification import NotificationCountResponse, NotificationResponse
from app.services.notification_service import sync_attendance_notifications

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])


def _employee_for_user(db: Session, user: User) -> Employee:
    employee = db.query(Employee).filter(Employee.user_id == user.id).first()
    if employee is None:
        raise HTTPException(status_code=404, detail="Employee profile not found")
    return employee


@router.get("", response_model=list[NotificationResponse])
def get_notifications(include_resolved: bool = Query(False), limit: int = Query(30, ge=1, le=100), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role == UserRole.EMPLOYEE:
        employee = _employee_for_user(db, current_user)
        sync_attendance_notifications(db, employee)
        db.commit()
        query = db.query(Notification).filter(Notification.employee_id == employee.id)
    else:
        query = db.query(Notification)
    if not include_resolved:
        query = query.filter(Notification.resolved_at.is_(None))
    return query.order_by(Notification.created_at.desc()).limit(limit).all()


@router.get("/unread-count", response_model=NotificationCountResponse)
def get_unread_count(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role == UserRole.EMPLOYEE:
        employee = _employee_for_user(db, current_user)
        sync_attendance_notifications(db, employee)
        db.commit()
        query = db.query(Notification).filter(Notification.employee_id == employee.id)
    else:
        query = db.query(Notification)
    count = query.filter(Notification.resolved_at.is_(None), Notification.is_read.is_(False)).count()
    return NotificationCountResponse(unread_count=count)


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
def mark_notification_read(notification_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    notification = db.query(Notification).filter(Notification.id == notification_id).first()
    if notification is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    if current_user.role == UserRole.EMPLOYEE and notification.employee.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only update your own notifications")
    notification.is_read = True
    notification.read_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(notification)
    return notification