# app/api/v1/rooms.py

"""Room and bed endpoints - FIXED SOFT DELETE."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.room import (
    RoomCreate,
    RoomUpdate,
    RoomResponse,
    BedCreate,
    BedUpdate,
    BedResponse,
    BedAssignRequest,
)
from app.schemas.common import MessageResponse
from app.models.user import User, UserRole
from app.models.room import Room, Bed
from app.repositories.room import RoomRepository, BedRepository
from app.core.rbac import require_role, check_hostel_access
from app.api.deps import get_current_user
from app.services.subscription import SubscriptionService

router = APIRouter(tags=["Rooms & Beds"])


# Room endpoints
@router.get("/rooms", response_model=List[RoomResponse])
async def list_rooms(
    hostel_id: int = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List rooms."""
    if current_user.role == UserRole.SUPER_ADMIN:
        if not hostel_id:
            raise HTTPException(status_code=400, detail="hostel_id required for Super Admin")
    else:
        hostel_id = current_user.hostel_id

    check_hostel_access(current_user, hostel_id)

    room_repo = RoomRepository(Room, db)
    rooms = await room_repo.get_by_hostel(hostel_id)

    return rooms


@router.get("/rooms/{room_id}", response_model=RoomResponse)
async def get_room(
    room_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get room by ID."""
    room_repo = RoomRepository(Room, db)
    room = await room_repo.get(room_id)

    if not room or room.is_deleted:
        raise HTTPException(status_code=404, detail="Room not found")

    check_hostel_access(current_user, room.hostel_id)

    return room


@router.post("/rooms", response_model=RoomResponse, status_code=status.HTTP_201_CREATED)
async def create_room(
    request: RoomCreate,
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.HOSTEL_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """Create a new room."""

    # Determine hostel_id based on role and request
    if current_user.role == UserRole.SUPER_ADMIN:
        if not request.hostel_id:
            raise HTTPException(
                status_code=400,
                detail="hostel_id is required for Super Admin to create rooms"
            )
        hostel_id = request.hostel_id
    else:  # Hostel admin
        # ✅ FIX: If hostel_id provided, verify access; otherwise use first hostel
        if request.hostel_id:
            hostel_id = request.hostel_id
            # Verify this hostel admin has access to this hostel
            hostel_ids = current_user.get_hostel_ids()
            if hostel_id not in hostel_ids:
                raise HTTPException(
                    status_code=403,
                    detail="You don't have access to this hostel"
                )
        else:
            # Use first associated hostel
            hostel_ids = current_user.get_hostel_ids()
            if not hostel_ids:
                raise HTTPException(
                    status_code=400,
                    detail="No hostels associated with your account"
                )
            hostel_id = hostel_ids[0]

    # Continue with validation...
    subscription_service = SubscriptionService(db)
    await subscription_service.check_room_limit(hostel_id)

    room_repo = RoomRepository(Room, db)
    existing = await room_repo.get_by_number(hostel_id, request.number)
    if existing:
        raise HTTPException(status_code=409, detail="Room number already exists in this hostel")

    room_data = {
        "hostel_id": hostel_id,
        "number": request.number,
        "floor": request.floor,
        "room_type": request.room_type,
        "capacity": request.capacity,
    }
    if request.description:
        room_data["description"] = request.description

    room = await room_repo.create(room_data)
    await db.commit()
    return room



@router.patch("/rooms/{room_id}", response_model=RoomResponse)
async def update_room(
    room_id: int,
    request: RoomUpdate,
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.HOSTEL_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """Update room."""
    room_repo = RoomRepository(Room, db)

    room = await room_repo.get(room_id)
    if not room or room.is_deleted:
        raise HTTPException(status_code=404, detail="Room not found")

    check_hostel_access(current_user, room.hostel_id)

    update_data = request.model_dump(exclude_unset=True)
    room = await room_repo.update(room_id, update_data)
    await db.commit()

    return room


# ✅ FIXED: Changed from hard delete to soft delete
@router.delete("/rooms/{room_id}", response_model=MessageResponse)
async def delete_room(
    room_id: int,
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.HOSTEL_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """Soft delete room."""
    room_repo = RoomRepository(Room, db)

    room = await room_repo.get(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    check_hostel_access(current_user, room.hostel_id)

    # ✅ CHANGED: Use soft_delete instead of delete
    await room_repo.soft_delete(room_id)
    await db.commit()

    return MessageResponse(message="Room deleted successfully")


# ✅ NEW: Restore endpoint for soft-deleted rooms
@router.post("/rooms/{room_id}/restore", response_model=RoomResponse)
async def restore_room(
    room_id: int,
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.HOSTEL_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """Restore a soft-deleted room."""
    from sqlalchemy import select
    
    # Query without soft-delete filter
    result = await db.execute(
        select(Room).where(Room.id == room_id)
    )
    room = result.scalar_one_or_none()
    
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    check_hostel_access(current_user, room.hostel_id)
    
    if not room.is_deleted:
        raise HTTPException(status_code=400, detail="Room is not deleted")
    
    # Restore room
    room_repo = RoomRepository(Room, db)
    room = await room_repo.update(room_id, {
        "is_deleted": False,
        "deleted_at": None
    })
    await db.commit()
    await db.refresh(room)
    
    return room


# Bed endpoints
@router.get("/beds", response_model=List[BedResponse])
async def list_beds(
    room_id: int = None,
    hostel_id: int = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List beds."""
    bed_repo = BedRepository(Bed, db)

    if room_id:
        beds = await bed_repo.get_by_room(room_id)
        if beds and beds[0].hostel_id:
            check_hostel_access(current_user, beds[0].hostel_id)
    elif hostel_id:
        check_hostel_access(current_user, hostel_id)
        beds = await bed_repo.get_multi(filters={"hostel_id": hostel_id, "is_deleted": False})
    else:
        if current_user.hostel_id:
            beds = await bed_repo.get_multi(
                filters={"hostel_id": current_user.hostel_id, "is_deleted": False}
            )
        else:
            raise HTTPException(status_code=400, detail="hostel_id or room_id required")

    return beds


@router.post("/beds", response_model=BedResponse, status_code=status.HTTP_201_CREATED)
async def create_bed(
    request: BedCreate,
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.HOSTEL_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """Create a new bed."""
    room_repo = RoomRepository(Room, db)
    bed_repo = BedRepository(Bed, db)

    room = await room_repo.get(request.room_id)
    if not room or room.is_deleted:
        raise HTTPException(status_code=404, detail="Room not found")

    check_hostel_access(current_user, room.hostel_id)

    bed_data = request.model_dump()
    bed_data["hostel_id"] = room.hostel_id

    bed = await bed_repo.create(bed_data)
    await db.commit()

    return bed


# ✅ FIXED: Bed soft delete
@router.delete("/beds/{bed_id}", response_model=MessageResponse)
async def delete_bed(
    bed_id: int,
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.HOSTEL_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """Soft delete bed."""
    bed_repo = BedRepository(Bed, db)

    bed = await bed_repo.get(bed_id)
    if not bed or bed.is_deleted:
        raise HTTPException(status_code=404, detail="Bed not found")

    check_hostel_access(current_user, bed.hostel_id)

    if bed.is_occupied:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete occupied bed. Please vacate it first."
        )

    # ✅ CHANGED: Use soft_delete instead of delete
    await bed_repo.soft_delete(bed_id)
    await db.commit()

    return MessageResponse(message="Bed deleted successfully")


# ✅ NEW: Restore endpoint for beds
@router.post("/beds/{bed_id}/restore", response_model=BedResponse)
async def restore_bed(
    bed_id: int,
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.HOSTEL_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """Restore a soft-deleted bed."""
    from sqlalchemy import select
    
    result = await db.execute(
        select(Bed).where(Bed.id == bed_id)
    )
    bed = result.scalar_one_or_none()
    
    if not bed:
        raise HTTPException(status_code=404, detail="Bed not found")
    
    check_hostel_access(current_user, bed.hostel_id)
    
    if not bed.is_deleted:
        raise HTTPException(status_code=400, detail="Bed is not deleted")
    
    bed_repo = BedRepository(Bed, db)
    bed = await bed_repo.update(bed_id, {
        "is_deleted": False,
        "deleted_at": None
    })
    await db.commit()
    await db.refresh(bed)
    
    return bed


@router.post("/beds/{bed_id}/assign", response_model=BedResponse)
async def assign_bed(
    bed_id: int,
    request: BedAssignRequest,
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.HOSTEL_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """Assign a tenant to a bed."""
    bed_repo = BedRepository(Bed, db)

    bed = await bed_repo.get(bed_id)
    if not bed or bed.is_deleted:
        raise HTTPException(status_code=404, detail="Bed not found")

    check_hostel_access(current_user, bed.hostel_id)

    if bed.is_occupied:
        raise HTTPException(status_code=400, detail="Bed is already occupied")

    bed = await bed_repo.update(
        bed_id,
        {"tenant_id": request.tenant_id, "is_occupied": True},
    )
    await db.commit()

    return bed


@router.post("/beds/{bed_id}/vacate", response_model=BedResponse)
async def vacate_bed(
    bed_id: int,
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.HOSTEL_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """Vacate a bed."""
    bed_repo = BedRepository(Bed, db)

    bed = await bed_repo.get(bed_id)
    if not bed or bed.is_deleted:
        raise HTTPException(status_code=404, detail="Bed not found")

    check_hostel_access(current_user, bed.hostel_id)

    bed = await bed_repo.update(bed_id, {"tenant_id": None, "is_occupied": False})
    await db.commit()

    return bed