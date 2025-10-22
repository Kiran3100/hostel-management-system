# Hostel Management System - API Documentation (Ordered Endpoints)

## System Overview

**Base URL**: `/api/v1`  
**Authentication**: JWT Bearer Token  
**Date Format**: ISO 8601 (YYYY-MM-DD / YYYY-MM-DDTHH:mm:ssZ)  
**Currency**: INR (Indian Rupee)

---

## Table of Contents

1. [Authentication Endpoints (Public)](#authentication-endpoints-public) - Endpoints 1-8
2. [SuperAdmin Endpoints](#superadmin-endpoints) - Endpoints 9-25
3. [Hostel Admin Endpoints](#hostel-admin-endpoints) - Endpoints 26-71
4. [Tenant Endpoints](#tenant-endpoints) - Endpoints 72-97
5. [Visitor Endpoints](#visitor-endpoints) - Endpoints 98-103
6. [Common Models & Error Responses](#common-models--error-responses)

---

## Authentication Endpoints (Public)

### Endpoint 1: Register User
```http
POST /auth/register
```
**Access**: Admin-controlled (creates users for system)

**Request Body**:
```json
{
  "email": "admin@hostel.com",
  "phone": "919876543210",
  "password": "SecurePass123",
  "role": "HOSTEL_ADMIN",
  "hostel_code": "HOSTELLUXURY"
}
```

**Response**: `201 Created`
```json
{
  "id": 5,
  "email": "admin@hostel.com",
  "phone": "+919876543210",
  "role": "HOSTEL_ADMIN",
  "hostel_code": "HOSTELLUXURY",
  "is_active": true,
  "is_verified": true,
  "created_at": "2025-01-15T10:30:00Z"
}
```

---

### Endpoint 2: Login (Email/Password)
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

### Endpoint 3: Request OTP (Phone Login)
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

### Endpoint 4: Verify OTP
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

### Endpoint 5: Refresh Access Token
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

### Endpoint 6: Get Current User Profile
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

### Endpoint 7: Change Password
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

### Endpoint 8: Logout
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

## SuperAdmin Endpoints

### Hostel Management

### Endpoint 9: List All Hostels
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

### Endpoint 10: Get Hostel Details
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

### Endpoint 11: Create Hostel
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

### Endpoint 12: Update Hostel
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

### Endpoint 13: Delete Hostel (Soft Delete)
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

### Endpoint 14: Restore Deleted Hostel
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

### Endpoint 15: List All Users
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

### Endpoint 16: Get User Details
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

### Endpoint 17: Update User
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

### Endpoint 18: Delete User (Soft Delete)
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

### Endpoint 19: Restore Deleted User
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

### Endpoint 20: List Subscription Plans
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
  }
]
```

---

### Endpoint 21: List All Subscriptions
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

### Endpoint 22: Get Subscription Details
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

### Endpoint 23: Create Subscription
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

### Endpoint 24: Update Subscription
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

### Endpoint 25: Super Admin Dashboard
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

### Endpoint 26: List Rooms
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
  }
]
```

---

### Endpoint 27: Get Room Details
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

### Endpoint 28: Create Room
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

### Endpoint 29: Update Room
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
  "updated_at": "2025-01-15T13:30:00Z"
}
```

---

### Endpoint 30: Delete Room (Soft Delete)
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

### Endpoint 31: Restore Room
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

### Endpoint 32: List Beds in Room
```http
GET /rooms/{room_id}/beds
Authorization: Bearer {access_token}
```

**Response**: `200 OK`
```json
[
  {
    "id": 1,
    "room_id": 1,
    "bed_number": "A",
    "is_occupied": true,
    "current_tenant_id": 10,
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-01-10T08:00:00Z"
  },
  {
    "id": 2,
    "room_id": 1,
    "bed_number": "B",
    "is_occupied": false,
    "current_tenant_id": null,
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-01-01T00:00:00Z"
  }
]
```

---

### Endpoint 33: Get Bed Details
```http
GET /beds/{bed_id}
Authorization: Bearer {access_token}
```

**Response**: `200 OK`
```json
{
  "id": 1,
  "room_id": 1,
  "bed_number": "A",
  "is_occupied": true,
  "current_tenant_id": 10,
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-01-10T08:00:00Z"
}
```

---

### Endpoint 34: Create Bed
```http
POST /beds
Authorization: Bearer {access_token}
```

**Request Body**:
```json
{
  "room_id": 1,
  "bed_number": "C"
}
```

**Response**: `201 Created`
```json
{
  "id": 3,
  "room_id": 1,
  "bed_number": "C",
  "is_occupied": false,
  "current_tenant_id": null,
  "created_at": "2025-01-15T14:00:00Z",
  "updated_at": "2025-01-15T14:00:00Z"
}
```

---

### Endpoint 35: Update Bed
```http
PATCH /beds/{bed_id}
Authorization: Bearer {access_token}
```

**Request Body**:
```json
{
  "bed_number": "D"
}
```

**Response**: `200 OK`
```json
{
  "id": 3,
  "bed_number": "D",
  "updated_at": "2025-01-15T14:30:00Z"
}
```

---

### Endpoint 36: Delete Bed (Soft Delete)
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

### Endpoint 37: Restore Bed
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

### Endpoint 38: List Tenants
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

### Endpoint 39: Get Tenant Details
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

### Endpoint 40: Create Tenant Profile
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

### Endpoint 41: Update Tenant Profile
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

### Endpoint 42: Check-In Tenant
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

### Endpoint 43: Check-Out Tenant
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

### Endpoint 44: Delete Tenant Profile
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

### Endpoint 45: Restore Tenant
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

### Endpoint 46: List Complaints
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

### Endpoint 47: Get Complaint Details
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

### Endpoint 48: Update Complaint
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

### Endpoint 49: List Complaint Comments
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

### Endpoint 50: Add Comment to Complaint
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

### Endpoint 51: List Notices
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

### Endpoint 52: Get Notice Details
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

### Endpoint 53: Create Notice
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

### Endpoint 54: Update Notice
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

### Endpoint 55: Delete Notice
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

### Endpoint 56: List Mess Menus
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

### Endpoint 57: Get Mess Menu
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

### Endpoint 58: Create Mess Menu
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

### Endpoint 59: Update Mess Menu
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

### Endpoint 60: Delete Mess Menu
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

### Endpoint 61: Bulk Create Menus
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

### Endpoint 62: List Leave Applications
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

### Endpoint 63: Get Leave Application
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

### Endpoint 64: Approve/Reject Leave
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

### Endpoint 65: List Invoices
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

### Endpoint 66: Create Invoice
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

### Endpoint 67: List Payments
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

### Endpoint 68: Hostel Dashboard
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

### Endpoint 69: Occupancy Report
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

### Endpoint 70: Income Report
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
  "total_income": 210000.00,
  "pending_payments": 25000.00,
  "paid_payments": 185000.00,
  "payment_methods": {
    "UPI": 120000.00,
    "CARD": 50000.00,
    "CASH": 15000.00
  }
}
```

---

### Endpoint 71: Complaints Report
```http
GET /reports/complaints?hostel_id=1&date_from=2025-01-01&date_to=2025-01-31
Authorization: Bearer {access_token}
```

**Response**: `200 OK`
```json
{
  "hostel_id": 1,
  "date_from": "2025-01-01",
  "date_to": "2025-01-31",
  "total_complaints": 15,
  "open": 3,
  "in_progress": 5,
  "resolved": 7,
  "by_category": {
    "MAINTENANCE": 8,
    "CLEANLINESS": 3,
    "FOOD": 2,
    "OTHER": 2
  }
}
```

---

## Tenant Endpoints

### Profile & Room

### Endpoint 72: Get My Profile
```http
GET /tenant/profile
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
  "created_at": "2025-01-10T08:00:00Z"
}
```

---

### Endpoint 73: Update My Profile
```http
PATCH /tenant/profile
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
  "updated_at": "2025-01-16T10:00:00Z"
}
```

---

### Endpoint 74: Get My Room Details
```http
GET /tenant/room
Authorization: Bearer {access_token}
```

**Response**: `200 OK`
```json
{
  "room": {
    "id": 1,
    "number": "101",
    "floor": 1,
    "room_type": "DOUBLE",
    "capacity": 2
  },
  "bed": {
    "id": 1,
    "bed_number": "A",
    "is_occupied": true
  },
  "roommates": [
    {
      "id": 11,
      "full_name": "Jane Smith",
      "bed_number": "B"
    }
  ]
}
```

---

### Complaints

### Endpoint 75: List My Complaints
```http
GET /complaints
Authorization: Bearer {access_token}
```

**Response**: `200 OK`
```json
[
  {
    "id": 1,
    "tenant_id": 10,
    "title": "AC not working",
    "description": "The AC in room 101 is not cooling properly",
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

### Endpoint 76: Get Complaint Details
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
  "description": "The AC in room 101 is not cooling properly",
  "category": "MAINTENANCE",
  "priority": "HIGH",
  "status": "IN_PROGRESS",
  "assigned_to": 5,
  "resolved_at": null,
  "resolution_notes": null,
  "created_at": "2025-01-15T10:00:00Z",
  "updated_at": "2025-01-15T16:00:00Z"
}
```

---

### Endpoint 77: Create Complaint
```http
POST /complaints
Authorization: Bearer {access_token}
```

**Request Body**:
```json
{
  "title": "Water leakage in bathroom",
  "description": "There is water leaking from the ceiling in the bathroom",
  "category": "WATER",
  "priority": "URGENT"
}
```

**Response**: `201 Created`
```json
{
  "id": 2,
  "tenant_id": 10,
  "hostel_id": 1,
  "title": "Water leakage in bathroom",
  "description": "There is water leaking from the ceiling in the bathroom",
  "category": "WATER",
  "priority": "URGENT",
  "status": "OPEN",
  "created_at": "2025-01-16T11:00:00Z"
}
```

---

### Endpoint 78: List Complaint Comments
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
    "user_id": 5,
    "comment": "AC technician will visit tomorrow",
    "created_at": "2025-01-15T16:10:00Z"
  }
]
```

---

### Endpoint 79: Add Comment to Complaint
```http
POST /complaints/{complaint_id}/comments
Authorization: Bearer {access_token}
```

**Request Body**:
```json
{
  "comment": "Thank you for the update"
}
```

**Response**: `200 OK`
```json
{
  "id": 3,
  "complaint_id": 1,
  "user_id": 20,
  "comment": "Thank you for the update",
  "created_at": "2025-01-16T11:30:00Z"
}
```

---

### Notices

### Endpoint 80: List Notices
```http
GET /notices
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
  },
  {
    "id": 2,
    "title": "Holiday Notice",
    "content": "Hostel will be closed for cleaning on Sunday",
    "priority": "NORMAL",
    "published_at": "2025-01-15T12:00:00Z",
    "expires_at": "2025-01-19T00:00:00Z"
  }
]
```

---

### Endpoint 81: Get Notice Details
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

### Endpoint 82: List Mess Menus
```http
GET /mess-menu?date_from=2025-01-16&date_to=2025-01-20
Authorization: Bearer {access_token}
```

**Query Parameters**:
- `menu_date` (optional): Specific date
- `meal_type` (optional): BREAKFAST, LUNCH, SNACKS, DINNER
- `date_from` (optional): Range start
- `date_to` (optional): Range end

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

### Endpoint 83: Get Mess Menu for Date
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

### Endpoint 84: List My Leave Applications
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

### Endpoint 85: Get Leave Application
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

### Endpoint 86: Apply for Leave
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

### Endpoint 87: List My Invoices
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

### Endpoint 88: Initiate Payment
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

### Endpoint 89: List My Payments
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

### Endpoint 90: Download Payment Receipt
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

### Endpoint 91: List My Notifications
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

### Endpoint 92: Get Notification Count
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

### Endpoint 93: Mark Notification as Read
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

### Endpoint 94: Mark All Notifications as Read
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

### Endpoint 95: Register Device Token (Push Notifications)
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

### Endpoint 96: List My Device Tokens
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

### Endpoint 97: Delete Device Token
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

### Endpoint 98: List Available Hostels
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

### Endpoint 99: Get Hostel Details
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

### Endpoint 100: List Public Notices
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

### Endpoint 101: Get Notice Details
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

### Endpoint 102: Get Public Mess Menu
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

### Endpoint 103: Get Visitor Account Info
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

## Common Models & Error Responses

### User Roles
```typescript
enum UserRole {
  SUPER_ADMIN = "SUPER_ADMIN",
  HOSTEL_ADMIN = "HOSTEL_ADMIN",
  TENANT = "TENANT",
  VISITOR = "VISITOR"
}
```

### Room Types
```typescript
enum RoomType {
  SINGLE = "SINGLE",
  DOUBLE = "DOUBLE",
  TRIPLE = "TRIPLE",
  DORMITORY = "DORMITORY"
}
```

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

### Notice Priority
```typescript
enum NoticePriority {
  LOW = "LOW",
  NORMAL = "NORMAL",
  HIGH = "HIGH",
  URGENT = "URGENT"
}
```

### Meal Types
```typescript
enum MealType {
  BREAKFAST = "BREAKFAST",
  LUNCH = "LUNCH",
  SNACKS = "SNACKS",
  DINNER = "DINNER"
}
```

### Leave Status
```typescript
enum LeaveStatus {
  PENDING = "PENDING",
  APPROVED = "APPROVED",
  REJECTED = "REJECTED",
  CANCELLED = "CANCELLED"
}
```

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

## Endpoint Summary by Role

### Authentication (Public) - 8 endpoints
Endpoints 1-8: Registration, login, OTP, token management, password change

### SuperAdmin - 17 endpoints
Endpoints 9-25: Hostel management, user management, subscriptions, platform analytics

### Hostel Admin - 46 endpoints
Endpoints 26-71: Rooms, beds, tenants, complaints, notices, mess menu, leaves, payments, hostel analytics

### Tenant - 26 endpoints
Endpoints 72-97: Profile, room, complaints, notices, mess menu, leaves, payments, notifications

### Visitor - 6 endpoints
Endpoints 98-103: Read-only access to hostel info, public notices, mess menu

**Total: 103 API Endpoints**
