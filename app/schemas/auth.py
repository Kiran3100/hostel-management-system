"""Authentication schemas."""

from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.user import UserRole


class LoginRequest(BaseModel):
    """Login with email and password."""
    
    email: EmailStr
    password: str = Field(..., min_length=8)


class LoginResponse(BaseModel):
    """Login response with tokens."""
    
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_id: int
    role: UserRole


class OTPRequestRequest(BaseModel):
    """Request OTP for phone login."""
    
    phone: str = Field(..., pattern=r"^\+?[1-9]\d{1,14}$")
    hostel_code: str = Field(..., min_length=3, max_length=50)


class OTPVerifyRequest(BaseModel):
    """Verify OTP and login."""
    
    phone: str = Field(..., pattern=r"^\+?[1-9]\d{1,14}$")
    otp: str = Field(..., min_length=4, max_length=6)


class RefreshTokenRequest(BaseModel):
    """Refresh access token."""
    
    refresh_token: str


class RegisterRequest(BaseModel):
    """User registration (admin-only)."""
    
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, pattern=r"^\+?[1-9]\d{1,14}$")
    password: Optional[str] = Field(None, min_length=8)
    role: UserRole
    hostel_code: Optional[str] = None
    
    @field_validator("email", "phone")
    @classmethod
    def check_contact_method(cls, v, info):
        """At least one of email or phone must be provided."""
        # This will be checked in the service layer
        return v


class ChangePasswordRequest(BaseModel):
    """Change password."""
    
    old_password: str
    new_password: str = Field(..., min_length=8)