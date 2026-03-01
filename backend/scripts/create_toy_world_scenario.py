"""
Oyuncak Dünyası Macerası — Meşhur oyuncaklarla büyülü macera
=============================================================
- Modular prompt (500 char limit, tüm placeholder'lar mevcut)
- Outfit: EXACTLY lock phrase
- Blueprint hikaye (bölüm bölüm, dopamin döngüsü)
- Çocuk TEK BAŞINA (aile yok)
"""

import asyncio
import os
import sys
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import select

from app.core.database import async_session_factory
from app.models.scenario import Scenario

# ============================================================================
# MODULAR PROMPT COMPONENTS (500 char limit!)
# ============================================================================

TOY_COVER_PROMPT = (
    "An {child_age}-year-old {child_gender} named {child_name} "
    "with {hair_description}, wearing {clothing_description}. "
    "{scene_description}. "
    "Giant colorful toy kingdom: oversized teddy bears, wooden block castles, "
    "spinning tops, toy soldiers marching, rainbow marble roads. "
    "Warm playful lighting, candy-colored palette. "
    "Wide shot: child 30%, toy world 70%. "
    "Magical, whimsical atmosphere."
)

TOY_PAGE_PROMPT = (
    "An {child_age}-year-old {child_gender} named {child_name} "
    "with {hair_description}, wearing {clothing_description}. "
    "{scene_description}. "
    "Elements: [Teddy bears: giant plush, warm brown / Block castle: colorful wooden towers / "
    "Toy soldiers: marching tin figures / Marble roads: rainbow glass / "
    "Train: wooden toy train on tracks / Dolls: porcelain, friendly faces]. "
    "Candy colors: pastel pink, sky blue, mint green, sunny yellow."
)

# ============================================================================
# OUTFIT DEFINITIONS
# ============================================================================

OUTFIT_GIRL = (
    "bright magenta pink cotton t-shirt with small golden star on chest, "
    "light denim dungaree shorts with rainbow stitching on straps, "
    "white canvas sneakers with pink laces, small sparkly silver backpack. "
    "EXACTLY the same outfit on every page — same pink shirt, same denim dungarees, same white sneakers."
)

OUTFIT_BOY = (
    "bright turquoise blue cotton t-shirt with small rocket emblem on chest, "
    "dark navy cargo shorts with orange trim on pockets, "
    "red and white striped canvas sneakers, small orange backpack. "
    "EXACTLY the same outfit on every page — same turquoise shirt, same navy shorts, same striped sneakers."
)

# ============================================================================
# STORY BLUEPRINT
# ============================================================================

