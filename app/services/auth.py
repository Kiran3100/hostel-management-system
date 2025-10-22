"""Authentication service - UPDATED WITH MULTI-HOSTEL SUPPORT."""

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
    """Authentication service with multi-hostel support."""

    def __init__(
        self,
        db: AsyncSession,
        otp_provider: OTPProvider,
    ):
        self.db = db
        self.user_repo = UserRepository(User, db)
        self.token_repo = RefreshTokenRepository(RefreshToken, db)
        self.otp_repo = OTPRepository(OTPCode, db)
        
        from app.models.hostel import Hostel
        self.hostel_repo = HostelRepository(Hostel, db)
        
        self.otp_provider = otp_provider

    async def register_user(
        self,
        email: Optional[str],
        phone: Optional[str],
        password: Optional[str],
        role: UserRole,
        hostel_code: Optional[str] = None,
        hostel_codes: Optional[list[str]] = None,  # ✅ NEW: Support multiple codes
    ) -> User:
        """
        Register a new user using hostel code(s).
        
        Args:
            email: User email
            phone: User phone
            password: User password
            role: User role
            hostel_code: Single hostel code (for backward compatibility)
            hostel_codes: List of hostel codes (for multi-hostel admins)
        
        Returns:
            Created user with all hostel associations loaded
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

        # ✅ NEW: Handle multiple hostel codes
        hostels = []
        hostel_id = None
        
        if role != UserRole.SUPER_ADMIN:
            # Collect all hostel codes (prefer hostel_codes array, fallback to single code)
            codes = hostel_codes if hostel_codes else ([hostel_code] if hostel_code else [])
            
            if not codes:
                raise ValidationError("Hostel code(s) required for non-admin users")
            
            # Validate all hostel codes and collect hostel objects
            for code in codes:
                hostel = await self.hostel_repo.get_by_code(code)
                if not hostel:
                    raise NotFoundError(f"Hostel with code '{code}' not found")
                
                if not hostel.is_active:
                    raise ValidationError(f"Hostel '{hostel.name}' (code: {code}) is not active")
                
                hostels.append(hostel)
            
            # Set primary_hostel_id to the first hostel (for backward compatibility)
            hostel_id = hostels[0].id if hostels else None

        # Hash password if provided
        password_hash = hash_password(password) if password else None

        # Create user
        user_data = {
            "email": email,
            "phone": phone,
            "password_hash": password_hash,
            "role": role,
            "primary_hostel_id": hostel_id,  # First hostel for backward compatibility
            "is_verified": True if role == UserRole.SUPER_ADMIN else False,
        }

        user = await self.user_repo.create(user_data)
        
        # ✅ NEW: For HOSTEL_ADMIN, add ALL hostels to association table
        if role == UserRole.HOSTEL_ADMIN and hostels:
            from sqlalchemy import insert
            from app.models.associations import user_hostel_association
            
            # Add all hostels to the many-to-many relationship
            for hostel in hostels:
                stmt = insert(user_hostel_association).values(
                    user_id=user.id,
                    hostel_id=hostel.id
                )
                await self.db.execute(stmt)
        
        await self.db.commit()
        
        # ✅ NEW: Refresh user to load relationships
        await self.db.refresh(user)

        return user

    async def add_hostel_to_admin(
        self,
        user_id: int,
        hostel_code: str,
    ) -> User:
        """
        Add a hostel to an existing hostel admin.
        
        Args:
            user_id: Admin user ID
            hostel_code: Hostel code to add
        
        Returns:
            Updated user with new hostel association
        """
        user = await self.user_repo.get(user_id)
        if not user:
            raise NotFoundError("User not found")
        
        if user.role != UserRole.HOSTEL_ADMIN:
            raise ValidationError("User must be a hostel admin")
        
        # Validate hostel
        hostel = await self.hostel_repo.get_by_code(hostel_code)
        if not hostel:
            raise NotFoundError(f"Hostel with code '{hostel_code}' not found")
        
        if not hostel.is_active:
            raise ValidationError(f"Hostel '{hostel.name}' is not active")
        
        # Check if already associated
        current_hostel_ids = user.get_hostel_ids()
        if hostel.id in current_hostel_ids:
            raise ConflictError(f"Admin already manages hostel '{hostel.name}'")
        
        # Add to association table
        from sqlalchemy import insert
        from app.models.associations import user_hostel_association
        
        stmt = insert(user_hostel_association).values(
            user_id=user.id,
            hostel_id=hostel.id
        )
        await self.db.execute(stmt)
        await self.db.commit()
        
        # Refresh to load updated relationships
        await self.db.refresh(user)
        
        return user

    async def remove_hostel_from_admin(
        self,
        user_id: int,
        hostel_id: int,
    ) -> User:
        """
        Remove a hostel from an admin (must have at least one remaining).
        
        Args:
            user_id: Admin user ID
            hostel_id: Hostel ID to remove
        
        Returns:
            Updated user
        """
        user = await self.user_repo.get(user_id)
        if not user:
            raise NotFoundError("User not found")
        
        if user.role != UserRole.HOSTEL_ADMIN:
            raise ValidationError("User must be a hostel admin")
        
        # Check current hostels
        current_hostel_ids = user.get_hostel_ids()
        
        if hostel_id not in current_hostel_ids:
            raise ValidationError("Admin does not manage this hostel")
        
        if len(current_hostel_ids) == 1:
            raise ValidationError("Cannot remove last hostel. Admin must manage at least one hostel.")
        
        # Remove from association table
        from sqlalchemy import delete
        from app.models.associations import user_hostel_association
        
        stmt = delete(user_hostel_association).where(
            user_hostel_association.c.user_id == user.id,
            user_hostel_association.c.hostel_id == hostel_id
        )
        await self.db.execute(stmt)
        
        # Update primary_hostel_id if we're removing it
        if user.primary_hostel_id == hostel_id:
            remaining_ids = [hid for hid in current_hostel_ids if hid != hostel_id]
            await self.user_repo.update(user.id, {"primary_hostel_id": remaining_ids[0]})
        
        await self.db.commit()
        
        # Refresh to load updated relationships
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