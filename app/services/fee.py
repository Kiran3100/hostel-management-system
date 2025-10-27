"""Fee management service."""

from datetime import date, timedelta
from decimal import Decimal
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.fee import FeeSchedule, Invoice, InvoiceStatus
from app.repositories.payment import FeeScheduleRepository, InvoiceRepository
from app.exceptions import NotFoundError, ValidationError


class FeeService:
    """Service for managing fees and fee schedules."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.fee_schedule_repo = FeeScheduleRepository(FeeSchedule, db)
        self.invoice_repo = InvoiceRepository(Invoice, db)
    
    async def create_recurring_invoices(self, hostel_id: int) -> List[Invoice]:
        """Generate recurring invoices based on fee schedules."""
        # Get active fee schedules
        schedules = await self.fee_schedule_repo.get_by_hostel(hostel_id)
        
        invoices = []
        for schedule in schedules:
            if not schedule.is_active:
                continue
            
            # Check if invoice already exists for this period
            today = date.today()
            if schedule.frequency == "MONTHLY":
                due_date = date(today.year, today.month, schedule.due_day)
            elif schedule.frequency == "QUARTERLY":
                # Calculate quarter
                quarter = (today.month - 1) // 3
                due_date = date(today.year, quarter * 3 + 1, schedule.due_day)
            
            # Generate invoices for all active tenants
            # ... implementation
            
        await self.db.commit()
        return invoices
    
    async def calculate_late_fees(self, invoice_id: int) -> Decimal:
        """Calculate late fees for overdue invoices."""
        invoice = await self.invoice_repo.get(invoice_id)
        if not invoice:
            raise NotFoundError("Invoice not found")
        
        if invoice.status != InvoiceStatus.OVERDUE:
            return Decimal("0.00")
        
        days_overdue = (date.today() - invoice.due_date).days
        late_fee = invoice.amount * Decimal("0.01") * days_overdue 
        
        return min(late_fee, invoice.amount * Decimal("0.10"))  