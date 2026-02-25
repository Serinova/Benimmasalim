#!/bin/bash
set -e

echo "🚀 BENİMMASALIM PRODUCTION DEPLOYMENT BAŞLIYOR..."
echo "================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Repository güncelle
echo -e "${BLUE}📥 Repository güncelleniyor...${NC}"
cd /workspace
git pull origin main
echo -e "${GREEN}✅ Git pull tamamlandı${NC}"
echo ""

# 2. Backend migration'ları çalıştır
echo -e "${BLUE}📊 Database migration'ları çalıştırılıyor...${NC}"
cd backend

# DATABASE_URL'in set olduğundan emin ol
if [ -z "$DATABASE_URL" ]; then
    echo -e "${YELLOW}⚠️  DATABASE_URL environment variable bulunamadı!${NC}"
    echo "Lütfen ayarlayın: export DATABASE_URL='postgresql+asyncpg://...'"
    exit 1
fi

echo -e "${GREEN}✅ DATABASE_URL found${NC}"
echo ""

# Migration scriptlerini çalıştır
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

TOTAL=${#SCENARIOS[@]}
CURRENT=0

for scenario in "${SCENARIOS[@]}"; do
    CURRENT=$((CURRENT + 1))
    echo -e "${BLUE}[$CURRENT/$TOTAL] Migration: ${scenario}...${NC}"
    
    python -m scripts.update_${scenario}_scenario
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ ${scenario} tamamlandı${NC}"
    else
        echo -e "${YELLOW}⚠️  ${scenario} hata aldı, devam ediliyor...${NC}"
    fi
    echo ""
done

echo -e "${GREEN}✅ Tüm migration'lar tamamlandı!${NC}"
echo ""

# 3. Docker build
echo -e "${BLUE}🏗️  Backend Docker build başlıyor...${NC}"
cd /workspace/backend

# Project ID'yi al
PROJECT_ID=$(gcloud config get-value project)
echo "Project ID: $PROJECT_ID"

gcloud builds submit --tag gcr.io/$PROJECT_ID/benimmasalim-backend:latest

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Docker build tamamlandı${NC}"
else
    echo -e "${YELLOW}⚠️  Docker build hatası!${NC}"
    exit 1
fi
echo ""

# 4. Cloud Run deploy
echo -e "${BLUE}🚀 Cloud Run'a deploy ediliyor...${NC}"

gcloud run deploy benimmasalim-backend \
  --image gcr.io/$PROJECT_ID/benimmasalim-backend:latest \
  --region europe-west1 \
  --platform managed \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --min-instances 1 \
  --max-instances 100 \
  --set-cloudsql-instances $PROJECT_ID:europe-west1:benimmasalim-db

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Cloud Run deploy tamamlandı${NC}"
else
    echo -e "${YELLOW}⚠️  Cloud Run deploy hatası!${NC}"
    exit 1
fi
echo ""

# 5. Health check
echo -e "${BLUE}🏥 Health check yapılıyor...${NC}"
BACKEND_URL=$(gcloud run services describe benimmasalim-backend --region europe-west1 --format 'value(status.url)')
echo "Backend URL: $BACKEND_URL"

curl -f $BACKEND_URL/health
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Backend sağlıklı!${NC}"
else
    echo -e "${YELLOW}⚠️  Health check başarısız!${NC}"
fi
echo ""

# 6. Scenarios endpoint test
echo -e "${BLUE}📋 Scenarios endpoint test ediliyor...${NC}"
curl -f $BACKEND_URL/api/scenarios | jq '.[] | {name: .name, theme_key: .theme_key}'

echo ""
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}✅ DEPLOYMENT TAMAMLANDI!${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo "Backend URL: $BACKEND_URL"
echo "13 yeni senaryo production'da! 🎉"
echo ""
echo "Test için: $BACKEND_URL/api/scenarios"
