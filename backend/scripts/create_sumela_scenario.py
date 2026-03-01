"""
Sümela Manastırı Macerası — Düzeltilmiş
========================================
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

SUMELA_COVER_PROMPT = (
    "An {child_age}-year-old {child_gender} named {child_name} "
    "with {hair_description}, wearing {clothing_description}. "
    "{scene_description}. "
    "Sumela Monastery carved into cliff face at 1200m altitude in background. "
    "Dense emerald Black Sea forest, misty valley, waterfall beside cliff. "
    "Wide shot: child 25%, cliff monastery and forest 75%. "
    "Mystical, enchanted mountain atmosphere."
)

SUMELA_PAGE_PROMPT = (
    "An {child_age}-year-old {child_gender} named {child_name} "
    "with {hair_description}, wearing {clothing_description}. "
    "{scene_description}. "
    "Elements: [Monastery: multi-story stone on cliff, arched windows, balconies / "
    "Frescoes: Byzantine blue-gold-red ochre paintings / "
    "Sacred spring: clear water from rock / Forest: spruce, beech, ferns, mist / "
    "Waterfalls: cascading beside cliff / Stone stairs: mossy ancient path]. "
    "Emerald green, misty grey, warm stone."
)

# ============================================================================
# OUTFIT DEFINITIONS (update_all_outfits.py standardı)
# ============================================================================

OUTFIT_GIRL = (
    "dark emerald green waterproof rain jacket with hood, "
    "over cream white long-sleeve thermal shirt, dark navy blue hiking leggings, "
    "dark brown waterproof hiking boots with green laces, small olive green backpack. "
    "EXACTLY the same outfit on every page — same green jacket, same navy leggings, same brown boots."
)

OUTFIT_BOY = (
    "dark teal blue waterproof rain jacket with hood, "
    "over light gray long-sleeve thermal shirt, dark charcoal hiking pants, "
    "dark brown waterproof hiking boots with teal laces, small dark gray backpack. "
    "EXACTLY the same outfit on every page — same teal jacket, same charcoal pants, same brown boots."
)

# ============================================================================
# STORY BLUEPRINT
# ============================================================================

SUMELA_STORY_PROMPT_TR = """
# SÜMELA MANASTIRI MACERASI — SİSLİ DAĞIN SIRRI

## TEMEL YAPI: 7 BÖLÜM, 22 SAYFA

Bu hikaye bir dağ ve doğa macerası. {child_name}, Altındere Vadisi'nde
bir Gizemli Geyik (sis içinden beliren, manastırın eski koruyucusu) ile
birlikte 1200 metre yükseklikteki kayaya oyulmuş manastırı keşfeder.

⚠️ ÖNEMLİ KURALLAR:
- Bu bir MACERA hikayesi, gezi rehberi DEĞİL
- Her bölümde çocuk AKTİF katılımcı
- Endişe → Eylem → Başarı döngüsü
- Yardımcı karakter: Gizemli Geyik (sis içinden beliren koruyucu)
- Çocuk TEK BAŞINA macerada (aile yok)
- Korku/şiddet YOK
- Dini ritüel/ibadet YOK — manastır "kayaya oyulmuş antik yapı" olarak
- Freskler SANAT ESERİ olarak

---

### BÖLÜM 1 — GİRİŞ: SİSLİ ORMAN (Sayfa 1-4)
{child_name} Altındere Vadisi'nde yürüyor. Yoğun yeşil orman, sis,
dere sesleri. Sis içinden bir geyik beliriyor — Gizemli Geyik!
Geyik yukarıyı gösteriyor: kayalıklarda bir yapı! "Oraya tırmanmamız
lazım. Seni götüreyim."
- S1: Altındere Vadisi — yoğun yeşil orman, sis
- S2: Dere kenarında yürüyüş, kuş sesleri
- S3: Sis içinden Gizemli Geyik beliriyor!
- S4: Kayalıklarda bir yapı — "O ne?!" ✓ İLK HEYECAN
**Değer**: Merak, doğa

---

