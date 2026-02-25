"""
Sultanahmet Camii (Mavi Camii) MacerasÄ± Senaryosu - Master Prompt OluÅŸturma

Bu script, Sultanahmet Camii MacerasÄ± senaryosunu profesyonel, tutarlÄ± ve
kÃ¼ltÃ¼rel aÃ§Ä±dan zengin prompt'larla oluÅŸturur veya gÃ¼nceller.

Sultanahmet Camii (Mavi Camii): 1609-1616, I. Ahmed, Mimar SedefkÃ¢r Mehmed AÄŸa.
6 minare, 23,5m Ã§aplÄ± merkezi kubbe (43m yÃ¼kseklik), 20.000+ mavi Ä°znik Ã§inisi,
200+ renkli cam pencere. UNESCO Tarihi YarÄ±mada (1985). KarÅŸÄ±sÄ±nda Ayasofya.

Ã–NEMLÄ° - PuLID UYUMLULUK:
- Fiziksel Ã¶zellikler YASAK (saÃ§, gÃ¶z, ten rengi) - PuLID fotoÄŸraftan alÄ±yor
- {clothing_description} zorunlu - kÄ±yafet tutarlÄ±lÄ±ÄŸÄ± iÃ§in
- Sahne aÃ§Ä±klamalarÄ± ACTION-ONLY - stil StyleConfig'den geliyor
- YÃ¼z kimliÄŸi korunmalÄ± - "Bu kesin benim Ã§ocuÄŸum" hissi

Ã‡alÄ±ÅŸtÄ±rma:
    cd backend
    python -m scripts.create_sultanahmet_scenario
"""

import asyncio
import json
import os
import sys
import uuid

# Ensure /app (or parent dir) is in Python path for direct script execution
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import select
from app.core.database import async_session_factory
from app.models.scenario import Scenario


# =============================================================================
# SULTANAHMET CAMÄ°Ä° (MAVÄ° CAMÄ°Ä°) MACERASI - MASTER PROMPT TEMPLATES
# =============================================================================

# -----------------------------------------------------------------------------
# KAPAK PROMPT TEMPLATE
# -----------------------------------------------------------------------------

SULTANAHMET_COVER_PROMPT = """A breathtaking children's book cover illustration.

SCENE COMPOSITION:
A young child {scene_description}, standing in awe in the grand courtyard of the Sultanahmet Mosque (Blue Mosque) in Istanbul, Turkey, gazing up at the magnificent cascade of domes and six slender minarets reaching toward the sky.

ICONIC BACKGROUND ELEMENTS (include 2-3 key details):
- The Blue Mosque's majestic exterior: a grand cascade of domes â€” the large central dome (23.5m diameter, 43m high) flanked by semi-domes and smaller domes creating a pyramidal silhouette
- Six elegant, pencil-shaped minarets with ÅŸerefe (balcony) details, soaring into the sky
- The arcaded courtyard (avlu) with its elegant domed portico, central ablution fountain
- Warm Marmara limestone and white marble exterior glowing in golden light
- Lush courtyard gardens with trimmed hedges and historic plane trees
- Glimpse of the Istanbul skyline â€” distant Bosphorus waters, Ayasofya's dome visible nearby
- Flocks of pigeons taking flight in the courtyard, adding life and motion

LIGHTING & ATMOSPHERE:
- Warm golden hour light bathing the mosque's domes and minarets in amber glow
- A dramatic sky with scattered clouds lit by the setting sun
- The warm cream-white stone contrasting with the deep blue sky
- A feeling of grandeur, serenity, and 400 years of history
- Color palette: warm cream stone, sky blue, golden amber, dome grey-blue, courtyard green, minaret white

CLOTHING:
The child is wearing {clothing_description}.

STYLE:
{visual_style}.

COMPOSITION REQUIREMENTS:
- Professional book cover design with clear title space at the top
- Child positioned in lower third, in the courtyard looking up at the towering domes and minarets
- Epic cinematic scale emphasizing the mosque's monumental size and the dome cascade
- Minarets and dome silhouette framing the scene with vertical grandeur"""


