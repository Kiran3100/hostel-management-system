"""Role-Based Access Control utilities and dependencies."""

from typing import List, Optional
from fastapi import Depends, HTTPException, status

from app.models.user import User, UserRole
from app.exceptions import AuthorizationError
from app.api.deps import get_current_user


def require_role(allowed_roles: List[UserRole]):
    """Dependency to require specific roles."""
    
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise AuthorizationError(
                f"Access denied. Required roles: {', '.join([r.value for r in allowed_roles])}"
            )
        return current_user
    
    return role_checker


def require_super_admin(current_user: User = Depends(get_current_user)) -> User:
    """Dependency to require Super Admin role."""
    if current_user.role != UserRole.SUPER_ADMIN:
        raise AuthorizationError("Access denied. Super Admin role required.")
    return current_user


def require_hostel_admin(current_user: User = Depends(get_current_user)) -> User:
    """Dependency to require Hostel Admin role."""
    if current_user.role != UserRole.HOSTEL_ADMIN:
        raise AuthorizationError("Access denied. Hostel Admin role required.")
    return current_user


def require_tenant(current_user: User = Depends(get_current_user)) -> User:
    """Dependency to require Tenant role."""
    if current_user.role != UserRole.TENANT:
        raise AuthorizationError("Access denied. Tenant role required.")
    return current_user


def get_hostel_scope(current_user: User) -> Optional[int]:
    """Get hostel scope for current user.
    
    Returns:
        - None for Super Admin (can access all hostels)
        - hostel_id for Hostel Admin and Tenant (scoped to their hostel)
    """
    if current_user.role == UserRole.SUPER_ADMIN:
        return None  # No scope restriction
    return current_user.hostel_id


def check_hostel_access(user: User, hostel_id: int) -> None:
    """Check if user has access to a specific hostel.
    
    Raises:
        AuthorizationError: If user doesn't have access
    """
    if user.role == UserRole.SUPER_ADMIN:
        return  # Super admin has access to all hostels
    
    if user.hostel_id != hostel_id:
        raise AuthorizationError("Access denied. You don't have access to this hostel.")


def check_resource_ownership(user: User, resource_user_id: int) -> None:
    """Check if user owns a resource (e.g., can edit their own profile).
    
    Raises:
        AuthorizationError: If user doesn't own the resource
    """
    if user.role == UserRole.SUPER_ADMIN:
        return  # Super admin can access all resources
    
    if user.id != resource_user_id:
        raise AuthorizationError("Access denied. You can only access your own resources.")


# Note: get_current_user will be defined in app/api/deps.py
# It's imported here for type hints, but actual implementation is in dependencies
from app.api.deps import get_current_user  # noqa: E402