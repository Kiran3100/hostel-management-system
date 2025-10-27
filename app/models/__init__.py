"""SQLAlchemy models."""

from app.models.user import User, RefreshToken, OTPCode, UserRole
from app.models.hostel import Hostel, Subscription, Plan, PlanTier, SubscriptionStatus
from app.models.room import Room, Bed, RoomType
from app.models.tenant import TenantProfile, CheckInOut, CheckInOutStatus
from app.models.fee import (
    FeeSchedule,
    Invoice,
    Payment,
    FeeFrequency,
    InvoiceStatus,
    PaymentStatus,
)
from app.models.complaint import (
    Complaint,
    ComplaintComment,
    ComplaintCategory,
    ComplaintPriority,
    ComplaintStatus,
)
from app.models.notice import Notice, NoticePriority
from app.models.mess import MessMenu, MealType
from app.models.leave import LeaveApplication, LeaveStatus
from app.models.support import SupportTicket, TicketPriority, TicketStatus
from app.models.notification import Notification, DeviceToken, NotificationType, Platform
from app.models.audit import AuditLog, AuditAction
from app.models.attachment import Attachment

__all__ = [
    # User
    "User",
    "RefreshToken",
    "OTPCode",
    "UserRole",
    # Hostel
    "Hostel",
    "Subscription",
    "Plan",
    "PlanTier",
    "SubscriptionStatus",
    # Room
    "Room",
    "Bed",
    "RoomType",
    # Tenant
    "TenantProfile",
    "CheckInOut",
    "CheckInOutStatus",
    # Fee
    "FeeSchedule",
    "Invoice",
    "Payment",
    "FeeFrequency",
    "InvoiceStatus",
    "PaymentStatus",
    # Complaint
    "Complaint",
    "ComplaintComment",
    "ComplaintCategory",
    "ComplaintPriority",
    "ComplaintStatus",
    # Notice
    "Notice",
    "NoticePriority",
    # Mess
    "MessMenu",
    "MealType",
    # Leave
    "LeaveApplication",
    "LeaveStatus",
    # Support
    "SupportTicket",
    "TicketPriority",
    "TicketStatus",
    # Notification
    "Notification",
    "DeviceToken",
    "NotificationType",
    "Platform",
    # Audit
    "AuditLog",
    "AuditAction",
    # Attachment
    "Attachment",
]