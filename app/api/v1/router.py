# app/api/v1/router.py - UPDATE

"""Main API v1 router - UPDATED WITH USER ENDPOINTS."""

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
)

api_router = APIRouter()

# Include all routers
api_router.include_router(auth.router)
api_router.include_router(hostels.router)
api_router.include_router(rooms.router)
api_router.include_router(tenants.router)
api_router.include_router(users.router)  
api_router.include_router(subscriptions.router)
api_router.include_router(payments.router)
api_router.include_router(complaints.router)
api_router.include_router(notices.router)
api_router.include_router(mess.router)
api_router.include_router(leaves.router)
api_router.include_router(notifications.router)
api_router.include_router(reports.router)