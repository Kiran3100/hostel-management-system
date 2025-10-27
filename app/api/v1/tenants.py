# app/api/v1/tenants.py

"""Tenant endpoints - FIXED SOFT DELETE."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.database import get_db
from app.schemas.tenant import (
    TenantProfileCreate,
    TenantProfileUpdate,
    TenantProfileResponse,
    CheckInRequest,
    CheckOutRequest,
)
from app.schemas.common import MessageResponse
from app.models.user import User, UserRole
from app.models.tenant import TenantProfile, CheckInOut, CheckInOutStatus
from app.repositories.tenant import TenantRepository, CheckInOutRepository
from app.repositories.room import BedRepository
from app.repositories.user import UserRepository
from app.core.rbac import require_role, check_hostel_access
from app.api.deps import get_current_user
from app.services.subscription import SubscriptionService
from app.models.room import Bed

router = APIRouter(prefix="/tenants", tags=["Tenants"])


@router.get("", response_model=List[TenantProfileResponse])
async def list_tenants(
    hostel_id: int = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List tenants."""
    if current_user.role == UserRole.SUPER_ADMIN:
        if not hostel_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="hostel_id required for Super Admin"
            )
    else:
        hostel_id = current_user.primary_hostel_id

    check_hostel_access(current_user, hostel_id)

    tenant_repo = TenantRepository(TenantProfile, db)
    tenants = await tenant_repo.get_by_hostel(hostel_id)

    return tenants


@router.get("/{tenant_id}", response_model=TenantProfileResponse)
async def get_tenant(
    tenant_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get tenant profile."""
    tenant_repo = TenantRepository(TenantProfile, db)
    tenant = await tenant_repo.get(tenant_id)

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )

    if current_user.role == UserRole.TENANT:
        my_tenant = await tenant_repo.get_by_user_id(current_user.id)
        if not my_tenant or my_tenant.id != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
    else:
        check_hostel_access(current_user, tenant.hostel_id)

    return tenant


@router.post("", response_model=TenantProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    request: TenantProfileCreate,
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.HOSTEL_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """Create tenant profile."""
    hostel_id = request.hostel_id
    if current_user.role != UserRole.SUPER_ADMIN:
        hostel_id = current_user.primary_hostel_id

    check_hostel_access(current_user, hostel_id)

    tenant_repo = TenantRepository(TenantProfile, db)
    user_repo = UserRepository(User, db)

    user = await user_repo.get(request.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {request.user_id} not found"
        )

    existing_tenant = await tenant_repo.get_by_user_id(request.user_id)
    if existing_tenant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User '{user.email}' already has a tenant profile (ID: {existing_tenant.id})"
        )

    subscription_service = SubscriptionService(db)
    await subscription_service.check_tenant_limit(hostel_id)

    tenant_data = request.model_dump()
    tenant_data["hostel_id"] = hostel_id

    try:
        tenant = await tenant_repo.create(tenant_data)
        await db.commit()
        await db.refresh(tenant)
        return tenant
    except IntegrityError as e:
        await db.rollback()
        error_msg = str(e.orig) if hasattr(e, 'orig') else str(e)
        
        if "tenant_profiles_user_id_key" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User with ID {request.user_id} already has a tenant profile"
            )
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create tenant profile due to data integrity issue"
        )


@router.patch("/{tenant_id}", response_model=TenantProfileResponse)
async def update_tenant(
    tenant_id: int,
    request: TenantProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update tenant profile."""
    tenant_repo = TenantRepository(TenantProfile, db)
    tenant = await tenant_repo.get(tenant_id)

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )

    if current_user.role == UserRole.TENANT:
        my_tenant = await tenant_repo.get_by_user_id(current_user.id)
        if not my_tenant or my_tenant.id != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
    else:
        check_hostel_access(current_user, tenant.hostel_id)

    update_data = request.model_dump(exclude_unset=True)
    tenant = await tenant_repo.update(tenant_id, update_data)
    await db.commit()
    await db.refresh(tenant)

    return tenant


# ✅ FIXED: Changed from hard delete to soft delete
@router.delete("/{tenant_id}", response_model=MessageResponse)
async def delete_tenant(
    tenant_id: int,
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.HOSTEL_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """Soft delete tenant profile."""
    tenant_repo = TenantRepository(TenantProfile, db)
    tenant = await tenant_repo.get(tenant_id)

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )

    check_hostel_access(current_user, tenant.hostel_id)

    if tenant.current_bed_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete tenant who is currently checked in. Please check out first."
        )

    # ✅ CHANGED: Use soft_delete instead of delete
    await tenant_repo.soft_delete(tenant_id)
    await db.commit()

    return MessageResponse(message="Tenant profile deleted successfully")


