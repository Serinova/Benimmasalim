"""
YENİ SİSTEM: Galata Kulesi Macerası Scenario Update
================================================
ESKİ sistem TAMAMEN SİLİNDİ - SIFIRDAN yazıldı!

Ocean/Dinosaur standardına uygun:
- Modular prompt (500 char limit)
- Story blueprint (Dopamine Management)
- Cultural elements (Istanbul, tarih)
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

GALATA_COVER_PROMPT = """Istanbul Galata Tower scene: {scene_description}.
Child in foreground, iconic medieval Galata Tower (67m stone tower, conical roof) in background.
Bosphorus strait visible with ships, connecting Europe and Asia.
Historic Galata neighborhood: cobblestone streets, old stone buildings, red tile roofs.
Golden sunset over Istanbul cityscape.
Wide shot: child 25%, tower and cityscape 75%.
Historic, nostalgic atmosphere."""

GALATA_PAGE_PROMPT = """Istanbul Galata scene: {scene_description}.
Elements: [Galata Tower: 67m medieval stone tower, conical roof, observation deck / Bosphorus: strait with ships, ferries, seagulls / Bridges: Galata Bridge, Golden Horn / Historic quarter: cobblestone streets, stone buildings, cafes / Tram: nostalgic red tram / Cityscape: minarets, domes, red roofs / Sunset: golden light over Bosphorus].
Warm Istanbul colors: stone beige, red tile, blue strait.
Historic, bustling, beautiful city."""

# ============================================================================
# STORY BLUEPRINT (Dopamine Management)
# ============================================================================

GALATA_STORY_PROMPT_TR = """
# İSTANBUL KEŞFİ DOPAMIN YÖNETİMİ - GALATA KULESİ MACERASI

## TEMEL YAPI: 7 BÖLÜM, 22 SAYFA

Bu İstanbul keşif hikayesi, çocuğa **tarih**, **cesaret**, **keşif** ve **güzellik** değerlerini öğretir.

---

### BÖLÜM 1 - GİRİŞ: GALATA MAHALLESİ (1-4)
- {child_name}, İstanbul'un tarihi Galata mahallesine varıyor
- Taş sokaklar, eski binalar, kırmızı kiremitler
- İlk bakış: Galata Kulesi göğe yükseliyor (67m)
- Heyecan: "Çok yüksek! Çıkabilir miyim?"
- **Değer**: Cesaret, tarihi merak

**EPİK AN #0**: İlk bakışta 67m yükseklikte Galata Kulesi - tarihi ihtişam!

**Sayfa içeriği**: 
- S1: İstanbul'a varış, Galata mahallesi
- S2: Tarihi sokakları keşfetme
- S3: Galata Kulesi'ni ilk görme
- S4: Kuleye yaklaşma, "Ne kadar yüksek!" ✓ **İLK HAYRANLIK ZİRVESİ**

---

