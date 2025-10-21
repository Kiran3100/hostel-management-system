"""Razorpay payment provider."""

from typing import Dict, Any, Optional
from decimal import Decimal
import razorpay

from app.config import settings
from app.adapters.payment.base import PaymentProvider


class RazorpayProvider(PaymentProvider):
    """Razorpay payment provider."""

    def __init__(self):
        self.client = razorpay.Client(
            auth=(settings.razorpay_key_id, settings.razorpay_key_secret)
        )

    async def create_order(
        self,
        amount: Decimal,
        currency: str,
        order_id: str,
        customer_info: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Create Razorpay order."""
        # Razorpay amounts are in smallest currency unit (paise for INR)
        amount_paise = int(amount * 100)

        order_data = {
            "amount": amount_paise,
            "currency": currency,
            "receipt": order_id,
            "notes": customer_info,
        }

        order = self.client.order.create(data=order_data)

        return {
            "order_id": order["id"],
            "amount": float(amount),
            "currency": currency,
            "payment_url": f"https://razorpay.com/checkout/{order['id']}",
            "metadata": order,
        }

    async def verify_payment(
        self, payment_id: str, signature: Optional[str] = None
    ) -> Dict[str, Any]:
        """Verify Razorpay payment."""
        payment = self.client.payment.fetch(payment_id)

        status_map = {
            "captured": "success",
            "authorized": "success",
            "failed": "failed",
            "created": "pending",
        }

        return {
            "status": status_map.get(payment["status"], "pending"),
            "transaction_id": payment["id"],
            "amount": Decimal(str(payment["amount"] / 100)),  # Convert paise to rupees
            "metadata": payment,
        }

    async def refund_payment(
        self, payment_id: str, amount: Optional[Decimal] = None
    ) -> Dict[str, Any]:
        """Refund Razorpay payment."""
        refund_data = {}
        if amount:
            refund_data["amount"] = int(amount * 100)

        refund = self.client.payment.refund(payment_id, refund_data)

        return {
            "status": "success" if refund["status"] == "processed" else "pending",
            "refund_id": refund["id"],
            "amount": float(Decimal(str(refund["amount"] / 100))),
        }