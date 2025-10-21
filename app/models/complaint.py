"""Complaint models."""

from enum import Enum as PyEnum
from datetime import datetime
from typing import Optional, List

from sqlalchemy import String, Text, ForeignKey, Enum, Index, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin


class ComplaintCategory(str, PyEnum):
    """Complaint categories."""

    MAINTENANCE = "MAINTENANCE"
    CLEANLINESS = "CLEANLINESS"
    FOOD = "FOOD"
    ELECTRICITY = "ELECTRICITY"
    WATER = "WATER"
    SECURITY = "SECURITY"
    OTHER = "OTHER"


class ComplaintPriority(str, PyEnum):
    """Complaint priority."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"


class ComplaintStatus(str, PyEnum):
    """Complaint status."""

    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
    REJECTED = "REJECTED"


class Complaint(Base, TimestampMixin):
    """Complaint model."""

    __tablename__ = "complaints"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenant_profiles.id"), nullable=False)
    hostel_id: Mapped[int] = mapped_column(ForeignKey("hostels.id"), nullable=False)
    
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    
    category: Mapped[ComplaintCategory] = mapped_column(Enum(ComplaintCategory), nullable=False)
    priority: Mapped[ComplaintPriority] = mapped_column(
        Enum(ComplaintPriority), nullable=False, default=ComplaintPriority.MEDIUM
    )
    status: Mapped[ComplaintStatus] = mapped_column(
        Enum(ComplaintStatus), nullable=False, default=ComplaintStatus.OPEN
    )
    
    assigned_to: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships - FIXED: Removed duplicate hostel relationship
    tenant: Mapped["TenantProfile"] = relationship(
        "TenantProfile",
        back_populates="complaints"
    )
    hostel: Mapped["Hostel"] = relationship("Hostel", back_populates="complaints")
    assignee: Mapped[Optional["User"]] = relationship("User", foreign_keys=[assigned_to])
    comments: Mapped[List["ComplaintComment"]] = relationship(
        "ComplaintComment", back_populates="complaint", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_complaints_hostel_id", "hostel_id"),
        Index("idx_complaints_tenant_id", "tenant_id"),
        Index("idx_complaints_status", "status"),
    )


class ComplaintComment(Base, TimestampMixin):
    """Complaint comment model."""

    __tablename__ = "complaint_comments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    complaint_id: Mapped[int] = mapped_column(ForeignKey("complaints.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    
    comment: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Relationships
    complaint: Mapped["Complaint"] = relationship("Complaint", back_populates="comments")
    user: Mapped["User"] = relationship("User")

    __table_args__ = (Index("idx_complaint_comments_complaint_id", "complaint_id"),)