"""Notification schemas."""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel

from app.models.notification import NotificationType, Platform
from app.schemas.common import TimestampSchema


class NotificationResponse(TimestampSchema):
    """Notification response."""
    
    id: int
    user_id: int
    title: str
    message: str
    notification_type: NotificationType
    is_read: bool
    read_at: Optional[datetime]
    sent_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class DeviceTokenCreate(BaseModel):
    """Register device token."""
    
    token: str
    platform: Platform


class DeviceTokenResponse(TimestampSchema):
    """Device token response."""
    
    id: int
    user_id: int
    token: str
    platform: Platform
    is_active: bool
    
    class Config:
        from_attributes = True