### BÖLÜM 2 - TIRMANMA: MERDİVEN YOLCULUĞU (5-9)
**[HEYECAN DÖNGÜSÜ #1]**
- **Kaygı**: Dar spiral merdiven, yükseklik korkusu
- **Aksiyon**: Adım adım tırmanma, pencerelerden manzara
- **Başarı**: Her kat bir zafer!

**Sayfa içeriği**:
- S5: Merdivenler başlıyor, dar ve spiral
- S6: Yarı yol, pencereden ilk manzara
- S7: Yorgunluk ama devam, cesaret
- S8: Son katlar, neredeyse tepede
- S9: Gözlem katına ulaşma! ✓ **BAŞARI ZİRVESİ #1**

---

### BÖLÜM 3 - PANORAMA DORUĞU: 360° MANZARA (10-14)
**[HAYRANLİK DÖNGÜSÜ #2]**
- **Vay be!**: İstanbul panoraması, 360 derece manzara
- **Boğaz**: Avrupa ve Asya kıtaları aynı karede
- **Gemiler**: Boğaz'dan geçen dev gemiler, feribotlar, martılar
- **Tarihi Siluet**: Camiler, minareler, kırmızı çatılar

**EPİK AN #1**: Boğaz'ın iki yakası - iki kıta arasında durmak!

**Sayfa içeriği**:
- S10: İlk panorama, çocuk şaşkın
- S11: Boğaz'ı görme, gemiler
- S12: Avrupa yakası, tarihi siluet
- S13: Asya yakası, kıtalar arası geçiş
- S14: 360° dönme, İstanbul'un tamamı ✓ **HAYRANLİK ZİRVESİ #2**

---

### BÖLÜM 4 - BOĞAZ KEŞFİ: KÖPRÜLER VE GEMİLER (15-18)
**[KEŞİF DÖNGÜSÜ #3]**
- **Galata Köprüsü**: Tarihi köprü, balıkçılar, tekne
- **Haliç**: Altın Haliç'in güzelliği
- **Gemiler**: Dev yük gemileri, turist feribotları
- **Martılar**: Özgürce uçan martılar

**EPİK AN #2**: İki kıtayı birleştiren köprülerin ihtişamı!

**Sayfa içeriği**:
- S15: Galata Köprüsü'nü görme
- S16: Boğaz'dan geçen gemiler ✓ **KEŞİF ZİRVESİ #3**
- S17: Haliç'in güzelliği
- S18: Martıların uçuşu, özgürlük hissi

---

### BÖLÜM 5 - TARİHİ MAHALLE: NOSTALJI (19-20)
**[KÜLTÜREL KEŞİF DÖNGÜSÜ #4]**
- **Aşağı İnme**: Kuleden inme, mahalle keşfi
- **Taş Sokaklar**: Eski İstanbul dokusu
- **Nostaljik Tram**: Kırmızı tramvay, tarihi taşımacılık
- **Kafeler**: Kahve kokuları, sıcak atmosfer

**Sayfa içeriği**:
- S19: Kuleden inme, mahalle keşfi
- S20: Nostaljik tram, taş sokaklar ✓ **KÜLTÜREL TATMIN #4**

---

### BÖLÜM 6 - GÜNBATIMI: İSTANBUL'UN GÜZELLİĞİ (21-22)
**[DUYGU DORUĞU - FİNAL]**
- **Günbatımı**: Boğaz üzerinde altın ışık
- **İstanbul Silueti**: Camiler, kuleler, köprüler altın renklerle
- **Dönüş**: Kalbe dolan güzellik, öğrendikleri
- **Mesaj**: "İstanbul dünya güzeli!"

**EPİK AN #3**: Günbatımında İstanbul'un büyüsü! ✓ **DUYGU ZİRVESİ**

**Sayfa içeriği**:
- S21: Günbatımı, altın ışık
- S22: Veda, dönüş, kalbe dolan güzellik

---

## DOPAMIN ZİRVELERİ:
1. **Sayfa 4**: İlk bakış - 67m yükseklik (İLK HAYRANLIK)
2. **Sayfa 9**: Gözlem katına ulaşma (BAŞARI)
3. **Sayfa 14**: 360° İstanbul panoraması (HAYRANLİK)
4. **Sayfa 16**: Boğaz gemileri (KEŞİF)
5. **Sayfa 20**: Nostaljik mahalle (KÜLTÜR)
6. **Sayfa 22**: Günbatımı finali (DUYGU DORUĞU)

---

## DEĞERLER:
- **TARİH**: Kültürel miras, Galata Kulesi'nin hikayesi
- **CESARET**: Yüksekliğe tırmanma, korkuyu yenme
- **KEŞİF**: İstanbul'u keşfetme, iki kıta
- **GÜZELLİK**: Şehrin estetiği, günbatımı

---

## GÜVENLİK KURALLARI:
- Tırmanma güvenli, yetişkin rehberliğinde
- Yükseklikten düşme riski yok (korkuluklar var)
- Pozitif, güvenli atmosfer

---

## CUSTOM INPUTS:
- {favorite_location}: Çocuğun en sevdiği yer (örn: Galata Köprüsü, Boğaz, Kule Tepesi)
- Bu öğe sayfa 14-16 arasında vurgulanacak

---

## NOT:
Her sayfa {scene_description} ile dinamik olarak hikayeye entegre edilir.
Çocuk her sayfada aktif rol alır, keşfeder, öğrenir.
"""

# ============================================================================
# OUTFIT DEFINITIONS
# ============================================================================

OUTFIT_GIRL = """Modern casual outfit for Galata Tower visit.
White or pastel t-shirt with Istanbul graphic, denim shorts or light pants, comfortable sneakers.
Sun hat or baseball cap for Istanbul sun.
Small backpack with water bottle.
Practical for climbing stairs, comfortable for city exploration.
Age-appropriate, modest, safe for historic site visit."""

OUTFIT_BOY = """Modern casual outfit for Galata Tower visit.
Graphic t-shirt (Istanbul theme or plain color), denim shorts or cargo pants, comfortable sneakers.
Baseball cap or bucket hat for Istanbul sun.
Small backpack with water bottle.
Practical for climbing stairs, comfortable for city exploration.
Age-appropriate, safe for historic site visit."""

# ============================================================================
# CULTURAL ELEMENTS
# ============================================================================

GALATA_CULTURAL_ELEMENTS = {
    "location": "Istanbul, Turkey",
    "historic_site": "Galata Tower (Galata Kulesi), built 1348",
    "geography": "Bosphorus strait, connecting Europe and Asia",
    "landmarks": [
        "Galata Tower (67m medieval stone tower)",
        "Galata Bridge (Galata Köprüsü)",
        "Golden Horn (Haliç)",
        "Bosphorus strait",
        "Historic Galata neighborhood",
        "Nostalgic red tram"
    ],
    "cityscape": [
        "Mosques and minarets",
        "Red tile roofs",
        "Stone buildings",
        "Cobblestone streets"
    ],
    "marine_elements": [
        "Ships and ferries",
        "Seagulls",
        "Fishing boats"
    ],
    "atmosphere": "Historic, nostalgic, beautiful city, sunset golden light",
    "educational_focus": [
        "Medieval architecture",
        "Bosphorus geography",
        "Europe-Asia connection",
        "Istanbul history",
        "Cultural heritage"
    ],
    "values": ["History", "Courage", "Exploration", "Beauty appreciation"]
}

# ============================================================================
# CUSTOM INPUTS
# ============================================================================

GALATA_CUSTOM_INPUTS = {
    "favorite_location": {
        "type": "select",
        "label_tr": "En sevdiğin İstanbul yeri hangisi?",
        "label_en": "What's your favorite Istanbul spot?",
        "options": [
            {"value": "galata_tower", "label_tr": "Galata Kulesi", "label_en": "Galata Tower"},
            {"value": "bosphorus", "label_tr": "Boğaz", "label_en": "Bosphorus"},
            {"value": "galata_bridge", "label_tr": "Galata Köprüsü", "label_en": "Galata Bridge"},
            {"value": "historic_quarter", "label_tr": "Tarihi Mahalle", "label_en": "Historic Quarter"},
            {"value": "sunset_view", "label_tr": "Günbatımı Manzarası", "label_en": "Sunset View"}
        ],
        "default": "galata_tower",
        "usage": "Emphasized in pages 14-16 (panorama view)"
    }
}

# ============================================================================
# DATABASE UPDATE FUNCTION
# ============================================================================

async def update_galata_scenario():
    """GALATA KULESİ senaryosunu YENİ SİSTEM ile günceller."""
    
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL environment variable not set")
    
    engine = create_async_engine(db_url, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Find Galata scenario
        result = await session.execute(
            select(Scenario).where(
                (Scenario.theme_key == "galata_tower_istanbul") |
                (Scenario.name.ilike("%Galata%"))
            )
        )
        scenario = result.scalar_one_or_none()
        
        if not scenario:
            print("❌ Galata scenario not found!")
            return
        
        print(f"\n✅ Found scenario: {scenario.name} (ID: {scenario.id})")
        
        # Verify prompt lengths
        print(f"\n📏 PROMPT LENGTHS:")
        print(f"   Cover: {len(GALATA_COVER_PROMPT)} chars (max 500)")
        print(f"   Page: {len(GALATA_PAGE_PROMPT)} chars (max 500)")
        print(f"   Story: {len(GALATA_STORY_PROMPT_TR)} chars")
        
        if len(GALATA_COVER_PROMPT) > 500 or len(GALATA_PAGE_PROMPT) > 500:
            print("❌ HATA: Prompt 500 karakteri aşıyor!")
            return
        
        # Update scenario
        await session.execute(
            update(Scenario)
            .where(Scenario.id == scenario.id)
            .values(
                cover_prompt_template=GALATA_COVER_PROMPT,
                page_prompt_template=GALATA_PAGE_PROMPT,
                story_prompt_tr=GALATA_STORY_PROMPT_TR,
                outfit_girl=OUTFIT_GIRL,
                outfit_boy=OUTFIT_BOY,
                cultural_elements=GALATA_CULTURAL_ELEMENTS,
                custom_inputs_schema=GALATA_CUSTOM_INPUTS,
                description="İstanbul'un sembolü Galata Kulesi'ne tırmanma macerası. Boğaz'ın iki yakasını, tarihi mahalleleri ve İstanbul'un eşsiz güzelliğini keşfet!",
                marketing_badge="YENİ! İstanbul Keşfi",
                age_range="6-10",
                tagline="Galata'dan İstanbul'u keşfet!"
            )
        )
        
        await session.commit()
        
        print("\n✅ GALATA KULESİ scenario updated successfully!")
        print("   - Modular prompts: DONE")
        print("   - Story blueprint: DONE")
        print("   - Cultural elements: DONE")
        print("   - Custom inputs: DONE")

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    asyncio.run(update_galata_scenario())
