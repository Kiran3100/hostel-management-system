# Hostel Management System - API Documentation

## Project Overview

A production-grade, multi-tenant hostel management system built with FastAPI, featuring role-based access control (RBAC), subscription management, payment integration, and comprehensive hostel operations. The system supports multiple hostels on a single platform with flexible subscription tiers and feature limits.

---

## Project Structure

```
hostel-management-system/├── app/│   ├── adapters/          # External service adapters (payment, storage, OTP, notifications)│   ├── api/│   │   └── v1/           # API v1 endpoints│   ├── core/             # Core utilities (security, RBAC, middleware, pagination)│   ├── models/           # SQLAlchemy models│   ├── repositories/     # Data access layer│   ├── schemas/          # Pydantic schemas│   ├── services/         # Business logic layer│   ├── config.py         # Application configuration│   ├── database.py       # Database setup│   ├── exceptions.py     # Custom exceptions│   └── main.py           # FastAPI application entry point├── alembic/              # Database migrations├── scripts/              # Utility scripts (seeding, admin creation)├── .env                  # Environment variables└── requirements.txt      # Python dependencies
```

### Key Directories

-   **`/adapters`**: Abstract interfaces for external services (payment gateways, storage, OTP, notifications) with pluggable implementations
-   **`/api/v1`**: RESTful API endpoints organized by domain (auth, hostels, rooms, tenants, etc.)
-   **`/models`**: SQLAlchemy ORM models with relationships and constraints
-   **`/repositories`**: Repository pattern for data access abstraction
-   **`/schemas`**: Pydantic models for request/response validation
-   **`/services`**: Business logic and orchestration layer

---

## Setup and Installation

### Prerequisites

-   Python 3.11+
-   PostgreSQL 15+
-   Redis (for caching and rate limiting)

### Installation Steps

1.  **Clone the repository**
    
    ```bash
    git clone <repo-url>cd hostel-management-system
    ```
    
2.  **Create virtual environment**
    
    ```bash
    python -m venv venvsource venv/bin/activate  # On Windows: venvScriptsactivate
    ```
    
3.  **Install dependencies**
    
    ```bash
    pip install -r requirements.txt
    ```
    
4.  **Configure environment variables**
    
    Copy `.env.example` to `.env` and configure:
    
    ```bash
    # DatabaseDATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/hostel_db# SecuritySECRET_KEY=your-secret-key-min-32-chars# RedisREDIS_URL=redis://localhost:6379/0# Payment (Razorpay or mock)PAYMENT_PROVIDER=mockRAZORPAY_KEY_ID=your_key_idRAZORPAY_KEY_SECRET=your_key_secret
    ```
    

pip install pydantic  
pip install pydantic_settingspip install asyncpg

pip install PyJWT[crypto]==2.8.0 cryptography==41.0.7pip install PyJWTpip install cryptographypip install passlib[bcrypt]pip install redis[hiredis]

# For rate limiting

pip install slowapi

# For caching

pip install fastapi-cache2pip install fastapi-cache2[redis]

# Or all together

pip install redis slowapi fastapi-cache2[redis]pip install pydantic[email]pip install razorpay

5.  **Initialize database**
    
    ```bash
    # Reset and create tablespython scripts/reset_db_simple.py# Run migrationsalembic upgrade head# Seed initial datapython scripts/seed.py
    ```
    
6.  **Run the application**
    
    ```bash
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    ```
    
7.  **Access API Documentation**
    
    -   Swagger UI: `http://localhost:8000/docs`
    -   ReDoc: `http://localhost:8000/redoc`

### Default Credentials (Development Only)

Role

Email

Password

Super Admin

[superadmin@hostelms.com](mailto:superadmin@hostelms.com)

SuperAdmin@123

Hostel Admin

[admin@demo.com](mailto:admin@demo.com)

Admin@123

Tenant

[tenant@demo.com](mailto:tenant@demo.com)

Tenant@123

⚠️ **Change these passwords in production!**

---

## API Reference

### Authentication

#### `POST /api/v1/auth/register`

-   **Summary:** Register a new user (Admin only)
-   **Description:** Creates a new user account with specified role and hostel assignment. Requires Super Admin or Hostel Admin privileges.
-   **Tags:** `Authentication`
-   **Request Body:**
    
    ```json
    {  "email": "user@example.com",  "phone": "+919876543210",  "password": "SecurePass@123",  "role": "TENANT",  "hostel_id": 1}
    ```
    
