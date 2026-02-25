"""
Galata Kulesi MacerasÄ± Senaryosu - Master Prompt OluÅŸturma

Bu script, Galata Kulesi MacerasÄ± senaryosunu profesyonel, tutarlÄ± ve
kÃ¼ltÃ¼rel aÃ§Ä±dan zengin prompt'larla oluÅŸturur veya gÃ¼nceller.

Galata Kulesi: 1348 Ceneviz inÅŸasÄ±, BeyoÄŸlu/Ä°stanbul, 67 metre yÃ¼kseklik.
Silindirik taÅŸ gÃ¶vde, konik Ã§atÄ±, 9 kat, 360Â° seyir terasÄ±.
HezÃ¢rfen Ahmed Ã‡elebi'nin uÃ§uÅŸ efsanesi. UNESCO GeÃ§ici Listesi.
HaliÃ§, BoÄŸaziÃ§i ve Tarihi YarÄ±mada panoramasÄ±.

Ã–NEMLÄ° - PuLID UYUMLULUK:
- Fiziksel Ã¶zellikler YASAK (saÃ§, gÃ¶z, ten rengi) - PuLID fotoÄŸraftan alÄ±yor
- {clothing_description} zorunlu - kÄ±yafet tutarlÄ±lÄ±ÄŸÄ± iÃ§in
- Sahne aÃ§Ä±klamalarÄ± ACTION-ONLY - stil StyleConfig'den geliyor
- YÃ¼z kimliÄŸi korunmalÄ± - "Bu kesin benim Ã§ocuÄŸum" hissi

Ã‡alÄ±ÅŸtÄ±rma:
    cd backend
    python -m scripts.create_galata_scenario
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
# GALATA KULESÄ° MACERASI - MASTER PROMPT TEMPLATES
# =============================================================================

GALATA_COVER_PROMPT = """A breathtaking children's book cover illustration.

SCENE COMPOSITION:
A young child {scene_description}, standing on the famous 360-degree observation balcony of the Galata Tower in Istanbul, Turkey, with the wind in their clothes and the entire city spread out below.

ICONIC BACKGROUND ELEMENTS (include 2-3 key details):
- The Galata Tower's distinctive cylindrical stone body and conical cap roof visible below the balcony railing â€” warm grey Genoese stone, Gothic architectural details
- A sweeping 360Â° panorama of Istanbul: the Golden Horn (HaliÃ§) waterway sparkling below, the Bosphorus strait with ferries and boats, the Historic Peninsula skyline with domes and minarets
- The Galata Bridge spanning the Golden Horn with tiny fishermen silhouettes, colorful ferry boats passing underneath
- The rooftops of BeyoÄŸlu/KarakÃ¶y cascading down the hillside â€” terracotta and grey tile roofs, pastel-colored Ottoman-era buildings
- Flocks of seagulls soaring at eye level around the tower
- Distant silhouette of the Asian side of Istanbul across the Bosphorus

LIGHTING & ATMOSPHERE:
- Magical golden hour sunset light painting the city in warm amber and rose tones
- The Bosphorus and Golden Horn reflecting the sunset colors like liquid gold
- A vast dramatic sky with scattered clouds lit in orange, pink, and purple
- The feeling of flying â€” standing at 67 meters, the whole city at your feet
- Color palette: warm stone grey, golden amber, Bosphorus blue-green, sunset rose, terracotta rooftops

CLOTHING:
The child is wearing {clothing_description}.

STYLE:
{visual_style}.

COMPOSITION REQUIREMENTS:
- Professional book cover design with clear title space at the top
- Child positioned in lower third, leaning on the balcony railing looking out at the panorama
- Epic cinematic scale showing the vastness of Istanbul from the tower's vantage point
- The conical tower cap and seagulls framing the upper portion of the scene"""


GALATA_PAGE_PROMPT = """A stunning children's book illustration set in and around the iconic Galata Tower and the historic Galata/KarakÃ¶y district of Istanbul, Turkey.

SCENE ACTION:
A young child {scene_description}.

