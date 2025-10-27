"""Self-registration schemas for visitors."""

from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator
import re


class VisitorSelfRegisterRequest(BaseModel):
    """Self-registration request for visitors."""
    
    email: EmailStr
    password: str = Field(..., min_length=8)
    confirm_password: str = Field(..., min_length=8)
    hostel_code: str = Field(..., min_length=3, max_length=50)
    full_name: Optional[str] = Field(None, max_length=100)
    accept_terms: bool = Field(..., description="Must accept terms and conditions")
    
    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v):
        """Validate password meets strength requirements."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one number")
        
        # Check for special characters (recommended)
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            # Just a warning - don't fail
            pass
        
        return v
    
    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, v, info):
        """Verify passwords match."""
        if 'password' in info.data and v != info.data['password']:
            raise ValueError("Passwords do not match")
        return v
    
    @field_validator("accept_terms")
    @classmethod
    def validate_terms_accepted(cls, v):
        """Ensure terms are accepted."""
        if not v:
            raise ValueError("You must accept the terms and conditions")
        return v


class VisitorSelfRegisterResponse(BaseModel):
    """Self-registration response."""
    
    message: str
    email: str
    hostel_name: str
    expires_at: str
    verification_required: bool = True
    next_steps: list[str] = [
        "Check your email for verification link",
        "Verify your email within 24 hours",
        "Login to explore hostel information",
    ]


class EmailVerificationRequest(BaseModel):
    """Email verification request."""
    
    token: str


class EmailVerificationResponse(BaseModel):
    """Email verification response."""
    
    message: str
    email_verified: bool
    can_login: bool


class ResendVerificationRequest(BaseModel):
    """Resend verification email request."""
    
    email: EmailStr