-   **Successful Response:**
    -   **Status Code:** `201 Created`
    -   **Body:**
        
        ```json
        {  "id": 1,  "email": "user@example.com",  "phone": "+919876543210",  "role": "TENANT",  "hostel_id": 1,  "is_active": true,  "is_verified": true}
        ```
        

---

#### `POST /api/v1/auth/login`

-   **Summary:** Login with email and password
-   **Description:** Authenticates user with email/password and returns JWT access and refresh tokens.
-   **Tags:** `Authentication`
-   **Request Body:**
    
    ```json
    {  "email": "user@example.com",  "password": "SecurePass@123"}
    ```
    
-   **Successful Response:**
    -   **Status Code:** `200 OK`
    -   **Body:**
        
        ```json
        {  "access_token": "eyJhbGc...",  "refresh_token": "eyJhbGc...",  "token_type": "bearer",  "user_id": 1,  "role": "TENANT"}
        ```
        
-   **Error Responses:**
    -   `401 Unauthorized`: Invalid credentials
    -   `400 Bad Request`: Account inactive

---

#### `POST /api/v1/auth/login/otp/request`

-   **Summary:** Request OTP for phone login
-   **Description:** Generates and sends a 6-digit OTP to the provided phone number for passwordless authentication.
-   **Tags:** `Authentication`
-   **Request Body:**
    
    ```json
    {  "phone": "+919876543210",  "hostel_code": "DEMO001"}
    ```
    
-   **Successful Response:**
    -   **Status Code:** `200 OK`
    -   **Body:**
        
        ```json
        {  "message": "OTP sent successfully"}
        ```
        

---

#### `POST /api/v1/auth/login/otp/verify`

-   **Summary:** Verify OTP and login
-   **Description:** Verifies the OTP code and returns authentication tokens upon successful validation.
-   **Tags:** `Authentication`
-   **Request Body:**
    
    ```json
    {  "phone": "+919876543210",  "otp": "123456"}
    ```
    
-   **Successful Response:**
    -   **Status Code:** `200 OK`
    -   **Body:**
        
        ```json
        {  "access_token": "eyJhbGc...",  "refresh_token": "eyJhbGc...",  "token_type": "bearer",  "user_id": 1,  "role": "TENANT"}
        ```
        

---

#### `POST /api/v1/auth/refresh`

-   **Summary:** Refresh access token
-   **Description:** Generates a new access token using a valid refresh token.
-   **Tags:** `Authentication`
-   **Request Body:**
    
    ```json
    {  "refresh_token": "eyJhbGc..."}
    ```
    
-   **Successful Response:**
    -   **Status Code:** `200 OK`
    -   **Body:**
        
        ```json
        {  "access_token": "eyJhbGc...",  "token_type": "bearer"}
        ```
        

---

#### `GET /api/v1/auth/me`

-   **Summary:** Get current user profile
-   **Description:** Returns the authenticated user's profile information.
-   **Tags:** `Authentication`
-   **Successful Response:**
    -   **Status Code:** `200 OK`
    -   **Body:**
        
        ```json
        {  "id": 1,  "email": "user@example.com",  "phone": "+919876543210",  "role": "TENANT",  "hostel_id": 1,  "is_active": true,  "is_verified": true,  "last_login": "2025-10-08T10:30:00Z"}
        ```
        
-   **Dependencies:** `get_current_user`

---

### Hostels

#### `GET /api/v1/hostels`

-   **Summary:** List all hostels (Super Admin only)
-   **Description:** Retrieves paginated list of all hostels in the system. Only accessible to Super Admin users.
-   **Tags:** `Hostels`
-   **Query Parameters:**
    
    Name
    
    Type
    
    Default
    
    Description
    
    `page`
    
    `int`
    
    `1`
    
    Page number
    
    `page_size`
    
    `int`
    
    `20`
    
    Items per page
    
-   **Successful Response:**
    -   **Status Code:** `200 OK`
    -   **Body:**
        
        ```json
        {  "items": [    {      "id": 1,      "name": "Demo Hostel",      "code": "DEMO001",      "address": "123 Demo Street",      "city": "Mumbai",      "state": "Maharashtra",      "is_active": true    }  ],  "total": 1,  "page": 1,  "page_size": 20,  "total_pages": 1}
        ```
        
-   **Dependencies:** `require_role([UserRole.SUPER_ADMIN])`

---

#### `POST /api/v1/hostels`

