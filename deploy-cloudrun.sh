#!/usr/bin/env bash
# Deploy Unified Dashboard to Google Cloud Run
set -e

# Configuration Defaults (Override via environment variables if desired)
PROJECT_ID=${GCP_PROJECT_ID:-$(gcloud config get-value project 2>/dev/null)}
REGION=${GCP_REGION:-"us-central1"}
SERVICE_NAME=${SERVICE_NAME:-"unified-dashboard"}
REPO_NAME=${REPO_NAME:-"unified-dashboard-repo"}
IMAGE_NAME="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${SERVICE_NAME}:latest"

echo "========================================================"
echo " Deploying Unified Dashboard to GCP Cloud Run"
echo " Project ID:   ${PROJECT_ID}"
echo " Region:       ${REGION}"
echo " Service Name: ${SERVICE_NAME}"
echo " Image:        ${IMAGE_NAME}"
echo "========================================================"

if [ -z "${PROJECT_ID}" ]; then
  echo "Error: GCP Project ID is not set. Run 'gcloud config set project YOUR_PROJECT_ID' or set GCP_PROJECT_ID env var."
  exit 1
fi

echo "1. Enabling required GCP Service APIs..."
gcloud services enable run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com --project="${PROJECT_ID}"

echo "2. Ensuring Artifact Registry repository exists..."
gcloud artifacts repositories describe "${REPO_NAME}" --location="${REGION}" --project="${PROJECT_ID}" >/dev/null 2>&1 || \
gcloud artifacts repositories create "${REPO_NAME}" \
  --repository-format=docker \
  --location="${REGION}" \
  --description="Docker repository for Unified Dashboard" \
  --project="${PROJECT_ID}"

echo "3. Building and submitting image via Cloud Build..."
gcloud builds submit --tag "${IMAGE_NAME}" --project="${PROJECT_ID}" .

echo "4. Deploying service to Cloud Run..."
gcloud run deploy "${SERVICE_NAME}" \
  --image="${IMAGE_NAME}" \
  --region="${REGION}" \
  --platform=managed \
  --allow-unauthenticated \
  --port=8080 \
  --project="${PROJECT_ID}"

echo "========================================================"
echo " Deployment Complete!"
echo " Service URL:"
gcloud run services describe "${SERVICE_NAME}" --region="${REGION}" --project="${PROJECT_ID}" --format='value(status.url)'
echo "========================================================"
