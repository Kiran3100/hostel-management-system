from enum import Enum as PyEnum
from typing import Optional, List
from datetime import date

from sqlalchemy import String, Boolean, Text, ForeignKey, Enum, Index, Date, JSON, Table, Column, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, SoftDeleteMixin


class PlanTier(str, PyEnum):
    """Subscription plan tiers."""

    FREE = "FREE"
    STANDARD = "STANDARD"
    PREMIUM = "PREMIUM"


class SubscriptionStatus(str, PyEnum):
    """Subscription status."""

    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"
    TRIAL = "TRIAL"


from app.models.associations import user_hostel_association


class Plan(Base, TimestampMixin):
    """Subscription plan model with comprehensive limits."""

    __tablename__ = "plans"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    tier: Mapped[PlanTier] = mapped_column(Enum(PlanTier), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Resource Limits
    max_hostels: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    max_tenants_per_hostel: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    max_rooms_per_hostel: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    max_admins_per_hostel: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    max_storage_mb: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Feature Flags (JSON)
    features: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Relationships
    subscriptions: Mapped[List["Subscription"]] = relationship(
        "Subscription", back_populates="plan"
    )


class Hostel(Base, TimestampMixin, SoftDeleteMixin):  # ✅ Must inherit SoftDeleteMixin
    """Hostel model with timezone support."""

    __tablename__ = "hostels"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    pincode: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Timezone for display
    timezone: Mapped[str] = mapped_column(String(50), nullable=False, default="Asia/Kolkata")
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Relationships - FIXED: Single relationship for admins using association table
    admins: Mapped[List["User"]] = relationship(
        "User",
        secondary=user_hostel_association,
        back_populates="hostels"
    )
    
    subscription: Mapped[Optional["Subscription"]] = relationship(
        "Subscription", back_populates="hostel", uselist=False
    )
    rooms: Mapped[List["Room"]] = relationship("Room", back_populates="hostel")
    tenants: Mapped[List["TenantProfile"]] = relationship("TenantProfile", back_populates="hostel")
    fee_schedules: Mapped[List["FeeSchedule"]] = relationship("FeeSchedule", back_populates="hostel")
    invoices: Mapped[List["Invoice"]] = relationship("Invoice", back_populates="hostel")
    payments: Mapped[List["Payment"]] = relationship("Payment", back_populates="hostel")
    complaints: Mapped[List["Complaint"]] = relationship("Complaint", back_populates="hostel")
    notices: Mapped[List["Notice"]] = relationship("Notice", back_populates="hostel")
    mess_menus: Mapped[List["MessMenu"]] = relationship("MessMenu", back_populates="hostel")
    leave_applications: Mapped[List["LeaveApplication"]] = relationship(
        "LeaveApplication", back_populates="hostel"
    )
    support_tickets: Mapped[List["SupportTicket"]] = relationship(
        "SupportTicket", back_populates="hostel"
    )
    
    __table_args__ = (
        Index("idx_hostels_code", "code"),
        Index("idx_hostels_is_active", "is_active"),
    )


class Subscription(Base, TimestampMixin):
    """Subscription model."""

    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    hostel_id: Mapped[int] = mapped_column(ForeignKey("hostels.id"), nullable=False, unique=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("plans.id"), nullable=False)
    
    status: Mapped[SubscriptionStatus] = mapped_column(
        Enum(SubscriptionStatus), nullable=False, default=SubscriptionStatus.TRIAL
    )
    
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    auto_renew: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Relationships
    hostel: Mapped["Hostel"] = relationship("Hostel", back_populates="subscription")
    plan: Mapped["Plan"] = relationship("Plan", back_populates="subscriptions")

    __table_args__ = (
        Index("idx_subscriptions_hostel_id", "hostel_id"),
        Index("idx_subscriptions_status", "status"),
    )