# -----------------------------------------------------------------------------
# Ä°Ã‡ SAYFA PROMPT TEMPLATE
# -----------------------------------------------------------------------------

SULTANAHMET_PAGE_PROMPT = """A stunning children's book illustration set in and around the Sultanahmet Mosque (Blue Mosque) and the historic Sultanahmet Square in Istanbul, Turkey.

SCENE ACTION:
A young child {scene_description}.

AUTHENTIC SULTANAHMET SETTING (vary these elements per scene):
- BLUE MOSQUE INTERIOR: Breathtaking interior space with over 20,000 handmade blue Ä°znik tiles covering the upper walls â€” intricate tulip, carnation, cypress, and geometric patterns in cobalt blue, turquoise, white, and green; massive dome ceiling painted with floral arabesques; 200+ stained glass windows flooding the space with colored light; thick red carpet covering the floor; elephant-foot columns supporting massive arches
- DOME CASCADE EXTERIOR: The iconic silhouette of the central dome, half-domes, and quarter-domes stepping down in a harmonious pyramid; six minarets with three balconies each; warm Marmara stone exterior
- COURTYARD (AVLU): Elegant hexagonal ablution fountain under a small dome; 26 domed portico columns surrounding the courtyard; chain-link entrance where even the Sultan had to bow; historic plane trees and rose gardens
- Ä°ZNÄ°K TILE WORKSHOP: Artisan workshop showing how the famous tiles were made â€” hand-painted cobalt blue and turquoise patterns, tulip and carnation motifs, kiln firing, ceramic glazing process
- SULTANAHMET SQUARE: The Hippodrome area â€” the Egyptian Obelisk (DikilitaÅŸ, 3,500 years old), the Serpent Column (YÄ±lanlÄ± SÃ¼tun, from ancient Greece), the German Fountain (Alman Ã‡eÅŸmesi) with golden mosaic ceiling
- AYASOFYA PANORAMA: View of Hagia Sophia's massive dome and minarets from the square, creating the iconic Istanbul dual-silhouette with the Blue Mosque
- ARASTA BAZAAR: The historic market street beside the mosque â€” colorful ceramic shops, Turkish lamp stores, carpet merchants, tea vendors, mosaic art galleries
- ISTANBUL SKYLINE: Bosphorus waters visible in the distance, ferry boats crossing, seagulls soaring, the historic peninsula stretching along the Golden Horn

ARCHITECTURAL & HISTORICAL ACCURACY:
- Classical Ottoman architecture by SedefkÃ¢r Mehmed AÄŸa (student of Mimar Sinan)
- Over 20,000 Ä°znik tiles in 50+ different tulip patterns â€” cobalt blue dominant
- 260 windows (original glass by Ä°brahim the Drunkard, now replaced with modern versions)
- Central dome: 23.5m diameter, 43m high, decorated with floral arabesques
- Four massive "elephant-foot" (fil ayaÄŸÄ±) pillars supporting the dome, 5m in diameter each
- Built 1609-1616 by Sultan Ahmed I

LIGHTING OPTIONS (match to scene mood):
- Golden morning light streaming through 200+ stained glass windows, projecting colored patterns on the carpet
- Bright midday with blue sky and crisp dome shadows in the courtyard
- Warm sunset gilding the dome cascade and minarets in amber-rose light
- Interior lamplight from the grand chandelier circle illuminating blue tiles with warm glow

CLOTHING:
The child is wearing {clothing_description}.

STYLE:
{visual_style}.

COMPOSITION:
- Clear focal point on the child in the middle-ground
- Rich, detailed Sultanahmet background with Ottoman architectural splendor
- Space at bottom for text overlay (25% of image height)
- Vibrant color palette: Ä°znik cobalt blue, turquoise, warm cream stone, golden amber, stained glass jewel tones"""


