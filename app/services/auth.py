"""Authentication service."""

from datetime import datetime, timedelta
from typing import Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_token,
    generate_otp,
    hash_otp,
    verify_otp,
)
from app.config import settings
from app.exceptions import (
    AuthenticationError,
    NotFoundError,
    ValidationError,
    ConflictError,
)
from app.models.user import User, UserRole, RefreshToken, OTPCode
from app.repositories.user import UserRepository, RefreshTokenRepository, OTPRepository
from app.repositories.hostel import HostelRepository
from app.schemas.auth import LoginResponse
from app.adapters.otp.base import OTPProvider


class AuthService:
    """Authentication service."""

    def __init__(
        self,
        db: AsyncSession,
        otp_provider: OTPProvider,
    ):
        self.db = db
        self.user_repo = UserRepository(User, db)
        self.token_repo = RefreshTokenRepository(RefreshToken, db)
        self.otp_repo = OTPRepository(OTPCode, db)
        
        # Import Hostel model here to avoid circular imports
        from app.models.hostel import Hostel
        self.hostel_repo = HostelRepository(Hostel, db)
        
        self.otp_provider = otp_provider

    async def register_user(
        self,
        email: Optional[str],
        phone: Optional[str],
        password: Optional[str],
        role: UserRole,
        hostel_id: Optional[int] = None,
    ) -> User:
        """Register a new user."""
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

        # ✅ UPDATED: For HOSTEL_ADMIN, hostel_id is REQUIRED
        if role == UserRole.HOSTEL_ADMIN:
            if not hostel_id:
                raise ValidationError("Hostel ID is required for Hostel Admin registration")
            
            hostel = await self.hostel_repo.get(hostel_id)
            if not hostel:
                raise NotFoundError(f"Hostel with ID {hostel_id} not found")
            
            if not hostel.is_active:
                raise ValidationError("Cannot register admin for inactive hostel")

        # Validate hostel for non-super-admin
        if role != UserRole.SUPER_ADMIN:
            if not hostel_id:
                raise ValidationError("Hostel ID required for non-admin users")

            hostel = await self.hostel_repo.get(hostel_id)
            if not hostel:
                raise NotFoundError("Hostel not found")

        # Hash password if provided
        password_hash = hash_password(password) if password else None

        # ✅ UPDATED: Create user with primary_hostel_id for HOSTEL_ADMIN
        user_data = {
            "email": email,
            "phone": phone,
            "password_hash": password_hash,
            "role": role,
            "primary_hostel_id": hostel_id if role == UserRole.HOSTEL_ADMIN else None,
            "is_verified": True if role == UserRole.SUPER_ADMIN else False,
        }

        user = await self.user_repo.create(user_data)
        await self.db.flush()  # Flush to get user.id
        
        # ✅ UPDATED: Associate hostel admin with hostel via association table
        if role == UserRole.HOSTEL_ADMIN and hostel_id:
            from app.models.associations import user_hostel_association
            
            stmt = user_hostel_association.insert().values(
                user_id=user.id,
                hostel_id=hostel_id
            )
            await self.db.execute(stmt)
        
        await self.db.commit()
        await self.db.refresh(user)

        return user

    async def login(self, email: str, password: str) -> Tuple[str, str, User]:
        """Login with email and password."""
        # Get user
        user = await self.user_repo.get_by_email(email)
        if not user or not user.password_hash:
            raise AuthenticationError("Invalid email or password")

        # Verify password
        if not verify_password(password, user.password_hash):
            raise AuthenticationError("Invalid email or password")

        # Check if active
        if not user.is_active:
            raise AuthenticationError("Account is inactive")

        # Create tokens
        access_token = create_access_token({"sub": str(user.id), "role": user.role.value})
        refresh_token = create_refresh_token({"sub": str(user.id)})

        # Store refresh token
        await self._store_refresh_token(user.id, refresh_token)

        # Update last login
        await self.user_repo.update_last_login(user.id)
        await self.db.commit()

        return access_token, refresh_token, user

    async def request_otp(self, phone: str, hostel_code: str) -> bool:
        """Request OTP for phone login."""
        # Verify hostel exists
        hostel = await self.hostel_repo.get_by_code(hostel_code)
        if not hostel:
            raise NotFoundError("Invalid hostel code")

        # Check if user exists with this phone
        user = await self.user_repo.get_by_phone(phone)
        if not user:
            raise NotFoundError("Phone number not registered")

        if user.primary_hostel_id != hostel.id:
            raise AuthenticationError("Phone not registered with this hostel")

        # Generate OTP
        otp_code = generate_otp(6)
        otp_hash = hash_otp(otp_code)

        # Store OTP
        otp_data = {
            "phone": phone,
            "code_hash": otp_hash,
            "expires_at": datetime.utcnow() + timedelta(minutes=settings.otp_expiry_minutes),
        }

        await self.otp_repo.create(otp_data)
        await self.db.commit()

        # Send OTP
        await self.otp_provider.send_otp(phone, otp_code)

        return True

    async def verify_otp(self, phone: str, otp: str) -> Tuple[str, str, User]:
        """Verify OTP and login."""
        # Get latest OTP
        otp_record = await self.otp_repo.get_latest_by_phone(phone)
        if not otp_record:
            raise AuthenticationError("No OTP found for this phone")

        # Check expiry
        if otp_record.expires_at < datetime.utcnow():
            raise AuthenticationError("OTP expired")

        # Check attempts
        if otp_record.attempts >= 3:
            raise AuthenticationError("Too many failed attempts")

        # Verify OTP
        if not verify_otp(otp, otp_record.code_hash):
            await self.otp_repo.increment_attempts(otp_record.id)
            await self.db.commit()
            raise AuthenticationError("Invalid OTP")

        # Mark OTP as used
        await self.otp_repo.mark_used(otp_record.id)

        # Get user
        user = await self.user_repo.get_by_phone(phone)
        if not user:
            raise AuthenticationError("User not found")

        # Create tokens
        access_token = create_access_token({"sub": str(user.id), "role": user.role.value})
        refresh_token = create_refresh_token({"sub": str(user.id)})

        # Store refresh token
        await self._store_refresh_token(user.id, refresh_token)

        # Update last login
        await self.user_repo.update_last_login(user.id)
        await self.db.commit()

        return access_token, refresh_token, user

    async def refresh_access_token(self, refresh_token: str) -> str:
        """Refresh access token."""
        # Decode token
        try:
            payload = decode_token(refresh_token)
        except Exception:
            raise AuthenticationError("Invalid refresh token")

        if payload.get("type") != "refresh":
            raise AuthenticationError("Invalid token type")

        user_id = int(payload.get("sub"))

        # Verify token exists and not revoked
        token_hash = hash_token(refresh_token)
        token_record = await self.token_repo.get_by_token_hash(token_hash)

        if not token_record or token_record.is_revoked:
            raise AuthenticationError("Token revoked or invalid")

        # Get user
        user = await self.user_repo.get(user_id)
        if not user or not user.is_active:
            raise AuthenticationError("User not found or inactive")

        # Create new access token
        access_token = create_access_token({"sub": str(user.id), "role": user.role.value})

        return access_token

    async def logout(self, user_id: int, refresh_token: str) -> bool:
        """Logout user (revoke refresh token)."""
        token_hash = hash_token(refresh_token)
        token_record = await self.token_repo.get_by_token_hash(token_hash)

        if token_record:
            await self.token_repo.update(token_record.id, {"is_revoked": True})
            await self.db.commit()

        return True

    async def change_password(self, user_id: int, old_password: str, new_password: str) -> bool:
        """Change user password."""
        user = await self.user_repo.get(user_id)
        if not user or not user.password_hash:
            raise NotFoundError("User not found")

        # Verify old password
        if not verify_password(old_password, user.password_hash):
            raise AuthenticationError("Invalid old password")

        # Update password
        new_hash = hash_password(new_password)
        await self.user_repo.update(user_id, {"password_hash": new_hash})

        # Revoke all tokens
        await self.token_repo.revoke_user_tokens(user_id)
        await self.db.commit()

        return True

    async def _store_refresh_token(self, user_id: int, token: str) -> None:
        """Store refresh token in database."""
        token_hash = hash_token(token)
        expires_at = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)

        token_data = {
            "user_id": user_id,
            "token_hash": token_hash,
            "expires_at": expires_at,
        }

        await self.token_repo.create(token_data)