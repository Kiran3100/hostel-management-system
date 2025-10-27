"""API endpoints for hostel admin multi-hostel management."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.database import get_db
from app.schemas.hostel import HostelResponse, HostelCreate
from app.schemas.common import MessageResponse
from app.models.user import User, UserRole
from app.core.rbac import require_role
from app.api.deps import get_current_user
from app.services.hostel_admin import HostelAdminService

router = APIRouter(prefix="/admin/multi-hostel", tags=["Multi-Hostel Management"])


# ===== SCHEMAS =====

class AdminCodeResponse(BaseModel):
    """Admin code response."""
    
    admin_code: str
    admin_id: int
    admin_email: str
    created_at: str


class RegisterHostelWithCodeRequest(BaseModel):
    """Register hostel using admin code."""
    
    admin_code: str = Field(..., description="Hostel admin's unique code")
    hostel_name: str = Field(..., min_length=1, max_length=255)
    hostel_code: str = Field(..., min_length=3, max_length=50)
    address: str | None = None
    city: str | None = None
    state: str | None = None
    pincode: str | None = None
    phone: str | None = None
    email: str | None = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "admin_code": "ADMIN-A1B2C3D4",
                "hostel_name": "Green Valley Hostel",
                "hostel_code": "GVH-2025",
                "city": "Mumbai",
                "state": "Maharashtra",
            }
        }


class AssociateHostelRequest(BaseModel):
    """Associate existing hostel with admin."""
    
    hostel_id: int


class TransferHostelRequest(BaseModel):
    """Transfer hostel to another admin."""
    
    to_admin_id: int


# ===== ENDPOINTS =====

@router.post("/admin-code", response_model=AdminCodeResponse)
async def generate_admin_code(
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.HOSTEL_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate or regenerate admin code for hostel admin.
    
    **Permissions:** Super Admin (for any admin) or Hostel Admin (for self)
    
    **Description:**
    - Generates a unique admin code for the hostel admin
    - This code can be used to register new hostels under this admin
    - Code format: ADMIN-XXXXXXXX (8 hex characters)
    - Code can be regenerated if needed
    
    **Use Cases:**
    - Initial setup for new hostel admins
    - Regenerating code if compromised
    - Sharing code with authorized personnel
    """
    admin_service = HostelAdminService(db)
    
    # Super admin can generate for any admin, hostel admin only for self
    if current_user.role == UserRole.HOSTEL_ADMIN:
        admin_id = current_user.id
    else:
        # For super admin, this would need an admin_id parameter
        admin_id = current_user.id
    
    admin_code = await admin_service.create_admin_code(admin_id)
    
    return AdminCodeResponse(
        admin_code=admin_code,
        admin_id=current_user.id,
        admin_email=current_user.email,
        created_at=current_user.created_at.isoformat(),
    )


