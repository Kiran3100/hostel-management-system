"""OTP provider base interface."""

from abc import ABC, abstractmethod


class OTPProvider(ABC):
    """Abstract OTP provider interface."""

    @abstractmethod
    async def send_otp(self, phone: str, otp: str) -> bool:
        """Send OTP to phone number."""
        pass