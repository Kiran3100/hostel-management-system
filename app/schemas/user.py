# app/schemas/auth.py - UPDATE

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
    """Hostel Admin registration - FIXED to only allow hostel admin registration."""
    
    email: EmailStr
    phone: str = Field(..., pattern=r"^\+?[1-9]\d{1,14}$")
    password: str = Field(..., min_length=8)
    hostel_id: int = Field(..., description="Hostel ID that this admin will manage")
    
    # Optional fields
    full_name: Optional[str] = Field(None, max_length=100, description="Admin's full name")


class ChangePasswordRequest(BaseModel):
    """Change password."""
    
    old_password: str
    new_password: str = Field(..., min_length=8)