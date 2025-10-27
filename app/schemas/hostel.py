"""Hostel schemas."""

from typing import Optional
from pydantic import BaseModel, Field

from app.schemas.common import TimestampSchema


class HostelBase(BaseModel):
    """Base hostel schema."""
    
    name: str = Field(..., min_length=1, max_length=255)
    code: str = Field(..., min_length=3, max_length=50)
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None


class HostelCreate(HostelBase):
    """Create hostel schema."""
    pass


class HostelUpdate(BaseModel):
    """Update hostel schema."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    is_active: Optional[bool] = None


class HostelResponse(HostelBase, TimestampSchema):
    """Hostel response schema."""
    
    id: int
    is_active: bool
    
    class Config:
        from_attributes = True


class HostelWithStats(HostelResponse):
    """Hostel with statistics."""
    
    total_rooms: int = 0
    total_beds: int = 0
    occupied_beds: int = 0
    total_tenants: int = 0
    occupancy_rate: float = 0.0
    subscription_plan: Optional[str] = None