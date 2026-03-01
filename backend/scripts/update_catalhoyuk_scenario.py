"""
Çatalhöyük Macerası Scenario — Birleştirilmiş Güncelleme
=========================================================
update_ ve create_ script'lerinin en iyi parçaları birleştirildi:
- Modular prompt (500 char limit) — update_ standardı
- Hikaye: Macera odaklı (gezi rehberi DEĞİL) — create_ kalitesi
- Outfit: update_all_outfits.py standardı (EXACTLY lock phrase)
- custom_inputs_schema: list formatı (frontend uyumlu)
- theme_key: "catalhoyuk" (sabit)
- İsim: "Çatalhöyük Macerası" (Neolitik Kenti kaldırıldı)
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.models import Scenario

# ============================================================================
# MODULAR PROMPT COMPONENTS (500 char limit!)
# ============================================================================

CATALHOYUK_COVER_PROMPT = (
    "An {child_age}-year-old {child_gender} named {child_name} "
    "with {hair_description}, wearing {clothing_description}. "
    "{scene_description}. "
    "Ancient 9000-year-old Catalhoyuk settlement in background. "
    "Mud-brick houses with rooftop ladder entrances, no doors. "
    "Archaeological excavation layers, Konya plain. "
    "Wide shot: child 30%, ancient site 70%. "
    "Educational, time-travel atmosphere."
)

CATALHOYUK_PAGE_PROMPT = (
    "An {child_age}-year-old {child_gender} named {child_name} "
    "with {hair_description}, wearing {clothing_description}. "
    "{scene_description}. "
    "Elements: [Houses: mud-brick, flat roofs, ladder entrances from rooftop / "
    "Wall art: ancient paintings (bulls, geometric) / Excavation: dig site, layers / "
    "Daily life: pottery, tools, hearths / Settlement: clustered, no streets]. "
    "Earthy colors: mud brown, ochre, terracotta."
)

# ============================================================================
# OUTFIT DEFINITIONS (update_all_outfits.py standardı)
# ============================================================================

OUTFIT_GIRL = (
    "terracotta rust-colored cotton t-shirt with small geometric pattern on chest, "
    "dark brown cotton cargo shorts, tan leather ankle boots, "
    "light brown canvas bucket hat, small leather crossbody satchel. "
    "EXACTLY the same outfit on every page — same terracotta shirt, same brown shorts, same leather boots."
)

OUTFIT_BOY = (
    "ochre yellow cotton t-shirt with small arrowhead emblem, "
    "dark olive green cotton shorts, tan leather ankle boots, "
    "brown canvas explorer hat, small leather hip pouch on belt. "
    "EXACTLY the same outfit on every page — same ochre shirt, same olive shorts, same leather boots."
)

# ============================================================================
# STORY BLUEPRINT (Macera odaklı — gezi rehberi DEĞİL)
# ============================================================================

CATALHOYUK_STORY_PROMPT_TR = """
# ÇATALHÖYÜK MACERASI — ARKEOLOJİ KEŞFİ

## TEMEL YAPI: 7 BÖLÜM, 22 SAYFA

Bu hikaye bir arkeoloji macerası. {child_name}, Çatalhöyük'te 9000 yıl öncesine
hayal yolculuğu yaparak insanlığın ilk şehir yaşamını keşfeder.

⚠️ ÖNEMLİ KURALLAR:
- Bu bir MACERA hikayesi, gezi rehberi DEĞİL
- Her bölümde çocuk AKTİF katılımcı olmalı (gözlemci değil)
- Endişe → Eylem → Başarı döngüsü her bölümde olmalı
- Yardımcı karakter: Bilge Kedi (arkeolog kedisi, kazı alanında yaşıyor)
- Çocuk TEK BAŞINA macerada (aile yok)
- Korku/şiddet/gore YOK, eğitici ve heyecanlı

---

### BÖLÜM 1 — GİRİŞ: GİZEMLİ HÖYÜK (Sayfa 1-4)
{child_name} Konya ovasında yürürken garip bir tepe görür — bu Çatalhöyük höyüğü!
Bir kedi (Bilge Kedi) kazı alanından çıkıp ona yaklaşır ve gizem dolu bakışlarla
höyüğe doğru yürür. Çocuk merakla peşinden gider.
- S1: Konya ovasında yürüyüş, uzakta garip bir tepe
- S2: Höyüğe yaklaşma, kazı alanı, "Bu ne?"
- S3: Bilge Kedi ile tanışma, kedi höyüğe doğru yürüyor
- S4: Kazı alanına giriş, "9000 yıl önce burada insanlar yaşamış!" ✓ İLK HAYRANLIK
**Değer**: Merak, keşif cesareti

---

