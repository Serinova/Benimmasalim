"""
YENİ SİSTEM: Güneş Sistemi Macerası Scenario Update
===================================================
ESKİ sistem TAMAMEN SİLİNDİ - SIFIRDAN yazıldı!

Ocean/Dinosaur standardına uygun:
- Modular prompt (500 char limit)
- Story blueprint (8 Gezegen + Dopamin Merdiveni)
- Educational focus (bilimsel, epic scale!)
"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import sessionmaker
from backend.app.models import Scenario
import os

# ============================================================================
# MODULAR PROMPT COMPONENTS (500 char limit!)
# ============================================================================

SPACE_COVER_PROMPT = """Epic space scene: {scene_description}.
Modular space station orbiting Earth.
Friendly AI robot companion beside child.
8 planets visible: Mercury (small), Venus (cloudy), Mars (red), Jupiter (MASSIVE, Great Red Spot), Saturn (rings), Uranus, Neptune (distant blue).
Child TINY in vast cosmos.
Starfield, nebula hints.
Adventure atmosphere."""

SPACE_PAGE_PROMPT = """Space scene: {scene_description}.
AI robot companion (friendly guide).
Planets: [Mercury: cratered, extreme heat / Venus: thick clouds, volcanic / Moon: gray cratered / Mars: red surface, rovers / Jupiter: MASSIVE (1300 Earths), Great Red Spot, child TINY / Saturn: iconic rings (ice) / Uranus: ice giant, tilted / Neptune: distant blue].
Spacecraft, space station.
Deep space black, stars.
Child TINY, cosmos VAST."""

# ============================================================================
# STORY BLUEPRINT (8 Gezegen Dopamin Merdiveni)
# ============================================================================

SPACE_STORY_PROMPT_TR = """
# UZAY KEŞFİ DOPAMİN YÖNETİMİ - GÜNEŞ SİSTEMİ MACERASI

## TEMEL YAPI: 7 BÖLÜM, 22 SAYFA

Bu uzay keşif hikayesi, çocuğa **bilim**, **cesaret**, **keşif** ve **merak** değerlerini öğretir.

🚀 **8 GEZEGEN YOLCULUĞU**: Merkür'den Neptün'e, modüler istasyonla, AI robot {robot_name} rehberliğinde!

---

### BÖLÜM 1 - GİRİŞ: UZAY İSTASYONU VE İLK KALKIŞ (1-4)
- {child_name}, modüler uzay istasyonunda, AI robot {robot_name} ile tanışıyor
- Dünya mavi mermer gibi aşağıda
- Robot: "8 gezegeni keşfedeceğiz!"
- Heyecan: "Uzaya mı çıkacağız?"
- **Değer**: Cesaret, bilim, merak

**EPİK AN #1**: İlk uzay kalkışı, Dünya'dan ayrılış!

**Sayfa içeriği**:
- S1: Uzay istasyonuna varış
- S2: Robot {robot_name} ile tanışma
- S3: Dünya'ya bakış, "Ne güzel!"
- S4: "8 gezegen macerası başlıyor!" ✓ **İLK HEYECAN**

---

