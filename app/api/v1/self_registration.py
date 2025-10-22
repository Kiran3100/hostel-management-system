"""Self-registration endpoints for visitors."""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.database import get_db
from app.services.auth import AuthService
from app.adapters.otp.mock import MockOTPProvider
from app.config import settings
from app.core.rate_limit import rate_limit_by_ip
from app.exceptions import ConflictError, NotFoundError, ValidationError

# Import schemas (you'll need to create these)
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator
import re


# ===== SCHEMAS =====

class VisitorSelfRegisterRequest(BaseModel):
    """Self-registration request for visitors."""
    
    email: EmailStr
    password: str = Field(..., min_length=8)
    confirm_password: str = Field(..., min_length=8)
    hostel_code: str = Field(..., min_length=3, max_length=50, description="Hostel code (not ID)")
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
    hostel_code: str
    expires_at: str
    verification_required: bool = True
    next_steps: list[str]


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


class HostelListResponse(BaseModel):
    """Hostel information for registration."""
    
    name: str
    code: str
    city: Optional[str] = None
    state: Optional[str] = None


# ===== ROUTER =====

router = APIRouter(prefix="/auth/register", tags=["Visitors"])


def get_otp_provider():
    """Get OTP provider based on config."""
    if settings.otp_provider == "mock":
        return MockOTPProvider()
    return MockOTPProvider()


@router.post("/visitor", response_model=VisitorSelfRegisterResponse, status_code=status.HTTP_201_CREATED)
async def self_register_visitor(
    request: VisitorSelfRegisterRequest,
    db: AsyncSession = Depends(get_db),
    http_request: Request = None,
):
    """
    Self-registration endpoint for visitors.
    
    **Public Endpoint** - No authentication required.
    
    **Features:**
    - Email-based registration
    - Password strength validation
    - Automatic visitor role assignment
    - 30-day default access period
    - Email verification required
    - Rate limited to prevent abuse
    
    **Password Requirements:**
    - Minimum 8 characters
    - At least 1 uppercase letter
    - At least 1 lowercase letter
    - At least 1 number
    - Special characters recommended
    
    **Process:**
    1. User submits registration form with hostel code
    2. System validates email, password, and hostel code
    3. Creates visitor account (inactive until verified)
    4. Sends verification email
    5. User clicks verification link
    6. Account activated for 30 days
    """
    # Rate limiting (if enabled)
    if settings.rate_limit_enabled and http_request:
        await rate_limit_by_ip(http_request, max_requests=5)  # 5 registrations per minute per IP
    
    otp_provider = get_otp_provider()
    auth_service = AuthService(db, otp_provider)
    
    try:
        # Create visitor account using hostel_code
        user = await auth_service.self_register_visitor(
            email=request.email,
            password=request.password,
            hostel_code=request.hostel_code,  # Using hostel_code instead of hostel_id
            full_name=request.full_name,
        )
        
        # Get hostel details for response
        from app.repositories.hostel import HostelRepository
        from app.models.hostel import Hostel
        
        hostel_repo = HostelRepository(Hostel, db)
        hostel = await hostel_repo.get(user.primary_hostel_id)
        
        return VisitorSelfRegisterResponse(
            message="Registration successful! Please check your email to verify your account.",
            email=user.email,
            hostel_name=hostel.name if hostel else "Unknown",
            hostel_code=hostel.code if hostel else request.hostel_code,
            expires_at=user.visitor_expires_at.isoformat() if user.visitor_expires_at else "",
            verification_required=True,
            next_steps=[
                "Check your email for verification link",
                "Verify your email within 24 hours",
                "Login to explore hostel information",
                "Your visitor access expires in 30 days",
            ]
        )
        
    except ConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )


@router.post("/verify-email", response_model=EmailVerificationResponse)
async def verify_email(
    request: EmailVerificationRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Verify email address with token.
    
    **Public Endpoint** - No authentication required.
    
    **Process:**
    1. User clicks verification link in email
    2. Token is validated
    3. User account is activated
    4. User can now login
    """
    otp_provider = get_otp_provider()
    auth_service = AuthService(db, otp_provider)
    
    try:
        user = await auth_service.verify_email(request.token)
        
        return EmailVerificationResponse(
            message="Email verified successfully! You can now login.",
            email_verified=True,
            can_login=True
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/resend-verification")
async def resend_verification_email(
    request: ResendVerificationRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Resend verification email.
    
    **Public Endpoint** - No authentication required.
    
    **Use Case:**
    - User didn't receive original email
    - Verification link expired
    - Email was accidentally deleted
    """
    from app.repositories.user import UserRepository
    from app.models.user import User
    
    user_repo = UserRepository(User, db)
    user = await user_repo.get_by_email(request.email)
    
    if not user:
        # Don't reveal if email exists or not (security)
        return {
            "message": "If that email is registered, a verification link has been sent."
        }
    
    if user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already verified"
        )
    
    # Resend verification email
    otp_provider = get_otp_provider()
    auth_service = AuthService(db, otp_provider)
    
    try:
        from app.repositories.hostel import HostelRepository
        from app.models.hostel import Hostel
        
        hostel_repo = HostelRepository(Hostel, db)
        hostel = await hostel_repo.get(user.primary_hostel_id)
        
        await auth_service._send_verification_email(
            user.id, 
            user.email, 
            hostel.name if hostel else "Hostel"
        )
        
        return {
            "message": "Verification email sent. Please check your inbox."
        }
        
    except Exception as e:
        # Log error but don't expose details
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to resend verification: {str(e)}")
        
        return {
            "message": "If that email is registered, a verification link has been sent."
        }


@router.get("/hostels", response_model=list[HostelListResponse])
async def list_available_hostels(
    db: AsyncSession = Depends(get_db),
):
    """
    List available hostels for registration.
    
    **Public Endpoint** - No authentication required.
    
    **Use Case:**
    - Help users find their hostel code
    - Show active hostels accepting visitor registrations
    
    **Returns:** List of active hostels with their codes
    """
    from app.repositories.hostel import HostelRepository
    from app.models.hostel import Hostel
    
    hostel_repo = HostelRepository(Hostel, db)
    hostels = await hostel_repo.get_active_hostels()
    
    return [
        HostelListResponse(
            name=h.name,
            code=h.code,
            city=h.city,
            state=h.state,
        )
        for h in hostels
    ]