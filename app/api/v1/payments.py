"""Payment endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.fee import (
    InvoiceCreate,
    InvoiceResponse,
    PaymentInitiateRequest,
    PaymentResponse,
)
from app.schemas.common import MessageResponse
from app.models.user import User, UserRole
from app.models.fee import Invoice, Payment
from app.repositories.payment import InvoiceRepository, PaymentRepository
from app.core.rbac import require_role, check_hostel_access
from app.api.deps import get_current_user
from app.services.payment import PaymentService
from app.adapters.payment.mock import MockPaymentProvider
from app.adapters.payment.razorpay import RazorpayProvider
from app.config import settings

router = APIRouter(tags=["Payments"])


def get_payment_provider():
    """Get payment provider based on config."""
    if settings.payment_provider == "razorpay":
        return RazorpayProvider()
    return MockPaymentProvider()


@router.get("/invoices", response_model=List[InvoiceResponse])
async def list_invoices(
    tenant_id: int = None,
    hostel_id: int = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List invoices."""
    invoice_repo = InvoiceRepository(Invoice, db)

    if current_user.role == UserRole.TENANT:
        # Tenants can only see their own invoices
        from app.repositories.tenant import TenantRepository
        from app.models.tenant import TenantProfile

        tenant_repo = TenantRepository(TenantProfile, db)
        tenant = await tenant_repo.get_by_user(current_user.id)
        if not tenant:
            return []
        invoices = await invoice_repo.get_by_tenant(tenant.id)
    elif tenant_id:
        invoices = await invoice_repo.get_by_tenant(tenant_id)
        if invoices:
            check_hostel_access(current_user, invoices[0].hostel_id)
    elif hostel_id:
        check_hostel_access(current_user, hostel_id)
        invoices = await invoice_repo.get_by_hostel(hostel_id)
    else:
        # Default to current user's hostel
        if current_user.hostel_id:
            invoices = await invoice_repo.get_by_hostel(current_user.hostel_id)
        else:
            invoices = []

    return invoices


@router.post("/invoices", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
async def create_invoice(
    request: InvoiceCreate,
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.HOSTEL_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """Create an invoice."""
    hostel_id = current_user.hostel_id
    if current_user.role == UserRole.SUPER_ADMIN:
        # Super Admin must specify hostel via tenant
        from app.repositories.tenant import TenantRepository
        from app.models.tenant import TenantProfile

        tenant_repo = TenantRepository(TenantProfile, db)
        tenant = await tenant_repo.get(request.tenant_id)
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        hostel_id = tenant.hostel_id

    payment_provider = get_payment_provider()
    payment_service = PaymentService(db, payment_provider)

    invoice = await payment_service.generate_invoice(
        hostel_id=hostel_id,
        tenant_id=request.tenant_id,
        amount=request.amount,
        due_date=request.due_date,
        fee_schedule_id=request.fee_schedule_id,
        notes=request.notes,
    )

    return invoice


@router.post("/payments", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def initiate_payment(
    request: PaymentInitiateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Initiate a payment (Tenant)."""
    # Get tenant profile
    from app.repositories.tenant import TenantRepository
    from app.models.tenant import TenantProfile

    tenant_repo = TenantRepository(TenantProfile, db)
    tenant = await tenant_repo.get_by_user(current_user.id)

    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant profile not found")

    payment_provider = get_payment_provider()
    payment_service = PaymentService(db, payment_provider)

    payment = await payment_service.initiate_payment(
        invoice_id=request.invoice_id,
        tenant_id=tenant.id,
        amount=request.amount,
        gateway=request.gateway,
    )

    return payment


@router.get("/payments", response_model=List[PaymentResponse])
async def list_payments(
    tenant_id: int = None,
    hostel_id: int = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List payments."""
    payment_repo = PaymentRepository(Payment, db)

    if current_user.role == UserRole.TENANT:
        from app.repositories.tenant import TenantRepository
        from app.models.tenant import TenantProfile

        tenant_repo = TenantRepository(TenantProfile, db)
        tenant = await tenant_repo.get_by_user(current_user.id)
        if not tenant:
            return []
        payments = await payment_repo.get_multi(filters={"tenant_id": tenant.id})
    elif tenant_id:
        payments = await payment_repo.get_multi(filters={"tenant_id": tenant_id})
        if payments:
            check_hostel_access(current_user, payments[0].hostel_id)
    elif hostel_id:
        check_hostel_access(current_user, hostel_id)
        payments = await payment_repo.get_multi(filters={"hostel_id": hostel_id})
    else:
        if current_user.hostel_id:
            payments = await payment_repo.get_multi(filters={"hostel_id": current_user.hostel_id})
        else:
            payments = []

    return payments


@router.post("/payments/{payment_id}/confirm", response_model=PaymentResponse)
async def confirm_payment(
    payment_id: int,
    transaction_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Confirm payment (webhook or callback)."""
    payment_provider = get_payment_provider()
    payment_service = PaymentService(db, payment_provider)

    payment = await payment_service.confirm_payment(payment_id, transaction_id)

    return payment


@router.get("/payments/{payment_id}/receipt")
async def download_receipt(
    payment_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Download payment receipt."""
    payment_repo = PaymentRepository(Payment, db)
    payment = await payment_repo.get(payment_id)

    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    # Check access
    if current_user.role == UserRole.TENANT:
        from app.repositories.tenant import TenantRepository
        from app.models.tenant import TenantProfile

        tenant_repo = TenantRepository(TenantProfile, db)
        tenant = await tenant_repo.get_by_user(current_user.id)
        if not tenant or payment.tenant_id != tenant.id:
            raise HTTPException(status_code=403, detail="Access denied")
    else:
        check_hostel_access(current_user, payment.hostel_id)

    # In production, generate PDF receipt here
    return {
        "receipt_number": payment.receipt_number,
        "payment_id": payment.id,
        "amount": payment.amount,
        "status": payment.status,
        "paid_at": payment.paid_at,
    }