"""
Güneş Sistemi Macerası — Düzeltilmiş Güncelleme
================================================
- Modular prompt (500 char limit, tüm placeholder'lar mevcut)
- Hikaye: 8 gezegen dopamin merdiveni
- Outfit: update_all_outfits.py standardı (EXACTLY lock phrase)
- custom_inputs_schema: list formatı (frontend uyumlu)
- Yüz benzerliği: CHARACTER block önce
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import select

from app.models import Scenario

# ============================================================================
# MODULAR PROMPT COMPONENTS (500 char limit!)
# ============================================================================

SPACE_COVER_PROMPT = (
    "An {child_age}-year-old {child_gender} named {child_name} "
    "with {hair_description}, wearing {clothing_description}. "
    "{scene_description}. "
    "Modular space station orbiting Earth, friendly AI robot companion beside child. "
    "8 planets visible in background: Jupiter MASSIVE, Saturn rings, Mars red. "
    "Child TINY in vast cosmos, starfield, nebula hints. "
    "Epic space adventure atmosphere."
)

SPACE_PAGE_PROMPT = (
    "An {child_age}-year-old {child_gender} named {child_name} "
    "with {hair_description}, wearing {clothing_description}. "
    "{scene_description}. "
    "Elements: [Mercury: cratered / Venus: thick clouds / Mars: red, rovers / "
    "Jupiter: MASSIVE, Great Red Spot / Saturn: ice rings / Uranus: tilted ice giant / "
    "Neptune: distant blue]. AI robot companion. "
    "Deep space black, stars. Child TINY, cosmos VAST."
)

# ============================================================================
# OUTFIT DEFINITIONS (update_all_outfits.py standardı)
# ============================================================================

OUTFIT_GIRL = (
    "bright white NASA-style child space suit with pink and blue mission patches on shoulders, "
    "silver metallic utility belt with small gadget pouches, white space boots with pink soles, "
    "clear bubble space helmet with pink frame (helmet can be removed in indoor scenes), "
    "small silver star-shaped badge on chest. "
    "EXACTLY the same outfit on every page — same white space suit with pink patches, same silver belt, same white boots."
)

OUTFIT_BOY = (
    "bright white NASA-style child space suit with blue and orange mission patches on shoulders, "
    "silver metallic utility belt with small gadget pouches, white space boots with blue soles, "
    "clear bubble space helmet with blue frame (helmet can be removed in indoor scenes), "
    "small gold rocket-shaped badge on chest. "
    "EXACTLY the same outfit on every page — same white space suit with blue patches, same silver belt, same white boots."
)

# ============================================================================
# STORY BLUEPRINT (8 Gezegen Dopamin Merdiveni)
# ============================================================================

SPACE_STORY_PROMPT_TR = """
# GÜNEŞ SİSTEMİ MACERASI — 8 GEZEGEN KEŞFİ

## TEMEL YAPI: 7 BÖLÜM, 22 SAYFA

Bu uzay macerası, {child_name}'in AI robot arkadaşı NOVA ile Merkür'den
Neptün'e 8 gezegen keşfettiği epik bir yolculuk.

⚠️ ÖNEMLİ KURALLAR:
- Bu bir MACERA hikayesi, bilim dersi DEĞİL
- Her gezegende endişe → eylem → başarı döngüsü
- AI robot NOVA: rehber, koruyucu, arkadaş
- Çocuk TEK BAŞINA macerada (aile yok)
- Korku/şiddet YOK, bilimsel ve heyecanlı
- Her gezegende çocuk AKTİF katılımcı

---

### BÖLÜM 1 — GİRİŞ: UZAY İSTASYONU (Sayfa 1-4)
{child_name} modüler uzay istasyonunda uyanır. AI robot NOVA yanında:
"Bugün 8 gezegeni keşfedeceğiz!" Dünya mavi mermer gibi aşağıda.
İlk kalkış heyecanı!
- S1: Uzay istasyonunda uyanma, pencereden Dünya
- S2: NOVA ile tanışma — "Merhaba kaptan!"
- S3: Kontrol paneli, rota haritası — 8 gezegen
- S4: Kalkış! "3, 2, 1... Uzaya!" ✓ İLK HEYECAN
**Değer**: Cesaret, merak

---

