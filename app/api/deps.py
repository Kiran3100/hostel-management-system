"""Shared API dependencies - FIXED LAZY LOADING."""

from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.core.security import decode_token
from app.models.user import User
from app.repositories.user import UserRepository
from app.exceptions import AuthenticationError

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Get current authenticated user."""
    token = credentials.credentials

    try:
        payload = decode_token(token)
        user_id = int(payload.get("sub"))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )

    # Eagerly load relationships to avoid lazy loading issues
    from sqlalchemy import select
    result = await db.execute(
        select(User)
        .options(selectinload(User.hostels))
        .where(User.id == user_id, User.is_deleted == False)
    )
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    
    # CRITICAL FIX: Pre-compute hostel_id to avoid lazy loading in response serialization
    # This ensures the value is available without triggering database queries
    if user.role.value in ['TENANT', 'VISITOR']:
        # These roles use primary_hostel_id directly
        user._cached_hostel_id = user.primary_hostel_id
    elif user.role.value == 'HOSTEL_ADMIN':
        # For hostel admin, hostels are already loaded via selectinload
        # Access them safely since they're in the current session
        if user.hostels:
            user._cached_hostel_id = user.hostels[0].id
        else:
            user._cached_hostel_id = user.primary_hostel_id
    else:  # SUPER_ADMIN
        user._cached_hostel_id = None

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Get current active user."""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def get_client_ip(request: Request) -> str:
    """Get client IP address."""
    if request.client:
        return request.client.host
    return "unknown"