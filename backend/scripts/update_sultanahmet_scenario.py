"""
YENİ SİSTEM: Sultanahmet Camii Macerası Scenario Update
=======================================================
ESKİ sistem TAMAMEN SİLİNDİ - SIFIRDAN yazıldı!

Ocean/Dinosaur/Umre standardına uygun:
- Modular prompt (500 char limit)
- Story blueprint (Kültürel Keşif Dopamini)
- İslami hassasiyet kuralları (Umre/Kudüs gibi!)
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

SULTANAHMET_COVER_PROMPT = """Istanbul Blue Mosque scene: {scene_description}.
Child in foreground, iconic Sultanahmet Mosque (Blue Mosque) in background.
6 minarets, grand dome, Ottoman architecture.
Courtyard with fountain, historic Istanbul.
Blue Iznik tiles visible on exterior.
Golden sunset light.
Wide shot: child 30%, mosque 70%.
Peaceful, respectful, cultural atmosphere.
NO worship close-ups, NO religious figures."""

SULTANAHMET_PAGE_PROMPT = """Sultanahmet Mosque scene: {scene_description}.
Elements: [Blue Mosque: 6 minarets, grand dome, blue Iznik tiles (20,000+) / Courtyard: fountain, marble floor, arches / Architecture: Ottoman design, geometric patterns, calligraphy / Gardens: historic trees, flowers / Bosphorus view: distant / Istanbul skyline: minarets, domes].
Warm colors: blue tiles, white marble, gold accents.
Peaceful, cultural exploration.
NO worship close-ups, NO religious figures, distant people only."""

# ============================================================================
# STORY BLUEPRINT (Kültürel Keşif Dopamini)
# ============================================================================

SULTANAHMET_STORY_PROMPT_TR = """
# KÜLTÜREL KEŞİF DOPAMİN YÖNETİMİ - SULTANAHMET CAMİİ MACERASI

## TEMEL YAPI: 7 BÖLÜM, 22 SAYFA

Bu İslami mimari keşif hikayesi, çocuğa **saygı**, **sanat**, **tarih** ve **huzur** değerlerini öğretir.

⚠️ **KRİTİK İSLAMİ HASSASİYET KURALLARI**:
- ❌ İbadet close-up'ları YOK (namaz kılan insanlar gösterilmez!)
- ❌ Dini figür tasvirleri YOK (Hz. Muhammed, sahabe, melek YOK!)
- ❌ İçeride ibadet detayları YOK (sadece mimari ve sanat!)
- ❌ Detaylı yüz ifadeleri YOK (distant people sadece!)
- ✅ MİMARİ güzellik, SANAT, TARİH, KÜLTÜR odaklı!

---

### BÖLÜM 1 - GİRİŞ: SULTANAHMET MEYDANI (1-4)
- {child_name}, İstanbul'un tarihi Sultanahmet meydanına varıyor
- İlk bakış: Mavi Cami'nin ihtişamlı görünümü
- 6 minare göğe yükseliyor, dev kubbe parıldıyor
- Heyecan: "Ne kadar büyük ve güzel!"
- **Değer**: Saygı, kültürel merak

**Sayfa içeriği**:
- S1: Sultanahmet meydanına varış
- S2: Tarihi çevreyi keşfetme
- S3: Mavi Cami'yi ilk görme
- S4: Camiye yaklaşma, hayranlık ✓ **İLK HAYRANLIK**

---

