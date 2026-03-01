"""
Okyanus Derinlikleri: Mavi Dev ile Macera — Düzeltilmiş
========================================================
- Modular prompt (500 char limit, tüm placeholder'lar mevcut)
- Outfit: update_all_outfits.py standardı (EXACTLY lock phrase)
- custom_inputs_schema: list formatı (frontend uyumlu)
- Yüz benzerliği: CHARACTER block önce
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import or_, select

from app.core.database import async_session_factory
from app.models.scenario import Scenario

# ============================================================================
# MODULAR PROMPT COMPONENTS (500 char limit!)
# ============================================================================

OCEAN_COVER_PROMPT = (
    "An {child_age}-year-old {child_gender} named {child_name} "
    "with {hair_description}, wearing {clothing_description}. "
    "{scene_description}. "
    "MASSIVE blue whale in background (30m, child TINY). "
    "Dolphin companion beside child. Bioluminescent jellyfish glowing. "
    "Vibrant coral reefs. Deep ocean gradient turquoise to indigo. "
    "Sunlight rays from above. Peaceful, wondrous."
)

OCEAN_PAGE_PROMPT = (
    "An {child_age}-year-old {child_gender} named {child_name} "
    "with {hair_description}, wearing {clothing_description}. "
    "{scene_description}. "
    "Zones: [Epipelagic 0-200m: coral, tropical fish, turquoise, sun / "
    "Mesopelagic 200-1000m: blue-purple, glowing jellyfish / "
    "Bathypelagic 1000-4000m: dark, anglerfish, bioluminescence / "
    "Whale: MASSIVE 30m, child TINY / Abyss 4000m+: hydrothermal vents]. "
    "Match zone to depth."
)

# ============================================================================
# OUTFIT DEFINITIONS (update_all_outfits.py standardı)
# ============================================================================

OUTFIT_GIRL = (
    "teal and coral pink neoprene diving wetsuit with white trim stripes along arms, "
    "clear full-face diving mask with coral pink frame pushed up on forehead, "
    "compact metallic silver oxygen tank on back, bright yellow diving fins, "
    "waterproof wrist computer on left arm showing depth gauge display. "
    "EXACTLY the same outfit on every page — same teal-pink wetsuit, same coral mask, same yellow fins."
)

OUTFIT_BOY = (
    "navy blue and bright orange neoprene diving wetsuit with reflective white stripes, "
    "clear full-face diving mask with blue frame pushed up on forehead, "
    "compact metallic silver oxygen tank on back, bright orange diving fins, "
    "waterproof yellow flashlight clipped to belt on right hip. "
    "EXACTLY the same outfit on every page — same navy-orange wetsuit, same blue mask, same orange fins."
)

# ============================================================================
# STORY BLUEPRINT (Derinlik Derinlik Keşif)
# ============================================================================

OCEAN_STORY_PROMPT_TR = """
# OKYANUS DERİNLİKLERİ — MAVİ DEV İLE MACERA

## TEMEL YAPI: 7 BÖLÜM, 22 SAYFA

Bu hikaye bir okyanus keşif macerası. {child_name}, yunus arkadaşı ile
mercan bahçelerinden başlayıp okyanus dibine kadar iniyor ve 30 metrelik
dev mavi balina ile karşılaşıyor.

⚠️ ÖNEMLİ KURALLAR:
- Bu bir MACERA hikayesi
- Her bölümde endişe → eylem → başarı döngüsü
- Yardımcı karakter: Yunus arkadaş (rehber, oyuncu, güvenilir)
- Çocuk TEK BAŞINA macerada (aile yok)
- Korku/şiddet YOK — köpekbalığı saldırısı, boğulma, panik YOK
- Bilimsel ve heyecanlı

---

### BÖLÜM 1 — GİRİŞ: YUNUSLA TANIŞMA (Sayfa 1-4)
{child_name} araştırma gemisinde. Denize bakıyor, bir yunus su yüzeyinden
atlıyor! Göz göze geliyorlar. Yunus davet ediyor — "Gel, sana bir dünya
göstereyim!" İlk dalış, sığ suda mercan bahçeleri.
- S1: Araştırma gemisi, denize bakış
- S2: Yunus atlama gösterisi — ilk bağ!
- S3: İlk dalış — sığ su, güneş ışınları
- S4: Mercan bahçeleri — renk cümbüşü! ✓ İLK HAYRANLIK
**Değer**: Merak, doğa sevgisi

