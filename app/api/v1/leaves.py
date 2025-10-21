"""Leave application endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.database import get_db
from app.schemas.leave import (
    LeaveApplicationCreate,
    LeaveApplicationResponse,
    LeaveApprovalRequest,
)
from app.schemas.common import MessageResponse
from app.models.user import User, UserRole
from app.models.leave import LeaveApplication, LeaveStatus
from app.repositories.leave import LeaveRepository
from app.core.rbac import require_role, check_hostel_access
from app.api.deps import get_current_user

router = APIRouter(prefix="/leaves", tags=["Leave Applications"])


@router.get("", response_model=List[LeaveApplicationResponse])
async def list_leaves(
    hostel_id: int = None,
    tenant_id: int = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List leave applications."""
    leave_repo = LeaveRepository(LeaveApplication, db)

    if current_user.role == UserRole.TENANT:
        # Tenants see only their leaves
        from app.repositories.tenant import TenantRepository
        from app.models.tenant import TenantProfile

        tenant_repo = TenantRepository(TenantProfile, db)
        tenant = await tenant_repo.get_by_user(current_user.id)
        if not tenant:
            return []
        leaves = await leave_repo.get_by_tenant(tenant.id)
    elif tenant_id:
        leaves = await leave_repo.get_by_tenant(tenant_id)
        if leaves:
            check_hostel_access(current_user, leaves[0].hostel_id)
    elif hostel_id:
        check_hostel_access(current_user, hostel_id)
        leaves = await leave_repo.get_by_hostel(hostel_id)
    else:
        if current_user.hostel_id:
            leaves = await leave_repo.get_by_hostel(current_user.hostel_id)
        else:
            leaves = []

    return leaves


@router.get("/{leave_id}", response_model=LeaveApplicationResponse)
async def get_leave(
    leave_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get leave application by ID."""
    leave_repo = LeaveRepository(LeaveApplication, db)
    leave = await leave_repo.get(leave_id)

    if not leave:
        raise HTTPException(status_code=404, detail="Leave application not found")

    # Check access
    if current_user.role == UserRole.TENANT:
        from app.repositories.tenant import TenantRepository
        from app.models.tenant import TenantProfile

        tenant_repo = TenantRepository(TenantProfile, db)
        tenant = await tenant_repo.get_by_user(current_user.id)
        if not tenant or leave.tenant_id != tenant.id:
            raise HTTPException(status_code=403, detail="Access denied")
    else:
        check_hostel_access(current_user, leave.hostel_id)

    return leave


@router.post("", response_model=LeaveApplicationResponse, status_code=status.HTTP_201_CREATED)
async def create_leave(
    request: LeaveApplicationCreate,
    current_user: User = Depends(require_role([UserRole.TENANT])),
    db: AsyncSession = Depends(get_db),
):
    """Create leave application (Tenant only)."""
    from app.repositories.tenant import TenantRepository
    from app.models.tenant import TenantProfile

    tenant_repo = TenantRepository(TenantProfile, db)
    tenant = await tenant_repo.get_by_user(current_user.id)

    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant profile not found")

    leave_repo = LeaveRepository(LeaveApplication, db)

    leave_data = request.model_dump()
    leave_data["hostel_id"] = tenant.hostel_id
    leave_data["tenant_id"] = tenant.id
    leave_data["status"] = LeaveStatus.PENDING

    leave = await leave_repo.create(leave_data)
    await db.commit()

    return leave


@router.post("/{leave_id}/approve", response_model=LeaveApplicationResponse)
async def approve_leave(
    leave_id: int,
    request: LeaveApprovalRequest,
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.HOSTEL_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """Approve or reject leave application."""
    leave_repo = LeaveRepository(LeaveApplication, db)
    leave = await leave_repo.get(leave_id)

    if not leave:
        raise HTTPException(status_code=404, detail="Leave application not found")

    check_hostel_access(current_user, leave.hostel_id)

    update_data = {
        "status": LeaveStatus.APPROVED if request.approved else LeaveStatus.REJECTED,
        "approver_id": current_user.id,
        "approved_at": datetime.utcnow(),
        "approver_notes": request.notes,
    }

    leave = await leave_repo.update(leave_id, update_data)
    await db.commit()

    return leave