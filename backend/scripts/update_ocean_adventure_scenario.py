# -*- coding: utf-8 -*-
"""
Okyanus Derinlikleri: Mavi Dev ile Macera Senaryosu - Master Prompt Güncellemesi

Bu script, Okyanus Derinlikleri senaryosunu profesyonel, tutarlı ve
okyanus bilimi odaklı prompt'larla ekler/günceller.

Çalıştırma:
    cd backend
    python -m scripts.update_ocean_adventure_scenario
"""

import asyncio
import json

from sqlalchemy import or_, select
from app.core.database import async_session_factory
from app.models.scenario import Scenario


# =============================================================================
# OKYANUS DERINLIKLERI - MASTER PROMPT TEMPLATES
# =============================================================================

# -----------------------------------------------------------------------------
# KAPAK PROMPT TEMPLATE (Modular - Pipeline-Friendly: 347 char)
# -----------------------------------------------------------------------------

OCEAN_COVER_PROMPT = """Epic underwater scene: {scene_description}. 
Dolphin companion beside child (playful, friendly guide). 
MASSIVE blue whale in background (30m, emphasize scale - child tiny). 
Bioluminescent jellyfish glowing. Vibrant coral reefs. 
Deep ocean gradient (turquoise to indigo). Sunlight rays from above. 
Peaceful, wondrous atmosphere."""


# -----------------------------------------------------------------------------
# IC SAYFA PROMPT TEMPLATE (Modular - Pipeline-Friendly: 485 char)
# -----------------------------------------------------------------------------

OCEAN_PAGE_PROMPT = """Underwater scene: {scene_description}. 
Dolphin companion in shallow-mid depths (playful guide). 
Zone: [Epipelagic 0-200m: coral, tropical fish, turtle, turquoise, sun / Mesopelagic 200-1000m: blue-purple, glowing jellyfish, lanternfish / Bathypelagic 1000-4000m: dark, anglerfish, bioluminescence / Whale: MASSIVE (30m, 200 tons), child TINY, gentle, singing, riding / Abyssopelagic 4000m+: darkness, hydrothermal vents, phosphorescent stars]. 
Match zone to depth."""


# -----------------------------------------------------------------------------
# AI HIKAYE URETIM PROMPTU (Gemini icin - TR) - Blueprint Optimized
# -----------------------------------------------------------------------------

