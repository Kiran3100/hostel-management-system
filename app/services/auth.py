"""Authentication service - FULLY FIXED VERSION with proper polymorphic user creation."""

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
        """
        Register a new user with proper polymorphic profile creation.
        
        ✅ FIXED: Creates proper User + Profile records based on role.
        """
        from app.models.user import User, SuperAdmin, HostelAdmin, Tenant, Visitor
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
        
        # ✅ FIX 1: Create base User WITHOUT primary_hostel_id
        new_user = User(
            email=email,
            phone=phone,
            password_hash=hash_password(password),
            role=role,
            is_active=True,
            is_verified=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.db.add(new_user)
        await self.db.flush()  # Get the user.id
        
        # ✅ FIX 2: Create appropriate profile based on role
        if role == "SUPER_ADMIN":
            profile = SuperAdmin(
                user_id=new_user.id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            self.db.add(profile)
            
        elif role == "HOSTEL_ADMIN":
            if not hostel_id:
                raise ValidationError("hostel_code required for Hostel Admin")
            
            profile = HostelAdmin(
                user_id=new_user.id,
                primary_hostel_id=hostel_id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            self.db.add(profile)
            await self.db.flush()
            
            # Associate with hostel via many-to-many table
            from app.models.associations import user_hostel_association
            stmt = user_hostel_association.insert().values(
                user_id=new_user.id,
                hostel_id=hostel_id
            )
            await self.db.execute(stmt)
            
        elif role == "TENANT":
            if not hostel_id:
                raise ValidationError("hostel_code required for Tenant")
            
            # Create Tenant profile (NOT TenantProfile - that's the old model)
            # Derive a default full_name from email/phone
            if email:
                full_name = email.split('@')[0].replace('.', ' ').replace('_', ' ').title()
            else:
                full_name = f"Tenant {phone[-4:]}"
            
            profile = Tenant(
                user_id=new_user.id,
                hostel_id=hostel_id,
                full_name=full_name,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            self.db.add(profile)
            
        elif role == "VISITOR":
            if not hostel_id:
                raise ValidationError("hostel_code required for Visitor")
            
            # Visitors expire after 30 days by default
            expires_at = datetime.utcnow() + timedelta(days=30)
            
            profile = Visitor(
                user_id=new_user.id,
                hostel_id=hostel_id,
                visitor_expires_at=expires_at,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            self.db.add(profile)
        
        else:
            raise ValidationError(f"Invalid role: {role}")
        
        await self.db.flush()
        
        # ✅ FIX 3: Build response data using the profile's hostel_id
        user_data = {
            "id": new_user.id,
            "email": new_user.email,
            "phone": new_user.phone,
            "role": new_user.role,
            "hostel_id": hostel_id,  # From the profile, not User
            "is_active": new_user.is_active,
            "is_verified": new_user.is_verified,
            "last_login": None,
            "created_at": new_user.created_at,
            "updated_at": new_user.updated_at
        }
        
        await self.db.commit()
        
        return user_data
    
    # ... rest of the methods remain the same ...

    async def login(self, email: str, password: str) -> Tuple[str, str, User]:
        """Login with email and password."""
        user = await self.user_repo.get_by_email(email)
        if not user or not user.password_hash:
            raise AuthenticationError("Invalid email or password")

        if not verify_password(password, user.password_hash):
            raise AuthenticationError("Invalid email or password")

        if not user.is_active:
            raise AuthenticationError("Account is inactive")

        access_token = create_access_token({"sub": str(user.id), "role": user.role.value})
        refresh_token = create_refresh_token({"sub": str(user.id)})

        await self._store_refresh_token(user.id, refresh_token)
        await self.user_repo.update_last_login(user.id)
        await self.db.commit()

        return access_token, refresh_token, user

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