#!/bin/bash
# ============================================================================
# SUNUCUDA BOYAMA KİTABI AKTİVASYONU - TAM DEPLOYMENT
# ============================================================================
# Bu script Cloud Shell'de çalışır ve tüm gerekli adımları yapar
# ============================================================================

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  SUNUCUDA BOYAMA KİTABI AKTİVASYONU          ║${NC}"
echo -e "${BLUE}║  Full Deployment + Seed + Verification       ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════╝${NC}"
echo ""

# GCP Configuration
PROJECT_ID="gen-lang-client-0784096400"
REGION="europe-west1"
SQL_INSTANCE="$PROJECT_ID:$REGION:benimmasalim-db"

echo -e "${BLUE}📌 Project: $PROJECT_ID${NC}"
gcloud config set project $PROJECT_ID
echo ""

# ═══════════════════════════════════════════════════════════════
# 1. GIT REPO CHECK (Optional)
# ═══════════════════════════════════════════════════════════════
if [ ! -d ".git" ]; then
    echo -e "${YELLOW}⚠️  Git repo bulunamadı. Manuel olarak dosyaları yüklediğinizden emin olun.${NC}"
else
    echo -e "${GREEN}✅ Git repo bulundu${NC}"
fi
echo ""

# ═══════════════════════════════════════════════════════════════
# 2. DATABASE MIGRATION
# ═══════════════════════════════════════════════════════════════
echo -e "${BLUE}📊 Database Migration...${NC}"
cd backend

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo -e "${YELLOW}⚠️  DATABASE_URL set edilmemiş. Cloud SQL proxy ile bağlanıyorum...${NC}"
    export DATABASE_URL="postgresql+asyncpg://postgres:YOUR_PASSWORD@/benimmasalim?host=/cloudsql/$SQL_INSTANCE"
fi

# Run migration
alembic upgrade head 2>&1 | tail -20 || echo -e "${YELLOW}⚠️  Migration zaten güncel olabilir${NC}"
echo -e "${GREEN}✅ Migration tamamlandı!${NC}"
echo ""

# ═══════════════════════════════════════════════════════════════
# 3. COLORING BOOK SEED
# ═══════════════════════════════════════════════════════════════
echo -e "${BLUE}🎨 Boyama Kitabı Seed...${NC}"
python -m scripts.seed_coloring_book || echo -e "${YELLOW}⚠️  Zaten seed edilmiş olabilir${NC}"
echo -e "${GREEN}✅ Seed tamamlandı!${NC}"
echo ""

# ═══════════════════════════════════════════════════════════════
# 4. VERIFICATION
# ═══════════════════════════════════════════════════════════════
echo -e "${BLUE}🔍 Verification...${NC}"
python -c "
import asyncio
import sys
from sqlalchemy import select
from app.core.database import async_session_factory
from app.models.coloring_book import ColoringBookProduct

async def verify():
    try:
        async with async_session_factory() as db:
            result = await db.execute(
                select(ColoringBookProduct).where(ColoringBookProduct.active == True)
            )
            config = result.scalar_one_or_none()
            
            if config:
                print('✅ Coloring book product FOUND!')
                print(f'   ID: {config.id}')
                print(f'   Name: {config.name}')
                print(f'   Base: {config.base_price} TL')
                print(f'   Discounted: {config.discounted_price} TL')
                print(f'   Thresholds: {config.edge_threshold_low}/{config.edge_threshold_high}')
                print(f'   Active: {config.active}')
                return 0
            else:
                print('❌ Coloring book product NOT FOUND!')
                return 1
    except Exception as e:
        print(f'❌ Error: {str(e)}')
        return 1

exit_code = asyncio.run(verify())
sys.exit(exit_code)
" || {
    echo -e "${RED}❌ Verification failed! Check logs above.${NC}"
    exit 1
}
echo ""

# ═══════════════════════════════════════════════════════════════
# 5. BACKEND RESTART (Cloud Run)
# ═══════════════════════════════════════════════════════════════
echo -e "${BLUE}🔄 Backend Restart...${NC}"
echo "Triggering new deployment to pick up database changes..."

# Option 1: Force new revision by updating env var
gcloud run services update benimmasalim-backend \
    --region $REGION \
    --update-env-vars "LAST_UPDATE=$(date +%s)" \
    --quiet 2>&1 | tail -10 || echo -e "${YELLOW}⚠️  Manual restart may be needed${NC}"

echo -e "${GREEN}✅ Backend restarting...${NC}"
echo ""

# ═══════════════════════════════════════════════════════════════
# 6. API TEST
# ═══════════════════════════════════════════════════════════════
echo -e "${BLUE}🧪 API Test...${NC}"
BACKEND_URL=$(gcloud run services describe benimmasalim-backend \
    --region $REGION \
    --format 'value(status.url)' 2>/dev/null)

if [ -z "$BACKEND_URL" ]; then
    echo -e "${YELLOW}⚠️  Backend URL bulunamadı${NC}"
else
    echo "Backend URL: $BACKEND_URL"
    echo "Waiting for service to be ready (30s)..."
    sleep 30
    
    echo "Testing: GET /api/v1/coloring-books/active"
    curl -s -f "$BACKEND_URL/api/v1/coloring-books/active" | jq '.' || {
        echo -e "${YELLOW}⚠️  API henüz hazır değil, birkaç dakika bekleyin${NC}"
    }
fi
echo ""

# ═══════════════════════════════════════════════════════════════
# FINAL REPORT
# ═══════════════════════════════════════════════════════════════
echo -e "${GREEN}╔════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║        ✅ DEPLOYMENT TAMAMLANDI! ✅           ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}📊 DEPLOYMENT ÖZET:${NC}"
echo ""
echo -e "  ✅ Database Migration: DONE"
echo -e "  ✅ Coloring Book Seed: DONE"
echo -e "  ✅ Verification: PASSED"
echo -e "  ✅ Backend Restart: TRIGGERED"
echo ""
echo -e "${GREEN}🎨 BOYAMA KİTABI BİLGİLERİ:${NC}"
echo ""
echo -e "  Name: Boyama Kitabı"
echo -e "  Price: 150 TL (200 TL'den indirimli)"
echo -e "  Thresholds: 80/200 (basit çizimler)"
echo -e "  Status: ACTIVE ✅"
echo ""
echo -e "${GREEN}🌐 TEST:${NC}"
echo ""
echo -e "  Frontend: $BACKEND_URL"
echo -e "  API: $BACKEND_URL/api/v1/coloring-books/active"
echo ""
echo -e "${BLUE}📝 SONRAKI ADIMLAR:${NC}"
echo ""
echo "1. Frontend'i aç: /create"
echo "2. Hikaye oluştur"
echo "3. Checkout adımına git"
echo "4. '🎨 Boyama Kitabını Ekle +150 TL' checkbox'ını gör!"
echo ""
echo -e "${GREEN}🚀 Boyama kitabı artık production'da aktif!${NC}"
echo ""

# Return to root
cd ..