OCEAN_STORY_PROMPT_TR = """Sen {child_name} isimli {child_age} yaşında bir çocuğun OKYANUS DERİNLİKLERİNDE yaşadığı EPİK SUBALTI MACERASI yazıyorsun.
Çocuğun yanında {dolphin_name} adlı yunus arkadaşı rehberlik yapıyor.

🎯 BLUEPRINT YAPISI - HEYECANLI ÖRGÜ (22 sayfa):

**BÖLÜM 1 - GİRİŞ** (Sayfa 1-6) [role: opening→exploration]:
- Sayfa 1-2: Araştırma gemisi/lab, yunus tanışma
  → Epic #1: Yunus atlama gösterileri, ilk bağ
  → Duygu: Merak, heyecan ("Yunus benimle oynuyor!")
- Sayfa 3-6: İlk dalış (Epipelagic 0-200m)
  → Epic #2: Mercan tüneli, renkler göz kamaştırıyor
  → Duygu: Keşif ("Okyanus sihirli bir dünya!")

**BÖLÜM 2 - DERİNLEŞME + ENDİŞE** (Sayfa 7-12) [role: exploration→crisis]:
- Sayfa 7-8: Alacakaranlık (Mesopelagic 200-1000m)
  → Epic #3: İlk fosforlu denizanası - büyü gibi!
  → Endişe başlıyor: "Işık azalıyor, karanlığa gidiyoruz..."
- Sayfa 9-10: Gece bölgesi (Bathypelagic 1000-4000m)
  → Endişe ARTIYOR: "Karanlık! Garip canlılar..."
- Sayfa 11: Dev kalamar gölgesi
  → KRİZ: "Tehlikeli mi?!" → Yunus: "Uzakta, güvendesin"
- Sayfa 12: Yunus veda (sığ sulara dönüyor)
  → ENDİŞE ZİRVE: "Yalnız kalacağım..."
  → Foreshadowing: Uzaktan "şarkı" duyuluyor

**BÖLÜM 3 - DORUK/EPİK KARŞILAŞMA** (Sayfa 13-15) [role: climax]:
- Sayfa 13: MAVİ BALİNA İLK GÖRÜNÜŞ
  → Epic #4: DEVASA balina karanlıktan çıkıyor
  → ŞOK: "30 METRE! Gözü kafamdan büyük!"
  → Endişe→Hayranlık: "Korkmalı mıyım? → Şarkı söylüyor, nazik!"
- Sayfa 14: DOKUNMA ANI
  → Epic #5: Balinanın derisine dokunma, kalp atışları
  → BAĞLANMA: Göz göze, balina kabul ediyor
  → DEĞER: Sabır ve naziklik → güven kazandı
- Sayfa 15: BALINA BİNME
  → Epic #6 (ZİRVE!): Sırtında "uçuş"
  → ZAFER: "Başardım! En büyük canlıyla arkadaşım!"
  → SCALE: Dünyanın en büyüğü + en küçüğü birlikte

**BÖLÜM 4 - DERİN KEŞİF** (Sayfa 16-19) [role: resolution]:
- Sayfa 16-17: Abyss (Abyssopelagic 4000-6000m)
  → Epic #7: Hidrotermal bacalar - sualtı volkanları!
- Sayfa 18-19: Fosforlu galaksi
  → Epic #8: Binlerce ışık yıldız gibi - büyü!
  → Hazine bulma

**BÖLÜM 5 - KAPANIŞ** (Sayfa 20-22) [role: conclusion]:
- Sayfa 20-21: Yükseliş, vedalaşma töreni
  → DEĞER DORUK: "Sizi koruyacağım"
- Sayfa 22: Gün batımı
  → KAPANIŞ: "Devler bile nazik olabilir"

⚡ ENDİŞE-BAŞARI DÖNGÜLERİ:
1. Sayfa 8: "Karanlık..." → Fosforlu canlı: "Sihirli!"
2. Sayfa 11: "Kalamar!" → Yunus: "Güvendesin"
3. Sayfa 12: "Yalnızım" → Balina şarkısı
4. Sayfa 13: "DEVASA!" → Nazik şarkı

💎 DEĞER MESAJLARİ (Subliminal):
- CESARET: "Kalbim hızlı atıyordu ama merak güçlüydü" (eylem)
- SABIR: Yavaşça yaklaşma → balina güveniyor
- DOSTLUK: Farklı canlılarla bağ (yunus, balina)
- SAYGI: "Seni koruyacağım" (söz, öğüt değil)

🌊 HİKAYE YAPISI (Derinlik Derinlik Keşif):

AÇILIŞ - Denizle İlk Karşılaşma (2-3 sayfa):
- Araştırma gemisinde veya deniz biyoloji lab'ında başlangıç
- {dolphin_name} yunus ile kıyıda tanışma, bağ kurma (oyun, iletişim)
- İlk dalış: Snorkel ile sığ su, ilk mercan resifleri
- Yunus rehberlik yapıyor, daha derine davet ediyor

OLAY TETİKLEYİCİ - Derinlerdeki Çağrı:
- Yunus uzaktan gelen bir "şarkı" duyuyor (mavi balina çağrısı)
- {exploration_goal} görevi ortaya çıkıyor
- Daha derine inme kararı, denizaltıya veya gelişmiş dalgıç kıyafetine geçiş

GELİŞME - Kademeli Derinleşme (15-17 sayfa):

**1. IŞIKLI BÖLGE (0-200m) - Mercan Bahçeleri:**
- Rengarenk mercan bahçeleri: Beyin mercanlar, boynuz mercanlar
- Renkli balık sürüleri: Palyaço balığı, papağan balığı
- Deniz kaplumbağası ile yüzme
- Ahtapot kılık değiştiriyor, sihirli gibi
- Yunus ile oyun: Atlama gösterileri, yarış
- Denizaltıya geçiş: Mini denizaltı aracı tanıtımı

**2. ALACAKARANLIK BÖLGESİ (200-1000m):**
- Işık azalmaya başlıyor, mavi-mor tonlar
- İlk fosforlu canlılar ortaya çıkıyor
- Parlayan denizanaları (mavi ışık), fener balıkları (karın ışıkları)
- Gizemli ama güzel atmosfer
- Yunus hala yanında, denizaltıdan takip ediyor
- Işıktan karanlığa geçiş heyecanı

**3. GECE BÖLGESİ (1000-4000m):**
- Karanlık su, sadece biyolüminesans ışık
- Garip derin deniz canlıları: Fener balığı (ışıklı yem), baltabaşı balığı
- Dev kalamar kolları karanlıkta (gizemli, tehdit değil)
- Denizaltı ışıkları küçük alan aydınlatıyor
- Yunus sığ sulara dönüyor, "aşağıda arkadaşım var" mesajı
- Merak ve keşif hissi

**4. MAVİ BALİNA KARŞILAŞMASI (EPİK DORUK - 3 sayfa):**

*Sayfa 1 - İlk Görünüş:*
- 30 metre uzunluğunda DEVASA mavi balina derin maviden çıkıyor
- Çocuk UFACIK kalıyor - balinanın gözü bile çocuk başından büyük
- Balina nazik ve huzurlu, şarkı söylüyor (düşük frekanslı)
- İlk şok: "Bu kadar büyük bir canlı olabileceğine inanmıyorum!"

*Sayfa 2 - Yakınlaşma ve Bağ:*
- Çocuk denizaltıdan/gelişmiş dalgıç kıyafetiyle dikkatle yaklaşıyor
- Balinaya dokunma anı: Derisi pürüzsüz, kalp atışları su altında hissediliyor
- Göz göze gelme: Balinanın gözünde bilgelik ve nezaket
- Balina çocuğu "arkadaş" olarak kabul ediyor

*Sayfa 3 - Sırt Yolculuğu:*
- Balina çocuğu sırtına alıyor, su altında "uçuş"
- Balina okyanusun derinliklerine iniyor, çocuğu özel yere götürüyor
- Balina şarkısı suda yankılanıyor, kabarcıklar
- En büyük canlıyla en küçük keşifçi birlikte

**5. ABYSS SIRLARI (4000-6000m):**
- Okyanus dibine varış, tam karanlık
- Hidrotermal bacalar: Sıcak su fışkırıyor, egzotik yaşam
- Dev istiridye yatakları, tüpsüz solucanlar
- Fosforlu bir "galaksi" gibi deniz dibi: Binlerce parlayan canlı yıldız gibi
- Balina burada GİZLİ HAZİNE gösteriyor: Antik gemi enkazı veya kristal mağara
- Dönüş yolculuğu başlıyor

KAPANIŞ - Yüzeye Dönüş ve Vedalaşma (3-4 sayfa):
- Balina çocuğu nazikçe yüzeye taşıyor
- Yunus karşılıyor, heyecanla selam veriyor
- Vedalaşma töreni: Yunus + balina + deniz kaplumbağası + diğer canlılar
- Yüzeye çıkış: Gün batımı, deniz altın rengi parıyor
- "Okyanusun en büyük sırrını öğrendim: Devler bile nazik olabilir"
- Eve dönüş, anılar kalıcı
- Epilog: Çocuk yunusu ve balinayı asla unutmayacak, okyanusları koruyacak

⚡ HEYECAN VERİCİ SAHNELER (MUTLAKA):
1. **Yunus Atlama Gösterileri**: Sığ suda oyun, acrobatic atlayışlar
2. **Mercan Tüneli**: Renkli mercanlar arasında yüzme
3. **İlk Fosforlu Canlı**: Karanlıkta parlayan denizanası - büyü gibi
4. **Mavi Balina Şarkısı**: Ses dalgaları görselleştirilmiş, epik
5. **Balinanın Sırtında Uçuş**: Sualtı "uçma", en heyecanlı
6. **Fosforlu Galaksi**: Deniz dibi binlerce ışıkla kaplı
7. **Vedalaşma Töreni**: Tüm deniz canlıları bir arada

🐋 MAVİ BALİNA BOYUT ve NAZİKLİK YÖNETİMİ:
- Balina GERÇEKÇİ boyutta: 30m uzunluk, 200 ton ağırlık
- İLK karşılaşma: Heybetli, dev, çocuk karınca gibi küçük
- SONRA: Balina şarkı söylüyor, nazik, koruyucu
- Boyut farkı SÜREKLİ vurgulanır: "Balinanın kalbi arabam kadar büyüktü!"
- Ama bağ VAR: Dokunma, binme, birlikte yolculuk, göz göze gelme

🐬 YUNUS ARKADAŞ ({dolphin_name}):
- Her sahnede (sığ-orta derinlikte) görünür veya bahsedilir
- Rehberlik yapar, yolu gösterir
- Oyuncu, sevimli, güvenilir
- Derin sulara gidemez ama mesaj verir: "Aşağıda arkadaşım var"
- Kapanışta geri dönüyor, vedalaşma töreni

📚 OKYANUS BİLGİLERİ (Hikayeye Doğal Entegre):
- Okyanus yeryüzünün %71'i
- Mavi balina en büyük canlı, kalbi araba büyüklüğü
- Biyolüminesans = canlı ışık
- Hidrotermal bacalar = sualtı volkanları
- %95 okyanus keşfedilmemiş
- Mercan resifleri canlı organizmalar

💎 ANA DEĞER: MERAK + DOĞA SEVGİSİ
- Okyanusları keşfetme isteği
- Deniz yaşamını koruma bilinci
- Devasa canlılara saygı
- Bilimsel merak (okyanografi)
- Çevre sorumluluğu (plastik yok, temiz denizler)

⛔ YASAKLAR (Çocuk Güvenliği):
- Köpekbalığı saldırısı YOK
- Boğulma/oksijen bitmesi YOK
- Tehlikeli canlılar (zehirli, saldırgan) YOK
- Dev kalamar saldırısı YOK (sadece gizemli işaretler)
- Basınç ezilmesi YOK (ekipman korur)
- Kaybolma/panik YOK

📖 SAYFA DAĞILIMI:
Hikayeyi {page_count} sayfaya yaz. Her sayfa 3-5 cümle (60-100 kelime).
- Sayfa 1-2: Açılış (gemi/lab + yunus tanışma)
- Sayfa 3-6: Sığ su (mercan + yunus oyunu)
- Sayfa 7-10: Alacakaranlık + Gece bölgesi (fosforlu canlılar)
- Sayfa 11-12: Geçiş (yunus veda, balina çağrısı)
- Sayfa 13-15: MAVİ BALİNA (epik, 3 sayfa - görünüş, dokunma, binme)
- Sayfa 16-19: Abyss derinliği (hidrotermal, fosforlu galaksi, hazine)
- Sayfa 20-22: Kapanış (yükseliş, vedalaşma, gün batımı)

🎯 CUSTOM INPUT KULLANIMI:
- {favorite_creature}: Bu canlıya EN FAZLA zaman ayır, özel an
- {dolphin_name}: Yunus arkadaşın adı - sürekli kullan
- {exploration_goal}: Ana görev olarak hikayeye entegre et"""


