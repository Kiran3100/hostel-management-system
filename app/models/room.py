"""Room and bed models."""

from enum import Enum as PyEnum
from typing import Optional, List

from sqlalchemy import String, Integer, Boolean, ForeignKey, Enum, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, SoftDeleteMixin


class RoomType(str, PyEnum):
    """Room types."""

    SINGLE = "SINGLE"
    DOUBLE = "DOUBLE"
    TRIPLE = "TRIPLE"
    DORMITORY = "DORMITORY"


class Room(Base, TimestampMixin, SoftDeleteMixin):
    """Room model."""

    __tablename__ = "rooms"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    hostel_id: Mapped[int] = mapped_column(ForeignKey("hostels.id"), nullable=False)
    
    number: Mapped[str] = mapped_column(String(50), nullable=False)
    floor: Mapped[int] = mapped_column(Integer, nullable=False)
    room_type: Mapped[RoomType] = mapped_column(Enum(RoomType), nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Relationships
    hostel: Mapped["Hostel"] = relationship("Hostel", back_populates="rooms")
    beds: Mapped[List["Bed"]] = relationship(
        "Bed", back_populates="room", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_rooms_hostel_id", "hostel_id"),
        Index("idx_rooms_hostel_number", "hostel_id", "number", unique=True),
    )


class Bed(Base, TimestampMixin, SoftDeleteMixin):
    """Bed model."""

    __tablename__ = "beds"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    room_id: Mapped[int] = mapped_column(ForeignKey("rooms.id"), nullable=False)
    hostel_id: Mapped[int] = mapped_column(ForeignKey("hostels.id"), nullable=False)
    
    number: Mapped[str] = mapped_column(String(10), nullable=False)
    is_occupied: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Only Bed has the foreign key to tenant
    tenant_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("tenant_profiles.id"), nullable=True
    )
    
    # Relationships
    room: Mapped["Room"] = relationship("Room", back_populates="beds")
    
    # One-to-one relationship with tenant (bed can have one tenant)
    tenant: Mapped[Optional["TenantProfile"]] = relationship(
        "TenantProfile", 
        back_populates="current_bed",
        foreign_keys=[tenant_id],
        uselist=False  # This makes it one-to-one
    )
    
    check_in_outs: Mapped[List["CheckInOut"]] = relationship("CheckInOut", back_populates="bed")

    __table_args__ = (
        Index("idx_beds_room_id", "room_id"),
        Index("idx_beds_hostel_id", "hostel_id"),
        Index("idx_beds_tenant_id", "tenant_id"),
    )