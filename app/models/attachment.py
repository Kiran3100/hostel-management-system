"""File attachment models."""

from typing import Optional

from sqlalchemy import String, Integer, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin


class Attachment(Base, TimestampMixin):
    """File attachment model."""

    __tablename__ = "attachments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    hostel_id: Mapped[Optional[int]] = mapped_column(ForeignKey("hostels.id"), nullable=True)
    uploaded_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[int] = mapped_column(nullable=False)
    
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)  # bytes
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Relationships
    uploader: Mapped["User"] = relationship("User")

    __table_args__ = (
        Index("idx_attachments_hostel_id", "hostel_id"),
        Index("idx_attachments_entity", "entity_type", "entity_id"),
        Index("idx_attachments_uploaded_by", "uploaded_by"),
    )