# -*- coding: utf-8 -*-
"""
Kudus Eski Sehir Macerasi Senaryosu - Yeni Sistem (Sifirdan)

Bu script, Kudus Eski Sehir senaryosunu profesyonel, hassas ve
3 dine saygilי modular prompt'larla olusturur.

HASSAS ICERIK: Dini danisman onayi onerilir.

Calistirma:
    cd backend
    python -m scripts.update_jerusalem_scenario
"""

import asyncio
import json

from sqlalchemy import select, or_
from app.core.database import async_session_factory
from app.models.scenario import Scenario


# =============================================================================
# KUDUS ESKI SEHIR - MODULAR MASTER PROMPT TEMPLATES
# =============================================================================

# -----------------------------------------------------------------------------
# KAPAK PROMPT TEMPLATE (Modular - Pipeline-Friendly: ~410 char)
# -----------------------------------------------------------------------------

JERUSALEM_COVER_PROMPT = """Jerusalem Old City scene: {scene_description}. 
Child in foreground, golden Dome of the Rock and ancient stone walls in distance. 
Narrow cobblestone streets, arched doorways, limestone buildings. 
Peaceful pilgrims from diverse backgrounds (distant, no detailed faces). 
Golden sunset light on ancient Jerusalem stone. 
Wide shot: child 20%, historic architecture 80%. 
Multi-faith respect, peaceful atmosphere. 
NO religious figure depictions, NO worship close-ups."""


# -----------------------------------------------------------------------------
# IC SAYFA PROMPT TEMPLATE (Modular - Pipeline-Friendly: ~490 char)
# -----------------------------------------------------------------------------

JERUSALEM_PAGE_PROMPT = """Jerusalem Old City scene: {scene_description}. 
Locations: [Dome of Rock: golden dome, blue tiles / Al-Aqsa: gray dome / Western Wall: ancient stones / Holy Sepulchre: stone domes / Via Dolorosa: cobblestone / Gates: Jaffa, Damascus / Four Quarters: Armenian, Jewish, Christian, Muslim / Olive trees, limestone]. 
Golden Jerusalem stone, warm sunlight. 
Diverse pilgrims (distant, no faces). 
NO worship close-ups, NO religious figures. 
Historic, peaceful, multi-faith respect."""


# -----------------------------------------------------------------------------
# AI HIKAYE URETIM PROMPTU (Gemini icin - TR) - Cultural Journey Blueprint
# -----------------------------------------------------------------------------

