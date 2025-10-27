"""Tenant profile schemas."""

from typing import Optional
from datetime import date
from pydantic import BaseModel, Field, EmailStr

from app.schemas.common import TimestampSchema


class TenantProfileBase(BaseModel):
    """Base tenant profile schema."""
    
    full_name: str = Field(..., min_length=1, max_length=100)
    date_of_birth: Optional[date] = None
    gender: Optional[str] = Field(None, max_length=20)
    
    id_proof_type: Optional[str] = Field(None, max_length=50)
    id_proof_number: Optional[str] = Field(None, max_length=100)
    id_proof_url: Optional[str] = Field(None, max_length=500)
    
    guardian_name: Optional[str] = Field(None, max_length=100)
    guardian_phone: Optional[str] = Field(None, max_length=20)
    guardian_email: Optional[EmailStr] = None
    emergency_contact: Optional[str] = Field(None, max_length=20)


class TenantProfileCreate(TenantProfileBase):
    """Create tenant profile schema."""
    
    user_id: int
    hostel_id: int


class TenantProfileUpdate(BaseModel):
    """Update tenant profile schema."""
    
    full_name: Optional[str] = Field(None, min_length=1, max_length=100)
    date_of_birth: Optional[date] = None
    gender: Optional[str] = Field(None, max_length=20)
    
    id_proof_type: Optional[str] = Field(None, max_length=50)
    id_proof_number: Optional[str] = Field(None, max_length=100)
    id_proof_url: Optional[str] = Field(None, max_length=500)
    
    guardian_name: Optional[str] = Field(None, max_length=100)
    guardian_phone: Optional[str] = Field(None, max_length=20)
    guardian_email: Optional[EmailStr] = None
    emergency_contact: Optional[str] = Field(None, max_length=20)


class TenantProfileResponse(TenantProfileBase, TimestampSchema):
    """Tenant profile response schema."""
    
    id: int
    user_id: int
    hostel_id: int
    
    # Make these fields optional since they can be None
    current_bed_id: Optional[int] = None
    check_in_date: Optional[date] = None
    check_out_date: Optional[date] = None
    
    class Config:
        from_attributes = True


class CheckInRequest(BaseModel):
    """Check-in request schema."""
    
    bed_id: int
    check_in_date: date = Field(default_factory=date.today)


class CheckOutRequest(BaseModel):
    """Check-out request schema."""
    
    check_out_date: date = Field(default_factory=date.today)
    notes: Optional[str] = None