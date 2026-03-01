"""
Galata Kulesi Macerasi — Duzeltilmis
=====================================
- Modular prompt (500 char limit, tum placeholder'lar mevcut)
- Outfit: update_all_outfits.py standardi (EXACTLY lock phrase)
- Blueprint hikaye (bolum bolum, dopamin dongusu)
- Cocuk TEK BASINA (aile yok)
"""

import asyncio
import os
import sys
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import select

from app.core.database import async_session_factory
from app.models.scenario import Scenario

# ============================================================================
# MODULAR PROMPT COMPONENTS (500 char limit!)
# ============================================================================

GALATA_COVER_PROMPT = (
    "An {child_age}-year-old {child_gender} named {child_name} "
    "with {hair_description}, wearing {clothing_description}. "
    "{scene_description}. "
    "Galata Tower cylindrical stone body with conical cap in background. "
    "Istanbul panorama: Golden Horn, Bosphorus, ferries, domes and minarets. "
    "Seagulls soaring at eye level. Sunset golden light. "
    "Wide shot: child 25%, tower and city 75%. "
    "Magical Istanbul atmosphere."
)

GALATA_PAGE_PROMPT = (
    "An {child_age}-year-old {child_gender} named {child_name} "
    "with {hair_description}, wearing {clothing_description}. "
    "{scene_description}. "
    "Elements: [Tower: 67m cylindrical stone, conical cap, 360 balcony / "
    "Panorama: Golden Horn, Bosphorus, ferries, domes / "
    "Streets: cobblestone, cafes, street art, cats / "
    "Bridge: Galata Bridge, fishermen, restaurants / "
    "Istiklal: red tram, flower sellers]. "
    "Warm stone grey, Bosphorus blue-green, sunset amber."
)

# ============================================================================
# OUTFIT DEFINITIONS (update_all_outfits.py standardi)
# ============================================================================

OUTFIT_GIRL = (
    "bright cherry-red cotton hoodie with small white heart logo on chest, "
    "dark navy blue denim jeans, white canvas sneakers with red laces, "
    "small light gray backpack on back. "
    "EXACTLY the same outfit on every page — same red hoodie, same navy jeans, same white sneakers."
)

OUTFIT_BOY = (
    "royal blue zip-up cotton jacket over white crew-neck t-shirt, "
    "dark gray cargo pants with side pockets, black and white striped sneakers, "
    "small navy blue backpack on back. "
    "EXACTLY the same outfit on every page — same blue jacket, same gray pants, same striped sneakers."
)

# ============================================================================
# STORY BLUEPRINT
# ============================================================================

