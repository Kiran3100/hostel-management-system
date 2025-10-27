"""Notice repository - FIXED."""

from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload

from app.models.notice import Notice
from app.repositories.base import BaseRepository


class NoticeRepository(BaseRepository[Notice]):
    """Notice repository with proper relationship loading."""

    async def get(self, id: int) -> Optional[Notice]:
        """Get notice by ID with relationships."""
        result = await self.db.execute(
            select(Notice)
            .where(Notice.id == id)
            .options(
                selectinload(Notice.hostel),
                selectinload(Notice.author)
            )
        )
        return result.scalar_one_or_none()

    async def get_active_by_hostel(self, hostel_id: int) -> List[Notice]:
        """Get active notices for a hostel."""
        now = datetime.now(timezone.utc)
        
        result = await self.db.execute(
            select(Notice)
            .where(
                and_(
                    Notice.hostel_id == hostel_id,
                    or_(
                        Notice.published_at.is_(None),
                        Notice.published_at <= now
                    ),
                    or_(
                        Notice.expires_at.is_(None),
                        Notice.expires_at > now
                    )
                )
            )
            .options(
                selectinload(Notice.hostel),
                selectinload(Notice.author)
            )
            .order_by(Notice.published_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_hostel(self, hostel_id: int) -> List[Notice]:
        """Get all notices for a hostel (including expired)."""
        result = await self.db.execute(
            select(Notice)
            .where(Notice.hostel_id == hostel_id)
            .options(
                selectinload(Notice.hostel),
                selectinload(Notice.author)
            )
            .order_by(Notice.created_at.desc())
        )
        return list(result.scalars().all())