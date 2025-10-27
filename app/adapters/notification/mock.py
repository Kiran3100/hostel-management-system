"""Mock notification provider."""

from typing import List, Optional

from app.adapters.notification.base import NotificationProvider
from app.logging_config import get_logger

logger = get_logger(__name__)


class MockNotificationProvider(NotificationProvider):
    """Mock notification provider for development."""

    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        html: Optional[str] = None,
    ) -> bool:
        """Mock send email."""
        logger.info(f"[MOCK EMAIL] To: {to}, Subject: {subject}")
        logger.debug(f"[MOCK EMAIL] Body: {body}")
        return True

    async def send_sms(self, to: str, message: str) -> bool:
        """Mock send SMS."""
        logger.info(f"[MOCK SMS] To: {to}, Message: {message}")
        return True

    async def send_push(
        self,
        tokens: List[str],
        title: str,
        message: str,
        data: Optional[dict] = None,
    ) -> bool:
        """Mock send push notification."""
        logger.info(f"[MOCK PUSH] To {len(tokens)} devices, Title: {title}")
        logger.debug(f"[MOCK PUSH] Message: {message}, Data: {data}")
        return True