# -----------------------------------------------------------------------------
# KIYAFET TASARIMLARI (Scenario-Specific - Diving Suits)
# -----------------------------------------------------------------------------

OUTFIT_GIRL = """modern diving wetsuit in teal and coral pink colors with white trim, neoprene material with water droplet texture, clear full-face diving mask with pink frame, oxygen tank backpack in metallic silver, yellow diving fins, waterproof wrist computer showing depth gauge, underwater camera hanging from neck strap"""

OUTFIT_BOY = """navy blue and orange diving wetsuit with reflective stripes, neoprene texture with padding on chest and knees, clear diving mask with blue frame and anti-fog coating, compact silver oxygen tank on back, bright orange diving fins, waterproof flashlight attached to belt, diving knife in leg holster"""


# -----------------------------------------------------------------------------
# KULTUREL ELEMENTLER (JSON)
# -----------------------------------------------------------------------------

OCEAN_CULTURAL_ELEMENTS = {
    "ocean_zones": [
        "Epipelagic (Sunlight, 0-200m): Coral reefs, dolphins, turtles",
        "Mesopelagic (Twilight, 200-1000m): Bioluminescent creatures, lanternfish",
        "Bathypelagic (Midnight, 1000-4000m): Giant squid, anglerfish",
        "Abyssopelagic (Abyss, 4000-6000m): Hydrothermal vents, tube worms",
        "Hadalpelagic (Trenches, 6000m+): Deepest creatures, extreme pressure",
    ],
    "marine_creatures": [
        "Blue Whale - largest animal ever (30m, 200 tons)",
        "Dolphin - intelligent, playful, echolocation",
        "Giant Squid - mysterious deep sea creature",
        "Bioluminescent jellyfish - glowing in darkness",
        "Sea Turtle - ancient, graceful swimmers",
        "Manta Ray - gentle giants with wing-like fins",
        "Coral - living organism, reef builders",
        "Octopus - intelligent, color-changing",
        "Anglerfish - deep sea with bioluminescent lure",
        "Lanternfish - belly lights in twilight zone",
    ],
    "scientific_facts": [
        "Ocean covers 71% of Earth's surface",
        "Blue whale heart size of a small car",
        "95% of ocean still unexplored by humans",
        "Bioluminescence = living creatures producing light",
        "Hydrothermal vents = underwater volcanoes with unique life",
        "Mariana Trench deepest point (10,994 meters)",
        "Dolphins use echolocation to navigate",
        "Coral reefs support 25% of all marine species",
    ],
    "ocean_technology": [
        "Submarine/submersible vehicles",
        "Diving suits and oxygen tanks",
        "Underwater lights and cameras",
        "Sonar and echolocation",
        "Pressure-resistant equipment",
        "ROV (Remotely Operated Vehicles)",
        "Depth gauges and computers",
    ],
    "color_palette": "turquoise shallow water, sapphire blue mid-ocean, dark indigo abyss, bioluminescent blue-green-purple glow, golden sunlight god rays, coral reef rainbow colors (pink, orange, yellow, purple)",
    "atmosphere": "wondrous, peaceful, mysterious, vast, scientific curiosity, respect for ocean life, environmental awareness",
    "environmental_message": [
        "Ocean conservation and protection",
        "Plastic-free seas",
        "Protecting marine life and habitats",
        "Coral reef preservation",
        "Respecting giant creatures",
    ],
    "lighting_effects": [
        "sunlight god rays from surface",
        "bioluminescent creature glow",
        "submarine spotlight cones",
        "ambient deep blue darkness",
        "golden sunset surface glow",
    ],
}


