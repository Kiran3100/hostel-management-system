# ===== app/api/deps.py - COMPLETE WORKING VERSION =====

"""Shared API dependencies with proper JWT authentication."""

from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select

from app.database import get_db
from app.core.security import decode_token
from app.models.user import User
from app.exceptions import AuthenticationError

# HTTPBearer automatically validates "Bearer <token>" format
security = HTTPBearer(auto_error=True)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Get current authenticated user from JWT token.
    
    This dependency:
    1. Extracts the Bearer token from Authorization header
    2. Validates the token format
    3. Decodes and verifies the JWT
    4. Fetches the user from database
    5. Pre-loads relationships to avoid lazy loading
    
    Usage:
        @router.get("/protected")
        async def protected_route(
            current_user: User = Depends(get_current_user)
        ):
            return {"user_id": current_user.id}
    """
    # Extract the JWT token (credentials.credentials contains the actual token)
    token = credentials.credentials

    try:
        # Decode and verify the JWT token
        payload = decode_token(token)
        user_id = int(payload.get("sub"))
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user ID",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: user ID must be a number",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Fetch user with relationships pre-loaded
    result = await db.execute(
        select(User)
        .options(selectinload(User.hostels))
        .where(User.id == user_id, User.is_deleted == False)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check visitor expiration
    from app.models.user import UserRole
    if user.role == UserRole.VISITOR and user.is_visitor_expired():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Visitor account has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Pre-compute hostel_id to avoid lazy loading
    if user.role in [UserRole.TENANT, UserRole.VISITOR]:
        user._cached_hostel_id = user.primary_hostel_id
    elif user.role == UserRole.HOSTEL_ADMIN:
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
    """
    Ensure the current user is active.
    
    This is an additional layer of validation, but get_current_user
    already checks this, so this is mostly for backward compatibility.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


def get_client_ip(request: Request) -> str:
    """
    Extract client IP address from request.
    
    Handles X-Forwarded-For header for proxied requests.
    """
    # Check X-Forwarded-For header (for proxied requests)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Take the first IP if there are multiple
        return forwarded_for.split(",")[0].strip()
    
    # Fallback to direct client host
    if request.client:
        return request.client.host
    
    return "unknown"


# ===== Optional: Token from cookie =====

async def get_token_from_cookie(request: Request) -> str:
    """
    Alternative: Get JWT from cookie instead of header.
    
    Usage:
        @router.get("/protected")
        async def protected_route(
            token: str = Depends(get_token_from_cookie)
        ):
            # Use token to get user
            pass
    """
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token


# ===== Testing Helper =====

async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """
    Get user if token is provided, otherwise return None.
    
    Useful for endpoints that work both with and without authentication.
    
    Usage:
        @router.get("/mixed")
        async def mixed_route(
            current_user: Optional[User] = Depends(get_optional_user)
        ):
            if current_user:
                return {"message": f"Hello {current_user.email}"}
            return {"message": "Hello anonymous"}
    """
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        payload = decode_token(token)
        user_id = int(payload.get("sub"))
        
        result = await db.execute(
            select(User)
            .where(User.id == user_id, User.is_deleted == False, User.is_active == True)
        )
        return result.scalar_one_or_none()
    except:
        return None


# ===== Example Usage in Routes =====

"""
# In your route files (e.g., app/api/v1/users.py):

from fastapi import APIRouter, Depends
from app.api.deps import get_current_user, get_client_ip
from app.models.user import User

router = APIRouter()

@router.get("/me")
async def get_my_profile(
    current_user: User = Depends(get_current_user)
):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "role": current_user.role.value
    }

@router.get("/protected")
async def protected_route(
    current_user: User = Depends(get_current_user),
    client_ip: str = Depends(get_client_ip)
):
    return {
        "message": f"Hello {current_user.email}",
        "ip": client_ip
    }
"""