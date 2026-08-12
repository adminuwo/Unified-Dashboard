# Simplified Unified Service

A centralized shared infrastructure backend service that provides core services (**User Authentication**, **Single Central Identity**, **Account Verification**, **Payment Abstraction**, **Application API Keys**, and **Centralized Logging**) for multiple standalone applications.

---

## Project Structure

```text
unified-service/
│
├── frontend/             # Placeholder for future admin dashboard / portal tools
│   └── README.md
│
└── backend/              # Production FastAPI backend service
    ├── src/
    │   ├── main.py
    │   ├── config/
    │   ├── database/
    │   ├── auth/
    │   ├── verification/
    │   ├── payment/
    │   ├── applications/
    │   ├── logs/
    │   └── middleware/
    ├── tests/
    ├── .env
    ├── .env.example
    ├── requirements.txt
    └── README.md
```

---

## Architectural Principles & Ownership Boundaries

### Standalone Applications Own:
- Application Frontend & User Interface
- Product-specific User Experience
- Product Business Logic
- Standalone Application Backend
- Product-specific Databases & Schema Features

### Unified Service Owns:
- Central User Identity (`users` table with UUIDs)
- Authentication & Single Login across products
- Account Verification
- Payment Provider Secret Keys & Webhook Handling
- Application API Key Generation & Management
- Centralized Application Logging & Audit Trails

---

## Standalone Application Integration Guide

Standalone application backends communicate with the Unified Backend using standard REST HTTP calls.

### 1. Application Configuration

The standalone application backend needs **only**:

```env
UNIFIED_API_URL=http://localhost:8000
UNIFIED_API_KEY=key_your_generated_application_api_key
```

The standalone application **does NOT need** sensitive provider credentials:
- NO `PAYMENT_SECRET_KEY`
- NO `JWT_SECRET`
- NO `EMAIL_PROVIDER_SECRET`

Those secrets belong exclusively to the Unified Backend.

---

### 2. Integration Flows

#### User Registration Flow

```text
Standalone User UI
       │  (Fills Registration Form)
       ▼
Standalone Application Backend
       │  POST http://localhost:8000/api/auth/register
       │  Header: X-Application-Key: key_your_application_api_key
       │  Body: { "email": "user@domain.com", "password": "...", "name": "..." }
       ▼
Unified Backend Service
       │  1. Create User in `users` table
       │  2. Generate Verification Token
       ▼
Standalone Application Backend
       │  (Receives Unified User ID)
       ▼
Standalone User UI
```

#### User Login & JWT Flow

```text
Standalone User UI
       │  (Fills Login Form)
       ▼
Standalone Application Backend
       │  POST http://localhost:8000/api/auth/login
       │  Header: X-Application-Key: key_your_application_api_key
       │  Body: { "email": "user@domain.com", "password": "..." }
       ▼
Unified Backend Service
       │  1. Validate Credentials
       │  2. Generate JWT Access & Refresh Tokens
       ▼
Standalone Application Backend
       │  (Returns JWT Bearer token to User UI)
       ▼
Standalone User UI
```

#### Verification Flow

```text
Standalone User UI
       │  (Enters 6-digit or link Token)
       ▼
Standalone Application Backend
       │  POST http://localhost:8000/api/verification/verify
       │  Header: X-Application-Key: key_your_application_api_key
       │  Body: { "token": "..." }
       ▼
Unified Backend Service
       │  1. Validate token & expiration
       │  2. Set `is_verified = true` on `users` table
       ▼
Standalone Application Backend
       │  (Receives Verification Confirmation)
       ▼
Standalone User UI
```

#### Payment Flow

```text
Standalone User UI
       │  (Clicks "Subscribe / Buy Plan")
       ▼
Standalone Application Backend
       │  POST http://localhost:8000/api/payment/create
       │  Header: X-Application-Key: key_your_application_api_key
       │  Body: { "user_id": "...", "product_id": "app_product_1", "plan_id": "pro", "amount": 29.99 }
       ▼
Unified Backend Service
       │  1. Create Payment Record (Pending)
       │  2. Generate Checkout URL with Payment Secret
       ▼
Standalone Application Backend
       │  (Redirects user to payment checkout)
       ▼
Payment Provider Webhook -> Unified Backend /api/payment/webhook (Updates Status to Succeeded)
```

#### Centralized Logging Flow

```text
Standalone Application Backend
       │  POST http://localhost:8000/api/logs
       │  Header: X-Application-Key: key_your_application_api_key
       │  Body: {
       │    "level": "ERROR",
       │    "event": "database_timeout",
       │    "message": "Connection timeout on query",
       │    "user_id": "uuid_..."
       │  }
       ▼
Unified Backend Service
       │  1. Redact any sensitive keys in message/metadata
       │  2. Store log in `logs` table linked to Application ID
```

---

## Quick Start & Verification

1. Navigate to backend directory: `cd unified-service/backend`
2. Activate virtual environment: `.\.venv\Scripts\Activate.ps1`
3. Run tests: `python -m pytest tests/ -v`
4. Start backend server: `uvicorn src.main:app --reload --port 8000`
5. Open health check: `http://localhost:8000/api/health`
6. Open Swagger API documentation: `http://localhost:8000/docs`
