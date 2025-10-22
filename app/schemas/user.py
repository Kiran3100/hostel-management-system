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
        
        # CRITICAL FIX: Check for cached value first to avoid lazy loading
        if hasattr(user, '_cached_hostel_id'):
            data['hostel_id'] = user._cached_hostel_id
        # Map primary_hostel_id to hostel_id (for roles with primary_hostel_id)
        elif user.role.value in ['TENANT', 'VISITOR']:
            data['hostel_id'] = user.primary_hostel_id
        # For HOSTEL_ADMIN, try to get from loaded hostels list
        elif user.role.value == 'HOSTEL_ADMIN':
            # Only access hostels if they're already loaded (avoid lazy loading)
            try:
                # Check if hostels relationship is loaded
                from sqlalchemy.inspect import inspect
                insp = inspect(user)
                if 'hostels' in insp.unloaded:
                    # Not loaded, use primary_hostel_id as fallback
                    data['hostel_id'] = user.primary_hostel_id
                else:
                    # Already loaded, safe to access
                    data['hostel_id'] = user.hostels[0].id if user.hostels else None
            except:
                # Fallback to primary_hostel_id
                data['hostel_id'] = user.primary_hostel_id
        else:
            data['hostel_id'] = None
            
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