AUTHENTIC GALATA TOWER SETTING (vary these elements per scene):
- OBSERVATION TERRACE: The famous 360Â° balcony at the top of the 67-meter tower â€” panoramic views of Istanbul in every direction, stone balustrade, seagulls flying at eye level, the wind-swept feeling of being above the entire city
- TOWER INTERIOR: Nine floors of cylindrical stone chambers connected by a spiral staircase; museum displays of Ottoman, Byzantine, and Genoese artifacts; thick medieval stone walls (3.7m at base); dramatic upward view of the conical ceiling
- SPIRAL STAIRCASE: The narrow medieval stone spiral staircase winding upward through the tower's core â€” worn stone steps, torch-lit atmosphere, small arched windows with glimpses of the city at each level
- HEZÃ‚RFEN AHMED Ã‡ELEBÄ° LEGEND: Scenes evoking the 17th-century Ottoman aviator who legendarily flew from Galata Tower to ÃœskÃ¼dar on artificial wings â€” sense of daring, invention, and the dream of flight
- GALATA BRIDGE & GOLDEN HORN: The historic bridge spanning the Golden Horn waterway below â€” fishermen lining the railings, colorful ferry boats, fish restaurants underneath, bustling waterfront life
- GALATA/KARAKÃ–Y STREETS: Charming cobblestone streets winding downhill from the tower â€” art galleries, vintage shops, cozy cafes, street musicians, colorful graffiti and murals, cat-friendly doorways
- BEYOÄLU & Ä°STÄ°KLAL CADDESÄ°: The nearby bustling pedestrian boulevard â€” the historic red tram (nostaljik tramvay), flower sellers, historic passage buildings (pasajlar), bookshops
- BOSPHORUS PANORAMA: The strait connecting the Black Sea to the Marmara Sea â€” massive container ships, small fishing boats, ferry boats crisscrossing, the Asian shore visible across the water
- HISTORIC PENINSULA VIEW: From the tower looking south across the Golden Horn â€” the silhouette of domes and minarets, TopkapÄ± Palace on the hill, ancient city walls

ARCHITECTURAL & HISTORICAL ACCURACY:
- Built 1348 by the Genoese colony as "Christea Turris" (Tower of Christ)
- Cylindrical stone body with conical cap roof â€” medieval Genoese military architecture with Gothic influences
- Wall thickness: ~3.7m at base, tapering upward
- Total height: ~67 meters (including the conical roof)
- Used as prison, fire watch tower, and observatory through Ottoman centuries
- HezÃ¢rfen Ahmed Ã‡elebi's legendary flight (~1630s) â€” flew on artificial wings across the Bosphorus
- Major restoration in 2020s â€” now a museum with exhibitions on each floor

LIGHTING OPTIONS (match to scene mood):
- Golden sunrise with long shadows across BeyoÄŸlu rooftops and sparkling Bosphorus
- Bright midday with deep blue sky, crisp tower shadow, and busy Golden Horn below
- Spectacular sunset painting the city in amber, rose, and purple from the observation deck
- Twilight blue hour with city lights beginning to twinkle and ferry lights on the water

CLOTHING:
The child is wearing {clothing_description}.

STYLE:
{visual_style}.

COMPOSITION:
- Clear focal point on the child in the middle-ground
- Rich, detailed Istanbul panorama background with atmospheric depth
- Space at bottom for text overlay (25% of image height)
- Vibrant color palette: warm stone grey, Bosphorus blue-green, sunset amber-rose, terracotta rooftops, golden light"""


GALATA_STORY_PROMPT_TR = """Sen Ã¶dÃ¼llÃ¼ Ã§ocuk kitabÄ± yazarÄ± ve Ä°stanbul tarihi/Ceneviz-OsmanlÄ± kÃ¼ltÃ¼rÃ¼ uzmanÄ±sÄ±n.
Kahraman, yaÅŸ ve eÄŸitsel deÄŸerler yukarÄ±da verilmiÅŸtir. GÃ¶revin: Galata Kulesi ve Ã§evresinde geÃ§en bÃ¼yÃ¼lÃ¼ bir macera yazmak.

