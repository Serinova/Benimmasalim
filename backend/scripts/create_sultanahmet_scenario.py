"""
Sultanahmet Camii Macerası — Düzeltilmiş
==========================================
- Modular prompt (500 char limit, tüm placeholder'lar mevcut)
- Outfit: update_all_outfits.py standardı (EXACTLY lock phrase)
- custom_inputs_schema: list formatı
- Yüz benzerliği: CHARACTER block önce
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

SULTANAHMET_COVER_PROMPT = (
    "An {child_age}-year-old {child_gender} named {child_name} "
    "with {hair_description}, wearing {clothing_description}. "
    "{scene_description}. "
    "Blue Mosque (Sultanahmet) dome cascade and six minarets in background. "
    "Courtyard with ablution fountain, pigeons in flight. "
    "Warm golden light on cream stone. Istanbul skyline, Bosphorus hint. "
    "Wide shot: child 25%, mosque 75%. Majestic atmosphere."
)

SULTANAHMET_PAGE_PROMPT = (
    "An {child_age}-year-old {child_gender} named {child_name} "
    "with {hair_description}, wearing {clothing_description}. "
    "{scene_description}. "
    "Elements: [Interior: 20000+ blue Iznik tiles, tulip-carnation patterns, "
    "massive dome, 200+ stained glass windows, red carpet, elephant-foot pillars / "
    "Courtyard: hexagonal fountain, domed portico / "
    "Square: Egyptian Obelisk, Serpent Column / Arasta Bazaar: ceramics, lamps]. "
    "Iznik cobalt blue, golden amber tones."
)

# ============================================================================
# OUTFIT DEFINITIONS (update_all_outfits.py standardı)
# ============================================================================

OUTFIT_GIRL = (
    "soft white cotton long-sleeve modest dress reaching ankles with delicate blue floral embroidery on hem, "
    "white cotton hijab headscarf covering hair neatly, comfortable cream flat shoes, "
    "small white shoulder bag with blue strap. "
    "EXACTLY the same outfit on every page — same white dress with blue embroidery, same white hijab."
)

OUTFIT_BOY = (
    "clean white cotton long-sleeve shirt, light beige cotton loose-fitting pants, "
    "white knit taqiyah prayer cap on head, comfortable tan leather sandals, "
    "small beige canvas shoulder bag. "
    "EXACTLY the same outfit on every page — same white shirt, same beige pants, same white taqiyah cap."
)

# ============================================================================
# STORY BLUEPRINT
# ============================================================================

SULTANAHMET_STORY_PROMPT_TR = """
# SULTANAHMET CAMİİ MACERASI — MAVİ ÇİNİLERİN SIRRI

## TEMEL YAPI: 7 BÖLÜM, 22 SAYFA

Bu hikaye bir sanat ve mimari macerası. {child_name}, Sultanahmet'te
bir Konuşan Çini (İznik çinisindeki lale deseninden canlanan 400 yıllık
varlık) ile birlikte Osmanlı sanatının sırlarını keşfeder.

⚠️ ÖNEMLİ KURALLAR:
- Bu bir MACERA hikayesi, gezi rehberi DEĞİL
- Her bölümde çocuk AKTİF katılımcı
- Endişe → Eylem → Başarı döngüsü
- Yardımcı karakter: Konuşan Çini (lale deseninden canlanan)
- Çocuk TEK BAŞINA macerada (aile yok)
- Korku/şiddet YOK
- Dini ritüel/ibadet sahnesi YOK — cami "mimari şaheser" olarak
- İznik çinileri SANAT ve ZANAAT perspektifinden

---

### BÖLÜM 1 — GİRİŞ: MAVİ CAMİ'NİN AVLUSU (Sayfa 1-4)
{child_name} Sultanahmet Meydanı'nda. Dev kubbe kaskadı ve 6 minare!
Avluya giriyor, şadırvanın yanında bir çini parçası parlıyor.
Lale deseni canlanıyor — Konuşan Çini! "400 yıldır buradayım,
sana bir sır göstereyim!"
- S1: Sultanahmet Meydanı, kubbe kaskadı, 6 minare
- S2: Avluya giriş, şadırvan, güvercinler
- S3: Çini parçası parlıyor — Konuşan Çini canlanıyor!
- S4: "400 yıllık bir sır!" — macera başlıyor ✓ İLK HEYECAN
**Değer**: Merak, sanat