JERUSALEM_STORY_PROMPT_TR = """Ailesiyle birlikte Kudus Eski Sehir'e kulturel bir yolculuga giden {child_name} adli {child_age} yasinda bir cocugun tarih ve hos goru hikayesini yaz.

KULTUREL KESIF YAPISI - 7 BOLUM (22 sayfa):

**BOLUM 1 - GIRIS** (Sayfa 1-4) [role: opening]:
- Sayfa 1-2: Kudus Eski Sehir'e varis, tas sokaklari
  Ilk izlenim: Altin kubbenin gorunusu
  Emotion: Merak, tarih hissi
- Sayfa 3-4: Dort mahalleyi ogrenmek
  Kesfedilecek: Islam, Hiristiyan, Musevi, Ermeni mahalleleri
  Kesif basliyor

**BOLUM 2 - ALTIN KUBBE (Kubbetus-Sahra)** (Sayfa 5-8) [role: exploration]:
- Sayfa 5-6: Dome of the Rock yaklasma
  Epic #1: Altin kubbenin pariltisi guneste
  Mimari hayranlık: Sekizgen yapi, mavi cini suslemeleri
- Sayfa 7-8: Islamî mimari
  Tarihi bilgi: Hz. Muhammed'in Mirac gecesi (hikaye anlatimi, gorsel YOK)
  Deger: Kutsal mekan, saygi

**BOLUM 3 - MESCID-I AKSA** (Sayfa 9-11) [role: exploration]:
- Sayfa 9-10: Mescid-i Aksa avlusu
  Epic #2: Genis avlu, gri kubbe
  Mimari: Tas kemerler, tarihi binalar
- Sayfa 11: Islam tarihi
  Deger: Uc kutsal mescidden biri, manevi bag

**BOLUM 4 - AGLAMA DUVARI (Western Wall)** (Sayfa 12-14) [role: climax]:
- Sayfa 12-13: Western Wall plazasi
  Epic #3: Eski tas duvar (2000 yillik)
  Gozlem: Musevi ziyaretciler (uzaktan, saygili)
- Sayfa 14: Hosgoru anı
  Ogrenme: Farkli dinler, ayni sehir, baris
  Deger: Hosgoru, saygi

**BOLUM 5 - HRISTIYAN MIRASI** (Sayfa 15-17) [role: resolution]:
- Sayfa 15-16: Church of Holy Sepulchre
  Epic #4: Tas kubbe, tarihi giris
  Ogrenme: Hz. Isa'nin yolu (hikaye, gorsel YOK)
- Sayfa 17: Via Dolorosa sokagi
  Dar tasli sokaklar, tarihi atmosfer
  Deger: Hristiyan mirasi, saygi

**BOLUM 6 - DORT MAHALLE KESFI** (Sayfa 18-20) [role: resolution]:
- Sayfa 18: Ermeni mahallesi
  Farklı kültür, mozaik sanat
- Sayfa 19: Carsi ve sokaklari
  Rengarenk carsi, eski sehir yasami
- Sayfa 20: Dort mahallenin birligi
  Ogrenme: Farkliliklar zenginlik
  Deger: Kulturel cesitlilik

**BOLUM 7 - BARISIN SEHRI** (Sayfa 21-22) [role: conclusion]:
- Sayfa 21: Eski Sehir surlari panorama
  Epic #5: Tum sehir gorus, gun batimi
  3 din, 1 sehir, baris mesaji
- Sayfa 22: Donus ve soz
  "Farkliliklar bizi zenginlestirir"
  Emotion: Hosgoru, baris, umut

KULTUREL KESIF MOMENTLERI (5 Epic):

1. **Altin Kubbe pariltisi** (Sayfa 6): Mimari hayranlık
2. **Mescid-i Aksa avlu** (Sayfa 10): Islam tarihi
3. **Aglama Duvari** (Sayfa 13): 2000 yillik tas, Musevi mirası
4. **Church of Holy Sepulchre** (Sayfa 16): Hristiyan mirası
5. **Eski Sehir panorama** (Sayfa 21): 3 din birlikte, baris

4 KESIF DONGUSU (Hosgoru Merdivenֱ):

**Dongu 1 - Islam Mirası (5-8):**
- Kesif: Altin Kubbe + Mescid-i Aksa
- Ogrenme: Islamî mimari, Hz. Muhammed'in Mirac'i (hikaye)
- Deger: Kutsal mekan, manevi bag

**Dongu 2 - Musevi Mirası (12-14):**
- Kesif: Aglama Duvarי, 2000 yillik tas
- Ogrenme: Musevi ibadet (uzaktan gozlem, saygi)
- Deger: Farklı dine saygi, hosgoru ZIRVESI

**Dongu 3 - Hristiyan Mirası (15-17):**
- Kesif: Kutsal Kabir Kilisesi, Via Dolorosa
- Ogrenme: Hz. Isa'nin yolu (hikaye anlatimi)
- Deger: Hristiyan mirası, saygi

**Dongu 4 - Dort Mahalle Birligi (18-20):**
- Kesif: Dort mahalle (Islam, Musevi, Hristiyan, Ermeni)
- Ogrenme: Kulturel cesitlilik zenginlik
- Deger: Birlikte yasama, baris

HIKAYE YAPISI (Kulturel ve Tarihi Kesif):

KUTSAL MEKANLAR (3 Dine Saygili):
- **Islam**: Kubbetus-Sahra (Altin Kubbe), Mescid-i Aksa
- **Yahudilik**: Aglama Duvari (Western Wall)
- **Hristiyanlık**: Kutsal Kabir Kilisesi, Via Dolorosa

MIMARI UNSURLAR:
- Altin kubbe (Islamic architecture)
- Eski tas duvarlar (2000+ yillik)
- Dar tasli sokaklari
- Tas kemerler
- Dort mahalle farkli mimarileri

EGITSEL BILGILER (hikayeye organik):
- Kudus: 3 buyuk dinin kutsal sehri
- Eski Sehir: 4 mahalle (Islam, Musevi, Hristiyan, Ermeni)
- Mirac Gecesi hikayesi (gorsel YOK, anlatim)
- Hz. Isa'nin yolu (gorsel YOK, anlatim)
- Aglama Duvari: Ikinci Mabet'ten kalan duvar

ANA DEGER: HOSGORU ve BARIS
- 3 dine esit saygi
- Farkliliklara saygi
- Kulturel cesitlilik zenginliktir
- Birlikte yasama
- Baris mesajı

TON:
- Saygili, kulturel, ogretici
- Bariscil, dostane
- Tarihi odakli (dini degil)
- Hosgoru vurgusu
- Yaşa uygun dil ({child_age} yas)

YASAKLAR (Dini Hassasiyet - KRITIK!):
- Hz. Muhammed, Hz. Isa, peygamberler GORSELLESTIRMEZ
- Ibadet close-up'lari YOK (namaz, dua sadece uzaktan bahsedilir)
- 3 dinden birine oncelik YOK (esit saygi)
- Politik soylem YOK
- Mezhep/sekt ayrimciligi YOK
- Korku, catisma, travma YOK

SAYFA DAGILIMI:
Hikayeyi {page_count} sayfaya uygun yaz. Her sayfa 2-4 cumle (50-90 kelime).

CUSTOM INPUT KULLANIMI:
- {favorite_location}: Cocugun en sevdigi yeri hikayede one cikar
- {learning_focus}: Ogrenme odagi (tarih/mimari/kulturler)

Hikayede giris-gelisme-sonuc olsun, cocuk hosgoruyu ogrensin, farkliliklara saygi duysun.
Vurgulanmak istenen deger: HOSGORU ve BARIS. Kulturel zenginlik vurgula."""


