"""Subscription service."""

from datetime import date
from typing import Dict

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.hostel import Subscription, Plan, PlanTier
from app.models.room import Room, Bed
from app.models.tenant import TenantProfile
from app.repositories.subscription import SubscriptionRepository, PlanRepository
from app.repositories.room import RoomRepository, BedRepository
from app.repositories.tenant import TenantRepository
from app.exceptions import NotFoundError, SubscriptionLimitError


class SubscriptionService:
    """Subscription service."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.subscription_repo = SubscriptionRepository(Subscription, db)
        self.plan_repo = PlanRepository(Plan, db)
        # FIX: Pass the actual model classes, not None
        self.room_repo = RoomRepository(Room, db)
        self.bed_repo = BedRepository(Bed, db)
        self.tenant_repo = TenantRepository(TenantProfile, db)
        
        
    async def check_room_limit(self, hostel_id: int) -> bool:
        """Check if hostel can add more rooms."""
        subscription = await self.subscription_repo.get_by_hostel(hostel_id)
        
        # ✅ AUTO-CREATE FREE SUBSCRIPTION IF MISSING
        if not subscription:
            # Get FREE plan
            free_plan = await self.plan_repo.get_by_tier(PlanTier.FREE)
            if free_plan:
                # Create default subscription
                from app.models.hostel import SubscriptionStatus
                from datetime import date, timedelta
                
                subscription_data = {
                    "hostel_id": hostel_id,
                    "plan_id": free_plan.id,
                    "status": SubscriptionStatus.TRIAL,
                    "start_date": date.today(),
                    "end_date": date.today() + timedelta(days=365),
                    "auto_renew": False,
                }
                subscription = await self.subscription_repo.create(subscription_data)
                await self.db.commit()
            else:
                # No FREE plan exists, allow anyway
                return True

        plan = await self.plan_repo.get(subscription.plan_id)
        if not plan:
            raise NotFoundError("Plan not found")

        # Unlimited rooms
        if plan.max_rooms_per_hostel is None:
            return True

        # Count current rooms (excluding soft-deleted ones)
        current_count = await self.room_repo.count({
            "hostel_id": hostel_id,
            "is_deleted": False
        })

        if current_count >= plan.max_rooms_per_hostel:
            raise SubscriptionLimitError(
                f"Room limit reached. Maximum {plan.max_rooms_per_hostel} rooms allowed on {plan.name} plan."
            )

        return True

    async def check_tenant_limit(self, hostel_id: int) -> bool:
        """Check if hostel can add more tenants."""
        subscription = await self.subscription_repo.get_by_hostel(hostel_id)
        if not subscription:
            raise NotFoundError("No active subscription")

        plan = await self.plan_repo.get(subscription.plan_id)
        if not plan:
            raise NotFoundError("Plan not found")

        # Unlimited tenants
        if plan.max_tenants_per_hostel is None:
            return True

        # Count current tenants
        current_count = await self.tenant_repo.count_by_hostel(hostel_id)

        if current_count >= plan.max_tenants_per_hostel:
            raise SubscriptionLimitError(
                f"Tenant limit reached. Maximum {plan.max_tenants_per_hostel} tenants allowed on {plan.name} plan."
            )

        return True

    async def check_room_limit(self, hostel_id: int) -> bool:
        """Check if hostel can add more rooms."""
        subscription = await self.subscription_repo.get_by_hostel(hostel_id)
        if not subscription:
            raise NotFoundError("No active subscription")

        plan = await self.plan_repo.get(subscription.plan_id)
        if not plan:
            raise NotFoundError("Plan not found")

        # Unlimited rooms
        if plan.max_rooms_per_hostel is None:
            return True

        # Count current rooms (excluding soft-deleted ones)
        current_count = await self.room_repo.count({
            "hostel_id": hostel_id,
            "is_deleted": False
        })

        if current_count >= plan.max_rooms_per_hostel:
            raise SubscriptionLimitError(
                f"Room limit reached. Maximum {plan.max_rooms_per_hostel} rooms allowed on {plan.name} plan."
            )

        return True

    async def get_feature_usage(self, hostel_id: int) -> Dict:
        """Get feature usage statistics."""
        subscription = await self.subscription_repo.get_by_hostel(hostel_id)
        if not subscription:
            raise NotFoundError("No active subscription")

        plan = await self.plan_repo.get(subscription.plan_id)
        if not plan:
            raise NotFoundError("Plan not found")

        # Count current usage
        current_tenants = await self.tenant_repo.count_by_hostel(hostel_id)
        current_rooms = await self.room_repo.count({
            "hostel_id": hostel_id,
            "is_deleted": False
        })

        # Calculate percentages
        usage_percentage = {}

        if plan.max_tenants_per_hostel:
            usage_percentage["tenants"] = (current_tenants / plan.max_tenants_per_hostel) * 100
        else:
            usage_percentage["tenants"] = 0

        if plan.max_rooms_per_hostel:
            usage_percentage["rooms"] = (current_rooms / plan.max_rooms_per_hostel) * 100
        else:
            usage_percentage["rooms"] = 0

        return {
            "hostel_id": hostel_id,
            "plan_name": plan.name,
            "current_tenants": current_tenants,
            "max_tenants": plan.max_tenants_per_hostel,
            "current_rooms": current_rooms,
            "max_rooms": plan.max_rooms_per_hostel,
            "usage_percentage": usage_percentage,
        }

    async def create_subscription(
        self,
        hostel_id: int,
        plan_id: int,
        start_date: date,
        end_date: date = None,
        auto_renew: bool = False,
    ) -> Subscription:
        """Create a new subscription."""
        # Check if subscription already exists
        existing = await self.subscription_repo.get_by_hostel(hostel_id)
        if existing:
            # Update existing
            update_data = {
                "plan_id": plan_id,
                "start_date": start_date,
                "end_date": end_date,
                "auto_renew": auto_renew,
            }
            subscription = await self.subscription_repo.update(existing.id, update_data)
        else:
            # Create new
            from app.models.hostel import SubscriptionStatus

            subscription_data = {
                "hostel_id": hostel_id,
                "plan_id": plan_id,
                "status": SubscriptionStatus.ACTIVE,
                "start_date": start_date,
                "end_date": end_date,
                "auto_renew": auto_renew,
            }
            subscription = await self.subscription_repo.create(subscription_data)

        await self.db.commit()
        return subscription