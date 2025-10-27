"""User schemas - FIXED LAZY LOADING."""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator

from app.models.user import UserRole
from app.schemas.common import TimestampSchema


class UserBase(BaseModel):
    """Base user schema."""
    
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    role: UserRole


class UserCreate(UserBase):
    """Create user schema."""
    
    password: Optional[str] = Field(None, min_length=8)
    hostel_id: Optional[int] = None


class UserUpdate(BaseModel):
    """Update user schema."""
    
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    """User response schema - FIXED LAZY LOADING."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    email: Optional[str] = None
    phone: Optional[str] = None
    role: UserRole
    hostel_id: Optional[int] = None  # This will be computed from primary_hostel_id
    is_active: bool
    is_verified: bool
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

@classmethod
def from_orm(cls, user):
    """Custom from_orm to handle hostel_id mapping."""
    data = {
        'id': user.id,
        'email': user.email,
        'phone': user.phone,
        'role': user.role,
        'is_active': user.is_active,
        'is_verified': user.is_verified,
        'last_login': user.last_login,
        'created_at': user.created_at,
        'updated_at': user.updated_at,
    }
    
    # ✅ SIMPLIFIED: Always use cached value or primary_hostel_id
    if hasattr(user, '_cached_hostel_id'):
        data['hostel_id'] = user._cached_hostel_id
    else:
        # Just use primary_hostel_id for all roles
        data['hostel_id'] = user.primary_hostel_id
        
    return cls(**data)


class UserProfile(UserResponse):
    """Extended user profile."""
    
    hostel_name: Optional[str] = None
    hostel_ids: List[int] = []  # All hostels user has access to


class UserWithHostels(UserResponse):
    """User with all associated hostels (for admins)."""
    
    hostel_ids: List[int] = []
    
    @classmethod
    def from_orm(cls, user):
        """Custom from_orm to include all hostel IDs."""
        data = super().from_orm(user).__dict__
        data['hostel_ids'] = user.get_hostel_ids()
        return cls(**data)