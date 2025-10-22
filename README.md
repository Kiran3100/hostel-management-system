Here is your hostel management system API documentation formatted into a developer-friendly Markdown file with clear sections, tables, and curl examples:

```markdown
# Hostel Management System - API Documentation

## Project Overview

A production-grade, multi-tenant hostel management system built with FastAPI, featuring role-based access control (RBAC), subscription management, payment integration, and comprehensive hostel operations. The system supports multiple hostels on a single platform with flexible subscription tiers and feature limits.

---

## Project Structure

```

hostel-management-system/
├── app/
│   ├── adapters/          \# External service adapters (payment, storage, OTP, notifications)
│   ├── api/
│   │   └── v1/           \# API v1 endpoints
│   ├── core/             \# Core utilities (security, RBAC, middleware, pagination)
│   ├── models/           \# SQLAlchemy models
│   ├── repositories/     \# Data access layer
│   ├── schemas/          \# Pydantic schemas
│   ├── services/         \# Business logic layer
│   ├── config.py         \# Application configuration
│   ├── database.py       \# Database setup
│   ├── exceptions.py     \# Custom exceptions
│   └── main.py           \# FastAPI application entry point
├── alembic/              \# Database migrations
├── scripts/              \# Utility scripts (seeding, admin creation)
├── .env                  \# Environment variables
└── requirements.txt      \# Python dependencies

```

---

## Setup and Installation

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis (for caching and rate limiting)

### Installation Steps

1. Clone the repository

```

git clone <repo-url>
cd hostel-management-system

```

2. Create virtual environment

```

python -m venv venv
source venv/bin/activate  \# On Windows: venv\Scripts\activate

```

3. Install dependencies

```

pip install -r requirements.txt

```

4. Configure environment variables

Copy `.env.example` to `.env` and configure the following:

```


# Database

DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/hostel_db

# Security

SECRET_KEY=your-secret-key-min-32-chars

# Redis

REDIS_URL=redis://localhost:6379/0

# Payment (Razorpay or mock)

PAYMENT_PROVIDER=mock
RAZORPAY_KEY_ID=your_key_id
RAZORPAY_KEY_SECRET=your_key_secret

```

5. Initialize database

```


# Reset and create tables

python scripts/reset_db_simple.py

# Run migrations

alembic upgrade head

# Seed initial data

python scripts/seed.py

```

6. Run the application

```

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

```

7. Access API Documentation

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Default Credentials (Development Only)

| Role        | Email                     | Password          |
|-------------|---------------------------|-------------------|
| Super Admin | superadmin@hostelms.com   | SuperAdmin@123    |
| Hostel Admin| admin@demo.com            | Admin@123         |
| Tenant      | tenant@demo.com           | Tenant@123        |

⚠️ **Change these passwords in production!**

---

## Authentication & Authorization

### Authentication Methods

- Email/Password Login with JWT tokens
- OTP Login (passwordless phone authentication with 6-digit OTP)
- Token Refresh for extended sessions

### Role-Based Access Control (RBAC)

| Role        | Permissions                                                         |
|-------------|--------------------------------------------------------------------|
| SUPER_ADMIN | Full system access, manage all hostels, plans, subscriptions       |
| HOSTEL_ADMIN| Manage assigned hostel(s), rooms, tenants, complaints              |
| TENANT      | View own profile, create complaints, make payments                 |

### Authorization Header

All protected endpoints require Bearer token authentication:

```

Authorization: Bearer <access_token>

```

---

## API Reference - Selected Endpoints with curl Examples

### Register User (Admin only)

`POST /api/v1/auth/register`

Request Body:

```

{
"email": "user@example.com",
"phone": "+919876543210",
"password": "SecurePass@123",
"role": "TENANT",
"hostel_id": 1
}

```

Curl:

```

curl -X POST http://localhost:8000/api/v1/auth/register \
-H "Authorization: Bearer <access_token>" \
-H "Content-Type: application/json" \
-d '{"email":"user@example.com","phone":"+919876543210","password":"SecurePass@123","role":"TENANT","hostel_id":1}'

```

### Login

`POST /api/v1/auth/login`

Request Body:

```

{
"email": "user@example.com",
"password": "SecurePass@123"
}

```

Curl:

```

curl -X POST http://localhost:8000/api/v1/auth/login \
-H "Content-Type: application/json" \
-d '{"email":"user@example.com","password":"SecurePass@123"}'

```

### List Hostels (Super Admin only)

`GET /api/v1/hostels`

Curl:

```

curl -X GET http://localhost:8000/api/v1/hostels \
-H "Authorization: Bearer <access_token>"

```

### Create Room

`POST /api/v1/rooms`

Request Body:

```

{
"hostel_id": 1,
"number": "102",
"floor": 1,
"room_type": "SINGLE",
"capacity": 1,
"description": "Single occupancy room"
}

```

Curl:

```

curl -X POST http://localhost:8000/api/v1/rooms \
-H "Authorization: Bearer <access_token>" \
-H "Content-Type: application/json" \
-d '{"hostel_id":1,"number":"102","floor":1,"room_type":"SINGLE","capacity":1,"description":"Single occupancy room"}'

```

---

## Data Models Summary

### User

| Field              | Type      | Required | Description                       |
|--------------------|-----------|----------|---------------------------------|
| id                 | int       | Yes      | Unique user identifier           |
| email              | str       | No       | User email (unique)              |
| phone              | str       | No       | Phone number (unique)            |
| password_hash      | str       | No       | Hashed password                 |
| role               | UserRole  | Yes      | User role (SUPER_ADMIN, etc.)    |
| primary_hostel_id   | int       | No       | Associated hostel (for tenants)  |
| is_active          | bool      | Yes      | Account active status            |
| is_verified        | bool      | Yes      | Verification status             |

### Hostel

| Field     | Type    | Required | Description              |
|-----------|---------|----------|--------------------------|
| id        | int     | Yes      | Unique hostel identifier |
| name      | str     | Yes      | Hostel name              |
| code      | str     | Yes      | Unique hostel code       |
| address   | str     | No       | Full address             |
| city      | str     | No       | City                     |
| state     | str     | No       | State/Province           |
| phone     | str     | No       | Contact phone            |
| email     | str     | No       | Contact email            |
| timezone  | str     | Yes      | Hostel timezone          |
| is_active | bool    | Yes      | Active status            |

---

For a full set of API endpoints, request/response schemas, and error codes, access the live Swagger UI or ReDoc links after running the application.

If you want the entire documentation in a downloadable or exportable file format, I can prepare that for you as well.```

