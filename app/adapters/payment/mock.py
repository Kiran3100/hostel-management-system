"""Mock payment provider for testing."""

import asyncio
from typing import Dict, Any, Optional
from decimal import Decimal
import secrets

from app.adapters.payment.base import PaymentProvider


class MockPaymentProvider(PaymentProvider):
    """Mock payment provider for development/testing."""

    async def create_order(
        self,
        amount: Decimal,
        currency: str,
        order_id: str,
        customer_info: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Create mock payment order."""
        mock_order_id = f"mock_order_{secrets.token_hex(8)}"

        return {
            "order_id": mock_order_id,
            "amount": float(amount),
            "currency": currency,
            "payment_url": f"https://mock-payment-gateway.local/pay/{mock_order_id}",
            "metadata": {
                "customer": customer_info,
                "internal_order_id": order_id,
            },
        }

    async def verify_payment(
        self, payment_id: str, signature: Optional[str] = None
    ) -> Dict[str, Any]:
        """Verify mock payment (always succeeds after 1 second)."""
        await asyncio.sleep(1)  # Simulate processing

        return {
            "status": "success",
            "transaction_id": f"mock_txn_{secrets.token_hex(8)}",
            "amount": Decimal("1000.00"),  # Mock amount
            "metadata": {
                "payment_method": "mock_card",
                "card_last4": "4242",
            },
        }

    async def refund_payment(
        self, payment_id: str, amount: Optional[Decimal] = None
    ) -> Dict[str, Any]:
        """Refund mock payment."""
        return {
            "status": "success",
            "refund_id": f"mock_refund_{secrets.token_hex(8)}",
            "amount": float(amount) if amount else 0,
        }