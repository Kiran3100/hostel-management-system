"""Leave application repository."""

from sqlalchemy import select

from app.models.leave import LeaveApplication, LeaveStatus
from app.repositories.base import BaseRepository


class LeaveRepository(BaseRepository[LeaveApplication]):
    """Leave application repository."""

    async def get_by_tenant(self, tenant_id: int) -> list[LeaveApplication]:
        """Get leave applications by tenant."""
        result = await self.db.execute(
            select(LeaveApplication)
            .where(LeaveApplication.tenant_id == tenant_id)
            .order_by(LeaveApplication.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_hostel(self, hostel_id: int) -> list[LeaveApplication]:
        """Get leave applications by hostel."""
        result = await self.db.execute(
            select(LeaveApplication)
            .where(LeaveApplication.hostel_id == hostel_id)
            .order_by(LeaveApplication.created_at.desc())
        )
        return list(result.scalars().all())

    async def count_pending(self, hostel_id: int) -> int:
        """Count pending leave applications."""
        return await self.count({"hostel_id": hostel_id, "status": LeaveStatus.PENDING})