"""Complaint service."""

from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.complaint import Complaint, ComplaintComment, ComplaintStatus
from app.repositories.complaint import ComplaintRepository, ComplaintCommentRepository
from app.exceptions import NotFoundError, AuthorizationError


class ComplaintService:
    """Complaint service."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.complaint_repo = ComplaintRepository(Complaint, db)
        self.comment_repo = ComplaintCommentRepository(ComplaintComment, db)

    async def create_complaint(
        self,
        hostel_id: int,
        tenant_id: int,
        title: str,
        description: str,
        category: str,
        priority: str,
    ) -> Complaint:
        """Create a new complaint."""
        complaint_data = {
            "hostel_id": hostel_id,
            "tenant_id": tenant_id,
            "title": title,
            "description": description,
            "category": category,
            "priority": priority,
            "status": ComplaintStatus.OPEN,
        }

        complaint = await self.complaint_repo.create(complaint_data)
        await self.db.commit()
        
        # Fetch the complaint again with all relationships loaded
        complaint = await self.complaint_repo.get(complaint.id)

        return complaint

    async def update_complaint_status(
        self,
        complaint_id: int,
        status: ComplaintStatus,
        user_id: int,
        resolution_notes: str = None,
    ) -> Complaint:
        """Update complaint status."""
        complaint = await self.complaint_repo.get(complaint_id)
        if not complaint:
            raise NotFoundError("Complaint not found")

        update_data = {"status": status}

        # FIXED: Use timezone-aware datetime
        if status == ComplaintStatus.RESOLVED:
            update_data["resolved_at"] = datetime.now(timezone.utc)
            if resolution_notes:
                update_data["resolution_notes"] = resolution_notes

        complaint = await self.complaint_repo.update(complaint_id, update_data)
        await self.db.commit()
        await self.db.refresh(complaint)

        return complaint

    async def assign_complaint(self, complaint_id: int, assigned_to: int) -> Complaint:
        """Assign complaint to a user."""
        complaint = await self.complaint_repo.get(complaint_id)
        if not complaint:
            raise NotFoundError("Complaint not found")

        update_data = {"assigned_to": assigned_to, "status": ComplaintStatus.IN_PROGRESS}

        complaint = await self.complaint_repo.update(complaint_id, update_data)
        await self.db.commit()
        await self.db.refresh(complaint)

        return complaint

    async def add_comment(self, complaint_id: int, user_id: int, comment: str) -> ComplaintComment:
        """Add a comment to a complaint."""
        complaint = await self.complaint_repo.get(complaint_id)
        if not complaint:
            raise NotFoundError("Complaint not found")

        comment_data = {
            "complaint_id": complaint_id,
            "user_id": user_id,
            "comment": comment,
        }

        comment_obj = await self.comment_repo.create(comment_data)
        await self.db.commit()
        await self.db.refresh(comment_obj)

        return comment_obj