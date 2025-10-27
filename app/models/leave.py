"""Leave application models."""

from datetime import date, datetime
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import String, Text, ForeignKey, Date, DateTime, Enum, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin


class LeaveStatus(str, PyEnum):
    """Leave application status."""

    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class LeaveApplication(Base, TimestampMixin):
    """Leave application model."""

    __tablename__ = "leave_applications"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenant_profiles.id"), nullable=False)
    hostel_id: Mapped[int] = mapped_column(ForeignKey("hostels.id"), nullable=False)
    
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    
    status: Mapped[LeaveStatus] = mapped_column(
        Enum(LeaveStatus), nullable=False, default=LeaveStatus.PENDING
    )
    
    approver_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    approver_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    hostel: Mapped["Hostel"] = relationship("Hostel", back_populates="leave_applications")
    tenant: Mapped["TenantProfile"] = relationship(
        "TenantProfile",
        back_populates="leave_applications"
    )
    hostel: Mapped["Hostel"] = relationship("Hostel", back_populates="leave_applications")
    approver: Mapped[Optional["User"]] = relationship("User", foreign_keys=[approver_id])

    __table_args__ = (
        Index("idx_leave_applications_hostel_id", "hostel_id"),
        Index("idx_leave_applications_tenant_id", "tenant_id"),
        Index("idx_leave_applications_status", "status"),
    )