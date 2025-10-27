"""Notification and device token models."""

from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import String, Text, ForeignKey, DateTime, Boolean, Enum, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin


class NotificationType(str, PyEnum):
    """Notification types."""

    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    SUCCESS = "SUCCESS"


class Platform(str, PyEnum):
    """Device platforms."""

    IOS = "IOS"
    ANDROID = "ANDROID"
    WEB = "WEB"


class Notification(Base, TimestampMixin):
    """Notification model."""

    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    hostel_id: Mapped[Optional[int]] = mapped_column(ForeignKey("hostels.id"), nullable=True)
    
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    notification_type: Mapped[NotificationType] = mapped_column(
        Enum(NotificationType), nullable=False, default=NotificationType.INFO
    )
    
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="notifications")

    __table_args__ = (
        Index("idx_notifications_user_id", "user_id"),
        Index("idx_notifications_is_read", "is_read"),
    )


class DeviceToken(Base, TimestampMixin):
    """Device token model for push notifications."""

    __tablename__ = "device_tokens"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    
    token: Mapped[str] = mapped_column(String(500), nullable=False)
    platform: Mapped[Platform] = mapped_column(Enum(Platform), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="device_tokens")

    __table_args__ = (
        Index("idx_device_tokens_user_id", "user_id"),
        Index("idx_device_tokens_token", "token", unique=True),
    )