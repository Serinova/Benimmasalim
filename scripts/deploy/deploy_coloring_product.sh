#!/bin/bash
set -e

echo "🎨 BOYAMA KİTABI ÜRÜN GÜNCELLEME"
echo "================================"
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# DATABASE_URL kontrolü
if [ -z "$DATABASE_URL" ]; then
    echo -e "${YELLOW}⚠️  DATABASE_URL bulunamadı!${NC}"
    echo "Kullanım: export DATABASE_URL='postgresql+asyncpg://...'"
    exit 1
fi

echo -e "${GREEN}✅ DATABASE_URL found${NC}"
echo ""

# Backend dizinine git
cd backend

# Script'i çalıştır
echo -e "${BLUE}🎨 Coloring book product güncelleniyor...${NC}"
python -m scripts.update_coloring_book_product

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}================================${NC}"
    echo -e "${GREEN}✅ Güncelleme tamamlandı!${NC}"
    echo -e "${GREEN}================================${NC}"
else
    echo -e "${YELLOW}❌ Güncelleme başarısız!${NC}"
    exit 1
fi
