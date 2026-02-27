from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from uuid import UUID
from app.database import get_db
from app.schemas.notification import NotificationListResponse, NotificationResponse, UnreadCountResponse
from app.services.notification_service import NotificationService
from app.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("/unread-count", response_model=UnreadCountResponse)
async def get_unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """O'qilmagan bildirishnomalar soni"""
    service = NotificationService(db)
    count = service.get_unread_count(current_user.id)
    return {"count": count}


@router.get("", response_model=NotificationListResponse)
async def get_notifications(
    is_read: Optional[bool] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Bildirishnomalar ro'yxati"""
    service = NotificationService(db)
    items, unread_count = service.get_notifications(
        user_id=current_user.id,
        is_read=is_read,
        limit=limit
    )
    return {"items": items, "unread_count": unread_count}


@router.put("/{notification_id}/read", response_model=NotificationResponse)
async def mark_read(
    notification_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Bitta bildirishnomani o'qildi deb belgilash"""
    service = NotificationService(db)
    service.mark_read(notification_id, current_user.id)
    # Updated notification ni qaytarish
    from app.models.notification import Notification
    notif = db.query(Notification).filter(Notification.id == notification_id).first()
    return notif


@router.put("/read-all", response_model=UnreadCountResponse)
async def mark_all_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Barcha bildirishnomalarni o'qildi deb belgilash"""
    service = NotificationService(db)
    service.mark_all_read(current_user.id)
    return {"count": 0}