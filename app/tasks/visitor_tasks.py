"""Background tasks for visitor management."""

import asyncio
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.services.visitor import VisitorService
from app.logging_config import get_logger

logger = get_logger(__name__)


async def cleanup_expired_visitors_task():
    """
    Background task to cleanup expired visitor accounts.
    
    This task should be scheduled to run periodically (e.g., daily).
    It deactivates all visitor accounts that have passed their expiration date.
    """
    logger.info("Starting visitor cleanup task...")
    
    async with AsyncSessionLocal() as db:
        try:
            visitor_service = VisitorService(db)
            deactivated_count = await visitor_service.cleanup_expired_visitors()
            
            logger.info(
                f"Visitor cleanup completed. Deactivated {deactivated_count} expired accounts."
            )
            
            return {
                "success": True,
                "deactivated_count": deactivated_count,
                "timestamp": datetime.utcnow().isoformat(),
            }
            
        except Exception as e:
            logger.error(f"Error during visitor cleanup: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }


async def notify_expiring_visitors_task(days_before: int = 7):
    """
    Background task to notify visitors whose accounts are expiring soon.
    
    Args:
        days_before: Number of days before expiration to send notification
    """
    logger.info(f"Starting notification task for visitors expiring in {days_before} days...")
    
    async with AsyncSessionLocal() as db:
        try:
            from datetime import timedelta
            from sqlalchemy import select
            from app.models.user import User, UserRole
            from app.services.notification import NotificationService
            
            # Get visitors expiring soon
            expiring_date = datetime.utcnow() + timedelta(days=days_before)
            
            result = await db.execute(
                select(User).where(
                    User.role == UserRole.VISITOR,
                    User.is_active == True,
                    User.visitor_expires_at <= expiring_date,
                    User.visitor_expires_at > datetime.utcnow(),
                )
            )
            
            expiring_visitors = result.scalars().all()
            
            # Send notifications
            notification_service = NotificationService(db)
            sent_count = 0
            
            for visitor in expiring_visitors:
                try:
                    await notification_service.send_notification(
                        user_id=visitor.id,
                        title="Visitor Account Expiring Soon",
                        message=(
                            f"Your visitor account will expire on "
                            f"{visitor.visitor_expires_at.strftime('%Y-%m-%d %H:%M')}. "
                            f"Please contact the administrator if you need extended access."
                        ),
                        notification_type="WARNING",
                    )
                    sent_count += 1
                except Exception as e:
                    logger.error(
                        f"Failed to send notification to visitor {visitor.id}: {str(e)}"
                    )
            
            await db.commit()
            
            logger.info(
                f"Expiration notification task completed. "
                f"Sent {sent_count} notifications to {len(expiring_visitors)} visitors."
            )
            
            return {
                "success": True,
                "visitors_count": len(expiring_visitors),
                "notifications_sent": sent_count,
                "timestamp": datetime.utcnow().isoformat(),
            }
            
        except Exception as e:
            logger.error(f"Error during expiration notification: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }


# ===== SCHEDULER INTEGRATION =====

def schedule_visitor_tasks():
    """
    Schedule visitor management tasks.
    
    This should be called during application startup.
    Requires APScheduler or similar task scheduler.
    """
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.cron import CronTrigger
    
    scheduler = AsyncIOScheduler()
    
    # Cleanup expired visitors daily at 2 AM
    scheduler.add_job(
        cleanup_expired_visitors_task,
        trigger=CronTrigger(hour=2, minute=0),
        id="visitor_cleanup",
        name="Cleanup expired visitor accounts",
        replace_existing=True,
    )
    
    # Notify expiring visitors daily at 9 AM
    scheduler.add_job(
        notify_expiring_visitors_task,
        trigger=CronTrigger(hour=9, minute=0),
        id="visitor_expiry_notification",
        name="Notify visitors about expiring accounts",
        replace_existing=True,
        kwargs={"days_before": 7},
    )
    
    scheduler.start()
    logger.info("Visitor management tasks scheduled successfully")
    
    return scheduler


# ===== MANUAL EXECUTION =====

async def run_cleanup_now():
    """Run visitor cleanup immediately (for manual execution)."""
    return await cleanup_expired_visitors_task()


async def run_notification_now(days_before: int = 7):
    """Run expiration notification immediately (for manual execution)."""
    return await notify_expiring_visitors_task(days_before)


if __name__ == "__main__":
    # For testing purposes
    print("Running visitor cleanup...")
    result = asyncio.run(run_cleanup_now())
    print(f"Result: {result}")
    
    print("\nRunning expiration notifications...")
    result = asyncio.run(run_notification_now())
    print(f"Result: {result}")