---

### BÖLÜM 2 — MAVİ ÇİNİLER: 20.000 SANAT ESERİ (Sayfa 5-8)
İç mekâna giriş. 20.000+ mavi İznik çinisi! Lale, karanfil, servi
desenleri. Vitray pencerelerden renkli ışık huzmeleri. Konuşan Çini:
"Her bir çini bir ustanın elinden çıktı. Ama bir çini kayıp..."
- S5: İç mekân — 20.000 mavi çini! "İnanılmaz!"
- S6: Lale ve karanfil desenleri — "Her biri farklı!"
- S7: Vitray pencereler — renkli ışık huzmeleri ✓ IŞIK ZİRVESİ
- S8: "Bir çini kayıp!" — gizem başlıyor ✓ MERAK
**Değer**: Sanat, detay, özen

---

### BÖLÜM 3 — KUBBE ALTI: SONSUZLUK HİSSİ (Sayfa 9-12)
Kubbenin altında durma — 43 metre yükseklik! Çiçekli arabesk
süslemeler, fil ayağı sütunları. Konuşan Çini bir ipucu veriyor:
"Kayıp çini kubbenin sırrını biliyor."
- S9: Kubbenin altı — "Ne kadar yüksek!" ✓ HAYRANLIK
- S10: Fil ayağı sütunları — devasa boyut
- S11: Arabesk süslemeler — "Sonsuz gibi!"
- S12: İpucu bulundu — kayıp çininin izi ✓ KEŞİF HEYECANI
**Değer**: Mimari, ölçek kavramı

---

### BÖLÜM 4 — İZNİK ÇİNİ ATÖLYESİ: USTANIN SANATI (Sayfa 13-16)
Konuşan Çini çocuğu gizli bir atölyeye götürüyor. Usta çinici
kobalt mavisi boyayla lale deseni çiziyor. Çocuk deniyor — acele
edince desen bozuluyor! "Sabır, sabır..." Tekrar deniyor, bu sefer
güzel oluyor!
- S13: Gizli atölye — çini yapım süreci
- S14: Usta çinici — kobalt mavisi, lale motifi
- S15: Çocuk deniyor — acele, desen bozuluyor! ✓ ZORLUK
- S16: Sabırla tekrar — güzel bir lale! ✓ BAŞARI ZİRVESİ
**Değer**: Sabır, özen, el sanatı

---

### BÖLÜM 5 — HİPODROM: 3500 YILLIK TARİH (Sayfa 17-19)
Meydana çıkış. Dikilitaş (3500 yaşında Mısır obeliski!), Yılanlı
Sütun (antik Yunan). Konuşan Çini: "Bu meydan binlerce yıl boyunca
farklı uygarlıklara ev sahipliği yaptı."
- S17: Dikilitaş — "3500 yaşında!" ✓ TARİH ZİRVESİ
- S18: Yılanlı Sütun — antik Yunan
- S19: Ayasofya manzarası — ikili silüet
**Değer**: Tarih bilinci, uygarlık mirası

---

### BÖLÜM 6 — KAYIP ÇİNİ: GİZEMİN ÇÖZÜMÜ (Sayfa 20-21)
Arasta Çarşısı'nda ipucunu takip ediyor. Renkli Türk lambaları,
seramik dükkânları. Sonunda kayıp çiniyi buluyor — ustanın en
güzel eseri, gizli bir niş içinde!
- S20: Arasta Çarşısı — renkli lambalar, seramikler
- S21: Kayıp çini bulundu! "Ustanın şaheseri!" ✓ DORUK KEŞİF
**Değer**: Azim, problem çözme

---

### BÖLÜM 7 — FİNAL: SANATIN GÜCÜ (Sayfa 22)
Gün batımında kubbe kaskadı altın rengi. Konuşan Çini: "Sanat
sabırla, özenle, sevgiyle yapılır. Sen de bir sanatçısın."
Çini gülümseyerek desenine geri dönüyor.
- S22: Gün batımı, sanat mesajı, gurur ✓ TATMIN DORUĞU
**Değer**: Sanat, sabır, yaratıcılık

---