### BÖLÜM 2 — TIRMANMA: TAŞ MERDİVENLER (Sayfa 5-8)
Yüzlerce basamaklık antik taş merdiven. Yosunlu duvarlar, ahşap
köprüler, dere geçitleri. Yoruluyor, vazgeçmek istiyor. Geyik:
"Her dönemeçte yeni bir manzara var. Devam et!"
- S5: Taş merdivenlere başlama — "Çok uzun!"
- S6: Yosunlu duvarlar, ahşap köprü
- S7: Yorgunluk — "Vazgeçsem mi?" ✓ ENDİŞE
- S8: Dönemeçte şelale manzarası — "Devam!" ✓ AZİM ZİRVESİ
**Değer**: Azim, vazgeçmeme

---

### BÖLÜM 3 — MANASTIR: KAYAYA OYULMUŞ DÜNYA (Sayfa 9-12)
Manastıra varış! Dik kayalığa yapışmış çok katlı taş yapı. Taş
balkondan vadiye bakış — sis denizi, orman okyanusu! İç mekâna
giriş, karanlık koridorlar.
- S9: Manastıra varış — "Kayaya yapışmış!" ✓ HAYRANLIK
- S10: Taş balkon — vadiye bakış, sis denizi
- S11: İç mekân — karanlık koridorlar, Geyik yol gösteriyor
- S12: Çok katlı yapı keşfi — merdivenler, odalar ✓ MİMARİ ZİRVESİ
**Değer**: Keşif, mimari hayranlık

---

### BÖLÜM 4 — FRESKLER: 1000 YILLIK SANAT (Sayfa 13-16)
Fresk odası! Duvarlarda ve tavanda 1000 yıllık resimler — derin
mavi, altın, kırmızı toprak tonları. Geyik: "Bu resimleri yapanlar
da senin gibi meraklıydı." Çocuk doğal boyalarla kendi resmini yapıyor.
- S13: Fresk odası — "1000 yıllık resimler!"
- S14: Mavi-altın tonlar — detaylar, yüz ifadeleri
- S15: Çocuk kendi resmini yapıyor — doğal boyalar ✓ SANAT ZİRVESİ
- S16: "Sanat zamanı yener!" — farkındalık
**Değer**: Sanat, yaratıcılık, kültürel miras

---

### BÖLÜM 5 — KUTSAL KAYNAK: DOĞANIN BÜYÜSÜ (Sayfa 17-19)
Kayadan çıkan berrak su kaynağı. Soğuk, temiz su. Geyik: "Bu su
binlerce yıldır akıyor. Doğa en sabırlı sanatçı." Çocuk suya
dokunuyor, ferahlık hissediyor.
- S17: Kutsal kaynak — kayadan akan berrak su
- S18: Suya dokunma — ferahlık, huzur ✓ HUZUR ZİRVESİ
- S19: "Doğa en sabırlı sanatçı" — farkındalık
**Değer**: Doğa saygısı, sabır

---

### BÖLÜM 6 — GİZLİ ODA: MANASTIRIN SIRRI (Sayfa 20-21)
Geyik çocuğu gizli bir geçitten bilinmeyen bir odaya götürüyor.
İçeride en güzel freskler — hiç görülmemiş! Manastırın en derin
sırrı, en korunaklı hazinesi.
- S20: Gizli geçit — heyecan!
- S21: Bilinmeyen oda — en güzel freskler! ✓ DORUK KEŞİF
**Değer**: Azim, sabır → ödül

---

### BÖLÜM 7 — FİNAL: SİS DENİZİ (Sayfa 22)
Gün batımında taş balkonda. Vadi sis denizi gibi, orman üstünde
altın ışık. Geyik: "Bu dağ sana ne öğretti?" Çocuk: "Tırmanmaya
değer." Geyik sis içinde kayboluyor, ama gülümsüyor.
- S22: Gün batımı, sis denizi, gurur ✓ TATMIN DORUĞU
**Değer**: Azim, doğa bilinci, kültürel miras

---

## DOPAMIN ZİRVELERİ:
1. S4: Gizemli Geyik + kayalıktaki yapı
2. S8: Şelale manzarası — azim ödülü
3. S10: Taş balkon — sis denizi
4. S15: Fresk yapma — sanat
5. S18: Kutsal kaynak — huzur
6. S21: Gizli oda — doruk keşif
7. S22: Gün batımı — tatmin

