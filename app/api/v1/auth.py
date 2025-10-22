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
    UserRole,
)
from app.schemas.common import MessageResponse
from app.schemas.user import UserResponse
from app.services.auth import AuthService
from app.api.deps import get_current_user
from app.models.user import User
from app.adapters.otp.mock import MockOTPProvider
from app.config import settings
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.exceptions import ConflictError, NotFoundError, ValidationError


router = APIRouter(prefix="/auth", tags=["Authentication"])


def get_otp_provider():
    """Get OTP provider based on config."""
    if settings.otp_provider == "mock":
        return MockOTPProvider()
    # Add other providers here
    return MockOTPProvider()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """Register a new user (Admin only - actual check done in service)."""
    
    # Validation
    if not request.email and not request.phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either email or phone is required"
        )
    
    if not request.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password is required"
        )
    
    if request.role != UserRole.SUPER_ADMIN and not request.hostel_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Hostel code is required for non-admin users"
        )
    
    otp_provider = get_otp_provider()
    auth_service = AuthService(db, otp_provider)

    try:
        # FIXED: Using request.hostel_code instead of request.hostel_id
        user_data = await auth_service.register_user(
            email=request.email,
            phone=request.phone,
            password=request.password,
            role=request.role,
            hostel_code=request.hostel_code,  # ✅ FIXED: was hostel_id
        )

        # Return UserResponse created from dict
        return UserResponse(**user_data)
    
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        # Log the error for debugging
        print(f"Registration error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during registration: {str(e)}"
        )


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
    # Use the custom from_orm method to properly map fields
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