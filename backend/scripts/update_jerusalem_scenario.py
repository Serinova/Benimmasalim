"""
Kudüs Eski Şehir Macerası — Birleştirilmiş Güncelleme
======================================================
create_kudus_scenario.py ve eski update_jerusalem_scenario.py birleştirildi.
- Modular prompt (500 char limit, tüm placeholder'lar mevcut)
- Hikaye: Kültürel keşif macerası (3 dine eşit saygı)
- Outfit: update_all_outfits.py standardı (EXACTLY lock phrase)
- custom_inputs_schema: list formatı (frontend uyumlu)
- theme_key: kudus (tek senaryo)
- Yüz benzerliği: CHARACTER block önce
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import select, or_

from app.core.database import async_session_factory
from app.models.scenario import Scenario

# ============================================================================
# MODULAR PROMPT COMPONENTS (500 char limit!)
# ============================================================================

KUDUS_COVER_PROMPT = (
    "An {child_age}-year-old {child_gender} named {child_name} "
    "with {hair_description}, wearing {clothing_description}. "
    "{scene_description}. "
    "Ancient Jerusalem Old City walls, golden Dome of the Rock in distance. "
    "Narrow cobblestone streets, arched doorways, golden Jerusalem stone. "
    "Wide shot: child 25%, historic architecture 75%. "
    "Peaceful, multi-cultural atmosphere. UNESCO site."
)

KUDUS_PAGE_PROMPT = (
    "An {child_age}-year-old {child_gender} named {child_name} "
    "with {hair_description}, wearing {clothing_description}. "
    "{scene_description}. "
    "Elements: [Walls: Ottoman golden limestone / Dome of Rock: golden dome, blue tiles / "
    "Souq: spices, copper lanterns, crafts / Alleys: narrow cobblestone, arched / "
    "Four Quarters: diverse architecture / Jerusalem stone: warm golden glow]. "
    "Golden light, peaceful, historic atmosphere."
)

# ============================================================================
# OUTFIT DEFINITIONS (update_all_outfits.py standardı)
# ============================================================================

OUTFIT_GIRL = (
    "soft ivory white cotton long-sleeve modest dress reaching ankles, "
    "white cotton hijab headscarf covering hair completely with neat edges, "
    "comfortable light beige flat sandals, small white cotton drawstring bag. "
    "EXACTLY the same outfit on every page — same ivory dress, same white hijab, same beige sandals."
)

OUTFIT_BOY = (
    "clean white cotton knee-length kurta tunic shirt, "
    "white knit taqiyah prayer cap on head, light beige loose-fitting cotton pants, "
    "comfortable tan leather sandals, small white cotton drawstring bag. "
    "EXACTLY the same outfit on every page — same white kurta, same white taqiyah, same beige pants."
)

# ============================================================================
# STORY BLUEPRINT (Kültürel Keşif Macerası)
# ============================================================================

KUDUS_STORY_PROMPT_TR = """
# KUDÜS ESKİ ŞEHİR MACERASI — KÜLTÜREL KEŞİF

## TEMEL YAPI: 7 BÖLÜM, 22 SAYFA

Bu hikaye bir kültürel keşif macerası. {child_name}, Kudüs Eski Şehir'de
bir Bilge Kedi (surların labirent sokaklarını ezbere bilen antik kedi) ile
birlikte 5000 yıllık tarihi, kültürel çeşitliliği ve hoşgörüyü keşfeder.

⚠️ ÖNEMLİ KURALLAR:
- Bu bir MACERA hikayesi, gezi rehberi DEĞİL
- Her bölümde çocuk AKTİF katılımcı
- Endişe → Eylem → Başarı döngüsü
- Yardımcı karakter: Bilge Kedi (surların antik kedisi)
- Çocuk TEK BAŞINA macerada (aile yok)
- Korku/şiddet/gore YOK
- Dini ritüel/ibadet sahnesi YOK — yapılar "mimari şaheser" olarak
- 3 dine EŞİT saygı, siyasi mesaj YOK
- Peygamber görseli YOK (sadece hikaye anlatımı)
- Odak: MİMARİ, ARKEOLOJİ, ÇARŞI KÜLTÜRÜ, HOŞGÖRÜ

---

### BÖLÜM 1 — GİRİŞ: SURLARIN ARDINDA (Sayfa 1-4)
{child_name} Şam Kapısı'ndan Eski Şehir'e giriyor. Dev taş surlar,
dar sokaklar, altın rengi taşlar. Bilge Kedi kapının kenarında bekliyor.
"Bu surların arkasında 5000 yıllık sırlar var. Gel, göstereyim!"
- S1: Şam Kapısı'na varış, dev kemerli giriş
- S2: Surların içine adım atma — dar taş sokaklar
- S3: Bilge Kedi ile tanışma — "5000 yıllık sırlar!"
- S4: Altın rengi Kudüs taşı güneşte parlıyor ✓ İLK HAYRANLIK
**Değer**: Merak, keşif cesareti

