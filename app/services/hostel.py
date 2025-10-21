"""Hostel management service."""

from typing import Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.hostel import Hostel
from app.models.room import Room, Bed
from app.models.tenant import TenantProfile
from app.repositories.hostel import HostelRepository
from app.exceptions import ConflictError, NotFoundError


class HostelService:
    """Service for hostel management operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.hostel_repo = HostelRepository(Hostel, db)
    
    async def get_hostel_analytics(self, hostel_id: int) -> Dict:
        """Get comprehensive analytics for a hostel."""
        hostel = await self.hostel_repo.get(hostel_id)
        if not hostel:
            raise NotFoundError("Hostel not found")
        
        # Occupancy trends
        occupancy_query = select(
            func.date_trunc('month', TenantProfile.check_in_date).label('month'),
            func.count(TenantProfile.id).label('count')
        ).where(
            TenantProfile.hostel_id == hostel_id
        ).group_by('month')
        
        result = await self.db.execute(occupancy_query)
        occupancy_trends = result.all()
        
        # Revenue trends
        # ... implementation
        
        return {
            "hostel": hostel,
            "occupancy_trends": occupancy_trends,
            "revenue_trends": [],
            "maintenance_score": 0,
        }
    
    async def bulk_import_rooms(
        self, 
        hostel_id: int, 
        rooms_data: List[Dict]
    ) -> List[Room]:
        """Bulk import rooms for a hostel."""
        rooms = []
        for room_data in rooms_data:
            room = Room(
                hostel_id=hostel_id,
                **room_data
            )
            self.db.add(room)
            rooms.append(room)
        
        await self.db.commit()
        return rooms