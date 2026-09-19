#!/bin/sh
set -e

export PORT="${PORT:-8080}"
export BACKEND_API_URL="${BACKEND_API_URL:-https://uwo24.com}"
# Strip trailing slash if present
export BACKEND_API_URL=$(echo "$BACKEND_API_URL" | sed 's:/*$::')

echo "=========================================================="
echo "🚀 Starting Unified Dashboard UI Container"
echo "🌐 Cloud Run PORT    : ${PORT}"
echo "🔗 Backend Proxy URL : ${BACKEND_API_URL}"
echo "=========================================================="

# Substitute ${PORT} and ${BACKEND_API_URL} in nginx config
envsubst '${PORT} ${BACKEND_API_URL}' < /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf

echo "🌟 Starting Nginx web server..."
exec nginx -g 'daemon off;'