### BÖLÜM 2 - AVLU KEŞFİ: ŞADIRVAN VE MERMERLİ AVLU (5-9)
**[KEŞİF DÖNGÜSÜ #1]**
- **Avlu**: Geniş mermerli avlu, sütunlar, kemerler
- **Şadırvan**: Ortadaki güzel şadırvan (tarihte abdest için kullanılırdı - eğitici!)
- **Mimari Detaylar**: Osmanlı desen ve süslemeleri
- **Huzur**: Sakin, barışçıl atmosfer

**EPİK AN #1**: Şadırvanlı avlunun simetrisi ve güzelliği!

**Sayfa içeriği**:
- S5: Avluya giriş, geniş alan
- S6: Şadırvanı keşfetme, su sesleri
- S7: Mermer sütunlar, kemerler
- S8: Avlu detayları, geometrik desenler
- S9: Avludan camiye bakış ✓ **MİMARİ GÜZELLİK ZİRVESİ #1**

---

### BÖLÜM 3 - MİMARİ DORUK: 6 MİNARE VE DEV KUBBE (10-14)
**[HAYRANLIK DÖNGÜSÜ #2]**
- **6 Minare**: Dünyada tek! (Mekke'den sonra en fazla minare)
- **Dev Kubbe**: 23.5m çap, gökyüzüne uzanan ihtişam
- **Dış Cephe**: Zarif hatlar, Osmanlı mimarisi
- **Tarih**: Sultan I. Ahmet tarafından 1616'da yaptırıldı

**EPİK AN #2**: 6 minarenin gökyüzündeki muhteşem görünümü!

**Sayfa içeriği**:
- S10: 6 minareyi saymak, "Vay be!"
- S11: Dev kubbeyi görmek, yükseklik
- S12: Dış cephe detayları, Osmanlı sanatı
- S13: Mimari simetri, mükemmellik
- S14: Bütünsel bakış, ihtişam ✓ **MİMARİ HAYRANLIK ZİRVESİ #2**

---

### BÖLÜM 4 - ÇİNİ SANATI: 20.000+ MAVİ ÇİNİ (15-18)
**[SANAT KEŞFİ DÖNGÜSÜ #3]**
- **Mavi Çiniler**: 20.000'den fazla İznik çinisi (Mavi Cami ismi buradan!)
- **Desenler**: Laleler, güller, geometrik şekiller
- **Hat Sanatı**: Kufi ve sülüs hat (uzaktan, okunmaz - sadece sanat!)
- **Renk**: Mavi, turkuaz, beyaz uyumu

**EPİK AN #3**: Çini sanatının ihtişamı, el emeği! ✓ **SANAT ZİRVESİ #3**

**Sayfa içeriği**:
- S15: Çinileri fark etme, "Ne kadar çok!"
- S16: Mavi renk, el emeği
- S17: Desenler, laleler, geometrik şekiller ✓ **SANAT KEŞFİ DORUĞU**
- S18: Hat sanatı (uzaktan, sanat olarak), güzellik

---

### BÖLÜM 5 - KÜLTÜREL DEĞERLER: OSMANLI MİRASI (19-20)
**[KÜLTÜR DÖNGÜSÜ #4]**
- **Tarih**: 400+ yıllık miras, Sultan I. Ahmet'in eseri
- **Sanat**: Osmanlı çini sanatı, mimari ustalık
- **Kültür**: İslami sanat ve geometri
- **Öğrenme**: Tarih ve kültür bilgisi

**Sayfa içeriği**:
- S19: Osmanlı tarihi, Sultan I. Ahmet
- S20: Sanat ve kültür mirası ✓ **KÜLTÜREL TATMIN #4**

---

### BÖLÜM 6 - FİNAL: GÜNBATIMI VE İSTANBUL PANORAMASI (21-22)
**[DUYGU DORUĞU - FİNAL]**
- **Günbatımı**: Altın ışık minarelere vuruyor
- **İstanbul Silueti**: Camiler, minareler, Boğaz
- **Huzur**: Kalbe dolan huzur ve güzellik
- **Mesaj**: "Sanat ve tarih ne kadar değerli!"

**EPİK AN #4**: Günbatımında Sultanahmet'in büyüsü! ✓ **HUZUR DORUĞU**

**Sayfa içeriği**:
- S21: Günbatımı, altın ışık
- S22: Veda, dönüş, kalbe dolan huzur

---

## DOPAMIN ZİRVELERİ:
1. **Sayfa 4**: İlk hayranlık (caminin ihtişamı)
2. **Sayfa 9**: Şadırvanlı avlu (mimari güzellik)
3. **Sayfa 14**: 6 minare + dev kubbe (mimari doruk)
4. **Sayfa 17**: 20.000+ mavi çini (sanat zirvesi)
5. **Sayfa 20**: Kültürel miras (öğrenme tatmini)
6. **Sayfa 22**: Günbatımı finali (huzur doruğu)

---

## DEĞERLER:
- **SAYGI**: İslami mekana saygı, kültürel duyarlılık
- **SANAT**: Osmanlı çini sanatı, mimari ustalık
- **TARİH**: 400+ yıllık miras, Sultan I. Ahmet
- **HUZUR**: Barışçıl, sakin, güzel atmosfer

---

## GÜVENLİK VE HASSASİYET KURALLARI:
- ❌ İbadet close-up'ları YOK
- ❌ Dini figür tasvirleri YOK
- ❌ İçeride namaz kılan insanlar gösterilmez
- ❌ Detaylı yüz ifadeleri YOK
- ✅ MİMARİ ve SANAT odaklı
- ✅ DIŞ mekan ağırlıklı (avlu, dış cephe)
- ✅ EĞİTİCİ yaklaşım (tarih, kültür, sanat)

---

## CUSTOM INPUTS:
- {favorite_element}: Çocuğun en sevdiği unsur (örn: Mavi Çiniler, 6 Minare, Şadırvan, Avlu)
- Bu öğe sayfa 15-17 arasında vurgulanacak

---

## NOT:
Her sayfa {scene_description} ile dinamik olarak hikayeye entegre edilir.
Çocuk her sayfada MİMARİ ve SANAT keşfeder, İBADET detayı YOK!
UMRE/KUDÜS hassasiyet kuralları AYNIDIR!
"""

# ============================================================================
# OUTFIT DEFINITIONS (İSLAMİ KURALLARA UYGUN!)
# ============================================================================

OUTFIT_GIRL = """Islamic modest outfit for mosque visit (UMRE standard).
WHITE or LIGHT-COLORED HIJAB headscarf covering hair completely (full head coverage!).
Long modest dress (ankle-length), loose-fitting, pastel colors (white, cream, light blue).
Comfortable flat shoes or modest sneakers.
Small bag for personal items.
Age-appropriate, respectful, suitable for sacred site visit.
CRITICAL: Hijab MUST cover hair completely, as per Islamic requirements."""

OUTFIT_BOY = """Islamic modest outfit for mosque visit (UMRE standard).
WHITE or LIGHT-COLORED TAQIYAH prayer cap on head (Islamic head covering).
Modest tunic (knee-length or longer) or button-up shirt, loose pants.
Comfortable shoes or modest sneakers.
Small bag for personal items.
Age-appropriate, respectful, suitable for sacred site visit.
CRITICAL: Taqiyah MUST be worn on head, as per Islamic requirements."""

# ============================================================================
# CULTURAL ELEMENTS
# ============================================================================

SULTANAHMET_CULTURAL_ELEMENTS = {
    "location": "Istanbul, Turkey (Sultanahmet Square)",
    "historic_site": "Sultanahmet Mosque (Blue Mosque), built 1616",
    "islamic_architecture": "Ottoman mosque architecture",
    "key_features": [
        "6 minarets (unique feature!)",
        "Grand dome (23.5m diameter)",
        "20,000+ blue Iznik tiles",
        "Courtyard with fountain (şadırvan)",
        "Marble floors and columns",
        "Geometric patterns",
        "Islamic calligraphy (art perspective only)"
    ],
    "art_elements": [
        "Blue Iznik tiles",
        "Tulip and rose patterns",
        "Geometric Islamic designs",
        "Ottoman craftsmanship"
    ],
    "atmosphere": "Peaceful, respectful, cultural exploration, NO worship details",
    "educational_focus": [
        "Ottoman architecture",
        "Islamic art and geometry",
        "Historical significance (Sultan Ahmed I)",
        "Cultural heritage",
        "Tile craftsmanship"
    ],
    "values": ["Respect", "Art appreciation", "History", "Peace"],
    "sensitivity_rules": [
        "NO worship close-ups",
        "NO religious figure depictions",
        "NO detailed faces of people",
        "Architecture and art focus only",
        "Distant people only",
        "Exterior and courtyard emphasis"
    ]
}

# ============================================================================
# CUSTOM INPUTS
# ============================================================================

SULTANAHMET_CUSTOM_INPUTS = {
    "favorite_element": {
        "type": "select",
        "label_tr": "En sevdiğin unsur hangisi?",
        "label_en": "What's your favorite element?",
        "options": [
            {"value": "blue_tiles", "label_tr": "Mavi Çiniler", "label_en": "Blue Tiles"},
            {"value": "six_minarets", "label_tr": "6 Minare", "label_en": "6 Minarets"},
            {"value": "fountain", "label_tr": "Şadırvan", "label_en": "Fountain"},
            {"value": "courtyard", "label_tr": "Avlu", "label_en": "Courtyard"},
            {"value": "dome", "label_tr": "Dev Kubbe", "label_en": "Grand Dome"}
        ],
        "default": "blue_tiles",
        "usage": "Emphasized in pages 15-17 (art discovery)"
    }
}

# ============================================================================
# DATABASE UPDATE FUNCTION
# ============================================================================

async def update_sultanahmet_scenario():
    """SULTANAHMET CAMİİ senaryosunu YENİ SİSTEM ile günceller."""
    
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL environment variable not set")
    
    engine = create_async_engine(db_url, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Find Sultanahmet scenario
        result = await session.execute(
            select(Scenario).where(
                (Scenario.theme_key == "sultanahmet_blue_mosque") |
                (Scenario.name.ilike("%Sultanahmet%")) |
                (Scenario.name.ilike("%Blue Mosque%")) |
                (Scenario.name.ilike("%Mavi Cami%"))
            )
        )
        scenario = result.scalar_one_or_none()
        
        if not scenario:
            print("❌ Sultanahmet scenario not found!")
            return
        
        print(f"\n✅ Found scenario: {scenario.name} (ID: {scenario.id})")
        
        # Verify prompt lengths
        print(f"\n📏 PROMPT LENGTHS:")
        print(f"   Cover: {len(SULTANAHMET_COVER_PROMPT)} chars (max 500)")
        print(f"   Page: {len(SULTANAHMET_PAGE_PROMPT)} chars (max 500)")
        print(f"   Story: {len(SULTANAHMET_STORY_PROMPT_TR)} chars")
        
        if len(SULTANAHMET_COVER_PROMPT) > 500 or len(SULTANAHMET_PAGE_PROMPT) > 500:
            print("❌ HATA: Prompt 500 karakteri aşıyor!")
            return
        
        # Update scenario
        await session.execute(
            update(Scenario)
            .where(Scenario.id == scenario.id)
            .values(
                cover_prompt_template=SULTANAHMET_COVER_PROMPT,
                page_prompt_template=SULTANAHMET_PAGE_PROMPT,
                story_prompt_tr=SULTANAHMET_STORY_PROMPT_TR,
                outfit_girl=OUTFIT_GIRL,
                outfit_boy=OUTFIT_BOY,
                cultural_elements=SULTANAHMET_CULTURAL_ELEMENTS,
                custom_inputs_schema=SULTANAHMET_CUSTOM_INPUTS,
                description="Sultanahmet Camii'nin (Mavi Cami) mimari güzelliğini ve Osmanlı sanatını keşfet. 6 minare, 20.000+ mavi çini ve tarihi avluyla İslami mimarinin ihtişamını öğren!",
                marketing_badge="YENİ! İslami Mimari",
                age_range="6-10",
                tagline="Mavi Cami'nin büyüsünü keşfet!"
            )
        )
        
        await session.commit()
        
        print("\n✅ SULTANAHMET CAMİİ scenario updated successfully!")
        print("   - Modular prompts: DONE")
        print("   - Story blueprint: DONE")
        print("   - Islamic sensitivity rules: DONE")
        print("   - Outfit (hijab/taqiyah): DONE")
        print("   - Cultural elements: DONE")
        print("   - Custom inputs: DONE")

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    asyncio.run(update_sultanahmet_scenario())
