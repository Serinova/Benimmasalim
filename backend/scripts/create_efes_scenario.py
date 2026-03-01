"""
Efes Antik Kent Macerasi — Duzeltilmis
=======================================
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

EFES_COVER_PROMPT = (
    "An {child_age}-year-old {child_gender} named {child_name} "
    "with {hair_description}, wearing {clothing_description}. "
    "{scene_description}. "
    "Library of Celsus grand two-story marble facade with Corinthian columns in background. "
    "Marble-paved Curetes Street, scattered ancient columns. "
    "Golden Mediterranean sunlight on white marble. "
    "Wide shot: child 25%, ancient ruins 75%. "
    "Archaeological wonder atmosphere."
)

EFES_PAGE_PROMPT = (
    "An {child_age}-year-old {child_gender} named {child_name} "
    "with {hair_description}, wearing {clothing_description}. "
    "{scene_description}. "
    "Elements: [Celsus Library: two-story marble facade, 4 wisdom statues / "
    "Great Theatre: 25000-seat amphitheatre / Curetes Street: marble-paved, mosaics / "
    "Terrace Houses: floor mosaics, frescoes / Hadrian Temple: ornate arch]. "
    "Warm marble white, golden honey, Mediterranean blue."
)

# ============================================================================
# OUTFIT DEFINITIONS (update_all_outfits.py standardi)
# ============================================================================

OUTFIT_GIRL = (
    "soft lavender purple cotton t-shirt with small sun emblem, "
    "light blue denim shorts reaching knees, white canvas sneakers, "
    "wide-brim white sun hat with lavender ribbon, small white crossbody bag. "
    "EXACTLY the same outfit on every page — same lavender shirt, same blue shorts, same white hat."
)

OUTFIT_BOY = (
    "sky blue cotton t-shirt with small Greek column emblem, "
    "sand-colored cotton chino shorts, white canvas sneakers with blue stripes, "
    "white baseball cap, small beige canvas backpack on back. "
    "EXACTLY the same outfit on every page — same blue shirt, same sand shorts, same white cap."
)

# ============================================================================
# STORY BLUEPRINT
# ============================================================================

EFES_STORY_PROMPT_TR = """
# EFES ANTİK KENT MACERASI — BİLGELİĞİN İZİNDE

## TEMEL YAPI: 7 BÖLÜM, 22 SAYFA

Bu hikaye bir antik kent macerası. {child_name}, Efes'te bir Konuşan
Baykuş (Celsus Kütüphanesi'ndeki Bilgelik heykeli Sophia'dan canlanan,
3000 yıllık bilge rehber) ile birlikte antik kentin sırlarını keşfeder.

