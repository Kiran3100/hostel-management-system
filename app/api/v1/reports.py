"""Report endpoints."""

from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.report import (
    DashboardStats,
    HostelDashboardStats,
    OccupancyReport,
    IncomeReport,
)
from app.models.user import User, UserRole
from app.core.rbac import require_role, check_hostel_access
from app.api.deps import get_current_user
from app.services.report import ReportService

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/dashboard", response_model=DashboardStats)
async def super_admin_dashboard(
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """Get Super Admin dashboard."""
    report_service = ReportService(db)
    dashboard = await report_service.get_super_admin_dashboard()

    return DashboardStats(**dashboard)


@router.get("/hostel-dashboard", response_model=HostelDashboardStats)
async def hostel_dashboard(
    hostel_id: int = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get Hostel dashboard."""
    if current_user.role != UserRole.SUPER_ADMIN:
        hostel_id = current_user.hostel_id

    if not hostel_id:
        raise HTTPException(status_code=400, detail="hostel_id required")

    check_hostel_access(current_user, hostel_id)

    report_service = ReportService(db)
    dashboard = await report_service.get_hostel_dashboard(hostel_id)

    # Get hostel name
    from app.repositories.hostel import HostelRepository
    from app.models.hostel import Hostel

    hostel_repo = HostelRepository(Hostel, db)
    hostel = await hostel_repo.get(hostel_id)

    dashboard["hostel_name"] = hostel.name if hostel else "Unknown"

    return HostelDashboardStats(**dashboard)


@router.get("/occupancy")
async def occupancy_report(
    hostel_id: int,
    date_from: date = Query(None),
    date_to: date = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get occupancy report."""
    check_hostel_access(current_user, hostel_id)

    report_service = ReportService(db)
    stats = await report_service.get_occupancy_stats(hostel_id)

    return {
        "hostel_id": hostel_id,
        "date_from": date_from,
        "date_to": date_to,
        **stats,
    }


@router.get("/income")
async def income_report(
    hostel_id: int,
    date_from: date = Query(None),
    date_to: date = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get income report."""
    check_hostel_access(current_user, hostel_id)

    report_service = ReportService(db)
    stats = await report_service.get_income_stats(hostel_id, date_from, date_to)

    return {
        "hostel_id": hostel_id,
        "date_from": date_from,
        "date_to": date_to,
        **stats,
    }