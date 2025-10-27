"""Role-Based Access Control utilities and dependencies - UPDATED WITH VISITOR ROLE."""

from typing import List, Optional
from fastapi import Depends, HTTPException, status

from app.models.user import User, UserRole
from app.exceptions import AuthorizationError
from app.api.deps import get_current_user


# ✅ NEW: Define permissions for each role
ROLE_PERMISSIONS = {
    UserRole.SUPER_ADMIN: {
        "read": ["*"],  # All resources
        "write": ["*"],  # All resources
        "delete": ["*"],  # All resources
        "admin": ["*"],  # All admin functions
    },
    UserRole.HOSTEL_ADMIN: {
        "read": ["hostels", "rooms", "beds", "tenants", "complaints", "notices", "mess", "payments", "reports"],
        "write": ["rooms", "beds", "tenants", "complaints", "notices", "mess"],
        "delete": ["rooms", "beds", "notices", "mess"],
        "admin": ["hostel_management"],
    },
    UserRole.TENANT: {
        "read": ["own_profile", "own_room", "own_payments", "notices", "mess", "complaints"],
        "write": ["own_profile", "complaints", "leave_applications"],
        "delete": [],
        "admin": [],
    },
    UserRole.VISITOR: {  # ✅ NEW: Visitor permissions (read-only)
        "read": ["public_notices", "public_mess_menu", "hostel_info"],
        "write": [],  # No write access
        "delete": [],  # No delete access
        "admin": [],  # No admin access
    },
}


def require_role(allowed_roles: List[UserRole]):
    """Dependency to require specific roles."""
    
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        # ✅ NEW: Check if visitor account is expired
        if current_user.role == UserRole.VISITOR and current_user.is_visitor_expired():
            raise AuthorizationError("Visitor account has expired. Please contact administrator.")
        
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


# ✅ NEW: Visitor-specific dependency
def require_visitor(current_user: User = Depends(get_current_user)) -> User:
    """Dependency to require Visitor role."""
    if current_user.role != UserRole.VISITOR:
        raise AuthorizationError("Access denied. Visitor role required.")
    
    # Check expiration
    if current_user.is_visitor_expired():
        raise AuthorizationError("Visitor account has expired. Please contact administrator.")
    
    return current_user


# ✅ NEW: Allow visitors or higher roles
def allow_visitors(current_user: User = Depends(get_current_user)) -> User:
    """Dependency to allow visitors and all other roles (for public endpoints)."""
    if current_user.role == UserRole.VISITOR and current_user.is_visitor_expired():
        raise AuthorizationError("Visitor account has expired.")
    return current_user


def get_hostel_scope(current_user: User) -> Optional[int]:
    """Get hostel scope for current user.
    
    Returns:
        - None for Super Admin (can access all hostels)
        - hostel_id for Hostel Admin, Tenant, and Visitor (scoped to their hostel)
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
    
    # ✅ NEW: Visitors also check expiration
    if user.role == UserRole.VISITOR and user.is_visitor_expired():
        raise AuthorizationError("Visitor account has expired.")
    
    # ✅ FIX: For Hostel Admins, check all associated hostels
    if user.role == UserRole.HOSTEL_ADMIN:
        hostel_ids = user.get_hostel_ids()
        if hostel_id not in hostel_ids:
            raise AuthorizationError("Access denied. You don't have access to this hostel.")
        return
    
    # For Tenants and Visitors, check primary_hostel_id
    if user.primary_hostel_id != hostel_id:
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


# ✅ NEW: Permission checking helper
def has_permission(user: User, action: str, resource: str) -> bool:
    """Check if user has permission to perform action on resource.
    
    Args:
        user: User object
        action: Action to perform (read, write, delete, admin)
        resource: Resource name (hostels, rooms, etc.)
    
    Returns:
        True if user has permission, False otherwise
    """
    if user.role not in ROLE_PERMISSIONS:
        return False
    
    permissions = ROLE_PERMISSIONS[user.role].get(action, [])
    
    # Check for wildcard permission
    if "*" in permissions:
        return True
    
    # Check for specific resource permission
    return resource in permissions


def require_permission(action: str, resource: str):
    """Dependency to require specific permission.
    
    Usage:
        @router.get("/hostels", dependencies=[Depends(require_permission("read", "hostels"))])
    """
    async def permission_checker(current_user: User = Depends(get_current_user)) -> User:
        if not has_permission(current_user, action, resource):
            raise AuthorizationError(
                f"Access denied. You don't have permission to {action} {resource}."
            )
        return current_user
    
    return permission_checker

