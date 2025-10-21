# app/api/v1/users.py (create this file if it doesn't exist)

"""User management endpoints - FIXED SOFT DELETE."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.user import UserResponse, UserUpdate
from app.schemas.common import MessageResponse
from app.models.user import User, UserRole
from app.repositories.user import UserRepository
from app.core.rbac import require_role, check_hostel_access
from app.api.deps import get_current_user

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
        # Hostel admin can only see users from their hostel
        hostel_id = current_user.primary_hostel_id
        users = await user_repo.get_by_hostel(hostel_id, role)
    
    return users


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get user by ID."""
    user_repo = UserRepository(User, db)
    user = await user_repo.get(user_id)
    
    if not user or user.is_deleted:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check access
    if current_user.role == UserRole.TENANT:
        if current_user.id != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
    elif current_user.role == UserRole.HOSTEL_ADMIN:
        if user.primary_hostel_id != current_user.primary_hostel_id:
            raise HTTPException(status_code=403, detail="Access denied")
    
    return user


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
        if user.primary_hostel_id != current_user.primary_hostel_id:
            raise HTTPException(status_code=403, detail="Access denied")
    
    update_data = request.model_dump(exclude_unset=True)
    user = await user_repo.update(user_id, update_data)
    await db.commit()
    
    return user


# ✅ FIXED: Changed from hard delete to soft delete
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
    
    # Hostel admin can only delete users from their hostel
    if current_user.role == UserRole.HOSTEL_ADMIN:
        if user.primary_hostel_id != current_user.primary_hostel_id:
            raise HTTPException(status_code=403, detail="Access denied")
    
    # Prevent self-deletion
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    
    # ✅ CHANGED: Use soft_delete instead of delete
    await user_repo.soft_delete(user_id)
    await db.commit()
    
    return MessageResponse(message="User deleted successfully")


# ✅ NEW: Restore endpoint for soft-deleted users
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