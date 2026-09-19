# =========================================================================
# Stage 1: Build Frontend SPA (React + Vite + Chart.js)
# =========================================================================
FROM node:20-alpine AS builder

WORKDIR /app

# Copy dependency manifests
COPY frontend/package*.json ./

# Install dependencies
RUN npm ci || npm install

# Copy frontend source code
COPY frontend/ ./

ARG VITE_API_URL=https://uwo24.com
ENV VITE_API_URL=$VITE_API_URL

# Build production bundle (outputs to /app/dist)
RUN npm run build

# =========================================================================
# Stage 2: Production Web Server (High-Performance Nginx Alpine)
# =========================================================================
FROM nginx:alpine AS runner

# Install gettext for envsubst
RUN apk add --no-cache gettext

# Copy compiled assets from builder
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy Nginx configuration template and entrypoint script
COPY nginx.conf.template /etc/nginx/templates/default.conf.template
COPY entrypoint.sh /entrypoint.sh

# Ensure script has Linux line endings and execute permissions
RUN sed -i 's/\r$//' /entrypoint.sh && chmod +x /entrypoint.sh

# Cloud Run default port
ENV PORT=8080
ENV BACKEND_API_URL="https://uwo24.com"

EXPOSE 8080

ENTRYPOINT ["/entrypoint.sh"]