-   **Summary:** Create a new hostel
-   **Description:** Creates a new hostel with unique code. Only Super Admins can create hostels.
-   **Tags:** `Hostels`
-   **Request Body:**
    
    ```json
    {  "name": "New Hostel",  "code": "NEW001",  "address": "456 New Street",  "city": "Delhi",  "state": "Delhi",  "pincode": "110001",  "phone": "+919876543220",  "email": "new@hostel.com"}
    ```
    
-   **Successful Response:**
    -   **Status Code:** `201 Created`
    -   **Body:**
        
        ```json
        {  "id": 2,  "name": "New Hostel",  "code": "NEW001",  "is_active": true}
        ```
        
-   **Error Responses:**
    -   `409 Conflict`: Hostel code already exists

---

#### `GET /api/v1/hostels/{hostel_id}/dashboard`

-   **Summary:** Get hostel dashboard statistics
-   **Description:** Returns comprehensive dashboard data including occupancy, revenue, complaints, and tenant statistics.
-   **Tags:** `Hostels`
-   **Path Parameters:**
    
    Name
    
    Type
    
    Description
    
    `hostel_id`
    
    `int`
    
    Hostel ID
    
-   **Successful Response:**
    -   **Status Code:** `200 OK`
    -   **Body:**
        
        ```json
        {  "hostel_id": 1,  "total_rooms": 10,  "total_beds": 25,  "occupied_beds": 18,  "occupancy_rate": 72.0,  "total_tenants": 18,  "pending_fees": 50000.00,  "total_revenue": 200000.00,  "pending_complaints": 3}
        ```
        

---

### Rooms & Beds

#### `GET /api/v1/rooms`

-   **Summary:** List rooms
-   **Description:** Retrieves all rooms for a hostel. Hostel scope is automatically determined based on user role.
-   **Tags:** `Rooms & Beds`
-   **Query Parameters:**
    
    Name
    
    Type
    
    Required
    
    Description
    
    `hostel_id`
    
    `int`
    
    No
    
    Hostel ID (required for Super Admin)
    
-   **Successful Response:**
    -   **Status Code:** `200 OK`
    -   **Body:**
        
        ```json
        [  {    "id": 1,    "hostel_id": 1,    "number": "101",    "floor": 1,    "room_type": "DOUBLE",    "capacity": 2,    "description": "Standard room with attached bathroom"  }]
        ```
        

---

#### `POST /api/v1/rooms`

-   **Summary:** Create a new room
-   **Description:** Creates a room with automatic bed generation. Checks subscription limits before creation.
-   **Tags:** `Rooms & Beds`
-   **Request Body:**
    
    ```json
    {  "hostel_id": 1,  "number": "102",  "floor": 1,  "room_type": "SINGLE",  "capacity": 1,  "description": "Single occupancy room"}
    ```
    
-   **Successful Response:**
    -   **Status Code:** `201 Created`
    -   **Body:**
        
        ```json
        {  "id": 2,  "hostel_id": 1,  "number": "102",  "floor": 1,  "room_type": "SINGLE",  "capacity": 1}
        ```
        
-   **Error Responses:**
    -   `402 Payment Required`: Room limit exceeded for subscription plan
    -   `409 Conflict`: Room number already exists

---

#### `POST /api/v1/beds/{bed_id}/assign`

-   **Summary:** Assign tenant to bed
-   **Description:** Assigns a tenant to a specific bed, marking it as occupied.
-   **Tags:** `Rooms & Beds`
-   **Path Parameters:**
    
    Name
    
    Type
    
    Description
    
    `bed_id`
    
    `int`
    
    Bed ID
    
-   **Request Body:**
    
    ```json
    {  "tenant_id": 1}
    ```
    
-   **Successful Response:**
    -   **Status Code:** `200 OK`
    -   **Body:**
        
        ```json
        {  "id": 1,  "room_id": 1,  "number": "1",  "is_occupied": true,  "tenant_id": 1}
        ```
        
-   **Error Responses:**
    -   `400 Bad Request`: Bed already occupied

---

### Tenants

#### `GET /api/v1/tenants`

-   **Summary:** List tenants
-   **Description:** Retrieves all tenant profiles for a hostel. Includes user and bed information.
-   **Tags:** `Tenants`
-   **Query Parameters:**
    
    Name
    
    Type
    
    Description
    
    `hostel_id`
    
    `int`
    
    Hostel ID (required for Super Admin)
    
