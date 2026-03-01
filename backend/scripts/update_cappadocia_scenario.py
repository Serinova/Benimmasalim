"""
Kapadokya Macerası — Düzeltilmiş Güncelleme
============================================
- Modular prompt (500 char limit, tüm placeholder'lar mevcut)
- Hikaye: Macera odaklı (balon + yeraltı + peri bacaları)
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

CAPPADOCIA_COVER_PROMPT = (
    "An {child_age}-year-old {child_gender} named {child_name} "
    "with {hair_description}, wearing {clothing_description}. "
    "{scene_description}. "
    "Iconic Cappadocia fairy chimneys in background, colorful hot air balloons in sky. "
    "Goreme valley, volcanic tuff formations, golden sunrise light. "
    "Wide shot: child 25%, fairy chimneys and balloons 75%. "
    "Magical adventure atmosphere. UNESCO site."
)

CAPPADOCIA_PAGE_PROMPT = (
    "An {child_age}-year-old {child_gender} named {child_name} "
    "with {hair_description}, wearing {clothing_description}. "
    "{scene_description}. "
    "Elements: [Fairy chimneys: cone-shaped volcanic tuff / Hot air balloons: colorful, sunrise / "
    "Underground city: multi-level caves, tunnels / Rock churches: ancient frescoes / "
    "Valleys: Goreme, Rose Valley / Village: stone houses in rocks]. "
    "Earth colors: ochre, beige, rose pink. Magical, adventurous."
)

# ============================================================================
# OUTFIT DEFINITIONS (update_all_outfits.py standardı)
# ============================================================================

OUTFIT_GIRL = (
    "warm coral-orange puffer vest over cream white long-sleeve henley shirt, "
    "light khaki cotton pants, tan brown suede hiking boots with orange laces, "
    "small beige canvas backpack on back. "
    "EXACTLY the same outfit on every page — same coral vest, same cream shirt, same khaki pants."
)

OUTFIT_BOY = (
    "forest green quilted vest over light gray long-sleeve t-shirt, "
    "tan khaki cargo pants with zippered pockets, dark brown leather hiking boots, "
    "olive green canvas backpack on back. "
    "EXACTLY the same outfit on every page — same green vest, same gray shirt, same khaki pants."
)

# ============================================================================
# STORY BLUEPRINT (Doğa Mucizesi + Balon + Yeraltı)
# ============================================================================

CAPPADOCIA_STORY_PROMPT_TR = """
# KAPADOKYA MACERASI — DOĞA MUCİZESİ KEŞFİ

## TEMEL YAPI: 7 BÖLÜM, 22 SAYFA

Bu hikaye bir doğa ve tarih macerası. {child_name}, Kapadokya'da bir
Peri Kızı (peri bacasından canlanan küçük ışıklı varlık) ile birlikte
balonla gökyüzüne çıkar, yeraltı şehrine iner ve doğanın 60 milyon
yıllık heykeltıraşlığını keşfeder.

⚠️ ÖNEMLİ KURALLAR:
- Bu bir MACERA hikayesi, gezi rehberi DEĞİL
- Her bölümde çocuk AKTİF katılımcı
- Endişe → Eylem → Başarı döngüsü her bölümde
- Yardımcı karakter: Peri Kızı (peri bacasından canlanan ışıklı varlık)
- Çocuk TEK BAŞINA macerada (aile yok)
- Korku/şiddet YOK, büyülü ve heyecanlı

---

### BÖLÜM 1 — GİRİŞ: PERİ BACALARI (Sayfa 1-4)
{child_name} Göreme vadisinde yürürken garip kaya oluşumları görür.
Bir peri bacasının tepesinden küçük bir ışık çıkıyor — Peri Kızı!
"Bu kayalar 60 milyon yıl önce volkanla oluştu. Sana göstereyim!"
- S1: Göreme vadisine varış, garip kayalar
- S2: Peri bacaları — "Mantar gibi! Nasıl oluşmuş?"
- S3: Peri Kızı ile tanışma — ışıklı küçük varlık
- S4: "60 milyon yıllık doğa mucizesi!" ✓ İLK HAYRANLIK
**Değer**: Doğa merakı, gözlem

---

