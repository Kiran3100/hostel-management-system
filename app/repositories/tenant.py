"""Tenant and check-in/out repositories."""

from typing import Optional, List
from sqlalchemy import select, func
from sqlalchemy.orm import joinedload

from app.models.tenant import TenantProfile, CheckInOut, CheckInOutStatus
from app.repositories.base import BaseRepository


class TenantRepository(BaseRepository[TenantProfile]):
    """Tenant repository."""

    async def get(self, id: int) -> Optional[TenantProfile]:
        """Get tenant by ID, excluding soft-deleted."""
        query = select(TenantProfile).where(TenantProfile.id == id)
        
        # Filter out soft-deleted records
        if hasattr(TenantProfile, 'is_deleted'):
            query = query.where(TenantProfile.is_deleted == False)
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_user_id(self, user_id: int) -> Optional[TenantProfile]:
        """Get tenant profile by user ID, excluding soft-deleted."""
        query = select(TenantProfile).where(TenantProfile.user_id == user_id)
        
        # Filter out soft-deleted records
        if hasattr(TenantProfile, 'is_deleted'):
            query = query.where(TenantProfile.is_deleted == False)
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_user(self, user_id: int) -> Optional[TenantProfile]:
        """Alias for get_by_user_id for backward compatibility."""
        return await self.get_by_user_id(user_id)

    async def get_by_hostel(self, hostel_id: int) -> List[TenantProfile]:
        """Get all tenants in a hostel, excluding soft-deleted."""
        query = select(TenantProfile).where(TenantProfile.hostel_id == hostel_id)
        
        # Filter out soft-deleted records
        if hasattr(TenantProfile, 'is_deleted'):
            query = query.where(TenantProfile.is_deleted == False)
        
        query = query.options(
            joinedload(TenantProfile.user),
            joinedload(TenantProfile.current_bed)
        )
        
        result = await self.db.execute(query)
        return list(result.unique().scalars().all())

    async def count_by_hostel(self, hostel_id: int) -> int:
        """Count non-deleted tenants in a hostel."""
        query = select(func.count(TenantProfile.id)).where(
            TenantProfile.hostel_id == hostel_id
        )
        
        # Filter out soft-deleted records
        if hasattr(TenantProfile, 'is_deleted'):
            query = query.where(TenantProfile.is_deleted == False)
        
        result = await self.db.execute(query)
        return result.scalar_one()


class CheckInOutRepository(BaseRepository[CheckInOut]):
    """Check-in/out repository."""

    async def get_by_tenant(self, tenant_id: int) -> List[CheckInOut]:
        """Get check-in/out records for a tenant."""
        result = await self.db.execute(
            select(CheckInOut)
            .where(CheckInOut.tenant_id == tenant_id)
            .order_by(CheckInOut.check_in_date.desc())
        )
        return list(result.scalars().all())

    async def get_active_checkin(self, tenant_id: int) -> Optional[CheckInOut]:
        """Get active check-in for a tenant."""
        result = await self.db.execute(
            select(CheckInOut)
            .where(
                CheckInOut.tenant_id == tenant_id,
                CheckInOut.status == CheckInOutStatus.CHECKED_IN
            )
            .order_by(CheckInOut.check_in_date.desc())
        )
        return result.scalar_one_or_none()

    async def get_by_hostel(self, hostel_id: int) -> List[CheckInOut]:
        """Get all check-in/out records for a hostel."""
        result = await self.db.execute(
            select(CheckInOut)
            .where(CheckInOut.hostel_id == hostel_id)
            .order_by(CheckInOut.check_in_date.desc())
        )
        return list(result.scalars().all())

    async def get_by_bed(self, bed_id: int) -> List[CheckInOut]:
        """Get check-in/out records for a specific bed."""
        result = await self.db.execute(
            select(CheckInOut)
            .where(CheckInOut.bed_id == bed_id)
            .order_by(CheckInOut.check_in_date.desc())
        )
        return list(result.scalars().all())