"""Mess menu models."""

from datetime import date
from enum import Enum as PyEnum

from sqlalchemy import ForeignKey, Date, Enum, Index, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin


class MealType(str, PyEnum):
    """Meal types."""

    BREAKFAST = "BREAKFAST"
    LUNCH = "LUNCH"
    SNACKS = "SNACKS"
    DINNER = "DINNER"


class MessMenu(Base, TimestampMixin):
    """Mess menu model."""

    __tablename__ = "mess_menus"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    hostel_id: Mapped[int] = mapped_column(ForeignKey("hostels.id"), nullable=False)
    
    date: Mapped[Date] = mapped_column(Date, nullable=False)
    meal_type: Mapped[MealType] = mapped_column(
        Enum(MealType, name="meal_type_enum"), nullable=False
    )
    items: Mapped[dict] = mapped_column(JSON, nullable=False)  # {"items": ["Rice", "Dal", ...]}
    
    # Relationships
    hostel: Mapped["Hostel"] = relationship("Hostel", back_populates="mess_menus")

    __table_args__ = (
        Index("idx_mess_menus_hostel_id", "hostel_id"),
        Index("idx_mess_menus_date", "date"),
        Index("idx_mess_menus_hostel_date_meal", "hostel_id", "date", "meal_type", unique=True),
    )