"""Fee schedule, invoice, and payment models (NO TAX)."""

from decimal import Decimal
from datetime import date, datetime
from enum import Enum as PyEnum
from typing import Optional, List

from sqlalchemy import String, Numeric, ForeignKey, Date, DateTime, Enum, Index, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin


class FeeFrequency(str, PyEnum):
    """Fee payment frequency."""

    MONTHLY = "MONTHLY"
    QUARTERLY = "QUARTERLY"
    HALF_YEARLY = "HALF_YEARLY"
    YEARLY = "YEARLY"
    ONE_TIME = "ONE_TIME"


class InvoiceStatus(str, PyEnum):
    """Invoice status."""

    PENDING = "PENDING"
    PAID = "PAID"
    PARTIAL = "PARTIAL"
    OVERDUE = "OVERDUE"
    CANCELLED = "CANCELLED"


class PaymentStatus(str, PyEnum):
    """Payment status."""

    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"


class FeeSchedule(Base, TimestampMixin):
    """Fee schedule model."""

    __tablename__ = "fee_schedules"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    hostel_id: Mapped[int] = mapped_column(ForeignKey("hostels.id"), nullable=False)
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    frequency: Mapped[FeeFrequency] = mapped_column(Enum(FeeFrequency), nullable=False)
    due_day: Mapped[int] = mapped_column(nullable=False)  # Day of month for payment
    
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    
    # Relationships
    hostel: Mapped["Hostel"] = relationship("Hostel", back_populates="fee_schedules")
    invoices: Mapped[List["Invoice"]] = relationship("Invoice", back_populates="fee_schedule")

    __table_args__ = (Index("idx_fee_schedules_hostel_id", "hostel_id"),)


class Invoice(Base, TimestampMixin):
    """Invoice model (NO TAX FIELDS)."""

    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    hostel_id: Mapped[int] = mapped_column(ForeignKey("hostels.id"), nullable=False)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenant_profiles.id"), nullable=False)
    fee_schedule_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("fee_schedules.id"), nullable=True
    )
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10,2), nullable=False)
    invoice_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    # NO TAX - total_amount equals amount
    
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[InvoiceStatus] = mapped_column(
        Enum(InvoiceStatus), nullable=False, default=InvoiceStatus.PENDING
    )
    
    paid_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"))
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    hostel: Mapped["Hostel"] = relationship("Hostel", back_populates="invoices")
    tenant: Mapped["TenantProfile"] = relationship("TenantProfile", back_populates="invoices")
    fee_schedule: Mapped[Optional["FeeSchedule"]] = relationship(
        "FeeSchedule", back_populates="invoices"
    )
    payments: Mapped[List["Payment"]] = relationship("Payment", back_populates="invoice")

    __table_args__ = (
        Index("idx_invoices_hostel_id", "hostel_id"),
        Index("idx_invoices_tenant_id", "tenant_id"),
        Index("idx_invoices_status", "status"),
        Index("idx_invoices_due_date", "due_date"),
    )


class Payment(Base, TimestampMixin):
    """Payment model."""

    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("invoices.id"), nullable=False)
    hostel_id: Mapped[int] = mapped_column(ForeignKey("hostels.id"), nullable=False)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenant_profiles.id"), nullable=False)
    
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus), nullable=False, default=PaymentStatus.PENDING
    )
    
    gateway: Mapped[str] = mapped_column(String(50), nullable=False)  # razorpay, mock
    transaction_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    idempotency_key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    
    receipt_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    receipt_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    payment_method: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # RENAMED: metadata -> payment_metadata (metadata is reserved in SQLAlchemy)
    payment_metadata: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON as text
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="payments")
    hostel: Mapped["Hostel"] = relationship("Hostel", back_populates="payments")
    tenant: Mapped["TenantProfile"] = relationship("TenantProfile", back_populates="payments")

    __table_args__ = (
        Index("idx_payments_hostel_id", "hostel_id"),
        Index("idx_payments_tenant_id", "tenant_id"),
        Index("idx_payments_invoice_id", "invoice_id"),
        Index("idx_payments_idempotency_key", "idempotency_key"),
        Index("idx_payments_status", "status"),
        Index("idx_payments_created_at", "created_at"),
    )