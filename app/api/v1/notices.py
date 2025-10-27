"""Notice/announcement endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.notice import NoticeCreate, NoticeUpdate, NoticeResponse
from app.schemas.common import MessageResponse
from app.models.user import User, UserRole
from app.models.notice import Notice, NoticePriority
from app.repositories.notice import NoticeRepository
from app.core.rbac import require_role, check_hostel_access
from app.api.deps import get_current_user

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload


router = APIRouter(prefix="/notices", tags=["Notices"])


@router.get("", response_model=List[NoticeResponse])
async def list_notices(
    hostel_id: int = None,
    active_only: bool = True,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List notices."""
    notice_repo = NoticeRepository(Notice, db)

    # Determine hostel scope
    if current_user.role == UserRole.SUPER_ADMIN:
        if not hostel_id:
            raise HTTPException(status_code=400, detail="hostel_id required for Super Admin")
    else:
        hostel_id = current_user.hostel_id

    check_hostel_access(current_user, hostel_id)

    if active_only:
        notices = await notice_repo.get_active_by_hostel(hostel_id)
    else:
        notices = await notice_repo.get_multi(filters={"hostel_id": hostel_id})

    return notices


@router.get("/{notice_id}", response_model=NoticeResponse)
async def get_notice(
    notice_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get notice by ID."""
    notice_repo = NoticeRepository(Notice, db)
    notice = await notice_repo.get(notice_id)

    if not notice:
        raise HTTPException(status_code=404, detail="Notice not found")

    check_hostel_access(current_user, notice.hostel_id)

    return notice


@router.post("", response_model=NoticeResponse, status_code=status.HTTP_201_CREATED)
async def create_notice(
    request: NoticeCreate,
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.HOSTEL_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """Create a notice."""
    hostel_id = current_user.hostel_id
    if current_user.role == UserRole.SUPER_ADMIN and not hostel_id:
        raise HTTPException(status_code=400, detail="hostel_id required")

    notice_repo = NoticeRepository(Notice, db)

    notice_data = request.model_dump()
    notice_data["hostel_id"] = hostel_id
    notice_data["author_id"] = current_user.id

    notice = await notice_repo.create(notice_data)
    await db.commit()

    # TODO: Send push notifications to all tenants in background
    # from app.services.notification import NotificationService
    # notification_service = NotificationService(db)
    # await notification_service.notify_hostel_tenants(hostel_id, title, message)

    return notice


@router.patch("/{notice_id}", response_model=NoticeResponse)
async def update_notice(
    notice_id: int,
    request: NoticeUpdate,
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.HOSTEL_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """
    Update a notice. Only provided fields will be updated.
    
    **Permissions:**
    - Super Admin: Can update any notice
    - Hostel Admin: Can update notices from their hostel only
    
    **Validations:**
    - Title must be 1-255 characters if provided
    - Content must not be empty if provided
    - expires_at must be after published_at if both are set
    """
    # Step 1: Fetch the notice with all relationships
    result = await db.execute(
        select(Notice)
        .where(Notice.id == notice_id)
        .options(
            selectinload(Notice.hostel),
            selectinload(Notice.author)
        )
    )
    notice = result.scalar_one_or_none()
    
    if not notice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notice with ID {notice_id} not found"
        )
    
    # Step 2: Check access permissions
    try:
        check_hostel_access(current_user, notice.hostel_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You don't have permission to update this notice: {str(e)}"
        )
    
    # Step 3: Get update data (only fields that were provided)
    update_data = request.model_dump(exclude_unset=True)
    
    if not update_data:
        # No fields provided, return unchanged notice
        return notice
    
    # Step 4: Validate date logic if both dates are being updated
    published_at = update_data.get("published_at", notice.published_at)
    expires_at = update_data.get("expires_at", notice.expires_at)
    
    if published_at and expires_at:
        # Ensure expires_at is after published_at
        if expires_at <= published_at:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="expires_at must be after published_at"
            )
    
    # Step 5: Perform the update using SQLAlchemy update statement
    # This is more reliable than repository update for complex cases
    stmt = (
        update(Notice)
        .where(Notice.id == notice_id)
        .values(**update_data)
        .execution_options(synchronize_session="fetch")
    )
    
    await db.execute(stmt)
    await db.commit()
    
    # Step 6: Fetch the updated notice with all relationships
    result = await db.execute(
        select(Notice)
        .where(Notice.id == notice_id)
        .options(
            selectinload(Notice.hostel),
            selectinload(Notice.author)
        )
    )
    updated_notice = result.scalar_one()
    
    return updated_notice


@router.patch("/{notice_id}/priority", response_model=NoticeResponse)
async def update_notice_priority(
    notice_id: int,
    priority: NoticePriority,
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.HOSTEL_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """
    Quick update: Change only the priority of a notice.
    
    Useful for urgently changing notice priority without a full PATCH.
    """
    # Fetch notice
    result = await db.execute(
        select(Notice)
        .where(Notice.id == notice_id)
        .options(selectinload(Notice.hostel), selectinload(Notice.author))
    )
    notice = result.scalar_one_or_none()
    
    if not notice:
        raise HTTPException(status_code=404, detail="Notice not found")
    
    check_hostel_access(current_user, notice.hostel_id)
    
    # Update priority
    stmt = update(Notice).where(Notice.id == notice_id).values(priority=priority)
    await db.execute(stmt)
    await db.commit()
    
    # Fetch updated notice
    result = await db.execute(
        select(Notice)
        .where(Notice.id == notice_id)
        .options(selectinload(Notice.hostel), selectinload(Notice.author))
    )
    return result.scalar_one()


# Alternative: If you still want to use repository pattern
@router.patch("/{notice_id}/alt", response_model=NoticeResponse)
async def update_notice_alt(
    notice_id: int,
    request: NoticeUpdate,
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.HOSTEL_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """Alternative PATCH using repository pattern."""
    notice_repo = NoticeRepository(Notice, db)
    
    # Get notice
    notice = await notice_repo.get(notice_id)
    if not notice:
        raise HTTPException(status_code=404, detail="Notice not found")
    
    # Check access
    check_hostel_access(current_user, notice.hostel_id)
    
    # Get update data
    update_data = request.model_dump(exclude_unset=True)
    if not update_data:
        return notice
    
    # Validate dates
    published = update_data.get("published_at", notice.published_at)
    expires = update_data.get("expires_at", notice.expires_at)
    if published and expires and expires <= published:
        raise HTTPException(
            status_code=422,
            detail="expires_at must be after published_at"
        )
    
    # Update using repository
    updated = await notice_repo.update(notice_id, update_data)
    await db.commit()
    
    # Refresh with relationships
    await db.refresh(updated)
    
    # Or fetch again to ensure relationships are loaded
    updated = await notice_repo.get(notice_id)
    
    return updated


# For testing purposes - minimal update endpoint
@router.patch("/{notice_id}/simple")
async def simple_update(
    notice_id: int,
    title: Optional[str] = None,
    priority: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Simplified update for debugging.
    Only updates title and/or priority.
    """
    # Check notice exists
    result = await db.execute(select(Notice).where(Notice.id == notice_id))
    notice = result.scalar_one_or_none()
    
    if not notice:
        return {"error": "Notice not found", "notice_id": notice_id}
    
    # Build update dict
    updates = {}
    if title:
        updates["title"] = title
    if priority:
        try:
            updates["priority"] = NoticePriority(priority.upper())
        except ValueError:
            return {"error": f"Invalid priority: {priority}"}
    
    if not updates:
        return {"message": "No updates provided", "notice": notice}
    
    # Update
    stmt = update(Notice).where(Notice.id == notice_id).values(**updates)
    await db.execute(stmt)
    await db.commit()
    
    # Fetch updated
    result = await db.execute(select(Notice).where(Notice.id == notice_id))
    updated = result.scalar_one()
    
    return {
        "success": True,
        "updated_fields": list(updates.keys()),
        "notice": {
            "id": updated.id,
            "title": updated.title,
            "priority": updated.priority.value,
            "updated_at": updated.updated_at.isoformat()
        }
    }


@router.delete("/{notice_id}", response_model=MessageResponse)
async def delete_notice(
    notice_id: int,
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.HOSTEL_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """Delete notice."""
    notice_repo = NoticeRepository(Notice, db)

    notice = await notice_repo.get(notice_id)
    if not notice:
        raise HTTPException(status_code=404, detail="Notice not found")

    check_hostel_access(current_user, notice.hostel_id)

    await notice_repo.delete(notice_id)
    await db.commit()

    return MessageResponse(message="Notice deleted successfully")