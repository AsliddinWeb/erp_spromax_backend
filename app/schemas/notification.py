from typing import Optional, List
from pydantic import Field
from datetime import datetime
from uuid import UUID
from app.schemas.base import BaseSchema, BaseIDSchema


class NotificationResponse(BaseIDSchema):
    user_id: UUID
    title: str
    message: str
    type: str
    is_read: bool
    reference_type: Optional[str] = None
    reference_id: Optional[UUID] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificationListResponse(BaseSchema):
    items: List[NotificationResponse]
    unread_count: int


class UnreadCountResponse(BaseSchema):
    count: int