### BÖLÜM 2 - İÇ GEZEGENLER: MERKÜR VE VENÜS (5-9)
**[SICAKLIK DÖNGÜSÜ #1]**
- **Merkür**: Güneş'e en yakın! Kraterler, 430°C sıcak!
- **Venüs**: Kalın bulutlar, asitli yağmur, volkanlar
- **Kaygı**: "Çok sıcak ve tehlikeli!"
- **Robot**: Koruyucu kalkan, güvenli mesafe
- **Başarı**: Güvenle gözlem, bilimsel veri!

**EPİK AN #2**: Merkür'ün Güneş'e yakınlığı - ateş gibi!

**Sayfa içeriği**:
- S5: Merkür'e yaklaşma, kraterler
- S6: "430 derece! Çok sıcak!"
- S7: Venüs bulutları, "Asit yağmuru?" ✓ **ENDIŞE→BAŞARI #1**
- S8: Robot koruyucu kalkan, güvenli
- S9: İç gezegen bilgisi, "Dünya şanslıymış!"

---

### BÖLÜM 3 - AY VE MARS: YAŞAM İZİ ARAŞTIRMASI (10-14)
**[KEŞİF DÖNGÜSÜ #2]**
- **Ay**: İlk Adım! Gri kraterler, Armstrong'un izi
- **Mars**: Kırmızı gezegen, Curiosity rover, eski su yatakları
- **Kaygı**: "Mars'ta yaşam var mıydı?"
- **Keşif**: Robot mikroskobik fosil izi buluyor!
- **Başarı**: "Yaşam izleri bulundu!" → KEŞIF DORUĞU!

**EPİK AN #3**: Mars'ta yaşam izi keşfi - bilim zaferi!

**Sayfa içeriği**:
- S10: Ay'a iniş, "Neil Armstrong buradaydı!"
- S11: Mars kırmızı çölü, roverlar
- S12: "Yaşam var mıydı?" araştırma ✓ **ENDIŞE→BAŞARI #2**
- S13: Robot mikroskobik iz buluyor, "YAŞAM İZİ!"
- S14: Mars keşfi tamamlandı, bilimsel zafer

---

### BÖLÜM 4 - DEV GEZEGENLER: JÜPİTER DORUĞU (15-18)
**[DEVASA ÖLÇEK DÖNGÜSÜ #3]**
- **Jüpiter**: DEVASA! 1300 Dünya sığar!
- **Kırmızı Leke**: Dev fırtına, 300 yıldır devam ediyor!
- **Kaygı**: "Çok büyük! Fırtına bizi yutacak!"
- **Robot**: Güvenli yörünge hesabı, "Uzaktan izleyelim"
- **Başarı**: Kırmızı Leke yakın geçiş → HAYRANLIK DORUĞU!

**EPİK AN #4**: Jüpiter'in ihtişamı - çocuk TINY, gezegen MASSIVE! ✓ **ÖLÇEK ZİRVESİ**

**Sayfa içeriği**:
- S15: Jüpiter'e yaklaşma, "NE BÜYÜK!"
- S16: Kırmızı Leke, "Dev fırtına!" ✓ **ENDIŞE→BAŞARI #3**
- S17: "1300 Dünya sığar!" → HAYRANLIK DORUĞU
- S18: Çocuk TINY, Jüpiter MASSIVE - ölçek farkı

---

### BÖLÜM 5 - HALKA VE BUZ DEVLERİ: SATÜRN, URANÜS (19-20)
**[GÜZELLIK DÖNGÜSÜ #4]**
- **Satürn**: İkonik halkalar, buzdan yapılmış!
- **Uranüs**: Buz devi, yan yatmış (tek!)

**EPİK AN #5**: Satürn'ün halkaları - kozmik güzellik!

**Sayfa içeriği**:
- S19: Satürn halkaları, "Buzdan köprü!"
- S20: Uranüs yan dönüyor ✓ **GÜZELLIK ZİRVESİ #4**

---

### BÖLÜM 6 - FİNAL: NEPTÜN VE DÖNÜŞ (21-22)
**[DÖNÜŞ DÖNGÜSÜ - FİNAL]**
- **Neptün**: En uzak gezegen, mavi dev
- **Kaygı**: "Çok uzak, dönebilir miyiz?"
- **Robot**: Rota hesaplama, "Dünya'ya dönüyoruz!"
- **Başarı**: 8 gezegen tamamlandı!
- **Mesaj**: "Evrenin ne kadar büyük ve güzel olduğunu öğrendik!"

**EPİK AN #6**: Dünya'ya dönüş - uzay yolculuğu tamamlandı! ✓ **DÖNÜŞ DORUĞU**

**Sayfa içeriği**:
- S21: Neptün mavi devi, en uzak
- S22: Dünya'ya dönüş, "Evimiz ne güzel!" ✓ **FİNAL DORUĞU**

---

## DOPAMIN ZİRVELERİ:
1. **Sayfa 4**: İlk uzay kalkışı (HEYECAN)
2. **Sayfa 7**: Venüs asit yağmuru → robot korur (ENDİŞE→BAŞARI)
3. **Sayfa 13**: Mars yaşam izi bulma (KEŞIF DORUĞU)
4. **Sayfa 17**: Jüpiter ihtişamı - 1300 Dünya (ÖLÇEK ZİRVESİ)
5. **Sayfa 19**: Satürn halkaları (GÜZELLIK ZİRVESİ)
6. **Sayfa 22**: Dünya'ya dönüş (FİNAL DORUĞU)

---

## DEĞERLER:
- **BİLİM**: Astronomi, gezegen bilgisi, uzay keşfi
- **CESARET**: Uzayda yolculuk, bilinmeze gitme
- **KEŞİF**: 8 gezegen, farklı dünyalar
- **MERAK**: "Neden?" soruları, bilimsel düşünce

---

## ROBOT ARKADAŞLIK:
- AI robot {robot_name}: Rehber, koruyucu, öğretmen
- Her gezegende bilimsel bilgi verir
- Endişe anlarında güven verir
- Çocukla arkadaş, uzay yoldaşı

---

## GÜVENLİK KURALLARI:
- Uzay yolculuğu güvenli, robot rehberliğinde
- Tehlikeli gezegenlere (Venüs, Jüpiter) güvenli mesafe
- Modüler istasyon korunaklı
- Pozitif, bilimsel, güvenli atmosfer

---

## CUSTOM INPUTS:
- {robot_name}: Çocuğun robot arkadaşının ismi (örn: NOVA, STELLA, COSMO)
- {favorite_planet}: Çocuğun favori gezegeni (örn: Jüpiter, Satürn, Mars)
- Favori gezegen sayfa 13-15 arasında vurgulanacak
"""

# ============================================================================
# OUTFIT DEFINITIONS
# ============================================================================

OUTFIT_GIRL = """NASA-style child astronaut suit for space adventure.
White or light blue space suit with mission patches.
Helmet with clear visor (space exploration).
Boots designed for space station walking.
Backpack with life support system (stylized, safe design).
Age-appropriate, inspiring, astronaut look.
Modern, sleek, scientific atmosphere."""

OUTFIT_BOY = """NASA-style child astronaut suit for space adventure.
White or light blue space suit with mission patches.
Helmet with clear visor (space exploration).
Boots designed for space station walking.
Backpack with life support system (stylized, safe design).
Age-appropriate, inspiring, astronaut look.
Modern, sleek, scientific atmosphere."""

# ============================================================================
# CULTURAL ELEMENTS
# ============================================================================

SPACE_CULTURAL_ELEMENTS = {
    "location": "Solar System (8 planets + Moon)",
    "theme": "Space exploration and astronomy",
    "planets": {
        "Mercury": {
            "distance": "57.9 million km from Sun",
            "features": "Heavily cratered, extreme temperatures (430°C day, -180°C night)",
            "size": "Smallest planet (4,879 km diameter)"
        },
        "Venus": {
            "distance": "108.2 million km from Sun",
            "features": "Thick sulfuric acid clouds, volcanic surface, greenhouse effect",
            "temperature": "462°C (hottest planet)"
        },
        "Earth_Moon": {
            "distance": "384,400 km from Earth",
            "features": "First human landing (1969), gray cratered surface",
            "significance": "Neil Armstrong's first step"
        },
        "Mars": {
            "distance": "227.9 million km from Sun",
            "features": "Red planet, ancient water traces, Curiosity rover exploration",
            "significance": "Potential for past microbial life"
        },
        "Jupiter": {
            "distance": "778.5 million km from Sun",
            "features": "MASSIVE (1,300 Earths fit inside!), Great Red Spot storm (300+ years old)",
            "size": "Largest planet (139,820 km diameter)",
            "epic": "Scale contrast - child TINY, Jupiter MASSIVE!"
        },
        "Saturn": {
            "distance": "1.43 billion km from Sun",
            "features": "Iconic rings made of ice and rock, thousands of ringlets",
            "beauty": "Most beautiful planet"
        },
        "Uranus": {
            "distance": "2.87 billion km from Sun",
            "features": "Ice giant, tilted 98° (rolls on its side!), blue-green color",
            "unique": "Only planet that rotates sideways"
        },
        "Neptune": {
            "distance": "4.5 billion km from Sun (farthest!)",
            "features": "Distant blue giant, fastest winds in solar system",
            "significance": "Edge of our planetary system"
        }
    },
    "ai_robot": "Friendly AI companion named {robot_name}, provides guidance and scientific knowledge",
    "space_station": "Modular space station orbiting Earth, safe home base",
    "atmosphere": "Epic scale, scientific, adventurous, child TINY in vast cosmos",
    "educational_focus": [
        "Planetary science and astronomy",
        "Scale comparison (child vs planets)",
        "Orbital mechanics",
        "Space exploration history",
        "Scientific method and observation"
    ],
    "values": ["Science", "Courage", "Curiosity", "Exploration"],
    "unique_features": [
        "8-planet progression (Mercury → Neptune)",
        "AI robot companionship throughout journey",
        "Scale emphasis (child TINY, cosmos VAST)",
        "Scientific accuracy with epic adventure"
    ]
}

# ============================================================================
# CUSTOM INPUTS
# ============================================================================

SPACE_CUSTOM_INPUTS = {
    "robot_name": {
        "type": "text",
        "label_tr": "Robot arkadaşının ismi ne olsun?",
        "label_en": "What should your robot friend's name be?",
        "default": "NOVA",
        "placeholder": "NOVA, STELLA, COSMO...",
        "usage": "Robot companion appears throughout all pages as guide and friend"
    },
    "favorite_planet": {
        "type": "select",
        "label_tr": "En sevdiğin gezegen hangisi?",
        "label_en": "What's your favorite planet?",
        "options": [
            {"value": "jupiter", "label_tr": "Jüpiter (En Büyük!)", "label_en": "Jupiter (Biggest!)"},
            {"value": "saturn", "label_tr": "Satürn (Halkaları!)", "label_en": "Saturn (Rings!)"},
            {"value": "mars", "label_tr": "Mars (Kırmızı Gezegen!)", "label_en": "Mars (Red Planet!)"},
            {"value": "neptune", "label_tr": "Neptün (En Uzak!)", "label_en": "Neptune (Farthest!)"},
            {"value": "earth", "label_tr": "Dünya (Evimiz!)", "label_en": "Earth (Our Home!)"}
        ],
        "default": "jupiter",
        "usage": "Emphasized in pages 13-15 (Jupiter peak)"
    }
}

# ============================================================================
# DATABASE UPDATE FUNCTION
# ============================================================================

async def update_space_scenario():
    """GÜNEŞ SİSTEMİ senaryosunu YENİ SİSTEM ile günceller."""
    
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL environment variable not set")
    
    engine = create_async_engine(db_url, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Find Space scenario
        result = await session.execute(
            select(Scenario).where(
                (Scenario.theme_key == "solar_systems_space") |
                (Scenario.name.ilike("%Güneş Sistemi%")) |
                (Scenario.name.ilike("%Uzay%")) |
                (Scenario.name.ilike("%Space%"))
            )
        )
        scenario = result.scalar_one_or_none()
        
        if not scenario:
            print("❌ Space scenario not found!")
            return
        
        print(f"\n✅ Found scenario: {scenario.name} (ID: {scenario.id})")
        
        # Verify prompt lengths
        print(f"\n📏 PROMPT LENGTHS:")
        print(f"   Cover: {len(SPACE_COVER_PROMPT)} chars (max 500)")
        print(f"   Page: {len(SPACE_PAGE_PROMPT)} chars (max 500)")
        print(f"   Story: {len(SPACE_STORY_PROMPT_TR)} chars")
        
        if len(SPACE_COVER_PROMPT) > 500 or len(SPACE_PAGE_PROMPT) > 500:
            print("❌ HATA: Prompt 500 karakteri aşıyor!")
            return
        
        # Update scenario
        await session.execute(
            update(Scenario)
            .where(Scenario.id == scenario.id)
            .values(
                cover_prompt_template=SPACE_COVER_PROMPT,
                page_prompt_template=SPACE_PAGE_PROMPT,
                story_prompt_tr=SPACE_STORY_PROMPT_TR,
                outfit_girl=OUTFIT_GIRL,
                outfit_boy=OUTFIT_BOY,
                cultural_elements=SPACE_CULTURAL_ELEMENTS,
                custom_inputs_schema=SPACE_CUSTOM_INPUTS,
                description="8 gezegen macerası! Modüler uzay istasyonundan başlayarak Merkür'den Neptün'e kadar tüm gezegenleri keşfet. AI robot arkadaşınla birlikte Jüpiter'in ihtişamını, Satürn'ün halkalarını ve Mars'taki yaşam izlerini öğren!",
                marketing_badge="YENİ! Uzay Macerası",
                age_range="7-10",
                tagline="8 gezegen, sonsuz keşif!"
            )
        )
        
        await session.commit()
        
        print("\n✅ GÜNEŞ SİSTEMİ scenario updated successfully!")
        print("   - Modular prompts: DONE")
        print("   - Story blueprint: DONE")
        print("   - 8-planet progression: DONE")
        print("   - AI robot companion: DONE")
        print("   - Outfit (astronaut): DONE")
        print("   - Cultural elements: DONE")
        print("   - Custom inputs: DONE")

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    asyncio.run(update_space_scenario())
