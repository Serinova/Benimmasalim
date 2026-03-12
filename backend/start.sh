#!/bin/bash
set -e

echo "🚀 Starting backend..."
echo "Running database migrations..."

alembic upgrade head

echo "✅ Migrations complete. Starting server..."

exec python -m gunicorn app.main:app \
     --bind 0.0.0.0:8000 \
     --workers 4 \
     --worker-class uvicorn.workers.UvicornWorker \
     --timeout 120 \
     --graceful-timeout 30 \
     --max-requests 1000 \
     --max-requests-jitter 50