TOY_STORY_PROMPT_TR = """
# OYUNCAK DÜNYASI MACERASI — CANLI OYUNCAKLAR ÜLKESİ

## TEMEL YAPI: 7 BÖLÜM, 22 SAYFA

Bu hikaye bir fantastik macera. {child_name}, gece yarısı odasındaki
oyuncaklar canlanınca kendini dev bir Oyuncak Dünyası'nda buluyor.
Rehberi: Cesur Ayıcık (eski, yamalı ama bilge bir oyuncak ayı).

⚠️ ÖNEMLİ KURALLAR:
- Bu bir MACERA hikayesi, oyuncak kataloğu DEĞİL
- Her bölümde çocuk AKTİF katılımcı
- Endişe → Eylem → Başarı döngüsü
- Yardımcı karakter: Cesur Ayıcık (yamalı, bilge oyuncak ayı)
- Çocuk TEK BAŞINA macerada (aile yok). Anne-baba-aile karakteri KULLANMA.
- Korku/şiddet YOK
- Oyuncaklar CANLI ve konuşabiliyor
- Meşhur oyuncak türleri: peluş ayı, tahta bloklar, kurşun askerler,
  bilye yolları, tren seti, uçan uçurtma, ip atlama, topaç, kukla

---

### BÖLÜM 1 — GİRİŞ: OYUNCAKLAR CANLANIYOR (Sayfa 1-4)
Gece yarısı. {child_name}'in odasında bir ışık parlıyor. Oyuncak kutusu
titriyor, kapağı açılıyor. Peluş ayı gözlerini kırpıyor! "Merhaba!
Ben Cesur Ayıcık. Oyuncak Dünyası tehlikede — yardımına ihtiyacım var!"
Oda büyüyor, oyuncaklar dev oluyor, çocuk küçülüyor!
- S1: Gece yarısı, odada garip ışık
- S2: Oyuncak kutusu titriyor, kapak açılıyor
- S3: Cesur Ayıcık canlanıyor! "Yardımına ihtiyacım var!" ✓ İLK HEYECAN
- S4: Oda dönüşüyor — oyuncaklar DEV, çocuk küçülüyor!
**Değer**: Merak, cesaret

---

### BÖLÜM 2 — TAHTA BLOK KALESİ (Sayfa 5-8)
Renkli tahta bloklardan yapılmış devasa kale. Blok Kral'ın tacı kayıp!
Kale çökmek üzere çünkü taç kalenin dengesi. Çocuk blokları doğru
sıraya dizerek kaleyi kurtarmalı.
- S5: Dev tahta blok kalesi — renkli kuleler
- S6: Blok Kral: "Tacım kayıp, kale çökecek!" ✓ ENDİŞE
- S7: Blokları doğru sıraya dizme — bulmaca!
- S8: Kale kurtarıldı! Blok Kral teşekkür ediyor ✓ BAŞARI
**Değer**: Problem çözme, mantık

---

### BÖLÜM 3 — BİLYE YOLLARI: GÖKKUŞAĞI LABYRENT (Sayfa 9-12)
Cam bilyelerden yapılmış gökkuşağı yollar. Bilyeler kendi kendine
yuvarlanıyor, yollar sürekli değişiyor. Kayıp Altın Bilye'yi bulmak
için labirenti geçmek lazım. Ama yollar hareket ediyor!
- S9: Gökkuşağı bilye yolları — parlak, renkli
- S10: Yollar değişiyor! "Hangi yöne gitsem?" ✓ ENDİŞE
- S11: Bilyelerle iletişim — onları takip et!
- S12: Altın Bilye bulundu! Yeni güç: yolları görebilme ✓ BAŞARI
**Değer**: Adaptasyon, gözlem

---

### BÖLÜM 4 — KURŞUN ASKER GEÇIT TÖRENİ (Sayfa 13-16)
Kurşun askerler geçit töreni yapıyor ama düzenleri bozulmuş.
Komutan Asker: "Müziğimiz kayıp, adım atamıyoruz!" Çocuk ritim
tutarak askerlerin yürümesine yardım ediyor. Birlikte marş!
- S13: Kurşun askerler — düzensiz, üzgün
- S14: "Müziğimiz kayıp!" — ritim bulmaca ✓ ENDİŞE
- S15: Çocuk ritim tutuyor, askerler yürümeye başlıyor!
- S16: Muhteşem geçit töreni! Çocuk komutan oluyor ✓ BAŞARI ZİRVESİ
**Değer**: Liderlik, ekip çalışması, ritim

---

### BÖLÜM 5 — OYUNCAK TREN YOLCULUĞU (Sayfa 17-19)
Tahta oyuncak tren! Raylar şeker kamışından, istasyonlar oyuncak
evlerden. Tren Oyuncak Dünyası'nın en uzak köşesine gidiyor.
Yolda sürprizler: uçan uçurtmalar, ip atlayan bebekler, dönen topaçlar.
- S17: Tahta trene biniş — düdük sesi!
- S18: Tren yolculuğu — pencereden sürprizler ✓ HAYRANLIK
- S19: Son istasyon — Oyuncak Sarayı'na varış
**Değer**: Yolculuk, keşif, sabır

---

### BÖLÜM 6 — OYUNCAK SARAYI: BÜYÜK GİZEM (Sayfa 20-21)
Oyuncak Sarayı'nda Oyuncak Kraliçesi (eski bir porselen bebek).
"Oyuncak Dünyası'nı kurtarmanın sırrı: SEVGİ. Bir çocuğun sevgisi
olmadan oyuncaklar canlı kalamaz." Çocuk anlıyor: oyuncaklarını
sevdiği için bu dünya var!
- S20: Oyuncak Sarayı — görkemli, renkli
- S21: "Sır SEVGİ!" — farkındalık ✓ DORUK KEŞİF
**Değer**: Sevgi, değer bilme, bağ kurma

---

### BÖLÜM 7 — FİNAL: SABAH IŞIĞI (Sayfa 22)
Sabah ışığı odasına vuruyor. Çocuk yatağında uyanıyor. Oyuncakları
yerinde duruyor ama... Cesur Ayıcık gülümsüyor gibi! Cebinde
küçük altın bilye — rüya değildi!
- S22: Uyanış, oyuncaklara sarılma, gülümseme ✓ TATMİN DORUĞU
**Değer**: Hayal gücü, sevgi, oyuncaklara değer verme

---

## DOPAMİN ZİRVELERİ:
1. S3: Cesur Ayıcık canlanıyor
2. S4: Oda dönüşüyor — dev oyuncaklar!
3. S8: Blok kalesi kurtarıldı
4. S12: Altın Bilye bulundu
5. S16: Geçit töreni — çocuk komutan!
6. S18: Tren yolculuğu sürprizleri
7. S21: "Sır SEVGİ!"
8. S22: Altın bilye — rüya değildi!

## GÜVENLİK KURALLARI:
- Korku/şiddet YOK (kötü karakter YOK)
- Oyuncaklar dost, sıcak, eğlenceli
- Çocuk TEK BAŞINA (aile yok)
- Pozitif, hayal gücü odaklı atmosfer

Hikayeyi {page_count} sayfaya yaz. Her sayfa 2-4 cümle (40-80 kelime).
"""