ğŸ“ GALATA KULESÄ° â€” KULLANILACAK KÃœLTÃœREL MEKANLAR (hikayeye en az 6 tanesini entegre et):
1. Seyir terasÄ± â€” 67 metre yÃ¼kseklikte 360Â° panoramik Ä°stanbul manzarasÄ±, martÄ±lar gÃ¶z hizasÄ±nda, rÃ¼zgÃ¢r, ÅŸehrin ayaklar altÄ±nda olma hissi
2. Spiral taÅŸ merdiven â€” kulenin iÃ§inden dÃ¶nerek yÃ¼kselen OrtaÃ§aÄŸ taÅŸ merdiveni, her katta kÃ¼Ã§Ã¼k kemerli pencerelerden ÅŸehrin farklÄ± yÃ¼zÃ¼
3. Kule mÃ¼zesi â€” 9 katta sergilenen OsmanlÄ±, Bizans ve Ceneviz dÃ¶nemine ait eserler, taÅŸ duvarlar, konik tavan
4. HezÃ¢rfen Ahmed Ã‡elebi efsanesi â€” 17. yÃ¼zyÄ±lda yapma kanatlarla Galata Kulesi'nden ÃœskÃ¼dar'a uÃ§an OsmanlÄ± mucidi, uÃ§ma hayali ve cesaret
5. Galata KÃ¶prÃ¼sÃ¼ ve HaliÃ§ â€” kulenin altÄ±ndaki altÄ±n sularÄ±n Ã¼zerindeki kÃ¶prÃ¼, sÄ±ra sÄ±ra balÄ±kÃ§Ä±lar, renkli vapurlar, kÃ¶prÃ¼ altÄ± balÄ±k restoranlarÄ±
6. Galata/KarakÃ¶y sokaklarÄ± â€” kuleden inen arnavut kaldÄ±rÄ±mlÄ± dar sokaklar, sanat galerileri, vintage dÃ¼kkanlar, sokak mÃ¼zisyenleri, kedili kapÄ±lar
7. BeyoÄŸlu ve Ä°stiklal Caddesi â€” nostaljik kÄ±rmÄ±zÄ± tramvay, Ã§iÃ§ekÃ§iler, tarihi pasajlar, kitapÃ§Ä±lar
8. BoÄŸaz manzarasÄ± â€” kuleden gÃ¶rÃ¼nen boÄŸaz, vapurlar, balÄ±kÃ§Ä± tekneleri, Asya yakasÄ±, dev gemiler
9. Tarihi YarÄ±mada silueti â€” kuleden gÃ¼neye bakÄ±nca HaliÃ§'in Ã¶tesinde kubbe ve minare silÃ¼eti, TopkapÄ± SarayÄ± tepede
10. Kulenin dÄ±ÅŸ gÃ¶rÃ¼nÃ¼mÃ¼ â€” silindirik taÅŸ gÃ¶vde, konik Ã§atÄ±, Gotik taÅŸ iÅŸÃ§iliÄŸi, 1348'den beri ayakta duran saÄŸlamlÄ±k

ğŸ­ YARDIMCI KARAKTER (en az biri hikayede olsun):
Cesur MartÄ± (kulenin tepesinden tÃ¼m Ä°stanbul'u gÃ¶ren, BoÄŸaz'Ä±n sÄ±rlarÄ±nÄ± bilen denizci kuÅŸ),
Hezârfen'in Sesi (yapma kanatlarla uçmuş Osmanlı mucidinin neşeli anısı, çocuğa cesaret veren),
Kurnaz Kedi (Galata sokaklarÄ±nÄ±n efendisi, her gizli geÃ§idi ve kestirme yolu bilen Ä°stanbul kedisi),
KonuÅŸan Fener (kulenin tepesindeki eski yangÄ±n gÃ¶zetleme feneri, yÃ¼zyÄ±llarÄ±n hikayelerini anlatan)
veya NeÅŸeli BalÄ±kÃ§Ä± Pelikan (Galata KÃ¶prÃ¼sÃ¼'nden balÄ±k kapan, HaliÃ§'in canlÄ±larÄ±nÄ± tanÄ±tan).
Karakter, kulenin 700 yÄ±llÄ±k tarihinden veya Ä°stanbul'un bÃ¼yÃ¼lÃ¼ atmosferinden "uyanmÄ±ÅŸ" olabilir.

âš¡ Ã–NEMLI â€” BU BÄ°R GEZÄ° REHBERÄ° DEÄÄ°L, BÄ°R MACERA HÄ°KAYESÄ°!
Galata Kulesi ve Ã§evresi ARKA PLAN olarak kullan. Hikayenin motorunu MEKANLAR DEÄÄ°L,
Ã§ocuÄŸun Ä°Ã‡ YOLCULUÄU ve eÄŸitsel deÄŸerler oluÅŸtursun.