# -----------------------------------------------------------------------------
# AI HÄ°KAYE ÃœRETÄ°M PROMPTU (Gemini Pass-1 iÃ§in)
# -----------------------------------------------------------------------------

SULTANAHMET_STORY_PROMPT_TR = """Sen Ã¶dÃ¼llÃ¼ Ã§ocuk kitabÄ± yazarÄ± ve Ä°stanbul tarihi/OsmanlÄ± mimarisi uzmanÄ±sÄ±n.
Kahraman, yaÅŸ ve eÄŸitsel deÄŸerler yukarÄ±da verilmiÅŸtir. GÃ¶revin: Sultanahmet MeydanÄ± ve Mavi Camii Ã§evresinde geÃ§en bÃ¼yÃ¼lÃ¼ bir macera yazmak.

ğŸ“ SULTANAHMET â€” KULLANILACAK KÃœLTÃœREL MEKANLAR (hikayeye en az 6 tanesini entegre et):
1. Mavi Camii iÃ§ mekÃ¢nÄ± â€” 20.000+ el yapÄ±mÄ± mavi Ä°znik Ã§inisi, lale-karanfil-servi desenleri, devasa kubbe, renkli vitray pencerelerden sÃ¼zÃ¼len Ä±ÅŸÄ±k huzmeleri, fil ayaÄŸÄ± sÃ¼tunlarÄ±
2. Kubbe kaskadÄ± â€” dÄ±ÅŸarÄ±dan merkezÃ® kubbe, yarÄ±m kubbeler, Ã§eyrek kubbelerin piramit silÃ¼eti, altÄ± zarif minare
3. Avlu â€” altÄ±gen ÅŸadÄ±rvan, 26 kubbeli revak sÃ¼tunu, zincirli giriÅŸ kapÄ±sÄ±, tarihi Ã§Ä±nar aÄŸaÃ§larÄ±
4. Ä°znik Ã§ini atÃ¶lyesi â€” usta Ã§inicinin kobalt mavisi ve turkuaz desenleri elle boyamasÄ±, lale motifleri, fÄ±rÄ±nlama sÃ¼reci
5. Sultanahmet MeydanÄ± (Hipodrom) â€” DikilitaÅŸ (3.500 yaÅŸÄ±nda MÄ±sÄ±r obelisk), YÄ±lanlÄ± SÃ¼tun (antik Yunan), Alman Ã‡eÅŸmesi (altÄ±n mozaikli tavan)
6. Ayasofya manzarasÄ± â€” meydandan Ayasofya'nÄ±n devasa kubbesi ve minareleri, iki yapÄ±nÄ±n ikonik ikili silÃ¼eti
7. Arasta Ã‡arÅŸÄ±sÄ± â€” caminin yanÄ±ndaki tarihi Ã§arÅŸÄ±, renkli seramik dÃ¼kkanlarÄ±, TÃ¼rk lambalarÄ±, halÄ± tÃ¼ccarlarÄ±, Ã§ay ikramÄ±
8. Renkli vitray pencereler â€” 200'den fazla renkli cam pencere, Ä°brahim SarhoÅŸ'un orijinal tasarÄ±mlarÄ±, Ä±ÅŸÄ±k ve renk oyunlarÄ±
9. Kubbe altÄ± â€” devasa kubbenin altÄ±nda durarak yukarÄ± bakmak, Ã§iÃ§ekli arabesk sÃ¼slemeler, sonsuzluk hissi
10. Ä°stanbul silueti â€” BoÄŸaz manzarasÄ±, vapur geÃ§iÅŸleri, martÄ±lar, Tarihi YarÄ±mada panoramasÄ±

ğŸ­ YARDIMCI KARAKTER (en az biri hikayede olsun):
Bilge MartÄ± (Ä°stanbul'un semalarÄ±ndan her ÅŸeyi gÃ¶ren, BoÄŸaz'Ä±n hikayesini bilen), MeraklÄ± GÃ¼vercin (avlunun sakinlerinden, caminin her kÃ¶ÅŸesini bilen),
Renkli Kelebek (vitray pencerelerden sÃ¼zÃ¼len Ä±ÅŸÄ±ktan doÄŸan bÃ¼yÃ¼lÃ¼ varlÄ±k), KonuÅŸan Ã‡ini (Ä°znik Ã§inisindeki lale deseninden canlanan, 400 yÄ±llÄ±k hikayeler anlatan)
veya NeÅŸeli Kedi (Ä°stanbul'un Ã¼nlÃ¼ sokak kedilerinden, Ã§arÅŸÄ±nÄ±n sÄ±rlarÄ±nÄ± bilen).
Karakter, OsmanlÄ± dÃ¶neminden veya Ä°stanbul'un bÃ¼yÃ¼lÃ¼ atmosferinden "uyanmÄ±ÅŸ" olabilir.

âš¡ Ã–NEMLI â€” BU BÄ°R GEZÄ° REHBERÄ° DEÄÄ°L, BÄ°R MACERA HÄ°KAYESÄ°!
Sultanahmet mekanlarÄ± ARKA PLAN olarak kullan. Hikayenin motorunu MEKANLAR DEÄÄ°L,
Ã§ocuÄŸun Ä°Ã‡ YOLCULUÄU ve eÄŸitsel deÄŸerler oluÅŸtursun.

âŒ YANLIÅ: "Ece camiyi gÃ¶rdÃ¼. Sonra Ã§inilere baktÄ±. Sonra meydana Ã§Ä±ktÄ±."
âœ… DOÄRU: Ã‡ocuÄŸun bir SORUNU/ZAYIFLIÄI var. Bu sorun Sultanahmet'in bÃ¼yÃ¼lÃ¼ mekanlarÄ±nda
bir MACERA'ya dÃ¶nÃ¼ÅŸÃ¼yor. Ä°znik Ã§inilerindeki lale deseni "canlanÄ±yor", vitray pencerelerden
sÃ¼zÃ¼len renkli Ä±ÅŸÄ±klar sihirli bir dÃ¼nya aÃ§Ä±yor, 400 yÄ±llÄ±k Ã§ini ustasÄ± Ã§ocuÄŸa
sabÄ±r ve Ã¶zenin deÄŸerini fÄ±sÄ±ldÄ±yor. Ã‡ocuk sanatÄ±n ve tarihin bÃ¼yÃ¼sÃ¼nÃ¼ keÅŸfederken KENDÄ°NÄ° keÅŸfediyor.

ğŸ”‘ EÄÄ°TSEL DEÄER ENTEGRASYONU:
SeÃ§ilen eÄŸitsel deÄŸer hikayenin OLAY Ã–RGÃœSÃœNÃœ belirlemeli:
- SabÄ±r seÃ§ildiyse â†’ Ã§ini ustasÄ± gibi sabÄ±rla Ã§alÄ±ÅŸmayÄ± Ã¶ÄŸrensin, acele edince desen bozulsun
- GÃ¼zellik/estetik seÃ§ildiyse â†’ Ã§ocuk sanatÄ±n gÃ¼cÃ¼nÃ¼ keÅŸfetsin, renklerin ve desenlerin anlamÄ±nÄ± Ã¶ÄŸrensin
- Cesaret seÃ§ildiyse â†’ kubbenin tepesine Ã§Ä±kmak veya gizli bir geÃ§ide girmek gereksin
- Merak seÃ§ildiyse â†’ vitray penceredeki bir ipucu Ã§ocuÄŸu kayÄ±p ustanÄ±n sÄ±rrÄ±na gÃ¶tÃ¼rsÃ¼n
- PaylaÅŸmak seÃ§ildiyse â†’ keÅŸfettiÄŸi gÃ¼zelliÄŸi baÅŸkalarÄ±yla paylaÅŸmanÄ±n Ã¶nemini anlasÄ±n
DeÄŸer sadece "sÃ¶ylenmesin", Ã§ocuk YAÅAYARAK Ã¶ÄŸrensin!

âš ï¸ Ã–NEMLÄ° KISITLAMA:
Hikayede DÄ°NÄ° RÄ°TÃœEL, Ä°BADET SAHNESÄ° veya DÄ°NÄ° Ã–ÄRETÄ° OLMAMALIDIR.
Camii "muhteÅŸem bir mimari ve sanat eseri" olarak sunulsun.
Ä°znik Ã§inileri SANAT ve ZANAAT perspektifinden, dini obje olarak DEÄÄ°L.
Kubbe ve minareler MÄ°MARÄ° BAÅARI olarak, dini sembol olarak DEÄÄ°L.
Ã‡ocuk mimariyi, sanatÄ±, Ã§ini ustalarÄ±nÄ±n zanaatÄ±nÄ± ve Ä°stanbul'un tarihsel zenginliÄŸini keÅŸfetsin.

ğŸ¨ SAHNE AÃ‡IKLAMASI KURALLARI (Pass-2 iÃ§in ipucu):
Her sahne iÃ§in spesifik Sultanahmet lokasyonu ve mimari/sanatsal detay kullan.
Ã–rn: "Kubbenin altÄ±nda 20.000 mavi Ã§iniye bakarken", "Avludaki ÅŸadÄ±rvanÄ±n yanÄ±nda gÃ¼vercinlerle",
"Arasta Ã‡arÅŸÄ±sÄ±'nda renkli TÃ¼rk lambalarÄ±nÄ±n arasÄ±nda", "Vitray pencereden sÃ¼zÃ¼len mavi Ä±ÅŸÄ±ÄŸÄ±n altÄ±nda",
"Meydandaki 3.500 yaÅŸÄ±ndaki DikilitaÅŸ'Ä±n Ã¶nÃ¼nde".
Genel ifadelerden kaÃ§Ä±n ("camide" yerine somut yer adÄ± ve detay kullan)."""