-   **Successful Response:**
    -   **Status Code:** `200 OK`
    -   **Body:**
        
        ```json
        [  {    "id": 1,    "user_id": 3,    "hostel_id": 1,    "full_name": "John Doe",    "date_of_birth": "2000-01-15",    "gender": "Male",    "guardian_name": "Jane Doe",    "guardian_phone": "+919876543213",    "current_bed_id": 5,    "check_in_date": "2025-09-01"  }]
        ```
        

---

#### `POST /api/v1/tenants`

-   **Summary:** Create tenant profile
-   **Description:** Creates a tenant profile for an existing user. Checks subscription tenant limit.
-   **Tags:** `Tenants`
-   **Request Body:**
    
    ```json
    {  "user_id": 3,  "hostel_id": 1,  "full_name": "John Doe",  "date_of_birth": "2000-01-15",  "gender": "Male",  "id_proof_type": "Aadhaar",  "id_proof_number": "1234-5678-9012",  "guardian_name": "Jane Doe",  "guardian_phone": "+919876543213",  "emergency_contact": "+919876543213"}
    ```
    
-   **Successful Response:**
    -   **Status Code:** `201 Created`
    -   **Body:**
        
        ```json
        {  "id": 1,  "user_id": 3,  "full_name": "John Doe",  "hostel_id": 1}
        ```
        
-   **Error Responses:**
    -   `402 Payment Required`: Tenant limit exceeded
    -   `400 Bad Request`: User already has tenant profile

---

#### `POST /api/v1/tenants/{tenant_id}/check-in`

-   **Summary:** Check-in tenant to bed
-   **Description:** Assigns tenant to a bed and creates check-in record.
-   **Tags:** `Tenants`
-   **Path Parameters:**
    
    Name
    
    Type
    
    Description
    
    `tenant_id`
    
    `int`
    
    Tenant profile ID
    
-   **Request Body:**
    
    ```json
    {  "bed_id": 5,  "check_in_date": "2025-10-08"}
    ```
    
-   **Successful Response:**
    -   **Status Code:** `200 OK`
    -   **Body:**
        
        ```json
        {  "id": 1,  "full_name": "John Doe",  "current_bed_id": 5,  "check_in_date": "2025-10-08"}
        ```
        
-   **Error Responses:**
    -   `400 Bad Request`: Bed already occupied or tenant already checked in

---

### Payments & Invoices

#### `GET /api/v1/invoices`

-   **Summary:** List invoices
-   **Description:** Retrieves invoices. Tenants see only their invoices; admins can filter by tenant or hostel.
-   **Tags:** `Payments`
-   **Query Parameters:**
    
    Name
    
    Type
    
    Description
    
    `tenant_id`
    
    `int`
    
    Filter by tenant
    
    `hostel_id`
    
    `int`
    
    Filter by hostel
    
-   **Successful Response:**
    -   **Status Code:** `200 OK`
    -   **Body:**
        
        ```json
        [  {    "id": 1,    "invoice_number": "INV-1-20251008-A1B2",    "tenant_id": 1,    "amount": 5000.00,    "due_date": "2025-10-15",    "status": "PENDING",    "paid_amount": 0.00  }]
        ```
        

---

#### `POST /api/v1/payments`

-   **Summary:** Initiate payment
-   **Description:** Creates a payment order with the configured payment gateway (Razorpay or mock).
-   **Tags:** `Payments`
-   **Request Body:**
    
    ```json
    {  "invoice_id": 1,  "amount": 5000.00,  "gateway": "razorpay"}
    ```
    
-   **Successful Response:**
    -   **Status Code:** `201 Created`
    -   **Body:**
        
        ```json
        {  "id": 1,  "invoice_id": 1,  "amount": 5000.00,  "status": "PROCESSING",  "transaction_id": "order_xyz123",  "gateway": "razorpay"}
        ```
        

---

### Complaints

#### `GET /api/v1/complaints`

-   **Summary:** List complaints
-   **Description:** Tenants see their own complaints; admins see all complaints for their hostel.
-   **Tags:** `Complaints`
-   **Query Parameters:**
    
    Name
    
    Type
    
    Description
    
    `hostel_id`
    
    `int`
    
    Filter by hostel (admin only)
    
-   **Successful Response:**
    -   **Status Code:** `200 OK`
    -   **Body:**
        
        ```json
        [  {    "id": 1,    "tenant_id": 1,    "title": "Water leakage in room",    "description": "Water is leaking from bathroom ceiling",    "category": "MAINTENANCE",    "priority": "HIGH",    "status": "OPEN",    "created_at": "2025-10-08T10:00:00Z"  }]
        ```
        

---

