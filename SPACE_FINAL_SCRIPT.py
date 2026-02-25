# -*- coding: utf-8 -*-
"""
Guines Sistemi Macerasi: Gezegen Kasifleri Senaryosu - Modular Prompt Update

Bu script, Guines Sistemi Macerasi senaryosunu profesyonel, tutar

li,
uzay bilimi odakli modular prompt'larla gunceller.

Calistirma:
    cd backend
    python -m scripts.update_space_adventure_scenario
"""

import asyncio
import json

from sqlalchemy import select, or_
from app.core.database import async_session_factory
from app.models.scenario import Scenario


# SPACE_COVER_PROMPT (339 char)
SPACE_COVER_PROMPT = """Epic space scene: {scene_description}. 
Modular space station orbiting Earth. 
Friendly AI robot companion beside child. 
8 planets visible: Mercury (small), Venus (cloudy), Mars (red), Jupiter (MASSIVE, Great Red Spot), Saturn (rings), Uranus, Neptune (distant blue). 
Child TINY in vast cosmos. 
Starfield, nebula hints. 
Adventure atmosphere."""

# SPACE_PAGE_PROMPT (418 char)
SPACE_PAGE_PROMPT = """Space scene: {scene_description}. 
AI robot companion (friendly guide). 
Planets: [Mercury: cratered, extreme heat / Venus: thick clouds, volcanic / Moon: gray cratered / Mars: red surface, rovers / Jupiter: MASSIVE (1300 Earths), Great Red Spot, child TINY / Saturn: iconic rings (ice) / Uranus: ice giant, tilted / Neptune: distant blue]. 
Spacecraft, space station. 
Deep space black, stars. 
Child TINY, cosmos VAST."""

