"""Subscription schemas."""

from typing import Optional
from datetime import date
from pydantic import BaseModel, Field

from app.models.hostel import PlanTier, SubscriptionStatus
from app.schemas.common import TimestampSchema


class PlanResponse(BaseModel):
    """Subscription plan response."""
    
    id: int
    name: str
    tier: PlanTier
    description: Optional[str]
    max_tenants: Optional[int] = Field(alias="max_tenants_per_hostel")
    max_rooms: Optional[int] = Field(alias="max_rooms_per_hostel")
    max_admins: Optional[int] = Field(alias="max_admins_per_hostel")
    max_storage_mb: Optional[int]
    features: dict
    is_active: bool
    
    class Config:
        from_attributes = True
        populate_by_name = True


class SubscriptionCreate(BaseModel):
    """Create subscription."""
    
    hostel_id: int
    plan_id: int
    start_date: date
    end_date: Optional[date] = None
    auto_renew: bool = False


class SubscriptionUpdate(BaseModel):
    """Update subscription."""
    
    plan_id: Optional[int] = None
    status: Optional[SubscriptionStatus] = None
    end_date: Optional[date] = None
    auto_renew: Optional[bool] = None


class SubscriptionResponse(TimestampSchema):
    """Subscription response."""
    
    id: int
    hostel_id: int
    plan_id: int
    status: SubscriptionStatus
    start_date: date
    end_date: Optional[date]
    auto_renew: bool
    
    class Config:
        from_attributes = True


class SubscriptionWithPlan(SubscriptionResponse):
    """Subscription with plan details."""
    
    plan: PlanResponse


class FeatureUsageResponse(BaseModel):
    """Feature usage statistics."""
    
    hostel_id: int
    plan_name: str
    current_tenants: int
    max_tenants: Optional[int]
    current_rooms: int
    max_rooms: Optional[int]
    storage_used_mb: float
    max_storage_mb: Optional[int]
    usage_percentage: dict  # {"tenants": 75.0, "rooms": 50.0, ...}