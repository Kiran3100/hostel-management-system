# Complete API Documentation - Hostel Management System

## System Overview

**Base URL**: `/api/v1`  
**Authentication**: JWT Bearer Token  
**Date Format**: ISO 8601 (YYYY-MM-DD / YYYY-MM-DDTHH:mm:ssZ)  
**Currency**: INR (Indian Rupee)

---

## Table of Contents

1. [Authentication & Authorization](#authentication--authorization)
2. [Role Definitions](#role-definitions)
3. [SuperAdmin Endpoints](#superadmin-endpoints)
4. [Hostel Admin Endpoints](#hostel-admin-endpoints)
5. [Tenant Endpoints](#tenant-endpoints)
6. [Visitor Endpoints](#visitor-endpoints)
7. [Common Models](#common-models)
8. [Error Responses](#error-responses)

---

## Authentication & Authorization

### Authentication Endpoints (Public)

#### 1. Register User
```http
POST /auth/register
```
**Access**: Admin-controlled (creates users for system)

**Request Body**:
```json
{
  "email": "admin@hostel.com",
  "phone": "+919876543210",
  "password": "SecurePass123",
  "role": "HOSTEL_ADMIN",
  "hostel_id": 1
}
```

**Response**: `201 Created`
```json
{
  "id": 5,
  "email": "admin@hostel.com",
  "phone": "+919876543210",
  "role": "HOSTEL_ADMIN",
  "hostel_id": 1,
  "is_active": true,
  "is_verified": true,
  "created_at": "2025-01-15T10:30:00Z"
}
```

---

#### 2. Login (Email/Password)
```http
POST /auth/login
```

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "SecurePass123"
}
```

**Response**: `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user_id": 5,
  "role": "HOSTEL_ADMIN"
}
```

---

#### 3. Request OTP (Phone Login)
```http
POST /auth/login/otp/request
```

**Request Body**:
```json
{
  "phone": "+919876543210",
  "hostel_code": "HOSTELLUXURY"
}
```

**Response**: `200 OK`
```json
{
  "message": "OTP sent successfully"
}
```

---

#### 4. Verify OTP
```http
POST /auth/login/otp/verify
```

**Request Body**:
```json
{
  "phone": "+919876543210",
  "otp": "123456"
}
```

**Response**: `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user_id": 5,
  "role": "TENANT"
}
```

---

#### 5. Refresh Access Token
```http
POST /auth/refresh
```

**Request Body**:
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Response**: `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

---

#### 6. Get Current User Profile
```http
GET /auth/me
Authorization: Bearer {access_token}
```

**Response**: `200 OK`
```json
{
  "id": 5,
  "email": "user@example.com",
  "phone": "+919876543210",
  "role": "TENANT",
  "hostel_id": 1,
  "is_active": true,
  "is_verified": true,
  "last_login": "2025-01-15T10:30:00Z",
  "created_at": "2025-01-10T08:00:00Z",
  "updated_at": "2025-01-15T10:30:00Z"
}
```

---

#### 7. Change Password
```http
POST /auth/change-password
Authorization: Bearer {access_token}
```

**Request Body**:
```json
{
  "old_password": "OldPass123",
  "new_password": "NewSecurePass456"
}
```

**Response**: `200 OK`
```json
{
  "message": "Password changed successfully"
}
```

---

#### 8. Logout
```http
POST /auth/logout
Authorization: Bearer {access_token}
```

**Request Body**:
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Response**: `200 OK`
```json
{
  "message": "Logged out successfully"
}
```

---

## Role Definitions

### 1. SuperAdmin
- **Scope**: Entire platform (all hostels)
- **Capabilities**:
  - Manage all hostels and their settings
  - Create/manage all user accounts (admins, tenants)
  - View platform-wide analytics and reports
  - Manage subscriptions and billing
  - Access all financial records
  - Configure system settings
  - View audit logs

### 2. Hostel Admin
- **Scope**: Specific hostel(s) they manage
- **Capabilities**:
  - Manage their hostel's rooms, beds, and inventory
  - Create/manage tenant accounts for their hostel
  - Handle bookings and check-in/check-out
  - Manage complaints and notices
  - View hostel-specific analytics
  - Process payments for their hostel
  - Manage mess menus and schedules
  - Handle leave applications

### 3. Tenant
- **Scope**: Personal account and assigned room
- **Capabilities**:
  - View personal profile and room details
  - Make payments for invoices
  - Submit complaints and track status
  - View notices and mess menus
  - Apply for leaves
  - Access personal payment history
  - Receive notifications

### 4. Visitor (Read-Only)
- **Scope**: Assigned hostel (limited access)
- **Capabilities**:
  - View basic hostel information
  - View public notices
  - View mess menus
  - **Cannot**: Create, update, or delete any resources

---

## SuperAdmin Endpoints

### Hostel Management

#### 1. List All Hostels
```http
GET /hostels?page=1&page_size=20
Authorization: Bearer {access_token}
```

**Query Parameters**:
- `page` (optional): Page number (default: 1)
- `page_size` (optional): Items per page (default: 20)

**Response**: `200 OK`
```json
{
  "items": [
    {
      "id": 1,
      "name": "Luxury Hostel",
      "code": "HOSTELLUXURY",
      "address": "123 Main Street",
      "city": "Mumbai",
      "state": "Maharashtra",
      "pincode": "400001",
      "phone": "+912212345678",
      "email": "info@luxuryhostel.com",
      "timezone": "Asia/Kolkata",
      "is_active": true,
      "created_at": "2025-01-01T00:00:00Z",
      "updated_at": "2025-01-15T10:30:00Z"
    }
  ],
  "total": 50,
  "page": 1,
  "page_size": 20,
  "total_pages": 3
}
```

---

#### 2. Get Hostel Details
```http
GET /hostels/{hostel_id}
Authorization: Bearer {access_token}
```

**Response**: `200 OK`
```json
{
  "id": 1,
  "name": "Luxury Hostel",
  "code": "HOSTELLUXURY",
  "address": "123 Main Street",
  "city": "Mumbai",
  "state": "Maharashtra",
  "pincode": "400001",
  "phone": "+912212345678",
  "email": "info@luxuryhostel.com",
  "timezone": "Asia/Kolkata",
  "is_active": true,
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-01-15T10:30:00Z"
}
```

---

#### 3. Create Hostel
```http
POST /hostels
Authorization: Bearer {access_token}
```

**Request Body**:
```json
{
  "name": "New Hostel",
  "code": "HOSTELNEW",
  "address": "456 Park Avenue",
  "city": "Delhi",
  "state": "Delhi",
  "pincode": "110001",
  "phone": "+911112345678",
  "email": "info@newhostel.com"
}
```

**Response**: `201 Created`
```json
{
  "id": 2,
  "name": "New Hostel",
  "code": "HOSTELNEW",
  "address": "456 Park Avenue",
  "city": "Delhi",
  "state": "Delhi",
  "pincode": "110001",
  "phone": "+911112345678",
  "email": "info@newhostel.com",
  "timezone": "Asia/Kolkata",
  "is_active": true,
  "created_at": "2025-01-15T11:00:00Z",
  "updated_at": "2025-01-15T11:00:00Z"
}
```

---

#### 4. Update Hostel
```http
PATCH /hostels/{hostel_id}
Authorization: Bearer {access_token}
```

**Request Body** (partial update):
```json
{
  "phone": "+911198765432",
  "email": "newemail@hostel.com"
}
```

**Response**: `200 OK`
```json
{
  "id": 1,
  "name": "Luxury Hostel",
  "code": "HOSTELLUXURY",
  "phone": "+911198765432",
  "email": "newemail@hostel.com",
  "is_active": true,
  "updated_at": "2025-01-15T11:30:00Z"
}
```

---

#### 5. Delete Hostel (Soft Delete)
```http
DELETE /hostels/{hostel_id}
Authorization: Bearer {access_token}
```

**Response**: `200 OK`
```json
{
  "message": "Hostel deleted successfully"
}
```

---

#### 6. Restore Deleted Hostel
```http
POST /hostels/{hostel_id}/restore
Authorization: Bearer {access_token}
```

**Response**: `200 OK`
```json
{
  "id": 1,
  "name": "Luxury Hostel",
  "is_active": true,
  "is_deleted": false
}
```

---

### User Management

#### 7. List All Users
```http
GET /users?hostel_id=1&role=HOSTEL_ADMIN
Authorization: Bearer {access_token}
```

**Query Parameters**:
- `hostel_id` (optional): Filter by hostel
- `role` (optional): Filter by role (SUPER_ADMIN, HOSTEL_ADMIN, TENANT, VISITOR)

**Response**: `200 OK`
```json
[
  {
    "id": 5,
    "email": "admin@hostel.com",
    "phone": "+919876543210",
    "role": "HOSTEL_ADMIN",
    "hostel_id": 1,
    "is_active": true,
    "is_verified": true,
    "last_login": "2025-01-15T10:00:00Z",
    "created_at": "2025-01-10T00:00:00Z",
    "updated_at": "2025-01-15T10:00:00Z"
  }
]
```

---

#### 8. Get User Details
```http
GET /users/{user_id}
Authorization: Bearer {access_token}
```

**Response**: `200 OK`
```json
{
  "id": 5,
  "email": "admin@hostel.com",
  "phone": "+919876543210",
  "role": "HOSTEL_ADMIN",
  "hostel_id": 1,
  "is_active": true,
  "is_verified": true,
  "last_login": "2025-01-15T10:00:00Z",
  "created_at": "2025-01-10T00:00:00Z",
  "updated_at": "2025-01-15T10:00:00Z"
}
```

---

#### 9. Update User
```http
PATCH /users/{user_id}
Authorization: Bearer {access_token}
```

**Request Body**:
```json
{
  "is_active": false
}
```

**Response**: `200 OK`
```json
{
  "id": 5,
  "is_active": false,
  "updated_at": "2025-01-15T11:45:00Z"
}
```

---

#### 10. Delete User (Soft Delete)
```http
DELETE /users/{user_id}
Authorization: Bearer {access_token}
```

**Response**: `200 OK`
```json
{
  "message": "User deleted successfully"
}
```

---

#### 11. Restore Deleted User
```http
POST /users/{user_id}/restore
Authorization: Bearer {access_token}
```

**Response**: `200 OK`
```json
{
  "id": 5,
  "is_active": true,
  "is_deleted": false
}
```

---

### Subscription Management

#### 12. List Subscription Plans
```http
GET /subscriptions/plans
Authorization: Bearer {access_token}
```

**Response**: `200 OK`
```json
[
  {
    "id": 1,
    "name": "Free Plan",
    "tier": "FREE",
    "description": "Basic features for small hostels",
    "max_tenants": 10,
    "max_rooms": 5,
    "max_storage_mb": 100,
    "features": {
      "complaints": true,
      "notices": true,
      "payments": false,
      "analytics": false
    },
    "is_active": true
  },
  {
    "id": 2,
    "name": "Standard Plan",
    "tier": "STANDARD",
    "description": "All essential features",
    "max_tenants": 50,
    "max_rooms": 20,
    "max_storage_mb": 1000,
    "features": {
      "complaints": true,
      "notices": true,
      "payments": true,
      "analytics": true,
      "mess_management": true
    },
    "is_active": true
  },
  {
    "id": 3,
    "name": "Premium Plan",
    "tier": "PREMIUM",
    "description": "Unlimited access with advanced features",
    "max_tenants": null,
    "max_rooms": null,
    "max_storage_mb": null,
    "features": {
      "complaints": true,
      "notices": true,
      "payments": true,
      "analytics": true,
      "mess_management": true,
      "advanced_reports": true,
      "api_access": true
    },
    "is_active": true
  }
]
```

---

#### 13. List All Subscriptions
```http
GET /subscriptions?hostel_id=1
Authorization: Bearer {access_token}
```

**Query Parameters**:
- `hostel_id` (optional): Filter by specific hostel

**Response**: `200 OK`
```json
[
  {
    "id": 10,
    "hostel_id": 1,
    "plan_id": 2,
    "status": "ACTIVE",
    "start_date": "2025-01-01",
    "end_date": "2025-12-31",
    "auto_renew": true,
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-01-01T00:00:00Z"
  }
]
```

---

#### 14. Get Subscription Details
```http
GET /subscriptions/{subscription_id}
Authorization: Bearer {access_token}
```

**Response**: `200 OK`
```json
{
  "id": 10,
  "hostel_id": 1,
  "plan_id": 2,
  "status": "ACTIVE",
  "start_date": "2025-01-01",
  "end_date": "2025-12-31",
  "auto_renew": true,
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-01-01T00:00:00Z",
  "plan": {
    "id": 2,
    "name": "Standard Plan",
    "tier": "STANDARD",
    "max_tenants": 50,
    "max_rooms": 20
  }
}
```

---

#### 15. Create/Update Subscription
```http
POST /subscriptions
Authorization: Bearer {access_token}
```

**Request Body**:
```json
{
  "hostel_id": 1,
  "plan_id": 2,
  "start_date": "2025-01-01",
  "end_date": "2025-12-31",
  "auto_renew": true
}
```

**Response**: `201 Created`
```json
{
  "id": 10,
  "hostel_id": 1,
  "plan_id": 2,
  "status": "ACTIVE",
  "start_date": "2025-01-01",
  "end_date": "2025-12-31",
  "auto_renew": true,
  "created_at": "2025-01-15T12:00:00Z",
  "updated_at": "2025-01-15T12:00:00Z"
}
```

---

#### 16. Update Subscription
```http
PATCH /subscriptions/{subscription_id}
Authorization: Bearer {access_token}
```

**Request Body**:
```json
{
  "plan_id": 3,
  "end_date": "2026-12-31"
}
```

**Response**: `200 OK`
```json
{
  "id": 10,
  "hostel_id": 1,
  "plan_id": 3,
  "status": "ACTIVE",
  "end_date": "2026-12-31",
  "updated_at": "2025-01-15T12:30:00Z"
}
```

---

### Platform Analytics

#### 17. Super Admin Dashboard
```http
GET /reports/dashboard
Authorization: Bearer {access_token}
```

**Response**: `200 OK`
```json
{
  "total_hostels": 50,
  "active_hostels": 45,
  "total_tenants": 2500,
  "total_revenue": 5000000.00,
  "active_subscriptions": 45,
  "pending_tickets": 12
}
```

---

## Hostel Admin Endpoints

### Room & Bed Management

#### 1. List Rooms
```http
GET /rooms?hostel_id=1
Authorization: Bearer {access_token}
```

**Note**: For Hostel Admin, `hostel_id` is automatically scoped to their hostel.

**Response**: `200 OK`
```json
[
  {
    "id": 1,
    "hostel_id": 1,
    "number": "101",
    "floor": 1,
    "room_type": "DOUBLE",
    "capacity": 2,
    "description": "Spacious double room with attached bathroom",
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-01-01T00:00:00Z"
  },
  {
    "id": 2,
    "hostel_id": 1,
    "number": "102",
    "floor": 1,
    "room_type": "SINGLE",
    "capacity": 1,
    "description": null,
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-01-01T00:00:00Z"
  }
]
```

---

#### 2. Get Room Details
```http
GET /rooms/{room_id}
Authorization: Bearer {access_token}
```

**Response**: `200 OK`
```json
{
  "id": 1,
  "hostel_id": 1,
  "number": "101",
  "floor": 1,
  "room_type": "DOUBLE",
  "capacity": 2,
  "description": "Spacious double room with attached bathroom",
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-01-01T00:00:00Z"
}
```

---

#### 3. Create Room
```http
POST /rooms
Authorization: Bearer {access_token}
```

**Request Body**:
```json
{
  "number": "201",
  "floor": 2,
  "room_type": "TRIPLE",
  "capacity": 3,
  "description": "Triple occupancy room"
}
```

**Note**: `hostel_id` is automatically set to admin's hostel.

**Response**: `201 Created`
```json
{
  "id": 3,
  "hostel_id": 1,
  "number": "201",
  "floor": 2,
  "room_type": "TRIPLE",
  "capacity": 3,
  "description": "Triple occupancy room",
  "created_at": "2025-01-15T13:00:00Z",
  "updated_at": "2025-01-15T13:00:00Z"
}
```

---

#### 4. Update Room
```http
PATCH /rooms/{room_id}
Authorization: Bearer {access_token}
```

**Request Body**:
```json
{
  "description": "Updated room description"
}
```

**Response**: `200 OK`
```json
{
  "id": 1,
  "description": "Updated room description",
  "updated_at": "2025-01-15T13:15:00Z"
}
```

---

#### 5. Delete Room (Soft Delete)
```http
DELETE /rooms/{room_id}
Authorization: Bearer {access_token}
```

**Response**: `200 OK`
```json
{
  "message": "Room deleted successfully"
}
```

---

#### 6. Restore Room
```http
POST /rooms/{room_id}/restore
Authorization: Bearer {access_token}
```

**Response**: `200 OK`
```json
{
  "id": 1,
  "is_deleted": false
}
```

---

#### 7. List Beds
```http
GET /beds?room_id=1
GET /beds?hostel_id=1
Authorization: Bearer {access_token}
```

**Query Parameters**:
- `room_id` (optional): Filter by specific room
- `hostel_id` (optional): Filter by hostel (auto-scoped for admins)

**Response**: `200 OK`
```json
[
  {
    "id": 1,
    "room_id": 1,
    "hostel_id": 1,
    "number": "A",
    "is_occupied": true,
    "tenant_id": 10,
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-01-10T08:00:00Z"
  },
  {
    "id": 2,
    "room_id": 1,
    "hostel_id": 1,
    "number": "B",
    "is_occupied": false,
    "tenant_id": null,
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-01-01T00:00:00Z"
  }
]
```

---

#### 8. Create Bed
```http
POST /beds
Authorization: Bearer {access_token}
```

**Request Body**:
```json
{
  "room_id": 1,
  "number": "C"
}
```

**Response**: `201 Created`
```json
{
  "id": 3,
  "room_id": 1,
  "hostel_id": 1,
  "number": "C",
  "is_occupied": false,
  "tenant_id": null,
  "created_at": "2025-01-15T13:30:00Z",
  "updated_at": "2025-01-15T13:30:00Z"
}
```

---

#### 9. Assign Bed to Tenant
```http
POST /beds/{bed_id}/assign
Authorization: Bearer {access_token}
```

**Request Body**:
```json
{
  "tenant_id": 10
}
```

**Response**: `200 OK`
```json
{
  "id": 2,
  "is_occupied": true,
  "tenant_id": 10,
  "updated_at": "2025-01-15T14:00:00Z"
}
```

---

#### 10. Vacate Bed
```http
POST /beds/{bed_id}/vacate
Authorization: Bearer {access_token}
```

**Response**: `200 OK`
```json
{
  "id": 2,
  "is_occupied": false,
  "tenant_id": null,
  "updated_at": "2025-01-15T14:30:00Z"
}
```

---

#### 11. Delete Bed (Soft Delete)
```http
DELETE /beds/{bed_id}
Authorization: Bearer {access_token}
```

**Response**: `200 OK`
```json
{
  "message": "Bed deleted successfully"
}
```

---

#### 12. Restore Bed
```http
POST /beds/{bed_id}/restore
Authorization: Bearer {access_token}
```

**Response**: `200 OK`
```json
{
  "id": 2,
  "is_deleted": false
}
```

---

### Tenant Management

#### 13. List Tenants
```http
GET /tenants?hostel_id=1
Authorization: Bearer {access_token}
```

**Response**: `200 OK`
```json
[
  {
    "id": 10,
    "user_id": 20,
    "hostel_id": 1,
    "full_name": "John Doe",
    "date_of_birth": "1995-05-15",
    "gender": "Male",
    "id_proof_type": "AADHAAR",
    "id_proof_number": "123456789012",
    "guardian_name": "Jane Doe",
    "guardian_phone": "+919876543210",
    "emergency_contact": "+919876543211",
    "current_bed_id": 1,
    "check_in_date": "2025-01-10",
    "check_out_date": null,
    "created_at": "2025-01-10T08:00:00Z",
    "updated_at": "2025-01-10T08:00:00Z"
  }
]
```

---

#### 14. Get Tenant Details
```http
GET /tenants/{tenant_id}
Authorization: Bearer {access_token}
```

**Response**: `200 OK`
```json
{
  "id": 10,
  "user_id": 20,
  "hostel_id": 1,
  "full_name": "John Doe",
  "date_of_birth": "1995-05-15",
  "gender": "Male",
  "id_proof_type": "AADHAAR",
  "id_proof_number": "123456789012",
  "guardian_name": "Jane Doe",
  "guardian_phone": "+919876543210",
  "emergency_contact": "+919876543211",
  "current_bed_id": 1,
  "check_in_date": "2025-01-10",
  "check_out_date": null,
  "created_at": "2025-01-10T08:00:00Z",
  "updated_at": "2025-01-10T08:00:00Z"
}
```

---

#### 15. Create Tenant Profile
```http
POST /tenants
Authorization: Bearer {access_token}
```

**Request Body**:
```json
{
  "user_id": 25,
  "hostel_id": 1,
  "full_name": "Alice Smith",
  "date_of_birth": "1998-03-20",
  "gender": "Female",
  "id_proof_type": "PASSPORT",
  "id_proof_number": "X1234567",
  "guardian_name": "Bob Smith",
  "guardian_phone": "+919876543212",
  "emergency_contact": "+919876543213"
}
```

**Response**: `201 Created`
```json
{
  "id": 11,
  "user_id": 25,
  "hostel_id": 1,
  "full_name": "Alice Smith",
  "date_of_birth": "1998-03-20",
  "gender": "Female",
  "current_bed_id": null,
  "created_at": "2025-01-15T15:00:00Z"
}
```

---

#### 16. Update Tenant Profile
```http
PATCH /tenants/{tenant_id}
Authorization: Bearer {access_token}
```

**Request Body**:
```json
{
  "emergency_contact": "+919999999999"
}
```

**Response**: `200 OK`
```json
{
  "id": 10,
  "emergency_contact": "+919999999999",
  "updated_at": "2025-01-15T15:15:00Z"
}
```

---

#### 17. Check-In Tenant
```http
POST /tenants/{tenant_id}/check-in
Authorization: Bearer {access_token}
```

**Request Body**:
```json
{
  "bed_id": 2,
  "check_in_date": "2025-01-16"
}
```

**Response**: `200 OK`
```json
{
  "id": 11,
  "current_bed_id": 2,
  "check_in_date": "2025-01-16",
  "updated_at": "2025-01-15T15:30:00Z"
}
```

---

#### 18. Check-Out Tenant
```http
POST /tenants/{tenant_id}/check-out
Authorization: Bearer {access_token}
```

**Request Body**:
```json
{
  "check_out_date": "2025-03-31",
  "notes": "End of semester"
}
```

**Response**: `200 OK`
```json
{
  "id": 10,
  "current_bed_id": null,
  "check_out_date": "2025-03-31",
  "updated_at": "2025-01-15T15:45:00Z"
}
```

---

#### 19. Delete Tenant Profile
```http
DELETE /tenants/{tenant_id}
Authorization: Bearer {access_token}
```

**Response**: `200 OK`
```json
{
  "message": "Tenant profile deleted successfully"
}
```

---

#### 20. Restore Tenant
```http
POST /tenants/{tenant_id}/restore
Authorization: Bearer {access_token}
```

**Response**: `200 OK`
```json
{
  "id": 10,
  "is_deleted": false
}
```

---

### Complaint Management

#### 21. List Complaints
```http
GET /complaints?hostel_id=1
Authorization: Bearer {access_token}
```

**Response**: `200 OK`
```json
[
  {
    "id": 1,
    "hostel_id": 1,
    "tenant_id": 10,
    "title": "AC not working",
    "description": "The AC in room 101 is not cooling properly",
    "category": "MAINTENANCE",
    "priority": "HIGH",
    "status": "OPEN",
    "assigned_to": null,
    "resolved_at": null,
    "created_at": "2025-01-15T10:00:00Z",
    "updated_at": "2025-01-15T10:00:00Z"
  }
]
```

---

#### 22. Get Complaint Details
```http
GET /complaints/{complaint_id}
Authorization: Bearer {access_token}
```

**Response**: `200 OK`
```json
{
  "id": 1,
  "hostel_id": 1,
  "tenant_id": 10,
  "title": "AC not working",
  "description": "The AC in room 101 is not cooling properly",
  "category": "MAINTENANCE",
  "priority": "HIGH",
  "status": "OPEN",
  "assigned_to": null,
  "resolved_at": null,
  "resolution_notes": null,
  "created_at": "2025-01-15T10:00:00Z",
  "updated_at": "2025-01-15T10:00:00Z"
}
```

---

#### 23. Update Complaint
```http
PATCH /complaints/{complaint_id}
Authorization: Bearer {access_token}
```

**Request Body**:
```json
{
  "status": "IN_PROGRESS",
  "priority": "URGENT",
  "assigned_to": 5
}
```

**Response**: `200 OK`
```json
{
  "id": 1,
  "status": "IN_PROGRESS",
  "priority": "URGENT",
  "assigned_to": 5,
  "updated_at": "2025-01-15T16:00:00Z"
}
```

---

#### 24. List Complaint Comments
```http
GET /complaints/{complaint_id}/comments
Authorization: Bearer {access_token}
```

**Response**: `200 OK`
```json
[
  {
    "id": 1,
    "complaint_id": 1,
    "user_id": 5,
    "comment": "Maintenance team assigned",
    "created_at": "2025-01-15T16:05:00Z"
  }
]
```

---

#### 25. Add Comment to Complaint
```http
POST /complaints/{complaint_id}/comments
Authorization: Bearer {access_token}
```

**Request Body**:
```json
{
  "comment": "AC technician will visit tomorrow"
}
```

**Response**: `200 OK`
```json
{
  "id": 2,
  "complaint_id": 1,
  "user_id": 5,
  "comment": "AC technician will visit tomorrow",
  "created_at": "2025-01-15T16:10:00Z"
}
```

---

### Notice Management

#### 26. List Notices
```http
GET /notices?hostel_id=1&active_only=true
Authorization: Bearer {access_token}
```

**Query Parameters**:
- `hostel_id` (required for SuperAdmin)
- `active_only` (optional): Show only active notices (default: true)

**Response**: `200 OK`
```json
[
  {
    "id": 1,
    "hostel_id": 1,
    "author_id": 5,
    "title": "Electricity Maintenance",
    "content": "Power will be off from 2 PM to 4 PM tomorrow",
    "priority": "URGENT",
    "published_at": "2025-01-15T10:00:00Z",
    "expires_at": "2025-01-17T00:00:00Z",
    "created_at": "2025-01-15T09:00:00Z",
    "updated_at": "2025-01-15T09:00:00Z"
  }
]
```

---

#### 27. Get Notice Details
```http
GET /notices/{notice_id}
Authorization: Bearer {access_token}
```

**Response**: `200 OK`
```json
{
  "id": 1,
  "hostel_id": 1,
  "author_id": 5,
  "title": "Electricity Maintenance",
  "content": "Power will be off from 2 PM to 4 PM tomorrow",
  "priority": "URGENT",
  "published_at": "2025-01-15T10:00:00Z",
  "expires_at": "2025-01-17T00:00:00Z",
  "created_at": "2025-01-15T09:00:00Z",
  "updated_at": "2025-01-15T09:00:00Z"
}
```

---

#### 28. Create Notice
```http
POST /notices
Authorization: Bearer {access_token}
```

**Request Body**:
```json
{
  "title": "Holiday Notice",
  "content": "Hostel will be closed for cleaning on Sunday",
  "priority": "NORMAL",
  "published_at": "2025-01-15T12:00:00Z",
  "expires_at": "2025-01-19T00:00:00Z"
}
```

**Response**: `201 Created`
```json
{
  "id": 2,
  "hostel_id": 1,
  "author_id": 5,
  "title": "Holiday Notice",
  "content": "Hostel will be closed for cleaning on Sunday",
  "priority": "NORMAL",
  "published_at": "2025-01-15T12:00:00Z",
  "expires_at": "2025-01-19T00:00:00Z",
  "created_at": "2025-01-15T11:00:00Z"
}
```

---

#### 29. Update Notice
```http
PATCH /notices/{notice_id}
Authorization: Bearer {access_token}
```

**Request Body**:
```json
{
  "priority": "HIGH",
  "expires_at": "2025-01-20T00:00:00Z"
}
```

**Response**: `200 OK`
```json
{
  "id": 1,
  "priority": "HIGH",
  "expires_at": "2025-01-20T00:00:00Z",
  "updated_at": "2025-01-15T17:00:00Z"
}
```

---

#### 30. Delete Notice
```http
DELETE /notices/{notice_id}
Authorization: Bearer {access_token}
```

**Response**: `200 OK`
```json
{
  "message": "Notice deleted successfully"
}
```

---

### Mess Menu Management

#### 31. List Mess Menus
```http
GET /mess-menu?hostel_id=1&menu_date=2025-01-16&meal_type=BREAKFAST
Authorization: Bearer {access_token}
```

**Query Parameters**:
- `hostel_id` (optional for SuperAdmin, auto-scoped for Admin)
- `menu_date` (optional): Specific date (default: today)
- `meal_type` (optional): BREAKFAST, LUNCH, SNACKS, DINNER
- `date_from` (optional): Range start
- `date_to` (optional): Range end

**Response**: `200 OK`
```json
[
  {
    "id": 1,
    "hostel_id": 1,
    "date": "2025-01-16",
    "meal_type": "BREAKFAST",
    "items": ["Idli", "Sambar", "Chutney", "Coffee"],
    "created_at": "2025-01-15T18:00:00Z",
    "updated_at": "2025-01-15T18:00:00Z"
  }
]
```

---

#### 32. Get Mess Menu
```http
GET /mess-menu/{menu_id}
Authorization: Bearer {access_token}
```

**Response**: `200 OK`
```json
{
  "id": 1,
  "hostel_id": 1,
  "date": "2025-01-16",
  "meal_type": "BREAKFAST",
  "items": ["Idli", "Sambar", "Chutney", "Coffee"],
  "created_at": "2025-01-15T18:00:00Z",
  "updated_at": "2025-01-15T18:00:00Z"
}
```

---

#### 33. Create Mess Menu
```http
POST /mess-menu
Authorization: Bearer {access_token}
```

**Request Body**:
```json
{
  "date": "2025-01-17",
  "meal_type": "LUNCH",
  "items": ["Rice", "Dal", "Roti", "Vegetable Curry", "Salad"]
}
```

**Response**: `201 Created`
```json
{
  "id": 2,
  "hostel_id": 1,
  "date": "2025-01-17",
  "meal_type": "LUNCH",
  "items": ["Rice", "Dal", "Roti", "Vegetable Curry", "Salad"],
  "created_at": "2025-01-15T18:30:00Z",
  "updated_at": "2025-01-15T18:30:00Z"
}
```

---

#### 34. Update Mess Menu
```http
PATCH /mess-menu/{menu_id}
Authorization: Bearer {access_token}
```

**Request Body**:
```json
{
  "items": ["Rice", "Dal", "Roti", "Paneer Curry", "Salad", "Curd"]
}
```

**Response**: `200 OK`
```json
{
  "id": 2,
  "items": ["Rice", "Dal", "Roti", "Paneer Curry", "Salad", "Curd"],
  "updated_at": "2025-01-15T19:00:00Z"
}
```

---

#### 35. Delete Mess Menu
```http
DELETE /mess-menu/{menu_id}
Authorization: Bearer {access_token}
```

**Response**: `200 OK`
```json
{
  "message": "Menu deleted successfully"
}
```

---

#### 36. Bulk Create Menus
```http
POST /mess-menu/bulk
Authorization: Bearer {access_token}
```

**Request Body**:
```json
{
  "menus": [
    {
      "date": "2025-01-18",
      "meal_type": "BREAKFAST",
      "items": ["Poha", "Tea"]
    },
    {
      "date": "2025-01-18",
      "meal_type": "LUNCH",
      "items": ["Rice", "Sambar", "Curd"]
    },
    {
      "date": "2025-01-18",
      "meal_type": "DINNER",
      "items": ["Roti", "Vegetable", "Dal"]
    }
  ]
}
```

**Response**: `200 OK`
```json
{
  "message": "Bulk operation completed: 3 created, 0 updated"
}
```

---

### Leave Management

#### 37. List Leave Applications
```http
GET /leaves?hostel_id=1&tenant_id=10
Authorization: Bearer {access_token}
```

**Query Parameters**:
- `hostel_id` (optional for SuperAdmin)
- `tenant_id` (optional): Filter by specific tenant

**Response**: `200 OK`
```json
[
  {
    "id": 1,
    "hostel_id": 1,
    "tenant_id": 10,
    "start_date": "2025-02-01",
    "end_date": "2025-02-05",
    "reason": "Family emergency",
    "status": "PENDING",
    "approver_id": null,
    "approved_at": null,
    "approver_notes": null,
    "created_at": "2025-01-15T20:00:00Z",
    "updated_at": "2025-01-15T20:00:00Z"
  }
]
```

---

#### 38. Get Leave Application
```http
GET /leaves/{leave_id}
Authorization: Bearer {access_token}
```

**Response**: `200 OK`
```json
{
  "id": 1,
  "hostel_id": 1,
  "tenant_id": 10,
  "start_date": "2025-02-01",
  "end_date": "2025-02-05",
  "reason": "Family emergency",
  "status": "PENDING",
  "approver_id": null,
  "approved_at": null,
  "approver_notes": null,
  "created_at": "2025-01-15T20:00:00Z",
  "updated_at": "2025-01-15T20:00:00Z"
}
```

---

#### 39. Approve/Reject Leave
```http
POST /leaves/{leave_id}/approve
Authorization: Bearer {access_token}
```

**Request Body**:
```json
{
  "approved": true,
  "notes": "Approved for family emergency"
}
```

**Response**: `200 OK`
```json
{
  "id": 1,
  "status": "APPROVED",
  "approver_id": 5,
  "approved_at": "2025-01-15T20:30:00Z",
  "approver_notes": "Approved for family emergency",
  "updated_at": "2025-01-15T20:30:00Z"
}
```

---

### Payment Management

#### 40. List Invoices
```http
GET /invoices?hostel_id=1&tenant_id=10
Authorization: Bearer {access_token}
```

**Query Parameters**:
- `hostel_id` (optional for SuperAdmin)
- `tenant_id` (optional): Filter by tenant

**Response**: `200 OK`
```json
[
  {
    "id": 1,
    "hostel_id": 1,
    "tenant_id": 10,
    "invoice_number": "INV-1-20250115-ABC123",
    "amount": 5000.00,
    "total_amount": 5000.00,
    "due_date": "2025-01-31",
    "status": "PENDING",
    "paid_amount": 0.00,
    "paid_at": null,
    "created_at": "2025-01-15T08:00:00Z",
    "updated_at": "2025-01-15T08:00:00Z"
  }
]
```

---

#### 41. Create Invoice
```http
POST /invoices
Authorization: Bearer {access_token}
```

**Request Body**:
```json
{
  "tenant_id": 10,
  "amount": 5000.00,
  "due_date": "2025-02-28",
  "notes": "Monthly rent for February"
}
```

**Response**: `201 Created`
```json
{
  "id": 2,
  "hostel_id": 1,
  "tenant_id": 10,
  "invoice_number": "INV-1-20250115-DEF456",
  "amount": 5000.00,
  "total_amount": 5000.00,
  "due_date": "2025-02-28",
  "status": "PENDING",
  "notes": "Monthly rent for February",
  "created_at": "2025-01-15T21:00:00Z"
}
```

---

#### 42. List Payments
```http
GET /payments?hostel_id=1&tenant_id=10
Authorization: Bearer {access_token}
```

**Response**: `200 OK`
```json
[
  {
    "id": 1,
    "invoice_id": 1,
    "hostel_id": 1,
    "tenant_id": 10,
    "amount": 5000.00,
    "status": "SUCCESS",
    "gateway": "razorpay",
    "transaction_id": "pay_ABC123",
    "receipt_number": "RCP-1-20250116-XYZ789",
    "payment_method": "UPI",
    "paid_at": "2025-01-16T10:00:00Z",
    "created_at": "2025-01-16T09:50:00Z"
  }
]
```

---

### Analytics & Reports

#### 43. Hostel Dashboard
```http
GET /hostels/{hostel_id}/dashboard
Authorization: Bearer {access_token}
```

**Response**: `200 OK`
```json
{
  "hostel_id": 1,
  "hostel_name": "Luxury Hostel",
  "total_rooms": 20,
  "total_beds": 50,
  "occupied_beds": 42,
  "occupancy_rate": 84.0,
  "total_tenants": 42,
  "pending_fees": 25000.00,
  "total_revenue": 500000.00,
  "pending_complaints": 3,
  "active_notices": 2
}
```

---

#### 44. Get Hostel Dashboard (Alternate)
```http
GET /reports/hostel-dashboard?hostel_id=1
Authorization: Bearer {access_token}
```

**Response**: Same as above

---

#### 45. Occupancy Report
```http
GET /reports/occupancy?hostel_id=1&date_from=2025-01-01&date_to=2025-01-31
Authorization: Bearer {access_token}
```

**Response**: `200 OK`
```json
{
  "hostel_id": 1,
  "date_from": "2025-01-01",
  "date_to": "2025-01-31",
  "total_beds": 50,
  "occupied_beds": 42,
  "available_beds": 8,
  "occupancy_rate": 84.0
}
```

---

#### 46. Income Report
```http
GET /reports/income?hostel_id=1&date_from=2025-01-01&date_to=2025-01-31
Authorization: Bearer {access_token}
```

**Response**: `200 OK`
```json
{
  "hostel_id": 1,
  "date_from": "2025-01-01",
  "date_to": "2025-01-31",
  "total_revenue": 250000.00,
  "total_payments": 50,
  "pending_fees": 25000.00
}
```

---

## Tenant Endpoints

### Profile Management

#### 1. Get My Profile
```http
GET /auth/me
Authorization: Bearer {access_token}
```

**Response**: `200 OK`
```json
{
  "id": 20,
  "email": "tenant@example.com",
  "phone": "+919876543210",
  "role": "TENANT",
  "hostel_id": 1,
  "is_active": true,
  "is_verified": true,
  "last_login": "2025-01-16T08:00:00Z",
  "created_at": "2025-01-10T00:00:00Z"
}
```

---

#### 2. Get My Tenant Profile
```http
GET /tenants/{tenant_id}
Authorization: Bearer {access_token}
```

**Note**: Tenant can only access their own profile

**Response**: `200 OK`
```json
{
  "id": 10,
  "user_id": 20,
  "hostel_id": 1,
  "full_name": "John Doe",
  "date_of_birth": "1995-05-15",
  "gender": "Male",
  "current_bed_id": 1,
  "check_in_date": "2025-01-10",
  "check_out_date": null,
  "created_at": "2025-01-10T08:00:00Z"
}
```

---

#### 3. Update My Profile
```http
PATCH /tenants/{tenant_id}
Authorization: Bearer {access_token}
```

**Request Body**:
```json
{
  "emergency_contact": "+919999999999"
}
```

**Response**: `200 OK`
```json
{
  "id": 10,
  "emergency_contact": "+919999999999",
  "updated_at": "2025-01-16T09:00:00Z"
}
```

---

### Complaint Management

#### 4. List My Complaints
```http
GET /complaints
Authorization: Bearer {access_token}
```

**Note**: Automatically filtered to tenant's complaints

**Response**: `200 OK`
```json
[
  {
    "id": 1,
    "tenant_id": 10,
    "title": "AC not working",
    "description": "The AC in my room is not cooling",
    "category": "MAINTENANCE",
    "priority": "HIGH",
    "status": "IN_PROGRESS",
    "assigned_to": 5,
    "created_at": "2025-01-15T10:00:00Z",
    "updated_at": "2025-01-15T16:00:00Z"
  }
]
```

---

#### 5. Get Complaint Details
```http
GET /complaints/{complaint_id}
Authorization: Bearer {access_token}
```

**Response**: `200 OK`
```json
{
  "id": 1,
  "tenant_id": 10,
  "title": "AC not working",
  "description": "The AC in my room is not cooling",
  "category": "MAINTENANCE",
  "priority": "HIGH",
  "status": "IN_PROGRESS",
  "assigned_to": 5,
  "resolved_at": null,
  "created_at": "2025-01-15T10:00:00Z",
  "updated_at": "2025-01-15T16:00:00Z"
}
```

---

#### 6. Create Complaint
```http
POST /complaints
Authorization: Bearer {access_token}
```

**Request Body**:
```json
{
  "title": "Water leakage",
  "description": "Water is leaking from bathroom ceiling",
  "category": "MAINTENANCE",
  "priority": "URGENT"
}
```

**Response**: `201 Created`
```json
{
  "id": 2,
  "tenant_id": 10,
  "hostel_id": 1,
  "title": "Water leakage",
  "description": "Water is leaking from bathroom ceiling",
  "category": "MAINTENANCE",
  "priority": "URGENT",
  "status": "OPEN",
  "created_at": "2025-01-16T10:00:00Z"
}
```

---

#### 7. Get Complaint Comments
```http
GET /complaints/{complaint_id}/comments
Authorization: Bearer {access_token}
```

**Response**: `200 OK`
```json
[
  {
    "id": 1,
    "complaint_id": 1,
    "user_id": 5,
    "comment": "Maintenance team assigned",
    "created_at": "2025-01-15T16:05:00Z"
  },
  {
    "id": 2,
    "complaint_id": 1,
    "user_id": 20,
    "comment": "Thank you for the quick response",
    "created_at": "2025-01-15T16:15:00Z"
  }
]
```

---

#### 8. Add Comment to Complaint
```http
POST /complaints/{complaint_id}/comments
Authorization: Bearer {access_token}
```

**Request Body**:
```json
{
  "comment": "Issue persists. Please check again."
}
```

**Response**: `200 OK`
```json
{
  "id": 3,
  "complaint_id": 1,
  "user_id": 20,
  "comment": "Issue persists. Please check again.",
  "created_at": "2025-01-16T11:00:00Z"
}
```

---

### Notice & Announcements

#### 9. List Active Notices
```http
GET /notices?active_only=true
Authorization: Bearer {access_token}
```

**Note**: Automatically scoped to tenant's hostel

**Response**: `200 OK`
```json
[
  {
    "id": 1,
    "title": "Electricity Maintenance",
    "content": "Power will be off from 2 PM to 4 PM tomorrow",
    "priority": "URGENT",
    "published_at": "2025-01-15T10:00:00Z",
    "expires_at": "2025-01-17T00:00:00Z",
    "created_at": "2025-01-15T09:00:00Z"
  }
]
```

---

#### 10. Get Notice Details
```http
GET /notices/{notice_id}
Authorization: Bearer {access_token}
```

**Response**: `200 OK`
```json
{
  "id": 1,
  "title": "Electricity Maintenance",
  "content": "Power will be off from 2 PM to 4 PM tomorrow. Please plan accordingly.",
  "priority": "URGENT",
  "published_at": "2025-01-15T10:00:00Z",
  "expires_at": "2025-01-17T00:00:00Z"
}
```

---

### Mess Menu

#### 11. Get Today's Mess Menu
```http
GET /mess-menu
Authorization: Bearer {access_token}
```

**Response**: `200 OK`
```json
[
  {
    "id": 1,
    "date": "2025-01-16",
    "meal_type": "BREAKFAST",
    "items": ["Idli", "Sambar", "Chutney", "Coffee"]
  },
  {
    "id": 2,
    "date": "2025-01-16",
    "meal_type": "LUNCH",
    "items": ["Rice", "Dal", "Roti", "Vegetable Curry", "Salad"]
  },
  {
    "id": 3,
    "date": "2025-01-16",
    "meal_type": "DINNER",
    "items": ["Roti", "Paneer Curry", "Dal", "Curd"]
  }
]
```

---

#### 12. Get Mess Menu for Date
```http
GET /mess-menu?menu_date=2025-01-17&meal_type=LUNCH
Authorization: Bearer {access_token}
```

**Response**: `200 OK`
```json
[
  {
    "id": 4,
    "date": "2025-01-17",
    "meal_type": "LUNCH",
    "items": ["Rice", "Sambar", "Roti", "Vegetable", "Papad"]
  }
]
```

---

### Leave Applications

#### 13. List My Leave Applications
```http
GET /leaves
Authorization: Bearer {access_token}
```

**Response**: `200 OK`
```json
[
  {
    "id": 1,
    "tenant_id": 10,
    "start_date": "2025-02-01",
    "end_date": "2025-02-05",
    "reason": "Family emergency",
    "status": "APPROVED",
    "approver_id": 5,
    "approved_at": "2025-01-15T20:30:00Z",
    "approver_notes": "Approved",
    "created_at": "2025-01-15T20:00:00Z"
  }
]
```

---

#### 14. Get Leave Application
```http
GET /leaves/{leave_id}
Authorization: Bearer {access_token}
```

**Response**: `200 OK`
```json
{
  "id": 1,
  "tenant_id": 10,
  "start_date": "2025-02-01",
  "end_date": "2025-02-05",
  "reason": "Family emergency",
  "status": "APPROVED",
  "approver_id": 5,
  "approved_at": "2025-01-15T20:30:00Z",
  "approver_notes": "Approved",
  "created_at": "2025-01-15T20:00:00Z"
}
```

---

#### 15. Apply for Leave
```http
POST /leaves
Authorization: Bearer {access_token}
```

**Request Body**:
```json
{
  "start_date": "2025-03-01",
  "end_date": "2025-03-07",
  "reason": "Semester break - going home"
}
```

**Response**: `201 Created`
```json
{
  "id": 2,
  "tenant_id": 10,
  "hostel_id": 1,
  "start_date": "2025-03-01",
  "end_date": "2025-03-07",
  "reason": "Semester break - going home",
  "status": "PENDING",
  "created_at": "2025-01-16T12:00:00Z"
}
```

---

### Payments & Invoices

#### 16. List My Invoices
```http
GET /invoices
Authorization: Bearer {access_token}
```

**Response**: `200 OK`
```json
[
  {
    "id": 1,
    "tenant_id": 10,
    "invoice_number": "INV-1-20250115-ABC123",
    "amount": 5000.00,
    "total_amount": 5000.00,
    "due_date": "2025-01-31",
    "status": "PAID",
    "paid_amount": 5000.00,
    "paid_at": "2025-01-16T10:00:00Z",
    "created_at": "2025-01-15T08:00:00Z"
  },
  {
    "id": 2,
    "tenant_id": 10,
    "invoice_number": "INV-1-20250115-DEF456",
    "amount": 5000.00,
    "total_amount": 5000.00,
    "due_date": "2025-02-28",
    "status": "PENDING",
    "paid_amount": 0.00,
    "paid_at": null,
    "created_at": "2025-01-15T21:00:00Z"
  }
]
```

---

#### 17. Initiate Payment
```http
POST /payments
Authorization: Bearer {access_token}
```

**Request Body**:
```json
{
  "invoice_id": 2,
  "amount": 5000.00,
  "gateway": "razorpay"
}
```

**Response**: `201 Created`
```json
{
  "id": 2,
  "invoice_id": 2,
  "tenant_id": 10,
  "amount": 5000.00,
  "status": "PROCESSING",
  "gateway": "razorpay",
  "transaction_id": "order_ABC123XYZ",
  "created_at": "2025-01-16T13:00:00Z"
}
```

---

#### 18. List My Payments
```http
GET /payments
Authorization: Bearer {access_token}
```

**Response**: `200 OK`
```json
[
  {
    "id": 1,
    "invoice_id": 1,
    "tenant_id": 10,
    "amount": 5000.00,
    "status": "SUCCESS",
    "gateway": "razorpay",
    "transaction_id": "pay_ABC123",
    "receipt_number": "RCP-1-20250116-XYZ789",
    "payment_method": "UPI",
    "paid_at": "2025-01-16T10:00:00Z",
    "created_at": "2025-01-16T09:50:00Z"
  }
]
```

---

#### 19. Download Payment Receipt
```http
GET /payments/{payment_id}/receipt
Authorization: Bearer {access_token}
```

**Response**: `200 OK`
```json
{
  "receipt_number": "RCP-1-20250116-XYZ789",
  "payment_id": 1,
  "amount": 5000.00,
  "status": "SUCCESS",
  "paid_at": "2025-01-16T10:00:00Z"
}
```

---

### Notifications

#### 20. List My Notifications
```http
GET /notifications?is_read=false&page=1&page_size=20
Authorization: Bearer {access_token}
```

**Query Parameters**:
- `is_read` (optional): Filter by read status
- `page` (optional): Page number
- `page_size` (optional): Items per page

**Response**: `200 OK`
```json
{
  "items": [
    {
      "id": 1,
      "user_id": 20,
      "title": "Payment Successful",
      "message": "Your payment of ₹5000 has been received",
      "notification_type": "SUCCESS",
      "is_read": false,
      "read_at": null,
      "sent_at": "2025-01-16T10:05:00Z",
      "created_at": "2025-01-16T10:05:00Z"
    },
    {
      "id": 2,
      "user_id": 20,
      "title": "New Notice",
      "message": "Electricity maintenance scheduled for tomorrow",
      "notification_type": "INFO",
      "is_read": false,
      "read_at": null,
      "sent_at": "2025-01-15T10:00:00Z",
      "created_at": "2025-01-15T10:00:00Z"
    }
  ],
  "total": 15,
  "page": 1,
  "page_size": 20,
  "total_pages": 1
}
```

---

#### 21. Get Notification Count
```http
GET /notifications/count
Authorization: Bearer {access_token}
```

**Response**: `200 OK`
```json
{
  "total": 15,
  "unread": 8
}
```

---

#### 22. Mark Notification as Read
```http
PATCH /notifications/{notification_id}
Authorization: Bearer {access_token}
```

**Response**: `200 OK`
```json
{
  "id": 1,
  "is_read": true,
  "read_at": "2025-01-16T14:00:00Z"
}
```

---

#### 23. Mark All Notifications as Read
```http
POST /notifications/mark-all-read
Authorization: Bearer {access_token}
```

**Response**: `200 OK`
```json
{
  "message": "All notifications marked as read"
}
```

---

#### 24. Register Device Token (Push Notifications)
```http
POST /notifications/device-tokens
Authorization: Bearer {access_token}
```

**Request Body**:
```json
{
  "token": "fcm_device_token_abc123xyz",
  "platform": "ANDROID"
}
```

**Platforms**: `IOS`, `ANDROID`, `WEB`

**Response**: `201 Created`
```json
{
  "id": 1,
  "user_id": 20,
  "token": "fcm_device_token_abc123xyz",
  "platform": "ANDROID",
  "is_active": true,
  "created_at": "2025-01-16T15:00:00Z"
}
```

---

#### 25. List My Device Tokens
```http
GET /notifications/device-tokens
Authorization: Bearer {access_token}
```

**Response**: `200 OK`
```json
[
  {
    "id": 1,
    "user_id": 20,
    "token": "fcm_device_token_abc123xyz",
    "platform": "ANDROID",
    "is_active": true,
    "created_at": "2025-01-16T15:00:00Z"
  }
]
```

---

#### 26. Delete Device Token
```http
DELETE /notifications/device-tokens/{token_id}
Authorization: Bearer {access_token}
```

**Response**: `200 OK`
```json
{
  "message": "Device token deactivated successfully"
}
```

---

## Visitor Endpoints

**Note**: Visitors have **read-only access** to limited public information.

### Hostel Information

#### 1. List Available Hostels
```http
GET /visitor/hostels
Authorization: Bearer {access_token}
```

**Note**: Visitors can only see their assigned hostel

**Response**: `200 OK`
```json
[
  {
    "id": 1,
    "name": "Luxury Hostel",
    "code": "HOSTELLUXURY",
    "address": "123 Main Street",
    "city": "Mumbai",
    "state": "Maharashtra",
    "phone": "+912212345678",
    "email": "info@luxuryhostel.com",
    "is_active": true
  }
]
```

---

#### 2. Get Hostel Details
```http
GET /visitor/hostels/{hostel_id}
Authorization: Bearer {access_token}
```

**Response**: `200 OK`
```json
{
  "id": 1,
  "name": "Luxury Hostel",
  "code": "HOSTELLUXURY",
  "address": "123 Main Street",
  "city": "Mumbai",
  "state": "Maharashtra",
  "pincode": "400001",
  "phone": "+912212345678",
  "email": "info@luxuryhostel.com",
  "is_active": true
}
```

---

### Public Notices

#### 3. List Public Notices
```http
GET /visitor/notices
Authorization: Bearer {access_token}
```

**Response**: `200 OK`
```json
[
  {
    "id": 1,
    "title": "Electricity Maintenance",
    "content": "Power will be off from 2 PM to 4 PM tomorrow",
    "priority": "URGENT",
    "published_at": "2025-01-15T10:00:00Z",
    "expires_at": "2025-01-17T00:00:00Z"
  }
]
```

---

#### 4. Get Notice Details
```http
GET /visitor/notices/{notice_id}
Authorization: Bearer {access_token}
```

**Response**: `200 OK`
```json
{
  "id": 1,
  "title": "Electricity Maintenance",
  "content": "Power will be off from 2 PM to 4 PM tomorrow. Please plan accordingly.",
  "priority": "URGENT",
  "published_at": "2025-01-15T10:00:00Z",
  "expires_at": "2025-01-17T00:00:00Z"
}
```

---

### Mess Menu

#### 5. Get Public Mess Menu
```http
GET /visitor/mess-menu?menu_date=2025-01-16&meal_type=LUNCH
Authorization: Bearer {access_token}
```

**Response**: `200 OK`
```json
[
  {
    "id": 2,
    "date": "2025-01-16",
    "meal_type": "LUNCH",
    "items": ["Rice", "Dal", "Roti", "Vegetable Curry", "Salad"]
  }
]
```

---

### Visitor Information

#### 6. Get Visitor Account Info
```http
GET /visitor/info
Authorization: Bearer {access_token}
```

**Response**: `200 OK`
```json
{
  "user_id": 50,
  "role": "VISITOR",
  "hostel_id": 1,
  "is_active": true,
  "visitor_expires_at": "2025-02-15T00:00:00Z",
  "is_expired": false,
  "permissions": {
    "read": ["public_notices", "public_mess_menu", "hostel_info"],
    "write": [],
    "delete": [],
    "admin": []
  }
}
```

---

## Common Models

### User Roles
```typescript
enum UserRole {
  SUPER_ADMIN = "SUPER_ADMIN",
  HOSTEL_ADMIN = "HOSTEL_ADMIN",
  TENANT = "TENANT",
  VISITOR = "VISITOR"
}
```

---

### Room Types
```typescript
enum RoomType {
  SINGLE = "SINGLE",
  DOUBLE = "DOUBLE",
  TRIPLE = "TRIPLE",
  DORMITORY = "DORMITORY"
}
```

---

### Complaint Status
```typescript
enum ComplaintStatus {
  OPEN = "OPEN",
  IN_PROGRESS = "IN_PROGRESS",
  RESOLVED = "RESOLVED",
  CLOSED = "CLOSED",
  REJECTED = "REJECTED"
}

enum ComplaintCategory {
  MAINTENANCE = "MAINTENANCE",
  CLEANLINESS = "CLEANLINESS",
  FOOD = "FOOD",
  ELECTRICITY = "ELECTRICITY",
  WATER = "WATER",
  SECURITY = "SECURITY",
  OTHER = "OTHER"
}

enum ComplaintPriority {
  LOW = "LOW",
  MEDIUM = "MEDIUM",
  HIGH = "HIGH",
  URGENT = "URGENT"
}
```

---

### Notice Priority
```typescript
enum NoticePriority {
  LOW = "LOW",
  NORMAL = "NORMAL",
  HIGH = "HIGH",
  URGENT = "URGENT"
}
```

---

### Meal Types
```typescript
enum MealType {
  BREAKFAST = "BREAKFAST",
  LUNCH = "LUNCH",
  SNACKS = "SNACKS",
  DINNER = "DINNER"
}
```

---

### Leave Status
```typescript
enum LeaveStatus {
  PENDING = "PENDING",
  APPROVED = "APPROVED",
  REJECTED = "REJECTED",
  CANCELLED = "CANCELLED"
}
```

---

### Payment Status
```typescript
enum PaymentStatus {
  PENDING = "PENDING",
  PROCESSING = "PROCESSING",
  SUCCESS = "SUCCESS",
  FAILED = "FAILED",
  REFUNDED = "REFUNDED"
}
```

---

### Invoice Status
```typescript
enum InvoiceStatus {
  PENDING = "PENDING",
  PAID = "PAID",
  PARTIAL = "PARTIAL",
  OVERDUE = "OVERDUE",
  CANCELLED = "CANCELLED"
}
```

---

## Error Responses

### Standard Error Format
```json
{
  "error": "Error message",
  "detail": "Detailed error description",
  "status_code": 400
}
```

---

### Common HTTP Status Codes

- **200 OK**: Successful request
- **201 Created**: Resource created successfully
- **400 Bad Request**: Invalid request parameters
- **401 Unauthorized**: Authentication required or failed
- **403 Forbidden**: Insufficient permissions
- **404 Not Found**: Resource not found
- **409 Conflict**: Resource conflict (duplicate)
- **422 Unprocessable Entity**: Validation error
- **429 Too Many Requests**: Rate limit exceeded
- **500 Internal Server Error**: Server error

---

### Example Error Responses

#### Authentication Error
```json
{
  "error": "Invalid authentication credentials",
  "status_code": 401
}
```

#### Authorization Error
```json
{
  "error": "Insufficient permissions",
  "detail": "You don't have permission to access this resource",
  "status_code": 403
}
```

#### Validation Error
```json
{
  "error": "Validation error",
  "detail": "Invalid email format",
  "status_code": 422
}
```

#### Not Found Error
```json
{
  "error": "Resource not found",
  "detail": "Hostel with ID 999 not found",
  "status_code": 404
}
```

#### Conflict Error
```json
{
  "error": "Resource conflict",
  "detail": "Email already registered",
  "status_code": 409
}
```

---

## Rate Limiting

### Standard Users
- **Per Minute**: 60 requests
- **Per Hour**: 1000 requests
- **Per Day**: 10,000 requests

### Visitors
- **Per Minute**: 10 requests
- **Per Hour**: 100 requests
- **Per Day**: 500 requests

### Rate Limit Headers
```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1642345678
```

---

## Pagination

All list endpoints support pagination:

**Query Parameters**:
- `page` (default: 1)
- `page_size` (default: 20, max: 100)

**Response Format**:
```json
{
  "items": [...],
  "total": 150,
  "page": 1,
  "page_size": 20,
  "total_pages": 8
}
```

---

## Authentication Flow

### 1. Email/Password Login
```
1. POST /auth/login → Get tokens
2. Use access_token for API calls
3. When access_token expires → POST /auth/refresh
4. On logout → POST /auth/logout
```

### 2. Phone/OTP Login
```
1. POST /auth/login/otp/request → Receive OTP
2. POST /auth/login/otp/verify → Get tokens
3. Use access_token for API calls
```

### 3. Token Refresh
```
1. Access token expires after 30 minutes
2. POST /auth/refresh with refresh_token
3. Get new access_token
4. Refresh token expires after 7 days
```

---

## Permission Matrix

| Endpoint Category | SuperAdmin | HostelAdmin | Tenant | Visitor |
|-------------------|------------|-------------|--------|---------|
| **Hostels** |
| List/Create/Update/Delete | ✅ | ❌ | ❌ | ❌ |
| View Own Hostel | ✅ | ✅ | ✅ | ✅ (Read-only) |
| **Rooms & Beds** |
| Manage Rooms/Beds | ✅ | ✅ | ❌ | ❌ |
| View Rooms | ✅ | ✅ | ✅ (Own room) | ❌ |
| **Tenants** |
| Manage All Tenants | ✅ | ❌ | ❌ | ❌ |
| Manage Hostel Tenants | ✅ | ✅ | ❌ | ❌ |
| View Own Profile | ✅ | ✅ | ✅ | ❌ |
| **Complaints** |
| View All | ✅ | ✅ (Hostel) | ❌ | ❌ |
| Create | ✅ | ✅ | ✅ | ❌ |
| Update/Resolve | ✅ | ✅ | ❌ | ❌ |
| **Notices** |
| Create/Update/Delete | ✅ | ✅ | ❌ | ❌ |
| View | ✅ | ✅ | ✅ | ✅ (Public only) |
| **Mess Menu** |
| Manage | ✅ | ✅ | ❌ | ❌ |
| View | ✅ | ✅ | ✅ | ✅ |
| **Payments** |
| View All | ✅ | ✅ (Hostel) | ❌ | ❌ |
| Make Payment | ❌ | ❌ | ✅ | ❌ |
| **Leave Applications** |
| Approve/Reject | ✅ | ✅ | ❌ | ❌ |
| Apply | ❌ | ❌ | ✅ | ❌ |
| **Analytics** |
| Platform Dashboard | ✅ | ❌ | ❌ | ❌ |
| Hostel Dashboard | ✅ | ✅ | ❌ | ❌ |
| **Subscriptions** |
| Manage | ✅ | ❌ | ❌ | ❌ |
| View | ✅ | ✅ (Own) | ❌ | ❌ |

---

## Best Practices

### 1. Authentication
- Always include `Authorization: Bearer {token}` header
- Refresh tokens before expiry
- Logout when done to revoke tokens

### 2. Error Handling
- Check HTTP status codes
- Parse error response for details
- Implement retry logic for 5xx errors

### 3. Rate Limiting
- Monitor rate limit headers
- Implement exponential backoff
- Cache frequently accessed data

### 4. Data Validation
- Validate inputs before sending
- Handle validation errors gracefully
- Follow enum constraints

### 5. Pagination
- Always paginate list endpoints
- Use reasonable page sizes
- Cache results when appropriate

---

This comprehensive API documentation covers all endpoints across the four user roles in the hostel management system. Each endpoint includes request/response formats, authentication requirements, and permission boundaries.