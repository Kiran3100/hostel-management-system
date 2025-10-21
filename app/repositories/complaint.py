"""Complaint repository."""

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.complaint import Complaint, ComplaintComment, ComplaintStatus
from app.repositories.base import BaseRepository


class ComplaintRepository(BaseRepository[Complaint]):
    """Complaint repository."""

    async def get(self, id: int) -> Complaint | None:
        """Get complaint by ID with relationships loaded."""
        result = await self.db.execute(
            select(Complaint)
            .where(Complaint.id == id)
            .options(
                selectinload(Complaint.tenant),
                selectinload(Complaint.hostel),
                selectinload(Complaint.assignee),
                selectinload(Complaint.comments)
            )
        )
        return result.scalar_one_or_none()

    async def get_by_hostel(self, hostel_id: int) -> list[Complaint]:
        """Get complaints by hostel with relationships loaded."""
        result = await self.db.execute(
            select(Complaint)
            .where(Complaint.hostel_id == hostel_id)
            .options(
                selectinload(Complaint.tenant),
                selectinload(Complaint.hostel),
                selectinload(Complaint.assignee)
            )
            .order_by(Complaint.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_tenant(self, tenant_id: int) -> list[Complaint]:
        """Get complaints by tenant with relationships loaded."""
        result = await self.db.execute(
            select(Complaint)
            .where(Complaint.tenant_id == tenant_id)
            .options(
                selectinload(Complaint.tenant),
                selectinload(Complaint.hostel),
                selectinload(Complaint.assignee)
            )
            .order_by(Complaint.created_at.desc())
        )
        return list(result.scalars().all())

    async def count_by_status(self, hostel_id: int, status: ComplaintStatus) -> int:
        """Count complaints by status."""
        return await self.count({"hostel_id": hostel_id, "status": status})


class ComplaintCommentRepository(BaseRepository[ComplaintComment]):
    """Complaint comment repository."""

    async def get_by_complaint(self, complaint_id: int) -> list[ComplaintComment]:
        """Get comments for a complaint with user relationship loaded."""
        result = await self.db.execute(
            select(ComplaintComment)
            .where(ComplaintComment.complaint_id == complaint_id)
            .options(selectinload(ComplaintComment.user))
            .order_by(ComplaintComment.created_at.asc())
        )
        return list(result.scalars().all())