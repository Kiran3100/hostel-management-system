# app/repositories/hostel.py - COMPLETE FIX

"""Hostel repository - FIXED SOFT DELETE."""

from typing import Optional
from sqlalchemy import select, func

from app.models.hostel import Hostel
from app.repositories.base import BaseRepository


class HostelRepository(BaseRepository[Hostel]):
    """Hostel repository with soft delete support."""

    async def get(self, id: int) -> Optional[Hostel]:
        """Get hostel by ID, excluding soft-deleted."""
        result = await self.db.execute(
            select(Hostel).where(
                Hostel.id == id,
                Hostel.is_deleted == False
            )
        )
        return result.scalar_one_or_none()

    async def get_by_code(self, code: str) -> Optional[Hostel]:
        """Get hostel by code (case-insensitive), excluding soft-deleted."""
        result = await self.db.execute(
            select(Hostel).where(
                func.upper(Hostel.code) == code.upper(),  # Case-insensitive
                Hostel.is_deleted == False
            )
        )
        return result.scalar_one_or_none()

    async def get_active_hostels(self) -> list[Hostel]:
        """Get all active hostels, excluding soft-deleted."""
        result = await self.db.execute(
            select(Hostel).where(
                Hostel.is_active == True, 
                Hostel.is_deleted == False
            )
        )
        return list(result.scalars().all())
    
    # ✅ Override get_multi to filter soft-deleted
    async def get_multi(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[dict] = None,
    ) -> list[Hostel]:
        """Get multiple hostels, excluding soft-deleted by default."""
        query = select(Hostel)
        
        # Always filter soft-deleted unless explicitly requested
        if filters is None:
            filters = {}
        
        if "is_deleted" not in filters:
            filters["is_deleted"] = False
        
        for key, value in filters.items():
            if hasattr(Hostel, key):
                query = query.where(getattr(Hostel, key) == value)
        
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())