# -----------------------------------------------------------------------------
# LOKASYON KISITLAMALARI
# -----------------------------------------------------------------------------

SULTANAHMET_LOCATION_CONSTRAINTS = """Sultanahmet Mosque (Blue Mosque) and Square iconic elements (include 1-2 relevant details depending on the scene):
- Ottoman dome cascade silhouette with six minarets
- Blue Ä°znik tiles with tulip, carnation, and geometric patterns (cobalt blue, turquoise, white)
- Stained glass windows projecting colored light beams
- Sultanahmet Square historic monuments (Obelisk, Serpent Column)
- Istanbul skyline with Bosphorus, Ayasofya visible in distance"""


# -----------------------------------------------------------------------------
# KÃœLTÃœREL ELEMENTLER (JSON)
# -----------------------------------------------------------------------------

SULTANAHMET_CULTURAL_ELEMENTS = {
    "primary_landmarks": [
        "Blue Mosque interior (20,000+ Ä°znik tiles, massive dome, stained glass)",
        "dome cascade exterior with six minarets",
        "arcaded courtyard with hexagonal fountain",
        "Sultanahmet Square / Hippodrome (Egyptian Obelisk, Serpent Column)",
        "Ayasofya (Hagia Sophia) panoramic view from the square"
    ],
    "secondary_elements": [
        "Arasta Bazaar (historic market beside the mosque)",
        "Ä°znik tile workshop (artisan ceramic painting)",
        "German Fountain with golden mosaic ceiling",
        "elephant-foot pillars inside the mosque",
        "Istanbul Bosphorus and historic peninsula skyline"
    ],
    "cultural_items": [
        "Ä°znik tiles with cobalt blue tulip and carnation motifs",
        "stained glass windows (200+ colored panels)",
        "Ottoman calligraphy roundels (hat levhalarÄ±)",
        "Turkish lamps and lanterns (Arasta Bazaar)",
        "traditional Turkish ceramics, carpets, and tea glasses"
    ],
    "color_palette": "Ä°znik cobalt blue, turquoise, warm cream stone, golden amber, stained glass jewel tones, minaret white, dome grey-blue",
    "atmosphere": "majestic, serene, awe-inspiring, artistically rich, historically grand, Istanbul magic",
    "time_periods": [
        "golden morning with colored light through stained glass windows",
        "bright midday with blue sky and dome shadows in courtyard",
        "amber sunset gilding the dome cascade and minarets",
        "warm interior lamplight illuminating blue tiles"
    ]
}


