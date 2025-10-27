"""Leave application schemas."""

from typing import Optional
from datetime import date, datetime
from pydantic import BaseModel, Field, field_validator

from app.models.leave import LeaveStatus
from app.schemas.common import TimestampSchema


class LeaveApplicationBase(BaseModel):
    """Base leave application schema."""
    
    start_date: date
    end_date: date
    reason: str = Field(..., min_length=1)
    
    @field_validator("end_date")
    @classmethod
    def validate_dates(cls, v, info):
        if "start_date" in info.data and v < info.data["start_date"]:
            raise ValueError("end_date must be after start_date")
        return v


class LeaveApplicationCreate(LeaveApplicationBase):
    """Create leave application."""
    pass


class LeaveApplicationResponse(LeaveApplicationBase, TimestampSchema):
    """Leave application response."""
    
    id: int
    hostel_id: int
    tenant_id: int
    status: LeaveStatus
    approver_id: Optional[int]
    approved_at: Optional[datetime]
    approver_notes: Optional[str]
    
    class Config:
        from_attributes = True


class LeaveApprovalRequest(BaseModel):
    """Approve/reject leave."""
    
    approved: bool
    notes: Optional[str] = None