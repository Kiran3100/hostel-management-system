"""Payment provider base interface."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from decimal import Decimal


class PaymentProvider(ABC):
    """Abstract payment provider interface."""

    @abstractmethod
    async def create_order(
        self,
        amount: Decimal,
        currency: str,
        order_id: str,
        customer_info: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Create a payment order.
        
        Returns:
            {
                "order_id": "provider_order_id",
                "amount": amount,
                "currency": currency,
                "payment_url": "https://...",
                "metadata": {...}
            }
        """
        pass

    @abstractmethod
    async def verify_payment(
        self, payment_id: str, signature: Optional[str] = None
    ) -> Dict[str, Any]:
        """Verify payment status.
        
        Returns:
            {
                "status": "success" | "failed" | "pending",
                "transaction_id": "...",
                "amount": Decimal,
                "metadata": {...}
            }
        """
        pass

    @abstractmethod
    async def refund_payment(
        self, payment_id: str, amount: Optional[Decimal] = None
    ) -> Dict[str, Any]:
        """Refund a payment (full or partial)."""
        pass