#### `POST /api/v1/complaints`

-   **Summary:** Create complaint (Tenant only)
-   **Description:** Allows tenants to file complaints about hostel facilities or services.
-   **Tags:** `Complaints`
-   **Request Body:**
    
    ```json
    {  "title": "Water leakage",  "description": "Water leaking from ceiling in room 101",  "category": "MAINTENANCE",  "priority": "HIGH"}
    ```
    
-   **Successful Response:**
    -   **Status Code:** `201 Created`
    -   **Body:**
        
        ```json
        {  "id": 1,  "title": "Water leakage",  "status": "OPEN",  "created_at": "2025-10-08T10:00:00Z"}
        ```
        

---

#### `PATCH /api/v1/complaints/{complaint_id}`

-   **Summary:** Update complaint (Admin only)
-   **Description:** Admins can update complaint status, priority, assignment, and resolution notes.
-   **Tags:** `Complaints`
-   **Path Parameters:**
    
    Name
    
    Type
    
    Description
    
    `complaint_id`
    
    `int`
    
    Complaint ID
    
-   **Request Body:**
    
    ```json
    {  "status": "RESOLVED",  "assigned_to": 2,  "resolution_notes": "Fixed the pipe leak"}
    ```
    
-   **Successful Response:**
    -   **Status Code:** `200 OK`
    -   **Body:**
        
        ```json
        {  "id": 1,  "status": "RESOLVED",  "resolved_at": "2025-10-08T11:00:00Z",  "resolution_notes": "Fixed the pipe leak"}
        ```
        

---

### Subscriptions

#### `GET /api/v1/subscriptions/plans`

-   **Summary:** List subscription plans
-   **Description:** Retrieves all available subscription plans with features and limits.
-   **Tags:** `Subscriptions`
-   **Successful Response:**
    -   **Status Code:** `200 OK`
    -   **Body:**
        
        ```json
        [  {    "id": 1,    "name": "Free Plan",    "tier": "FREE",    "max_tenants_per_hostel": 10,    "max_rooms_per_hostel": 5,    "features": {      "basic_billing": true,      "reports": false    }  }]
        ```
        

---

#### `GET /api/v1/subscriptions/{subscription_id}/usage`

-   **Summary:** Get feature usage
-   **Description:** Shows current usage against subscription limits (tenants, rooms, storage).
-   **Tags:** `Subscriptions`
-   **Path Parameters:**
    
    Name
    
    Type
    
    Description
    
    `subscription_id`
    
    `int`
    
    Subscription ID
    
-   **Successful Response:**
    -   **Status Code:** `200 OK`
    -   **Body:**
        
        ```json
        {  "hostel_id": 1,  "plan_name": "Free Plan",  "current_tenants": 8,  "max_tenants": 10,  "current_rooms": 4,  "max_rooms": 5,  "usage_percentage": {    "tenants": 80.0,    "rooms": 80.0  }}
        ```
        

---

### Reports

#### `GET /api/v1/reports/dashboard`

-   **Summary:** Super Admin dashboard
-   **Description:** Provides system-wide statistics for Super Admin.
-   **Tags:** `Reports`
-   **Successful Response:**
    -   **Status Code:** `200 OK`
    -   **Body:**
        
        ```json
        {  "total_hostels": 5,  "active_hostels": 4,  "total_tenants": 120,  "total_revenue": 500000.00}
        ```
        
-   **Dependencies:** `require_role([UserRole.SUPER_ADMIN])`

---

## Data Models

### User

Field

Type

Required

Description

`id`

`int`

Yes

Unique user identifier

`email`

`str`

No

User email (unique)

`phone`

`str`

No

Phone number (unique)

`password_hash`

`str`

No

Hashed password

`role`

`UserRole`

Yes

User role (SUPER_ADMIN, HOSTEL_ADMIN, TENANT)

`primary_hostel_id`

`int`

No

Associated hostel (for tenants)

`is_active`

`bool`

Yes

Account active status

`is_verified`

`bool`

Yes

Verification status

### Hostel

Field

Type

Required

Description

`id`

`int`

Yes

Unique hostel identifier

`name`

`str`

Yes

Hostel name

`code`

`str`

Yes

Unique hostel code

`address`

`str`

No

Full address

`city`

`str`

No

City

`state`

`str`

No

State/Province

`phone`

`str`

No

Contact phone

`email`

`str`

No

Contact email

`timezone`

`str`

Yes

Hostel timezone (default: Asia/Kolkata)

`is_active`

`bool`