### BÖLÜM 2 — ZAMAN YOLCULUĞU: 9000 YIL ÖNCESİ (Sayfa 5-8)
Bilge Kedi eski bir obsidyen aynaya dokunur ve her şey değişir — çocuk kendini
9000 yıl öncesinde bulur! Etrafta kerpiç evler, insanlar tarım yapıyor,
çocuklar oynuyor. Neolitik Çağ'ın canlı dünyası!
- S5: Obsidyen ayna, dokunuş, ışık patlaması
- S6: 9000 yıl öncesi! Canlı şehir, insanlar, hayvanlar
- S7: "Artık göçebe değiller, yerleşik yaşam başlamış!" ✓ ZAMAN ZİRVESİ
- S8: Neolitik insanlarla ilk temas, çocuklar oynuyor
**Değer**: Tarih bilinci, adaptasyon

---

### BÖLÜM 3 — KERPİÇ EVLER: DAMDAN GİRİŞ SIRRI (Sayfa 9-12)
Bilge Kedi çocuğu bir evin damına çıkarır. Kapı yok! Damdan merdiven ile
iniliyor — dünyanın en ilginç mimari çözümü! İçeride ocak, tahıl depoları,
duvar resimleri. Çocuk bir ev inşaatına yardım eder.
- S9: Evlerin damlarında yürüme, "Kapı nerede?"
- S10: Damdan merdiven ile iniş, "Akıllıca!"
- S11: İç mekan keşfi — ocak, tahıl, aletler
- S12: Kerpiç yapımına yardım, çamur ve saman karıştırma ✓ MİMARİ ZİRVESİ
**Değer**: Yaratıcılık, problem çözme

---

### BÖLÜM 4 — DUVAR RESİMLERİ: İNSANLIĞIN İLK SANATI (Sayfa 13-16)
Bir evin duvarında devasa boğa resmi! 9000 yıllık sanat eseri. Çocuk doğal
boyalarla (kırmızı toprak, kömür karası) kendi resmini yapmaya çalışır.
Geometrik desenler, el izleri, avcılık sahneleri — insanlığın ilk sanat galerisi!
- S13: Devasa boğa duvar resmi, "Bu 9000 yıllık!"
- S14: Doğal boyalar keşfi — kırmızı toprak, kömür
- S15: Çocuk kendi resmini yapıyor, el izi bırakıyor
- S16: Geometrik desenler, "İlk soyut sanat!" ✓ SANAT ZİRVESİ
**Değer**: Sanat, yaratıcılık, kültürel miras

---

### BÖLÜM 5 — İLK UYGARLIK: TARIM VE İŞBİRLİĞİ (Sayfa 17-19)
Çocuk tarlada buğday hasadına katılır. Obsidyen bıçaklarla kesim, el yapımı
çömleklere depolama. Herkes birlikte çalışıyor — ilk toplum kuralları!
Bir sorun çıkar: Tahıl deposuna su sızıyor. Çocuk çözüm önerir.
- S17: Buğday hasadı, obsidyen bıçak kullanımı
- S18: Çömlek yapımı, tahıl depolama
- S19: Su sızıntısı sorunu, çocuğun çözüm önerisi ✓ UYGARLIK ZİRVESİ
**Değer**: İşbirliği, sorumluluk, problem çözme

---

### BÖLÜM 6 — BÜYÜK KEŞİF: GİZLİ ODA (Sayfa 20-21)
Bilge Kedi çocuğu gizli bir odaya götürür. İçeride hiç görülmemiş duvar
resimleri, özel eşyalar, belki de bir tapınak! Bu keşif arkeolojinin gücünü
gösterir — geçmişin sırları sabırla ortaya çıkar.
- S20: Gizli oda keşfi, Bilge Kedi'nin rehberliği
- S21: Hiç görülmemiş duvar resimleri, "Muhteşem!" ✓ DORUK KEŞİF
**Değer**: Sabır, bilimsel merak

---

### BÖLÜM 7 — FİNAL: DÖNÜŞ VE GURUR (Sayfa 22)
Obsidyen ayna tekrar parlar, çocuk bugüne döner. Kazı alanında durup
9000 yıllık mirasa bakar. "Tarih bize kim olduğumuzu söyler."
Bilge Kedi yanında, ikisi birlikte gün batımını izler.
- S22: Bugüne dönüş, gurur ve şükran hissi ✓ TATMIN DORUĞU
**Değer**: Tarih bilinci, kültürel miras koruma

---

## DOPAMIN ZİRVELERİ:
1. S4: İlk hayranlık — 9000 yıl!
2. S7: Zaman yolculuğu — canlı Neolitik dünya
3. S12: Mimari keşif — damdan giriş ve kerpiç yapımı
4. S16: Sanat zirvesi — ilk duvar resimleri
5. S19: Uygarlık — işbirliği ve problem çözme
6. S21: Doruk keşif — gizli oda
7. S22: Tatmin — gurur ve dönüş

## DEĞERLER:
- Merak ve keşif cesareti
- Tarih bilinci ve kültürel miras
- Yaratıcılık ve problem çözme
- İşbirliği ve sorumluluk
- Bilimsel düşünme (arkeoloji)