---

### BÖLÜM 2 — MERCAN BAHÇELERİ: IŞIKLI BÖLGE (Sayfa 5-8)
Epipelagic zone (0-200m). Renkli mercanlar, palyaço balıkları, deniz
kaplumbağası ile yüzme, ahtapot kılık değiştiriyor! Yunus rehberlik
yapıyor, oyun oynuyorlar.
- S5: Mercan tüneli — göz kamaştırıcı renkler
- S6: Palyaço balığı ve deniz kaplumbağası
- S7: Ahtapot kılık değiştiriyor — "Sihir gibi!"
- S8: Yunus ile yarış — eğlence! ✓ OYUN ZİRVESİ
**Değer**: Keşif, doğa hayranlığı

---

### BÖLÜM 3 — DERİNLEŞME: KARANLIĞA DOĞRU (Sayfa 9-12)
Mesopelagic (200-1000m). Işık azalıyor, mavi-mor tonlar. İlk fosforlu
canlılar! Bathypelagic (1000-4000m). Karanlık, garip canlılar. Dev
kalamar gölgesi! Yunus sığ sulara dönüyor — "Aşağıda bir arkadaşım var."
- S9: Işık azalıyor — "Karanlığa gidiyoruz..." ✓ ENDİŞE
- S10: İlk fosforlu denizanası — "Büyü gibi!"
- S11: Dev kalamar gölgesi — "Tehlikeli mi?!" → Yunus: "Güvendesin"
- S12: Yunus veda — "Yalnız kalacağım..." Uzaktan şarkı duyuluyor ✓ GERİLİM ZİRVESİ
**Değer**: Cesaret, güven

---

### BÖLÜM 4 — MAVİ BALİNA: EPİK KARŞILAŞMA (Sayfa 13-16)
Karanlıktan DEVASA bir gölge çıkıyor — 30 metrelik mavi balina!
"Gözü kafamdan büyük!" Ama şarkı söylüyor, nazik. Yavaşça yaklaşma,
dokunma, kalp atışları. Balina kabul ediyor — sırtına binme!
- S13: Mavi balina ilk görünüş — DEVASA! ✓ ŞOK
- S14: "Korkmalı mıyım?" → Şarkı söylüyor, nazik
- S15: Dokunma anı — kalp atışları, göz göze ✓ BAĞLANMA
- S16: Sırtında "uçuş" — en büyük canlıyla arkadaş! ✓ DORUK ZİRVE
**Değer**: Sabır, naziklik → güven kazanma

---

### BÖLÜM 5 — ABYSS: OKYANUS DİBİ (Sayfa 17-19)
Abyssopelagic (4000-6000m). Tam karanlık. Hidrotermal bacalar — sualtı
volkanları! Fosforlu "galaksi" — binlerce parlayan canlı yıldız gibi.
Balina gizli hazineyi gösteriyor.
- S17: Okyanus dibi — hidrotermal bacalar!
- S18: Fosforlu galaksi — "Yıldızlar gibi!" ✓ BÜYÜ ZİRVESİ
- S19: Gizli hazine keşfi — kristal mağara
**Değer**: Bilimsel merak, keşif

---

### BÖLÜM 6 — YÜZEYE DÖNÜŞ (Sayfa 20-21)
Balina çocuğu nazikçe yüzeye taşıyor. Yunus karşılıyor! Vedalaşma
töreni — yunus, balina, kaplumbağa, deniz canlıları bir arada.
- S20: Yükseliş, balina vedası
- S21: Yunus geri döndü! Vedalaşma töreni ✓ VEDA DORUĞU
**Değer**: Dostluk, vefa

---

### BÖLÜM 7 — FİNAL: GÜN BATIMI (Sayfa 22)
Yüzeye çıkış. Gün batımı, deniz altın rengi. "Okyanusun en büyük
sırrını öğrendim: Devler bile nazik olabilir." Çocuk okyanusları
koruyacağına söz veriyor.
- S22: Gün batımı, söz, gurur ✓ TATMIN DORUĞU
**Değer**: Doğa koruma, sorumluluk

---

## DOPAMIN ZİRVELERİ:
1. S4: Mercan bahçeleri — renk cümbüşü
2. S8: Yunus ile yarış
3. S10: Fosforlu denizanası — büyü
4. S13: Mavi balina — DEVASA şok
5. S16: Balina sırtında uçuş — doruk
6. S18: Fosforlu galaksi
7. S22: Gün batımı — tatmin