# -----------------------------------------------------------------------------
# Ã–ZEL GÄ°RÄ°Å ALANLARI (Custom Inputs)
# -----------------------------------------------------------------------------

SULTANAHMET_CUSTOM_INPUTS = [
    {
        "key": "favorite_element",
        "label": "En SevdiÄŸi Sanat DetayÄ±",
        "type": "select",
        "options": ["Mavi Ä°znik Ã‡inileri", "Renkli Vitray Pencereler", "Dev Kubbe", "Lale Desenleri"],
        "default": "Mavi Ä°znik Ã‡inileri",
        "required": False,
        "help_text": "Hikayenin en bÃ¼yÃ¼lÃ¼ sahnesi bu sanat eseri etrafÄ±nda geÃ§ecek"
    },
    {
        "key": "special_discovery",
        "label": "KeÅŸfetmek Ä°stediÄŸi Åey",
        "type": "select",
        "options": ["KayÄ±p Ã‡ini UstasÄ±nÄ±n SÄ±rrÄ±", "Gizli Kubbe OdasÄ±", "Sihirli Vitray Renkleri", "Antik Hipodrom Hazinesi"],
        "default": "KayÄ±p Ã‡ini UstasÄ±nÄ±n SÄ±rrÄ±",
        "required": False,
        "help_text": "Hikayede Ã§ocuÄŸun keÅŸfedeceÄŸi bÃ¼yÃ¼k sÄ±r"
    },
    {
        "key": "travel_companion",
        "label": "Yol ArkadaÅŸÄ±",
        "type": "select",
        "options": ["Bilge MartÄ±", "MeraklÄ± GÃ¼vercin", "Renkli Kelebek", "NeÅŸeli Kedi"],
        "default": "NeÅŸeli Kedi",
        "required": False,
        "help_text": "Sultanahmet'te Ã§ocuÄŸa eÅŸlik edecek Ä°stanbul arkadaÅŸÄ±"
    }
]