## DOPAMIN ZİRVELERİ:
1. S4: Konuşan Çini canlanıyor
2. S7: Vitray ışık huzmeleri
3. S9: Kubbe altı — sonsuzluk
4. S16: Çini yapma başarısı
5. S17: 3500 yıllık Dikilitaş
6. S21: Kayıp çini bulundu
7. S22: Gün batımı — tatmin

## GÜVENLİK KURALLARI:
- Korku/şiddet YOK
- Dini ritüel/ibadet YOK
- Cami "mimari şaheser" olarak
- Pozitif, sanatsal atmosfer
"""

# ============================================================================
# CULTURAL ELEMENTS
# ============================================================================

SULTANAHMET_CULTURAL_ELEMENTS = {
    "location": "Sultanahmet Square, Istanbul, Turkey",
    "historic_site": "Blue Mosque (1609-1616), UNESCO Historic Peninsula",
    "architecture": [
        "20,000+ blue Iznik tiles (tulip, carnation, cypress patterns)",
        "Dome cascade with 6 minarets",
        "200+ stained glass windows",
        "Elephant-foot pillars (5m diameter)",
    ],
    "atmosphere": "Majestic, serene, artistically rich, historically grand",
    "color_palette": "Iznik cobalt blue, turquoise, warm cream stone, golden amber, stained glass jewel tones",
    "values": ["Art appreciation", "Patience", "Craftsmanship", "History"],
}

# ============================================================================
# CUSTOM INPUTS (list formatı — frontend uyumlu)
# ============================================================================

SULTANAHMET_CUSTOM_INPUTS = [
    {
        "key": "favorite_element",
        "label": "En Sevdiği Sanat Detayı",
        "type": "select",
        "options": ["Mavi İznik Çinileri", "Renkli Vitray Pencereler", "Dev Kubbe", "Lale Desenleri"],
        "default": "Mavi İznik Çinileri",
        "required": False,
        "help_text": "Hikayenin en büyülü sahnesi bu sanat eseri etrafında geçecek",
    },
    {
        "key": "special_discovery",
        "label": "Keşfetmek İstediği Şey",
        "type": "select",
        "options": ["Kayıp Çini Ustasının Sırrı", "Gizli Kubbe Odası", "Sihirli Vitray Renkleri", "Antik Hipodrom Hazinesi"],
        "default": "Kayıp Çini Ustasının Sırrı",
        "required": False,
        "help_text": "Hikayede çocuğun keşfedeceği büyük sır",
    },
]

# ============================================================================
# DATABASE UPDATE FUNCTION
# ============================================================================


async def create_sultanahmet_scenario():
    """Sultanahmet senaryosunu oluşturur veya günceller."""

    async with async_session_factory() as db:
        result = await db.execute(
            select(Scenario).where(
                (Scenario.theme_key == "sultanahmet")
                | (Scenario.name.ilike("%Sultanahmet%"))
            )
        )
        scenario = result.scalar_one_or_none()

        if not scenario:
            scenario = Scenario(id=uuid.uuid4())
            db.add(scenario)

        scenario.name = "Sultanahmet Camii Macerası"
        scenario.description = (
            "Sultanahmet Camii'nin (Mavi Cami) mimari güzelliğini ve "
            "Osmanlı sanatını keşfet. 6 minare, 20.000+ mavi çini ve "
            "tarihi avluyla İslami mimarinin ihtişamını öğren!"
        )
        scenario.theme_key = "sultanahmet"
        scenario.cover_prompt_template = SULTANAHMET_COVER_PROMPT
        scenario.page_prompt_template = SULTANAHMET_PAGE_PROMPT
        scenario.story_prompt_tr = SULTANAHMET_STORY_PROMPT_TR
        scenario.outfit_girl = OUTFIT_GIRL
        scenario.outfit_boy = OUTFIT_BOY
        scenario.cultural_elements = SULTANAHMET_CULTURAL_ELEMENTS
        scenario.custom_inputs_schema = SULTANAHMET_CUSTOM_INPUTS
        scenario.marketing_badge = "YENİ! İslami Mimari"
        scenario.age_range = "6-10"
        scenario.tagline = "20.000 mavi çininin sırrı!"
        scenario.is_active = True
        scenario.display_order = 7

        await db.commit()
        print(f"Sultanahmet scenario updated: {scenario.id}")


if __name__ == "__main__":
    asyncio.run(create_sultanahmet_scenario())
