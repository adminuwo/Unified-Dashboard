# Unified Backend Service

A simple, centralized, shared infrastructure service providing authentication, single user identity, account verification, generic payment handling, application API key management, and centralized logging for multiple standalone applications.

---

## Architecture Overview

```text
                  UNIFIED SERVICE
               ┌────────────────────┐
               │                    │
               │     BACKEND        │
               │                    │
               │ Authentication     │
               │ User Identity      │
               │ Verification       │
               │ Payment            │
               │ Application Keys   │
               │ Logging            │
               │                    │
               │ PostgreSQL         │
               │                    │
               └─────────┬──────────┘
                         │
                     REST APIs
                         │
          ┌──────────────┼──────────────┐
          │              │              │
          ▼              ▼              ▼
    ┌──────────┐   ┌──────────┐   ┌──────────┐
    │ Standalone│   │ Standalone│  │ Standalone│
    │Application│   │Application│  │Application│
    │     A     │   │     B     │  │     C     │
    │           │   │           │  │           │
    │ Frontend  │   │ Frontend  │  │ Frontend  │
    │ Backend   │   │ Backend   │  │ Backend   │
    └──────────┘   └──────────┘   └──────────┘
```

The Unified Backend acts as an **invisible shared infrastructure layer**. Standalone applications communicate with it exclusively via backend-to-backend REST API calls. Users interact solely with the standalone application UI and are **never redirected to the Unified Backend frontend**.

---

## Core Features & Shared Services

1. **Application API-Key Authentication**: Every standalone application authenticates using an application key passed in the `X-Application-Key` header. Keys are securely stored using SHA-256 hashes.
2. **Central User Identity & Single Login**: A single user account (`users` table) spans across all standalone applications without requiring separate authentication databases.
3. **User Authentication (JWT)**: Issues JWT access & refresh tokens via backend-to-backend auth requests.
4. **Account Verification**: Generates secure verification tokens for account activation (`is_verified` flag).
5. **Payment Handling**: Centralized product/plan payment initialization, payment status lookup, and HMAC-signed webhook processing.
6. **Centralized Logging**: Stores application logs (`INFO`, `WARNING`, `ERROR`) with automatic redaction of sensitive credentials (passwords, JWTs, API keys).

---

## Directory Structure

```text
backend/
├── src/
│   ├── main.py                   # FastAPI Application Entrypoint & Health Check
│   ├── config/
│   │   └── settings.py           # Environment Configuration (Pydantic Settings)
│   ├── database/
│   │   ├── connection.py         # SQLAlchemy DB Connection & Engine Setup
│   │   └── models.py             # User, AppKey, Verification, Payment, Log Models
│   ├── auth/
│   │   ├── router.py             # /api/auth Endpoints (register, login, refresh, me)
│   │   ├── service.py            # Password hashing (Bcrypt) & JWT token logic
│   │   └── schemas.py            # Pydantic Auth Request/Response Models
│   ├── verification/
│   │   ├── router.py             # /api/verification Endpoints (send, verify)
│   │   ├── service.py            # Verification token generation & validation
│   │   └── schemas.py            # Verification Schemas
│   ├── payment/
│   │   ├── router.py             # /api/payment Endpoints (create, status, webhook)
│   │   ├── service.py            # Payment intents & HMAC Webhook verification
│   │   └── schemas.py            # Payment Schemas
│   ├── applications/
│   │   ├── router.py             # /api/applications/keys Endpoints (create, list, revoke)
│   │   ├── service.py            # API key generation (key_...) & SHA-256 hashing
│   │   └── schemas.py            # Application Key Schemas
│   ├── logs/
│   │   ├── router.py             # /api/logs Endpoint
│   │   ├── service.py            # Centralized log storage & sensitive data redaction
│   │   └── schemas.py            # Logging Schemas
│   └── middleware/
│       └── authentication.py     # Application Key & User JWT FastAPI Dependencies
├── tests/                        # Automated Pytest Suite
│   ├── conftest.py
│   ├── test_applications.py
│   ├── test_auth.py
│   ├── test_verification.py
│   ├── test_payment.py
│   └── test_logs.py
├── .env                          # Active Environment Variables
├── .env.example                  # Environment Template
├── requirements.txt              # Dependency Manifest
└── README.md                     # Backend Documentation
```

---

## Environment Variables

All secrets reside exclusively in `backend/.env`. Example template (`.env.example`):

```env
APP_NAME=unified-service
ENVIRONMENT=development
PORT=8000

# Database Configuration (PostgreSQL in Production, SQLite for local dev/testing)
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/unified_service_db

# Security & JWT Configuration
JWT_SECRET=super-secret-jwt-key-change-this-in-production-32-bytes
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7

# Payment Provider Secrets
PAYMENT_SECRET_KEY=sk_test_mock_payment_provider_secret_key_12345
PAYMENT_WEBHOOK_SECRET=whsec_mock_payment_webhook_secret_key_67890

# Verification / Email Provider
EMAIL_API_KEY=mock_email_api_key_abc123

# External Services
EXTERNAL_API_KEY=mock_external_service_key_xyz789
```

---

## Setup & Running Locally

### 1. Create Virtual Environment & Install Dependencies

```bash
cd backend
python -m venv .venv

# On Windows PowerShell:
.\.venv\Scripts\Activate.ps1

# On Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Run the Development Server

```bash
uvicorn src.main:app --reload --port 8000
```

Interactive API documentation (Swagger UI) is available at:
`http://localhost:8000/docs`

---

## Running Automated Tests

Run the complete pytest test suite:

```bash
python -m pytest tests/ -v
```

---

## REST API Endpoints Summary

### Health Check
- `GET /api/health`: Health status & DB connectivity test.

### Application API Keys
- `POST /api/applications/keys`: Generate a new application API key. Returns plaintext key once.
- `GET /api/applications/keys`: List registered application keys.
- `DELETE /api/applications/keys/{id}`: Revoke an application API key.

### Authentication
- `POST /api/auth/register`: Register user under central identity (Header: `X-Application-Key`).
- `POST /api/auth/login`: Authenticate credentials & generate JWT tokens (Header: `X-Application-Key`).
- `POST /api/auth/refresh`: Refresh access token using refresh token (Header: `X-Application-Key`).
- `POST /api/auth/logout`: Invalidate session.
- `GET /api/auth/me`: Fetch profile of logged in user (Header: `Authorization: Bearer <JWT>`).

### Account Verification
- `POST /api/verification/send`: Issue verification token (Header: `X-Application-Key`).
- `POST /api/verification/verify`: Validate verification token and mark user `is_verified = true` (Header: `X-Application-Key`).

### Payment Handling
- `POST /api/payment/create`: Initialize payment intent (Header: `X-Application-Key`).
- `GET /api/payment/status/{payment_id}`: Query payment status (Header: `X-Application-Key`).
- `POST /api/payment/webhook`: Receive provider webhook events with HMAC signature verification (Header: `X-Signature`).

### Centralized Logging
- `POST /api/logs`: Record log entry with automatic secret redaction (Header: `X-Application-Key`).
