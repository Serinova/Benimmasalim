"""
YENİ SİSTEM: Çatalhöyük Neolitik Kenti Macerası Scenario Update
===============================================================
ESKİ sistem TAMAMEN SİLİNDİ - SIFIRDAN yazıldı!

Ocean/Dinosaur/Galata standardına uygun:
- Modular prompt (500 char limit)
- Story blueprint (Arkeoloji Keşfi + Tarih Dopamini)
- Educational focus (9000 yıllık tarih!)
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

CATALHOYUK_COVER_PROMPT = """Catalhoyuk Neolithic site scene: {scene_description}.
Child in foreground, ancient Catalhoyuk archaeological site in background.
9000-year-old settlement, mud-brick houses with rooftop entrances.
Archaeological excavation site visible, layers of ancient city.
Konya plain landscape, Turkish countryside.
Wide shot: child 30%, ancient site 70%.
Educational, time-travel atmosphere.
Historic discovery feeling."""

CATALHOYUK_PAGE_PROMPT = """Catalhoyuk Neolithic scene: {scene_description}.
Elements: [Houses: mud-brick structures, flat roofs, ladder entrances / Wall art: ancient paintings (bulls, geometric patterns) / Excavation: archaeological dig site, layers / Daily life: pottery, tools, hearths / Settlement: clustered houses, no streets / Landscape: Konya plain, open field].
Earthy colors: mud brown, ochre, terracotta.
Ancient, educational, discovery atmosphere.
UNESCO World Heritage site."""

# ============================================================================
# STORY BLUEPRINT (Arkeoloji Keşfi + Tarih Dopamini)
# ============================================================================

CATALHOYUK_STORY_PROMPT_TR = """
# ARKEOLOJİ KEŞFİ DOPAMİN YÖNETİMİ - ÇATALHÖYÜK NEOLİTİK KENTİ MACERASI

## TEMEL YAPI: 7 BÖLÜM, 22 SAYFA

Bu arkeoloji ve tarih keşif hikayesi, çocuğa **bilim**, **tarih**, **merak** ve **uygarlık** değerlerini öğretir.

🏛️ **ÇATALHÖYÜK**: Dünyanın en eski şehirlerinden biri (9000 yıl önce!), UNESCO Dünya Mirası!

---

### BÖLÜM 1 - GİRİŞ: ÇATALHÖYÜK ARKEOLOJİK ALANI (1-4)
- {child_name}, Konya'nın Çumra ilçesinde, Çatalhöyük arkeolojik alanına varıyor
- Höyük: Eski kentin kalıntıları tepede
- İlk bakış: "Burası 9000 yıl önce bir şehirmiş!"
- Heyecan: "İnsanlık tarihinin ilk şehirlerinden biri!"
- **Değer**: Bilim, tarih, merak

**Sayfa içeriği**:
- S1: Çatalhöyük'e varış, Konya ovası
- S2: Höyüğü görme, eski kent tepesi
- S3: Arkeolojik kazı alanı, bilim insanları
- S4: "9000 yıl önce!" hayranlığı ✓ **İLK HAYRANLIK**

---

