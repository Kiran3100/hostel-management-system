"""Subscription repository."""

from typing import Optional
from sqlalchemy import select

from app.models.hostel import Subscription, Plan, PlanTier
from app.repositories.base import BaseRepository


class SubscriptionRepository(BaseRepository[Subscription]):
    """Subscription repository."""

    async def get_by_hostel(self, hostel_id: int) -> Optional[Subscription]:
        """Get subscription by hostel ID."""
        result = await self.db.execute(
            select(Subscription).where(Subscription.hostel_id == hostel_id)
        )
        return result.scalar_one_or_none()


class PlanRepository(BaseRepository[Plan]):
    """Plan repository."""

    async def get_by_tier(self, tier: PlanTier) -> Optional[Plan]:
        """Get plan by tier."""
        result = await self.db.execute(select(Plan).where(Plan.tier == tier))
        return result.scalar_one_or_none()

    async def get_active_plans(self) -> list[Plan]:
        """Get all active plans."""
        result = await self.db.execute(select(Plan).where(Plan.is_active == True))
        return list(result.scalars().all())