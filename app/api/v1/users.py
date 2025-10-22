"""User management endpoints - WITH MULTI-HOSTEL ADMIN FEATURES."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.user import UserResponse, UserUpdate, UserWithHostels
from app.schemas.common import MessageResponse
from app.schemas.auth import AddHostelRequest, RemoveHostelRequest
from app.models.user import User, UserRole
from app.models.hostel import Hostel
from app.repositories.user import UserRepository
from app.core.rbac import require_role, check_hostel_access
from app.api.deps import get_current_user
from app.services.auth import AuthService
from app.adapters.otp.mock import MockOTPProvider

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=List[UserResponse])
async def list_users(
    hostel_id: int = None,
    role: UserRole = None,
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.HOSTEL_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """List users."""
    user_repo = UserRepository(User, db)
    
    if current_user.role == UserRole.SUPER_ADMIN:
        if hostel_id:
            users = await user_repo.get_by_hostel(hostel_id, role)
        else:
            filters = {"is_deleted": False}
            if role:
                filters["role"] = role
            users = await user_repo.get_multi(filters=filters)
    else:
        # Hostel admin can only see users from their hostels
        hostel_id = current_user.primary_hostel_id
        users = await user_repo.get_by_hostel(hostel_id, role)
    
    return users


@router.get("/my-hostels", response_model=List[dict])
async def get_my_hostels(
    current_user: User = Depends(require_role([UserRole.HOSTEL_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all hostels managed by current admin.
    
    **Permissions:** Hostel Admin only
    
    **Returns:** List of hostels the admin manages
    """
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    
    # Fetch user with hostels relationship loaded
    result = await db.execute(
        select(User)
        .where(User.id == current_user.id)
        .options(selectinload(User.hostels))
    )
    user = result.scalar_one()
    
    hostels_data = [
        {
            "id": hostel.id,
            "name": hostel.name,
            "code": hostel.code,
            "city": hostel.city,
            "state": hostel.state,
            "is_active": hostel.is_active,
        }
        for hostel in user.hostels
    ]
    
    return hostels_data


@router.get("/{user_id}", response_model=UserWithHostels)
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get user by ID with hostel information."""
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    
    # Fetch user with hostels relationship loaded
    result = await db.execute(
        select(User)
        .where(User.id == user_id, User.is_deleted == False)
        .options(selectinload(User.hostels))
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check access
    if current_user.role == UserRole.TENANT:
        if current_user.id != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
    elif current_user.role == UserRole.HOSTEL_ADMIN:
        if user.primary_hostel_id not in current_user.get_hostel_ids():
            raise HTTPException(status_code=403, detail="Access denied")
    
    return UserWithHostels.from_orm(user)


@router.get("/{user_id}/hostels", response_model=List[dict])
async def get_user_hostels(
    user_id: int,
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.HOSTEL_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all hostels associated with a user (for admins).
    
    **Permissions:** Super Admin or Hostel Admin
    """
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    
    result = await db.execute(
        select(User)
        .where(User.id == user_id)
        .options(selectinload(User.hostels))
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Hostel admin can only see if user shares a hostel
    if current_user.role == UserRole.HOSTEL_ADMIN:
        user_hostel_ids = user.get_hostel_ids()
        current_hostel_ids = current_user.get_hostel_ids()
        
        if not any(hid in current_hostel_ids for hid in user_hostel_ids):
            raise HTTPException(status_code=403, detail="Access denied")
    
    hostels_data = [
        {
            "id": hostel.id,
            "name": hostel.name,
            "code": hostel.code,
            "city": hostel.city,
            "is_active": hostel.is_active,
        }
        for hostel in user.hostels
    ]
    
    return hostels_data


@router.post("/{user_id}/add-hostel", response_model=UserWithHostels)
async def add_hostel_to_admin(
    user_id: int,
    request: AddHostelRequest,
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """
    Add a hostel to an existing hostel admin.
    
    **Permissions:** Super Admin only
    
    **Use Case:** When you want to give an existing admin access to manage another hostel
    """
    otp_provider = MockOTPProvider()
    auth_service = AuthService(db, otp_provider)
    
    user = await auth_service.add_hostel_to_admin(
        user_id=user_id,
        hostel_code=request.hostel_code,
    )
    
    return UserWithHostels.from_orm(user)


@router.post("/{user_id}/remove-hostel", response_model=UserWithHostels)
async def remove_hostel_from_admin(
    user_id: int,
    request: RemoveHostelRequest,
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """
    Remove a hostel from an admin (must have at least one remaining).
    
    **Permissions:** Super Admin only
    
    **Note:** Admin must manage at least one hostel
    """
    otp_provider = MockOTPProvider()
    auth_service = AuthService(db, otp_provider)
    
    user = await auth_service.remove_hostel_from_admin(
        user_id=user_id,
        hostel_id=request.hostel_id,
    )
    
    return UserWithHostels.from_orm(user)


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    request: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update user."""
    user_repo = UserRepository(User, db)
    user = await user_repo.get(user_id)
    
    if not user or user.is_deleted:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check access
    if current_user.role == UserRole.TENANT:
        if current_user.id != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
    elif current_user.role == UserRole.HOSTEL_ADMIN:
        if user.primary_hostel_id not in current_user.get_hostel_ids():
            raise HTTPException(status_code=403, detail="Access denied")
    
    update_data = request.model_dump(exclude_unset=True)
    user = await user_repo.update(user_id, update_data)
    await db.commit()
    
    return user


@router.delete("/{user_id}", response_model=MessageResponse)
async def delete_user(
    user_id: int,
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.HOSTEL_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """Soft delete user."""
    user_repo = UserRepository(User, db)
    user = await user_repo.get(user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Super admin check
    if user.role == UserRole.SUPER_ADMIN and current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Cannot delete super admin")
    
    # Hostel admin can only delete users from their hostels
    if current_user.role == UserRole.HOSTEL_ADMIN:
        if user.primary_hostel_id not in current_user.get_hostel_ids():
            raise HTTPException(status_code=403, detail="Access denied")
    
    # Prevent self-deletion
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    
    await user_repo.soft_delete(user_id)
    await db.commit()
    
    return MessageResponse(message="User deleted successfully")


@router.post("/{user_id}/restore", response_model=UserResponse)
async def restore_user(
    user_id: int,
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """Restore a soft-deleted user (Super Admin only)."""
    from sqlalchemy import select
    
    # Query without soft-delete filter
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not user.is_deleted:
        raise HTTPException(status_code=400, detail="User is not deleted")
    
    # Restore user
    user_repo = UserRepository(User, db)
    user = await user_repo.update(user_id, {
        "is_deleted": False,
        "deleted_at": None
    })
    await db.commit()
    await db.refresh(user)
    
    return user