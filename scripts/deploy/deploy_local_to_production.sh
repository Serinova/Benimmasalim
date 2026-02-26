#!/bin/bash
set -e

echo "🎨 BOYAMA KİTABI - FULL BUILD & DEPLOY"
echo "======================================="
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
    echo "Lütfen şu komutu çalıştırın: gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi

REGION="europe-west1"
REPO="benimmasalim"
TAG="latest"

echo -e "${BLUE}📋 Build Bilgileri:${NC}"
echo "   Project ID: $PROJECT_ID"
echo "   Region: $REGION"
echo "   Repository: $REPO"
echo "   Tag: $TAG"
echo ""

# Onay iste
read -p "Build başlasın mı? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "İptal edildi."
    exit 0
fi

echo ""
echo -e "${BLUE}🏗️  1/4 - Docker image'ları build ediliyor...${NC}"
echo ""

# Cloud Build ile build et
gcloud builds submit \
  --config=cloudbuild.yaml \
  --substitutions=_REGION=$REGION,_REPO=$REPO,_TAG=$TAG \
  .

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Build başarısız!${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}✅ Build tamamlandı${NC}"
echo ""

# Database migration için backend container'ı geçici çalıştır
echo -e "${BLUE}🗄️  2/4 - Database migration çalıştırılıyor...${NC}"
echo ""

# Cloud SQL Proxy üzerinden migration çalıştır
# NOT: Bu bölüm için DATABASE_URL environment variable gerekli
echo -e "${YELLOW}⚠️  Database migration için Cloud Shell'den şu komutu çalıştırın:${NC}"
echo ""
echo -e "${BLUE}gcloud compute ssh <sunucu-adı> --zone=europe-west1-b --command='cd /workspace/backend && python -m scripts.update_coloring_book_product'${NC}"
echo ""
echo "veya"
echo ""
echo -e "${BLUE}gcloud cloud-shell ssh --command='cd /workspace && bash deploy_coloring_product.sh'${NC}"
echo ""

read -p "Migration tamamlandı mı? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}⚠️  Migration'ı manuel olarak çalıştırmanız gerekiyor.${NC}"
fi

echo ""
echo -e "${BLUE}🚀 3/4 - Backend Cloud Run'a deploy ediliyor...${NC}"
echo ""

gcloud run deploy benimmasalim-backend \
  --image=$REGION-docker.pkg.dev/$PROJECT_ID/$REPO/backend:$TAG \
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

echo -e "${BLUE}🌐 4/4 - Frontend Cloud Run'a deploy ediliyor...${NC}"
echo ""

# Backend URL'i al ve frontend'e environment variable olarak ver
BACKEND_URL=$(gcloud run services describe benimmasalim-backend --region=$REGION --format='value(status.url)')

gcloud run deploy benimmasalim-frontend \
  --image=$REGION-docker.pkg.dev/$PROJECT_ID/$REPO/frontend:$TAG \
  --region=$REGION \
  --platform=managed \
  --allow-unauthenticated \
  --memory=1Gi \
  --cpu=1 \
  --min-instances=0 \
  --max-instances=50 \
  --set-env-vars="NEXT_PUBLIC_API_URL=$BACKEND_URL"

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Frontend deploy başarısız!${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}✅ Frontend deploy tamamlandı${NC}"
echo ""

# Health check
echo -e "${BLUE}🏥 Health check yapılıyor...${NC}"
echo ""

FRONTEND_URL=$(gcloud run services describe benimmasalim-frontend --region=$REGION --format='value(status.url)')

curl -sf $BACKEND_URL/health >/dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Backend sağlıklı!${NC}"
else
    echo -e "${RED}❌ Backend health check başarısız!${NC}"
fi

curl -sf $FRONTEND_URL >/dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Frontend sağlıklı!${NC}"
else
    echo -e "${RED}❌ Frontend health check başarısız!${NC}"
fi

echo ""
echo -e "${GREEN}=======================================${NC}"
echo -e "${GREEN}✅ DEPLOYMENT TAMAMLANDI!${NC}"
echo -e "${GREEN}=======================================${NC}"
echo ""
echo -e "${BLUE}🌐 URLs:${NC}"
echo "   Backend:  $BACKEND_URL"
echo "   Frontend: $FRONTEND_URL"
echo ""
echo -e "${BLUE}📋 Test için:${NC}"
echo "   $BACKEND_URL/api/v1/coloring-books"
echo ""
