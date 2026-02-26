"""
YENİ SİSTEM: Kapadokya Macerası Scenario Update
===============================================
ESKİ sistem TAMAMEN SİLİNDİ - SIFIRDAN yazıldı!

Ocean/Galata/Göbeklitepe standardına uygun:
- Modular prompt (500 char limit)
- Story blueprint (Doğa Mucizesi + Balon Macerası Dopamini)
- Adventure focus (peri bacaları, balon, yeraltı şehri!)
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

CAPPADOCIA_COVER_PROMPT = """Cappadocia fairy chimneys scene: {scene_description}.
Child in foreground, iconic Cappadocia landscape in background.
Fairy chimney rock formations (volcanic tuff), hot air balloons in sky.
Unique geological wonder, Goreme valley visible.
Central Anatolia landscape, sunrise golden light.
Wide shot: child 25%, fairy chimneys and balloons 75%.
Magical, adventurous atmosphere.
UNESCO World Heritage site."""

CAPPADOCIA_PAGE_PROMPT = """Cappadocia scene: {scene_description}.
Elements: [Fairy chimneys: cone-shaped rock formations, volcanic tuff / Hot air balloons: colorful balloons in sky, sunrise flight / Underground city: multi-level caves, tunnels / Rock churches: ancient frescoes, carved interiors / Valleys: Goreme, Love Valley, rock formations / Village: stone houses in rocks].
Earth colors: ochre, beige, rose valley pink.
Magical, adventurous, geological wonder.
UNESCO site."""

# ============================================================================
# STORY BLUEPRINT (Doğa Mucizesi + Balon Macerası Dopamini)
# ============================================================================

CAPPADOCIA_STORY_PROMPT_TR = """
# DOĞA MUCİZESİ DOPAMİN YÖNETİMİ - KAPADOKYA MACERASI

## TEMEL YAPI: 7 BÖLÜM, 22 SAYFA

Bu doğa mucizesi keşif hikayesi, çocuğa **doğa**, **macera**, **tarih** ve **keşif** değerlerini öğretir.

🎈 **KAPADOKYA**: Dünyanın en benzersiz coğrafyası, peri bacaları, balon turu, UNESCO Dünya Mirası!

---

### BÖLÜM 1 - GİRİŞ: KAPADOKYA'YA VARIŞ (1-4)
- {child_name}, Nevşehir'de, Kapadokya'nın büyülü dünyasına varıyor
- İlk bakış: Peri bacaları, benzersiz kaya oluşumları
- Gökyüzünde yüzlerce renkli balon!
- Heyecan: "Burası masaldan mı çıkmış?"
- **Değer**: Doğa, merak, macera

**Sayfa içeriği**:
- S1: Kapadokya'ya varış, ilk bakış
- S2: Peri bacalarını görme, "Ne garip!"
- S3: Gökyüzünde balonlar, "Çok güzel!"
- S4: "Masaldan çıkmış gibi!" ✓ **İLK HAYRANLIK**

---

