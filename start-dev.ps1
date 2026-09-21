# Launch both Unified Backend and Unified Frontend development servers
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host " Starting Unified Dashboard & Backend..." -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

# Check venv
if (-not (Test-Path "backend\.venv")) {
    Write-Host "Creating Python virtual environment in backend\.venv..." -ForegroundColor Yellow
    python -m venv backend\.venv
    & ".\backend\.venv\Scripts\pip.exe" install -r backend\requirements.txt
}

# Check frontend node_modules
if (-not (Test-Path "frontend\node_modules")) {
    Write-Host "Installing frontend dependencies..." -ForegroundColor Yellow
    npm --prefix frontend install
}

Write-Host "Launching services with npm run dev..." -ForegroundColor Green
npm run dev
