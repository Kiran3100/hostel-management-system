# app/api/v1/router.py - UPDATED WITH VISITOR ENDPOINTS

"""Main API v1 router - UPDATED WITH VISITOR ENDPOINTS."""

from fastapi import APIRouter

from app.api.v1 import (
    auth,
    hostels,
    rooms,
    tenants,
    subscriptions,
    payments,
    complaints,
    notices,
    mess,
    leaves,
    notifications,
    reports,
    users,
    visitor,  
    self_registration,
    multi_hostel,
)



api_router = APIRouter()

# Include all routers
api_router.include_router(auth.router)
api_router.include_router(hostels.router)
# api_router.include_router(multi_hostel.router)
api_router.include_router(rooms.router)
api_router.include_router(tenants.router)
api_router.include_router(subscriptions.router)
api_router.include_router(payments.router)
api_router.include_router(complaints.router)
api_router.include_router(notices.router)
api_router.include_router(mess.router)
api_router.include_router(leaves.router)
api_router.include_router(notifications.router)
api_router.include_router(reports.router)
api_router.include_router(self_registration.router)

# ✅ NEW: Visitor endpoints
# api_router.include_router(visitor.router)
# api_router.include_router(admin_visitors.router)
api_router.include_router(users.router)