# -----------------------------------------------------------------------------
# OZEL GIRIS ALANLARI (Custom Inputs)
# -----------------------------------------------------------------------------

OCEAN_CUSTOM_INPUTS = [
    {
        "key": "favorite_creature",
        "label": "En Sevdiği Deniz Canlısı",
        "type": "select",
        "options": [
            "Mavi Balina",
            "Yunus",
            "Deniz Kaplumbagasi",
            "Ahtapot",
        ],
        "default": "Mavi Balina",
        "required": False,
        "help_text": "Hikayede en çok vakit geçirilecek deniz canlısı",
    },
    {
        "key": "dolphin_name",
        "label": "Yunus Arkadaşın Adı",
        "type": "select",
        "options": [
            "Dodo",
            "Luna",
            "Flip",
            "Echo",
        ],
        "default": "Luna",
        "required": False,
        "help_text": "Rehber yunus arkadaşının adı",
    },
    {
        "key": "exploration_goal",
        "label": "Keşif Amacı",
        "type": "select",
        "options": [
            "Mavi Balinayı Görme",
            "En Derin Noktaya İnme",
            "Kayıp Hazineyi Bulma",
            "Fosforlu Canlıları Keşfetme",
        ],
        "default": "Mavi Balinayı Görme",
        "required": False,
        "help_text": "Macera sırasında tamamlanacak ana görev",
    },
]


