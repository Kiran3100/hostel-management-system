"""Mess menu repository - COMPLETE & WORKING."""

from datetime import date
from typing import Optional, List
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

from app.models.mess import MessMenu, MealType
from app.repositories.base import BaseRepository


class MessMenuRepository(BaseRepository[MessMenu]):
    """Mess menu repository with all required methods."""

    async def get(self, id: int) -> Optional[MessMenu]:
        """Get menu by ID with hostel relationship."""
        result = await self.db.execute(
            select(MessMenu)
            .where(MessMenu.id == id)
            .options(selectinload(MessMenu.hostel))
        )
        return result.scalar_one_or_none()

    async def get_by_date(self, hostel_id: int, menu_date: date) -> List[MessMenu]:
        """Get all menus for a specific date."""
        result = await self.db.execute(
            select(MessMenu)
            .where(
                and_(
                    MessMenu.hostel_id == hostel_id,
                    MessMenu.date == menu_date
                )
            )
            .options(selectinload(MessMenu.hostel))
            .order_by(MessMenu.meal_type)
        )
        return list(result.scalars().all())

    async def get_by_date_range(
        self, 
        hostel_id: int, 
        date_from: date, 
        date_to: date
    ) -> List[MessMenu]:
        """Get menus for a date range."""
        result = await self.db.execute(
            select(MessMenu)
            .where(
                and_(
                    MessMenu.hostel_id == hostel_id,
                    MessMenu.date >= date_from,
                    MessMenu.date <= date_to
                )
            )
            .options(selectinload(MessMenu.hostel))
            .order_by(MessMenu.date, MessMenu.meal_type)
        )
        return list(result.scalars().all())

    async def get_by_date_and_meal(
        self, 
        hostel_id: int, 
        menu_date: date, 
        meal_type: MealType
    ) -> Optional[MessMenu]:
        """Get specific menu by date and meal type."""
        result = await self.db.execute(
            select(MessMenu)
            .where(
                and_(
                    MessMenu.hostel_id == hostel_id,
                    MessMenu.date == menu_date,
                    MessMenu.meal_type == meal_type
                )
            )
            .options(selectinload(MessMenu.hostel))
        )
        return result.scalar_one_or_none()