# SPACE_STORY_PROMPT_TR (blueprint + dopamin)
SPACE_STORY_PROMPT_TR = """Sen {child_name} isimli {child_age} yasinda bir cocugun GUNES SISTEMI KESFINDE yasadigi EPIK UZAY MACERASI yaziyorsun.
Cocugun yaninda {robot_name} adli yapay zeka robot arkadasi rehberlik yapiyor.

DOPAMIN MERDIVENI - 8 GEZEGEN YOLCULUGU:

**BOLUM 1 - GIRIS** (Sayfa 1-4) [role: opening]:
- Sayfa 1-2: Uzay istasyonu, robot tanisma
  Epic #1: Ilk firlatma, Dunya'dan uzaklasma
  Emotion: Heyecan
- Sayfa 3-4: Ilk gezegen goruntusu
  Dopamin ⭐⭐⭐ (baslangic)

**BOLUM 2 - IC GEZEGENLER** (Sayfa 5-8) [role: exploration]:
- Sayfa 5-6: MERKUR - en yakin, kraterleri, sicak
  Robot bilgi veriyor
- Sayfa 7-8: VENUS - bulutlari, asitli
  Endise: "Tehlikeli!" Robot korur
  Dopamin ⭐⭐⭐ (guvenlik)

**BOLUM 3 - AY + MARS** (Sayfa 9-12) [role: exploration]:
- Sayfa 9-10: AY INISI - tarihi moment!
  Epic #2: "Armstrong gibi!"
  Dopamin ⭐⭐⭐⭐
- Sayfa 11-12: MARS - kirmizi gezegen
  Epic #3: Yasam izi kesfi?
  Endise→Kesif dongusu
  Dopamin ⭐⭐⭐⭐

**BOLUM 4 - JUPITER DORUGU** (Sayfa 13-15) [role: climax]:
- Sayfa 13: JUPITER gorunusu
  SOK: "DEVASA! 1300 Dunya!"
- Sayfa 14: Kirmizi Leke yakin gecis
  Epic #4 (ZIRVE!): Dev firtina
  Endise MAX: "Firtina bizi alir mi?"
- Sayfa 15: Robot hesaplama guvenli gecis
  BASARI! Dopamin ⭐⭐⭐⭐⭐⭐
  Scale: cocuk TINY, Jupiter DEVASA

**BOLUM 5 - SATURN** (Sayfa 16-18) [role: resolution]:
- Sayfa 16-17: SATURN halkalari
  Epic #5: Buzdan halka fly-through
  Dopamin ⭐⭐⭐⭐⭐ (en ikonik!)
- Sayfa 18: Titan uydusu
  Bilimsel kesif

**BOLUM 6 - UZAK DEVLER** (Sayfa 19-21) [role: resolution]:
- Sayfa 19: URANUS - yan donuyor, gizemli
- Sayfa 20: NEPTUN - en uzak, mavi dev
  Epic #6: "En uzaga ulastik!"
  Endise: "Donebilir miyiz?"
- Sayfa 21: Robot hesaplama basarili donus plani
  Dopamin ⭐⭐⭐⭐

**BOLUM 7 - KAPANIS** (Sayfa 22) [role: conclusion]:
- Sayfa 22: Istasyona donus, Dunya gorunuyor
  ZAFER: "8 gezegeni gorduk!"
  Dopamin: Surdurulebilir mutluluk

ENDISE→BASARI DONGULERI (4 Kritik):

**Dongu 1 - Venus (Sayfa 7-8):**
- Endise: "Asit bulutlari! Tehlikeli!"
- Cozum: Robot koruyucu kalkali
- Basari: Guvenli gecis Dopamin ⭐⭐⭐

**Dongu 2 - Mars (Sayfa 11-12):**
- Endise: "Yasam yok mu? Issiz..."
- Kesif: Robot fosil iz buluyor!
- Basari: BILIMSEL KESIF Dopamin ⭐⭐⭐⭐

**Dongu 3 - Jupiter (Sayfa 13-15) - EN BUYUK:**
- Endise MAX: "DEVASA firtina! Kirmizi Leke!"
- Eylem: Robot navigasyon hesapliyor
- Basari: Guvenli yakin gecis, fotograf
- Epic odul: En buyuk gezegeni gorduk!
- Dopamin: ⭐⭐⭐⭐⭐⭐ (MAX!)

**Dongu 4 - Neptun (Sayfa 20-21):**
- Endise: "4.5 milyar km! Donebilir miyiz?"
- Cozum: Robot yakit/yorunge hesaplama
- Basari: Basarili donus Dopamin ⭐⭐⭐⭐

HIKAYE YAPISI (8 Gezegen Kesfi):

GIRIS:
- Uzay istasyonunda hazirlik
- Robot {robot_name} tanitim
- Ilk firlatma heyecani

GELISME - GEZEGEN SIRALAMASI:
1. **MERKUR:** En yakin, kraterleri, sicak (58M-430°C)
2. **VENUS:** Bulutlu, volkanik?, "ikiz gezegen"
3. **AY:** Inis, Armstrong anisi
4. **MARS:** Kirmizi yuzey, roverlar, yasam izi?
5. **JUPITER:** DEVASA (1300 Dunya), Kirmizi Leke firtinasi
6. **SATURN:** Ikonik halkalar, buzdan kopru
7. **URANUS:** Buz devi, yan donuyor
8. **NEPTUN:** En uzak, mavi dev, gizemli

EPIK MOMENTLER (6 adet):
1. Ilk firlatma - Dunya'dan uzaklasma
2. Ay inis - "Bir kucuk adim"
3. Mars yasam izi - fosil bulma
4. Jupiter Kirmizi Leke - dev firtina
5. Saturn halkalari - buzdan gecis
6. Neptun mavi dev - en uzak nokta

KAPANIS:
- Tum gezegenler tamamlandi
- Istasyona guvenli donus
- Robot ve cocuk zafer
- "8 gezegen, 1 macera!"

ROBOT ARKADASLIK ({robot_name}):
- Her sayfada robot yardim ediyor
- Navigasyon, bilgi, guvenlik
- Komik ve yardimever
- Macera'nin vazgecilmez arkadasi

ANA DEGER ve ATMOSFER:
- **MERAK:** Bilimsel merak, gezegenlerin sirlari
- **CESARET:** Uzay boslegunda cesaret
- **BILIM:** Astronomi temelleri, her gezegen farkli
- **KESIF:** Bilinmeyeni kesfetme heyecani
- NEA/ESA tarzi gercekci bilim + heyecan dengesi

Hikayede giris-gelisme-sonuc olsun, cocuk heyeclansin, kesfetsin, endiselensin ve basarsin. 
Vurgulanmak istenen deger: {value_name}. Dopamini yonet, cekici bir hikaye olsun."""

OUTFIT_GIRL = """{
"outfit_girl": "white and silver NEA-style astronaut suit with blue chest patch and mission insignia, puffy insulated arms and legs with subtle gray seam lines, clear curved helmet with gold-tinted visor, white EVA gloves, sturdy white space boots with dark gray soles, compact life support pack on back"
}"""

OUTFIT_BOY = """{
"outfit_boy": "white and silver NEA-style astronaut suit with red chest stripe and mission patch, puffy insulated arms and legs with subtle gray seam lines, clear curved helmet with gold-tinted visor, white EVA gloves, sturdy white space boots with dark gray soles, compact life support pack on back"
}"""

