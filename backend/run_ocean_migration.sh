#!/bin/bash
# Cloud Shell'de çalıştır
# Ocean modular prompts migration

echo "=== CLOUD MIGRATION RUNNER ==="

cd /workspace/backend

# DB bağlantı bilgilerini ayarla (Cloud SQL proxy veya direct)
export DATABASE_URL="postgresql+asyncpg://..."  # Cloud SQL URL buraya

# Migration çalıştır
echo "Running migration: 68f0daf6de81_ocean_modular_prompts_pilot"
alembic upgrade head

# Veya direkt script çalıştır
echo ""
echo "Running update script..."
python -m scripts.update_ocean_adventure_scenario

echo ""
echo "✓ Ocean modular prompts deployed!"
