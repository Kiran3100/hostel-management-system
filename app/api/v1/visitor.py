"""Visitor-specific endpoints - PUBLIC READ-ONLY ACCESS."""

from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.notice import NoticeResponse
from app.schemas.mess import MessMenuResponse
from app.schemas.hostel import HostelResponse
from app.models.user import User, UserRole
from app.models.notice import Notice
from app.models.mess import MessMenu, MealType
from app.models.hostel import Hostel
from app.repositories.notice import NoticeRepository
from app.repositories.mess import MessMenuRepository
from app.repositories.hostel import HostelRepository
from app.core.rbac import allow_visitors, has_permission
from app.api.deps import get_current_user

router = APIRouter(prefix="/visitor", tags=["Visitor Access"])


@router.get("/hostels", response_model=List[HostelResponse])
async def list_public_hostels(
    current_user: User = Depends(allow_visitors),
    db: AsyncSession = Depends(get_db),
):
    """
    Get list of hostels (public information only).
    
    **Accessible by:** Visitors and all other roles
    **Returns:** Basic hostel information without sensitive data
    """
    # Check permission
    if not has_permission(current_user, "read", "hostel_info"):
        if current_user.role != UserRole.VISITOR:
            # Non-visitors can access their hostel info via other endpoints
            raise HTTPException(
                status_code=403,
                detail="Use /api/v1/hostels for full hostel access"
            )
        raise HTTPException(status_code=403, detail="Access denied")
    
    hostel_repo = HostelRepository(Hostel, db)
    
    # Visitors only see their assigned hostel
    if current_user.role == UserRole.VISITOR:
        if not current_user.primary_hostel_id:
            return []
        
        hostel = await hostel_repo.get(current_user.primary_hostel_id)
        return [hostel] if hostel and hostel.is_active else []
    
    # Other roles see all active hostels
    hostels = await hostel_repo.get_active_hostels()
    return hostels


@router.get("/hostels/{hostel_id}", response_model=HostelResponse)
async def get_public_hostel(
    hostel_id: int,
    current_user: User = Depends(allow_visitors),
    db: AsyncSession = Depends(get_db),
):
    """
    Get basic information about a specific hostel.
    
    **Accessible by:** Visitors and all other roles
    """
    if current_user.role == UserRole.VISITOR:
        if current_user.primary_hostel_id != hostel_id:
            raise HTTPException(
                status_code=403,
                detail="Visitors can only access their assigned hostel"
            )
    
    hostel_repo = HostelRepository(Hostel, db)
    hostel = await hostel_repo.get(hostel_id)
    
    if not hostel or not hostel.is_active:
        raise HTTPException(status_code=404, detail="Hostel not found")
    
    return hostel


@router.get("/notices", response_model=List[NoticeResponse])
async def list_public_notices(
    hostel_id: Optional[int] = Query(None, description="Filter by hostel ID"),
    current_user: User = Depends(allow_visitors),
    db: AsyncSession = Depends(get_db),
):
    """
    Get active public notices.
    
    **Accessible by:** Visitors and all other roles
    **Returns:** Only active, published notices
    """
    # Check permission
    if not has_permission(current_user, "read", "public_notices"):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Determine hostel scope
    if current_user.role == UserRole.VISITOR:
        hostel_id = current_user.primary_hostel_id
        if not hostel_id:
            return []
    elif not hostel_id:
        raise HTTPException(
            status_code=400,
            detail="hostel_id required"
        )
    
    notice_repo = NoticeRepository(Notice, db)
    notices = await notice_repo.get_active_by_hostel(hostel_id)
    
    return notices


@router.get("/notices/{notice_id}", response_model=NoticeResponse)
async def get_public_notice(
    notice_id: int,
    current_user: User = Depends(allow_visitors),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a specific public notice.
    
    **Accessible by:** Visitors and all other roles
    """
    notice_repo = NoticeRepository(Notice, db)
    notice = await notice_repo.get(notice_id)
    
    if not notice:
        raise HTTPException(status_code=404, detail="Notice not found")
    
    # Check hostel access for visitors
    if current_user.role == UserRole.VISITOR:
        if notice.hostel_id != current_user.primary_hostel_id:
            raise HTTPException(
                status_code=403,
                detail="Access denied"
            )
    
    return notice


@router.get("/mess-menu", response_model=List[MessMenuResponse])
async def get_public_mess_menu(
    menu_date: Optional[date] = Query(None, description="Date (default: today)"),
    meal_type: Optional[MealType] = Query(None, description="Filter by meal type"),
    current_user: User = Depends(allow_visitors),
    db: AsyncSession = Depends(get_db),
):
    """
    Get mess menu for a specific date.
    
    **Accessible by:** Visitors and all other roles
    **Returns:** Public mess menu information
    """
    # Check permission
    if not has_permission(current_user, "read", "public_mess_menu"):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get hostel ID
    if current_user.role == UserRole.VISITOR:
        hostel_id = current_user.primary_hostel_id
        if not hostel_id:
            raise HTTPException(
                status_code=400,
                detail="Visitor not assigned to any hostel"
            )
    else:
        # Non-visitors should use the main mess endpoint
        raise HTTPException(
            status_code=403,
            detail="Use /api/v1/mess-menu for full access"
        )
    
    mess_repo = MessMenuRepository(MessMenu, db)
    
    # Use today if no date specified
    if not menu_date:
        menu_date = date.today()
    
    menus = await mess_repo.get_by_date(hostel_id, menu_date)
    
    # Filter by meal type if specified
    if meal_type:
        menus = [m for m in menus if m.meal_type == meal_type]
    
    # Convert to response format
    from app.api.v1.mess import convert_menu_to_response
    return [MessMenuResponse(**convert_menu_to_response(menu)) for menu in menus]


@router.get("/info", response_model=dict)
async def get_visitor_info(
    current_user: User = Depends(allow_visitors),
):
    """
    Get visitor account information.
    
    **Accessible by:** All users (primarily for visitors)
    **Returns:** User role, permissions, and expiration info
    """
    from app.core.rbac import ROLE_PERMISSIONS
    
    info = {
        "user_id": current_user.id,
        "role": current_user.role.value,
        "hostel_id": current_user.primary_hostel_id,
        "is_active": current_user.is_active,
        "permissions": ROLE_PERMISSIONS.get(current_user.role, {}),
    }
    
    # Add visitor-specific info
    if current_user.role == UserRole.VISITOR:
        info["visitor_expires_at"] = (
            current_user.visitor_expires_at.isoformat() 
            if current_user.visitor_expires_at 
            else None
        )
        info["is_expired"] = current_user.is_visitor_expired()
    
    return info