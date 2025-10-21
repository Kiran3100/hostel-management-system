# app/api/v1/auth.py - UPDATE REGISTER ENDPOINT

"""Authentication endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    OTPRequestRequest,
    OTPVerifyRequest,
    RefreshTokenRequest,
    RegisterRequest,
    ChangePasswordRequest,
)
from app.schemas.common import MessageResponse
from app.schemas.user import UserResponse
from app.services.auth import AuthService
from app.api.deps import get_current_user
from app.models.user import User, UserRole
from app.adapters.otp.mock import MockOTPProvider
from app.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])


def get_otp_provider():
    """Get OTP provider based on config."""
    if settings.otp_provider == "mock":
        return MockOTPProvider()
    # Add other providers here
    return MockOTPProvider()


# ✅ UPDATED: Removed role from request, hardcoded to HOSTEL_ADMIN
@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Register a new Hostel Admin.
    
    **Public endpoint** - Anyone can register as a hostel admin for a specific hostel.
    
    **Required fields:**
    - `email`: Valid email address
    - `phone`: Valid phone number (E.164 format)
    - `password`: Minimum 8 characters
    - `hostel_id`: ID of the hostel this admin will manage
    
    **Optional fields:**
    - `full_name`: Admin's full name
    
    **Note:** The role is automatically set to `HOSTEL_ADMIN`.
    """
    otp_provider = get_otp_provider()
    auth_service = AuthService(db, otp_provider)

    # ✅ FIXED: Role is hardcoded to HOSTEL_ADMIN
    user = await auth_service.register_user(
        email=request.email,
        phone=request.phone,
        password=request.password,
        role=UserRole.HOSTEL_ADMIN,  # ✅ Hardcoded
        hostel_id=request.hostel_id,
    )

    return user


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Login with email and password."""
    otp_provider = get_otp_provider()
    auth_service = AuthService(db, otp_provider)

    access_token, refresh_token, user = await auth_service.login(
        email=request.email,
        password=request.password,
    )

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user_id=user.id,
        role=user.role,
    )


@router.post("/login/otp/request", response_model=MessageResponse)
async def request_otp(
    request: OTPRequestRequest,
    db: AsyncSession = Depends(get_db),
):
    """Request OTP for phone login."""
    otp_provider = get_otp_provider()
    auth_service = AuthService(db, otp_provider)

    await auth_service.request_otp(
        phone=request.phone,
        hostel_code=request.hostel_code,
    )

    return MessageResponse(message="OTP sent successfully")


@router.post("/login/otp/verify", response_model=LoginResponse)
async def verify_otp(
    request: OTPVerifyRequest,
    db: AsyncSession = Depends(get_db),
):
    """Verify OTP and login."""
    otp_provider = get_otp_provider()
    auth_service = AuthService(db, otp_provider)

    access_token, refresh_token, user = await auth_service.verify_otp(
        phone=request.phone,
        otp=request.otp,
    )

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user_id=user.id,
        role=user.role,
    )


@router.post("/refresh", response_model=dict)
async def refresh_token(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """Refresh access token."""
    otp_provider = get_otp_provider()
    auth_service = AuthService(db, otp_provider)

    access_token = await auth_service.refresh_access_token(request.refresh_token)

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/logout", response_model=MessageResponse)
async def logout(
    request: RefreshTokenRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Logout user."""
    otp_provider = get_otp_provider()
    auth_service = AuthService(db, otp_provider)

    await auth_service.logout(current_user.id, request.refresh_token)

    return MessageResponse(message="Logged out successfully")


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user profile."""
    return UserResponse.from_orm(current_user)


@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Change password."""
    otp_provider = get_otp_provider()
    auth_service = AuthService(db, otp_provider)

    await auth_service.change_password(
        user_id=current_user.id,
        old_password=request.old_password,
        new_password=request.new_password,
    )

    return MessageResponse(message="Password changed successfully")