### BÖLÜM 2 — İÇ GEZEGENLER: MERKÜR VE VENÜS (Sayfa 5-8)
Merkür'e yaklaşma — kraterler, 430°C sıcaklık! "Çok sıcak!" NOVA
koruyucu kalkanı açıyor. Venüs'te kalın bulutlar, asit yağmuru.
"Dünya ne kadar şanslıymış!"
- S5: Merkür'e yaklaşma, dev kraterler
- S6: "430 derece! Eritir bizi!" — NOVA kalkan açıyor ✓ ENDİŞE→BAŞARI
- S7: Venüs bulutları, asit yağmuru — "Tehlikeli!"
- S8: Güvenle geçiş, "Dünya şanslıymış!" ✓ SICAKLIK ZİRVESİ
**Değer**: Bilimsel gözlem, karşılaştırma

---

### BÖLÜM 3 — AY VE MARS: YAŞAM İZİ (Sayfa 9-12)
Ay'a iniş — Armstrong'un ayak izi! Mars'ta kırmızı çöl, Curiosity rover.
NOVA sensörleriyle tarama yapıyor... "Yaşam izi buldum!"
- S9: Ay'a iniş, gri kraterler, "Armstrong buradaydı!"
- S10: Mars kırmızı çölü, dev kanyon
- S11: "Yaşam var mıydı?" — NOVA tarama yapıyor ✓ MERAK
- S12: Mikroskobik fosil izi! "YAŞAM İZİ!" ✓ KEŞİF DORUĞU
**Değer**: Bilimsel yöntem, sabır

---

### BÖLÜM 4 — JÜPİTER: DEVASA ÖLÇEK (Sayfa 13-16)
Jüpiter'e yaklaşma — DEVASA! 1300 Dünya sığar! Kırmızı Leke fırtınası
300 yıldır devam ediyor. "Çok büyük, fırtına bizi yutacak!" NOVA
güvenli yörünge hesaplıyor.
- S13: Jüpiter'e yaklaşma — "NE BÜYÜK!"
- S14: Kırmızı Leke fırtınası — "Bizi yutacak!" ✓ ENDİŞE
- S15: NOVA güvenli yörünge — yakın geçiş başarılı!
- S16: "1300 Dünya sığar!" — çocuk TINY, Jüpiter MASSIVE ✓ ÖLÇEK ZİRVESİ
**Değer**: Ölçek kavramı, güven

---

### BÖLÜM 5 — SATÜRN VE URANÜS: KOZMİK GÜZELLİK (Sayfa 17-19)
Satürn'ün halkaları — buzdan yapılmış, inanılmaz güzel! Uranüs yan
yatmış dönüyor — evrende tek! Çocuk halkaların arasından geçiyor.
- S17: Satürn halkaları — "Buzdan köprü!"
- S18: Halkaların arasından geçiş — heyecan! ✓ GÜZELLİK ZİRVESİ
- S19: Uranüs yan dönüyor — "Evrende tek!"
**Değer**: Doğa güzelliği, benzersizlik

---

### BÖLÜM 6 — NEPTÜN: EN UZAK NOKTA (Sayfa 20-21)
Neptün — en uzak gezegen, mavi dev. "Çok uzak, dönebilir miyiz?"
NOVA: "Tabii ki! Rota hesaplandı." Güneş Sistemi'nin sınırı.
- S20: Neptün mavi devi — en uzak nokta
- S21: "Dönebilir miyiz?" — NOVA güven veriyor ✓ ENDİŞE→BAŞARI
**Değer**: Cesaret, güven

---

### BÖLÜM 7 — FİNAL: DÜNYA'YA DÖNÜŞ (Sayfa 22)
8 gezegen tamamlandı! Dünya'ya dönüş. Pencereden mavi mermer —
"Evimiz ne güzel!" NOVA: "Sen artık bir gezegen kaşifisin!"
- S22: Dünya'ya dönüş, gurur, "Evimiz ne güzel!" ✓ TATMIN DORUĞU
**Değer**: Dünya bilinci, başarı gururu

---

## DOPAMIN ZİRVELERİ:
1. S4: İlk uzay kalkışı
2. S8: Merkür/Venüs — sıcaklık tehlikesi atlatıldı
3. S12: Mars — yaşam izi keşfi
4. S16: Jüpiter — devasa ölçek
5. S18: Satürn — halkaların arasından geçiş
6. S21: Neptün — en uzak noktadan dönüş
7. S22: Dünya'ya dönüş — başarı

