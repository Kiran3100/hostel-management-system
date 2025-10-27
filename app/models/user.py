"""User models - REFACTORED WITH SEPARATE TABLES FOR EACH USER TYPE."""

from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional, List

from sqlalchemy import String, Boolean, DateTime, ForeignKey, Enum, Index, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, SoftDeleteMixin
from app.models.associations import user_hostel_association


class UserRole(str, PyEnum):
    """User roles."""

    SUPER_ADMIN = "SUPER_ADMIN"
    HOSTEL_ADMIN = "HOSTEL_ADMIN"
    TENANT = "TENANT"
    VISITOR = "VISITOR"


# ===== BASE USER TABLE =====

class User(Base, TimestampMixin, SoftDeleteMixin):
    """
    Base user table - contains common fields for all user types.
    
    This is the polymorphic base table. Specific user data is stored
    in separate tables based on role.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), unique=True, nullable=True)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Polymorphic relationships - one-to-one with role-specific tables
    super_admin: Mapped[Optional["SuperAdmin"]] = relationship(
        "SuperAdmin", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    hostel_admin: Mapped[Optional["HostelAdmin"]] = relationship(
        "HostelAdmin", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    tenant: Mapped[Optional["Tenant"]] = relationship(
        "Tenant", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    visitor: Mapped[Optional["Visitor"]] = relationship(
        "Visitor", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    
    # Common relationships
    refresh_tokens: Mapped[List["RefreshToken"]] = relationship(
        "RefreshToken", back_populates="user", cascade="all, delete-orphan"
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
        Index("idx_users_role", "role"),
    )

    @property
    def profile(self):
        """Get role-specific profile."""
        if self.role == UserRole.SUPER_ADMIN:
            return self.super_admin
        elif self.role == UserRole.HOSTEL_ADMIN:
            return self.hostel_admin
        elif self.role == UserRole.TENANT:
            return self.tenant
        elif self.role == UserRole.VISITOR:
            return self.visitor
        return None
    
    @property
    def hostel_id(self) -> Optional[int]:
        """Get primary hostel_id - backward compatibility."""
        profile = self.profile
        if profile and hasattr(profile, 'primary_hostel_id'):
            return profile.primary_hostel_id
        elif profile and hasattr(profile, 'hostel_id'):
            return profile.hostel_id
        return None

    def get_hostel_ids(self) -> List[int]:
        """Get list of hostel IDs this user has access to."""
        if self.role == UserRole.SUPER_ADMIN:
            return []  # Super admin has access to all
        elif self.role == UserRole.HOSTEL_ADMIN and self.hostel_admin:
            return [h.id for h in self.hostel_admin.hostels]
        elif self.role == UserRole.TENANT and self.tenant:
            return [self.tenant.hostel_id]
        elif self.role == UserRole.VISITOR and self.visitor:
            return [self.visitor.hostel_id]
        return []

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"


# ===== SUPER ADMIN TABLE =====

class SuperAdmin(Base, TimestampMixin):
    """Super Admin specific data."""
    
    __tablename__ = "super_admins"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), 
        unique=True, 
        nullable=False
    )
    
    # Super admin specific fields
    permissions: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="super_admin")
    
    __table_args__ = (
        Index("idx_super_admins_user_id", "user_id"),
    )


# ===== HOSTEL ADMIN TABLE =====

class HostelAdmin(Base, TimestampMixin):
    """Hostel Admin specific data."""
    
    __tablename__ = "hostel_admins"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), 
        unique=True, 
        nullable=False
    )
    
    # Admin code for registering new hostels
    admin_code: Mapped[Optional[str]] = mapped_column(
        String(50), unique=True, nullable=True,
        comment="Unique code for registering new hostels"
    )
    
    # Primary hostel (for backward compatibility)
    primary_hostel_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("hostels.id"), nullable=True
    )
    
    # Hostel admin specific fields
    department: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="hostel_admin")
    
    # Many-to-many with hostels
    hostels: Mapped[List["Hostel"]] = relationship(
        "Hostel",
        secondary=user_hostel_association,
        back_populates="admins"
    )
    
    __table_args__ = (
        Index("idx_hostel_admins_user_id", "user_id"),
        Index("idx_hostel_admins_admin_code", "admin_code"),
    )


# ===== TENANT TABLE =====

class Tenant(Base, TimestampMixin, SoftDeleteMixin):
    """
    Tenant data - replaces TenantProfile.
    
    This table stores all tenant-specific information including
    personal details, documents, and hostel assignment.
    """
    
    __tablename__ = "tenants"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), 
        unique=True, 
        nullable=False
    )
    hostel_id: Mapped[int] = mapped_column(ForeignKey("hostels.id"), nullable=False)
    
    # Personal Information
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    date_of_birth: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    gender: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    # Identity Documents
    id_proof_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    id_proof_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    id_proof_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Guardian Information
    guardian_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    guardian_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    guardian_email: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    emergency_contact: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    # Bed Assignment
    current_bed_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("beds.id", use_alter=True, name="fk_tenant_current_bed"), 
        nullable=True
    )
    check_in_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    check_out_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="tenant")
    hostel: Mapped["Hostel"] = relationship("Hostel", back_populates="tenants")
    
    current_bed: Mapped[Optional["Bed"]] = relationship(
        "Bed",
        foreign_keys=[current_bed_id],
        uselist=False,
        overlaps="tenant,occupied_bed"
    )
    
    occupied_bed: Mapped[Optional["Bed"]] = relationship(
        "Bed",
        foreign_keys="Bed.tenant_id",
        back_populates="tenant",
        uselist=False,
        overlaps="current_bed"
    )
    
    # Financial relationships
    invoices: Mapped[List["Invoice"]] = relationship(
        "Invoice",
        back_populates="tenant",
        foreign_keys="Invoice.tenant_id",
        cascade="all, delete-orphan"
    )
    
    payments: Mapped[List["Payment"]] = relationship(
        "Payment",
        back_populates="tenant",
        foreign_keys="Payment.tenant_id",
        cascade="all, delete-orphan"
    )
    
    # Check-in/out records
    check_in_outs: Mapped[List["CheckInOut"]] = relationship(
        "CheckInOut",
        back_populates="tenant",
        cascade="all, delete-orphan"
    )
    
    # Complaints
    complaints: Mapped[List["Complaint"]] = relationship(
        "Complaint",
        back_populates="tenant",
        foreign_keys="Complaint.tenant_id",
        cascade="all, delete-orphan"
    )
    
    # Leave applications
    leave_applications: Mapped[List["LeaveApplication"]] = relationship(
        "LeaveApplication",
        back_populates="tenant",
        foreign_keys="LeaveApplication.tenant_id",
        cascade="all, delete-orphan"
    )
    
    __table_args__ = (
        Index("idx_tenants_user_id", "user_id"),
        Index("idx_tenants_hostel_id", "hostel_id"),
    )


# ===== VISITOR TABLE =====

class Visitor(Base, TimestampMixin):
    """Visitor specific data."""
    
    __tablename__ = "visitors"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), 
        unique=True, 
        nullable=False
    )
    hostel_id: Mapped[int] = mapped_column(ForeignKey("hostels.id"), nullable=False)
    
    # Visitor-specific fields
    visitor_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
        comment="Expiration time for visitor account"
    )
    
    full_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    purpose: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Who created/approved this visitor
    created_by_admin_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="visitor")
    hostel: Mapped["Hostel"] = relationship("Hostel")
    created_by: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[created_by_admin_id]
    )
    
    __table_args__ = (
        Index("idx_visitors_user_id", "user_id"),
        Index("idx_visitors_hostel_id", "hostel_id"),
        Index("idx_visitors_expires_at", "visitor_expires_at"),
    )
    
    def is_expired(self) -> bool:
        """Check if visitor account has expired."""
        if not self.visitor_expires_at:
            return False
        return datetime.utcnow() > self.visitor_expires_at


# ===== REFRESH TOKEN (unchanged) =====

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


# ===== OTP CODE (unchanged) =====

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