## GÜVENLİK KURALLARI:
- Korku/şiddet/gore YOK
- Tehlikeli davranış teşviki YOK
- Çocuk güvenli ortamda keşif yapıyor
- Neolitik insanlar dostane ve yardımsever
"""

# ============================================================================
# CULTURAL ELEMENTS
# ============================================================================

CATALHOYUK_CULTURAL_ELEMENTS = {
    "location": "Konya, Turkey (Çumra district)",
    "historic_site": "Çatalhöyük, 9000 years old (7100-5700 BC)",
    "unesco": "UNESCO World Heritage Site",
    "period": "Neolithic Age (New Stone Age)",
    "significance": "One of the world's oldest cities, first urban settlement",
    "architecture": [
        "Mud-brick houses with flat roofs",
        "Rooftop entrances (no doors, ladder access!)",
        "Clustered houses (no streets between)",
        "Interior hearths and storage areas",
    ],
    "art_elements": [
        "Wall paintings (9000 years old!)",
        "Bull motifs and hunting scenes",
        "Geometric patterns (first abstract art)",
        "Natural pigments (red, black, white)",
    ],
    "daily_life": [
        "Agriculture (wheat, barley cultivation)",
        "Pottery making",
        "Obsidian tools and blades",
        "Community living and cooperation",
    ],
    "atmosphere": "Educational, archaeological wonder, time-travel feeling",
    "educational_focus": [
        "Neolithic Age and agricultural revolution",
        "First settled urban life",
        "Early civilization development",
        "Archaeology as a science",
        "UNESCO World Heritage preservation",
    ],
    "values": ["Curiosity", "History appreciation", "Creativity", "Cooperation"],
    "color_palette": "earthy brown, ochre, terracotta, mud, warm amber",
}

# ============================================================================
# CUSTOM INPUTS (list formatı — frontend uyumlu)
# ============================================================================

CATALHOYUK_CUSTOM_INPUTS = [
    {
        "key": "favorite_discovery",
        "label": "En Merak Ettiği Keşif",
        "type": "select",
        "options": ["Damdan Giriş Sırrı", "Duvar Resimleri", "İlk Tarım", "Kerpiç Ev Yapımı", "Gizli Oda"],
        "default": "Damdan Giriş Sırrı",
        "required": False,
        "help_text": "Hikayede çocuğun en çok heyecanlanacağı keşif",
    },
    {
        "key": "companion_name",
        "label": "Bilge Kedi'nin Adı",
        "type": "select",
        "options": ["Tarçın", "Höyük", "Kedi Usta", "Obsidyen"],
        "default": "Tarçın",
        "required": False,
        "help_text": "Arkeolog kedisinin adı",
    },
    {
        "key": "special_skill",
        "label": "Çocuğun Özel Yeteneği",
        "type": "select",
        "options": ["Resim Yapma", "Yapı İnşa Etme", "Tarım", "Keşif ve Gözlem"],
        "default": "Keşif ve Gözlem",
        "required": False,
        "help_text": "Hikayede çocuğun öne çıkan yeteneği",
    },
]

# ============================================================================
# DATABASE UPDATE FUNCTION
# ============================================================================


async def update_catalhoyuk_scenario():
    """Çatalhöyük senaryosunu günceller (upsert)."""
    from app.core.database import async_session_factory

    async with async_session_factory() as session:
        result = await session.execute(
            select(Scenario).where(
                (Scenario.theme_key == "catalhoyuk")
                | (Scenario.theme_key == "catalhoyuk_neolithic_city")
                | (Scenario.name.ilike("%Çatalhöyük%"))
                | (Scenario.name.ilike("%Catalhoyuk%"))
            )
        )
        scenario = result.scalar_one_or_none()

        if not scenario:
            print("Çatalhöyük scenario not found — skipping")
            return

        scenario.name = "Çatalhöyük Macerası"
        scenario.description = (
            "9000 yıl öncesine yolculuk! Dünyanın en eski şehirlerinden "
            "Çatalhöyük'ü keşfet. Damdan girilen kerpiç evler, duvar resimleri "
            "ve ilk uygarlık adımlarını öğren. UNESCO Dünya Mirası'nda "
            "arkeoloji macerası!"
        )
        scenario.theme_key = "catalhoyuk"
        scenario.cover_prompt_template = CATALHOYUK_COVER_PROMPT
        scenario.page_prompt_template = CATALHOYUK_PAGE_PROMPT
        scenario.story_prompt_tr = CATALHOYUK_STORY_PROMPT_TR
        scenario.outfit_girl = OUTFIT_GIRL
        scenario.outfit_boy = OUTFIT_BOY
        scenario.cultural_elements = CATALHOYUK_CULTURAL_ELEMENTS
        scenario.custom_inputs_schema = CATALHOYUK_CUSTOM_INPUTS
        scenario.marketing_badge = "YENİ! Arkeoloji Macerası"
        scenario.age_range = "7-10"
        scenario.tagline = "9000 yıllık zaman yolculuğu!"
        scenario.is_active = True
        scenario.display_order = 5

        await session.commit()
        print(f"Çatalhöyük scenario updated: {scenario.id}")


if __name__ == "__main__":
    asyncio.run(update_catalhoyuk_scenario())
