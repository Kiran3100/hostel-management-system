import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.database import AsyncSessionLocal
from app.models.notification import Notification, NotificationType
from app.models.user import User
from sqlalchemy import select


async def create_test_notification():
    """Create test notification for debugging."""
    async with AsyncSessionLocal() as db:
        # Get tenant user
        result = await db.execute(
            select(User).where(User.email == "tenant@demo.com")
        )
        user = result.scalar_one_or_none()
        
        if not user:
            print("❌ User not found!")
            return
        
        print(f"✅ Found user: {user.email} (ID: {user.id})")
        
        # Create test notification
        notification = Notification(
            user_id=user.id,
            hostel_id=user.primary_hostel_id,
            title="Test Notification",
            message="This is a test notification to verify the system is working!",
            notification_type=NotificationType.INFO,
            is_read=False
        )
        
        db.add(notification)
        await db.commit()
        await db.refresh(notification)
        
        print(f"✅ Created notification ID: {notification.id}")
        print(f"\nNow test in Swagger:")
        print(f"1. Login as tenant@demo.com")
        print(f"2. GET /api/v1/notifications")
        print(f"3. You should see the test notification!")
        
        return notification


if __name__ == "__main__":
    asyncio.run(create_test_notification())