Yes

Active status

### Room

Field

Type

Required

Description

`id`

`int`

Yes

Unique room identifier

`hostel_id`

`int`

Yes

Associated hostel

`number`

`str`

Yes

Room number

`floor`

`int`

Yes

Floor number

`room_type`

`RoomType`

Yes

Type (SINGLE, DOUBLE, TRIPLE, DORMITORY)

`capacity`

`int`

Yes

Maximum occupants

`description`

`str`

No

Room description

### TenantProfile

Field

Type

Required

Description

`id`

`int`

Yes

Unique profile identifier

`user_id`

`int`

Yes

Associated user account

`hostel_id`

`int`

Yes

Current hostel

`full_name`

`str`

Yes

Full name

`date_of_birth`

`date`

No

Date of birth

`gender`

`str`

No

Gender

`id_proof_type`

`str`

No

ID proof type

`id_proof_number`

`str`

No

ID proof number

`guardian_name`

`str`

No

Guardian name

`guardian_phone`

`str`

No

Guardian phone

`emergency_contact`

`str`

No

Emergency contact

`current_bed_id`

`int`

No

Currently assigned bed

`check_in_date`

`date`

No

Check-in date

### Invoice

Field

Type

Required

Description

`id`

`int`

Yes

Unique invoice identifier

`invoice_number`

`str`

Yes

Unique invoice number

`hostel_id`

`int`

Yes

Associated hostel

`tenant_id`

`int`

Yes

Tenant being billed

`amount`

`Decimal`

Yes

Invoice amount (no tax)

`due_date`

`date`

Yes

Payment due date

`status`

`InvoiceStatus`

Yes

Status (PENDING, PAID, PARTIAL, OVERDUE)

`paid_amount`

`Decimal`

Yes

Amount paid so far

### Complaint

Field

Type

Required

Description

`id`

`int`

Yes

Unique complaint identifier

`tenant_id`

`int`

Yes

Tenant who filed complaint

`hostel_id`

`int`

Yes

Associated hostel

`title`

`str`

Yes

Complaint title

`description`

`str`

Yes

Detailed description

`category`

`ComplaintCategory`

Yes

Category (MAINTENANCE, CLEANLINESS, etc.)

`priority`

`ComplaintPriority`

Yes

Priority (LOW, MEDIUM, HIGH, URGENT)

`status`

`ComplaintStatus`

Yes

Status (OPEN, IN_PROGRESS, RESOLVED, etc.)

`assigned_to`

`int`

No

Admin assigned to complaint

`resolved_at`

`datetime`

No

Resolution timestamp

`resolution_notes`

`str`

No

Resolution notes

### Subscription

Field

Type

Required

Description

`id`

`int`

Yes

Unique subscription identifier

`hostel_id`

`int`

Yes

Associated hostel

`plan_id`

`int`

Yes

Selected plan

`status`

`SubscriptionStatus`

Yes

Status (ACTIVE, EXPIRED, TRIAL, etc.)

`start_date`

`date`

Yes

Subscription start date

`end_date`

`date`

No

Subscription end date

`auto_renew`

`bool`

Yes

Auto-renewal enabled

---

## Authentication & Authorization

### Authentication Methods

1.  **Email/Password Login**: Standard login with JWT tokens
2.  **OTP Login**: Passwordless phone authentication with 6-digit OTP
3.  **Token Refresh**: Refresh tokens for extended sessions

### Role-Based Access Control (RBAC)

Role

Permissions

**SUPER_ADMIN**

Full system access, manage all hostels, plans, subscriptions

**HOSTEL_ADMIN**

Manage assigned hostel(s), rooms, tenants, complaints

**TENANT**

View own profile, create complaints, make payments

### Authorization Headers

All protected endpoints require Bearer token authentication:

```
Authorization: Bearer <access_token>
```

---

## Error Responses

Common error response format:

```json
{  "error": "Error message",  "detail": "Additional details"}
```

### HTTP Status Codes

-   `200 OK`: Success
-   `201 Created`: Resource created successfully
-   `400 Bad Request`: Invalid request data
-   `401 Unauthorized`: Authentication required
-   `403 Forbidden`: Insufficient permissions
-   `404 Not Found`: Resource not found
-   `409 Conflict`: Duplicate resource
-   `422 Unprocessable Entity`: Validation error
-   `429 Too Many Requests`: Rate limit exceeded
-   `500 Internal Server Error`: Server error

---

## Rate Limiting

-   **Default**: 60 requests per minute per IP