async def update_ocean_adventure_scenario():
    """Okyanus Derinlikleri senaryosunu master prompt'larla guncelle veya olustur."""

    print("\n" + "=" * 60)
    print("OKYANUS DERINLIKLERI: MAVI DEV ILE MACERA SENARYO GUNCELLEMESI")
    print("=" * 60 + "\n")

    async with async_session_factory() as db:
        result = await db.execute(
            select(Scenario).where(
                or_(
                    Scenario.name.ilike("%Okyanus%"),
                    Scenario.name.ilike("%Ocean%"),
                    Scenario.theme_key == "ocean_depths",
                )
            )
        )
        scenario = result.scalar_one_or_none()

        if not scenario:
            print(
                "[INFO] 'Okyanus Derinlikleri' senaryosu bulunamadi. Yeni olusturuluyor..."
            )
            scenario = Scenario(
                name="Okyanus Derinlikleri: Mavi Dev ile Macera",
                is_active=True,
            )
            db.add(scenario)
        else:
            print(f"[OK] Senaryo bulundu: {scenario.name} (ID: {scenario.id})")

        scenario.description = (
            "Okyanusun derinliklerine dal! Yunus arkadasinla mercan bahcelerinden basla, "
            "fosforlu canlilarla tanis, 30 metrelik dev mavi balinaya bin. "
            "5 farkli derinlik seviyesinde unutulmaz kesif!"
        )
        scenario.thumbnail_url = "/scenarios/ocean_adventure.jpg"
        scenario.cover_prompt_template = OCEAN_COVER_PROMPT
        scenario.page_prompt_template = OCEAN_PAGE_PROMPT
        scenario.story_prompt_tr = OCEAN_STORY_PROMPT_TR
        scenario.ai_prompt_template = None
        scenario.location_en = "Pacific Ocean"
        scenario.theme_key = "ocean_depths"
        scenario.cultural_elements = OCEAN_CULTURAL_ELEMENTS
        scenario.custom_inputs_schema = OCEAN_CUSTOM_INPUTS
        scenario.outfit_girl = OUTFIT_GIRL
        scenario.outfit_boy = OUTFIT_BOY
        scenario.default_page_count = 22
        scenario.display_order = 16
        scenario.is_active = True

        scenario.marketing_badge = "Okyanus Keşfi"
        scenario.age_range = "5-10 yaş"
        scenario.tagline = (
            "Mavi balinadan okyanus dibine! Yunusla derin deniz macerasi"
        )
        scenario.marketing_features = [
            "Devasa mavi balina karsilasmasi",
            "Yunus arkadasla yuzme",
            "5 farkli derinlik seviyesi",
            "Fosforlu canlilar (biyoluminesans)",
            "Denizalti + dalgic deneyimi",
            "Okyanus bilimi ve cevre bilinci",
        ]
        scenario.marketing_gallery = [
            {
                "url": "/gallery/ocean/coral_reef.jpg",
                "caption": "Renkli mercan bahçeleri",
                "alt_text": "Çocuk renkli mercanlar arasında yüzüyor"
            },
            {
                "url": "/gallery/ocean/blue_whale.jpg", 
                "caption": "30 metrelik mavi balina ile tanışma",
                "alt_text": "Dev mavi balina ve küçük çocuk"
            },
            {
                "url": "/gallery/ocean/bioluminescent.jpg",
                "caption": "Fosforlu denizanaları",
                "alt_text": "Karanlıkta parlayan denizanaları"
            },
            {
                "url": "/gallery/ocean/dolphin_play.jpg",
                "caption": "Yunus arkadaşla oyun",
                "alt_text": "Çocuk yunusla birlikte yüzüyor"
            }
        ]
        scenario.estimated_duration = "20-25 dakika okuma"
        scenario.marketing_price_label = "299 TL'den başlayan fiyatlarla"
        scenario.rating = 5.0

        await db.commit()
        await db.refresh(scenario)

        print("\n[OK] GUNCELLEME TAMAMLANDI!\n")
        print("-" * 60)
        print("Guncellenen alanlar:")
        print(f"   - ID: {scenario.id}")
        print(f"   - name: {scenario.name}")
        print(f"   - description: {len(scenario.description or '')} karakter")
        print(f"   - thumbnail_url: {scenario.thumbnail_url}")
        print(f"   - cover_prompt_template: {len(OCEAN_COVER_PROMPT)} karakter")
        print(f"   - page_prompt_template: {len(OCEAN_PAGE_PROMPT)} karakter")
        print(f"   - story_prompt_tr: {len(OCEAN_STORY_PROMPT_TR)} karakter")
        print("   - location_en: Pacific Ocean")
        print("   - theme_key: ocean_depths")
        print(
            f"   - cultural_elements: {len(json.dumps(OCEAN_CULTURAL_ELEMENTS))} karakter (JSON)"
        )
        print(f"   - custom_inputs_schema: {len(OCEAN_CUSTOM_INPUTS)} ozel alan")
        print(f"   - outfit_girl: {len(OUTFIT_GIRL)} karakter")
        print(f"   - outfit_boy: {len(OUTFIT_BOY)} karakter")
        print(f"   - default_page_count: {scenario.default_page_count}")
        print(f"   - display_order: {scenario.display_order}")
        print(f"   - rating: {scenario.rating}")
        print("-" * 60)

        print("\nKAPAK PROMPT ONIZLEME (ilk 500 karakter):")
        print("-" * 60)
        print(OCEAN_COVER_PROMPT[:500] + "...")

        print("\nSAYFA PROMPT ONIZLEME (ilk 500 karakter):")
        print("-" * 60)
        print(OCEAN_PAGE_PROMPT[:500] + "...")

        print("\nSTORY_PROMPT_TR ONIZLEME (ilk 400 karakter):")
        print("-" * 60)
        print(OCEAN_STORY_PROMPT_TR[:400] + "...")

        print("\n" + "=" * 60)
        print("Okyanus Derinlikleri artik master-level prompt'lara sahip!")
        print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(update_ocean_adventure_scenario())