async def create_sultanahmet_scenario():
    """Sultanahmet Camii (Mavi Camii) MacerasÄ± senaryosunu oluÅŸtur veya gÃ¼ncelle."""

    print("\n" + "=" * 70)
    print("SULTANAHMET CAMÄ°Ä° (MAVÄ° CAMÄ°Ä°) MACERASI SENARYO OLUÅTURMA")
    print("Master Prompts - PuLID Optimized - Ottoman Architectural Wonder")
    print("=" * 70 + "\n")

    async with async_session_factory() as db:
        # Mevcut senaryoyu kontrol et
        result = await db.execute(
            select(Scenario).where(Scenario.name.ilike("%Sultanahmet%"))
        )
        existing = result.scalar_one_or_none()

        if existing:
            print(f"[INFO] Mevcut senaryo bulundu, gÃ¼ncelleniyor... (ID: {existing.id})")
            scenario = existing
        else:
            print("[INFO] Yeni senaryo oluÅŸturuluyor...")
            scenario = Scenario(id=uuid.uuid4())
            db.add(scenario)

        # TÃ¼m alanlarÄ± gÃ¼ncelle
        scenario.name = "Sultanahmet Camii MacerasÄ±"
        scenario.description = (
            "Ä°stanbul'un kalbinde 20.000 mavi Ä°znik Ã§inisiyle sÃ¼slÃ¼ Mavi Camii'de bÃ¼yÃ¼lÃ¼ bir macera! "
            "Vitray pencerelerden sÃ¼zÃ¼len renkli Ä±ÅŸÄ±klar, canlanan lale desenleri ve 400 yÄ±llÄ±k Ã§ini ustasÄ±nÄ±n sÄ±rrÄ±. "
            "Sultanahmet MeydanÄ±'nda sanat ve tarihin bÃ¼yÃ¼sÃ¼nÃ¼ keÅŸfet!"
        )
        scenario.thumbnail_url = "/scenarios/sultanahmet.jpg"
        scenario.cover_prompt_template = SULTANAHMET_COVER_PROMPT
        scenario.page_prompt_template = SULTANAHMET_PAGE_PROMPT
        # V2: story_prompt_tr Ã¶ncelikli
        scenario.story_prompt_tr = SULTANAHMET_STORY_PROMPT_TR
        scenario.ai_prompt_template = None  # V2 story_prompt_tr kullanÄ±yor
        scenario.location_constraints = SULTANAHMET_LOCATION_CONSTRAINTS
        scenario.location_en = "Sultanahmet Mosque (Blue Mosque)"
        scenario.cultural_elements = SULTANAHMET_CULTURAL_ELEMENTS
        scenario.theme_key = "sultanahmet"
        scenario.custom_inputs_schema = SULTANAHMET_CUSTOM_INPUTS
        scenario.is_active = True
        scenario.display_order = 7

        await db.commit()

        print("\n[OK] SULTANAHMET CAMÄ°Ä° MACERASI OLUÅTURULDU!\n")
        print("-" * 70)
        print("Senaryo DetaylarÄ±:")
        print(f"  - name: {scenario.name}")
        print(f"  - description: {len(scenario.description)} karakter")
        print(f"  - cover_prompt_template: {len(SULTANAHMET_COVER_PROMPT)} karakter")
        print(f"  - page_prompt_template: {len(SULTANAHMET_PAGE_PROMPT)} karakter")
        print(f"  - story_prompt_tr: {len(SULTANAHMET_STORY_PROMPT_TR)} karakter")
        print("  - location_en: Sultanahmet Mosque (Blue Mosque)")
        print(f"  - location_constraints: {len(SULTANAHMET_LOCATION_CONSTRAINTS)} karakter")
        print(f"  - cultural_elements: {len(json.dumps(SULTANAHMET_CULTURAL_ELEMENTS))} karakter (JSON)")
        print("  - theme_key: sultanahmet")
        print(f"  - custom_inputs_schema: {len(SULTANAHMET_CUSTOM_INPUTS)} Ã¶zel alan")
        print("-" * 70)

        # Custom inputs preview
        print("\nÃ–ZEL GÄ°RÄ°Å ALANLARI:")
        for inp in SULTANAHMET_CUSTOM_INPUTS:
            print(f"  - {inp['label']}: {', '.join(inp['options'][:3])}...")

        # Prompt previews
        print("\n" + "=" * 70)
        print("KAPAK PROMPT Ã–NÄ°ZLEME (ilk 500 karakter):")
        print("-" * 70)
        print(SULTANAHMET_COVER_PROMPT[:500] + "...")

        print("\n" + "=" * 70)
        print("SAYFA PROMPT Ã–NÄ°ZLEME (ilk 500 karakter):")
        print("-" * 70)
        print(SULTANAHMET_PAGE_PROMPT[:500] + "...")

        print("\n" + "=" * 70)
        print("STORY_PROMPT_TR Ã–NÄ°ZLEME (ilk 500 karakter):")
        print("-" * 70)
        print(SULTANAHMET_STORY_PROMPT_TR[:500] + "...")

        print("\n" + "=" * 70)
        print("Sultanahmet Camii MacerasÄ± senaryosu hazÄ±r!")
        print("Ã‡ocuklar artÄ±k Ä°stanbul'un mavi Ã§inili harikasÄ±nÄ± keÅŸfedebilir!")
        print("=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(create_sultanahmet_scenario())