## GÜVENLİK KURALLARI:
- Korku/şiddet YOK
- Dini ritüel/ibadet YOK
- Yükseklik sahnesi korkutucu DEĞİL (Geyik koruyucu)
- Pozitif, doğa odaklı atmosfer
"""

# ============================================================================
# CULTURAL ELEMENTS
# ============================================================================

SUMELA_CULTURAL_ELEMENTS = {
    "location": "Altindere Valley, Trabzon, Turkey (Black Sea coast)",
    "historic_site": "Sumela Monastery (founded ~386 AD), 1200m altitude",
    "architecture": [
        "Multi-story stone building carved into cliff face",
        "Byzantine frescoes (deep blue, gold, red ochre)",
        "Rock-cut chapel with vaulted ceilings",
        "Sacred spring from rock",
        "Ancient stone stairway through forest",
    ],
    "atmosphere": "Mystical, hidden, enchanted, forest-shrouded, serene",
    "color_palette": "emerald green, misty grey, warm stone, Byzantine gold and blue",
    "values": ["Perseverance", "Nature appreciation", "Art", "Cultural heritage"],
}

# ============================================================================
# CUSTOM INPUTS (list formatı — frontend uyumlu)
# ============================================================================

SUMELA_CUSTOM_INPUTS = [
    {
        "key": "favorite_place",
        "label": "En Sevdiği Gizemli Mekân",
        "type": "select",
        "options": ["Fresk Odası", "Kutsal Kaynak", "Taş Balkon", "Şelale Yanı"],
        "default": "Fresk Odası",
        "required": False,
        "help_text": "Hikayenin en büyülü sahnesi bu mekânda geçecek",
    },
    {
        "key": "special_discovery",
        "label": "Keşfetmek İstediği Şey",
        "type": "select",
        "options": ["Gizli Fresk Odası", "Sihirli Kaynak Suyu", "Gizemli Yeraltı Geçidi", "Kayıp Hazine"],
        "default": "Gizli Fresk Odası",
        "required": False,
        "help_text": "Hikayede çocuğun keşfedeceği büyük sır",
    },
]

# ============================================================================
# DATABASE UPDATE FUNCTION
# ============================================================================


async def create_sumela_scenario():
    """Sümela senaryosunu oluşturur veya günceller."""

    async with async_session_factory() as db:
        result = await db.execute(
            select(Scenario).where(
                (Scenario.theme_key == "sumela")
                | (Scenario.name.ilike("%Sümela%"))
                | (Scenario.name.ilike("%Sumela%"))
            )
        )
        scenario = result.scalar_one_or_none()

        if not scenario:
            scenario = Scenario(id=uuid.uuid4())
            db.add(scenario)

        scenario.name = "Sümela Manastırı Macerası"
        scenario.description = (
            "Trabzon'un büyülü Sümela Manastırı'na dağ macerası! "
            "1200m yükseklikte kayaya oyulmuş tarihi manastırı keşfet, "
            "şelaleler ve yeşil ormanlarla dolu Altındere Vadisi'nde "
            "doğa ve tarihi birlikte öğren!"
        )
        scenario.theme_key = "sumela"
        scenario.cover_prompt_template = SUMELA_COVER_PROMPT
        scenario.page_prompt_template = SUMELA_PAGE_PROMPT
        scenario.story_prompt_tr = SUMELA_STORY_PROMPT_TR
        scenario.outfit_girl = OUTFIT_GIRL
        scenario.outfit_boy = OUTFIT_BOY
        scenario.cultural_elements = SUMELA_CULTURAL_ELEMENTS
        scenario.custom_inputs_schema = SUMELA_CUSTOM_INPUTS
        scenario.marketing_badge = "YENİ! Dağ Macerası"
        scenario.age_range = "7-10"
        scenario.tagline = "Sisli dağın sırrını keşfet!"
        scenario.is_active = True
        scenario.display_order = 6

        await db.commit()
        print(f"Sümela scenario updated: {scenario.id}")


if __name__ == "__main__":
    asyncio.run(create_sumela_scenario())
