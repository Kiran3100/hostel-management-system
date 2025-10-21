# app/repositories/user.py - UPDATE

"""User repository - FIXED SOFT DELETE FILTERING."""

from typing import Optional
from datetime import datetime
from sqlalchemy import select, or_

from app.models.user import User, RefreshToken, OTPCode, UserRole
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """User repository with soft delete support."""

    async def get(self, id: int) -> Optional[User]:
        """Get user by ID, excluding soft-deleted."""
        result = await self.db.execute(
            select(User).where(
                User.id == id,
                User.is_deleted == False  # ✅ ADDED: Filter soft-deleted
            )
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email, excluding soft-deleted."""
        result = await self.db.execute(
            select(User).where(
                User.email == email, 
                User.is_deleted == False  # ✅ Already filtered
            )
        )
        return result.scalar_one_or_none()

    async def get_by_phone(self, phone: str) -> Optional[User]:
        """Get user by phone, excluding soft-deleted."""
        result = await self.db.execute(
            select(User).where(
                User.phone == phone, 
                User.is_deleted == False  # ✅ Already filtered
            )
        )
        return result.scalar_one_or_none()

    async def get_by_email_or_phone(self, email: str, phone: str) -> Optional[User]:
        """Get user by email or phone, excluding soft-deleted."""
        result = await self.db.execute(
            select(User).where(
                or_(User.email == email, User.phone == phone), 
                User.is_deleted == False  # ✅ Already filtered
            )
        )
        return result.scalar_one_or_none()

    async def get_by_hostel(self, hostel_id: int, role: Optional[UserRole] = None) -> list[User]:
        """Get users by hostel, excluding soft-deleted."""
        query = select(User).where(
            User.hostel_id == hostel_id, 
            User.is_deleted == False  # ✅ Already filtered
        )

        if role:
            query = query.where(User.role == role)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_last_login(self, user_id: int) -> None:
        """Update last login timestamp."""
        await self.update(user_id, {"last_login": datetime.utcnow()})


class RefreshTokenRepository(BaseRepository[RefreshToken]):
    """Refresh token repository."""

    async def get_by_token_hash(self, token_hash: str) -> Optional[RefreshToken]:
        """Get refresh token by hash."""
        result = await self.db.execute(
            select(RefreshToken).where(
                RefreshToken.token_hash == token_hash, RefreshToken.is_revoked == False
            )
        )
        return result.scalar_one_or_none()

    async def revoke_user_tokens(self, user_id: int) -> None:
        """Revoke all tokens for a user."""
        from sqlalchemy import update

        stmt = (
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id)
            .values(is_revoked=True)
        )
        await self.db.execute(stmt)
        await self.db.flush()


class OTPRepository(BaseRepository[OTPCode]):
    """OTP code repository."""

    async def get_latest_by_phone(self, phone: str) -> Optional[OTPCode]:
        """Get latest OTP for a phone number."""
        result = await self.db.execute(
            select(OTPCode)
            .where(OTPCode.phone == phone, OTPCode.is_used == False)
            .order_by(OTPCode.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def mark_used(self, otp_id: int) -> None:
        """Mark OTP as used."""
        await self.update(otp_id, {"is_used": True})

    async def increment_attempts(self, otp_id: int) -> None:
        """Increment OTP verification attempts."""
        otp = await self.get(otp_id)
        if otp:
            await self.update(otp_id, {"attempts": otp.attempts + 1})