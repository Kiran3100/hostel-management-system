"""Authentication service - FIXED VERSION."""

from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

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
        password: str,
        role: str,
        hostel_code: Optional[str]
    ) -> Dict[str, Any]:
        """Register a new user and return user data as dict"""
        
        from app.models.user import User
        from app.models.hostel import Hostel
        
        # Validate input
        if not email and not phone:
            raise ValidationError("Either email or phone is required")
        
        # Check if user already exists
        if email:
            stmt = select(User).where(User.email == email)
            result = await self.db.execute(stmt)
            if result.scalar_one_or_none():
                raise ConflictError(f"User with email {email} already exists")
        
        if phone:
            stmt = select(User).where(User.phone == phone)
            result = await self.db.execute(stmt)
            if result.scalar_one_or_none():
                raise ConflictError(f"User with phone {phone} already exists")
        
        # Get hostel_id from hostel_code if provided
        hostel_id = None
        if hostel_code and role != "SUPER_ADMIN":
            stmt = select(Hostel).where(Hostel.code == hostel_code)
            result = await self.db.execute(stmt)
            hostel = result.scalar_one_or_none()
            if not hostel:
                raise NotFoundError(f"Hostel with code {hostel_code} not found")
            hostel_id = hostel.id
        
        # ✅ FIXED: Create new user with correct field name 'password_hash'
        new_user = User(
            email=email,
            phone=phone,
            password_hash=hash_password(password),  # ✅ CORRECT: use password_hash
            role=role,
            primary_hostel_id=hostel_id,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.db.add(new_user)
        await self.db.flush()
        
        # Store the data before commit
        user_data = {
            "id": new_user.id,
            "email": new_user.email,
            "phone": new_user.phone,
            "role": new_user.role,
            "primary_hostel_id": new_user.primary_hostel_id,
            "is_active": new_user.is_active,
            "is_verified": new_user.is_verified,
            "created_at": new_user.created_at,
            "updated_at": new_user.updated_at
        }
        
        await self.db.commit()
        
        return user_data
    
    async def authenticate_user(
        self,
        email: Optional[str],
        phone: Optional[str],
        password: str
    ) -> Optional[Dict[str, Any]]:
        """Authenticate a user by email/phone and password"""
        
        from app.models.user import User
        
        if email:
            stmt = select(User).where(User.email == email)
        elif phone:
            stmt = select(User).where(User.phone == phone)
        else:
            return None
        
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            return None
        
        # ✅ FIXED: Use user.password_hash (correct field name)
        if not verify_password(password, user.password_hash):
            return None
        
        return {
            "id": user.id,
            "email": user.email,
            "phone": user.phone,
            "role": user.role,
            "primary_hostel_id": user.primary_hostel_id,
            "is_active": user.is_active,
            "created_at": user.created_at,
            "updated_at": user.updated_at
        }

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