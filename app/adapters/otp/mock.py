"""Mock OTP provider."""

from app.adapters.otp.base import OTPProvider
from app.logging_config import get_logger

logger = get_logger(__name__)


class MockOTPProvider(OTPProvider):
    """Mock OTP provider for development."""

    async def send_otp(self, phone: str, otp: str) -> bool:
        """Mock send OTP."""
        logger.info(f"[MOCK OTP] Sending OTP to {phone}: {otp}")
        # In development, just log the OTP
        print(f"\n{'='*50}\nOTP for {phone}: {otp}\n{'='*50}\n")
        return True