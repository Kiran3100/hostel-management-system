"""Visitor management service."""

from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole
from app.repositories.user import UserRepository
from app.repositories.hostel import HostelRepository
from app.exceptions import (
    NotFoundError,
    ValidationError,
    ConflictError,
    AuthorizationError,
)
from app.core.security import hash_password, generate_otp


class VisitorService:
    """Service for managing visitor accounts."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(User, db)
        from app.models.hostel import Hostel
        self.hostel_repo = HostelRepository(Hostel, db)

    async def create_visitor(
        self,
        email: Optional[str],
        phone: Optional[str],
        hostel_id: int,
        duration_days: int = 30,
        password: Optional[str] = None,
        created_by_admin_id: int = None,
    ) -> User:
        """
        Create a new visitor account.
        
        Args:
            email: Visitor email (optional)
            phone: Visitor phone (optional)
            hostel_id: Hostel to grant access to
            duration_days: Number of days before account expires (default 30)
            password: Optional password (if not provided, generates temporary one)
            created_by_admin_id: ID of admin creating the visitor account
        
        Returns:
            Created visitor user
        """
        # Validate at least one contact method
        if not email and not phone:
            raise ValidationError("Either email or phone is required")

        # Check for existing user
        if email:
            existing = await self.user_repo.get_by_email(email)
            if existing:
                raise ConflictError("Email already registered")

        if phone:
            existing = await self.user_repo.get_by_phone(phone)
            if existing:
                raise ConflictError("Phone already registered")

        # Validate hostel exists
        hostel = await self.hostel_repo.get(hostel_id)
        if not hostel:
            raise NotFoundError("Hostel not found")

        # Generate temporary password if not provided
        if not password:
            password = generate_otp(8)  # 8-digit temporary password

        password_hash = hash_password(password)

        # Calculate expiration time
        expires_at = datetime.utcnow() + timedelta(days=duration_days)

        # Create visitor user
        user_data = {
            "email": email,
            "phone": phone,
            "password_hash": password_hash,
            "role": UserRole.VISITOR,
            "primary_hostel_id": hostel_id,
            "is_verified": False,  # Visitors are not verified
            "is_active": True,
            "visitor_expires_at": expires_at,
        }

        user = await self.user_repo.create(user_data)
        await self.db.commit()

        # Log the visitor creation
        from app.models.audit import AuditLog, AuditAction
        from app.repositories.audit import AuditLogRepository
        
        audit_repo = AuditLogRepository(AuditLog, self.db)
        await audit_repo.create({
            "user_id": created_by_admin_id,
            "hostel_id": hostel_id,
            "entity_type": "User",
            "entity_id": user.id,
            "action": AuditAction.CREATE,
            "new_values": {
                "role": "VISITOR",
                "email": email,
                "phone": phone,
                "expires_at": expires_at.isoformat(),
            },
        })
        await self.db.commit()

        return user

    async def extend_visitor_access(
        self,
        visitor_id: int,
        additional_days: int,
        extended_by_admin_id: int,
    ) -> User:
        """
        Extend visitor account expiration.
        
        Args:
            visitor_id: Visitor user ID
            additional_days: Number of days to extend
            extended_by_admin_id: ID of admin extending access
        
        Returns:
            Updated visitor user
        """
        user = await self.user_repo.get(visitor_id)
        
        if not user:
            raise NotFoundError("Visitor not found")
        
        if user.role != UserRole.VISITOR:
            raise ValidationError("User is not a visitor")

        # Calculate new expiration
        current_expiration = user.visitor_expires_at or datetime.utcnow()
        
        # If already expired, extend from now
        if current_expiration < datetime.utcnow():
            new_expiration = datetime.utcnow() + timedelta(days=additional_days)
        else:
            new_expiration = current_expiration + timedelta(days=additional_days)

        # Update visitor
        user = await self.user_repo.update(
            visitor_id,
            {"visitor_expires_at": new_expiration}
        )
        await self.db.commit()

        # Log the extension
        from app.models.audit import AuditLog, AuditAction
        from app.repositories.audit import AuditLogRepository
        
        audit_repo = AuditLogRepository(AuditLog, self.db)
        await audit_repo.create({
            "user_id": extended_by_admin_id,
            "hostel_id": user.primary_hostel_id,
            "entity_type": "User",
            "entity_id": visitor_id,
            "action": AuditAction.UPDATE,
            "old_values": {"expires_at": current_expiration.isoformat()},
            "new_values": {"expires_at": new_expiration.isoformat()},
        })
        await self.db.commit()

        return user

    async def revoke_visitor_access(
        self,
        visitor_id: int,
        revoked_by_admin_id: int,
    ) -> User:
        """
        Immediately revoke visitor access.
        
        Args:
            visitor_id: Visitor user ID
            revoked_by_admin_id: ID of admin revoking access
        
        Returns:
            Updated visitor user
        """
        user = await self.user_repo.get(visitor_id)
        
        if not user:
            raise NotFoundError("Visitor not found")
        
        if user.role != UserRole.VISITOR:
            raise ValidationError("User is not a visitor")

        # Set expiration to now
        user = await self.user_repo.update(
            visitor_id,
            {
                "visitor_expires_at": datetime.utcnow(),
                "is_active": False,
            }
        )
        await self.db.commit()

        # Log the revocation
        from app.models.audit import AuditLog, AuditAction
        from app.repositories.audit import AuditLogRepository
        
        audit_repo = AuditLogRepository(AuditLog, self.db)
        await audit_repo.create({
            "user_id": revoked_by_admin_id,
            "hostel_id": user.primary_hostel_id,
            "entity_type": "User",
            "entity_id": visitor_id,
            "action": AuditAction.UPDATE,
            "new_values": {
                "status": "revoked",
                "is_active": False,
            },
        })
        await self.db.commit()

        return user

    async def get_active_visitors(self, hostel_id: int) -> list[User]:
        """Get all active visitors for a hostel."""
        filters = {
            "role": UserRole.VISITOR,
            "primary_hostel_id": hostel_id,
            "is_active": True,
            "is_deleted": False,
        }
        
        visitors = await self.user_repo.get_multi(filters=filters)
        
        # Filter out expired visitors
        active_visitors = [
            v for v in visitors 
            if not v.is_visitor_expired()
        ]
        
        return active_visitors

    async def cleanup_expired_visitors(self) -> int:
        """
        Deactivate all expired visitor accounts.
        
        Returns:
            Number of accounts deactivated
        """
        filters = {
            "role": UserRole.VISITOR,
            "is_active": True,
            "is_deleted": False,
        }
        
        visitors = await self.user_repo.get_multi(filters=filters, limit=1000)
        
        deactivated_count = 0
        for visitor in visitors:
            if visitor.is_visitor_expired():
                await self.user_repo.update(
                    visitor.id,
                    {"is_active": False}
                )
                deactivated_count += 1
        
        if deactivated_count > 0:
            await self.db.commit()
        
        return deactivated_count