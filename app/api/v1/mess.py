"""Mess menu endpoints - COMPLETE WORKING FIX"""

from typing import List, Optional
from datetime import date, datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.mess import (
    MessMenuCreate, 
    MessMenuUpdate, 
    MessMenuResponse,
    MessMenuBulkCreate,
    WeeklyMenuResponse
)
from app.schemas.common import MessageResponse
from app.models.user import User, UserRole
from app.models.mess import MessMenu, MealType
from app.repositories.mess import MessMenuRepository
from app.core.rbac import require_role, check_hostel_access
from app.api.deps import get_current_user

router = APIRouter(prefix="/mess-menu", tags=["Mess Menu"])


def convert_menu_to_response(menu: MessMenu) -> dict:
    """Helper function to convert MessMenu model to response dict."""
    return {
        "id": menu.id,
        "hostel_id": menu.hostel_id,
        "date": menu.date,
        "meal_type": menu.meal_type,
        "items": menu.items.get("items", []) if isinstance(menu.items, dict) else menu.items,
        "created_at": menu.created_at,
        "updated_at": menu.updated_at,
    }


@router.get("", response_model=List[MessMenuResponse])
async def list_menus(
    hostel_id: int = Query(None, description="Filter by hostel ID"),
    menu_date: date = Query(None, description="Specific date (default: today)"),
    date_from: date = Query(None, description="Date range start"),
    date_to: date = Query(None, description="Date range end"),
    meal_type: MealType = Query(None, description="Filter by meal type"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List mess menus with flexible filtering."""
    # Determine hostel scope
    if current_user.role == UserRole.SUPER_ADMIN:
        if not hostel_id:
            raise HTTPException(
                status_code=400, 
                detail="hostel_id required for Super Admin"
            )
    else:
        hostel_id = current_user.primary_hostel_id
        if not hostel_id:
            raise HTTPException(
                status_code=400,
                detail="User not associated with any hostel"
            )

    check_hostel_access(current_user, hostel_id)
    mess_repo = MessMenuRepository(MessMenu, db)

    # Determine date filter
    if date_from and date_to:
        menus = await mess_repo.get_by_date_range(hostel_id, date_from, date_to)
    elif menu_date:
        menus = await mess_repo.get_by_date(hostel_id, menu_date)
    else:
        menus = await mess_repo.get_by_date(hostel_id, date.today())

    # Filter by meal type if specified
    if meal_type:
        menus = [m for m in menus if m.meal_type == meal_type]

    # Convert all menus to response dicts
    return [MessMenuResponse(**convert_menu_to_response(menu)) for menu in menus]


@router.get("/{menu_id}", response_model=MessMenuResponse)
async def get_menu(
    menu_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get specific menu by ID."""
    mess_repo = MessMenuRepository(MessMenu, db)
    menu = await mess_repo.get(menu_id)

    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")

    check_hostel_access(current_user, menu.hostel_id)

    # Convert to response dict
    return MessMenuResponse(**convert_menu_to_response(menu))


@router.post("", response_model=MessMenuResponse, status_code=status.HTTP_201_CREATED)
async def create_menu(
    request: MessMenuCreate,
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.HOSTEL_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """Create or update a mess menu for specific date and meal type."""
    # Determine hostel
    hostel_id = current_user.primary_hostel_id
    if current_user.role == UserRole.SUPER_ADMIN and not hostel_id:
        raise HTTPException(
            status_code=400, 
            detail="hostel_id required for Super Admin"
        )

    mess_repo = MessMenuRepository(MessMenu, db)

    # Check if menu already exists for this date and meal type
    existing = await mess_repo.get_by_date_and_meal(
        hostel_id, 
        request.date, 
        request.meal_type
    )

    if existing:
        # Update existing menu
        menu = await mess_repo.update(existing.id, {"items": {"items": request.items}})
        await db.commit()
        await db.refresh(menu)
    else:
        # Create new menu
        menu_data = {
            "hostel_id": hostel_id,
            "date": request.date,
            "meal_type": request.meal_type,
            "items": {"items": request.items}
        }
        menu = await mess_repo.create(menu_data)
        await db.commit()
        await db.refresh(menu)

    # Convert to response dict
    return MessMenuResponse(**convert_menu_to_response(menu))


@router.patch("/{menu_id}", response_model=MessMenuResponse)
async def update_menu(
    menu_id: int,
    request: MessMenuUpdate,
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.HOSTEL_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """Update menu items for an existing menu."""
    mess_repo = MessMenuRepository(MessMenu, db)
    menu = await mess_repo.get(menu_id)
    
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")

    check_hostel_access(current_user, menu.hostel_id)

    # Update only items
    menu = await mess_repo.update(menu_id, {"items": {"items": request.items}})
    await db.commit()
    await db.refresh(menu)

    # Convert to response dict
    return MessMenuResponse(**convert_menu_to_response(menu))


@router.delete("/{menu_id}", response_model=MessageResponse)
async def delete_menu(
    menu_id: int,
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.HOSTEL_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """Delete a menu entry."""
    mess_repo = MessMenuRepository(MessMenu, db)
    menu = await mess_repo.get(menu_id)
    
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")

    check_hostel_access(current_user, menu.hostel_id)
    await mess_repo.delete(menu_id)
    await db.commit()

    return MessageResponse(message="Menu deleted successfully")


@router.post("/bulk", response_model=MessageResponse)
async def create_bulk_menus(
    request: MessMenuBulkCreate,
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.HOSTEL_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """Create multiple menus at once."""
    hostel_id = current_user.primary_hostel_id
    if current_user.role == UserRole.SUPER_ADMIN and not hostel_id:
        raise HTTPException(status_code=400, detail="hostel_id required")

    mess_repo = MessMenuRepository(MessMenu, db)
    created_count = 0
    updated_count = 0

    for menu_req in request.menus:
        existing = await mess_repo.get_by_date_and_meal(
            hostel_id,
            menu_req.date,
            menu_req.meal_type
        )

        if existing:
            await mess_repo.update(existing.id, {"items": {"items": menu_req.items}})
            updated_count += 1
        else:
            menu_data = {
                "hostel_id": hostel_id,
                "date": menu_req.date,
                "meal_type": menu_req.meal_type,
                "items": {"items": menu_req.items}
            }
            await mess_repo.create(menu_data)
            created_count += 1

    await db.commit()

    return MessageResponse(
        message=f"Bulk operation completed: {created_count} created, {updated_count} updated"
    )