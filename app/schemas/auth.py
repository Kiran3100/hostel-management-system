"""Authentication schemas - UPDATED WITH MULTI-HOSTEL SUPPORT."""

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
    """User registration (admin-only) - UPDATED WITH MULTI-HOSTEL SUPPORT."""
    
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, pattern=r"^\+?[1-9]\d{1,14}$")
    password: Optional[str] = Field(None, min_length=8)
    role: UserRole
    
    # ✅ NEW: Support both single and multiple hostel codes
    hostel_code: Optional[str] = None  # Single code (backward compatible)
    hostel_codes: Optional[list[str]] = None  # Multiple codes for HOSTEL_ADMIN
    
    @field_validator("email", "phone")
    @classmethod
    def check_contact_method(cls, v, info):
        """At least one of email or phone must be provided."""
        # This will be checked in the service layer
        return v
    
    @field_validator("hostel_codes")
    @classmethod
    def validate_hostel_codes(cls, v):
        """Validate hostel codes list."""
        if v is not None:
            # Remove duplicates
            v = list(set(v))
            # Validate each code format
            for code in v:
                if not code or len(code) < 3 or len(code) > 50:
                    raise ValueError(f"Invalid hostel code: {code}")
        return v
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "title": "Single Hostel Admin",
                    "value": {
                        "email": "admin@example.com",
                        "password": "SecurePass123",
                        "role": "HOSTEL_ADMIN",
                        "hostel_code": "HST001"
                    }
                },
                {
                    "title": "Multi-Hostel Admin",
                    "value": {
                        "email": "admin@example.com",
                        "password": "SecurePass123",
                        "role": "HOSTEL_ADMIN",
                        "hostel_codes": ["HST001", "HST002", "HST003"]
                    }
                },
                {
                    "title": "Tenant",
                    "value": {
                        "email": "tenant@example.com",
                        "phone": "+919876543210",
                        "password": "SecurePass123",
                        "role": "TENANT",
                        "hostel_code": "HST001"
                    }
                }
            ]
        }


class AddHostelRequest(BaseModel):
    """Add hostel to existing admin."""
    
    hostel_code: str = Field(..., min_length=3, max_length=50)
    
    class Config:
        json_schema_extra = {
            "example": {
                "hostel_code": "HST002"
            }
        }


class RemoveHostelRequest(BaseModel):
    """Remove hostel from admin."""
    
    hostel_id: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "hostel_id": 2
            }
        }


class ChangePasswordRequest(BaseModel):
    """Change password."""
    
    old_password: str
    new_password: str = Field(..., min_length=8)