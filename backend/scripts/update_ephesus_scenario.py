"""
YENİ SİSTEM: Efes Antik Kenti Macerası Scenario Update
======================================================
ESKİ sistem TAMAMEN SİLİNDİ - SIFIRDAN yazıldı!

Ocean/Dinosaur/Galata/Çatalhöyük standardına uygun:
- Modular prompt (500 char limit)
- Story blueprint (Antik Kent Keşfi + Tarih İhtişamı Dopamini)
- Educational focus (3000+ yıllık Roma-Yunan uygarlığı!)
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

EPHESUS_COVER_PROMPT = """Ephesus ancient city scene: {scene_description}.
Child in foreground, magnificent Ephesus ruins in background.
Celsus Library facade (iconic columns and statues), marble street visible.
3000-year-old Greco-Roman archaeological site.
Turkish Aegean landscape, ancient city atmosphere.
Wide shot: child 30%, ancient ruins 70%.
Epic historical scale, educational atmosphere.
UNESCO World Heritage site."""

EPHESUS_PAGE_PROMPT = """Ephesus ancient city scene: {scene_description}.
Elements: [Celsus Library: grand facade, columns, statues / Theater: massive 25,000-seat amphitheater / Marble street: Curetes Street, columns / Terrace houses: Roman mosaics, frescoes / Temple ruins: Artemis Temple remains / Agora: ancient marketplace].
Ancient colors: white marble, weathered stone.
Grand, majestic, educational atmosphere.
Greco-Roman civilization glory."""

# ============================================================================
# STORY BLUEPRINT (Antik Kent Keşfi + Tarih İhtişamı Dopamini)
# ============================================================================

EPHESUS_STORY_PROMPT_TR = """
# ANTİK KENT KEŞFİ DOPAMİN YÖNETİMİ - EFES ANTİK KENTİ MACERASI

## TEMEL YAPI: 7 BÖLÜM, 22 SAYFA

Bu antik kent keşif hikayesi, çocuğa **tarih**, **bilim**, **sanat** ve **uygarlık** değerlerini öğretir.

🏛️ **EFES**: Antik Çağ'ın en önemli kentlerinden (3000+ yıl!), UNESCO Dünya Mirası!

---

### BÖLÜM 1 - GİRİŞ: EFES'E VARIŞ (1-4)
- {child_name}, İzmir'in Selçuk ilçesinde, Efes Antik Kenti'ne varıyor
- İlk bakış: Mermer sütunlar, antik yollar, tarihin ihtişamı
- Heyecan: "3000 yıl önce burada insanlar yaşamış!"
- **Değer**: Tarih, merak, saygı

**Sayfa içeriği**:
- S1: Efes'e varış, antik kent girişi
- S2: Mermer sütunları görme, ilk hayranlık
- S3: Antik yollar, "Roma döneminden kalma!"
- S4: "3000 yıl önce!" hayranlığı ✓ **İLK HAYRANLIK**

---