## GÜVENLİK KURALLARI:
- Köpekbalığı saldırısı YOK
- Boğulma/oksijen bitmesi YOK
- Dev kalamar saldırısı YOK
- Kaybolma/panik YOK
- Pozitif, bilimsel atmosfer
"""

# ============================================================================
# CULTURAL ELEMENTS
# ============================================================================

OCEAN_CULTURAL_ELEMENTS = {
    "location": "Pacific Ocean (5 depth zones)",
    "theme": "Ocean exploration and marine biology",
    "ocean_zones": [
        "Epipelagic (0-200m): coral, dolphins, turtles",
        "Mesopelagic (200-1000m): bioluminescent creatures",
        "Bathypelagic (1000-4000m): giant squid, anglerfish",
        "Abyssopelagic (4000-6000m): hydrothermal vents",
    ],
    "atmosphere": "Wondrous, peaceful, mysterious, vast, scientific",
    "color_palette": "turquoise, sapphire blue, dark indigo, bioluminescent glow, coral rainbow",
    "values": ["Curiosity", "Nature conservation", "Courage", "Friendship"],
}

# ============================================================================
# CUSTOM INPUTS (list formatı — frontend uyumlu)
# ============================================================================

OCEAN_CUSTOM_INPUTS = [
    {
        "key": "favorite_creature",
        "label": "En Sevdiği Deniz Canlısı",
        "type": "select",
        "options": ["Mavi Balina", "Yunus", "Deniz Kaplumbağası", "Ahtapot"],
        "default": "Mavi Balina",
        "required": False,
        "help_text": "Hikayede en çok vakit geçirilecek deniz canlısı",
    },
    {
        "key": "dolphin_name",
        "label": "Yunus Arkadaşın Adı",
        "type": "select",
        "options": ["Luna", "Dodo", "Flip", "Echo"],
        "default": "Luna",
        "required": False,
        "help_text": "Rehber yunus arkadaşının adı",
    },
    {
        "key": "exploration_goal",
        "label": "Keşif Amacı",
        "type": "select",
        "options": ["Mavi Balinayı Görme", "En Derin Noktaya İnme", "Kayıp Hazineyi Bulma", "Fosforlu Canlıları Keşfetme"],
        "default": "Mavi Balinayı Görme",
        "required": False,
        "help_text": "Macera sırasında tamamlanacak ana görev",
    },
]

# ============================================================================
# DATABASE UPDATE FUNCTION
# ============================================================================


async def update_ocean_adventure_scenario():
    """Okyanus Derinlikleri senaryosunu günceller."""

    async with async_session_factory() as db:
        result = await db.execute(
            select(Scenario).where(
                or_(
                    Scenario.theme_key == "ocean_depths",
                    Scenario.name.ilike("%Okyanus%"),
                    Scenario.name.ilike("%Ocean%"),
                )
            )
        )
        scenario = result.scalar_one_or_none()

        if not scenario:
            scenario = Scenario(name="Okyanus Derinlikleri: Mavi Dev ile Macera", is_active=True)
            db.add(scenario)

        scenario.description = (
            "Okyanusun derinliklerine dal! Yunus arkadaşınla mercan bahçelerinden başla, "
            "fosforlu canlılarla tanış, 30 metrelik dev mavi balinaya bin. "
            "5 farklı derinlik seviyesinde unutulmaz keşif!"
        )
        scenario.theme_key = "ocean_depths"
        scenario.cover_prompt_template = OCEAN_COVER_PROMPT
        scenario.page_prompt_template = OCEAN_PAGE_PROMPT
        scenario.story_prompt_tr = OCEAN_STORY_PROMPT_TR
        scenario.outfit_girl = OUTFIT_GIRL
        scenario.outfit_boy = OUTFIT_BOY
        scenario.cultural_elements = OCEAN_CULTURAL_ELEMENTS
        scenario.custom_inputs_schema = OCEAN_CUSTOM_INPUTS
        scenario.marketing_badge = "Okyanus Keşfi"
        scenario.age_range = "5-10"
        scenario.tagline = "Mavi balinadan okyanus dibine!"
        scenario.is_active = True
        scenario.display_order = 16

        await db.commit()
        print(f"Okyanus scenario updated: {scenario.id}")


if __name__ == "__main__":
    asyncio.run(update_ocean_adventure_scenario())