---

### BÖLÜM 2 — ALTIN KUBBE: MİMARİ ŞAHESER (Sayfa 5-8)
Bilge Kedi çocuğu yüksek bir noktaya götürüyor. Altın Kubbe
(Kubbetüs-Sahra) güneşte parlıyor! Sekizgen yapı, mavi çini
süslemeleri. "Bu kubbe 1300 yıldır burada parlıyor!"
- S5: Yüksek noktaya tırmanma, manzara
- S6: Altın Kubbe'nin parıltısı — "İnanılmaz!" ✓ MİMARİ ZİRVESİ
- S7: Sekizgen yapı, mavi çiniler — mimari detaylar
- S8: Mescid-i Aksa avlusu, geniş taş alan
**Değer**: Mimari güzellik, tarih bilinci

---

### BÖLÜM 3 — ÇARŞI: BAHARAT VE ZANAAT (Sayfa 9-12)
Kapalı çarşıya giriş! Baharat dağları (zerdeçal, kırmızı biber, zahter),
bakır fenerler, zeytin ağacı oymalar, seramik karolar. Bilge Kedi
bir baharat tüccarının tezgahının altından geçiyor. Çocuk mozaik
ustasından küçük taşları birleştirmeyi öğreniyor.
- S9: Çarşıya giriş — renk ve koku cümbüşü
- S10: Baharat dağları — "Zerdeçal altın gibi!"
- S11: Mozaik ustasının atölyesi — sabırla taş birleştirme ✓ ZANAAT ZİRVESİ
- S12: Kendi mozaiğini yapma — başarı! ✓ BAŞARI HİSSİ
**Değer**: Sabır, el sanatı, kültürel zenginlik

---

### BÖLÜM 4 — DÖRT MAHALLE: FARKLILIKLAR ZENGİNLİK (Sayfa 13-16)
Bilge Kedi çocuğu dört mahalleye götürüyor. Her mahallede farklı
mimari, farklı kokular, farklı sesler. Ama hepsi aynı surların
içinde, aynı taş sokaklarda. "Farklılıklar zenginliktir!"
- S13: İlk mahalle — kendine özgü mimari ve atmosfer
- S14: İkinci mahalle — farklı ama güzel
- S15: Üçüncü mahalle — "Her biri ayrı dünya!" ✓ KÜLTÜREL ZİRVE
- S16: Dördüncü mahalle — "Hepsi bir arada yaşıyor!"
**Değer**: Hoşgörü, farklılıklara saygı, birlikte yaşama

---

### BÖLÜM 5 — YERALTI: ARKEOLOJİK KATMANLAR (Sayfa 17-19)
Bilge Kedi gizli bir geçitten yeraltına iniyor. Arkeolojik katmanlar —
Roma sütunları, Bizans mozaikleri, Osmanlı kemerleri. Her katman
farklı uygarlık! "Bu şehir katman katman tarih."
- S17: Yeraltı geçidine giriş — karanlık, Bilge Kedi yol gösteriyor
- S18: Arkeolojik katmanlar — "Roma, Bizans, Osmanlı!" ✓ TARİH ZİRVESİ
- S19: Antik su tüneli — "Binlerce yıllık mühendislik!"
**Değer**: Tarih bilinci, uygarlık mirası

---

### BÖLÜM 6 — SURLAR: PANORAMA (Sayfa 20-21)
Surların üstüne çıkma. Tüm Eski Şehir ayakların altında — altın
kubbeler, taş çatılar, minareler, çan kuleleri. Gün batımında
her şey altın rengi. Bilge Kedi: "Bu şehir insanlığın ortak hazinesi."
- S20: Surların üstünde yürüme — panoramik manzara
- S21: Gün batımı — tüm şehir altın rengi ✓ PANORAMA DORUĞU
**Değer**: Kültürel miras, insanlığın ortak değeri

---

### BÖLÜM 7 — FİNAL: HOŞGÖRÜNÜN ŞEHRİ (Sayfa 22)
Şam Kapısı'na dönüş. Bilge Kedi: "Bu şehir sana ne öğretti?"
Çocuk: "Farklılıklar zenginliktir. Birlikte yaşamak güzeldir."
Bilge Kedi gülümsüyor ve surların arasında kayboluyor.
- S22: Dönüş, hoşgörü mesajı, gurur ✓ TATMIN DORUĞU
**Değer**: Hoşgörü, barış, kültürel zenginlik

---

## DOPAMIN ZİRVELERİ:
1. S4: Kudüs taşının altın parıltısı
2. S6: Altın Kubbe — mimari şaheser
3. S12: Mozaik yapma — el sanatı başarısı
4. S15: Dört mahalle — kültürel çeşitlilik
5. S18: Arkeolojik katmanlar — uygarlık tarihi
6. S21: Surlardan panorama — gün batımı
7. S22: Hoşgörü mesajı — tatmin