âŒ YANLIÅ: "Ali kuleye Ã§Ä±ktÄ±. Sonra manzaraya baktÄ±. Sonra aÅŸaÄŸÄ± indi."
âœ… DOÄRU: Ã‡ocuÄŸun bir SORUNU/ZAYIFLIÄI var. Bu sorun Galata Kulesi'nin bÃ¼yÃ¼lÃ¼ mekanlarÄ±nda
bir MACERA'ya dÃ¶nÃ¼ÅŸÃ¼yor. Spiral merdivende her kat farklÄ± bir zaman dilimine aÃ§Ä±lÄ±yor,
Hezârfen'in anısı çocuğa cesaretin sırrını fısıldıyor, kulenin tepesinden bakınca
tÃ¼m Ä°stanbul'un hikayeleri gÃ¶rÃ¼nÃ¼yor. Ã‡ocuk yÃ¼ksekliÄŸin ve perspektifin gÃ¼cÃ¼nÃ¼ keÅŸfederken KENDÄ°NÄ° keÅŸfediyor.

ğŸ”‘ EÄÄ°TSEL DEÄER ENTEGRASYONU:
SeÃ§ilen eÄŸitsel deÄŸer hikayenin OLAY Ã–RGÃœSÃœNÃœ belirlemeli:
- Cesaret seÃ§ildiyse â†’ Ã§ocuÄŸun yÃ¼kseklik korkusu olsun, HezÃ¢rfen gibi cesareti bulsun
- Merak seÃ§ildiyse â†’ spiral merdivende her kat farklÄ± bir gizem, Ã§ocuÄŸun sorularÄ± onu tepeye gÃ¶tÃ¼rsÃ¼n
- Hayal gÃ¼cÃ¼ seÃ§ildiyse â†’ HezÃ¢rfen'in kanatlarÄ± Ã§ocuÄŸu hayali bir uÃ§uÅŸa Ã§Ä±karsÄ±n, imkansÄ±zÄ± hayal etmeyi Ã¶ÄŸretsin
- Azim seÃ§ildiyse â†’ 67 metre tÄ±rmanÄ±ÅŸ zor gelsin, her katta vazgeÃ§mek istesin ama devam etsin
- FarklÄ±lÄ±klara saygÄ± seÃ§ildiyse â†’ kule Ceneviz, Bizans, OsmanlÄ± â€” farklÄ± kÃ¼ltÃ¼rlerin bir arada oluÅŸu
DeÄŸer sadece "sÃ¶ylenmesin", Ã§ocuk YAÅAYARAK Ã¶ÄŸrensin!

âš ï¸ Ã–NEMLÄ° KISITLAMA:
Hikayede DÄ°NÄ° RÄ°TÃœEL veya Ä°BADET SAHNESÄ° OLMAMALIDIR.
Kule "tarihÃ® gÃ¶zetleme kulesi ve mÃ¼ze" olarak sunulsun.
HezÃ¢rfen efsanesi BÄ°LÄ°MSEL MERAK ve CESARET perspektifinden.
Ã‡ocuk mimariyi, manzarayÄ±, tarihi ve kÃ¼ltÃ¼rel Ã§eÅŸitliliÄŸi keÅŸfetsin.

