"""Audit log models."""

from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import String, Text, ForeignKey, Enum, Index, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin


class AuditAction(str, PyEnum):
    """Audit actions."""

    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    PAYMENT = "PAYMENT"


class AuditLog(Base, TimestampMixin):
    """Audit log model."""

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    hostel_id: Mapped[Optional[int]] = mapped_column(ForeignKey("hostels.id"), nullable=True)
    
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[Optional[int]] = mapped_column(nullable=True)
    action: Mapped[AuditAction] = mapped_column(Enum(AuditAction), nullable=False)
    
    old_values: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    new_values: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    user: Mapped[Optional["User"]] = relationship(
        "User", back_populates="audit_logs", foreign_keys=[user_id]
    )

    __table_args__ = (
        Index("idx_audit_logs_user_id", "user_id"),
        Index("idx_audit_logs_hostel_id", "hostel_id"),
        Index("idx_audit_logs_entity", "entity_type", "entity_id"),
        Index("idx_audit_logs_created_at", "created_at"),
    )