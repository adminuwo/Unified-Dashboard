# Deploying Unified Dashboard to GCP Cloud Run

This guide outlines the step-by-step procedure to deploy the **Unified Dashboard** (FastAPI Backend + React Vite Frontend) to **Google Cloud Run**.

---

## 📋 Prerequisites

1. **Google Cloud SDK (`gcloud` CLI)** installed and authenticated:
   ```bash
   gcloud auth login
   gcloud auth application-default login
   ```
2. **Active GCP Project**:
   ```bash
   gcloud config set project YOUR_GCP_PROJECT_ID
   ```
3. **MongoDB Instance**:
   - Cloud Run containers are stateless. A persistent MongoDB database is required (e.g., [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) or GCP Compute Engine MongoDB instance).
   - Obtain your MongoDB connection string (e.g., `mongodb+srv://<user>:<password>@cluster.mongodb.net/unified_service_db`).

---

## 🚀 Quick One-Command Deployment

We provide automated deployment scripts for Windows, Linux, macOS, and GCP Cloud Shell:

### On Windows (PowerShell):
```powershell
$env:GCP_PROJECT_ID="YOUR_GCP_PROJECT_ID"
.\deploy-cloudrun.ps1
```

### On Linux / macOS / Cloud Shell (Bash):
```bash
export GCP_PROJECT_ID="YOUR_GCP_PROJECT_ID"
chmod +x deploy-cloudrun.sh
./deploy-cloudrun.sh
```

---

## 🛠️ Step-by-Step Manual Deployment

If you prefer to perform deployment steps manually:

### 1. Enable Required GCP APIs
```bash
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com
```

### 2. Create Artifact Registry Docker Repository
```bash
gcloud artifacts repositories create unified-dashboard-repo \
  --repository-format=docker \
  --location=us-central1 \
  --description="Docker repository for Unified Dashboard"
```

### 3. Build & Submit Container Image using Cloud Build
```bash
gcloud builds submit \
  --tag us-central1-docker.pkg.dev/YOUR_GCP_PROJECT_ID/unified-dashboard-repo/unified-dashboard:latest .
```

### 4. Deploy Image to Cloud Run
```bash
gcloud run deploy unified-dashboard \
  --image us-central1-docker.pkg.dev/YOUR_GCP_PROJECT_ID/unified-dashboard-repo/unified-dashboard:latest \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --port 8080 \
  --set-env-vars ENVIRONMENT=production \
  --set-env-vars MONGODB_URL="YOUR_MONGODB_ATLAS_CONNECTION_STRING" \
  --set-env-vars MONGODB_DB_NAME="unified_service_db" \
  --set-env-vars JWT_SECRET="YOUR_SECURE_RANDOM_JWT_SECRET_32_BYTES"
```

---

## 🔐 Environment Variables & Secrets Configuration

Configure your environment variables directly in Cloud Run or via Secret Manager:

| Variable | Description | Recommended Value / Example |
|---|---|---|
| `ENVIRONMENT` | Application environment | `production` |
| `PORT` | Container listening port (managed by Cloud Run) | `8080` |
| `MONGODB_URL` | Persistent MongoDB URI | `mongodb+srv://admin:pass@cluster.mongodb.net/` |
| `MONGODB_DB_NAME` | Database name | `unified_service_db` |
| `JWT_SECRET` | Secret key for JWT auth tokens | `secure_32_character_random_string` |
| `ALLOWED_ORIGINS` | CORS allowed origins | `https://your-custom-domain.com,*` |
| `PAYMENT_SECRET_KEY` | Razorpay / Stripe secret key | `sk_live_...` |

### Setting Environment Variables after Deployment:
```bash
gcloud run services update unified-dashboard \
  --region us-central1 \
  --set-env-vars MONGODB_URL="mongodb+srv://user:pass@cluster.mongodb.net",JWT_SECRET="super-secret-key"
```

---

## 🔍 Verification & Health Checks

- **App Interface**: Navigate to the service URL printed at the end of deployment (e.g. `https://unified-dashboard-xyz-uc.a.run.app/app/`).
- **Health Check Endpoint**: Test health endpoint at `https://unified-dashboard-xyz-uc.a.run.app/api/health`.

Response format:
```json
{
  "status": "ok",
  "service": "unified-service",
  "environment": "production",
  "database": "connected"
}
```

---

## ⚙️ Architecture & Features

- **Multi-Stage Docker Build**: First stage builds React/Vite frontend static assets into `/dist`. Second stage packages Python 3.11 backend with production static files mounted seamlessly under `/app`.
- **Stateless Scaling**: Automatically scales from 0 to N instances based on web traffic.
- **Port Mapping**: Dynamically binds Uvicorn to `${PORT:-8080}` as required by Cloud Run runtime contract.
