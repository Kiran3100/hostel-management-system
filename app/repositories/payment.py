"""Payment repositories."""

from typing import Optional
from sqlalchemy import select

from app.models.fee import FeeSchedule, Invoice, Payment
from app.repositories.base import BaseRepository


class FeeScheduleRepository(BaseRepository[FeeSchedule]):
    """Fee schedule repository."""

    async def get_by_hostel(self, hostel_id: int) -> list[FeeSchedule]:
        """Get fee schedules by hostel."""
        result = await self.db.execute(
            select(FeeSchedule).where(
                FeeSchedule.hostel_id == hostel_id, FeeSchedule.is_active == True
            )
        )
        return list(result.scalars().all())


class InvoiceRepository(BaseRepository[Invoice]):
    """Invoice repository."""

    async def get_by_number(self, invoice_number: str) -> Optional[Invoice]:
        """Get invoice by number."""
        result = await self.db.execute(
            select(Invoice).where(Invoice.invoice_number == invoice_number)
        )
        return result.scalar_one_or_none()

    async def get_by_tenant(self, tenant_id: int) -> list[Invoice]:
        """Get invoices by tenant."""
        result = await self.db.execute(
            select(Invoice)
            .where(Invoice.tenant_id == tenant_id)
            .order_by(Invoice.due_date.desc())
        )
        return list(result.scalars().all())

    async def get_by_hostel(self, hostel_id: int) -> list[Invoice]:
        """Get invoices by hostel."""
        result = await self.db.execute(
            select(Invoice)
            .where(Invoice.hostel_id == hostel_id)
            .order_by(Invoice.created_at.desc())
        )
        return list(result.scalars().all())


class PaymentRepository(BaseRepository[Payment]):
    """Payment repository."""

    async def get_by_idempotency_key(self, key: str) -> Optional[Payment]:
        """Get payment by idempotency key."""
        result = await self.db.execute(
            select(Payment).where(Payment.idempotency_key == key)
        )
        return result.scalar_one_or_none()

    async def get_by_transaction_id(self, transaction_id: str) -> Optional[Payment]:
        """Get payment by transaction ID."""
        result = await self.db.execute(
            select(Payment).where(Payment.transaction_id == transaction_id)
        )
        return result.scalar_one_or_none()

    async def get_by_invoice(self, invoice_id: int) -> list[Payment]:
        """Get payments for an invoice."""
        result = await self.db.execute(
            select(Payment)
            .where(Payment.invoice_id == invoice_id)
            .order_by(Payment.created_at.desc())
        )
        return list(result.scalars().all())