GALATA_STORY_PROMPT_TR = """
# GALATA KULESİ MACERASI — İSTANBUL'UN TEPESİNDEN

## TEMEL YAPI: 7 BÖLÜM, 22 SAYFA

Bu hikaye bir İstanbul keşif macerası. {child_name}, Galata Kulesi'nde
bir Bilge Martı (İstanbul'un semalarından 700 yıldır her şeyi gören,
Boğaz'ın hikâyesini bilen eski koruyucu) ile birlikte şehrin
sırlarını keşfeder.

⚠️ ÖNEMLİ KURALLAR:
- Bu bir MACERA hikayesi, gezi rehberi DEĞİL
- Her bölümde çocuk AKTİF katılımcı
- Endişe → Eylem → Başarı döngüsü
- Yardımcı karakter: Bilge Martı (700 yıllık koruyucu)
- Çocuk TEK BAŞINA macerada (aile yok). Anne-baba-aile karakteri KULLANMA.
- Korku/şiddet YOK
- Hezarfen Ahmed Çelebi uçuş efsanesi hikayeye entegre

---

### BÖLÜM 1 — GİRİŞ: GALATA SOKAKLARI (Sayfa 1-4)
{child_name} Galata'nın arnavut kaldırımlı sokaklarında yürüyor.
Sanat galerileri, kediler, sokak müzisyenleri. Kulenin önüne
geliyor — tepesinde bir martı parlıyor. Bilge Martı: "700 yıldır
buradayım. Sana İstanbul'un sırrını göstereyim!"
- S1: Galata sokakları — arnavut kaldırım, kediler
- S2: Sanat galerileri, sokak müzisyenleri
- S3: Kulenin önü — Bilge Martı canlanıyor!
- S4: "700 yıllık sır!" — macera başlıyor ✓ İLK HEYECAN
**Değer**: Merak, keşif

---

### BÖLÜM 2 — KULE İÇİ: SPIRAL MERDİVEN (Sayfa 5-8)
Kulenin içine giriş. Dar taş spiral merdiven, 9 kat yukarı.
Her katta küçük kemerli pencereden farklı manzara. Çocuk
yoruluyor ama Martı: "Her kat yeni bir hikâye!"
- S5: Spiral merdiven — "Çok uzun!" ✓ ENDİŞE
- S6: 3. kat penceresi — ilk manzara parçası
- S7: 6. kat — Hezarfen'in hikâyesi (Martı anlatıyor)
- S8: "Hezarfen buradan UÇTU!" — hayal gücü ✓ HEYECAN ZİRVESİ
**Değer**: Azim, hayal gücü

---

### BÖLÜM 3 — SEYIR TERASİ: 360° PANORAMA (Sayfa 9-12)
Tepeye varış! 67 metre yükseklikte 360° İstanbul panoraması.
Haliç, Boğaz, vapurlar, kubbeler, minareler. Rüzgâr, martılar
göz hizasında. "Uçuyorum gibi!"
- S9: Terasa çıkış — "VAAAY!" ✓ HAYRANLIK DORUĞU
- S10: Haliç ve Galata Köprüsü — balıkçılar, vapurlar
- S11: Boğaz — gemiler, Asya yakası
- S12: Tarihi Yarımada — kubbeler, minareler silüeti
**Değer**: Perspektif, büyük resmi görme

---

### BÖLÜM 4 — HEZARFEN'İN UÇUŞU: HAYAL GÜCÜ (Sayfa 13-16)
Martı, Hezarfen Ahmed Çelebi'nin hikâyesini anlatıyor: 1630'larda
yapay kanatlarla Galata'dan Üsküdar'a uçuş! Çocuk gözlerini
kapatıyor, Hezarfen'in uçuşunu hayal ediyor — rüzgâr, Boğaz,
martılar yanında!
- S13: Hezarfen hikâyesi — "Buradan Üsküdar'a UÇTU!"
- S14: Hayal sahnesi — çocuk uçuyor! ✓ BÜYÜ ZİRVESİ
- S15: Boğaz üzerinde süzülme — rüzgâr, martılar
- S16: "Hayal eden başarır!" — farkındalık
**Değer**: Cesaret, inovasyon, hayal gücü

---

### BÖLÜM 5 — GALATA KÖPRÜSÜ: HAYATIN AKIŞI (Sayfa 17-19)
Kuleden inip köprüye yürüyüş. Balıkçılar, altında balık
restoranları, vapurlar geçiyor. Martı: "Bu köprü iki dünyayı
birleştirir — eski ve yeni, Avrupa ve Asya."
- S17: Galata Köprüsü — balıkçılar, vapurlar
- S18: Köprü altı — balık kokusu, canlı hayat
- S19: "İki dünya birleşiyor" — bağlantı ✓ ANLAM ZİRVESİ
**Değer**: Birlik, bağlantı, çeşitlilik

---

### BÖLÜM 6 — İSTİKLAL CADDESİ: KIRMIZI TRAMVAY (Sayfa 20-21)
Nostaljik kırmızı tramvay! Çiçekçiler, kitapçılar, pasajlar.
Martı son ipucunu veriyor: "İstanbul'un sırrı nedir biliyor musun?
Her köşede yeni bir hikâye var."
- S20: Kırmızı tramvay — nostaljik, eğlenceli
- S21: "Her köşede yeni bir hikâye!" ✓ DORUK KEŞİF
**Değer**: Keşif, hikâye, kültür

---

### BÖLÜM 7 — FİNAL: GÜN BATIMI (Sayfa 22)
Gün batımında kulenin önünde. İstanbul altın rengi parlıyor.
Martı: "Sen de bir hikâyesin. Keşfetmeye devam et."
Martı kanat çırparak Boğaz'a doğru uçuyor.
- S22: Gün batımı, İstanbul altın rengi, gurur ✓ TATMİN DORUĞU
**Değer**: Keşif, hikâye, özgüven

---

## DOPAMİN ZİRVELERİ:
1. S4: Bilge Martı canlanıyor
2. S8: Hezarfen "buradan uçtu!"
3. S9: 360° panorama — "VAAAY!"
4. S14: Hayal uçuşu — Boğaz üzerinde
5. S19: İki dünya birleşiyor
6. S21: "Her köşede yeni bir hikâye!"
7. S22: Gün batımı — tatmin

## GÜVENLİK KURALLARI:
- Korku/şiddet YOK
- Yükseklik korkutucu DEĞİL (Martı koruyucu)
- Pozitif, keşif odaklı atmosfer
- Çocuk TEK BAŞINA (aile yok)
"""

