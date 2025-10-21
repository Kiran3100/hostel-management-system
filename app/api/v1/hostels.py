# app/api/v1/hostels.py

"""Hostel endpoints - FIXED SOFT DELETE."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.hostel import (
    HostelCreate,
    HostelUpdate,
    HostelResponse,
    HostelWithStats,
)
from app.schemas.common import MessageResponse
from app.models.user import User, UserRole
from app.models.hostel import Hostel
from app.repositories.hostel import HostelRepository
from app.core.rbac import require_role, check_hostel_access
from app.api.deps import get_current_user
from app.core.pagination import PaginationParams, PageResponse
from app.services.report import ReportService

router = APIRouter(prefix="/hostels", tags=["Hostels"])


@router.get("", response_model=PageResponse[HostelResponse])
async def list_hostels(
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """List all hostels (Super Admin only)."""
    hostel_repo = HostelRepository(Hostel, db)

    hostels = await hostel_repo.get_multi(
        skip=pagination.offset,
        limit=pagination.limit,
        filters={"is_deleted": False},
    )

    total = await hostel_repo.count({"is_deleted": False})

    return PageResponse.create(
        items=hostels,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.get("/{hostel_id}", response_model=HostelResponse)
async def get_hostel(
    hostel_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get hostel by ID."""
    check_hostel_access(current_user, hostel_id)

    hostel_repo = HostelRepository(Hostel, db)
    hostel = await hostel_repo.get(hostel_id)

    if not hostel or hostel.is_deleted:
        raise HTTPException(status_code=404, detail="Hostel not found")

    return hostel


@router.post("", response_model=HostelResponse, status_code=status.HTTP_201_CREATED)
async def create_hostel(
    request: HostelCreate,
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """Create a new hostel (Super Admin only)."""
    hostel_repo = HostelRepository(Hostel, db)

    existing = await hostel_repo.get_by_code(request.code)
    if existing:
        raise HTTPException(status_code=409, detail="Hostel code already exists")

    hostel = await hostel_repo.create(request.model_dump())
    await db.commit()

    return hostel


@router.patch("/{hostel_id}", response_model=HostelResponse)
async def update_hostel(
    hostel_id: int,
    request: HostelUpdate,
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """Update hostel (Super Admin only)."""
    hostel_repo = HostelRepository(Hostel, db)

    hostel = await hostel_repo.get(hostel_id)
    if not hostel or hostel.is_deleted:
        raise HTTPException(status_code=404, detail="Hostel not found")

    update_data = request.model_dump(exclude_unset=True)
    hostel = await hostel_repo.update(hostel_id, update_data)
    await db.commit()

    return hostel


# ✅ FIXED: Changed from hard delete to soft delete
@router.delete("/{hostel_id}", response_model=MessageResponse)
async def delete_hostel(
    hostel_id: int,
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """Soft delete hostel (Super Admin only)."""
    hostel_repo = HostelRepository(Hostel, db)

    hostel = await hostel_repo.get(hostel_id)
    if not hostel:
        raise HTTPException(status_code=404, detail="Hostel not found")

    # ✅ CHANGED: Use soft_delete instead of delete
    await hostel_repo.soft_delete(hostel_id)
    await db.commit()

    return MessageResponse(message="Hostel deleted successfully")


# ✅ NEW: Restore endpoint for soft-deleted hostels
@router.post("/{hostel_id}/restore", response_model=HostelResponse)
async def restore_hostel(
    hostel_id: int,
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """Restore a soft-deleted hostel (Super Admin only)."""
    from sqlalchemy import select
    
    # Query without soft-delete filter
    result = await db.execute(
        select(Hostel).where(Hostel.id == hostel_id)
    )
    hostel = result.scalar_one_or_none()
    
    if not hostel:
        raise HTTPException(status_code=404, detail="Hostel not found")
    
    if not hostel.is_deleted:
        raise HTTPException(status_code=400, detail="Hostel is not deleted")
    
    # Restore hostel
    hostel_repo = HostelRepository(Hostel, db)
    hostel = await hostel_repo.update(hostel_id, {
        "is_deleted": False,
        "deleted_at": None
    })
    await db.commit()
    await db.refresh(hostel)
    
    return hostel


@router.get("/{hostel_id}/dashboard", response_model=dict)
async def hostel_dashboard(
    hostel_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get hostel dashboard statistics."""
    check_hostel_access(current_user, hostel_id)

    report_service = ReportService(db)
    dashboard = await report_service.get_hostel_dashboard(hostel_id)

    return dashboard