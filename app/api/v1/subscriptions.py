"""Subscription endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.subscription import (
    PlanResponse,
    SubscriptionCreate,
    SubscriptionUpdate,
    SubscriptionResponse,
    SubscriptionWithPlan,
    FeatureUsageResponse,
)
from app.models.user import User, UserRole
from app.models.hostel import Plan, Subscription
from app.repositories.subscription import PlanRepository, SubscriptionRepository
from app.core.rbac import require_role, check_hostel_access
from app.api.deps import get_current_user
from app.services.subscription import SubscriptionService

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])


@router.get("/plans", response_model=List[PlanResponse])
async def list_plans(
    db: AsyncSession = Depends(get_db),
):
    """List all available subscription plans."""
    plan_repo = PlanRepository(Plan, db)
    plans = await plan_repo.get_active_plans()

    return plans


@router.get("", response_model=List[SubscriptionResponse])
async def list_subscriptions(
    hostel_id: int = None,
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """List subscriptions (Super Admin only)."""
    subscription_repo = SubscriptionRepository(Subscription, db)

    if hostel_id:
        subscription = await subscription_repo.get_by_hostel(hostel_id)
        return [subscription] if subscription else []
    else:
        subscriptions = await subscription_repo.get_multi()
        return subscriptions


@router.get("/{subscription_id}", response_model=SubscriptionWithPlan)
async def get_subscription(
    subscription_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get subscription details."""
    subscription_repo = SubscriptionRepository(Subscription, db)
    subscription = await subscription_repo.get(subscription_id)

    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")

    # Check access
    if current_user.role != UserRole.SUPER_ADMIN:
        check_hostel_access(current_user, subscription.hostel_id)

    # Get plan details
    plan_repo = PlanRepository(Plan, db)
    plan = await plan_repo.get(subscription.plan_id)

    from app.schemas.subscription import SubscriptionWithPlan

    return SubscriptionWithPlan(
        **subscription.__dict__,
        plan=PlanResponse(**plan.__dict__) if plan else None,
    )


@router.post("", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_subscription(
    request: SubscriptionCreate,
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """Create or update subscription (Super Admin only)."""
    subscription_service = SubscriptionService(db)

    subscription = await subscription_service.create_subscription(
        hostel_id=request.hostel_id,
        plan_id=request.plan_id,
        start_date=request.start_date,
        end_date=request.end_date,
        auto_renew=request.auto_renew,
    )

    return subscription


@router.patch("/{subscription_id}", response_model=SubscriptionResponse)
async def update_subscription(
    subscription_id: int,
    request: SubscriptionUpdate,
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """Update subscription (Super Admin only)."""
    subscription_repo = SubscriptionRepository(Subscription, db)

    subscription = await subscription_repo.get(subscription_id)
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")

    update_data = request.model_dump(exclude_unset=True)
    subscription = await subscription_repo.update(subscription_id, update_data)
    await db.commit()

    return subscription


@router.get("/{subscription_id}/usage", response_model=FeatureUsageResponse)
async def get_feature_usage(
    subscription_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get feature usage statistics."""
    subscription_repo = SubscriptionRepository(Subscription, db)
    subscription = await subscription_repo.get(subscription_id)

    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")

    # Check access
    if current_user.role != UserRole.SUPER_ADMIN:
        check_hostel_access(current_user, subscription.hostel_id)

    subscription_service = SubscriptionService(db)
    usage = await subscription_service.get_feature_usage(subscription.hostel_id)

    return FeatureUsageResponse(**usage)