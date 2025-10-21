"""Tenant profile and check-in/out models."""

from enum import Enum as PyEnum
from typing import Optional, List
from datetime import date

from sqlalchemy import String, Integer, Date, ForeignKey, Enum, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, SoftDeleteMixin


class TenantProfile(Base, TimestampMixin, SoftDeleteMixin):
    """Tenant profile model."""

    __tablename__ = "tenant_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, nullable=False)
    hostel_id: Mapped[int] = mapped_column(ForeignKey("hostels.id"), nullable=False)
    
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    gender: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    id_proof_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    id_proof_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    id_proof_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    guardian_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    guardian_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    guardian_email: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    emergency_contact: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    # Bed assignment fields - use_alter=True to break circular dependency with beds table
    current_bed_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("beds.id", use_alter=True, name="fk_tenant_current_bed"), 
        nullable=True
    )
    check_in_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    check_out_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="tenant_profile")
    hostel: Mapped["Hostel"] = relationship("Hostel", back_populates="tenants")
    
    # Bed relationships
    current_bed: Mapped[Optional["Bed"]] = relationship(
        "Bed",
        foreign_keys=[current_bed_id],
        uselist=False,
        overlaps="tenant,occupied_bed"
    )
    
    occupied_bed: Mapped[Optional["Bed"]] = relationship(
        "Bed",
        foreign_keys="Bed.tenant_id",
        back_populates="tenant",
        uselist=False,
        overlaps="current_bed"
    )
    
    # Financial relationships
    invoices: Mapped[List["Invoice"]] = relationship(
        "Invoice",
        back_populates="tenant",
        foreign_keys="Invoice.tenant_id",
        cascade="all, delete-orphan"
    )
    
    payments: Mapped[List["Payment"]] = relationship(
        "Payment",
        back_populates="tenant",
        foreign_keys="Payment.tenant_id",
        cascade="all, delete-orphan"
    )
    
    # Check-in/out records
    check_in_outs: Mapped[List["CheckInOut"]] = relationship(
        "CheckInOut",
        back_populates="tenant",
        cascade="all, delete-orphan"
    )
    
    # Complaints filed by tenant
    complaints: Mapped[List["Complaint"]] = relationship(
        "Complaint",
        back_populates="tenant",
        foreign_keys="Complaint.tenant_id",
        cascade="all, delete-orphan"
    )
    
    # Leave applications
    leave_applications: Mapped[List["LeaveApplication"]] = relationship(
        "LeaveApplication",
        back_populates="tenant",
        foreign_keys="LeaveApplication.tenant_id",
        cascade="all, delete-orphan"
    )


class CheckInOutStatus(str, PyEnum):
    """Check-in/out status."""
    
    CHECKED_IN = "CHECKED_IN"
    CHECKED_OUT = "CHECKED_OUT"


class CheckInOut(Base, TimestampMixin):
    """Check-in/out record model."""

    __tablename__ = "check_in_outs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenant_profiles.id"), nullable=False)
    hostel_id: Mapped[int] = mapped_column(ForeignKey("hostels.id"), nullable=False)
    bed_id: Mapped[int] = mapped_column(ForeignKey("beds.id"), nullable=False)
    
    check_in_date: Mapped[date] = mapped_column(Date, nullable=False)
    check_out_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    status: Mapped[CheckInOutStatus] = mapped_column(
        Enum(CheckInOutStatus),
        nullable=False,
        default=CheckInOutStatus.CHECKED_IN
    )
    
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    tenant: Mapped["TenantProfile"] = relationship(
        "TenantProfile",
        back_populates="check_in_outs"
    )
    
    bed: Mapped["Bed"] = relationship(
        "Bed",
        back_populates="check_in_outs"
    )
    
    hostel: Mapped["Hostel"] = relationship("Hostel")