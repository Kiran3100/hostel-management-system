"""Admin endpoints for visitor management - ADD TO router.py"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr, Field

from app.database import get_db
from app.schemas.user import UserResponse
from app.schemas.common import MessageResponse
from app.models.user import User, UserRole
from app.core.rbac import require_role, check_hostel_access
from app.api.deps import get_current_user
from app.services.visitor import VisitorService

router = APIRouter(prefix="/admin/visitors", tags=["Admin - Visitor Management"])


# ===== SCHEMAS =====

class VisitorCreateRequest(BaseModel):
    """Create visitor account."""
    
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, pattern=r"^\+?[1-9]\d{1,14}$")
    hostel_id: int
    duration_days: int = Field(default=30, ge=1, le=365, description="Access duration in days")
    password: Optional[str] = Field(None, min_length=8)
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "visitor@example.com",
                "phone": "+919876543210",
                "hostel_id": 1,
                "duration_days": 30,
                "password": "TempPass123"
            }
        }


class VisitorExtendRequest(BaseModel):
    """Extend visitor access."""
    
    additional_days: int = Field(..., ge=1, le=365, description="Days to extend access")


class VisitorResponse(UserResponse):
    """Visitor account response with expiration info."""
    
    visitor_expires_at: Optional[datetime] = None
    is_expired: bool = False


# ===== ENDPOINTS =====

@router.post("", response_model=VisitorResponse, status_code=status.HTTP_201_CREATED)
async def create_visitor_account(
    request: VisitorCreateRequest,
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.HOSTEL_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new visitor account.
    
    **Permissions:** Super Admin or Hostel Admin
    
    **Description:**
    - Creates a temporary visitor account with read-only access
    - Visitor account expires after specified duration (default: 30 days)
    - Visitors can only access their assigned hostel's public information
    - Returns temporary password if not provided
    
    **Use Cases:**
    - Guest access for prospective students
    - Temporary access for parents/guardians
    - Trial access for partners or vendors
    """
    # Check hostel access for Hostel Admins
    if current_user.role == UserRole.HOSTEL_ADMIN:
        check_hostel_access(current_user, request.hostel_id)
    
    visitor_service = VisitorService(db)
    
    visitor = await visitor_service.create_visitor(
        email=request.email,
        phone=request.phone,
        hostel_id=request.hostel_id,
        duration_days=request.duration_days,
        password=request.password,
        created_by_admin_id=current_user.id,
    )
    
    # Convert to response
    response_data = {
        "id": visitor.id,
        "email": visitor.email,
        "phone": visitor.phone,
        "role": visitor.role,
        "hostel_id": visitor.primary_hostel_id,
        "is_active": visitor.is_active,
        "is_verified": visitor.is_verified,
        "last_login": visitor.last_login,
        "created_at": visitor.created_at,
        "updated_at": visitor.updated_at,
        "visitor_expires_at": visitor.visitor_expires_at,
        "is_expired": visitor.is_visitor_expired(),
    }
    
    return VisitorResponse(**response_data)


@router.get("", response_model=List[VisitorResponse])
async def list_visitors(
    hostel_id: Optional[int] = None,
    include_expired: bool = False,
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.HOSTEL_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """
    List all visitor accounts.
    
    **Permissions:** Super Admin or Hostel Admin
    
    **Query Parameters:**
    - `hostel_id`: Filter by hostel (required for Hostel Admins)
    - `include_expired`: Include expired visitor accounts (default: false)
    """
    from app.repositories.user import UserRepository
    
    # Determine hostel scope
    if current_user.role == UserRole.HOSTEL_ADMIN:
        hostel_id = current_user.primary_hostel_id
    elif not hostel_id and current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=400,
            detail="hostel_id required"
        )
    
    user_repo = UserRepository(User, db)
    
    # Build filters
    filters = {
        "role": UserRole.VISITOR,
        "is_deleted": False,
    }
    
    if hostel_id:
        filters["primary_hostel_id"] = hostel_id
    
    if not include_expired:
        filters["is_active"] = True
    
    visitors = await user_repo.get_multi(filters=filters, limit=1000)
    
    # Filter expired if needed
    if not include_expired:
        visitors = [v for v in visitors if not v.is_visitor_expired()]
    
    # Convert to response
    response_list = []
    for visitor in visitors:
        response_data = {
            "id": visitor.id,
            "email": visitor.email,
            "phone": visitor.phone,
            "role": visitor.role,
            "hostel_id": visitor.primary_hostel_id,
            "is_active": visitor.is_active,
            "is_verified": visitor.is_verified,
            "last_login": visitor.last_login,
            "created_at": visitor.created_at,
            "updated_at": visitor.updated_at,
            "visitor_expires_at": visitor.visitor_expires_at,
            "is_expired": visitor.is_visitor_expired(),
        }
        response_list.append(VisitorResponse(**response_data))
    
    return response_list