### BÖLÜM 2 — BALON MACERASI: GÖKYÜZÜ (Sayfa 5-9)
Sabah erken, gün doğumu. Peri Kızı çocuğu sıcak hava balonuna
götürüyor. Yavaşça göğe yükselme — etrafta yüzlerce renkli balon!
Tepeden Kapadokya'nın tamamı görünüyor. Ama rüzgar sertleşiyor...
- S5: Balona binme, ateş yakılıyor, heyecan
- S6: Yavaşça yükselme — "Göğe çıkıyoruz!"
- S7: Gökyüzünden manzara — peri bacaları, vadiler ✓ GÖKYÜZÜ ZİRVESİ
- S8: Rüzgar sertleşiyor! "Düşecek miyiz?" ✓ ENDİŞE
- S9: Peri Kızı rüzgarı yatıştırıyor, güvenli iniş ✓ BAŞARI
**Değer**: Cesaret, güven, doğa saygısı

---

### BÖLÜM 3 — YERALTI ŞEHRİ: DERİNKUYU (Sayfa 10-14)
Peri Kızı çocuğu yeraltı şehrine götürüyor. Dar tüneller, 8 kat
derinlik! Karanlık geçitler, ama Peri Kızı ışık saçıyor. Mutfak,
depo, kilise — 2000 yıl önce insanlar burada yaşamış!
- S10: Yeraltı şehrine giriş, dar tünel
- S11: Aşağı inme — "8 kat derinlik!" ✓ MERAK
- S12: Karanlık geçit — biraz korku, Peri Kızı ışık veriyor
- S13: Odalar keşfi — mutfak, depo, havalandırma
- S14: "2000 yıl önce burada yaşamışlar!" ✓ TARİH ZİRVESİ
**Değer**: Cesaret, tarih bilinci

---

### BÖLÜM 4 — KAYA KİLİSELER: 1000 YILLIK FRESKLER (Sayfa 15-17)
Göreme Açık Hava Müzesi. Kayaya oyulmuş kiliseler, duvarlarda
1000 yıllık resimler! Peri Kızı: "Bu resimleri yapanlar da senin
gibi meraklıydı." Çocuk kendi resmini yapmaya çalışıyor.
- S15: Kaya kiliselere giriş — "Tamamı kayadan oyulmuş!"
- S16: 1000 yıllık freskler — "İnanılmaz!" ✓ SANAT ZİRVESİ
- S17: Çocuk kendi resmini yapıyor — yaratıcılık
**Değer**: Sanat, yaratıcılık, kültürel miras

---

### BÖLÜM 5 — PEMBE VADİ: DOĞANIN RENKLERİ (Sayfa 18-19)
Pembe Vadi'de yürüyüş. Gün batımında kayalar pembe, turuncu, altın
rengi! Doğanın renk paleti. Peri Kızı: "Doğa en büyük sanatçı."
- S18: Pembe Vadi — kayalar renk değiştiriyor
- S19: Gün batımı renkleri — "Doğa en büyük sanatçı!" ✓ GÜZELLİK ZİRVESİ
**Değer**: Doğa güzelliği, estetik

---

### BÖLÜM 6 — GİZLİ MAĞARA: DOĞANIN SIRRI (Sayfa 20-21)
Peri Kızı çocuğu gizli bir mağaraya götürüyor. İçeride volkanik
tüf katmanları — 60 milyon yılın hikayesi duvarlarda yazılı!
Her katman farklı renk, farklı dönem.
- S20: Gizli mağara — volkanik katmanlar
- S21: "60 milyon yılın hikayesi duvarlarda!" ✓ DORUK KEŞİF
**Değer**: Jeoloji, bilimsel merak

---

### BÖLÜM 7 — FİNAL: KAPADOKYA'NIN BÜYÜSÜ (Sayfa 22)
Gün batımında peri bacalarının tepesinde oturma. Gökyüzünde son
balonlar. Peri Kızı: "Doğa ve insan birlikte mucize yaratmış.
Sen de bu mucizenin parçasısın." Peri Kızı kayaya geri dönüyor
ama ışığı hâlâ parlıyor.
- S22: Gün batımı, peri bacaları, gurur ✓ TATMIN DORUĞU
**Değer**: Doğa bilinci, kültürel miras koruma

---

## DOPAMIN ZİRVELERİ:
1. S4: Peri Kızı ile tanışma — 60 milyon yıl
2. S7: Balondan gökyüzü manzarası
3. S9: Rüzgar tehlikesi atlatıldı
4. S14: Yeraltı şehri — 2000 yıllık tarih
5. S16: 1000 yıllık freskler
6. S21: Gizli mağara — jeolojik sır
7. S22: Gün batımı — tatmin