ğŸ¨ SAHNE AÃ‡IKLAMASI KURALLARI (Pass-2 iÃ§in ipucu):
Her sahne iÃ§in spesifik Galata Kulesi lokasyonu ve mimari/panoramik detay kullan.
Ã–rn: "Kulenin seyir terasÄ±ndan BoÄŸaz'a gÃ¼n batÄ±mÄ±nda bakarken", "Spiral taÅŸ merdivende 5. kata tÄ±rmanÄ±rken",
"Galata KÃ¶prÃ¼sÃ¼'nde balÄ±kÃ§Ä±larÄ±n arasÄ±nda HaliÃ§'e bakarken", "KarakÃ¶y sokaklarÄ±nda bir sokak kedisiyle".
Genel ifadelerden kaÃ§Ä±n ("kulede" yerine somut yer adÄ± ve detay kullan)."""


GALATA_LOCATION_CONSTRAINTS = """Galata Tower and surrounding Galata/KarakÃ¶y district iconic elements (include 1-2 relevant details depending on the scene):
- Galata Tower's cylindrical stone body with conical cap roof (67m tall, 1348 Genoese)
- 360Â° Istanbul panorama: Golden Horn, Bosphorus, Historic Peninsula skyline
- Medieval spiral stone staircase and thick stone walls
- Galata Bridge with fishermen and ferry boats on the Golden Horn
- Charming BeyoÄŸlu/KarakÃ¶y cobblestone streets, cafes, and Istanbul cats"""


GALATA_CULTURAL_ELEMENTS = {
    "primary_landmarks": [
        "Galata Tower observation terrace (67m, 360Â° Istanbul panorama)",
        "spiral stone staircase through nine floors",
        "Galata Bridge spanning the Golden Horn (fishermen, ferries)",
        "Bosphorus strait panoramic view",
        "Historic Peninsula skyline (domes, minarets, TopkapÄ± Palace)"
    ],
    "secondary_elements": [
        "Galata/KarakÃ¶y cobblestone streets (art galleries, cafes, vintage shops)",
        "Ä°stiklal Avenue and nostalgic red tram",
        "HezÃ¢rfen Ahmed Ã‡elebi flight legend",
        "tower museum (Ottoman, Byzantine, Genoese artifacts)",
        "KarakÃ¶y waterfront and ferry terminals"
    ],
    "cultural_items": [
        "Genoese medieval stone architecture with Gothic details",
        "traditional Turkish tea glasses at Galata cafes",
        "Istanbul street cats (Galata's famous residents)",
        "fishermen's tackle on Galata Bridge railings",
        "nostalgic red tram (Ä°stiklal Caddesi)"
    ],
    "color_palette": "warm stone grey, Bosphorus blue-green, sunset amber-rose, terracotta rooftops, golden light, conical cap dark grey",
    "atmosphere": "panoramic, exhilarating, historic, romantic, breezy, culturally layered",
    "time_periods": [
        "golden sunrise with sparkling Bosphorus and long shadows on BeyoÄŸlu rooftops",
        "bright midday with blue sky and busy Golden Horn below",
        "spectacular sunset painting Istanbul in amber and rose from the observation deck",
        "twilight blue hour with city lights twinkling and ferry lights on the water"
    ]
}


GALATA_CUSTOM_INPUTS = [
    {
        "key": "favorite_view",
        "label": "En SevdiÄŸi Manzara",
        "type": "select",
        "options": ["BoÄŸaz ManzarasÄ±", "HaliÃ§ ve Galata KÃ¶prÃ¼sÃ¼", "Tarihi YarÄ±mada Silueti", "GÃ¼n BatÄ±mÄ± PanoramasÄ±"],
        "default": "GÃ¼n BatÄ±mÄ± PanoramasÄ±",
        "required": False,
        "help_text": "Hikayenin en bÃ¼yÃ¼lÃ¼ sahnesinin manzarasÄ±"
    },
    {
        "key": "special_discovery",
        "label": "KeÅŸfetmek Ä°stediÄŸi Åey",
        "type": "select",
        "options": ["HezÃ¢rfen'in Gizli KanatlarÄ±", "Kulenin KayÄ±p KatÄ±", "Sihirli GÃ¶zetleme Feneri", "Ceneviz Hazine HaritasÄ±"],
        "default": "HezÃ¢rfen'in Gizli KanatlarÄ±",
        "required": False,
        "help_text": "Hikayede Ã§ocuÄŸun keÅŸfedeceÄŸi bÃ¼yÃ¼k sÄ±r"
    },
    {
        "key": "travel_companion",
        "label": "Yol ArkadaÅŸÄ±",
        "type": "select",
        "options": ["Cesur MartÄ±", "HezÃ¢rfen'in Hayaleti", "Kurnaz Kedi", "NeÅŸeli Pelikan"],
        "default": "Kurnaz Kedi",
        "required": False,
        "help_text": "Galata'da Ã§ocuÄŸa eÅŸlik edecek Ä°stanbul arkadaÅŸÄ±"
    }
]


async def create_galata_scenario():
    """Galata Kulesi MacerasÄ± senaryosunu oluÅŸtur veya gÃ¼ncelle."""

    print("\n" + "=" * 70)
    print("GALATA KULESÄ° MACERASI SENARYO OLUÅTURMA")
    print("Master Prompts - PuLID Optimized - Medieval Tower Wonder")
    print("=" * 70 + "\n")

    async with async_session_factory() as db:
        result = await db.execute(
            select(Scenario).where(Scenario.name.ilike("%Galata%"))
        )
        existing = result.scalar_one_or_none()

        if existing:
            print(f"[INFO] Mevcut senaryo bulundu, gÃ¼ncelleniyor... (ID: {existing.id})")
            scenario = existing
        else:
            print("[INFO] Yeni senaryo oluÅŸturuluyor...")
            scenario = Scenario(id=uuid.uuid4())
            db.add(scenario)

        scenario.name = "Galata Kulesi MacerasÄ±"
        scenario.description = (
            "Ä°stanbul'un 700 yÄ±llÄ±k gÃ¶zetleme kulesinde 67 metre yÃ¼kseklikte bÃ¼yÃ¼lÃ¼ bir macera! "
            "Spiral merdivende zaman yolculuÄŸu, HezÃ¢rfen'in uÃ§uÅŸ sÄ±rrÄ± ve 360Â° Ä°stanbul panoramasÄ±. "
            "Galata'nÄ±n bÃ¼yÃ¼lÃ¼ sokaklarÄ±nda tarih ve cesaretin gÃ¼cÃ¼nÃ¼ keÅŸfet!"
        )
        scenario.thumbnail_url = "/scenarios/galata.jpg"
        scenario.cover_prompt_template = GALATA_COVER_PROMPT
        scenario.page_prompt_template = GALATA_PAGE_PROMPT
        scenario.story_prompt_tr = GALATA_STORY_PROMPT_TR
        scenario.ai_prompt_template = None
        scenario.location_constraints = GALATA_LOCATION_CONSTRAINTS
        scenario.location_en = "Galata Tower"
        scenario.cultural_elements = GALATA_CULTURAL_ELEMENTS
        scenario.theme_key = "galata"
        scenario.custom_inputs_schema = GALATA_CUSTOM_INPUTS
        scenario.is_active = True
        scenario.display_order = 8

        await db.commit()

        print("\n[OK] GALATA KULESÄ° MACERASI OLUÅTURULDU!\n")
        print("-" * 70)
        print("Senaryo DetaylarÄ±:")
        print(f"  - name: {scenario.name}")
        print(f"  - description: {len(scenario.description)} karakter")
        print(f"  - cover_prompt_template: {len(GALATA_COVER_PROMPT)} karakter")
        print(f"  - page_prompt_template: {len(GALATA_PAGE_PROMPT)} karakter")
        print(f"  - story_prompt_tr: {len(GALATA_STORY_PROMPT_TR)} karakter")
        print("  - location_en: Galata Tower")
        print(f"  - location_constraints: {len(GALATA_LOCATION_CONSTRAINTS)} karakter")
        print(f"  - cultural_elements: {len(json.dumps(GALATA_CULTURAL_ELEMENTS))} karakter (JSON)")
        print("  - theme_key: galata")
        print(f"  - custom_inputs_schema: {len(GALATA_CUSTOM_INPUTS)} Ã¶zel alan")
        print("-" * 70)

        print("\nÃ–ZEL GÄ°RÄ°Å ALANLARI:")
        for inp in GALATA_CUSTOM_INPUTS:
            print(f"  - {inp['label']}: {', '.join(inp['options'][:3])}...")

        print("\n" + "=" * 70)
        print("KAPAK PROMPT Ã–NÄ°ZLEME (ilk 500 karakter):")
        print("-" * 70)
        print(GALATA_COVER_PROMPT[:500] + "...")

        print("\n" + "=" * 70)
        print("STORY_PROMPT_TR Ã–NÄ°ZLEME (ilk 500 karakter):")
        print("-" * 70)
        print(GALATA_STORY_PROMPT_TR[:500] + "...")

        print("\n" + "=" * 70)
        print("Galata Kulesi MacerasÄ± senaryosu hazÄ±r!")
        print("Ã‡ocuklar artÄ±k Ä°stanbul'un 700 yÄ±llÄ±k kulesinden dÃ¼nyaya bakabilir!")
        print("=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(create_galata_scenario())


