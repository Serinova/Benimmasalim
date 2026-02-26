"""
YENİ SİSTEM: Sümela Manastırı Macerası Scenario Update
======================================================
ESKİ sistem TAMAMEN SİLİNDİ - SIFIRDAN yazıldı!

Ocean/Dinosaur/Galata standardına uygun:
- Modular prompt (500 char limit)
- Story blueprint (Dağ Keşfi + Tarih Dopamini)
- Kültürel hassasiyet (Kudüs standardı - dini figür YOK!)
"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import sessionmaker
from app.models import Scenario
import os

# ============================================================================
# MODULAR PROMPT COMPONENTS (500 char limit!)
# ============================================================================

SUMELA_COVER_PROMPT = """Trabzon Sumela Monastery scene: {scene_description}.
Child in foreground, historic Sumela Monastery carved into cliff face in background.
1200m altitude, perched on steep rock wall.
Lush green Altındere Valley forest below, waterfalls visible.
Mountain atmosphere, mist.
Wide shot: child 25%, monastery and nature 75%.
Epic scale: tiny child, massive cliff and monastery.
Historic, adventurous atmosphere."""

SUMELA_PAGE_PROMPT = """Sumela Monastery scene: {scene_description}.
Elements: [Monastery: carved into cliff (1200m), Byzantine frescoes (distant), stone arches / Cliff: steep rock face, dramatic height / Forest: lush green Altındere Valley, pine trees / Waterfalls: cascading water, mist / Mountain: peaks, clouds, fresh air / Path: stone steps climbing up].
Nature colors: green forest, gray rock, white mist.
Epic scale, adventurous.
NO religious figures, architecture and nature focus only."""

# ============================================================================
# STORY BLUEPRINT (Dağ Keşfi + Tarih Dopamini)
# ============================================================================

SUMELA_STORY_PROMPT_TR = """
# DAĞ KEŞFİ DOPAMİN YÖNETİMİ - SÜMELA MANASTIRI MACERASI

## TEMEL YAPI: 7 BÖLÜM, 22 SAYFA

Bu dağ ve tarih keşif hikayesi, çocuğa **cesaret**, **tarih**, **doğa** ve **keşif** değerlerini öğretir.

⚠️ **KÜLTÜREL HASSASİYET KURALLARI (KUDÜS STANDARDI)**:
- ❌ Dini figür tasvirleri YOK (İsa, Meryem, azizler YOK!)
- ❌ İbadet detayları YOK
- ✅ TARİHİ MİMARİ ve DOĞA odaklı
- ✅ KÜLTÜREL MİRAS perspektifi
- ✅ Freskler uzaktan, sanat olarak (figür detayı YOK!)

---

### BÖLÜM 1 - GİRİŞ: ALTINDERe VADİSİ (1-4)
- {child_name}, Trabzon'un yemyeşil Altındere Vadisi'ne varıyor
- Dağ havasında, orman sesleri
- İlk bakış: Kayalarda bir manastır! (1200m yükseklikte!)
- Heyecan: "Çok yüksekte! Nasıl çıkacağız?"
- **Değer**: Cesaret, merak

**Sayfa içeriği**:
- S1: Altındere Vadisi'ne varış, yeşil orman
- S2: Dağ havasını soluma, kuş sesleri
- S3: Manastırı uzaktan görme, "Kayaya oyulmuş!"
- S4: Macera başlıyor, heyecan ✓ **İLK HEYECAN**

---

