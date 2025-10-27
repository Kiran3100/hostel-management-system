"""User and authentication models - UPDATED WITH VISITOR ROLE."""

from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional, List

from sqlalchemy import String, Boolean, DateTime, ForeignKey, Enum, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, SoftDeleteMixin
from app.models.associations import user_hostel_association


class UserRole(str, PyEnum):
    """User roles."""

    SUPER_ADMIN = "SUPER_ADMIN"
    HOSTEL_ADMIN = "HOSTEL_ADMIN"
    TENANT = "TENANT"
    VISITOR = "VISITOR"  # ✅ NEW: Read-only access role


class User(Base, TimestampMixin, SoftDeleteMixin):
    """User model - can be associated with multiple hostels if admin."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), unique=True, nullable=True)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False)
    
    # For tenants and visitors - they belong to one hostel
    primary_hostel_id: Mapped[Optional[int]] = mapped_column(ForeignKey("hostels.id"), nullable=True)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    admin_code: Mapped[Optional[str]] = mapped_column(
    String(50), unique=True, nullable=True,
    comment="Unique code for hostel admins to register new hostels"
    )
    
    # ✅ NEW: Visitor-specific fields
    visitor_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, 
        comment="Expiration time for visitor accounts"
    )
    
    # Relationships
    hostels: Mapped[List["Hostel"]] = relationship(
        "Hostel",
        secondary=user_hostel_association,
        back_populates="admins"
    )
    
    refresh_tokens: Mapped[List["RefreshToken"]] = relationship(
        "RefreshToken", back_populates="user", cascade="all, delete-orphan"
    )
    tenant_profile: Mapped[Optional["TenantProfile"]] = relationship(
        "TenantProfile", back_populates="user", uselist=False
    )
    notifications: Mapped[List["Notification"]] = relationship(
        "Notification", back_populates="user", cascade="all, delete-orphan"
    )
    device_tokens: Mapped[List["DeviceToken"]] = relationship(
        "DeviceToken", back_populates="user", cascade="all, delete-orphan"
    )
    audit_logs: Mapped[List["AuditLog"]] = relationship(
        "AuditLog", back_populates="user", foreign_keys="AuditLog.user_id"
    )

    __table_args__ = (
        Index("idx_users_email", "email"),
        Index("idx_users_phone", "phone"),
        Index("idx_users_primary_hostel_id", "primary_hostel_id"),
        Index("idx_users_role", "role"),
    )

    @property
    def hostel_id(self) -> Optional[int]:
        """
        Get hostel_id for the user - backward compatibility property.
        - For TENANT/VISITOR: returns primary_hostel_id
        - For HOSTEL_ADMIN: returns first hostel from association
        - For SUPER_ADMIN: returns None
        """
        if self.role in [UserRole.TENANT, UserRole.VISITOR]:
            return self.primary_hostel_id
        elif self.role == UserRole.HOSTEL_ADMIN:
            return self.hostels[0].id if self.hostels else None
        else:  # SUPER_ADMIN
            return None

    def get_hostel_ids(self) -> List[int]:
        """Get list of hostel IDs this user has access to."""
        if self.role == UserRole.SUPER_ADMIN:
            return []  # Super admin has access to all
        elif self.role in [UserRole.TENANT, UserRole.VISITOR]:
            return [self.primary_hostel_id] if self.primary_hostel_id else []
        else:  # HOSTEL_ADMIN
            # First try to get from many-to-many relationship
            hostel_ids = [h.id for h in self.hostels]
            
            # Fallback to primary_hostel_id if no associations exist
            if not hostel_ids and self.primary_hostel_id:
                hostel_ids = [self.primary_hostel_id]
            
            return hostel_ids
    
    def is_visitor_expired(self) -> bool:
        """Check if visitor account has expired."""
        if self.role != UserRole.VISITOR:
            return False
        if not self.visitor_expires_at:
            return False
        return datetime.utcnow() > self.visitor_expires_at

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"


class RefreshToken(Base, TimestampMixin):
    """Refresh token model."""

    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="refresh_tokens")

    __table_args__ = (Index("idx_refresh_tokens_user_id", "user_id"),)


class OTPCode(Base, TimestampMixin):
    """OTP code model for phone authentication."""

    __tablename__ = "otp_codes"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    code_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    attempts: Mapped[int] = mapped_column(default=0, nullable=False)

    __table_args__ = (Index("idx_otp_codes_phone", "phone"),)