@router.get("/admin-code", response_model=AdminCodeResponse)
async def get_my_admin_code(
    current_user: User = Depends(require_role([UserRole.HOSTEL_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """
    Get current hostel admin's admin code.
    
    **Permissions:** Hostel Admin only
    
    **Returns:** Current admin code or error if not generated yet
    """
    if not current_user.admin_code:
        raise HTTPException(
            status_code=404,
            detail="Admin code not generated. Please generate one first.",
        )
    
    return AdminCodeResponse(
        admin_code=current_user.admin_code,
        admin_id=current_user.id,
        admin_email=current_user.email,
        created_at=current_user.created_at.isoformat(),
    )


@router.post("/register-hostel", response_model=HostelResponse, status_code=status.HTTP_201_CREATED)
async def register_hostel_with_code(
    request: RegisterHostelWithCodeRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Register a new hostel using admin code.
    
    **Public Endpoint** - No authentication required (validated by admin code)
    
    **Description:**
    - Allows registration of new hostels using a hostel admin's code
    - Automatically associates the hostel with the admin
    - Hostel admin can manage multiple hostels this way
    
    **Process:**
    1. Provide valid admin code
    2. Enter hostel details
    3. Hostel is created and associated with the admin
    
    **Security:**
    - Admin code must be valid and active
    - Hostel code must be unique across all hostels
    - Only hostel admins can have admin codes
    """
    admin_service = HostelAdminService(db)
    
    try:
        hostel = await admin_service.register_hostel_with_admin_code(
            admin_code=request.admin_code,
            hostel_name=request.hostel_name,
            hostel_code=request.hostel_code,
            address=request.address,
            city=request.city,
            state=request.state,
            pincode=request.pincode,
            phone=request.phone,
            email=request.email,
        )
        
        return HostelResponse.from_orm(hostel)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/my-hostels", response_model=List[HostelResponse])
async def get_my_hostels(
    current_user: User = Depends(require_role([UserRole.HOSTEL_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all hostels managed by current hostel admin.
    
    **Permissions:** Hostel Admin only
    
    **Returns:** List of all hostels associated with this admin
    """
    admin_service = HostelAdminService(db)
    
    hostels = await admin_service.get_admin_hostels(current_user.id)
    
    return [HostelResponse.from_orm(hostel) for hostel in hostels]


@router.post("/associate-hostel", response_model=MessageResponse)
async def associate_existing_hostel(
    request: AssociateHostelRequest,
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """
    Associate an existing hostel with a hostel admin.
    
    **Permissions:** Super Admin only
    
    **Description:**
    - Links an existing hostel to a hostel admin
    - Used for transferring hostel management
    - Admin gains full access to the hostel
    """
    from fastapi import Query
    
    # This would need admin_id as a query parameter
    # For now, using current_user (super admin) - you'd adjust this
    
    raise HTTPException(
        status_code=501,
        detail="This endpoint requires admin_id parameter - please use transfer endpoint",
    )


@router.post("/hostels/{hostel_id}/transfer", response_model=MessageResponse)
async def transfer_hostel(
    hostel_id: int,
    request: TransferHostelRequest,
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """
    Transfer hostel ownership to another admin.
    
    **Permissions:** Super Admin only
    
    **Description:**
    - Transfers a hostel from one admin to another
    - Previous admin loses access
    - New admin gains full access
    
    **Use Cases:**
    - Admin changing roles
    - Reorganizing hostel management structure
    - Admin leaving the organization
    """
    admin_service = HostelAdminService(db)
    
    # Get current admin of the hostel
    hostel = await admin_service.hostel_repo.get(hostel_id)
    if not hostel:
        raise HTTPException(status_code=404, detail="Hostel not found")
    
    # This requires knowing the current admin - you'd need to track this
    # For now, simplified version
    
    raise HTTPException(
        status_code=501,
        detail="Transfer endpoint requires additional implementation for tracking current admin",
    )


@router.delete("/hostels/{hostel_id}/remove", response_model=MessageResponse)
async def remove_hostel_from_admin(
    hostel_id: int,
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.HOSTEL_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """
    Remove hostel association from admin.
    
    **Permissions:** Super Admin or Hostel Admin (for their own hostels)
    
    **Description:**
    - Removes hostel from admin's managed hostels list
    - Admin loses access to this hostel
    - Hostel itself is not deleted
    
    **Note:** Cannot remove if admin has only one hostel
    """
    admin_service = HostelAdminService(db)
    
    # Check if admin has multiple hostels
    if current_user.role == UserRole.HOSTEL_ADMIN:
        hostels = await admin_service.get_admin_hostels(current_user.id)
        if len(hostels) <= 1:
            raise HTTPException(
                status_code=400,
                detail="Cannot remove last hostel from admin",
            )
        
        admin_id = current_user.id
    else:
        # Super admin would need to specify which admin
        raise HTTPException(
            status_code=400,
            detail="Super admin must specify admin_id",
        )
    
    await admin_service.remove_hostel_from_admin(admin_id, hostel_id)
    
    return MessageResponse(message="Hostel removed from admin successfully")


# ===== STATISTICS =====

@router.get("/stats", response_model=dict)
async def get_multi_hostel_stats(
    current_user: User = Depends(require_role([UserRole.HOSTEL_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """
    Get statistics across all hostels managed by admin.
    
    **Permissions:** Hostel Admin only
    
    **Returns:** Aggregated statistics from all managed hostels
    """
    admin_service = HostelAdminService(db)
    
    hostels = await admin_service.get_admin_hostels(current_user.id)
    
    # Aggregate statistics
    total_hostels = len(hostels)
    active_hostels = sum(1 for h in hostels if h.is_active)
    
    # You could add more detailed stats here
    from app.services.report import ReportService
    report_service = ReportService(db)
    
    hostel_stats = []
    for hostel in hostels:
        stats = await report_service.get_hostel_dashboard(hostel.id)
        hostel_stats.append({
            "hostel_id": hostel.id,
            "hostel_name": hostel.name,
            **stats,
        })
    
    return {
        "admin_id": current_user.id,
        "admin_email": current_user.email,
        "total_hostels": total_hostels,
        "active_hostels": active_hostels,
        "hostels": hostel_stats,
    }