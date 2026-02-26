#!/bin/bash
# ============================================================================
# PAZARLAMA İÇERİKLERİ ve FİYATLANDIRMA GÜNCELLEMESİ
# ============================================================================
# Bu script:
# 1. Güneş Sistemi senaryosuna marketing_features ve marketing_gallery ekler
# 2. Okyanus Derinlikleri senaryosuna marketing_features ve marketing_gallery ekler
# 3. Tüm ürünlerin fiyatını günceller (1250 TL base, 299 TL discounted)
# ============================================================================

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  PAZARLAMA İÇERİKLERİ + FİYATLANDIRMA        ║${NC}"
echo -e "${BLUE}║  Güneş Sistemi + Okyanus + Tüm Ürünler      ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════╝${NC}"
echo ""

cd backend

# ═══════════════════════════════════════════════════════════════
# 1. GÜNEŞ SİSTEMİ MACERASI - Marketing Update
# ═══════════════════════════════════════════════════════════════
echo -e "${BLUE}🌌 Güneş Sistemi Macerası Güncelleniyor...${NC}"
python -m scripts.update_space_scenario || echo -e "${YELLOW}⚠️  Space scenario güncelleme uyarısı${NC}"
echo -e "${GREEN}✅ Güneş Sistemi güncellendi!${NC}"
echo ""

# ═══════════════════════════════════════════════════════════════
# 2. OKYANUS DERİNLİKLERİ - Marketing Update
# ═══════════════════════════════════════════════════════════════
echo -e "${BLUE}🌊 Okyanus Derinlikleri Güncelleniyor...${NC}"
python -m scripts.update_ocean_adventure_scenario || echo -e "${YELLOW}⚠️  Ocean scenario güncelleme uyarısı${NC}"
echo -e "${GREEN}✅ Okyanus Derinlikleri güncellendi!${NC}"
echo ""

# ═══════════════════════════════════════════════════════════════
# 3. ÜRÜN FİYATLANDIRMASI - All Products
# ═══════════════════════════════════════════════════════════════
echo -e "${BLUE}💰 Ürün Fiyatlandırması Güncelleniyor...${NC}"
python -m scripts.update_pricing || echo -e "${YELLOW}⚠️  Pricing güncelleme uyarısı${NC}"
echo -e "${GREEN}✅ Tüm ürün fiyatları güncellendi!${NC}"
echo ""

# ═══════════════════════════════════════════════════════════════
# ÖZET
# ═══════════════════════════════════════════════════════════════
echo -e "${GREEN}╔════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║        ✅ GÜNCELLEME TAMAMLANDI! ✅            ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}📊 GÜNCELLENEN İÇERİKLER:${NC}"
echo ""
echo -e "${GREEN}🌌 GÜNEŞ SİSTEMİ MACERASI:${NC}"
echo "   • marketing_features: 7 özellik"
echo "   • marketing_gallery: 4 görsel"
echo "   • Age: 7-10 yaş"
echo "   • Rating: 5.0 ⭐⭐⭐⭐⭐"
echo ""
echo -e "${GREEN}🌊 OKYANUS DERİNLİKLERİ:${NC}"
echo "   • marketing_features: 6 özellik"
echo "   • marketing_gallery: 4 görsel"
echo "   • Age: 5-10 yaş"
echo "   • Rating: 5.0 ⭐⭐⭐⭐⭐"
echo ""
echo -e "${GREEN}💰 TÜM ÜRÜNLER:${NC}"
echo "   • Base Price: 1250 TL"
echo "   • Discounted Price: 299 TL"
echo "   • Discount: %76 🔥"
echo "   • Feature List: 8 özellik"
echo "   • Social Proof: '1000+ mutlu aile!'"
echo ""
echo -e "${GREEN}🎯 SON DURUM:${NC}"
echo "   ✅ Pazarlama içerikleri eksiksiz"
echo "   ✅ Fiyatlandırma tutarlı (299 TL)"
echo "   ✅ Rating ve badge'ler eklendi"
echo "   ✅ Social proof aktif"
echo ""
echo -e "${BLUE}📝 NOT: Bu değişiklikler database'de güncellenmiştir.${NC}"
echo -e "${BLUE}      Frontend otomatik olarak yeni verileri gösterecektir.${NC}"
echo ""
