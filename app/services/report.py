from datetime import date
from decimal import Decimal
from typing import Dict, List

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.room import Bed
from app.models.tenant import TenantProfile
from app.models.fee import Invoice, Payment, PaymentStatus, InvoiceStatus
from app.models.complaint import Complaint, ComplaintStatus
from app.models.hostel import Hostel, Subscription, SubscriptionStatus
from app.models.support import SupportTicket, TicketStatus


class ReportService:
    """Report and analytics service - FIXED."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_occupancy_stats(self, hostel_id: int) -> Dict:
        """Get occupancy statistics for a hostel."""
        # Total beds
        total_beds_query = select(func.count(Bed.id)).where(
            Bed.hostel_id == hostel_id, Bed.is_deleted == False
        )
        result = await self.db.execute(total_beds_query)
        total_beds = result.scalar() or 0

        # Occupied beds
        occupied_beds_query = select(func.count(Bed.id)).where(
            Bed.hostel_id == hostel_id, Bed.is_occupied == True, Bed.is_deleted == False
        )
        result = await self.db.execute(occupied_beds_query)
        occupied_beds = result.scalar() or 0

        # Calculate occupancy rate
        occupancy_rate = (occupied_beds / total_beds * 100) if total_beds > 0 else 0

        return {
            "total_beds": total_beds,
            "occupied_beds": occupied_beds,
            "available_beds": total_beds - occupied_beds,
            "occupancy_rate": round(occupancy_rate, 2),
        }

    async def get_income_stats(
        self, hostel_id: int, date_from: date = None, date_to: date = None
    ) -> Dict:
        """Get income statistics."""
        query = select(
            func.sum(Payment.amount).label("total_revenue"),
            func.count(Payment.id).label("total_payments"),
        ).where(Payment.hostel_id == hostel_id, Payment.status == PaymentStatus.SUCCESS)

        if date_from:
            query = query.where(Payment.paid_at >= date_from)
        if date_to:
            query = query.where(Payment.paid_at <= date_to)

        result = await self.db.execute(query)
        row = result.one()

        # Pending fees
        pending_query = select(func.sum(Invoice.total_amount - Invoice.paid_amount)).where(
            Invoice.hostel_id == hostel_id,
            Invoice.status.in_([InvoiceStatus.PENDING, InvoiceStatus.PARTIAL]),
        )
        result = await self.db.execute(pending_query)
        pending_fees = result.scalar() or Decimal("0.00")

        return {
            "total_revenue": row.total_revenue or Decimal("0.00"),
            "total_payments": row.total_payments or 0,
            "pending_fees": pending_fees,
        }

    async def get_complaint_stats(self, hostel_id: int) -> Dict:
        """Get complaint statistics."""
        # Total complaints
        total_query = select(func.count(Complaint.id)).where(Complaint.hostel_id == hostel_id)
        result = await self.db.execute(total_query)
        total_complaints = result.scalar() or 0

        # Open complaints
        open_query = select(func.count(Complaint.id)).where(
            Complaint.hostel_id == hostel_id, Complaint.status == ComplaintStatus.OPEN
        )
        result = await self.db.execute(open_query)
        open_complaints = result.scalar() or 0

        # Resolved complaints
        resolved_query = select(func.count(Complaint.id)).where(
            Complaint.hostel_id == hostel_id, Complaint.status == ComplaintStatus.RESOLVED
        )
        result = await self.db.execute(resolved_query)
        resolved_complaints = result.scalar() or 0

        return {
            "total_complaints": total_complaints,
            "open_complaints": open_complaints,
            "resolved_complaints": resolved_complaints,
            "resolution_rate": (
                round((resolved_complaints / total_complaints * 100), 2)
                if total_complaints > 0
                else 0
            ),
        }

    async def get_super_admin_dashboard(self) -> Dict:
        """Get Super Admin dashboard statistics - FIXED."""
        # Total hostels
        total_hostels_query = select(func.count(Hostel.id)).where(Hostel.is_deleted == False)
        result = await self.db.execute(total_hostels_query)
        total_hostels = result.scalar() or 0

        # Active hostels
        active_hostels_query = select(func.count(Hostel.id)).where(
            Hostel.is_active == True, Hostel.is_deleted == False
        )
        result = await self.db.execute(active_hostels_query)
        active_hostels = result.scalar() or 0

        # Total tenants
        total_tenants_query = select(func.count(TenantProfile.id))
        result = await self.db.execute(total_tenants_query)
        total_tenants = result.scalar() or 0

        # Total revenue
        revenue_query = select(func.sum(Payment.amount)).where(
            Payment.status == PaymentStatus.SUCCESS
        )
        result = await self.db.execute(revenue_query)
        total_revenue = result.scalar() or Decimal("0.00")

        # Active subscriptions - FIXED: Added this field
        active_subs_query = select(func.count(Subscription.id)).where(
            Subscription.status == SubscriptionStatus.ACTIVE
        )
        result = await self.db.execute(active_subs_query)
        active_subscriptions = result.scalar() or 0

        # Pending tickets - FIXED: Added this field
        pending_tickets_query = select(func.count(SupportTicket.id)).where(
            SupportTicket.status.in_([TicketStatus.OPEN, TicketStatus.IN_PROGRESS])
        )
        result = await self.db.execute(pending_tickets_query)
        pending_tickets = result.scalar() or 0

        return {
            "total_hostels": total_hostels,
            "active_hostels": active_hostels,
            "total_tenants": total_tenants,
            "total_revenue": total_revenue,
            "active_subscriptions": active_subscriptions,  # FIXED: Added
            "pending_tickets": pending_tickets,  # FIXED: Added
        }

    async def get_hostel_dashboard(self, hostel_id: int) -> Dict:
        """Get Hostel Admin dashboard statistics."""
        occupancy = await self.get_occupancy_stats(hostel_id)
        income = await self.get_income_stats(hostel_id)
        complaints = await self.get_complaint_stats(hostel_id)

        # Total tenants
        tenant_query = select(func.count(TenantProfile.id)).where(
            TenantProfile.hostel_id == hostel_id
        )
        result = await self.db.execute(tenant_query)
        total_tenants = result.scalar() or 0

        return {
            "hostel_id": hostel_id,
            **occupancy,
            **income,
            **complaints,
            "total_tenants": total_tenants,
        }