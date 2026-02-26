"""
YENİ SİSTEM: Göbeklitepe Macerası Scenario Update
=================================================
ESKİ sistem TAMAMEN SİLİNDİ - SIFIRDAN yazıldı!

Ocean/Çatalhöyük/Efes standardına uygun:
- Modular prompt (500 char limit)
- Story blueprint (Prehistorik Keşif + Zaman Sıfır Noktası Dopamini)
- Educational focus (12.000 yıllık - dünyanın EN ESKİ tapınağı!)
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

GOBEKLI_COVER_PROMPT = """Gobekli Tepe archaeological site scene: {scene_description}.
Child in foreground, ancient Gobekli Tepe megalithic temple in background.
12,000-year-old stone pillars with T-shaped monoliths.
World's oldest temple complex, pre-dating Stonehenge by 6000 years.
Sanliurfa landscape, archaeological excavation site.
Wide shot: child 30%, ancient megaliths 70%.
Epic prehistoric scale, time-travel atmosphere.
UNESCO World Heritage site."""

GOBEKLI_PAGE_PROMPT = """Gobekli Tepe scene: {scene_description}.
Elements: [T-pillars: massive T-shaped stone monoliths (5m tall) / Animal carvings: lions, foxes, snakes, birds relief / Stone circles: circular temple structures / Excavation: archaeological layers, 12,000 years / Megaliths: limestone pillars, prehistoric engineering].
Ancient colors: weathered stone, earth tones.
Mysterious, prehistoric, scientific discovery atmosphere.
Pre-agricultural civilization wonder."""

# ============================================================================
# STORY BLUEPRINT (Prehistorik Keşif + Zaman Sıfır Noktası Dopamini)
# ============================================================================

GOBEKLI_STORY_PROMPT_TR = """
# PREHİSTORİK KEŞİF DOPAMİN YÖNETİMİ - GÖBEKLİTEPE MACERASI

## TEMEL YAPI: 7 BÖLÜM, 22 SAYFA

Bu prehistorik keşif hikayesi, çocuğa **bilim**, **tarih**, **merak** ve **mucize** değerlerini öğretir.

🌍 **GÖBEKLİTEPE**: Dünyanın EN ESKİ tapınağı (12.000 yıl!), Çatalhöyük'ten 3000 yıl DAHA ESKİ!

---

### BÖLÜM 1 - GİRİŞ: GÖBEKLİTEPE'YE VARIŞ (1-4)
- {child_name}, Şanlıurfa'da, Göbeklitepe arkeolojik alanına varıyor
- İlk bakış: Dev taş sütunlar, T-şekilli megaliths
- Heyecan: "Dünyanın en eski yapısı!"
- **Değer**: Bilim, merak, hayret

**Sayfa içeriği**:
- S1: Göbeklitepe'ye varış, Şanlıurfa ovası
- S2: İlk bakış, dev taş sütunlar
- S3: T-şekilli monolitler, "Ne büyük!"
- S4: "Dünyanın EN ESKİ tapınağı!" ✓ **İLK HAYRANLIK**

---

