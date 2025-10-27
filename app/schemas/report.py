from typing import List, Optional
from datetime import date
from decimal import Decimal
from pydantic import BaseModel, Field


class DashboardStats(BaseModel):
    """Super Admin dashboard statistics - FIXED."""
    
    total_hostels: int = 0
    active_hostels: int = 0
    total_tenants: int = 0
    total_revenue: Decimal = Decimal("0.00")
    active_subscriptions: int = 0  # Added default
    pending_tickets: int = 0  # Added default


class HostelDashboardStats(BaseModel):
    """Hostel Admin dashboard statistics."""
    
    hostel_id: int
    hostel_name: str = "Unknown"
    total_rooms: int = 0
    total_beds: int = 0
    occupied_beds: int = 0
    occupancy_rate: float = 0.0
    total_tenants: int = 0
    pending_fees: Decimal = Decimal("0.00")
    total_revenue: Decimal = Decimal("0.00")
    pending_complaints: int = 0
    active_notices: int = 0


class OccupancyReport(BaseModel):
    """Occupancy report."""
    
    hostel_id: int
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    total_beds: int = 0
    average_occupancy: float = 0.0
    peak_occupancy: int = 0
    daily_occupancy: List[dict] = Field(default_factory=list)


class IncomeReport(BaseModel):
    """Income/revenue report."""
    
    hostel_id: int
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    total_revenue: Decimal = Decimal("0.00")
    total_fees_collected: Decimal = Decimal("0.00")
    total_pending: Decimal = Decimal("0.00")
    payment_breakdown: dict = Field(default_factory=dict)
    monthly_revenue: List[dict] = Field(default_factory=list)


class ComplaintReport(BaseModel):
    """Complaint analytics."""
    
    hostel_id: int
    total_complaints: int = 0
    open_complaints: int = 0
    resolved_complaints: int = 0
    average_resolution_time_hours: float = 0.0
    category_breakdown: dict = Field(default_factory=dict)
    priority_breakdown: dict = Field(default_factory=dict)