### BÖLÜM 2 - PERİ BACALARI: DOĞANIN HEYKELTRAŞLIĞI (5-9)
**[DOĞA KEŞFİ DÖNGÜSÜ #1]**
- **Volkanik Oluşum**: 60 milyon yıl önce volkan patlaması!
- **Erozyon**: Rüzgar ve yağmur milyonlarca yıl yontmuş
- **Koni Şekiller**: Mantarlı, külahlı, sivri peri bacaları
- **Jeoloji Mucizesi**: Doğa nasıl heykeltıraş olmuş!

**EPİK AN #1**: Doğanın 60 milyon yıllık heykeltıraşlığı! ✓ **DOĞA ZİRVESİ #1**

**Sayfa içeriği**:
- S5: Peri bacalarına yaklaşma
- S6: Farklı şekiller, "Mantar gibi!"
- S7: "60 milyon yıl önce volkan!" ✓ **DOĞA KEŞİF ZİRVESİ**
- S8: Erozyon, rüzgar ve yağmur yontmuş
- S9: Jeoloji mucizesi, doğa sanatı

---

### BÖLÜM 3 - BALON TURU: GÖKYÜZÜ MACERASI (10-14)
**[MACERA DÖNGÜSÜ #2]**
- **Gün Doğumu**: Sabahın erken saati, altın ışık
- **Balon Kalkışı**: Yavaşça göğe yükselme, heyecan!
- **Gökyüzü Manzarası**: Tepeden peri bacaları, vadiler
- **Yüzlerce Balon**: Renkli balonlar aynı anda uçuyor
- **Kuş Bakışı**: Kapadokya'nın tamamını görme

**EPİK AN #2**: Gökyüzünden Kapadokya - balon macerası! ✓ **MACERA ZİRVESİ #2**

**Sayfa içeriği**:
- S10: Balona binme, heyecan
- S11: Yavaşça yükselme, "Göğe çıkıyoruz!"
- S12: Gökyüzünden manzara ✓ **MACERA KEŞİF ZİRVESİ**
- S13: Yüzlerce renkli balon etrafta
- S14: Kuş bakışı Kapadokya, "İnanılmaz!"

---

### BÖLÜM 4 - YERALTI ŞEHRİ: DERİNKUYU KEŞFİ (15-18)
**[YERALTI KEŞFİ DÖNGÜSÜ #3]**
- **Derinkuyu Yeraltı Şehri**: 8-10 kat derinlik!
- **Tüneller**: Karanlık geçitler, dar yollar
- **Odalar**: Mutfak, depo, kilise, havalandırma
- **Tarih**: 2000 yıl önce, insanlar burada yaşamış!
- **Gizlenme**: Düşmandan korunmak için yapılmış

**EPİK AN #3**: 8 kat derinlikte yeraltı şehri - tarih altımızda! ✓ **KEŞİF ZİRVESİ #3**

**Sayfa içeriği**:
- S15: Yeraltı şehrine inme
- S16: "8 kat derinlik!" tüneller ✓ **YERALTI KEŞİF ZİRVESİ**
- S17: Odalar, mutfak, kilise, "Burada yaşamışlar!"
- S18: 2000 yıl önce, tarih altımızda

---

### BÖLÜM 5 - KAYA KİLİSELER: GÖREME AÇIK HAVA MÜZESİ (19-20)
**[TARİH SANAT DÖNGÜSÜ #4]**
- **Kayaya Oyulmuş Kiliseler**: 10-11. yüzyıl, Bizans dönemi
- **Freskler**: Duvarlarda 1000 yıllık resimler
- **Kaya Mimarisi**: Tüm kilise kayadan oyulmuş!
- **UNESCO**: Dünya Mirası koruma

**EPİK AN #4**: Kayaya oyulmuş kiliseler, 1000 yıllık freskler! ✓ **TARİH SANAT ZİRVESİ #4**

**Sayfa içeriği**:
- S19: Kaya kiliselere girme, "Kayaya oyulmuş!"
- S20: Freskler, 1000 yıllık sanat ✓ **TARİH SANAT DORUĞU**

---

### BÖLÜM 6 - FİNAL: KAPADOKYA'NIN BÜYÜSÜ (21-22)
**[BÜYÜ DORUĞU - FİNAL]**
- **Gün Batımı**: Pembe vadiler, altın ışık
- **Kapadokya Büyüsü**: Doğa, tarih, macera bir arada
- **UNESCO**: Dünya'nın hazinesi
- **Mesaj**: "Doğa ve insan birlikte mucize yaratmış!"

**EPİK AN #5**: Kapadokya'nın büyüsü - doğa ve tarih buluşması! ✓ **BÜYÜ DORUĞU**

**Sayfa içeriği**:
- S21: Gün batımı, pembe vadiler
- S22: "Doğa ve tarih mucizesi!"

---

## DOPAMIN ZİRVELERİ:
1. **Sayfa 4**: Masaldan çıkmış gibi (İLK HAYRANLIK)
2. **Sayfa 7**: Peri bacaları - 60 milyon yıl (DOĞA ZİRVESİ)
3. **Sayfa 12**: Balon turu - gökyüzü (MACERA ZİRVESİ)
4. **Sayfa 16**: Yeraltı şehri - 8 kat (KEŞİF ZİRVESİ)
5. **Sayfa 20**: Kaya kiliseler - 1000 yıl (TARİH SANAT ZİRVESİ)
6. **Sayfa 22**: Kapadokya büyüsü (BÜYÜ DORUĞU)

---

## DEĞERLER:
- **DOĞA**: Jeolojik mucize, volkanik oluşum, erozyon
- **MACERA**: Balon turu, yeraltı keşfi, cesaret
- **TARİH**: Yeraltı şehirleri, kaya kiliseleri, Bizans dönemi
- **KEŞİF**: Benzersiz coğrafya, doğa ve tarih öğrenme

---

## EĞİTİM ODAKLARI:
- **Jeoloji**: Volkanik oluşum (60 milyon yıl), erozyon
- **Yeraltı Şehirleri**: Derinkuyu (8-10 kat), 2000 yıl önce
- **Bizans Sanatı**: Kaya kiliseleri (10-11. yüzyıl), freskler
- **Sıcak Hava Balonu**: Gün doğumu turu, kuş bakışı
- **UNESCO**: Göreme Tarihi Milli Parkı (1985'te Dünya Mirası)

---

## CUSTOM INPUTS:
- {favorite_experience}: Çocuğun en sevdiği deneyim (örn: Balon Turu, Peri Bacaları, Yeraltı Şehri, Kaya Kiliseler)
- Bu öğe sayfa 15-17 arasında vurgulanacak

---

## NOT:
Her sayfa {scene_description} ile dinamik olarak hikayeye entegre edilir.
Çocuk her sayfada DOĞA ve MACERA keşfeder, Kapadokya'nın büyüsünü yaşar!
Heyecanlı, eğitici, büyülü!
"""

# ============================================================================
# OUTFIT DEFINITIONS
# ============================================================================

OUTFIT_GIRL = """Comfortable adventure outfit for Cappadocia outdoor activities.
T-shirt or long-sleeve shirt, comfortable pants or jeans.
Light jacket or windbreaker (mornings can be cool, especially for balloon ride!).
Comfortable sneakers or hiking shoes.
Sun hat or baseball cap for daytime sun.
Small backpack with water bottle.
Age-appropriate, practical for hot air balloon, underground exploration, and outdoor sites.
Layers recommended for temperature changes."""

OUTFIT_BOY = """Comfortable adventure outfit for Cappadocia outdoor activities.
T-shirt or long-sleeve shirt, comfortable pants or cargo pants.
Light jacket or windbreaker (mornings can be cool, especially for balloon ride!).
Comfortable sneakers or hiking shoes.
Baseball cap or sun hat for daytime sun.
Small backpack with water bottle.
Age-appropriate, practical for hot air balloon, underground exploration, and outdoor sites.
Layers recommended for temperature changes."""

# ============================================================================
# CULTURAL ELEMENTS
# ============================================================================

CAPPADOCIA_CULTURAL_ELEMENTS = {
    "location": "Cappadocia region (Nevşehir, Ürgüp, Göreme), Central Anatolia, Turkey",
    "unesco": "Göreme National Park and Rock Sites of Cappadocia - UNESCO World Heritage Site (1985)",
    "geological_wonder": "Unique fairy chimney rock formations formed over 60 million years",
    "natural_features": [
        "Fairy chimneys (peri bacaları) - cone-shaped volcanic rock formations",
        "Volcanic tuff from ancient eruptions",
        "Erosion by wind and rain over millions of years",
        "Rose Valley (pink-hued rocks)",
        "Love Valley (unique pillar formations)",
        "Göreme Valley (iconic landscape)"
    ],
    "hot_air_balloon": [
        "Sunrise hot air balloon rides (world-famous)",
        "Hundreds of balloons in sky simultaneously",
        "Bird's eye view of fairy chimneys and valleys",
        "Magical experience at dawn"
    ],
    "underground_cities": [
        "Derinkuyu Underground City (8-10 levels deep!)",
        "Kaymaklı Underground City",
        "Built 2000 years ago for protection",
        "Tunnels, rooms, kitchens, churches, ventilation shafts",
        "Multi-level cave complexes"
    ],
    "rock_churches": [
        "Göreme Open Air Museum",
        "Byzantine rock-carved churches (10th-11th century)",
        "1000-year-old frescoes on cave walls",
        "Churches entirely carved into rock"
    ],
    "atmosphere": "Magical, adventurous, geological wonder, unique landscape",
    "educational_focus": [
        "Volcanic geology (60 million years of formation)",
        "Erosion and natural sculpture",
        "Byzantine history and art",
        "Underground city engineering (2000 years ago)",
        "Hot air balloon science and adventure",
        "UNESCO World Heritage preservation"
    ],
    "values": ["Nature appreciation", "Adventure", "History", "Geological wonder"],
    "unique_features": [
        "Most famous hot air balloon destination in world",
        "Fairy chimneys found nowhere else like this",
        "Multi-level underground cities (unique engineering)",
        "Rock-carved Byzantine churches with ancient frescoes"
    ]
}

# ============================================================================
# CUSTOM INPUTS
# ============================================================================

CAPPADOCIA_CUSTOM_INPUTS = {
    "favorite_experience": {
        "type": "select",
        "label_tr": "En sevdiğin deneyim hangisi?",
        "label_en": "What's your favorite experience?",
        "options": [
            {"value": "hot_air_balloon", "label_tr": "Balon Turu (Gökyüzü Macerası!)", "label_en": "Hot Air Balloon (Sky Adventure!)"},
            {"value": "fairy_chimneys", "label_tr": "Peri Bacaları (Doğa Mucizesi!)", "label_en": "Fairy Chimneys (Nature Wonder!)"},
            {"value": "underground_city", "label_tr": "Yeraltı Şehri (8 kat derinlik!)", "label_en": "Underground City (8 levels!)"},
            {"value": "rock_churches", "label_tr": "Kaya Kiliseler (1000 yıllık freskler!)", "label_en": "Rock Churches (1000-year frescoes!)"},
            {"value": "valleys", "label_tr": "Pembe Vadiler", "label_en": "Rose Valley"}
        ],
        "default": "hot_air_balloon",
        "usage": "Emphasized in pages 15-17 (discovery peak)"
    }
}

# ============================================================================
# DATABASE UPDATE FUNCTION
# ============================================================================

async def update_cappadocia_scenario():
    """KAPADOKYA senaryosunu YENİ SİSTEM ile günceller."""
    
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL environment variable not set")
    
    engine = create_async_engine(db_url, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Find Cappadocia scenario
        result = await session.execute(
            select(Scenario).where(
                (Scenario.theme_key == "cappadocia_fairy_chimneys") |
                (Scenario.name.ilike("%Kapadokya%")) |
                (Scenario.name.ilike("%Cappadocia%"))
            )
        )
        scenario = result.scalar_one_or_none()
        
        if not scenario:
            print("❌ Kapadokya scenario not found!")
            return
        
        print(f"\n✅ Found scenario: {scenario.name} (ID: {scenario.id})")
        
        # Verify prompt lengths
        print(f"\n📏 PROMPT LENGTHS:")
        print(f"   Cover: {len(CAPPADOCIA_COVER_PROMPT)} chars (max 500)")
        print(f"   Page: {len(CAPPADOCIA_PAGE_PROMPT)} chars (max 500)")
        print(f"   Story: {len(CAPPADOCIA_STORY_PROMPT_TR)} chars")
        
        if len(CAPPADOCIA_COVER_PROMPT) > 500 or len(CAPPADOCIA_PAGE_PROMPT) > 500:
            print("❌ HATA: Prompt 500 karakteri aşıyor!")
            return
        
        # Update scenario
        await session.execute(
            update(Scenario)
            .where(Scenario.id == scenario.id)
            .values(
                cover_prompt_template=CAPPADOCIA_COVER_PROMPT,
                page_prompt_template=CAPPADOCIA_PAGE_PROMPT,
                story_prompt_tr=CAPPADOCIA_STORY_PROMPT_TR,
                outfit_girl=OUTFIT_GIRL,
                outfit_boy=OUTFIT_BOY,
                cultural_elements=CAPPADOCIA_CULTURAL_ELEMENTS,
                custom_inputs_schema=CAPPADOCIA_CUSTOM_INPUTS,
                description="Kapadokya'nın büyülü dünyasına yolculuk! Peri bacaları (60 milyon yıllık!), sıcak hava balonu turu, yeraltı şehri keşfi (8 kat derinlik!) ve kaya kiliselerdeki 1000 yıllık freskler. UNESCO Dünya Mirası'nda doğa mucizesi ve macera!",
                marketing_badge="YENİ! Balon Macerası",
                age_range="6-10",
                tagline="Kapadokya'nın büyüsünü keşfet!"
            )
        )
        
        await session.commit()
        
        print("\n✅ KAPADOKYA scenario updated successfully!")
        print("   - Modular prompts: DONE")
        print("   - Story blueprint: DONE")
        print("   - Adventure focus: DONE")
        print("   - Outfit (layers for balloon): DONE")
        print("   - Cultural elements: DONE")
        print("   - Custom inputs: DONE")

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    asyncio.run(update_cappadocia_scenario())