### BÖLÜM 2 - ZAMAN SIFIR NOKTASI: 12.000 YIL ÖNCESİNE (5-9)
**[ZAMAN KEŞFİ DÖNGÜSÜ #1]**
- **12.000 Yıl Önce**: MÖ 10.000 - Taş Devri!
- **Her Şeyden ÖNCE**: Yazıdan, tekerlek, metalden, tarımdan ÖNCE!
- **Çatalhöyük'ten 3000 Yıl Daha Eski**: 9000 yıllık Çatalhöyük bile "genç"!
- **Stonehenge'den 6000 Yıl Önce**: Piramitlerden 7000 yıl önce!

**EPİK AN #1**: İnsanlık tarihinin sıfır noktası - her şey buradan başladı! ✓ **ZAMAN ZİRVESİ #1**

**Sayfa içeriği**:
- S5: Hayal ile 12.000 yıl öncesine
- S6: "Yazıdan ÖNCE!" şaşkınlığı
- S7: "Çatalhöyük'ten bile eski!" ✓ **ZAMAN KEŞFİ ZİRVESİ**
- S8: Stonehenge karşılaştırması, 6000 yıl önce
- S9: "Her şey buradan başladı!"

---

### BÖLÜM 3 - T-SÜTUNLAR: DEV MEGALİTLER (10-14)
**[MUCİZE DÖNGÜSÜ #2]**
- **T-Şekilli Sütunlar**: 5 metre yüksek, 10 ton ağır!
- **Nasıl Yapılmış?**: Metal alet YOK, sadece taş aletler!
- **Mühendislik**: Taşları taşıma, dikme, yerleştirme mucizesi
- **Dairesel Düzen**: Tapınak çemberleri, kutsal alan

**EPİK AN #2**: 10 tonluk taşları metal olmadan dikme - prehistorik mucize! ✓ **MUCİZE ZİRVESİ #2**

**Sayfa içeriği**:
- S10: T-sütunları keşfetme, "5 metre!"
- S11: "10 ton! Nasıl kaldırmışlar?"
- S12: "Metal yok, sadece taş aletler!" ✓ **MUCİZE KEŞİF ZİRVESİ**
- S13: Dairesel tapınak düzeni
- S14: Mühendislik harikası

---

### BÖLÜM 4 - HAYVAN KABARTMALARI: 12.000 YILLIK SANAT (15-18)
**[SANAT KEŞFİ DÖNGÜSÜ #3]**
- **Hayvan Kabartmaları**: Aslan, tilki, yılan, kuş, akrep
- **3D Kabartma**: Taşa oyulmuş, derinlikli sanat
- **Sembolizm**: Hayvanlar kutsal semboller
- **El Emeği**: 12.000 yıl önce, taş aletlerle yapılmış!

**EPİK AN #3**: 12.000 yıllık taş sanatı - ilk sanatçılar! ✓ **SANAT ZİRVESİ #3**

**Sayfa içeriği**:
- S15: Hayvan kabartmalarını görme
- S16: Aslan, tilki, yılan detayları ✓ **SANAT KEŞFİ ZİRVESİ**
- S17: "El emeği, 12.000 yıl önce!"
- S18: Kutsal semboller, hayvan topluluğu

---

### BÖLÜM 5 - AVCI-TOPLAYICILAR: TARIMDAN ÖNCE TAPINAK! (19-20)
**[PARADOKS DÖNGÜSÜ #4]**
- **Avcı-Toplayıcılar**: Henüz yerleşik değiller, göçebeler!
- **Tarım YOK**: Buğday ekimi henüz başlamamış!
- **Ama Tapınak Var!**: Nasıl organize olmuşlar?
- **Devrim**: Tapınak için bir araya gelmişler, sonra yerleşik yaşam başlamış!

**EPİK AN #4**: Tarımdan ÖNCE tapınak - tarihin en büyük paradoksu! ✓ **PARADOKS ZİRVESİ #4**

**Sayfa içeriği**:
- S19: Avcı-toplayıcılar, "Tarım bile yok!"
- S20: "Tapınak için toplanmışlar!" ✓ **PARADOKS DORUĞU**

---

### BÖLÜM 6 - FİNAL: İNSANLIK TARİHİNİN BAŞLANGICI (21-22)
**[TARİH DORUĞU - FİNAL]**
- **Arkeolojik Mucize**: Klaus Schmidt'in keşfi (1994)
- **UNESCO**: Dünya Mirası, insanlığın hazinesi
- **Tarih Yeniden Yazıldı**: Göbeklitepe öncesi ve sonrası!
- **Mesaj**: "İnsanlık buradan başladı - düşünce, inanç, birliktelik!"

**EPİK AN #5**: İnsanlık tarihinin başlangıç noktası! ✓ **TARİH DORUĞU**

**Sayfa içeriği**:
- S21: Klaus Schmidt'in keşfi, arkeoloji mucizesi
- S22: "İnsanlık buradan başladı!"

---

## DOPAMIN ZİRVELERİ:
1. **Sayfa 4**: Dünyanın en eski yapısı (İLK HAYRANLIK)
2. **Sayfa 7**: 12.000 yıl - her şeyden önce (ZAMAN ZİRVESİ)
3. **Sayfa 12**: 10 ton taş, metal yok (MUCİZE ZİRVESİ)
4. **Sayfa 16**: 12.000 yıllık kabartmalar (SANAT ZİRVESİ)
5. **Sayfa 20**: Tarımdan önce tapınak (PARADOKS ZİRVESİ)
6. **Sayfa 22**: İnsanlık başlangıcı (TARİH DORUĞU)

---

## DEĞERLER:
- **BİLİM**: Arkeoloji, Klaus Schmidt'in keşfi, bilimsel yöntem
- **TARİH**: 12.000 yıllık miras, insanlık tarihinin başlangıcı
- **MERAK**: Nasıl yapılmış? Neden? Soru sorma
- **HAYRET**: İnsanlık mucizesi, metal olmadan dev yapı!

---

## EĞİTİM ODAKLARI:
- **Taş Devri**: MÖ 10.000 (Neolitik öncesi!)
- **Avcı-Toplayıcılar**: Göçebe yaşam, henüz tarım yok
- **Megalith Mühendisliği**: 5m yüksek, 10 ton taşlar
- **Tarih Karşılaştırması**: Çatalhöyük (9000), Stonehenge (4500), Piramitler (4500)
- **Klaus Schmidt**: 1994'te keşfeden Alman arkeolog
- **UNESCO**: 2018'de Dünya Mirası listesi

---

## CUSTOM INPUTS:
- {favorite_element}: Çocuğun en sevdiği unsur (örn: T-Sütunlar, Hayvan Kabartmaları, Zaman Yolculuğu, Avcı-Toplayıcılar)
- Bu öğe sayfa 15-17 arasında vurgulanacak

---

## NOT:
Her sayfa {scene_description} ile dinamik olarak hikayeye entegre edilir.
Çocuk her sayfada TARİH ve BİLİM keşfeder, 12.000 yıllık zaman sıfır noktasına gider!
Mucize, hayret, bilim!
"""

# ============================================================================
# OUTFIT DEFINITIONS
# ============================================================================

OUTFIT_GIRL = """Casual archaeological site visit outfit for Sanliurfa sun.
Comfortable t-shirt or casual top, practical pants or jeans.
Wide-brimmed sun hat or baseball cap for strong sun protection.
Comfortable sneakers or walking shoes.
Small backpack with water bottle and notebook (archaeologist style!).
Age-appropriate, practical for outdoor prehistoric site exploration.
Light colors recommended for hot weather."""

OUTFIT_BOY = """Casual archaeological site visit outfit for Sanliurfa sun.
Comfortable t-shirt, practical pants or cargo pants.
Baseball cap or sun hat for strong sun protection.
Comfortable sneakers or walking shoes.
Small backpack with water bottle and notebook (archaeologist style!).
Age-appropriate, practical for outdoor prehistoric site exploration.
Light colors recommended for hot weather."""

# ============================================================================
# CULTURAL ELEMENTS
# ============================================================================

GOBEKLI_CULTURAL_ELEMENTS = {
    "location": "Sanliurfa, Turkey",
    "historic_site": "Göbeklitepe (Gobekli Tepe), 12,000 years old (10,000-8,000 BC)",
    "unesco": "UNESCO World Heritage Site (2018)",
    "significance": "World's oldest temple complex, predates agriculture",
    "discovery": "Discovered by Klaus Schmidt in 1994, revolutionized archaeology",
    "period": "Pre-Pottery Neolithic A (Stone Age)",
    "unique_features": [
        "12,000 years old (oldest known temple!)",
        "Built BEFORE agriculture, writing, wheel, metal tools",
        "3,000 years OLDER than Çatalhöyük (9,000 years)",
        "6,000 years OLDER than Stonehenge",
        "7,000 years OLDER than Egyptian Pyramids",
        "Hunter-gatherers built it (not settled farmers!)"
    ],
    "architecture": [
        "T-shaped stone pillars (5m tall, 10 tons each)",
        "Circular temple structures",
        "Megalithic limestone monoliths",
        "Stone circles arranged in layers",
        "Built with stone tools only (no metal!)"
    ],
    "art_elements": [
        "3D animal relief carvings",
        "Lions, foxes, snakes, birds, scorpions",
        "Sacred animal symbolism",
        "Carved with stone tools 12,000 years ago"
    ],
    "atmosphere": "Mysterious, prehistoric, scientific wonder, time zero point",
    "educational_focus": [
        "Pre-agricultural civilization",
        "Hunter-gatherer society building temples",
        "Megalithic engineering without metal tools",
        "Oldest known religious/ceremonial site",
        "How history was rewritten by this discovery",
        "Klaus Schmidt archaeological discovery (1994)"
    ],
    "values": ["Science", "Wonder", "Curiosity", "Human achievement miracle"],
    "historical_comparisons": {
        "Göbeklitepe": "12,000 years (BC 10,000)",
        "Çatalhöyük": "9,000 years (BC 7,100)",
        "Stonehenge": "4,500 years (BC 3,000)",
        "Egyptian Pyramids": "4,500 years (BC 2,600)",
        "Writing invention": "5,500 years (BC 3,500)"
    }
}

# ============================================================================
# CUSTOM INPUTS
# ============================================================================

GOBEKLI_CUSTOM_INPUTS = {
    "favorite_element": {
        "type": "select",
        "label_tr": "En sevdiğin unsur hangisi?",
        "label_en": "What's your favorite element?",
        "options": [
            {"value": "t_pillars", "label_tr": "T-Sütunlar (5m yüksek!)", "label_en": "T-Pillars (5m tall!)"},
            {"value": "animal_carvings", "label_tr": "Hayvan Kabartmaları (12.000 yıllık!)", "label_en": "Animal Carvings (12,000 years!)"},
            {"value": "time_travel", "label_tr": "12.000 Yıl Önce Zaman Yolculuğu", "label_en": "Time Travel 12,000 Years"},
            {"value": "hunter_gatherers", "label_tr": "Avcı-Toplayıcıların Mucizesi", "label_en": "Hunter-Gatherers Miracle"},
            {"value": "oldest_temple", "label_tr": "Dünyanın En Eski Tapınağı", "label_en": "World's Oldest Temple"}
        ],
        "default": "t_pillars",
        "usage": "Emphasized in pages 15-17 (discovery peak)"
    }
}

# ============================================================================
# DATABASE UPDATE FUNCTION
# ============================================================================

async def update_gobekli_scenario():
    """GÖBEKLİTEPE senaryosunu YENİ SİSTEM ile günceller."""
    
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL environment variable not set")
    
    engine = create_async_engine(db_url, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Find Gobekli Tepe scenario
        result = await session.execute(
            select(Scenario).where(
                (Scenario.theme_key == "gobekli_tepe_temple") |
                (Scenario.name.ilike("%Göbeklitepe%")) |
                (Scenario.name.ilike("%Gobekli%"))
            )
        )
        scenario = result.scalar_one_or_none()
        
        if not scenario:
            print("❌ Göbeklitepe scenario not found!")
            return
        
        print(f"\n✅ Found scenario: {scenario.name} (ID: {scenario.id})")
        
        # Verify prompt lengths
        print(f"\n📏 PROMPT LENGTHS:")
        print(f"   Cover: {len(GOBEKLI_COVER_PROMPT)} chars (max 500)")
        print(f"   Page: {len(GOBEKLI_PAGE_PROMPT)} chars (max 500)")
        print(f"   Story: {len(GOBEKLI_STORY_PROMPT_TR)} chars")
        
        if len(GOBEKLI_COVER_PROMPT) > 500 or len(GOBEKLI_PAGE_PROMPT) > 500:
            print("❌ HATA: Prompt 500 karakteri aşıyor!")
            return
        
        # Update scenario
        await session.execute(
            update(Scenario)
            .where(Scenario.id == scenario.id)
            .values(
                cover_prompt_template=GOBEKLI_COVER_PROMPT,
                page_prompt_template=GOBEKLI_PAGE_PROMPT,
                story_prompt_tr=GOBEKLI_STORY_PROMPT_TR,
                outfit_girl=OUTFIT_GIRL,
                outfit_boy=OUTFIT_BOY,
                cultural_elements=GOBEKLI_CULTURAL_ELEMENTS,
                custom_inputs_schema=GOBEKLI_CUSTOM_INPUTS,
                description="12.000 yıl öncesine yolculuk! Dünyanın EN ESKİ tapınağı Göbeklitepe'yi keşfet. 5m yüksek T-sütunlar, hayvan kabartmaları ve avcı-toplayıcıların mucizesi. Çatalhöyük'ten 3000 yıl, Stonehenge'den 6000 yıl daha eski! UNESCO Dünya Mirası'nda prehistorik keşif!",
                marketing_badge="YENİ! Zaman Sıfır Noktası",
                age_range="8-10",
                tagline="12.000 yıllık zaman mucizesi!"
            )
        )
        
        await session.commit()
        
        print("\n✅ GÖBEKLİTEPE scenario updated successfully!")
        print("   - Modular prompts: DONE")
        print("   - Story blueprint: DONE")
        print("   - Educational focus: DONE")
        print("   - Outfit (Sanliurfa sun): DONE")
        print("   - Cultural elements: DONE")
        print("   - Custom inputs: DONE")

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    asyncio.run(update_gobekli_scenario())