### BÖLÜM 2 - CELSUS KÜTÜPHANESİ: BİLİM MERKEZİ (5-9)
**[BİLİM KEŞFİ DÖNGÜSÜ #1]**
- **Muhteşem Cephe**: İki katlı, heybetli sütunlar, heykeller
- **12.000 Kitap**: Antik Çağ'ın en büyük kütüphanelerinden!
- **Mimari**: İyonik ve Korint sütunları, mükemmel oran
- **Bilim Merkezi**: Bilim insanları, filozoflar burada buluşurmuş

**EPİK AN #1**: 12.000 kitaplık dev kütüphane - antik bilim merkezi! ✓ **BİLİM ZİRVESİ #1**

**Sayfa içeriği**:
- S5: Celsus Kütüphanesi'ni görme, "Ne büyük!"
- S6: İki katlı cephe, heybetli sütunlar
- S7: Heykeller, antik sanat
- S8: "12.000 kitap varmış!" ✓ **BİLİM KEŞİF ZİRVESİ**
- S9: Antik bilim merkezi, filozoflar

---

### BÖLÜM 3 - BÜYÜK TİYATRO: 25.000 KİŞİLİK DEV (10-14)
**[MİMARİ HAYRANLIK DÖNGÜSÜ #2]**
- **Dev Tiyatro**: 25.000 kişi kapasiteli! (Antik Çağ'ın en büyüklerinden)
- **Akustik Mucize**: Sahneden en üst sıraya ses ulaşıyor!
- **Basamaklar**: 66 sıra, dağın yamacına oyulmuş
- **Tiyatro Kültürü**: Drama, müzik, halk toplantıları

**EPİK AN #2**: 25.000 kişilik dev tiyatro - mimari mucize! ✓ **MİMARİ ZİRVESİ #2**

**Sayfa içeriği**:
- S10: Büyük Tiyatro'yu görme, "Devasa!"
- S11: 66 sıra basamak, dağa oyulmuş
- S12: "25.000 kişi! İnanılmaz!" ✓ **MİMARİ HAYRANLIK ZİRVESİ**
- S13: Akustik mucize, sahne
- S14: Antik tiyatro kültürü, drama sanatı

---

### BÖLÜM 4 - MERMER SOKAKLAR: CURETES CADDESİ (15-18)
**[İHTİŞAM KEŞFİ DÖNGÜSÜ #3]**
- **Curetes Caddesi**: Ana cadde, mermerden döşenmiş
- **Sütunlar**: Yüksek sütunlar caddeyi süslüyor
- **Heykeller**: Tanrı ve tanrıça heykelleri
- **Mozaikler**: Yol kenarında eski mozaikler

**EPİK AN #3**: Sütunlarla süslü mermer cadde - Roma ihtişamı! ✓ **İHTİŞAM ZİRVESİ #3**

**Sayfa içeriği**:
- S15: Curetes Caddesi'ne girme
- S16: Yüksek sütunlar, "Hala ayakta!" ✓ **İHTİŞAM KEŞFİ ZİRVESİ**
- S17: Mermer yollar, antik taşlar
- S18: Heykeller ve mozaikler

---

### BÖLÜM 5 - ROMA YAŞAMI: TERAS EVLER VE MOZAİKLER (19-20)
**[SANAT DÖNGÜSÜ #4]**
- **Teras Evler**: Zengin Romalıların evleri
- **Mozaikler**: Renkli taş mozaikler, mitolojik sahneler
- **Freskler**: Duvar resimleri, 2000 yıllık!
- **Lüks Yaşam**: Roma'nın zengin yaşamı

**EPİK AN #4**: 2000 yıllık mozaikler - Roma sanatı! ✓ **SANAT ZİRVESİ #4**

**Sayfa içeriği**:
- S19: Teras evlere girme, mozaikler
- S20: "El emeği, 2000 yıllık!" ✓ **SANAT DORUĞU**

---

### BÖLÜM 6 - FİNAL: TARİHİN İHTİŞAMI VE UYGARLIK MİRASI (21-22)
**[TARİH DORUĞU - FİNAL]**
- **Artemis Tapınağı**: Dünya'nın 7 Harikasından biri (kalıntıları)
- **Uygarlık**: Yunan, Roma, Bizans medeniyetleri
- **UNESCO**: Dünya Mirası koruma
- **Mesaj**: "Büyük uygarlıklar böyle yaşamış!"

**EPİK AN #5**: Tarihin ihtişamı, uygarlık mirası! ✓ **TARİH DORUĞU**

**Sayfa içeriği**:
- S21: Artemis Tapınağı kalıntıları, 7 Harika
- S22: Uygarlık mirası, "Tarih yaşıyor!"

---

## DOPAMIN ZİRVELERİ:
1. **Sayfa 4**: 3000 yıl önce hayranlığı (İLK HAYRANLIK)
2. **Sayfa 8**: Celsus Kütüphanesi - 12.000 kitap (BİLİM ZİRVESİ)
3. **Sayfa 12**: Büyük Tiyatro - 25.000 kişi (MİMARİ ZİRVESİ)
4. **Sayfa 16**: Curetes Caddesi sütunları (İHTİŞAM ZİRVESİ)
5. **Sayfa 20**: Mozaikler ve freskler (SANAT ZİRVESİ)
6. **Sayfa 22**: Artemis Tapınağı - 7 Harika (TARİH DORUĞU)

---

## DEĞERLER:
- **TARİH**: 3000+ yıllık miras, Yunan-Roma-Bizans uygarlığı
- **BİLİM**: Celsus Kütüphanesi, 12.000 kitap, bilim merkezi
- **SANAT**: Tiyatro, mozaikler, freskler, heykeller, mimari
- **UYGARLIK**: Antik Çağ'ın en gelişmiş ve önemli kenti

---

## EĞİTİM ODAKLARI:
- **Yunan-Roma Dönemi**: MÖ 10. yüzyıl - MS 15. yüzyıl
- **Celsus Kütüphanesi**: Antik dünyanın 3. büyük kütüphanesi (12.000 kitap)
- **Büyük Tiyatro**: 25.000 kişi kapasiteli, akustik mucize
- **Artemis Tapınağı**: Dünya'nın 7 Harikasından biri
- **UNESCO**: Dünya Mirası koruma bilinci

---

## CUSTOM INPUTS:
- {favorite_monument}: Çocuğun en sevdiği anıt (örn: Celsus Kütüphanesi, Büyük Tiyatro, Mermer Sokaklar, Mozaikler)
- Bu öğe sayfa 15-17 arasında vurgulanacak

---

## NOT:
Her sayfa {scene_description} ile dinamik olarak hikayeye entegre edilir.
Çocuk her sayfada TARİH ve UYGARLIK keşfeder, 3000 yıllık Roma-Yunan ihtişamını yaşar!
Eğitici, ihtişamlı, bilimsel!
"""

# ============================================================================
# OUTFIT DEFINITIONS
# ============================================================================

OUTFIT_GIRL = """Casual ancient site visit outfit for Aegean sun.
Comfortable t-shirt or casual top, practical pants or shorts.
Wide-brimmed sun hat or baseball cap for strong Aegean sun protection.
Comfortable walking shoes or sneakers (marble paths!).
Small backpack with water bottle and sunscreen.
Age-appropriate, practical for outdoor archaeological site exploration.
Light colors recommended for hot weather."""

OUTFIT_BOY = """Casual ancient site visit outfit for Aegean sun.
Comfortable t-shirt, practical shorts or pants.
Baseball cap or sun hat for strong Aegean sun protection.
Comfortable walking shoes or sneakers (marble paths!).
Small backpack with water bottle and sunscreen.
Age-appropriate, practical for outdoor archaeological site exploration.
Light colors recommended for hot weather."""

# ============================================================================
# CULTURAL ELEMENTS
# ============================================================================

EPHESUS_CULTURAL_ELEMENTS = {
    "location": "Izmir, Turkey (Selçuk district)",
    "historic_site": "Ephesus Ancient City, 3000+ years old (10th century BC - 15th century AD)",
    "unesco": "UNESCO World Heritage Site",
    "civilizations": ["Ancient Greek", "Roman Empire", "Byzantine"],
    "significance": "One of the most important cities of the ancient world",
    "major_monuments": [
        "Celsus Library (12,000 scrolls, 3rd largest in ancient world)",
        "Great Theater (25,000 capacity, largest in Asia Minor)",
        "Curetes Street (marble colonnaded street)",
        "Terrace Houses (Roman luxury homes with mosaics)",
        "Temple of Artemis ruins (one of Seven Wonders of Ancient World)",
        "Agora (ancient marketplace)"
    ],
    "architecture": [
        "Greco-Roman temples and theaters",
        "Marble streets and columns",
        "Two-story library facade",
        "Amphitheater carved into hillside",
        "Mosaic floors and frescoes"
    ],
    "cultural_aspects": [
        "Theater and drama culture",
        "Library and knowledge center",
        "Roman bath culture",
        "Marketplace and commerce",
        "Religious temples"
    ],
    "atmosphere": "Grand, majestic, educational, ancient civilization glory",
    "educational_focus": [
        "Greco-Roman civilization",
        "Ancient library system (12,000 scrolls!)",
        "Theater acoustics and architecture",
        "Roman mosaic art",
        "Seven Wonders of Ancient World (Artemis Temple)",
        "UNESCO preservation"
    ],
    "values": ["History appreciation", "Science and knowledge", "Art and architecture", "Civilization awareness"],
    "unique_features": [
        "Celsus Library facade (iconic ancient architecture)",
        "25,000-seat theater with perfect acoustics",
        "Marble streets still visible after 2000 years",
        "Connection to Seven Wonders (Artemis Temple)"
    ]
}

# ============================================================================
# CUSTOM INPUTS
# ============================================================================

EPHESUS_CUSTOM_INPUTS = {
    "favorite_monument": {
        "type": "select",
        "label_tr": "En sevdiğin anıt hangisi?",
        "label_en": "What's your favorite monument?",
        "options": [
            {"value": "celsus_library", "label_tr": "Celsus Kütüphanesi (12.000 kitap!)", "label_en": "Celsus Library (12,000 scrolls!)"},
            {"value": "great_theater", "label_tr": "Büyük Tiyatro (25.000 kişi!)", "label_en": "Great Theater (25,000 seats!)"},
            {"value": "marble_street", "label_tr": "Mermer Sokaklar", "label_en": "Marble Streets"},
            {"value": "mosaics", "label_tr": "Roma Mozaikleri", "label_en": "Roman Mosaics"},
            {"value": "artemis_temple", "label_tr": "Artemis Tapınağı (7 Harika!)", "label_en": "Artemis Temple (7 Wonders!)"}
        ],
        "default": "celsus_library",
        "usage": "Emphasized in pages 15-17 (discovery peak)"
    }
}

# ============================================================================
# DATABASE UPDATE FUNCTION
# ============================================================================

async def update_ephesus_scenario():
    """EFES ANTİK KENTİ senaryosunu YENİ SİSTEM ile günceller."""
    
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL environment variable not set")
    
    engine = create_async_engine(db_url, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Find Ephesus scenario
        result = await session.execute(
            select(Scenario).where(
                (Scenario.theme_key == "ephesus_ancient_city") |
                (Scenario.name.ilike("%Efes%")) |
                (Scenario.name.ilike("%Ephesus%"))
            )
        )
        scenario = result.scalar_one_or_none()
        
        if not scenario:
            print("❌ Efes scenario not found!")
            return
        
        print(f"\n✅ Found scenario: {scenario.name} (ID: {scenario.id})")
        
        # Verify prompt lengths
        print(f"\n📏 PROMPT LENGTHS:")
        print(f"   Cover: {len(EPHESUS_COVER_PROMPT)} chars (max 500)")
        print(f"   Page: {len(EPHESUS_PAGE_PROMPT)} chars (max 500)")
        print(f"   Story: {len(EPHESUS_STORY_PROMPT_TR)} chars")
        
        if len(EPHESUS_COVER_PROMPT) > 500 or len(EPHESUS_PAGE_PROMPT) > 500:
            print("❌ HATA: Prompt 500 karakteri aşıyor!")
            return
        
        # Update scenario
        await session.execute(
            update(Scenario)
            .where(Scenario.id == scenario.id)
            .values(
                cover_prompt_template=EPHESUS_COVER_PROMPT,
                page_prompt_template=EPHESUS_PAGE_PROMPT,
                story_prompt_tr=EPHESUS_STORY_PROMPT_TR,
                outfit_girl=OUTFIT_GIRL,
                outfit_boy=OUTFIT_BOY,
                cultural_elements=EPHESUS_CULTURAL_ELEMENTS,
                custom_inputs_schema=EPHESUS_CUSTOM_INPUTS,
                description="3000 yıllık Roma-Yunan ihtişamına yolculuk! Celsus Kütüphanesi (12.000 kitap!), 25.000 kişilik Büyük Tiyatro, mermer sokaklar ve mozaiklerle Efes Antik Kenti'ni keşfet. UNESCO Dünya Mirası'nda antik uygarlık macerası!",
                marketing_badge="YENİ! Antik Kent Macerası",
                age_range="7-10",
                tagline="Roma ihtişamını keşfet!"
            )
        )
        
        await session.commit()
        
        print("\n✅ EFES ANTİK KENTİ scenario updated successfully!")
        print("   - Modular prompts: DONE")
        print("   - Story blueprint: DONE")
        print("   - Educational focus: DONE")
        print("   - Outfit (Aegean sun protection): DONE")
        print("   - Cultural elements: DONE")
        print("   - Custom inputs: DONE")

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    asyncio.run(update_ephesus_scenario())
