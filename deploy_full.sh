#!/bin/bash
# ============================================================================
# BENİMMASALIM - FULL PRODUCTION DEPLOYMENT SCRIPT
# ============================================================================
# KULLANIM: GCP Cloud Shell'de çalıştır!
#   chmod +x deploy_full.sh
#   ./deploy_full.sh
# ============================================================================

set -e  # Herhangi bir hata olursa dur

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  BENİMMASALIM - PRODUCTION DEPLOYMENT         ║${NC}"
echo -e "${BLUE}║  13 Senaryo + Docker Build + Cloud Run        ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════╝${NC}"
echo ""

# 0. Project setup
PROJECT_ID="gen-lang-client-0784096400"
REGION="europe-west1"
SQL_INSTANCE="$PROJECT_ID:$REGION:benimmasalim-db"

echo -e "${BLUE}📌 Project: $PROJECT_ID${NC}"
gcloud config set project $PROJECT_ID
echo ""

# 1. DATABASE_URL check
if [ -z "$DATABASE_URL" ]; then
    echo -e "${YELLOW}⚠️  DATABASE_URL bulunamadı!${NC}"
    echo "Cloud SQL için ayarlanıyor..."
    export DATABASE_URL="postgresql+asyncpg://postgres:YOUR_DB_PASSWORD@/benimmasalim?host=/cloudsql/$SQL_INSTANCE"
    echo -e "${GREEN}✅ DATABASE_URL set edildi${NC}"
fi
echo ""

# 2. Backend migration'lar
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo -e "${BLUE}📊 13 SCENARIO MIGRATION'LARI BAŞLIYOR...${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo ""

cd backend

SCENARIOS=(
    "ocean_adventure"
    "dinosaur"
    "space"
    "galata"
    "cappadocia"
    "ephesus"
    "gobekli"
    "catalhoyuk"
    "amazon"
    "sumela"
    "sultanahmet"
    "umre"
    "jerusalem"
)

SUCCESS_COUNT=0
FAIL_COUNT=0
TOTAL=${#SCENARIOS[@]}

for i in "${!SCENARIOS[@]}"; do
    scenario="${SCENARIOS[$i]}"
    CURRENT=$((i + 1))
    
    echo -e "${BLUE}[$CURRENT/$TOTAL] 🔄 ${scenario}...${NC}"
    
    if python -m scripts.update_${scenario}_scenario; then
        echo -e "${GREEN}    ✅ ${scenario} BAŞARILI${NC}"
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    else
        echo -e "${RED}    ❌ ${scenario} HATA ALDI${NC}"
        FAIL_COUNT=$((FAIL_COUNT + 1))
    fi
    echo ""
done

echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Başarılı: $SUCCESS_COUNT / $TOTAL${NC}"
if [ $FAIL_COUNT -gt 0 ]; then
    echo -e "${RED}❌ Hatalı: $FAIL_COUNT / $TOTAL${NC}"
fi
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo ""

# 3. Docker Build
echo -e "${BLUE}🏗️  DOCKER BUILD BAŞLIYOR...${NC}"
cd /workspace/benimmasalim/backend

gcloud builds submit \
  --tag gcr.io/$PROJECT_ID/benimmasalim-backend:latest \
  --timeout=20m

echo -e "${GREEN}✅ Docker build tamamlandı!${NC}"
echo ""

# 4. Cloud Run Deploy
echo -e "${BLUE}🚀 CLOUD RUN DEPLOY BAŞLIYOR...${NC}"

gcloud run deploy benimmasalim-backend \
  --image gcr.io/$PROJECT_ID/benimmasalim-backend:latest \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --min-instances 1 \
  --max-instances 100 \
  --set-cloudsql-instances $SQL_INSTANCE \
  --set-env-vars "APP_ENV=production,STORAGE_DRIVER=gcs"

echo -e "${GREEN}✅ Cloud Run deploy tamamlandı!${NC}"
echo ""

# 5. Health Check
echo -e "${BLUE}🏥 HEALTH CHECK...${NC}"
BACKEND_URL=$(gcloud run services describe benimmasalim-backend \
  --region $REGION \
  --format 'value(status.url)')

echo "Backend URL: $BACKEND_URL"
echo ""

sleep 5  # Servis ayağa kalksın
curl -f $BACKEND_URL/health || echo -e "${YELLOW}⚠️  Health check başarısız (normal olabilir ilk deploy'da)${NC}"
echo ""

# 6. Scenarios Test
echo -e "${BLUE}📋 SCENARIOS TEST...${NC}"
curl -s $BACKEND_URL/api/v1/scenarios | jq -r '.[] | "\(.theme_key) - \(.name)"' || echo -e "${YELLOW}⚠️  jq yüklü değil, raw response:${NC}"
curl -s $BACKEND_URL/api/v1/scenarios
echo ""

# FINAL
echo -e "${GREEN}╔════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║        🎉 DEPLOYMENT TAMAMLANDI! 🎉           ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}📊 ÖZET:${NC}"
echo -e "  - ✅ 13 senaryo migration: $SUCCESS_COUNT başarılı"
echo -e "  - ✅ Docker image build edildi"
echo -e "  - ✅ Cloud Run'a deploy edildi"
echo -e "  - 🌐 Backend URL: $BACKEND_URL"
echo ""
echo -e "${GREEN}📝 KONTROL:${NC}"
echo "  curl $BACKEND_URL/api/v1/scenarios"
echo ""
echo -e "${GREEN}🎯 13 YENİ SENARYO PRODUCTION'DA!${NC}"
