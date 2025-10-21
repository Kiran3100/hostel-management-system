"""Fee and payment schemas."""

from typing import Optional
from decimal import Decimal
from datetime import date
from pydantic import BaseModel, Field

from app.models.fee import FeeFrequency, InvoiceStatus, PaymentStatus
from app.schemas.common import TimestampSchema


class FeeScheduleBase(BaseModel):
    """Base fee schedule schema."""
    
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    frequency: FeeFrequency
    due_day: int = Field(..., ge=1, le=31)


class FeeScheduleCreate(FeeScheduleBase):
    """Create fee schedule."""
    
    hostel_id: int


class FeeScheduleUpdate(BaseModel):
    """Update fee schedule."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    amount: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    frequency: Optional[FeeFrequency] = None
    due_day: Optional[int] = Field(None, ge=1, le=31)
    is_active: Optional[bool] = None


class FeeScheduleResponse(FeeScheduleBase, TimestampSchema):
    """Fee schedule response."""
    
    id: int
    hostel_id: int
    is_active: bool
    
    class Config:
        from_attributes = True


class InvoiceCreate(BaseModel):
    """Create invoice."""
    
    tenant_id: int
    fee_schedule_id: Optional[int] = None
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    due_date: date
    notes: Optional[str] = None


class InvoiceResponse(TimestampSchema):
    """Invoice response."""
    
    id: int
    hostel_id: int
    tenant_id: int
    fee_schedule_id: Optional[int]
    invoice_number: str
    amount: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    due_date: date
    status: InvoiceStatus
    paid_amount: Decimal
    paid_at: Optional[date]
    notes: Optional[str]
    
    class Config:
        from_attributes = True


class PaymentInitiateRequest(BaseModel):
    """Initiate payment."""
    
    invoice_id: int
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    gateway: str = Field(default="razorpay")


class PaymentResponse(TimestampSchema):
    """Payment response."""
    
    id: int
    invoice_id: int
    hostel_id: int
    tenant_id: int
    amount: Decimal
    status: PaymentStatus
    gateway: str
    transaction_id: Optional[str]
    receipt_url: Optional[str]
    receipt_number: Optional[str]
    payment_method: Optional[str]
    paid_at: Optional[date]
    
    class Config:
        from_attributes = True


class ReceiptResponse(BaseModel):
    """Payment receipt."""
    
    receipt_number: str
    payment_id: int
    invoice_number: str
    tenant_name: str
    amount: Decimal
    paid_at: date
    payment_method: str
    hostel_name: str