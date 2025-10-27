"""Complaint endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.complaint import (
    ComplaintCreate,
    ComplaintUpdate,
    ComplaintResponse,
    ComplaintCommentCreate,
    ComplaintCommentResponse,
)
from app.schemas.common import MessageResponse
from app.models.user import User, UserRole
from app.models.complaint import Complaint, ComplaintComment
from app.repositories.complaint import ComplaintRepository, ComplaintCommentRepository
from app.core.rbac import require_role, check_hostel_access
from app.api.deps import get_current_user
from app.services.complaint import ComplaintService

router = APIRouter(prefix="/complaints", tags=["Complaints"])


@router.get("", response_model=List[ComplaintResponse])
async def list_complaints(
    hostel_id: int = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List complaints."""
    complaint_repo = ComplaintRepository(Complaint, db)

    if current_user.role == UserRole.TENANT:
        # Tenants see only their complaints
        from app.repositories.tenant import TenantRepository
        from app.models.tenant import TenantProfile

        tenant_repo = TenantRepository(TenantProfile, db)
        tenant = await tenant_repo.get_by_user(current_user.id)
        if not tenant:
            return []
        complaints = await complaint_repo.get_by_tenant(tenant.id)
    elif hostel_id:
        check_hostel_access(current_user, hostel_id)
        complaints = await complaint_repo.get_by_hostel(hostel_id)
    else:
        if current_user.hostel_id:
            complaints = await complaint_repo.get_by_hostel(current_user.hostel_id)
        else:
            complaints = []

    return complaints


