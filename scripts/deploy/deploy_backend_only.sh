#!/bin/bash
set -e

echo "🎨 BOYAMA KİTABI - BACKEND BUILD & MIGRATION"
echo "============================================="
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Project bilgilerini al
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}❌ Google Cloud project bulunamadı!${NC}"
    echo "Lütfen: gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi

REGION="europe-west1"
REPO="benimmasalim"

echo -e "${BLUE}📋 Project: $PROJECT_ID${NC}"
echo ""

# 1. Backend build
echo -e "${BLUE}🏗️  Backend build ediliyor...${NC}"
cd backend

gcloud builds submit \
  --tag=$REGION-docker.pkg.dev/$PROJECT_ID/$REPO/backend:latest \
  .

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Build başarısız!${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}✅ Build tamamlandı${NC}"
cd ..
echo ""

# 2. Migration için Cloud SQL'e bağlan ve çalıştır
echo -e "${BLUE}🗄️  Migration çalıştırılıyor...${NC}"
echo ""
echo -e "${YELLOW}Şimdi iki seçenek var:${NC}"
echo ""
echo "A) Cloud Shell'den migration çalıştır:"
echo -e "${BLUE}   gcloud cloud-shell ssh --command='cd /workspace/backend && python -m scripts.update_coloring_book_product'${NC}"
echo ""
echo "B) Yerel makineden Cloud SQL Proxy ile:"
echo -e "${BLUE}   cloud_sql_proxy -instances=$PROJECT_ID:$REGION:benimmasalim-db=tcp:5432 &${NC}"
echo -e "${BLUE}   export DATABASE_URL='postgresql+asyncpg://...'${NC}"
echo -e "${BLUE}   cd backend && python -m scripts.update_coloring_book_product${NC}"
echo ""

read -p "Migration'ı şimdi Cloud Shell'den çalıştırmalı mıyım? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo -e "${BLUE}Cloud Shell'e bağlanıyor...${NC}"
    gcloud cloud-shell ssh --command="cd /workspace/backend && python -m scripts.update_coloring_book_product"
    
    if [ $? -eq 0 ]; then
        echo ""
        echo -e "${GREEN}✅ Migration tamamlandı${NC}"
    else
        echo ""
        echo -e "${YELLOW}⚠️  Migration hatası. Manuel olarak çalıştırmanız gerekebilir.${NC}"
    fi
fi

echo ""

# 3. Cloud Run'a deploy
echo -e "${BLUE}🚀 Backend Cloud Run'a deploy ediliyor...${NC}"
echo ""

gcloud run deploy benimmasalim-backend \
  --image=$REGION-docker.pkg.dev/$PROJECT_ID/$REPO/backend:latest \
  --region=$REGION \
  --platform=managed \
  --allow-unauthenticated \
  --memory=2Gi \
  --cpu=2 \
  --min-instances=1 \
  --max-instances=100 \
  --set-cloudsql-instances=$PROJECT_ID:$REGION:benimmasalim-db

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Backend deploy başarısız!${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}✅ Backend deploy tamamlandı${NC}"
echo ""

echo -e "${BLUE}🚀 Worker Cloud Run'a deploy ediliyor...${NC}"
echo ""

gcloud run deploy benimmasalim-worker \
  --image=$REGION-docker.pkg.dev/$PROJECT_ID/$REPO/backend:latest \
  --region=$REGION \
  --platform=managed

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Worker deploy başarısız!${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}✅ Worker deploy tamamlandı${NC}"
echo ""

# Health check
BACKEND_URL=$(gcloud run services describe benimmasalim-backend --region=$REGION --format='value(status.url)')

echo -e "${BLUE}🏥 Health check...${NC}"
curl -sf $BACKEND_URL/health >/dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Backend sağlıklı!${NC}"
else
    echo -e "${RED}❌ Health check başarısız!${NC}"
fi

echo ""
echo -e "${GREEN}=============================================${NC}"
echo -e "${GREEN}✅ BACKEND DEPLOYMENT TAMAMLANDI!${NC}"
echo -e "${GREEN}=============================================${NC}"
echo ""
echo "Backend URL: $BACKEND_URL"
echo ""
echo -e "${BLUE}Test için:${NC}"
echo "curl $BACKEND_URL/api/v1/coloring-books"
echo ""
