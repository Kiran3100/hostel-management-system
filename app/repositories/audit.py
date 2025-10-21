"""Audit log repository."""

from sqlalchemy import select

from app.models.audit import AuditLog
from app.repositories.base import BaseRepository


class AuditLogRepository(BaseRepository[AuditLog]):
    """Audit log repository."""

    async def get_by_entity(self, entity_type: str, entity_id: int) -> list[AuditLog]:
        """Get audit logs by entity."""
        result = await self.db.execute(
            select(AuditLog)
            .where(AuditLog.entity_type == entity_type, AuditLog.entity_id == entity_id)
            .order_by(AuditLog.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_user(self, user_id: int) -> list[AuditLog]:
        """Get audit logs by user."""
        result = await self.db.execute(
            select(AuditLog)
            .where(AuditLog.user_id == user_id)
            .order_by(AuditLog.created_at.desc())
        )
        return list(result.scalars().all())