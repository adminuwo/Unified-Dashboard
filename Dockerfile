# Multi-stage Dockerfile for Unified Dashboard (FastAPI Backend + React Vite Frontend)

# --- Stage 1: Build Frontend ---
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm install

COPY frontend/ ./
RUN npm run build

# --- Stage 2: Production Python Backend ---
FROM python:3.11-slim
WORKDIR /app/backend

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy Backend Source Code
COPY backend/ ./

# Copy compiled Frontend dist assets into Backend directory
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist

# Expose container port (GCP Cloud Run defaults to 8080)
EXPOSE 8080

# Set production environment variables
ENV ENVIRONMENT=production
ENV PORT=8080

# Start Uvicorn production server binding dynamically to $PORT
CMD ["sh", "-c", "exec uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8080}"]

