# Hostel Management System - Complete Swagger API Testing Guide

**Version:** 1.0.0  
**Last Updated:** October 2025  
**Base URL:** `http://localhost:8000`

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Authentication](#authentication)
3. [Hostels Management](#hostels-management)
4. [Rooms & Beds Management](#rooms--beds-management)
5. [Tenant Management](#tenant-management)
6. [Subscription Management](#subscription-management)
7. [Payments & Invoices](#payments--invoices)
8. [Complaints Management](#complaints-management)
9. [Notices Management](#notices-management)
10. [Mess Menu Management](#mess-menu-management)
11. [Leave Applications](#leave-applications)
12. [Notifications](#notifications)
13. [Reports & Analytics](#reports--analytics)
14. [User Management](#user-management)
15. [Testing Workflows](#testing-workflows)
16. [Troubleshooting](#troubleshooting)

---

## Getting Started

### Prerequisites
- Python 3.11+
- PostgreSQL 15+
- Redis (optional, for rate limiting)

### Setup Steps

#### 1. Start the Server
```bash
# Navigate to project directory
cd hostel-management-system

# Activate virtual environment
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Start server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 2. Initialize Database (First Time Only)
```bash
# Reset database
python scripts/reset_db_simple.py

# Seed initial data
python scripts/seed.py

# Create tenant profile (for complaint testing)
python scripts/create_tenant_profile.py
```

#### 3. Access Swagger UI
Open browser and navigate to:
```
http://localhost:8000/docs
```

### Default Test Credentials

| Role | Email | Password | Purpose |
|------|-------|----------|---------|
| **Super Admin** | superadmin@hostelms.com | SuperAdmin@123 | Full system access |
| **Hostel Admin** | admin@demo.com | Admin@123 | Manage Demo Hostel |
| **Tenant** | tenant@demo.com | Tenant@123 | Tenant operations |

⚠️ **IMPORTANT:** Change these passwords in production!

---

## Authentication

### Authorization Process

**All endpoints except login require authentication.**

#### Step 1: Login
Use any login endpoint to get access token.

#### Step 2: Authorize in Swagger
1. Click the **"Authorize"** button (🔓 lock icon) at top-right
2. Enter: `Bearer YOUR_ACCESS_TOKEN`
3. Click **"Authorize"**
4. Click **"Close"**

✅ All subsequent requests will now include authentication!

---

### 1.1 Register New User

**Endpoint:** `POST /api/v1/auth/register`  
**Permission:** Admin only (Super Admin or Hostel Admin)  
**Description:** Create a new user account

**Request Body:**
```json
{
  "email": "newuser@example.com",
  "phone": "+919876543299",
  "password": "SecurePass@123",
  "role": "TENANT",
  "hostel_id": 1
}
```

**Valid Roles:**
- `TENANT` - Regular hostel tenant
- `HOSTEL_ADMIN` - Hostel administrator
- `SUPER_ADMIN` - System administrator

**Response (201 Created):**
```json
{
  "id": 4,
  "email": "newuser@example.com",
  "phone": "+919876543299",
  "role": "TENANT",
  "hostel_id": 1,
  "is_active": true,
  "is_verified": true
}
```

---

### 1.2 Login with Email/Password

**Endpoint:** `POST /api/v1/auth/login`  
**Permission:** Public

**Request Body:**
```json
{
  "email": "admin@demo.com",
  "password": "Admin@123"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer",
  "user_id": 2,
  "role": "HOSTEL_ADMIN"
}
```

---

### 1.3 OTP Login (Passwordless)

#### Step 1: Request OTP
**Endpoint:** `POST /api/v1/auth/login/otp/request`

```json
{
  "phone": "+919876543212",
  "hostel_code": "DEMO001"
}
```

#### Step 2: Verify OTP
**Endpoint:** `POST /api/v1/auth/login/otp/verify`

```json
{
  "phone": "+919876543212",
  "otp": "123456"
}
```

---

### 1.4 Get Current User Profile

**Endpoint:** `GET /api/v1/auth/me`  
**Permission:** Authenticated users

**Response (200 OK):**
```json
{
  "id": 2,
  "email": "admin@demo.com",
  "phone": "+919876543211",
  "role": "HOSTEL_ADMIN",
  "hostel_id": 1,
  "is_active": true,
  "is_verified": true
}
```

---

### 1.5 Change Password

**Endpoint:** `POST /api/v1/auth/change-password`

```json
{
  "old_password": "Admin@123",
  "new_password": "NewSecure@456"
}
```

---

## Hostels Management

### 2.1 List All Hostels

**Endpoint:** `GET /api/v1/hostels`  
**Permission:** Super Admin only

**Query Parameters:**
- `page` (integer): Page number (default: 1)
- `page_size` (integer): Items per page (default: 20)

**Response (200 OK):**
```json
{
  "items": [
    {
      "id": 1,
      "name": "Demo Hostel",
      "code": "DEMO001",
      "city": "Mumbai",
      "state": "Maharashtra",
      "is_active": true
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20,
  "total_pages": 1
}
```

---

### 2.2 Create Hostel

**Endpoint:** `POST /api/v1/hostels`  
**Permission:** Super Admin only

**Request Body:**
```json
{
  "name": "New Hostel",
  "code": "NEW001",
  "address": "456 New Street",
  "city": "Delhi",
  "state": "Delhi",
  "pincode": "110001",
  "phone": "+919876543220",
  "email": "new@hostel.com"
}
```

---

### 2.3 Update Hostel

**Endpoint:** `PATCH /api/v1/hostels/{hostel_id}`  
**Permission:** Super Admin only

```json
{
  "name": "Updated Name",
  "is_active": true
}
```

---

### 2.4 Get Hostel Dashboard

**Endpoint:** `GET /api/v1/hostels/{hostel_id}/dashboard`  
**Permission:** Authenticated users

**Response (200 OK):**
```json
{
  "hostel_id": 1,
  "total_rooms": 10,
  "total_beds": 25,
  "occupied_beds": 18,
  "occupancy_rate": 72.0,
  "total_tenants": 18,
  "pending_fees": 50000.00,
  "total_revenue": 200000.00,
  "pending_complaints": 3
}
```

---

## Rooms & Beds Management

### 3.1 List Rooms

**Endpoint:** `GET /api/v1/rooms`  
**Query Parameters:** `hostel_id` (required for Super Admin)

---

### 3.2 Create Room

**Endpoint:** `POST /api/v1/rooms`  
**Permission:** Admin

**Request Body:**
```json
{
  "hostel_id": 1,
  "number": "102",
  "floor": 1,
  "room_type": "SINGLE",
  "capacity": 1,
  "description": "Single room with AC"
}
```

**Room Types:** `SINGLE`, `DOUBLE`, `TRIPLE`, `DORMITORY`

---

### 3.3 Assign Tenant to Bed

**Endpoint:** `POST /api/v1/beds/{bed_id}/assign`

```json
{
  "tenant_id": 1
}
```

---

### 3.4 Vacate Bed

**Endpoint:** `POST /api/v1/beds/{bed_id}/vacate`

---

## Tenant Management

### 4.1 List Tenants

**Endpoint:** `GET /api/v1/tenants`  
**Query Parameters:** `hostel_id`

---

### 4.2 Create Tenant Profile

**Endpoint:** `POST /api/v1/tenants`  
**Permission:** Admin

**Request Body:**
```json
{
  "user_id": 4,
  "hostel_id": 1,
  "full_name": "John Doe",
  "date_of_birth": "2000-01-15",
  "gender": "Male",
  "id_proof_type": "Aadhaar",
  "id_proof_number": "1234-5678-9012",
  "guardian_name": "Jane Doe",
  "guardian_phone": "+919876543213",
  "emergency_contact": "+919876543213"
}
```

---

### 4.3 Check-In Tenant

**Endpoint:** `POST /api/v1/tenants/{tenant_id}/check-in`

```json
{
  "bed_id": 5,
  "check_in_date": "2025-10-09"
}
```

---

### 4.4 Check-Out Tenant

**Endpoint:** `POST /api/v1/tenants/{tenant_id}/check-out`

```json
{
  "check_out_date": "2025-10-09",
  "notes": "All good"
}
```

---

## Subscription Management

### 5.1 List Subscription Plans

**Endpoint:** `GET /api/v1/subscriptions/plans`

**Response:**
```json
[
  {
    "id": 1,
    "name": "Free Plan",
    "tier": "FREE",
    "max_tenants": 10,
    "max_rooms": 5,
    "features": {
      "basic_billing": true,
      "reports": false
    }
  }
]
```

---

### 5.2 Create Subscription

**Endpoint:** `POST /api/v1/subscriptions`  
**Permission:** Super Admin

```json
{
  "hostel_id": 1,
  "plan_id": 2,
  "start_date": "2025-10-09",
  "end_date": "2025-11-09",
  "auto_renew": false
}
```

---

### 5.3 Get Feature Usage

**Endpoint:** `GET /api/v1/subscriptions/{subscription_id}/usage`

**Response:**
```json
{
  "hostel_id": 1,
  "plan_name": "Free Plan",
  "current_tenants": 8,
  "max_tenants": 10,
  "current_rooms": 4,
  "max_rooms": 5,
  "usage_percentage": {
    "tenants": 80.0,
    "rooms": 80.0
  }
}
```

---

## Payments & Invoices

### 6.1 List Invoices

**Endpoint:** `GET /api/v1/invoices`  
**Query Parameters:** `tenant_id`, `hostel_id`

---

### 6.2 Create Invoice

**Endpoint:** `POST /api/v1/invoices`  
**Permission:** Admin

```json
{
  "tenant_id": 1,
  "amount": 5000.00,
  "due_date": "2025-10-15",
  "notes": "Monthly rent"
}
```

---

### 6.3 Initiate Payment

**Endpoint:** `POST /api/v1/payments`  
**Permission:** Tenant

```json
{
  "invoice_id": 1,
  "amount": 5000.00,
  "gateway": "mock"
}
```

---

### 6.4 List Payments

**Endpoint:** `GET /api/v1/payments`  
**Query Parameters:** `tenant_id`, `hostel_id`

---

## Complaints Management

### 7.1 List Complaints

**Endpoint:** `GET /api/v1/complaints`  
**Query Parameters:** `hostel_id`

---

### 7.2 Create Complaint

**Endpoint:** `POST /api/v1/complaints`  
**Permission:** Tenant only

**Request Body:**
```json
{
  "title": "Water leakage in room",
  "description": "Water is leaking from bathroom ceiling",
  "category": "MAINTENANCE",
  "priority": "HIGH"
}
```

**Categories:** `MAINTENANCE`, `CLEANLINESS`, `FOOD`, `ELECTRICITY`, `WATER`, `SECURITY`, `OTHER`

**Priorities:** `LOW`, `MEDIUM`, `HIGH`, `URGENT`

---

### 7.3 Update Complaint

**Endpoint:** `PATCH /api/v1/complaints/{complaint_id}`  
**Permission:** Admin

```json
{
  "status": "IN_PROGRESS",
  "assigned_to": 2,
  "priority": "URGENT"
}
```

**Statuses:** `OPEN`, `IN_PROGRESS`, `RESOLVED`, `CLOSED`, `REJECTED`

---

### 7.4 Add Comment

**Endpoint:** `POST /api/v1/complaints/{complaint_id}/comments`

```json
{
  "comment": "Working on fixing the leak"
}
```

---

## Notices Management

### 8.1 List Notices

**Endpoint:** `GET /api/v1/notices`  
**Query Parameters:** `hostel_id`, `active_only` (default: true)

---

### 8.2 Create Notice

**Endpoint:** `POST /api/v1/notices`  
**Permission:** Admin

**Request Body:**
```json
{
  "title": "Maintenance Notice",
  "content": "Water will be shut off tomorrow from 10 AM to 2 PM",
  "priority": "HIGH",
  "published_at": "2025-10-09T10:00:00Z",
  "expires_at": "2025-10-10T18:00:00Z"
}
```

**Priorities:** `LOW`, `NORMAL`, `HIGH`, `URGENT`

---

### 8.3 Update Notice

**Endpoint:** `PATCH /api/v1/notices/{notice_id}`  
**Permission:** Admin

```json
{
  "title": "Updated Title",
  "priority": "URGENT"
}
```

---

## Mess Menu Management

### 9.1 List Menus

**Endpoint:** `GET /api/v1/mess-menu`

**Query Parameters:**
- `hostel_id` (required for Super Admin)
- `menu_date` (YYYY-MM-DD)
- `date_from`, `date_to` (date range)
- `meal_type`

---

### 9.2 Create/Update Menu

**Endpoint:** `POST /api/v1/mess-menu`  
**Permission:** Admin

**Request Body:**
```json
{
  "date": "2025-10-09",
  "meal_type": "LUNCH",
  "items": ["Rice", "Dal", "Roti", "Curry", "Salad"]
}
```

**Meal Types:** `BREAKFAST`, `LUNCH`, `SNACKS`, `DINNER`

---

### 9.3 Bulk Create Menus

**Endpoint:** `POST /api/v1/mess-menu/bulk`

```json
{
  "menus": [
    {
      "date": "2025-10-09",
      "meal_type": "BREAKFAST",
      "items": ["Idli", "Sambhar", "Chutney"]
    },
    {
      "date": "2025-10-09",
      "meal_type": "LUNCH",
      "items": ["Rice", "Dal", "Roti"]
    }
  ]
}
```

---

## Leave Applications

### 10.1 List Leaves

**Endpoint:** `GET /api/v1/leaves`  
**Query Parameters:** `hostel_id`, `tenant_id`

---

### 10.2 Create Leave Application

**Endpoint:** `POST /api/v1/leaves`  
**Permission:** Tenant

```json
{
  "start_date": "2025-10-15",
  "end_date": "2025-10-20",
  "reason": "Going home for festival"
}
```

---

### 10.3 Approve/Reject Leave

**Endpoint:** `POST /api/v1/leaves/{leave_id}/approve`  
**Permission:** Admin

```json
{
  "approved": true,
  "notes": "Approved. Have a safe trip!"
}
```

---

## Notifications

### 11.1 List Notifications

**Endpoint:** `GET /api/v1/notifications`

**Query Parameters:**
- `is_read` (true/false)
- `page`, `page_size`

---

### 11.2 Get Notification Count

**Endpoint:** `GET /api/v1/notifications/count`

**Response:**
```json
{
  "total": 15,
  "unread": 3
}
```

---

### 11.3 Mark as Read

**Endpoint:** `PATCH /api/v1/notifications/{notification_id}`

---

### 11.4 Mark All as Read

**Endpoint:** `POST /api/v1/notifications/mark-all-read`

---

### 11.5 Register Device Token

**Endpoint:** `POST /api/v1/notifications/device-tokens`

```json
{
  "token": "fcm_device_token_here",
  "platform": "ANDROID"
}
```

**Platforms:** `IOS`, `ANDROID`, `WEB`

---

## Reports & Analytics

### 12.1 Super Admin Dashboard

**Endpoint:** `GET /api/v1/reports/dashboard`  
**Permission:** Super Admin

**Response:**
```json
{
  "total_hostels": 5,
  "active_hostels": 4,
  "total_tenants": 120,
  "total_revenue": 500000.00,
  "active_subscriptions": 4,
  "pending_tickets": 2
}
```

---

### 12.2 Hostel Dashboard

**Endpoint:** `GET /api/v1/reports/hostel-dashboard`  
**Query Parameters:** `hostel_id`

**Response:**
```json
{
  "hostel_id": 1,
  "hostel_name": "Demo Hostel",
  "total_rooms": 10,
  "total_beds": 25,
  "occupied_beds": 18,
  "occupancy_rate": 72.0,
  "total_tenants": 18,
  "pending_fees": 50000.00,
  "total_revenue": 200000.00,
  "pending_complaints": 3
}
```

---

### 12.3 Occupancy Report

**Endpoint:** `GET /api/v1/reports/occupancy`

**Query Parameters:**
- `hostel_id` (required)
- `date_from`, `date_to`

---

### 12.4 Income Report

**Endpoint:** `GET /api/v1/reports/income`

**Query Parameters:**
- `hostel_id` (required)
- `date_from`, `date_to`

---

## User Management

### 13.1 List Users

**Endpoint:** `GET /api/v1/users`  
**Permission:** Admin

**Query Parameters:**
- `hostel_id`
- `role`

---

### 13.2 Update User

**Endpoint:** `PATCH /api/v1/users/{user_id}`

```json
{
  "email": "newemail@example.com",
  "phone": "+919999999999",
  "is_active": true
}
```

---

### 13.3 Delete User

**Endpoint:** `DELETE /api/v1/users/{user_id}`  
**Permission:** Admin

⚠️ Cannot delete yourself or other super admins

---

### 13.4 Restore User

**Endpoint:** `POST /api/v1/users/{user_id}/restore`  
**Permission:** Super Admin

---

## Testing Workflows

### Workflow 1: Complete Tenant Onboarding
```
1. POST /api/v1/auth/register (create user as TENANT)
2. POST /api/v1/tenants (create tenant profile)
3. POST /api/v1/tenants/{id}/check-in (assign to bed)
4. POST /api/v1/invoices (create first invoice)
```

### Workflow 2: Complaint Management
```
1. Login as Tenant
2. POST /api/v1/complaints (create complaint)
3. Login as Admin
4. PATCH /api/v1/complaints/{id} (assign & update)
5. POST /api/v1/complaints/{id}/comments (add comment)
6. PATCH /api/v1/complaints/{id} (mark resolved)
```

### Workflow 3: Payment Processing
```
1. POST /api/v1/invoices (admin creates invoice)
2. Login as Tenant
3. GET /api/v1/invoices (check pending)
4. POST /api/v1/payments (initiate payment)
5. POST /api/v1/payments/{id}/confirm (confirm)
```

---

## Troubleshooting

### Issue: "401 Unauthorized"
**Solution:** Click "Authorize" and enter `Bearer YOUR_TOKEN`

### Issue: "403 Forbidden"
**Solution:** Wrong role. Check endpoint permissions.

### Issue: "422 Validation Error"
**Solution:** Check request body matches schema exactly.

### Issue: "404 Not Found"
**Solution:** Verify resource ID exists. Run seed script.

### Issue: Tenant can't create complaint
**Solution:** Run `python scripts/create_tenant_profile.py`

---

## Quick Test Checklist

```
✅ Login as each role
✅ Create, Read, Update, Delete operations
✅ Test with valid and invalid data
✅ Check authorization
✅ Test pagination
✅ Test filters
✅ Test soft delete and restore
✅ Verify relationships
```

---

**Happy Testing! 🚀**