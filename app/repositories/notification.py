"""Notification repository."""

from sqlalchemy import select

from app.models.notification import Notification, DeviceToken
from app.repositories.base import BaseRepository


class NotificationRepository(BaseRepository[Notification]):
    """Notification repository."""

    async def get_by_user(self, user_id: int, is_read: bool = None) -> list[Notification]:
        """Get notifications by user."""
        query = select(Notification).where(Notification.user_id == user_id)

        if is_read is not None:
            query = query.where(Notification.is_read == is_read)

        query = query.order_by(Notification.created_at.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def mark_all_read(self, user_id: int) -> None:
        """Mark all notifications as read."""
        from sqlalchemy import update
        from datetime import datetime

        stmt = (
            update(Notification)
            .where(Notification.user_id == user_id, Notification.is_read == False)
            .values(is_read=True, read_at=datetime.utcnow())
        )
        await self.db.execute(stmt)
        await self.db.flush()


class DeviceTokenRepository(BaseRepository[DeviceToken]):
    """Device token repository."""

    async def get_by_user(self, user_id: int) -> list[DeviceToken]:
        """Get device tokens by user."""
        result = await self.db.execute(
            select(DeviceToken).where(
                DeviceToken.user_id == user_id, DeviceToken.is_active == True
            )
        )
        return list(result.scalars().all())