# -----------------------------------------------------------------------------
# KIYAFET TASARIMLARI (Islamic Modest - Umre gibi)
# -----------------------------------------------------------------------------

OUTFIT_GIRL = """white cotton modest dress with long sleeves reaching wrists, floor-length covering ankles, white hijab headscarf covering hair completely with simple edges, comfortable beige sandals, small backpack, simple and clean appearance, no jewelry, serene look"""

OUTFIT_BOY = """white cotton tunic (knee-length kurta style), white taqiyah prayer cap on head, light beige loose-fitting pants, comfortable tan sandals, small backpack, simple and clean appearance, no patterns, humble look"""


# -----------------------------------------------------------------------------
# KULTUREL ELEMENTLER (JSON)
# -----------------------------------------------------------------------------

JERUSALEM_CULTURAL_ELEMENTS = {
    "holy_sites": [
        "Dome of the Rock (Islamic)",
        "Al-Aqsa Mosque (Islamic)",
        "Western Wall (Jewish)",
        "Church of the Holy Sepulchre (Christian)",
        "Via Dolorosa (Christian)",
        "Four Quarters of Old City"
    ],
    "architecture": [
        "Golden Dome of the Rock",
        "Ancient Jerusalem stone (golden limestone)",
        "Narrow cobblestone streets",
        "Stone arches and doorways",
        "Old City walls and gates",
        "Blue decorative tiles (Islamic)",
        "Ancient olive trees"
    ],
    "four_quarters": [
        "Muslim Quarter",
        "Jewish Quarter",
        "Christian Quarter",
        "Armenian Quarter"
    ],
    "historical_elements": [
        "Miraj Night (Prophet Muhammad, narrative only)",
        "Western Wall - remnant of Second Temple",
        "Via Dolorosa - Jesus's path (narrative only)",
        "Multi-faith coexistence",
        "Ancient city history (3000+ years)"
    ],
    "values": [
        "Tolerance (Hosgoru)",
        "Peace (Baris)",
        "Respect for diversity",
        "Multi-faith harmony",
        "Cultural appreciation"
    ],
    "atmosphere": "peaceful, historic, multi-cultural, respectful, tolerant",
    "color_palette": "golden limestone, warm amber, ancient stone beige, blue tiles, sunset gold"
}


# -----------------------------------------------------------------------------
# OZEL GIRIS ALANLARI (Custom Inputs)
# -----------------------------------------------------------------------------

JERUSALEM_CUSTOM_INPUTS = [
    {
        "key": "favorite_location",
        "label": "En Sevdigi Yer",
        "type": "select",
        "options": [
            "Altin Kubbe (Kubbetus-Sahra)",
            "Mescid-i Aksa",
            "Eski Sehir Surlari",
            "Carsi ve Sokaklari"
        ],
        "default": "Altin Kubbe (Kubbetus-Sahra)",
        "required": False,
        "help_text": "Hikayede cocugun en cok vakit gecirecegi yer"
    },
    {
        "key": "learning_focus",
        "label": "Ogrenme Odagi",
        "type": "select",
        "options": [
            "Tarihi Yapilar",
            "Kulturel Cesitlilik",
            "Mimari Guzellikler",
            "Baris Mesaji"
        ],
        "default": "Kulturel Cesitlilik",
        "required": False,
        "help_text": "Hikayede vurgulanacak ana tema"
    }
]


