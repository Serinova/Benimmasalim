#!/usr/bin/env bash
# deploy_production.sh — Benim Masalım Full Deploy (Backend + Frontend)
# PowerShell: bash deploy_production.sh  veya  ./deploy_production.sh
# -------------------------------------------------------

set -e

PROJECT_ID="gen-lang-client-0784096400"
REGION="europe-west1"
REPO="benimmasalim"
BACKEND_IMAGE="europe-west1-docker.pkg.dev/${PROJECT_ID}/${REPO}/backend:latest"
FRONTEND_IMAGE="europe-west1-docker.pkg.dev/${PROJECT_ID}/${REPO}/frontend:latest"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=================================================="
echo "🚀 BenimMasalim Production Deploy"
echo "=================================================="

# ── Backend Build ──────────────────────────────────────
echo ""
echo "📦 Backend image build başlatılıyor..."
gcloud builds submit \
  --tag "${BACKEND_IMAGE}" \
  --timeout=20m \
  "${SCRIPT_DIR}/backend"

echo "✅ Backend image build tamamlandı."

# ── Frontend Build (cloudbuild.yaml: BACKEND URL + CSP uyumlu) ──
echo ""
echo "📦 Frontend image build başlatılıyor..."
gcloud builds submit \
  --config "${SCRIPT_DIR}/frontend/cloudbuild.yaml" \
  --timeout=20m \
  "${SCRIPT_DIR}/frontend"

echo "✅ Frontend image build tamamlandı."

# ── Cloud Run Deploy ───────────────────────────────────
# Not: update ile yeni revision oluşur ve varsayılan olarak %100 trafik yeni revision'a gider.
# Backend start.sh her ayağa kalkışta "alembic upgrade head" çalıştırır; migration'lar otomatik uygulanır.
echo ""
echo "🚀 Cloud Run servisleri güncelleniyor (trafik yeni revision'a yönlenir)..."

gcloud run services update benimmasalim-backend \
  --image "${BACKEND_IMAGE}" \
  --region "${REGION}" \
  --project "${PROJECT_ID}" \
  --min-instances=1 \
  --max-instances=10
echo "  ✓ benimmasalim-backend"

gcloud run services update benimmasalim-worker \
  --image "${BACKEND_IMAGE}" \
  --region "${REGION}" \
  --project "${PROJECT_ID}" \
  --min-instances=2 \
  --max-instances=5
echo "  ✓ benimmasalim-worker"

gcloud run services update benimmasalim-frontend \
  --image "${FRONTEND_IMAGE}" \
  --region "${REGION}" \
  --project "${PROJECT_ID}" \
  --min-instances=1 \
  --max-instances=5
echo "  ✓ benimmasalim-frontend"

echo ""
echo "=================================================="
echo "✅ Deploy tamamlandı!"
echo ""
echo "Backend:  $(gcloud run services describe benimmasalim-backend --region=${REGION} --format='value(status.url)')"
echo "Frontend: $(gcloud run services describe benimmasalim-frontend --region=${REGION} --format='value(status.url)')"
echo "=================================================="