@router.get("/{complaint_id}", response_model=ComplaintResponse)
async def get_complaint(
    complaint_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get complaint by ID."""
    complaint_repo = ComplaintRepository(Complaint, db)
    complaint = await complaint_repo.get(complaint_id)

    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    # Check access
    if current_user.role == UserRole.TENANT:
        from app.repositories.tenant import TenantRepository
        from app.models.tenant import TenantProfile

        tenant_repo = TenantRepository(TenantProfile, db)
        tenant = await tenant_repo.get_by_user(current_user.id)
        if not tenant or complaint.tenant_id != tenant.id:
            raise HTTPException(status_code=403, detail="Access denied")
    else:
        check_hostel_access(current_user, complaint.hostel_id)

    return complaint


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_complaint(
    request: ComplaintCreate,
    current_user: User = Depends(require_role([UserRole.TENANT])),
    db: AsyncSession = Depends(get_db),
):
    """Create a complaint (Tenant only)."""
    from app.repositories.tenant import TenantRepository
    from app.models.tenant import TenantProfile
    import traceback

    print(f"\n{'='*60}")
    print(f"CREATE COMPLAINT DEBUG")
    print(f"{'='*60}")
    print(f"Current User ID: {current_user.id}")
    print(f"Current User Email: {current_user.email}")
    print(f"Current User Role: {current_user.role}")
    print(f"Request: {request}")

    tenant_repo = TenantRepository(TenantProfile, db)
    
    try:
        print(f"\nFetching tenant profile for user_id: {current_user.id}")
        tenant = await tenant_repo.get_by_user(current_user.id)
        
        print(f"Tenant result: {tenant}")
        
        if not tenant:
            print(f"❌ No tenant profile found!")
            
            # Try to check if it exists but is soft-deleted
            from sqlalchemy import select
            result = await db.execute(
                select(TenantProfile).where(TenantProfile.user_id == current_user.id)
            )
            any_profile = result.scalar_one_or_none()
            
            if any_profile:
                print(f"Found profile but it might be deleted: is_deleted={any_profile.is_deleted}")
            else:
                print(f"No profile exists at all in database")
            
            raise HTTPException(
                status_code=404, 
                detail=f"Tenant profile not found for user {current_user.id}"
            )
        
        print(f"✅ Found tenant profile:")
        print(f"   Tenant ID: {tenant.id}")
        print(f"   Hostel ID: {tenant.hostel_id}")
        print(f"   Full Name: {tenant.full_name}")

        complaint_service = ComplaintService(db)
        
        print(f"\nCreating complaint...")
        complaint = await complaint_service.create_complaint(
            hostel_id=tenant.hostel_id,
            tenant_id=tenant.id,
            title=request.title,
            description=request.description,
            category=request.category,
            priority=request.priority,
        )
        
        print(f"✅ Complaint created: ID={complaint.id}")
        print(f"{'='*60}\n")
        
        # Return raw dict to see if serialization works
        return {
            "id": complaint.id,
            "hostel_id": complaint.hostel_id,
            "tenant_id": complaint.tenant_id,
            "title": complaint.title,
            "description": complaint.description,
            "category": complaint.category.value if hasattr(complaint.category, 'value') else str(complaint.category),
            "priority": complaint.priority.value if hasattr(complaint.priority, 'value') else str(complaint.priority),
            "status": complaint.status.value if hasattr(complaint.status, 'value') else str(complaint.status),
            "assigned_to": complaint.assigned_to,
            "resolved_at": complaint.resolved_at.isoformat() if complaint.resolved_at else None,
            "resolution_notes": complaint.resolution_notes,
            "created_at": complaint.created_at.isoformat(),
            "updated_at": complaint.updated_at.isoformat(),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        print(f"Traceback:")
        traceback.print_exc()
        print(f"{'='*60}\n")
        raise HTTPException(
            status_code=500,
            detail=f"Error creating complaint: {str(e)}"
        )


@router.patch("/{complaint_id}", response_model=ComplaintResponse)
async def update_complaint(
    complaint_id: int,
    request: ComplaintUpdate,
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.HOSTEL_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """Update complaint (Admin only)."""
    complaint_repo = ComplaintRepository(Complaint, db)
    complaint = await complaint_repo.get(complaint_id)

    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    check_hostel_access(current_user, complaint.hostel_id)

    complaint_service = ComplaintService(db)

    # FIXED: Support updating multiple fields at once
    # Build update_data dictionary with all provided fields
    update_data = {}
    
    if request.priority is not None:
        update_data["priority"] = request.priority
    
    if request.assigned_to is not None:
        update_data["assigned_to"] = request.assigned_to
        # Auto-set status to IN_PROGRESS when assigning
        if complaint.status == "OPEN":
            update_data["status"] = "IN_PROGRESS"
    
    # Handle status update separately as it may need special logic
    if request.status is not None:
        complaint = await complaint_service.update_complaint_status(
            complaint_id=complaint_id,
            status=request.status,
            user_id=current_user.id,
            resolution_notes=request.resolution_notes,
        )
    
    # Apply other updates if any
    if update_data:
        complaint = await complaint_repo.update(complaint_id, update_data)
        await db.commit()
    
    # Refresh complaint with relationships loaded
    await db.refresh(complaint)
    
    return complaint


@router.get("/{complaint_id}/comments", response_model=List[ComplaintCommentResponse])
async def list_comments(
    complaint_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List comments for a complaint."""
    complaint_repo = ComplaintRepository(Complaint, db)
    complaint = await complaint_repo.get(complaint_id)

    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    # Check access
    if current_user.role == UserRole.TENANT:
        from app.repositories.tenant import TenantRepository
        from app.models.tenant import TenantProfile

        tenant_repo = TenantRepository(TenantProfile, db)
        tenant = await tenant_repo.get_by_user(current_user.id)
        if not tenant or complaint.tenant_id != tenant.id:
            raise HTTPException(status_code=403, detail="Access denied")
    else:
        check_hostel_access(current_user, complaint.hostel_id)

    comment_repo = ComplaintCommentRepository(ComplaintComment, db)
    comments = await comment_repo.get_by_complaint(complaint_id)

    return comments


@router.post("/{complaint_id}/comments", response_model=ComplaintCommentResponse)
async def add_comment(
    complaint_id: int,
    request: ComplaintCommentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a comment to a complaint."""
    complaint_repo = ComplaintRepository(Complaint, db)
    complaint = await complaint_repo.get(complaint_id)

    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    # Check access
    if current_user.role == UserRole.TENANT:
        from app.repositories.tenant import TenantRepository
        from app.models.tenant import TenantProfile

        tenant_repo = TenantRepository(TenantProfile, db)
        tenant = await tenant_repo.get_by_user(current_user.id)
        if not tenant or complaint.tenant_id != tenant.id:
            raise HTTPException(status_code=403, detail="Access denied")
    else:
        check_hostel_access(current_user, complaint.hostel_id)

    complaint_service = ComplaintService(db)
    comment = await complaint_service.add_comment(
        complaint_id=complaint_id,
        user_id=current_user.id,
        comment=request.comment,
    )

    return comment