@router.get("/{visitor_id}", response_model=VisitorResponse)
async def get_visitor(
    visitor_id: int,
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.HOSTEL_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """Get visitor account details."""
    from app.repositories.user import UserRepository
    
    user_repo = UserRepository(User, db)
    visitor = await user_repo.get(visitor_id)
    
    if not visitor or visitor.role != UserRole.VISITOR:
        raise HTTPException(status_code=404, detail="Visitor not found")
    
    # Check hostel access
    if current_user.role == UserRole.HOSTEL_ADMIN:
        check_hostel_access(current_user, visitor.primary_hostel_id)
    
    response_data = {
        "id": visitor.id,
        "email": visitor.email,
        "phone": visitor.phone,
        "role": visitor.role,
        "hostel_id": visitor.primary_hostel_id,
        "is_active": visitor.is_active,
        "is_verified": visitor.is_verified,
        "last_login": visitor.last_login,
        "created_at": visitor.created_at,
        "updated_at": visitor.updated_at,
        "visitor_expires_at": visitor.visitor_expires_at,
        "is_expired": visitor.is_visitor_expired(),
    }
    
    return VisitorResponse(**response_data)


@router.post("/{visitor_id}/extend", response_model=VisitorResponse)
async def extend_visitor_access(
    visitor_id: int,
    request: VisitorExtendRequest,
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.HOSTEL_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """
    Extend visitor account expiration.
    
    **Permissions:** Super Admin or Hostel Admin
    
    **Description:**
    - Extends the visitor account expiration by specified days
    - Can extend already expired accounts (extension starts from now)
    - Automatically reactivates expired accounts
    """
    visitor_service = VisitorService(db)
    
    # Get visitor to check hostel access
    from app.repositories.user import UserRepository
    user_repo = UserRepository(User, db)
    visitor = await user_repo.get(visitor_id)
    
    if not visitor or visitor.role != UserRole.VISITOR:
        raise HTTPException(status_code=404, detail="Visitor not found")
    
    # Check hostel access
    if current_user.role == UserRole.HOSTEL_ADMIN:
        check_hostel_access(current_user, visitor.primary_hostel_id)
    
    # Extend access
    visitor = await visitor_service.extend_visitor_access(
        visitor_id=visitor_id,
        additional_days=request.additional_days,
        extended_by_admin_id=current_user.id,
    )
    
    # Reactivate if expired
    if not visitor.is_active:
        await user_repo.update(visitor_id, {"is_active": True})
        await db.commit()
        visitor.is_active = True
    
    response_data = {
        "id": visitor.id,
        "email": visitor.email,
        "phone": visitor.phone,
        "role": visitor.role,
        "hostel_id": visitor.primary_hostel_id,
        "is_active": visitor.is_active,
        "is_verified": visitor.is_verified,
        "last_login": visitor.last_login,
        "created_at": visitor.created_at,
        "updated_at": visitor.updated_at,
        "visitor_expires_at": visitor.visitor_expires_at,
        "is_expired": visitor.is_visitor_expired(),
    }
    
    return VisitorResponse(**response_data)


@router.post("/{visitor_id}/revoke", response_model=MessageResponse)
async def revoke_visitor_access(
    visitor_id: int,
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.HOSTEL_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """
    Immediately revoke visitor access.
    
    **Permissions:** Super Admin or Hostel Admin
    
    **Description:**
    - Immediately expires and deactivates the visitor account
    - Visitor will be unable to login or access any resources
    - Can be reversed by extending access again
    """
    visitor_service = VisitorService(db)
    
    # Get visitor to check hostel access
    from app.repositories.user import UserRepository
    user_repo = UserRepository(User, db)
    visitor = await user_repo.get(visitor_id)
    
    if not visitor or visitor.role != UserRole.VISITOR:
        raise HTTPException(status_code=404, detail="Visitor not found")
    
    # Check hostel access
    if current_user.role == UserRole.HOSTEL_ADMIN:
        check_hostel_access(current_user, visitor.primary_hostel_id)
    
    await visitor_service.revoke_visitor_access(
        visitor_id=visitor_id,
        revoked_by_admin_id=current_user.id,
    )
    
    return MessageResponse(message="Visitor access revoked successfully")


@router.delete("/{visitor_id}", response_model=MessageResponse)
async def delete_visitor_account(
    visitor_id: int,
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.HOSTEL_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """
    Permanently delete visitor account (soft delete).
    
    **Permissions:** Super Admin or Hostel Admin
    """
    from app.repositories.user import UserRepository
    
    user_repo = UserRepository(User, db)
    visitor = await user_repo.get(visitor_id)
    
    if not visitor or visitor.role != UserRole.VISITOR:
        raise HTTPException(status_code=404, detail="Visitor not found")
    
    # Check hostel access
    if current_user.role == UserRole.HOSTEL_ADMIN:
        check_hostel_access(current_user, visitor.primary_hostel_id)
    
    await user_repo.soft_delete(visitor_id)
    await db.commit()
    
    return MessageResponse(message="Visitor account deleted successfully")