SPACE_CULTURAL_ELEMENTS = {
    "planets": [
        "Mercury - cratered, small, extreme temperatures",
        "Venus - cloudy, volcanic?, hot",
        "Moon - Earth's satellite, cratered, gray",
        "Mars - red surface, rovers, exploration",
        "Jupiter - gas giant, Great Red Spot",
        "Saturn - iconic rings",
        "Uranus - ice giant, blue-green, tilted",
        "Neptune - distant ice giant"
    ],
    "scientific_facts": [
        "Solar system has 8 planets",
        "Jupiter is largest, could fit 1300 Earths",
        "Saturn's rings are ice and rock",
        "Mars has Olympus Mons, largest volcano",
        "Moon orbits Earth every 27 days",
        "NEA missions explore space"
    ],
    "space_environment": [
        "zero-gravity floating",
        "space station interior",
        "lunar surface gray regolith",
        "martian red landscapes",
        "deep space black",
        "starfield and nebula"
    ],
    "robot_companion": [
        "friendly AI helper robot",
        "navigator and scientist",
        "compact, non-threatening",
        "trusted sidekick"
    ]
}

SPACE_CUSTOM_INPUTS = [
    {
        "key": "favorite_planet",
        "label": "En Sevdigi Gezegen",
        "type": "select",
        "options": ["Mars", "Jupiter", "Saturn", "Neptune"],
        "default": "Mars",
        "required": False,
        "help_text": "Hikayede en cok vakit gecirilecek gezegen"
    },
    {
        "key": "robot_name",
        "label": "Robot Arkadasin Adi",
        "type": "select",
        "options": ["NOVA", "COSMO", "STELLA", "ORBIT"],
        "default": "NOVA",
        "required": False,
        "help_text": "Cocugun yanindaki robot arkadasinin adi"
    }
]


async def update_space_adventure_scenario():
    """Gunes Sistemi Macerasi senaryosunu modular master prompt'larla gunceller."""

    print("\n" + "=" * 60)
    print(" GUNES SISTEMI MACERASI - MODULAR PROMPT UPDATE")
    print("=" * 60 + "\n")

    async with async_session_factory() as db:
        result = await db.execute(
            select(Scenario).where(
                or_(
                    Scenario.name.ilike("%Gunes Sistemi%"),
                    Scenario.name.ilike("%Uzay%"),
                    Scenario.theme_key == "solar_systems_space",
                )
            )
        )
        scenario = result.scalar_one_or_none()

        if not scenario:
            print("[INFO] Gunes Sistemi senaryosu bulunamadi. Yeni olusturuluyor...")
            scenario = Scenario(
                name="Gunes Sistemi Macerasi: Gezegen Kasifleri",
                is_active=True,
            )
            db.add(scenario)
        else:
            print(f"[OK] Senaryo bulundu: {scenario.name} (ID: {scenario.id})")

        scenario.description = (
            "Uzay istasyonundan Gunes Sistemi turuna cikan, 8 gezegeni kesfeden, "
            "robot arkadasiyla bilimsel ve heyecanli macera yasan bir cocuk hikayesi. "
            "Merkur'den Neptun'e macera dolu bir yolculuk."
        )
        scenario.thumbnail_url = "/scenarios/space_adventure.jpg"
        scenario.cover_prompt_template = SPACE_COVER_PROMPT
        scenario.page_prompt_template = SPACE_PAGE_PROMPT
        scenario.story_prompt_tr = SPACE_STORY_PROMPT_TR
        scenario.ai_prompt_template = None
        scenario.location_en = "Solar System"
        scenario.theme_key = "solar_systems_space"
        scenario.cultural_elements = SPACE_CULTURAL_ELEMENTS
        scenario.custom_inputs_schema = SPACE_CUSTOM_INPUTS
        scenario.outfit_girl = OUTFIT_GIRL
        scenario.outfit_boy = OUTFIT_BOY
        scenario.default_page_count = 22
        scenario.display_order = 15
        scenario.is_active = True
        scenario.marketing_badge = "Bilimsel Kesif"
        scenario.age_range = "6-10 yas"
        scenario.tagline = "Gunes Sistemi'nde 8 gezegeni kesfet! NEA tarzi bilimsel macera"
        scenario.marketing_features = [
            "8 gezegeni kesfet",
            "Robot arkadasla bilimsel macera",
            "Mars'a inis",
            "Jupiter'in firtinasina tanik",
            "Saturn'un halkalarini gor",
            "NEA tarzi gercekci uzay deneyimi",
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
        print(f"   - cover_prompt_template: {len(SPACE_COVER_PROMPT)} karakter")
        print(f"   - page_prompt_template: {len(SPACE_PAGE_PROMPT)} karakter")
        print(f"   - story_prompt_tr: {len(SPACE_STORY_PROMPT_TR)} karakter")
        print(f"   - default_page_count: {scenario.default_page_count}")
        print(f"   - display_order: {scenario.display_order}")
        print("-" * 60)
        print("\nKAPAK PROMPT (ilk 300 char):")
        print(SPACE_COVER_PROMPT[:300] + "...")
        print("\nSAYFA PROMPT (ilk 300 char):")
        print(SPACE_PAGE_PROMPT[:300] + "...")
        print("\n" + "=" * 60)
        print("Gunes Sistemi Macerasi modular prompt'lara sahip!")
        print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(update_space_adventure_scenario())
