"""Notification provider base interface."""

from abc import ABC, abstractmethod
from typing import List, Optional


class NotificationProvider(ABC):
    """Abstract notification provider interface."""

    @abstractmethod
    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        html: Optional[str] = None,
    ) -> bool:
        """Send email notification."""
        pass

    @abstractmethod
    async def send_sms(self, to: str, message: str) -> bool:
        """Send SMS notification."""
        pass

    @abstractmethod
    async def send_push(
        self,
        tokens: List[str],
        title: str,
        message: str,
        data: Optional[dict] = None,
    ) -> bool:
        """Send push notification."""
        pass