⚠️ ÖNEMLİ KURALLAR:
- Bu bir MACERA hikayesi, gezi rehberi DEĞİL
- Her bölümde çocuk AKTİF katılımcı
- Endişe → Eylem → Başarı döngüsü
- Yardımcı karakter: Konuşan Baykuş (Sophia'dan canlanan bilge)
- Çocuk TEK BAŞINA macerada (aile yok). Anne-baba-aile karakteri KULLANMA.
- Korku/şiddet YOK
- Dini ritüel YOK — Artemis Tapınağı "mimari harika" olarak

---

### BÖLÜM 1 — GİRİŞ: MERMER SOKAKLAR (Sayfa 1-4)
{child_name} Efes'in mermer sokaklarında yürüyor. Devasa sütunlar,
mozaik kaldırımlar. Celsus Kütüphanesi'nin önünde bir baykuş heykeli
parlıyor — Konuşan Baykuş canlanıyor! "3000 yıldır buradayım.
Sana bilgeliğin sırrını göstereyim!"
- S1: Efes'e varış — mermer sokaklar, sütunlar
- S2: Curetes Caddesi — mozaikler, kabartmalar
- S3: Celsus Kütüphanesi — Baykuş canlanıyor!
- S4: "Bilgeliğin sırrı!" — macera başlıyor ✓ İLK HEYECAN
**Değer**: Merak, bilgi arayışı

---

### BÖLÜM 2 — CELSUS KÜTÜPHANESİ: 12.000 KİTAP (Sayfa 5-8)
Kütüphanenin içine giriş. 4 bilgelik heykeli (Sophia, Arete, Ennoia,
Episteme). Baykuş: "Her heykel bir erdem temsil eder. Bilgelik,
erdem, düşünce, bilgi." Çocuk bir bulmaca çözüyor.
- S5: Kütüphane içi — "12.000 kitap buradaydı!"
- S6: 4 bilgelik heykeli — her biri bir erdem
- S7: Bulmaca — heykellerin sırrı ✓ MERAK ZİRVESİ
- S8: İlk ipucu bulundu — sonraki durak!
**Değer**: Bilgi, erdem, merak

---

### BÖLÜM 3 — BÜYÜK TİYATRO: 25.000 KİŞİ (Sayfa 9-12)
25.000 kişilik dev amfitiyatro. Baykuş: "Burada sesini duyurabilirsin."
Çocuk sahneye çıkıyor, fısıltısı en üst sıradan duyuluyor!
Akustik mucize.
- S9: Büyük Tiyatro — "Devasa!" ✓ HAYRANLIK
- S10: Sahneye çıkma — "25.000 kişi burada oturuyordu!"
- S11: Akustik deney — fısıltı en üstten duyuluyor!
- S12: "Sesini duyurmanın gücü!" ✓ BAŞARI ZİRVESİ
**Değer**: Cesaret, kendini ifade etme

---

### BÖLÜM 4 — TERAS EVLER: GİZLİ SANAT (Sayfa 13-16)
Zengin Romalıların evleri. Zemin mozaikleri, duvar freskleri,
yerden ısıtma sistemi! Baykuş: "Güzellik detaylarda gizlidir."
Çocuk bir mozaik deseni tamamlıyor.
- S13: Teras evler — mozaik zeminler
- S14: Freskler — renkli duvar resimleri
- S15: Mozaik tamamlama — sabır ve özen ✓ SANAT ZİRVESİ
- S16: Yerden ısıtma — "2000 yıl önce bile!"
**Değer**: Sanat, sabır, detay

---

### BÖLÜM 5 — ARTEMİS TAPINAĞI: 7 HARİKA (Sayfa 17-19)
Dünyanın 7 Harikası'ndan biri! Tek ayakta kalan sütun. Baykuş:
"Bir zamanlar 127 sütun vardı. Hayal gücünle gör." Çocuk gözlerini
kapatıyor, tapınak canlanıyor!
- S17: Tek sütun — "7 Harikadan biri!"
- S18: Hayal gücü — tapınak canlanıyor! ✓ BÜYÜ ZİRVESİ
- S19: "Hayal gücü en güçlü araç!"
**Değer**: Hayal gücü, tarih bilinci

---

### BÖLÜM 6 — HADRİAN TAPINAĞI: SON İPUCU (Sayfa 20-21)
Zarif kemerli tapınak. Tyche kabartması. Baykuş son ipucunu
veriyor: "Bilgeliğin sırrı bir yerde gizli değil — SENde gizli."
Çocuk anlıyor: Merak eden, soran, öğrenen herkes bilgedir.
- S20: Hadrian Tapınağı — zarif kemer, kabartmalar
- S21: "Bilgelik SENde!" ✓ DORUK KEŞİF
**Değer**: Özgüven, öğrenme sevgisi

---

### BÖLÜM 7 — FİNAL: GÜN BATIMI (Sayfa 22)
Gün batımında Celsus Kütüphanesi'nin önünde. Mermer altın rengi
parlıyor. Baykuş: "Merak etmeye devam et." Baykuş heykeline
geri dönüyor, ama gülümsüyor.
- S22: Gün batımı, bilgelik mesajı, gurur ✓ TATMİN DORUĞU
**Değer**: Merak, bilgi, keşif

---

## DOPAMİN ZİRVELERİ:
1. S4: Konuşan Baykuş canlanıyor
2. S7: Kütüphane bulmacası
3. S11: Akustik mucize — fısıltı duyuluyor
4. S15: Mozaik tamamlama
5. S18: Artemis Tapınağı canlanıyor
6. S21: "Bilgelik SENde!"
7. S22: Gün batımı — tatmin

## GÜVENLİK KURALLARI:
- Korku/şiddet YOK
- Dini ritüel YOK
- Pozitif, eğitici atmosfer
- Çocuk TEK BAŞINA (aile yok)
"""

# ============================================================================
# CULTURAL ELEMENTS
# ============================================================================

EFES_CULTURAL_ELEMENTS = {
    "location": "Ephesus, Aegean coast, Turkey",
    "historic_site": "Ephesus Ancient City, UNESCO World Heritage",
    "architecture": [
        "Library of Celsus (two-story marble facade, 4 wisdom statues)",
        "Great Theatre (25,000-seat amphitheatre)",
        "Curetes Street (marble-paved, mosaics)",
        "Terrace Houses (floor mosaics, frescoes)",
        "Temple of Artemis (one of Seven Wonders)",
        "Hadrian's Temple (ornate arch)",
    ],
    "atmosphere": "Archaeological wonder, Mediterranean warmth, ancient grandeur",
    "color_palette": "warm marble white, golden honey, Mediterranean blue, olive green, terracotta",
    "values": ["Knowledge", "Curiosity", "Art appreciation", "History"],
}

# ============================================================================
# CUSTOM INPUTS (list formati)
# ============================================================================

EFES_CUSTOM_INPUTS = [
    {
        "key": "favorite_place",
        "label": "En Merak Ettiği Yer",
        "type": "select",
        "options": ["Celsus Kütüphanesi", "Büyük Tiyatro", "Teras Evler", "Artemis Tapınağı"],
        "default": "Celsus Kütüphanesi",
        "required": False,
        "help_text": "Hikayenin en büyülü sahnesi bu mekânda geçecek",
    },
    {
        "key": "special_discovery",
        "label": "Keşfetmek İstediği Şey",
        "type": "select",
        "options": ["Bilgeliğin Sırrı", "Gizli Mozaik Odası", "Kayıp Kitap", "Antik Harita"],
        "default": "Bilgeliğin Sırrı",
        "required": False,
        "help_text": "Hikayede çocuğun keşfedeceği büyük sır",
    },
]

# ============================================================================
# DATABASE UPDATE FUNCTION
# ============================================================================


async def create_efes_scenario():
    """Efes senaryosunu oluşturur veya günceller."""

    async with async_session_factory() as db:
        result = await db.execute(
            select(Scenario).where(
                (Scenario.theme_key == "ephesus")
                | (Scenario.name.ilike("%Efes%"))
                | (Scenario.name.ilike("%Ephesus%"))
            )
        )
        scenario = result.scalar_one_or_none()

        if not scenario:
            scenario = Scenario(id=uuid.uuid4())
            db.add(scenario)

        scenario.name = "Efes Antik Kent Macerası"
        scenario.description = (
            "3000 yıllık Roma-Yunan ihtişamına yolculuk! "
            "Celsus Kütüphanesi (12.000 kitap!), 25.000 kişilik Büyük Tiyatro, "
            "mermer sokaklar ve mozaiklerle Efes Antik Kenti'ni keşfet."
        )
        scenario.theme_key = "ephesus"
        scenario.cover_prompt_template = EFES_COVER_PROMPT
        scenario.page_prompt_template = EFES_PAGE_PROMPT
        scenario.story_prompt_tr = EFES_STORY_PROMPT_TR
        scenario.outfit_girl = OUTFIT_GIRL
        scenario.outfit_boy = OUTFIT_BOY
        scenario.cultural_elements = EFES_CULTURAL_ELEMENTS
        scenario.custom_inputs_schema = EFES_CUSTOM_INPUTS
        scenario.marketing_badge = "YENİ! Antik Kent Macerası"
        scenario.age_range = "7-10"
        scenario.tagline = "Bilgeliğin izinde antik keşif!"
        scenario.is_active = True
        scenario.display_order = 4

        await db.commit()
        print(f"Efes scenario updated: {scenario.id}")


if __name__ == "__main__":
    asyncio.run(create_efes_scenario())