async def update_jerusalem_scenario():
    """Kudus Eski Sehir senaryosunu sifirdan modular prompt'larla olusturur."""
    
    print("\n" + "="*60)
    print(" KUDUS ESKI SEHIR - YENI SISTEM (SIFIRDAN)")
    print("="*60 + "\n")
    
    async with async_session_factory() as db:
        result = await db.execute(
            select(Scenario).where(
                or_(
                    Scenario.name.ilike("%Kudus%"),
                    Scenario.name.ilike("%Jerusalem%"),
                    Scenario.theme_key == "jerusalem_old_city",
                )
            )
        )
        scenario = result.scalar_one_or_none()
        
        if not scenario:
            print("[INFO] Kudus senaryosu bulunamadi. Yeni olusturuluyor...")
            scenario = Scenario(
                name="Kudus Eski Sehir Macerasi",
                is_active=True,
            )
            db.add(scenario)
        else:
            print(f"[OK] Senaryo bulundu: {scenario.name} (ID: {scenario.id})")
            print("[INFO] Eski prompt'lar SIFIRLANIYOR, yeni sistem yukleniyor...")
        
        scenario.description = (
            "3 buyuk dinin kutsal sehri Kudus'te kulturel bir yolculuk! "
            "Altin Kubbe, Mescid-i Aksa, Aglama Duvari, Kutsal Kabir. "
            "Hosgoru, baris ve kulturel zenginlik dolu bir deneyim."
        )
        scenario.thumbnail_url = "/scenarios/jerusalem_old_city.jpg"
        scenario.cover_prompt_template = JERUSALEM_COVER_PROMPT
        scenario.page_prompt_template = JERUSALEM_PAGE_PROMPT
        scenario.story_prompt_tr = JERUSALEM_STORY_PROMPT_TR
        scenario.ai_prompt_template = None
        scenario.location_en = "Jerusalem Old City"
        scenario.theme_key = "jerusalem_old_city"
        scenario.cultural_elements = JERUSALEM_CULTURAL_ELEMENTS
        scenario.custom_inputs_schema = JERUSALEM_CUSTOM_INPUTS
        scenario.outfit_girl = OUTFIT_GIRL
        scenario.outfit_boy = OUTFIT_BOY
        scenario.default_page_count = 22
        scenario.display_order = 11
        scenario.is_active = True
        scenario.marketing_badge = "Kulturel Kesif"
        scenario.age_range = "7-10 yas"
        scenario.tagline = "3 dinin kutsal sehrinde hosgoru ve baris yolculugu"
        scenario.marketing_features = [
            "Altin Kubbe ve Mescid-i Aksa",
            "Aglama Duvari ve Kutsal Kabir",
            "4 mahalle kesfi",
            "3 dine esit saygi",
            "Hosgoru ve baris degerleri",
            "Kulturel zenginlik"
        ]
        scenario.estimated_duration = "20-25 dakika okuma"
        scenario.rating = 5.0
        
        await db.commit()
        await db.refresh(scenario)
        
        print("\n[OK] GUNCELLEME TAMAMLANDI!\n")
        print("-" * 60)
        print("Guncellenen alanlar:")
        print(f"   - ID: {scenario.id}")
        print(f"   - name: {scenario.name}")
        print(f"   - cover_prompt_template: {len(JERUSALEM_COVER_PROMPT)} karakter")
        print(f"   - page_prompt_template: {len(JERUSALEM_PAGE_PROMPT)} karakter")
        print(f"   - story_prompt_tr: {len(JERUSALEM_STORY_PROMPT_TR)} karakter")
        print(f"   - default_page_count: {scenario.default_page_count}")
        print(f"   - display_order: {scenario.display_order}")
        print("-" * 60)
        print("\nKAPAK PROMPT (ilk 300 char):")
        print(JERUSALEM_COVER_PROMPT[:300] + "...")
        print("\nSAYFA PROMPT (ilk 300 char):")
        print(JERUSALEM_PAGE_PROMPT[:300] + "...")
        print("\n" + "=" * 60)
        print("Kudus Eski Sehir YENI SISTEM ile hazir!")
        print("DIKKAT: Dini danisman onayi onerilir!")
        print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(update_jerusalem_scenario())
