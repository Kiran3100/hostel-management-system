# app/repositories/room.py - UPDATE

"""Room and bed repositories - FIXED SOFT DELETE FILTERING."""

from typing import Optional
from sqlalchemy import select

from app.models.room import Room, Bed
from app.repositories.base import BaseRepository


class RoomRepository(BaseRepository[Room]):
    """Room repository with soft delete support."""

    async def get(self, id: int) -> Optional[Room]:
        """Get room by ID, excluding soft-deleted."""
        result = await self.db.execute(
            select(Room).where(
                Room.id == id,
                Room.is_deleted == False  # ✅ ADDED: Filter soft-deleted
            )
        )
        return result.scalar_one_or_none()

    async def get_by_hostel(self, hostel_id: int) -> list[Room]:
        """Get rooms by hostel, excluding soft-deleted."""
        result = await self.db.execute(
            select(Room).where(
                Room.hostel_id == hostel_id, 
                Room.is_deleted == False  # ✅ Already filtered
            )
        )
        return list(result.scalars().all())

    async def get_by_number(self, hostel_id: int, number: str) -> Optional[Room]:
        """Get room by hostel and number, excluding soft-deleted."""
        result = await self.db.execute(
            select(Room).where(
                Room.hostel_id == hostel_id,
                Room.number == number,
                Room.is_deleted == False,  # ✅ Already filtered
            )
        )
        return result.scalar_one_or_none()


class BedRepository(BaseRepository[Bed]):
    """Bed repository with soft delete support."""

    async def get(self, id: int) -> Optional[Bed]:
        """Get bed by ID, excluding soft-deleted."""
        result = await self.db.execute(
            select(Bed).where(
                Bed.id == id,
                Bed.is_deleted == False  # ✅ ADDED: Filter soft-deleted
            )
        )
        return result.scalar_one_or_none()

    async def get_by_room(self, room_id: int) -> list[Bed]:
        """Get beds by room, excluding soft-deleted."""
        result = await self.db.execute(
            select(Bed).where(
                Bed.room_id == room_id, 
                Bed.is_deleted == False  # ✅ Already filtered
            )
        )
        return list(result.scalars().all())

    async def get_available_beds(self, hostel_id: int) -> list[Bed]:
        """Get available beds in a hostel, excluding soft-deleted."""
        result = await self.db.execute(
            select(Bed).where(
                Bed.hostel_id == hostel_id,
                Bed.is_occupied == False,
                Bed.is_deleted == False,  # ✅ Already filtered
            )
        )
        return list(result.scalars().all())

    async def get_by_tenant(self, tenant_id: int) -> Optional[Bed]:
        """Get bed assigned to tenant, excluding soft-deleted."""
        result = await self.db.execute(
            select(Bed).where(
                Bed.tenant_id == tenant_id, 
                Bed.is_deleted == False  # ✅ Already filtered
            )
        )
        return result.scalar_one_or_none()