### BÖLÜM 2 - ORMAN KEŞFİ: YEŞİL YÜRÜYÜŞ VE ŞELALE (5-9)
**[DOĞA KEŞFİ DÖNGÜSÜ #1]**
- **Orman Yürüyüşü**: Yeşil çam ormanı, temiz hava
- **Şelale**: Çağlayan su, serinlik, doğa sesleri
- **Doğa**: Ağaçlar, çiçekler, kelebekler
- **Yol**: Taş patika, yukarı doğru

**EPİK AN #1**: Şelalenin güzelliği, doğa ile buluşma!

**Sayfa içeriği**:
- S5: Orman yürüyüşü başlıyor, yeşillik
- S6: Çam ağaçları, temiz hava
- S7: Şelaleyi keşfetme, "Ne güzel!" ✓ **DOĞA ZİRVESİ #1**
- S8: Su sesleri, serinlik
- S9: Yukarı yol devam ediyor, cesaret

---

### BÖLÜM 3 - TIRMANMA: TAŞ BASAMAKLAR VE YÜKSEKLİK (10-14)
**[CESARET DÖNGÜSÜ #2]**
- **Kaygı**: Çok yüksek! Dik taş basamaklar
- **Aksiyon**: Adım adım tırmanma, nefes nefese
- **Manzara**: Her basamakta yeni bir manzara
- **Başarı**: Yorgun ama devam, cesaret!

**EPİK AN #2**: Tırmanış zaferi, yüksekliğe cesaret!

**Sayfa içeriği**:
- S10: Taş basamaklar başlıyor, dik yokuş
- S11: Yükseklik artıyor, aşağı bakmak
- S12: Yorgunluk ama devam, cesaret ✓ **CESARET ZİRVESİ #2**
- S13: Neredeyse tepede, son çaba
- S14: Manastıra ulaşma! ✓ **BAŞARI!**

---

### BÖLÜM 4 - MANASTIR DORUĞU: KAYA OYMA MİMARİ (15-18)
**[TARİHİ KEŞİF DÖNGÜSÜ #3]**
- **Mimari**: Kayaya oyulmuş, 1200m yükseklikte
- **Tarih**: MS 386 yılından beri (1600+ yıl!)
- **Freskler**: Uzaktan sanat eserleri (figür detayı YOK!)
- **Bizans**: Taş işçiliği, kemerler, odalar

**EPİK AN #3**: Kayaya oyulmuş tarihi mucize! ✓ **TARİHİ HAYRANLIK ZİRVESİ**

**Sayfa içeriği**:
- S15: Manastırın girişi, taş kapı
- S16: Kayaya oyulmuş odalar, "İnanılmaz!" ✓ **TARİH ZİRVESİ #3**
- S17: Freskler (uzaktan, sanat olarak - figür YOK!)
- S18: Bizans taş işçiliği, kemerler

---

### BÖLÜM 5 - DAĞ PANORAMASI: 1200M MANZARA (19-20)
**[DOĞA DORUĞU DÖNGÜSÜ #4]**
- **Manzara**: Altındere Vadisi, yeşil orman aşağıda
- **Yükseklik**: 1200m rakım, bulutlara yakın
- **Dağlar**: Etrafta dağ sıraları, zirveler
- **Huzur**: Dağ havasında huzur, başarı tatmini

**EPİK AN #4**: Bulutların arasında, dağ zirvesinde!

**Sayfa içeriği**:
- S19: Dağ manzarası, vadi aşağıda
- S20: Bulutlara yakın, "Zirvedeyiz!" ✓ **DOĞA DORUĞU #4**

---

### BÖLÜM 6 - FİNAL: DOĞA VE TARİH BULUŞMASI (21-22)
**[DUYGU DORUĞU - FİNAL]**
- **Birleşim**: Doğa ve tarih bir arada
- **Öğrenme**: 1600 yıllık tarih, doğanın güzelliği
- **Dönüş**: Kalbe dolan cesaret ve bilgi
- **Mesaj**: "Tarih ve doğa ne kadar değerli!"

**EPİK AN #5**: Tarihin doğa ile buluşması! ✓ **FİNAL DORUĞU**

**Sayfa içeriği**:
- S21: Doğa ve tarih buluşması, son bakış
- S22: Veda, dönüş, kalbe dolan deneyim

---

## DOPAMIN ZİRVELERİ:
1. **Sayfa 7**: Şelale keşfi (DOĞA)
2. **Sayfa 12**: Tırmanış cesaret (BAŞARI)
3. **Sayfa 14**: Manastıra ulaşma (ZAFERİ)
4. **Sayfa 16**: Kaya oyma mimari (TARİH ZİRVESİ)
5. **Sayfa 20**: 1200m manzara (DOĞA DORUĞU)
6. **Sayfa 22**: Doğa-tarih birleşimi (FİNAL)

---

## DEĞERLER:
- **CESARET**: Yüksekliğe tırmanma, zorlukları aşma
- **TARİH**: 1600+ yıllık miras, Bizans dönemi, kültürel miras
- **DOĞA**: Orman, şelale, dağ güzelliği, doğayı koruma
- **KEŞİF**: Kültürel ve doğal keşif, öğrenme

---

## GÜVENLİK VE HASSASİYET KURALLARI:
- ❌ Dini figür tasvirleri YOK (İsa, Meryem, azizler)
- ❌ İbadet detayları YOK
- ✅ TARİHİ MİMARİ odaklı (kaya oyma, taş işçiliği)
- ✅ DOĞA odaklı (orman, şelale, dağ)
- ✅ Freskler UZAKTAN, sanat olarak (figür detayı YOK!)
- ✅ KÜLTÜREL MİRAS perspektifi
- ✅ Tırmanış GÜVENLİ (rehberli, korunaklı)

---

## CUSTOM INPUTS:
- {favorite_element}: Çocuğun en sevdiği unsur (örn: Şelale, Kaya Oyma, Dağ Manzarası, Orman)
- Bu öğe sayfa 16-18 arasında vurgulanacak

---

## NOT:
Her sayfa {scene_description} ile dinamik olarak hikayeye entegre edilir.
Çocuk her sayfada DOĞA ve TARİH keşfeder, DİNİ FİGÜR YOK!
KUDÜS hassasiyet kuralları AYNIDIR!
"""

# ============================================================================
# OUTFIT DEFINITIONS
# ============================================================================

OUTFIT_GIRL = """Outdoor mountain hiking outfit for Sumela Monastery adventure.
Comfortable sporty t-shirt or athletic top, hiking pants (khaki or dark colors).
Sturdy hiking boots with ankle support.
Sun hat or baseball cap for mountain sun.
Small backpack with water bottle and essentials.
Light jacket tied around waist (mountain weather).
Practical for climbing steep stone steps, comfortable for mountain trekking.
Age-appropriate, safe for outdoor adventure."""

OUTFIT_BOY = """Outdoor mountain hiking outfit for Sumela Monastery adventure.
Sporty t-shirt or athletic shirt, hiking pants or cargo pants.
Sturdy hiking boots with ankle support.
Baseball cap or sun hat for mountain sun.
Small backpack with water bottle and essentials.
Light jacket tied around waist (mountain weather).
Practical for climbing steep stone steps, comfortable for mountain trekking.
Age-appropriate, safe for outdoor adventure."""

# ============================================================================
# CULTURAL ELEMENTS
# ============================================================================

SUMELA_CULTURAL_ELEMENTS = {
    "location": "Trabzon, Turkey (Altındere Valley, Maçka)",
    "historic_site": "Sumela Monastery, founded 386 AD (1600+ years old)",
    "altitude": "1200m above sea level, carved into cliff face",
    "architecture": "Byzantine rock-carved monastery",
    "natural_features": [
        "Altındere Valley forest",
        "Waterfalls and streams",
        "Mountain peaks and clouds",
        "Pine trees and lush greenery",
        "Mountain atmosphere and fresh air"
    ],
    "monastery_features": [
        "Carved into cliff face",
        "Stone arches and rooms",
        "Byzantine frescoes (distant, art only - NO figure details!)",
        "Rock craftsmanship",
        "Dramatic cliff location"
    ],
    "atmosphere": "Adventurous, historic, natural beauty, peaceful mountain air",
    "educational_focus": [
        "Byzantine architecture",
        "Rock carving techniques",
        "Historical preservation (1600+ years)",
        "Mountain ecology",
        "Cultural heritage"
    ],
    "values": ["Courage", "History appreciation", "Nature preservation", "Exploration"],
    "sensitivity_rules": [
        "NO religious figure depictions (Jesus, Mary, saints)",
        "NO worship details",
        "Frescoes shown from distance only (art perspective, NO figure details)",
        "Architecture and nature focus",
        "Cultural heritage perspective"
    ]
}

# ============================================================================
# CUSTOM INPUTS
# ============================================================================

SUMELA_CUSTOM_INPUTS = {
    "favorite_element": {
        "type": "select",
        "label_tr": "En sevdiğin unsur hangisi?",
        "label_en": "What's your favorite element?",
        "options": [
            {"value": "waterfall", "label_tr": "Şelale", "label_en": "Waterfall"},
            {"value": "rock_carving", "label_tr": "Kaya Oyma Mimari", "label_en": "Rock Carving Architecture"},
            {"value": "mountain_view", "label_tr": "Dağ Manzarası", "label_en": "Mountain View"},
            {"value": "forest", "label_tr": "Yeşil Orman", "label_en": "Green Forest"},
            {"value": "climbing", "label_tr": "Tırmanış Macerası", "label_en": "Climbing Adventure"}
        ],
        "default": "rock_carving",
        "usage": "Emphasized in pages 16-18 (monastery discovery)"
    }
}

# ============================================================================
# DATABASE UPDATE FUNCTION
# ============================================================================

async def update_sumela_scenario():
    """SÜMELA MANASTIRI senaryosunu YENİ SİSTEM ile günceller."""
    
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL environment variable not set")
    
    engine = create_async_engine(db_url, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Find Sumela scenario
        result = await session.execute(
            select(Scenario).where(
                (Scenario.theme_key == "sumela_monastery_trabzon") |
                (Scenario.name.ilike("%Sümela%")) |
                (Scenario.name.ilike("%Sumela%"))
            )
        )
        scenario = result.scalar_one_or_none()
        
        if not scenario:
            print("❌ Sümela scenario not found!")
            return
        
        print(f"\n✅ Found scenario: {scenario.name} (ID: {scenario.id})")
        
        # Verify prompt lengths
        print(f"\n📏 PROMPT LENGTHS:")
        print(f"   Cover: {len(SUMELA_COVER_PROMPT)} chars (max 500)")
        print(f"   Page: {len(SUMELA_PAGE_PROMPT)} chars (max 500)")
        print(f"   Story: {len(SUMELA_STORY_PROMPT_TR)} chars")
        
        if len(SUMELA_COVER_PROMPT) > 500 or len(SUMELA_PAGE_PROMPT) > 500:
            print("❌ HATA: Prompt 500 karakteri aşıyor!")
            return
        
        # Update scenario
        await session.execute(
            update(Scenario)
            .where(Scenario.id == scenario.id)
            .values(
                cover_prompt_template=SUMELA_COVER_PROMPT,
                page_prompt_template=SUMELA_PAGE_PROMPT,
                story_prompt_tr=SUMELA_STORY_PROMPT_TR,
                outfit_girl=OUTFIT_GIRL,
                outfit_boy=OUTFIT_BOY,
                cultural_elements=SUMELA_CULTURAL_ELEMENTS,
                custom_inputs_schema=SUMELA_CUSTOM_INPUTS,
                description="Trabzon'un büyülü Sümela Manastırı'na dağ macerası! 1200m yükseklikte kayaya oyulmuş tarihi manastırı keşfet, şelaleler ve yeşil ormanlarla dolu Altındere Vadisi'nde doğa ve tarihi birlikte öğren!",
                marketing_badge="YENİ! Dağ Macerası",
                age_range="7-10",
                tagline="Sümela'da dağ ve tarih keşfi!"
            )
        )
        
        await session.commit()
        
        print("\n✅ SÜMELA MANASTIRI scenario updated successfully!")
        print("   - Modular prompts: DONE")
        print("   - Story blueprint: DONE")
        print("   - Cultural sensitivity rules: DONE")
        print("   - Outfit (mountain gear): DONE")
        print("   - Cultural elements: DONE")
        print("   - Custom inputs: DONE")

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    asyncio.run(update_sumela_scenario())
