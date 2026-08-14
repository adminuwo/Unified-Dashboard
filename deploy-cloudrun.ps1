# PowerShell script to deploy Unified Dashboard to Google Cloud Run
$ErrorActionPreference = "Stop"

# Configuration Defaults (Override via environment variables if desired)
$ProjectId = $env:GCP_PROJECT_ID
if ([string]::IsNullOrWhiteSpace($ProjectId)) {
    $ProjectId = (gcloud config get-value project 2>$null)
}

$Region = if ($env:GCP_REGION) { $env:GCP_REGION } else { "us-central1" }
$ServiceName = if ($env:SERVICE_NAME) { $env:SERVICE_NAME } else { "unified-dashboard" }
$RepoName = if ($env:REPO_NAME) { $env:REPO_NAME } else { "unified-dashboard-repo" }
$ImageName = "${Region}-docker.pkg.dev/${ProjectId}/${RepoName}/${ServiceName}:latest"

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host " Deploying Unified Dashboard to GCP Cloud Run" -ForegroundColor Cyan
Write-Host " Project ID:   $ProjectId" -ForegroundColor Yellow
Write-Host " Region:       $Region" -ForegroundColor Yellow
Write-Host " Service Name: $ServiceName" -ForegroundColor Yellow
Write-Host " Image:        $ImageName" -ForegroundColor Yellow
Write-Host "========================================================" -ForegroundColor Cyan

if ([string]::IsNullOrWhiteSpace($ProjectId)) {
    Write-Error "GCP Project ID is not set. Run 'gcloud config set project YOUR_PROJECT_ID' or set \$env:GCP_PROJECT_ID."
    exit 1
}

Write-Host "1. Enabling required GCP Service APIs..." -ForegroundColor Green
gcloud services enable run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com --project=$ProjectId

Write-Host "2. Ensuring Artifact Registry repository exists..." -ForegroundColor Green
$repoExists = gcloud artifacts repositories describe $RepoName --location=$Region --project=$ProjectId 2>$null
if (-not $repoExists) {
    gcloud artifacts repositories create $RepoName `
      --repository-format=docker `
      --location=$Region `
      --description="Docker repository for Unified Dashboard" `
      --project=$ProjectId
}

Write-Host "3. Building and submitting image via Cloud Build..." -ForegroundColor Green
gcloud builds submit --tag $ImageName --project=$ProjectId .

Write-Host "4. Deploying service to Cloud Run..." -ForegroundColor Green
gcloud run deploy $ServiceName `
  --image=$ImageName `
  --region=$Region `
  --platform=managed `
  --allow-unauthenticated `
  --port=8080 `
  --project=$ProjectId

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host " Deployment Complete!" -ForegroundColor Cyan
Write-Host " Service URL:" -ForegroundColor Yellow
gcloud run services describe $ServiceName --region=$Region --project=$ProjectId --format='value(status.url)'
Write-Host "========================================================" -ForegroundColor Cyan
