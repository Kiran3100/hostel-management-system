"""Notice/announcement models."""

from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import String, Text, ForeignKey, Enum, Index, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin


class NoticePriority(str, PyEnum):
    """Notice priority."""

    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    URGENT = "URGENT"


class Notice(Base, TimestampMixin):
    """Notice/announcement model."""

    __tablename__ = "notices"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    hostel_id: Mapped[int] = mapped_column(ForeignKey("hostels.id"), nullable=False)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[NoticePriority] = mapped_column(
        Enum(NoticePriority), nullable=False, default=NoticePriority.NORMAL
    )
    
    published_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    hostel: Mapped["Hostel"] = relationship("Hostel", back_populates="notices")
    author: Mapped["User"] = relationship("User")

    __table_args__ = (
        Index("idx_notices_hostel_id", "hostel_id"),
        Index("idx_notices_published_at", "published_at"),
    )