# ============================================================================
# CULTURAL ELEMENTS
# ============================================================================

GALATA_CULTURAL_ELEMENTS = {
    "location": "Galata Tower and district, Istanbul, Turkey",
    "historic_site": "Galata Tower (built 1348 by Genoese, 67m)",
    "architecture": [
        "Cylindrical stone tower with conical cap roof",
        "360-degree observation balcony",
        "Spiral staircase (9 floors)",
        "Galata Bridge over Golden Horn",
        "Istiklal Avenue with nostalgic red tram",
    ],
    "legends": "Hezarfen Ahmed Celebi flight (~1630s) from tower to Uskudar",
    "atmosphere": "Magical, panoramic, historic, vibrant, Istanbul spirit",
    "color_palette": "warm stone grey, Bosphorus blue-green, sunset amber-rose, terracotta rooftops",
    "values": ["Curiosity", "Courage", "Imagination", "Connection"],
}

# ============================================================================
# CUSTOM INPUTS (list formati)
# ============================================================================

GALATA_CUSTOM_INPUTS = [
    {
        "key": "favorite_view",
        "label": "En Merak Ettiği Manzara",
        "type": "select",
        "options": ["Boğaz Panoraması", "Haliç ve Köprü", "Tarihi Yarımada", "Gün Batımı"],
        "default": "Boğaz Panoraması",
        "required": False,
        "help_text": "Hikayenin en büyülü sahnesi bu manzarada geçecek",
    },
    {
        "key": "special_discovery",
        "label": "Keşfetmek İstediği Şey",
        "type": "select",
        "options": ["Hezarfen'in Uçuş Sırrı", "Kulenin Gizli Odası", "İstanbul'un Kayıp Haritası", "Martının 700 Yıllık Hikâyesi"],
        "default": "Hezarfen'in Uçuş Sırrı",
        "required": False,
        "help_text": "Hikayede çocuğun keşfedeceği büyük sır",
    },
]

# ============================================================================
# DATABASE UPDATE FUNCTION
# ============================================================================


async def create_galata_scenario():
    """Galata senaryosunu oluşturur veya günceller."""

    async with async_session_factory() as db:
        result = await db.execute(
            select(Scenario).where(
                (Scenario.theme_key == "galata")
                | (Scenario.name.ilike("%Galata%"))
            )
        )
        scenario = result.scalar_one_or_none()

        if not scenario:
            scenario = Scenario(id=uuid.uuid4())
            db.add(scenario)

        scenario.name = "Galata Kulesi Macerası"
        scenario.description = (
            "İstanbul'un sembolü Galata Kulesi'ne tırmanma macerası. "
            "Boğaz'ın iki yakasını, tarihi mahalleleri ve "
            "İstanbul'un eşsiz güzelliğini keşfet!"
        )
        scenario.theme_key = "galata"
        scenario.cover_prompt_template = GALATA_COVER_PROMPT
        scenario.page_prompt_template = GALATA_PAGE_PROMPT
        scenario.story_prompt_tr = GALATA_STORY_PROMPT_TR
        scenario.outfit_girl = OUTFIT_GIRL
        scenario.outfit_boy = OUTFIT_BOY
        scenario.cultural_elements = GALATA_CULTURAL_ELEMENTS
        scenario.custom_inputs_schema = GALATA_CUSTOM_INPUTS
        scenario.marketing_badge = "YENİ! İstanbul Keşfi"
        scenario.age_range = "6-10"
        scenario.tagline = "İstanbul'un tepesinden keşif!"
        scenario.is_active = True
        scenario.display_order = 8

        await db.commit()
        print(f"Galata scenario updated: {scenario.id}")


if __name__ == "__main__":
    asyncio.run(create_galata_scenario())
