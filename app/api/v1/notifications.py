from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone

from app.database import get_db
from app.schemas.notification import (
    NotificationResponse,
    DeviceTokenCreate,
    DeviceTokenResponse,
)
from app.schemas.common import MessageResponse
from app.models.user import User
from app.models.notification import Notification, DeviceToken
from app.repositories.notification import NotificationRepository, DeviceTokenRepository
from app.api.deps import get_current_user
from app.core.pagination import PaginationParams, PageResponse

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=PageResponse[NotificationResponse])
async def list_notifications(
    is_read: Optional[bool] = None,
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List user notifications.
    
    **Query Parameters:**
    - `is_read`: Filter by read status (true/false)
    - `page`: Page number (default: 1)
    - `page_size`: Items per page (default: 20)
    """
    notification_repo = NotificationRepository(Notification, db)

    notifications = await notification_repo.get_by_user(current_user.id, is_read=is_read)

    # Simple pagination
    start = pagination.offset
    end = start + pagination.limit
    paginated = notifications[start:end]

    return PageResponse.create(
        items=paginated,
        total=len(notifications),
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.get("/count", response_model=dict)
async def get_notification_count(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get notification counts (total, unread).
    
    **Returns:**
    - `total`: Total notification count
    - `unread`: Unread notification count
    """
    notification_repo = NotificationRepository(Notification, db)
    
    all_notifications = await notification_repo.get_by_user(current_user.id)
    unread_notifications = await notification_repo.get_by_user(current_user.id, is_read=False)
    
    return {
        "total": len(all_notifications),
        "unread": len(unread_notifications)
    }


@router.get("/{notification_id}", response_model=NotificationResponse)
async def get_notification(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific notification by ID."""
    notification_repo = NotificationRepository(Notification, db)
    notification = await notification_repo.get(notification_id)

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    if notification.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    return notification


@router.patch("/{notification_id}", response_model=NotificationResponse)
async def mark_notification_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark a notification as read."""
    notification_repo = NotificationRepository(Notification, db)
    notification = await notification_repo.get(notification_id)

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    if notification.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    notification = await notification_repo.update(
        notification_id,
        {"is_read": True, "read_at": datetime.now(timezone.utc)},
    )
    await db.commit()

    return notification


@router.post("/mark-all-read", response_model=MessageResponse)
async def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark all notifications as read for the current user."""
    notification_repo = NotificationRepository(Notification, db)
    await notification_repo.mark_all_read(current_user.id)
    await db.commit()

    return MessageResponse(message="All notifications marked as read")


@router.post("/device-tokens", response_model=DeviceTokenResponse, status_code=status.HTTP_201_CREATED)
async def register_device_token(
    request: DeviceTokenCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Register a device token for push notifications.
    
    **Platforms:**
    - `IOS` - iPhone/iPad devices
    - `ANDROID` - Android devices  
    - `WEB` - Web browsers
    
    **Note:** If token already exists, it will be updated for the current user.
    """
    device_repo = DeviceTokenRepository(DeviceToken, db)

    # Check if token already exists
    from sqlalchemy import select

    result = await db.execute(
        select(DeviceToken).where(DeviceToken.token == request.token)
    )
    existing = result.scalar_one_or_none()

    if existing:
        # Update existing token
        device = await device_repo.update(
            existing.id,
            {
                "user_id": current_user.id, 
                "platform": request.platform, 
                "is_active": True
            },
        )
    else:
        # Create new token
        device_data = {
            "user_id": current_user.id,
            "token": request.token,
            "platform": request.platform,
        }
        device = await device_repo.create(device_data)

    await db.commit()

    return device


@router.get("/device-tokens", response_model=List[DeviceTokenResponse])
async def list_device_tokens(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all device tokens registered for the current user."""
    device_repo = DeviceTokenRepository(DeviceToken, db)
    tokens = await device_repo.get_by_user(current_user.id)
    
    return tokens


@router.delete("/device-tokens/{token_id}", response_model=MessageResponse)
async def delete_device_token(
    token_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a device token (e.g., when user logs out from a device)."""
    device_repo = DeviceTokenRepository(DeviceToken, db)
    
    # Get token and verify ownership
    device = await device_repo.get(token_id)
    
    if not device:
        raise HTTPException(status_code=404, detail="Device token not found")
    
    if device.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Deactivate instead of deleting
    await device_repo.update(token_id, {"is_active": False})
    await db.commit()
    
    return MessageResponse(message="Device token deactivated successfully")
