"""Payment service (SYNC VERSION)."""

from decimal import Decimal
from datetime import datetime, date
import secrets
import json

from sqlalchemy.orm import Session

from app.models.fee import Invoice, Payment, InvoiceStatus, PaymentStatus
from app.repositories.payment import InvoiceRepository, PaymentRepository
from app.repositories.tenant import TenantRepository
from app.adapters.payment.base import PaymentProvider
from app.core.security import generate_idempotency_key
from app.exceptions import NotFoundError, PaymentError, ValidationError
from app.config import settings


class PaymentService:
    """Payment service."""

    def __init__(self, db: Session, payment_provider: PaymentProvider):
        self.db = db
        self.invoice_repo = InvoiceRepository(Invoice, db)
        self.payment_repo = PaymentRepository(Payment, db)
        self.tenant_repo = TenantRepository(None, db)
        self.payment_provider = payment_provider

    def generate_invoice(
        self,
        hostel_id: int,
        tenant_id: int,
        amount: Decimal,
        due_date: date,
        fee_schedule_id: int = None,
        notes: str = None,
    ) -> Invoice:
        """Generate an invoice for a tenant."""
        # Verify tenant exists
        tenant = self.tenant_repo.get(tenant_id)
        if not tenant or tenant.hostel_id != hostel_id:
            raise NotFoundError("Tenant not found")

        # NO TAX - total_amount equals amount
        total_amount = amount

        # Generate invoice number
        invoice_number = f"INV-{hostel_id}-{datetime.utcnow().strftime('%Y%m%d')}-{secrets.token_hex(4).upper()}"

        invoice_data = {
            "hostel_id": hostel_id,
            "tenant_id": tenant_id,
            "fee_schedule_id": fee_schedule_id,
            "invoice_number": invoice_number,
            "amount": amount,
            "due_date": due_date,
            "status": InvoiceStatus.PENDING,
        }

        if notes:
            invoice_data["notes"] = notes

        invoice = self.invoice_repo.create(invoice_data)
        self.db.commit()

        return invoice

    def initiate_payment(
        self,
        invoice_id: int,
        tenant_id: int,
        amount: Decimal,
        gateway: str = "razorpay",
    ) -> Payment:
        """Initiate a payment for an invoice."""
        # Get invoice
        invoice = self.invoice_repo.get(invoice_id)
        if not invoice:
            raise NotFoundError("Invoice not found")

        # Verify tenant
        if invoice.tenant_id != tenant_id:
            raise ValidationError("Invoice does not belong to this tenant")

        # Verify amount
        if amount <= 0 or amount > invoice.amount:
            raise ValidationError("Invalid payment amount")

        # Check for existing payment with same idempotency
        idempotency_key = generate_idempotency_key()

        # Create payment record
        payment_data = {
            "invoice_id": invoice_id,
            "hostel_id": invoice.hostel_id,
            "tenant_id": tenant_id,
            "amount": amount,
            "status": PaymentStatus.PENDING,
            "gateway": gateway,
            "idempotency_key": idempotency_key,
        }

        payment = self.payment_repo.create(payment_data)
        self.db.commit()

        # Create payment order with provider
        try:
            tenant = self.tenant_repo.get(tenant_id)
            customer_info = {
                "name": tenant.full_name,
                "phone": tenant.user.phone if tenant.user else "",
                "email": tenant.user.email if tenant.user else "",
            }

            order = self.payment_provider.create_order(
                amount=amount,
                currency=settings.payment_currency,
                order_id=str(payment.id),
                customer_info=customer_info,
            )

            # Update payment with provider order ID
            # CHANGED: metadata -> payment_metadata
            self.payment_repo.update(
                payment.id,
                {
                    "transaction_id": order["order_id"],
                    "status": PaymentStatus.PROCESSING,
                    "payment_metadata": json.dumps(order.get("metadata", {})),
                },
            )
            self.db.commit()

            payment.transaction_id = order["order_id"]

        except Exception as e:
            # Mark payment as failed
            self.payment_repo.update(
                payment.id,
                {"status": PaymentStatus.FAILED, "error_message": str(e)},
            )
            self.db.commit()
            raise PaymentError(f"Failed to initiate payment: {str(e)}")

        return payment

    def confirm_payment(self, payment_id: int, transaction_id: str) -> Payment:
        """Confirm payment after successful transaction."""
        payment = self.payment_repo.get(payment_id)
        if not payment:
            raise NotFoundError("Payment not found")

        # Verify payment with provider
        try:
            verification = self.payment_provider.verify_payment(transaction_id)

            if verification["status"] == "success":
                # Update payment
                receipt_number = f"RCP-{payment.hostel_id}-{datetime.utcnow().strftime('%Y%m%d')}-{secrets.token_hex(4).upper()}"

                self.payment_repo.update(
                    payment_id,
                    {
                        "status": PaymentStatus.SUCCESS,
                        "paid_at": datetime.utcnow(),
                        "receipt_number": receipt_number,
                        "payment_method": verification.get("metadata", {}).get("payment_method"),
                    },
                )

                # Update invoice
                invoice = self.invoice_repo.get(payment.invoice_id)
                new_paid_amount = invoice.paid_amount + payment.amount

                if new_paid_amount >= invoice.amount:
                    invoice_status = InvoiceStatus.PAID
                else:
                    invoice_status = InvoiceStatus.PARTIAL

                self.invoice_repo.update(
                    payment.invoice_id,
                    {
                        "paid_amount": new_paid_amount,
                        "status": invoice_status,
                        "paid_at": datetime.utcnow(),
                    },
                )

                self.db.commit()

                # Generate receipt (placeholder for now)
                payment.receipt_url = f"/api/v1/payments/{payment_id}/receipt"

            else:
                self.payment_repo.update(
                    payment_id,
                    {
                        "status": PaymentStatus.FAILED,
                        "error_message": verification.get("error", "Payment failed"),
                    },
                )
                self.db.commit()

        except Exception as e:
            self.payment_repo.update(
                payment_id,
                {"status": PaymentStatus.FAILED, "error_message": str(e)},
            )
            self.db.commit()
            raise PaymentError(f"Payment verification failed: {str(e)}")

        return self.payment_repo.get(payment_id)