### BÖLÜM 2 - ZAMAN YOLCULUĞU: 9000 YIL ÖNCESINE (5-9)
**[HAYAL DÖNGÜSÜ #1]**
- **Zaman Yolculuğu**: Hayal ile 9000 yıl öncesine
- **Neolitik Çağ**: MÖ 7100, tarım devrimi başlamış
- **İlk Yerleşik Yaşam**: Artık mağaralardan çıkıldı!
- **Topluluk**: Binlerce insan bir arada yaşıyor

**EPİK AN #1**: İnsanlık tarihinin dönüm noktası - ilk şehir yaşamı!

**Sayfa içeriği**:
- S5: Hayal ile zaman yolculuğu, "9000 yıl önce..."
- S6: Neolitik Çağ, tarım devrimi
- S7: İlk yerleşik yaşam, "Artık göçebe değil!" ✓ **ZAMAN ZİRVESİ #1**
- S8: Topluluk yaşamı, binlerce insan
- S9: Şehir görünümü, kerpiç evler

---

### BÖLÜM 3 - İLK EVLER: KERPİÇ VE DAMDAN GİRİŞ (10-14)
**[MİMARİ KEŞİF DÖNGÜSÜ #2]**
- **Kerpiç Evler**: Topraktan yapılmış, düz damlı
- **Damdan Giriş**: Kapı yok! Damdan merdiven ile iniş (benzersiz!)
- **Bitişik Düzen**: Evler yan yana, sokak yok!
- **İç Mekan**: Ocak, tahıl depolama, duvar resimleri

**EPİK AN #2**: Damdan girilen evler - akıllıca mimari! ✓ **MİMARİ ZİRVESİ #2**

**Sayfa içeriği**:
- S10: Kerpiç evleri keşfetme
- S11: Düz damlar, merdiven girişi
- S12: "Damdan mı giriliyor? Akıllıca!" ✓ **MİMARİ KEŞİF ZİRVESİ**
- S13: Bitişik evler, sokak yok
- S14: İç mekan, ocak ve depo

---

### BÖLÜM 4 - DUVAR RESİMLERİ: İLK SANAT (15-18)
**[SANAT KEŞFİ DÖNGÜSÜ #3]**
- **Duvar Resimleri**: 9000 yıllık sanat eserleri!
- **Boğa Resimleri**: Güçlü boğalar, avcılık sahneleri
- **Geometrik Desenler**: İlk soyut sanat
- **Renkler**: Doğal boyalar (kırmızı, siyah, beyaz)

**EPİK AN #3**: İnsanlık tarihinin ilk sanat eserleri! ✓ **SANAT ZİRVESİ #3**

**Sayfa içeriği**:
- S15: Duvar resimlerini keşfetme
- S16: Boğa resimleri, "9000 yıllık sanat!" ✓ **SANAT KEŞFİ ZİRVESİ**
- S17: Geometrik desenler, ilk soyut sanat
- S18: Doğal boyalar, el emeği

---

### BÖLÜM 5 - NEOLİTİK YAŞAM: İLK UYGARLIK (19-20)
**[UYGARLIK DÖNGÜSÜ #4]**
- **Tarım**: Buğday, arpa ekimi - artık toplayıcı değil!
- **Çanak Çömlek**: El yapımı kaplar, depolama
- **Aletler**: Obsidyen bıçaklar, taş aletler
- **Topluluk**: İşbirliği, paylaşım, ilk toplum kuralları

**EPİK AN #4**: İlk uygarlık adımları - her şey buradan başladı!

**Sayfa içeriği**:
- S19: Tarım ve çanak çömlek
- S20: İlk uygarlık, "Her şey buradan başladı!" ✓ **UYGARLIK ZİRVESİ #4**

---

### BÖLÜM 6 - FİNAL: TARİHİN DEĞERİ VE BİLİM (21-22)
**[BİLİM DORUĞU - FİNAL]**
- **Arkeoloji**: Geçmişi ortaya çıkarma bilimi
- **Koruma**: UNESCO Dünya Mirası olarak koruma
- **Öğrenme**: Geçmişten bugüne dersler
- **Mesaj**: "Tarih bize kim olduğumuzu söyler!"

**EPİK AN #5**: Bilimin gücü, tarihin değeri! ✓ **BİLİM DORUĞU**

**Sayfa içeriği**:
- S21: Arkeolojinin önemi, bilim
- S22: Tarihin değeri, "Geçmiş geleceğimizdir!"

---

## DOPAMIN ZİRVELERİ:
1. **Sayfa 4**: 9000 yıl önce hayranlığı (İLK HAYRANLIK)
2. **Sayfa 7**: İlk yerleşik yaşam (ZAMAN ZİRVESİ)
3. **Sayfa 12**: Damdan giriş keşfi (MİMARİ ZİRVESİ)
4. **Sayfa 16**: Duvar resimleri (SANAT ZİRVESİ)
5. **Sayfa 20**: İlk uygarlık (UYGARLIK ZİRVESİ)
6. **Sayfa 22**: Bilim ve tarih (BİLİM DORUĞU)

---

## DEĞERLER:
- **BİLİM**: Arkeoloji, tarih araştırması, bilimsel yöntem
- **TARİH**: 9000 yıllık miras, geçmişe saygı
- **MERAK**: Soru sorma, keşfetme, öğrenme
- **UYGARLIK**: İlk yerleşik yaşam, tarım devrimi, toplum kuralları

---

## EĞİTİM ODAKLARI:
- **Neolitik Çağ**: MÖ 7100 - MÖ 5700
- **Tarım Devrimi**: Göçebelikten yerleşik yaşama
- **İlk Şehir**: Dünyanın en eski şehirlerinden
- **UNESCO**: Dünya Mirası koruma
- **Arkeoloji**: Geçmişi bilimsel yöntemle ortaya çıkarma

---

## CUSTOM INPUTS:
- {favorite_discovery}: Çocuğun en sevdiği keşif (örn: Damdan Giriş, Duvar Resimleri, Tarım, Kerpiç Evler)
- Bu öğe sayfa 15-17 arasında vurgulanacak

---

## NOT:
Her sayfa {scene_description} ile dinamik olarak hikayeye entegre edilir.
Çocuk her sayfada TARİH ve BİLİM keşfeder, 9000 yıllık zaman yolculuğu yapar!
Eğitici, bilimsel, heyecanlı!
"""

# ============================================================================
# OUTFIT DEFINITIONS
# ============================================================================

OUTFIT_GIRL = """Casual archaeological site visit outfit.
Comfortable t-shirt or casual top, practical pants or jeans.
Sun hat or baseball cap for Konya sun protection.
Comfortable sneakers or walking shoes.
Small backpack with water bottle and notebook (archaeologist style!).
Age-appropriate, practical for outdoor historical site exploration.
Educational, adventurous atmosphere."""

OUTFIT_BOY = """Casual archaeological site visit outfit.
Comfortable t-shirt, practical pants or cargo pants.
Sun hat or baseball cap for Konya sun protection.
Comfortable sneakers or walking shoes.
Small backpack with water bottle and notebook (archaeologist style!).
Age-appropriate, practical for outdoor historical site exploration.
Educational, adventurous atmosphere."""

# ============================================================================
# CULTURAL ELEMENTS
# ============================================================================

CATALHOYUK_CULTURAL_ELEMENTS = {
    "location": "Konya, Turkey (Çumra district)",
    "historic_site": "Çatalhöyük Neolithic City, 9000 years old (7100-5700 BC)",
    "unesco": "UNESCO World Heritage Site",
    "period": "Neolithic Age (New Stone Age)",
    "significance": "One of the world's oldest cities, first urban settlement",
    "architecture": [
        "Mud-brick houses with flat roofs",
        "Rooftop entrances (no doors, ladder access!)",
        "Clustered houses (no streets between)",
        "Interior hearths and storage areas"
    ],
    "art_elements": [
        "Wall paintings (9000 years old!)",
        "Bull motifs and hunting scenes",
        "Geometric patterns (first abstract art)",
        "Natural pigments (red, black, white)"
    ],
    "daily_life": [
        "Agriculture (wheat, barley cultivation)",
        "Pottery making",
        "Obsidian tools and blades",
        "Community living"
    ],
    "atmosphere": "Educational, scientific discovery, time-travel feeling, archaeological wonder",
    "educational_focus": [
        "Neolithic Age and agricultural revolution",
        "First settled urban life (transition from nomadic)",
        "Early civilization development",
        "Archaeology as a science",
        "UNESCO World Heritage preservation"
    ],
    "values": ["Science", "History appreciation", "Curiosity", "Civilization awareness"],
    "unique_features": [
        "Rooftop entrances (unique architectural feature!)",
        "9000 years old (one of oldest cities)",
        "No streets (houses connected)",
        "First wall art in human history"
    ]
}

# ============================================================================
# CUSTOM INPUTS
# ============================================================================

CATALHOYUK_CUSTOM_INPUTS = {
    "favorite_discovery": {
        "type": "select",
        "label_tr": "En sevdiğin keşif hangisi?",
        "label_en": "What's your favorite discovery?",
        "options": [
            {"value": "rooftop_entrance", "label_tr": "Damdan Giriş", "label_en": "Rooftop Entrance"},
            {"value": "wall_paintings", "label_tr": "Duvar Resimleri", "label_en": "Wall Paintings"},
            {"value": "agriculture", "label_tr": "İlk Tarım", "label_en": "First Agriculture"},
            {"value": "mud_houses", "label_tr": "Kerpiç Evler", "label_en": "Mud-Brick Houses"},
            {"value": "first_city", "label_tr": "İlk Şehir", "label_en": "First City"}
        ],
        "default": "rooftop_entrance",
        "usage": "Emphasized in pages 15-17 (discovery peak)"
    }
}

# ============================================================================
# DATABASE UPDATE FUNCTION
# ============================================================================

async def update_catalhoyuk_scenario():
    """ÇATALHÖYÜK senaryosunu YENİ SİSTEM ile günceller."""
    
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL environment variable not set")
    
    engine = create_async_engine(db_url, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Find Catalhoyuk scenario
        result = await session.execute(
            select(Scenario).where(
                (Scenario.theme_key == "catalhoyuk_neolithic_city") |
                (Scenario.name.ilike("%Çatalhöyük%")) |
                (Scenario.name.ilike("%Catalhoyuk%"))
            )
        )
        scenario = result.scalar_one_or_none()
        
        if not scenario:
            print("❌ Çatalhöyük scenario not found!")
            return
        
        print(f"\n✅ Found scenario: {scenario.name} (ID: {scenario.id})")
        
        # Verify prompt lengths
        print(f"\n📏 PROMPT LENGTHS:")
        print(f"   Cover: {len(CATALHOYUK_COVER_PROMPT)} chars (max 500)")
        print(f"   Page: {len(CATALHOYUK_PAGE_PROMPT)} chars (max 500)")
        print(f"   Story: {len(CATALHOYUK_STORY_PROMPT_TR)} chars")
        
        if len(CATALHOYUK_COVER_PROMPT) > 500 or len(CATALHOYUK_PAGE_PROMPT) > 500:
            print("❌ HATA: Prompt 500 karakteri aşıyor!")
            return
        
        # Update scenario
        await session.execute(
            update(Scenario)
            .where(Scenario.id == scenario.id)
            .values(
                cover_prompt_template=CATALHOYUK_COVER_PROMPT,
                page_prompt_template=CATALHOYUK_PAGE_PROMPT,
                story_prompt_tr=CATALHOYUK_STORY_PROMPT_TR,
                outfit_girl=OUTFIT_GIRL,
                outfit_boy=OUTFIT_BOY,
                cultural_elements=CATALHOYUK_CULTURAL_ELEMENTS,
                custom_inputs_schema=CATALHOYUK_CUSTOM_INPUTS,
                description="9000 yıl öncesine yolculuk! Dünyanın en eski şehirlerinden Çatalhöyük'ü keşfet. Damdan girilen kerpiç evler, duvar resimleri ve ilk uygarlık adımlarını öğren. UNESCO Dünya Mirası'nda arkeoloji macerası!",
                marketing_badge="YENİ! Arkeoloji Macerası",
                age_range="7-10",
                tagline="9000 yıllık zaman yolculuğu!"
            )
        )
        
        await session.commit()
        
        print("\n✅ ÇATALHÖYÜK scenario updated successfully!")
        print("   - Modular prompts: DONE")
        print("   - Story blueprint: DONE")
        print("   - Educational focus: DONE")
        print("   - Outfit (archaeologist style): DONE")
        print("   - Cultural elements: DONE")
        print("   - Custom inputs: DONE")

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    asyncio.run(update_catalhoyuk_scenario())