# ✅ NEW: Restore endpoint for soft-deleted tenants
@router.post("/{tenant_id}/restore", response_model=TenantProfileResponse)
async def restore_tenant(
    tenant_id: int,
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.HOSTEL_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """Restore a soft-deleted tenant profile."""
    from sqlalchemy import select
    
    # Query without soft-delete filter to find deleted records
    result = await db.execute(
        select(TenantProfile).where(TenantProfile.id == tenant_id)
    )
    tenant = result.scalar_one_or_none()
    
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )
    
    check_hostel_access(current_user, tenant.hostel_id)
    
    if not tenant.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant is not deleted"
        )
    
    # Restore tenant
    tenant_repo = TenantRepository(TenantProfile, db)
    tenant = await tenant_repo.update(tenant_id, {
        "is_deleted": False,
        "deleted_at": None
    })
    await db.commit()
    await db.refresh(tenant)
    
    return tenant


@router.post("/{tenant_id}/check-in", response_model=TenantProfileResponse)
async def check_in_tenant(
    tenant_id: int,
    request: CheckInRequest,
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.HOSTEL_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """Check-in tenant to a bed."""
    tenant_repo = TenantRepository(TenantProfile, db)
    bed_repo = BedRepository(Bed, db)
    checkin_repo = CheckInOutRepository(CheckInOut, db)

    tenant = await tenant_repo.get(tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )

    check_hostel_access(current_user, tenant.hostel_id)

    # ✅ FIX: Check if tenant already has check_in_date, not just current_bed_id
    if tenant.current_bed_id and tenant.check_in_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tenant is already checked in to bed ID {tenant.current_bed_id}"
        )

    bed = await bed_repo.get(request.bed_id)
    if not bed or bed.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bed not found"
        )

    if bed.hostel_id != tenant.hostel_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bed does not belong to tenant's hostel"
        )

    # ✅ FIX: Allow check-in if bed is already assigned to this tenant
    if bed.is_occupied and bed.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bed is already occupied by another tenant"
        )

    # ✅ Update tenant with check-in date
    await tenant_repo.update(
        tenant_id,
        {
            "current_bed_id": bed.id,
            "check_in_date": request.check_in_date,
        },
    )

    # ✅ Update bed
    await bed_repo.update(bed.id, {"is_occupied": True, "tenant_id": tenant_id})

    # ✅ Create check-in record
    checkin_data = {
        "tenant_id": tenant_id,
        "hostel_id": tenant.hostel_id,
        "bed_id": bed.id,
        "check_in_date": request.check_in_date,
        "status": CheckInOutStatus.CHECKED_IN,
    }
    await checkin_repo.create(checkin_data)

    await db.commit()

    updated_tenant = await tenant_repo.get(tenant_id)
    await db.refresh(updated_tenant)
    return updated_tenant


@router.post("/{tenant_id}/check-out", response_model=TenantProfileResponse)
async def check_out_tenant(
    tenant_id: int,
    request: CheckOutRequest,
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.HOSTEL_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """Check-out tenant from bed."""
    tenant_repo = TenantRepository(TenantProfile, db)
    bed_repo = BedRepository(Bed, db)
    checkin_repo = CheckInOutRepository(CheckInOut, db)

    tenant = await tenant_repo.get(tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )

    check_hostel_access(current_user, tenant.hostel_id)

    if not tenant.current_bed_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant is not checked in"
        )

    bed_id = tenant.current_bed_id

    await bed_repo.update(
        bed_id,
        {"is_occupied": False, "tenant_id": None}
    )

    active_checkin = await checkin_repo.get_active_checkin(tenant_id)
    if active_checkin:
        await checkin_repo.update(
            active_checkin.id,
            {
                "check_out_date": request.check_out_date,
                "status": CheckInOutStatus.CHECKED_OUT,
                "notes": request.notes,
            },
        )

    await tenant_repo.update(
        tenant_id,
        {
            "current_bed_id": None,
            "check_out_date": request.check_out_date,
        },
    )

    await db.commit()

    updated_tenant = await tenant_repo.get(tenant_id)
    await db.refresh(updated_tenant)
    return updated_tenant