"""Hostel Admin service for managing multiple hostels."""

from typing import List, Optional
from datetime import datetime
import secrets
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.hostel import Hostel
from app.models.user import User, UserRole
from app.models.associations import user_hostel_association
from app.repositories.hostel import HostelRepository
from app.repositories.user import UserRepository
from app.exceptions import (
    NotFoundError,
    ConflictError,
    ValidationError,
    AuthorizationError,
)
from app.logging_config import get_logger

logger = get_logger(__name__)


class HostelAdminService:
    """Service for hostel admin multi-hostel management."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.hostel_repo = HostelRepository(Hostel, db)
        self.user_repo = UserRepository(User, db)

    @staticmethod
    def generate_admin_code() -> str:
        """Generate a unique admin code."""
        return f"ADMIN-{secrets.token_hex(4).upper()}"

    async def create_admin_code(self, admin_id: int) -> str:
        """
        Create or regenerate admin code for a hostel admin.
        
        Args:
            admin_id: Hostel admin user ID
        
        Returns:
            Generated admin code
        """
        user = await self.user_repo.get(admin_id)
        
        if not user:
            raise NotFoundError("User not found")
        
        if user.role != UserRole.HOSTEL_ADMIN:
            raise ValidationError("User is not a hostel admin")

        # Generate unique code
        admin_code = self.generate_admin_code()
        
        # Ensure uniqueness
        while await self._admin_code_exists(admin_code):
            admin_code = self.generate_admin_code()

        # Update user with admin code
        await self.user_repo.update(admin_id, {"admin_code": admin_code})
        await self.db.commit()

        logger.info(f"Generated admin code for user {admin_id}: {admin_code}")
        
        return admin_code

    async def register_hostel_with_admin_code(
        self,
        admin_code: str,
        hostel_name: str,
        hostel_code: str,
        address: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        pincode: Optional[str] = None,
        phone: Optional[str] = None,
        email: Optional[str] = None,
    ) -> Hostel:
        """
        Register a new hostel under a hostel admin using their admin code.
        
        Args:
            admin_code: The hostel admin's unique code
            hostel_name: Name of the new hostel
            hostel_code: Unique code for the hostel
            ... other hostel details
        
        Returns:
            Created hostel
        """
        # Find admin by code
        admin = await self._get_admin_by_code(admin_code)
        
        if not admin:
            raise NotFoundError("Invalid admin code")
        
        if admin.role != UserRole.HOSTEL_ADMIN:
            raise AuthorizationError("Admin code belongs to non-admin user")

        # Check if hostel code already exists
        existing_hostel = await self.hostel_repo.get_by_code(hostel_code)
        if existing_hostel:
            raise ConflictError(f"Hostel with code {hostel_code} already exists")

        # Create hostel
        hostel_data = {
            "name": hostel_name,
            "code": hostel_code,
            "address": address,
            "city": city,
            "state": state,
            "pincode": pincode,
            "phone": phone,
            "email": email,
            "is_active": True,
        }

        hostel = await self.hostel_repo.create(hostel_data)
        await self.db.flush()

        # Associate hostel with admin
        await self._associate_hostel_with_admin(admin.id, hostel.id)
        
        await self.db.commit()
        await self.db.refresh(hostel)

        logger.info(
            f"Registered hostel {hostel.name} (ID: {hostel.id}) "
            f"under admin {admin.email} (ID: {admin.id})"
        )

        return hostel

    async def add_hostel_to_admin(
        self,
        admin_id: int,
        hostel_id: int,
    ) -> None:
        """
        Add an existing hostel to a hostel admin's managed hostels.
        
        Args:
            admin_id: Hostel admin user ID
            hostel_id: Hostel ID to add
        """
        # Verify admin exists and is hostel admin
        admin = await self.user_repo.get(admin_id)
        if not admin:
            raise NotFoundError("Admin not found")
        
        if admin.role != UserRole.HOSTEL_ADMIN:
            raise ValidationError("User is not a hostel admin")

        # Verify hostel exists
        hostel = await self.hostel_repo.get(hostel_id)
        if not hostel:
            raise NotFoundError("Hostel not found")

        # Check if already associated
        if await self._is_hostel_associated(admin_id, hostel_id):
            raise ConflictError("Hostel already associated with this admin")

        # Associate hostel with admin
        await self._associate_hostel_with_admin(admin_id, hostel_id)
        await self.db.commit()

        logger.info(f"Added hostel {hostel_id} to admin {admin_id}")

    async def remove_hostel_from_admin(
        self,
        admin_id: int,
        hostel_id: int,
    ) -> None:
        """
        Remove a hostel from a hostel admin's managed hostels.
        
        Args:
            admin_id: Hostel admin user ID
            hostel_id: Hostel ID to remove
        """
        # Verify association exists
        if not await self._is_hostel_associated(admin_id, hostel_id):
            raise NotFoundError("Hostel not associated with this admin")

        # Remove association
        stmt = user_hostel_association.delete().where(
            user_hostel_association.c.user_id == admin_id,
            user_hostel_association.c.hostel_id == hostel_id,
        )
        await self.db.execute(stmt)
        await self.db.commit()

        logger.info(f"Removed hostel {hostel_id} from admin {admin_id}")

    async def get_admin_hostels(self, admin_id: int) -> List[Hostel]:
        """
        Get all hostels managed by a hostel admin.
        
        Args:
            admin_id: Hostel admin user ID
        
        Returns:
            List of hostels
        """
        admin = await self.user_repo.get(admin_id)
        
        if not admin:
            raise NotFoundError("Admin not found")
        
        if admin.role != UserRole.HOSTEL_ADMIN:
            raise ValidationError("User is not a hostel admin")

        # Get hostels through relationship
        result = await self.db.execute(
            select(Hostel)
            .join(user_hostel_association)
            .where(
                user_hostel_association.c.user_id == admin_id,
                Hostel.is_deleted == False,
            )
        )
        
        hostels = result.scalars().all()
        return list(hostels)

    async def transfer_hostel_ownership(
        self,
        hostel_id: int,
        from_admin_id: int,
        to_admin_id: int,
    ) -> None:
        """
        Transfer hostel ownership from one admin to another.
        
        Args:
            hostel_id: Hostel ID
            from_admin_id: Current admin ID
            to_admin_id: New admin ID
        """
        # Verify both admins exist and are hostel admins
        from_admin = await self.user_repo.get(from_admin_id)
        to_admin = await self.user_repo.get(to_admin_id)

        if not from_admin or not to_admin:
            raise NotFoundError("One or both admins not found")

        if from_admin.role != UserRole.HOSTEL_ADMIN or to_admin.role != UserRole.HOSTEL_ADMIN:
            raise ValidationError("Both users must be hostel admins")

        # Verify hostel exists
        hostel = await self.hostel_repo.get(hostel_id)
        if not hostel:
            raise NotFoundError("Hostel not found")

        # Verify from_admin owns the hostel
        if not await self._is_hostel_associated(from_admin_id, hostel_id):
            raise AuthorizationError("Source admin does not manage this hostel")

        # Remove from old admin
        await self.remove_hostel_from_admin(from_admin_id, hostel_id)
        
        # Add to new admin
        await self.add_hostel_to_admin(to_admin_id, hostel_id)

        logger.info(
            f"Transferred hostel {hostel_id} from admin {from_admin_id} to {to_admin_id}"
        )

    # Private helper methods

    async def _admin_code_exists(self, admin_code: str) -> bool:
        """Check if admin code already exists."""
        result = await self.db.execute(
            select(User).where(User.admin_code == admin_code)
        )
        return result.scalar_one_or_none() is not None

    async def _get_admin_by_code(self, admin_code: str) -> Optional[User]:
        """Get admin user by admin code."""
        result = await self.db.execute(
            select(User).where(User.admin_code == admin_code)
        )
        return result.scalar_one_or_none()

    async def _is_hostel_associated(self, admin_id: int, hostel_id: int) -> bool:
        """Check if hostel is associated with admin."""
        result = await self.db.execute(
            select(user_hostel_association).where(
                user_hostel_association.c.user_id == admin_id,
                user_hostel_association.c.hostel_id == hostel_id,
            )
        )
        return result.first() is not None

    async def _associate_hostel_with_admin(self, admin_id: int, hostel_id: int) -> None:
        """Associate hostel with admin in association table."""
        stmt = user_hostel_association.insert().values(
            user_id=admin_id,
            hostel_id=hostel_id,
        )
        await self.db.execute(stmt)