## GÜVENLİK KURALLARI:
- Korku/şiddet YOK
- Tehlikeli anlar NOVA tarafından çözülüyor
- Uzay güvenli, robot rehberliğinde
- Pozitif, bilimsel atmosfer
"""

# ============================================================================
# CULTURAL ELEMENTS
# ============================================================================

SPACE_CULTURAL_ELEMENTS = {
    "location": "Solar System (8 planets + Moon)",
    "theme": "Space exploration and astronomy",
    "planets": [
        "Mercury (cratered, 430°C)",
        "Venus (thick clouds, volcanic)",
        "Earth Moon (Armstrong's footprint)",
        "Mars (red, ancient water, rovers)",
        "Jupiter (MASSIVE, 1300 Earths, Great Red Spot)",
        "Saturn (ice rings, beautiful)",
        "Uranus (tilted 98°, ice giant)",
        "Neptune (farthest, blue, fastest winds)",
    ],
    "atmosphere": "Epic scale, scientific, adventurous, child TINY in vast cosmos",
    "color_palette": "deep space black, starfield white, planet colors, nebula purple",
    "educational_focus": [
        "Planetary science and astronomy",
        "Scale comparison (child vs planets)",
        "Space exploration history",
        "Scientific method and observation",
    ],
    "values": ["Science", "Courage", "Curiosity", "Exploration"],
}

# ============================================================================
# CUSTOM INPUTS (list formatı — frontend uyumlu)
# ============================================================================

SPACE_CUSTOM_INPUTS = [
    {
        "key": "robot_name",
        "label": "Robot Arkadaşının İsmi",
        "type": "select",
        "options": ["NOVA", "STELLA", "COSMO", "ORBIT", "LUNA"],
        "default": "NOVA",
        "required": False,
        "help_text": "Uzay yolculuğunda rehber robot arkadaşın adı",
    },
    {
        "key": "favorite_planet",
        "label": "En Sevdiği Gezegen",
        "type": "select",
        "options": ["Jüpiter (En Büyük!)", "Satürn (Halkaları!)", "Mars (Kırmızı!)", "Neptün (En Uzak!)", "Dünya (Evimiz!)"],
        "default": "Jüpiter (En Büyük!)",
        "required": False,
        "help_text": "Hikayede bu gezegen özel olarak vurgulanacak",
    },
]

# ============================================================================
# DATABASE UPDATE FUNCTION
# ============================================================================


async def update_space_scenario():
    """Güneş Sistemi senaryosunu günceller."""
    from app.core.database import async_session_factory

    async with async_session_factory() as session:
        result = await session.execute(
            select(Scenario).where(
                (Scenario.theme_key == "solar_system")
                | (Scenario.theme_key == "solar_systems_space")
                | (Scenario.name.ilike("%Güneş Sistemi%"))
                | (Scenario.name.ilike("%Uzay%"))
            )
        )
        scenario = result.scalar_one_or_none()

        if not scenario:
            print("Güneş Sistemi scenario not found — skipping")
            return

        scenario.name = "Güneş Sistemi Macerası: Gezegen Kaşifleri"
        scenario.description = (
            "8 gezegen macerası! Modüler uzay istasyonundan başlayarak "
            "Merkür'den Neptün'e kadar tüm gezegenleri keşfet. AI robot "
            "arkadaşınla birlikte Jüpiter'in ihtişamını, Satürn'ün "
            "halkalarını ve Mars'taki yaşam izlerini öğren!"
        )
        scenario.cover_prompt_template = SPACE_COVER_PROMPT
        scenario.page_prompt_template = SPACE_PAGE_PROMPT
        scenario.story_prompt_tr = SPACE_STORY_PROMPT_TR
        scenario.outfit_girl = OUTFIT_GIRL
        scenario.outfit_boy = OUTFIT_BOY
        scenario.cultural_elements = SPACE_CULTURAL_ELEMENTS
        scenario.custom_inputs_schema = SPACE_CUSTOM_INPUTS
        scenario.marketing_badge = "YENİ! Uzay Macerası"
        scenario.age_range = "7-10"
        scenario.tagline = "8 gezegen, sonsuz keşif!"
        scenario.is_active = True

        await session.commit()
        print(f"Güneş Sistemi scenario updated: {scenario.id}")


if __name__ == "__main__":
    asyncio.run(update_space_scenario())