## GÜVENLİK KURALLARI:
- Korku/şiddet/gore YOK
- Dini ritüel/ibadet sahnesi YOK
- Peygamber görseli YOK
- Siyasi mesaj/taraf tutma YOK
- 3 dine eşit saygı
- Yapılar "mimari şaheser ve tarihî anıt" olarak
"""

# ============================================================================
# CULTURAL ELEMENTS
# ============================================================================

KUDUS_CULTURAL_ELEMENTS = {
    "location": "Old City of Jerusalem, UNESCO World Heritage Site",
    "historic_significance": "5000+ years of continuous habitation",
    "architecture": [
        "Ottoman city walls (Suleiman the Magnificent, 16th century)",
        "Golden Dome of the Rock (iconic golden dome, blue tiles)",
        "Narrow cobblestone alleys with arched passageways",
        "Jerusalem stone (meleke limestone) — golden glow in sunlight",
        "Four distinct quarters with unique architecture",
    ],
    "cultural_elements": [
        "Covered souq bazaars (spices, crafts, lanterns)",
        "Artisan workshops (mosaic, olive wood, ceramics, copper)",
        "Archaeological layers (Roman, Byzantine, Crusader, Ottoman)",
        "Ancient water systems and underground tunnels",
    ],
    "atmosphere": "Ancient, multicultural, warm golden light, peaceful",
    "color_palette": "Jerusalem gold stone, Mediterranean blue, spice colors, olive green",
    "values": ["Tolerance", "Peace", "Cultural diversity", "Respect"],
}

# ============================================================================
# CUSTOM INPUTS (list formatı — frontend uyumlu)
# ============================================================================

KUDUS_CUSTOM_INPUTS = [
    {
        "key": "favorite_quarter",
        "label": "En Merak Ettiği Yer",
        "type": "select",
        "options": ["Çarşı ve Baharat Sokağı", "Zanaatkâr Atölyeleri", "Surlar ve Kapılar", "Arkeoloji Alanları"],
        "default": "Çarşı ve Baharat Sokağı",
        "required": False,
        "help_text": "Hikayenin en renkli sahnesinin geçeceği yer",
    },
    {
        "key": "special_discovery",
        "label": "Keşfetmek İstediği Şey",
        "type": "select",
        "options": ["Kayıp Mozaik Haritası", "Sihirli Baharat Tarifi", "Gizli Yeraltı Tüneli", "Antik Zanaatkâr Sırrı"],
        "default": "Kayıp Mozaik Haritası",
        "required": False,
        "help_text": "Hikayede çocuğun peşine düşeceği büyük gizem",
    },
]

# ============================================================================
# DATABASE UPDATE FUNCTION
# ============================================================================


async def update_jerusalem_scenario():
    """Kudüs senaryosunu günceller. Çift senaryo varsa birini siler."""

    async with async_session_factory() as db:
        result = await db.execute(
            select(Scenario).where(
                or_(
                    Scenario.theme_key == "kudus",
                    Scenario.theme_key == "jerusalem_old_city",
                    Scenario.name.ilike("%Kudüs%"),
                    Scenario.name.ilike("%Kudus%"),
                    Scenario.name.ilike("%Jerusalem%"),
                )
            )
        )
        scenarios = result.scalars().all()

        if len(scenarios) > 1:
            # Birden fazla Kudüs senaryosu var — birini koru, diğerlerini sil
            keep = scenarios[0]
            for s in scenarios[1:]:
                await db.delete(s)
                print(f"Deleted duplicate Kudüs scenario: {s.name} ({s.id})")
            scenario = keep
        elif len(scenarios) == 1:
            scenario = scenarios[0]
        else:
            print("Kudüs scenario not found — skipping")
            return

        scenario.name = "Kudüs Eski Şehir Macerası"
        scenario.description = (
            "UNESCO Dünya Mirası surlarla çevrili antik şehirde büyülü bir macera! "
            "5.000 yıllık taş sokaklarda zaman yolculuğu, sihirli baharat çarşısı "
            "ve altın rengi Kudüs taşının ışığında kültürlerin mozaiğini keşfet!"
        )
        scenario.theme_key = "kudus"
        scenario.cover_prompt_template = KUDUS_COVER_PROMPT
        scenario.page_prompt_template = KUDUS_PAGE_PROMPT
        scenario.story_prompt_tr = KUDUS_STORY_PROMPT_TR
        scenario.outfit_girl = OUTFIT_GIRL
        scenario.outfit_boy = OUTFIT_BOY
        scenario.cultural_elements = KUDUS_CULTURAL_ELEMENTS
        scenario.custom_inputs_schema = KUDUS_CUSTOM_INPUTS
        scenario.marketing_badge = "Kültürel Keşif"
        scenario.age_range = "7-10"
        scenario.tagline = "5000 yıllık kültürlerin mozaiği"
        scenario.is_active = True
        scenario.display_order = 9

        await db.commit()
        print(f"Kudüs scenario updated: {scenario.id}")


if __name__ == "__main__":
    asyncio.run(update_jerusalem_scenario())
