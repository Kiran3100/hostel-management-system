# app/api/v1/rooms.py - COMPLETE FIX

"""Room and bed endpoints - ALL ISSUES FIXED."""

from typing import List, Optional
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


# ===== ROOM ENDPOINTS =====

@router.get("/rooms", response_model=List[RoomResponse])
async def list_rooms(
    hostel_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List rooms in a hostel.
    
    **Query Parameters:**
    - `hostel_id`: Filter by hostel (required for Super Admin, optional for others)
    
    **Returns:** List of rooms (excluding soft-deleted)
    """
    # Determine hostel scope
    if current_user.role == UserRole.SUPER_ADMIN:
        if not hostel_id:
            raise HTTPException(
                status_code=400, 
                detail="hostel_id required for Super Admin"
            )
    else:
        # ✅ FIX: Use primary_hostel_id to avoid lazy loading
        hostel_id = hostel_id or current_user.primary_hostel_id
        if not hostel_id:
            raise HTTPException(
                status_code=400,
                detail="hostel_id required"
            )

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
    """
    Create a new room.
    
    **Permissions:** Super Admin or Hostel Admin
    
    **Body:**
    - `hostel_id`: Required for Super Admin, optional for Hostel Admin
    - `number`: Room number (unique per hostel)
    - `floor`: Floor number
    - `room_type`: SINGLE, DOUBLE, TRIPLE, DORMITORY
    - `capacity`: Number of beds
    - `description`: Optional description
    
    **Note:** Hostel Admin can only create rooms in their assigned hostels
    """
    # ✅ FIX: Properly determine hostel_id
    hostel_id = None
    
    if current_user.role == UserRole.SUPER_ADMIN:
        # Super admin must provide hostel_id
        if not request.hostel_id:
            raise HTTPException(
                status_code=400,
                detail="hostel_id is required for Super Admin"
            )
        hostel_id = request.hostel_id
        
    else:  # HOSTEL_ADMIN
        # If hostel_id provided, verify access
        if request.hostel_id:
            hostel_id = request.hostel_id
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

    # Check subscription limits
    subscription_service = SubscriptionService(db)
    await subscription_service.check_room_limit(hostel_id)

    # Check for duplicate room number
    room_repo = RoomRepository(Room, db)
    existing = await room_repo.get_by_number(hostel_id, request.number)
    if existing:
        raise HTTPException(
            status_code=409, 
            detail=f"Room number '{request.number}' already exists in this hostel"
        )

    # Create room
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
    
    # ✅ FIX: Refresh to get all fields
    await db.refresh(room)
    
    return room


@router.patch("/rooms/{room_id}", response_model=RoomResponse)
async def update_room(
    room_id: int,
    request: RoomUpdate,
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.HOSTEL_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """
    Update room details.
    
    **Permissions:** Super Admin or Hostel Admin
    
    **Note:** Only provided fields will be updated
    """
    room_repo = RoomRepository(Room, db)

    room = await room_repo.get(room_id)
    if not room or room.is_deleted:
        raise HTTPException(status_code=404, detail="Room not found")

    check_hostel_access(current_user, room.hostel_id)

    # Check for duplicate room number if changing number
    update_data = request.model_dump(exclude_unset=True)
    if "number" in update_data and update_data["number"] != room.number:
        existing = await room_repo.get_by_number(room.hostel_id, update_data["number"])
        if existing:
            raise HTTPException(
                status_code=409,
                detail=f"Room number '{update_data['number']}' already exists"
            )

    room = await room_repo.update(room_id, update_data)
    await db.commit()
    
    # ✅ FIX: Refresh to get updated fields
    await db.refresh(room)

    return room


@router.delete("/rooms/{room_id}", response_model=MessageResponse)
async def delete_room(
    room_id: int,
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.HOSTEL_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """
    Soft delete room.
    
    **Permissions:** Super Admin or Hostel Admin
    
    **Note:** Cannot delete rooms with occupied beds
    """
    room_repo = RoomRepository(Room, db)
    bed_repo = BedRepository(Bed, db)

    room = await room_repo.get(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    check_hostel_access(current_user, room.hostel_id)

    # Check if room has occupied beds
    beds = await bed_repo.get_by_room(room_id)
    occupied_beds = [bed for bed in beds if bed.is_occupied]
    
    if occupied_beds:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete room with {len(occupied_beds)} occupied bed(s). Please vacate all beds first."
        )

    await room_repo.soft_delete(room_id)
    await db.commit()

    return MessageResponse(message="Room deleted successfully")


@router.post("/rooms/{room_id}/restore", response_model=RoomResponse)
async def restore_room(
    room_id: int,
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.HOSTEL_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """
    Restore a soft-deleted room.
    
    **Permissions:** Super Admin or Hostel Admin
    """
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
    
    # ✅ FIX: Refresh to get updated state
    await db.refresh(room)
    
    return room


# ===== BED ENDPOINTS =====

@router.get("/beds", response_model=List[BedResponse])
async def list_beds(
    room_id: Optional[int] = None,
    hostel_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List beds.
    
    **Query Parameters:**
    - `room_id`: Filter by room
    - `hostel_id`: Filter by hostel
    
    **Note:** At least one filter is required
    """
    bed_repo = BedRepository(Bed, db)

    if room_id:
        beds = await bed_repo.get_by_room(room_id)
        if beds and beds[0].hostel_id:
            check_hostel_access(current_user, beds[0].hostel_id)
            
    elif hostel_id:
        check_hostel_access(current_user, hostel_id)
        beds = await bed_repo.get_multi(
            filters={"hostel_id": hostel_id, "is_deleted": False}
        )
        
    else:
        # ✅ FIX: Use primary_hostel_id to avoid lazy loading
        user_hostel_id = current_user.primary_hostel_id
        if user_hostel_id:
            beds = await bed_repo.get_multi(
                filters={"hostel_id": user_hostel_id, "is_deleted": False}
            )
        else:
            raise HTTPException(
                status_code=400, 
                detail="hostel_id or room_id required"
            )

    return beds


@router.get("/beds/{bed_id}", response_model=BedResponse)
async def get_bed(
    bed_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get bed by ID."""
    bed_repo = BedRepository(Bed, db)
    bed = await bed_repo.get(bed_id)

    if not bed or bed.is_deleted:
        raise HTTPException(status_code=404, detail="Bed not found")

    check_hostel_access(current_user, bed.hostel_id)

    return bed


@router.post("/beds", response_model=BedResponse, status_code=status.HTTP_201_CREATED)
async def create_bed(
    request: BedCreate,
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.HOSTEL_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new bed in a room.
    
    **Permissions:** Super Admin or Hostel Admin
    
    **Body:**
    - `room_id`: Room to add bed to
    - `number`: Bed number (e.g., "A1", "B2")
    """
    room_repo = RoomRepository(Room, db)
    bed_repo = BedRepository(Bed, db)

    # Verify room exists
    room = await room_repo.get(request.room_id)
    if not room or room.is_deleted:
        raise HTTPException(status_code=404, detail="Room not found")

    check_hostel_access(current_user, room.hostel_id)

    # Check room capacity
    existing_beds = await bed_repo.get_by_room(request.room_id)
    if len(existing_beds) >= room.capacity:
        raise HTTPException(
            status_code=400,
            detail=f"Room capacity ({room.capacity}) reached. Cannot add more beds."
        )

    # Check for duplicate bed number in room
    for bed in existing_beds:
        if bed.number == request.number:
            raise HTTPException(
                status_code=409,
                detail=f"Bed number '{request.number}' already exists in this room"
            )

    # Create bed
    bed_data = request.model_dump()
    bed_data["hostel_id"] = room.hostel_id

    bed = await bed_repo.create(bed_data)
    await db.commit()
    
    # ✅ FIX: Refresh to get all fields
    await db.refresh(bed)

    return bed


@router.patch("/beds/{bed_id}", response_model=BedResponse)
async def update_bed(
    bed_id: int,
    request: BedUpdate,
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.HOSTEL_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """
    Update bed details.
    
    **Permissions:** Super Admin or Hostel Admin
    """
    bed_repo = BedRepository(Bed, db)

    bed = await bed_repo.get(bed_id)
    if not bed or bed.is_deleted:
        raise HTTPException(status_code=404, detail="Bed not found")

    check_hostel_access(current_user, bed.hostel_id)

    # Check for duplicate bed number if changing
    update_data = request.model_dump(exclude_unset=True)
    if "number" in update_data and update_data["number"] != bed.number:
        room_beds = await bed_repo.get_by_room(bed.room_id)
        for other_bed in room_beds:
            if other_bed.id != bed_id and other_bed.number == update_data["number"]:
                raise HTTPException(
                    status_code=409,
                    detail=f"Bed number '{update_data['number']}' already exists in this room"
                )

    bed = await bed_repo.update(bed_id, update_data)
    await db.commit()
    
    # ✅ FIX: Refresh to get updated fields
    await db.refresh(bed)

    return bed


@router.delete("/beds/{bed_id}", response_model=MessageResponse)
async def delete_bed(
    bed_id: int,
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.HOSTEL_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """
    Soft delete bed.
    
    **Permissions:** Super Admin or Hostel Admin
    
    **Note:** Cannot delete occupied beds
    """
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

    await bed_repo.soft_delete(bed_id)
    await db.commit()

    return MessageResponse(message="Bed deleted successfully")


@router.post("/beds/{bed_id}/restore", response_model=BedResponse)
async def restore_bed(
    bed_id: int,
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.HOSTEL_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """
    Restore a soft-deleted bed.
    
    **Permissions:** Super Admin or Hostel Admin
    """
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
    
    # ✅ FIX: Refresh to get updated state
    await db.refresh(bed)
    
    return bed


@router.post("/beds/{bed_id}/assign", response_model=BedResponse)
async def assign_bed(
    bed_id: int,
    request: BedAssignRequest,
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.HOSTEL_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """
    Assign a tenant to a bed.
    
    **Permissions:** Super Admin or Hostel Admin
    
    **Body:**
    - `tenant_id`: Tenant to assign
    
    **Note:** Bed must be vacant and tenant must not have another bed
    """
    bed_repo = BedRepository(Bed, db)

    bed = await bed_repo.get(bed_id)
    if not bed or bed.is_deleted:
        raise HTTPException(status_code=404, detail="Bed not found")

    check_hostel_access(current_user, bed.hostel_id)

    if bed.is_occupied:
        raise HTTPException(
            status_code=400, 
            detail="Bed is already occupied"
        )

    # Verify tenant exists and belongs to same hostel
    from app.repositories.tenant import TenantRepository
    from app.models.tenant import TenantProfile
    
    tenant_repo = TenantRepository(TenantProfile, db)
    tenant = await tenant_repo.get(request.tenant_id)
    
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    if tenant.hostel_id != bed.hostel_id:
        raise HTTPException(
            status_code=400,
            detail="Tenant and bed must belong to same hostel"
        )
    
    # Check if tenant already has a bed
    if tenant.current_bed_id:
        raise HTTPException(
            status_code=400,
            detail=f"Tenant is already assigned to bed ID {tenant.current_bed_id}"
        )

    # ✅ FIX: Update BOTH bed and tenant
    bed = await bed_repo.update(
        bed_id,
        {
            "tenant_id": request.tenant_id, 
            "is_occupied": True
        },
    )
    
    # ✅ UPDATE TENANT'S CURRENT BED
    await tenant_repo.update(
        request.tenant_id,
        {"current_bed_id": bed_id}
    )
    
    await db.commit()
    
    # Refresh to get updated state
    await db.refresh(bed)

    return bed

@router.post("/beds/{bed_id}/vacate", response_model=BedResponse)
async def vacate_bed(
    bed_id: int,
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.HOSTEL_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """
    Vacate a bed (remove tenant assignment).
    
    **Permissions:** Super Admin or Hostel Admin
    """
    bed_repo = BedRepository(Bed, db)

    bed = await bed_repo.get(bed_id)
    if not bed or bed.is_deleted:
        raise HTTPException(status_code=404, detail="Bed not found")

    check_hostel_access(current_user, bed.hostel_id)

    if not bed.is_occupied:
        raise HTTPException(
            status_code=400,
            detail="Bed is not occupied"
        )

    # ✅ FIX: Update BOTH bed and tenant
    tenant_id = bed.tenant_id
    
    bed = await bed_repo.update(
        bed_id, 
        {
            "tenant_id": None, 
            "is_occupied": False
        }
    )
    
    # ✅ UPDATE TENANT'S CURRENT BED
    if tenant_id:
        from app.repositories.tenant import TenantRepository
        from app.models.tenant import TenantProfile
        
        tenant_repo = TenantRepository(TenantProfile, db)
        await tenant_repo.update(
            tenant_id,
            {"current_bed_id": None}
        )
    
    await db.commit()
    
    # Refresh to get updated state
    await db.refresh(bed)

    return bed


# ===== BULK OPERATIONS =====

@router.get("/rooms/{room_id}/beds", response_model=List[BedResponse])
async def get_room_beds(
    room_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all beds in a room.
    
    **Convenience endpoint** for getting all beds in a specific room.
    """
    room_repo = RoomRepository(Room, db)
    bed_repo = BedRepository(Bed, db)
    
    # Verify room exists
    room = await room_repo.get(room_id)
    if not room or room.is_deleted:
        raise HTTPException(status_code=404, detail="Room not found")
    
    check_hostel_access(current_user, room.hostel_id)
    
    # Get beds
    beds = await bed_repo.get_by_room(room_id)
    
    return beds


@router.get("/hostels/{hostel_id}/available-beds", response_model=List[BedResponse])
async def get_available_beds(
    hostel_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all available (unoccupied) beds in a hostel.
    
    **Useful for:** Assigning new tenants to beds
    """
    check_hostel_access(current_user, hostel_id)
    
    bed_repo = BedRepository(Bed, db)
    beds = await bed_repo.get_available_beds(hostel_id)
    
    return beds