# ============================================================================
# CULTURAL ELEMENTS
# ============================================================================

TOY_CULTURAL_ELEMENTS = {
    "location": "Magical Toy World (fantasy realm)",
    "toy_types": [
        "Giant teddy bears (plush, warm brown)",
        "Wooden block castles (colorful towers)",
        "Tin soldiers (marching, musical)",
        "Glass marble roads (rainbow, shifting)",
        "Wooden toy train (candy cane rails)",
        "Porcelain dolls (friendly, wise)",
        "Spinning tops, kites, jump ropes",
    ],
    "atmosphere": "Whimsical, magical, warm, playful, candy-colored",
    "color_palette": "pastel pink, sky blue, mint green, sunny yellow, candy red, lavender",
    "values": ["Love", "Imagination", "Problem-solving", "Teamwork", "Appreciation"],
}

# ============================================================================
# CUSTOM INPUTS
# ============================================================================

TOY_CUSTOM_INPUTS = [
    {
        "key": "favorite_toy",
        "label": "En Sevdiği Oyuncak",
        "type": "select",
        "options": ["Peluş Ayı", "Tahta Bloklar", "Tren Seti", "Bilye Koleksiyonu", "Kurşun Askerler"],
        "default": "Peluş Ayı",
        "required": False,
        "help_text": "Hikayede çocuğun en çok vakit geçireceği oyuncak",
    },
    {
        "key": "toy_mission",
        "label": "Oyuncak Görevi",
        "type": "select",
        "options": ["Kayıp Tacı Bul", "Gökkuşağı Bilyeyi Keşfet", "Müziği Geri Getir", "Oyuncak Sarayını Koru"],
        "default": "Kayıp Tacı Bul",
        "required": False,
        "help_text": "Hikayenin ana macera görevi",
    },
]

# ============================================================================
# DATABASE FUNCTION
# ============================================================================


async def create_toy_world_scenario():
    """Oyuncak Dünyası senaryosunu oluşturur veya günceller."""

    async with async_session_factory() as db:
        result = await db.execute(
            select(Scenario).where(
                (Scenario.theme_key == "toy_world")
                | (Scenario.name.ilike("%Oyuncak%"))
            )
        )
        scenario = result.scalar_one_or_none()

        if not scenario:
            scenario = Scenario(id=uuid.uuid4())
            db.add(scenario)

        scenario.name = "Oyuncak Dünyası Macerası"
        scenario.thumbnail_url = ""
        scenario.description = (
            "Gece yarısı oyuncaklar canlanıyor! Dev peluş ayılar, "
            "tahta blok kaleleri, gökkuşağı bilye yolları ve kurşun asker "
            "geçit töreninde büyülü bir macera. Sevginin gücünü keşfet!"
        )
        scenario.theme_key = "toy_world"
        scenario.cover_prompt_template = TOY_COVER_PROMPT
        scenario.page_prompt_template = TOY_PAGE_PROMPT
        scenario.story_prompt_tr = TOY_STORY_PROMPT_TR
        scenario.outfit_girl = OUTFIT_GIRL
        scenario.outfit_boy = OUTFIT_BOY
        scenario.cultural_elements = TOY_CULTURAL_ELEMENTS
        scenario.custom_inputs_schema = TOY_CUSTOM_INPUTS
        scenario.marketing_badge = "YENİ! Fantastik Macera"
        scenario.age_range = "4-8"
        scenario.tagline = "Oyuncaklar canlanıyor!"
        scenario.is_active = True
        scenario.display_order = 17

        await db.commit()
        print(f"Oyuncak Dünyası scenario created/updated: {scenario.id}")


if __name__ == "__main__":
    asyncio.run(create_toy_world_scenario())
