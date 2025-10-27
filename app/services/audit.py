"""Audit logging service."""

from typing import Optional, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog, AuditAction
from app.repositories.audit import AuditLogRepository


class AuditService:
    """Audit logging service."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.audit_repo = AuditLogRepository(AuditLog, db)

    async def log(
        self,
        user_id: Optional[int],
        hostel_id: Optional[int],
        entity_type: str,
        entity_id: Optional[int],
        action: AuditAction,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLog:
        """Log an audit event."""
        audit_data = {
            "user_id": user_id,
            "hostel_id": hostel_id,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "action": action,
            "old_values": old_values,
            "new_values": new_values,
            "ip_address": ip_address,
            "user_agent": user_agent,
        }

        audit_log = await self.audit_repo.create(audit_data)
        await self.db.commit()

        return audit_log