## GÜVENLİK KURALLARI:
- Korku/şiddet YOK
- Yeraltı sahnesi korkutucu DEĞİL (Peri Kızı ışık veriyor)
- Balon sahnesi güvenli (Peri Kızı koruyucu)
- Pozitif, büyülü atmosfer
"""

# ============================================================================
# CULTURAL ELEMENTS
# ============================================================================

CAPPADOCIA_CULTURAL_ELEMENTS = {
    "location": "Cappadocia (Nevsehir, Urgup, Goreme), Central Anatolia, Turkey",
    "unesco": "Goreme National Park — UNESCO World Heritage Site (1985)",
    "geological_wonder": "Fairy chimney formations (60 million years of volcanic activity + erosion)",
    "key_sites": [
        "Fairy chimneys (peri bacalari) — cone-shaped volcanic tuff",
        "Hot air balloon rides (world-famous sunrise flights)",
        "Derinkuyu Underground City (8-10 levels deep)",
        "Goreme Open Air Museum (rock-carved churches, 1000-year frescoes)",
        "Rose Valley (pink-hued rocks at sunset)",
    ],
    "atmosphere": "Magical, adventurous, geological wonder",
    "color_palette": "ochre, beige, rose pink, golden sunrise, earth tones",
    "values": ["Nature appreciation", "Adventure", "History", "Geological wonder"],
}

# ============================================================================
# CUSTOM INPUTS (list formatı — frontend uyumlu)
# ============================================================================

CAPPADOCIA_CUSTOM_INPUTS = [
    {
        "key": "favorite_experience",
        "label": "En Sevdiği Deneyim",
        "type": "select",
        "options": ["Balon Turu (Gökyüzü!)", "Peri Bacaları (Doğa!)", "Yeraltı Şehri (8 kat!)", "Kaya Kiliseler (Freskler!)", "Pembe Vadi"],
        "default": "Balon Turu (Gökyüzü!)",
        "required": False,
        "help_text": "Hikayede çocuğun en çok heyecanlanacağı deneyim",
    },
    {
        "key": "companion_name",
        "label": "Peri Kızı'nın Adı",
        "type": "select",
        "options": ["Işıl", "Tüf", "Pırıl", "Kayra", "Baca"],
        "default": "Işıl",
        "required": False,
        "help_text": "Peri bacasından canlanan ışıklı arkadaşın adı",
    },
]

# ============================================================================
# DATABASE UPDATE FUNCTION
# ============================================================================


async def update_cappadocia_scenario():
    """Kapadokya senaryosunu günceller."""
    from app.core.database import async_session_factory

    async with async_session_factory() as session:
        result = await session.execute(
            select(Scenario).where(
                (Scenario.theme_key == "cappadocia")
                | (Scenario.theme_key == "cappadocia_fairy_chimneys")
                | (Scenario.name.ilike("%Kapadokya%"))
                | (Scenario.name.ilike("%Cappadocia%"))
            )
        )
        scenario = result.scalar_one_or_none()

        if not scenario:
            print("Kapadokya scenario not found — skipping")
            return

        scenario.name = "Kapadokya Macerası"
        scenario.description = (
            "Kapadokya'nın büyülü dünyasına yolculuk! Peri bacaları "
            "(60 milyon yıllık!), sıcak hava balonu turu, yeraltı şehri "
            "keşfi (8 kat derinlik!) ve kaya kiliselerdeki 1000 yıllık "
            "freskler. UNESCO Dünya Mirası'nda doğa mucizesi ve macera!"
        )
        scenario.cover_prompt_template = CAPPADOCIA_COVER_PROMPT
        scenario.page_prompt_template = CAPPADOCIA_PAGE_PROMPT
        scenario.story_prompt_tr = CAPPADOCIA_STORY_PROMPT_TR
        scenario.outfit_girl = OUTFIT_GIRL
        scenario.outfit_boy = OUTFIT_BOY
        scenario.cultural_elements = CAPPADOCIA_CULTURAL_ELEMENTS
        scenario.custom_inputs_schema = CAPPADOCIA_CUSTOM_INPUTS
        scenario.marketing_badge = "YENİ! Balon Macerası"
        scenario.age_range = "6-10"
        scenario.tagline = "Kapadokya'nın büyüsünü keşfet!"
        scenario.is_active = True

        await session.commit()
        print(f"Kapadokya scenario updated: {scenario.id}")


if __name__ == "__main__":
    asyncio.run(update_cappadocia_scenario())
