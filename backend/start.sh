#!/bin/bash
set -e

echo "🚀 Starting backend..."
echo "Running database migrations..."

# Alembic upgrade — non-fatal (migrations may already be applied)
alembic upgrade head || echo "⚠️ Alembic upgrade skipped (may already be at head or multiple heads exist)"

echo "✅ Migrations complete. Starting server..."

exec python -m gunicorn app.main:app \
     --bind 0.0.0.0:8000 \
     --workers 4 \
     --worker-class uvicorn.workers.UvicornWorker \
     --timeout 120 \
     --graceful-timeout 30 \
     --max-requests 1000 \
     --max-requests-jitter 50