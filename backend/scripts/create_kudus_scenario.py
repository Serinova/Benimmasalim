"""
KudÃ¼s Eski Åehir MacerasÄ± Senaryosu - Master Prompt OluÅŸturma

Bu script, KudÃ¼s Eski Åehir MacerasÄ± senaryosunu profesyonel, tutarlÄ± ve
kÃ¼ltÃ¼rel aÃ§Ä±dan zengin prompt'larla oluÅŸturur veya gÃ¼nceller.

KudÃ¼s Eski Åehir: UNESCO DÃ¼nya MirasÄ± (1981), 0.9 kmÂ², surlarla Ã§evrili.
Kanuni Sultan SÃ¼leyman surlarÄ± (16. yy), 4 mahalle, binlerce yÄ±llÄ±k tarih.
Dar taÅŸ sokaklar, Ã§arÅŸÄ±lar, el sanatlarÄ±, baharatlar.
KÃ¼ltÃ¼rel mozaik: farklÄ± medeniyetlerin izleri iÃ§ iÃ§e.

Ã–NEMLÄ° - PuLID UYUMLULUK:
- Fiziksel Ã¶zellikler YASAK (saÃ§, gÃ¶z, ten rengi) - PuLID fotoÄŸraftan alÄ±yor
- {clothing_description} zorunlu - kÄ±yafet tutarlÄ±lÄ±ÄŸÄ± iÃ§in
- Sahne aÃ§Ä±klamalarÄ± ACTION-ONLY - stil StyleConfig'den geliyor
- YÃ¼z kimliÄŸi korunmalÄ± - "Bu kesin benim Ã§ocuÄŸum" hissi

âš ï¸ Ã–NEMLÄ° KISITLAMA:
- Hikayede DÄ°NÄ° RÄ°TÃœEL, Ä°BADET SAHNESÄ° veya DÄ°NÄ° Ã–ÄRETÄ° OLMAMALIDIR.
- Siyasi mesaj veya taraf tutma OLMAMALIDIR.
- KudÃ¼s "UNESCO DÃ¼nya MirasÄ±, insanlÄ±ÄŸÄ±n ortak kÃ¼ltÃ¼rel hazinesi" olarak sunulmalÄ±dÄ±r.
- Odak: MÄ°MARÄ°, ARKEOLOJÄ°, Ã‡ARÅI KÃœLTÃœRÃœ, TARIM ve KÃœLTÃœREL Ã‡EÅÄ°TLÄ°LÄ°K.

Ã‡alÄ±ÅŸtÄ±rma:
    cd backend
    python -m scripts.create_kudus_scenario
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
# KUDÃœS ESKÄ° ÅEHÄ°R MACERASI - MASTER PROMPT TEMPLATES
# =============================================================================

KUDUS_COVER_PROMPT = """A breathtaking children's book cover illustration.

SCENE COMPOSITION:
A young child {scene_description}, standing on the ancient stone ramparts of the Old City walls (built by Suleiman the Magnificent in the 16th century), gazing out over the golden-stone rooftops and domes of the walled Old City of Jerusalem.

ICONIC BACKGROUND ELEMENTS (include 2-3 key details):
- The magnificent Ottoman-era city walls and crenellated battlements stretching into the distance â€” warm golden limestone (Jerusalem stone)
- A panorama of the Old City rooftops: a sea of golden-stone domes, arches, and flat rooftops densely packed within the walls
- The iconic golden Dome of the Rock catching the sunlight â€” the most recognizable architectural landmark of the skyline
- Ancient stone gates (one of the eight historic gates) with massive arched doorways
- Olive trees and cypress trees dotting the hillsides beyond the walls
- The Kidron Valley and Mount of Olives visible in the golden distance

LIGHTING & ATMOSPHERE:
- Warm golden hour light bathing the Jerusalem stone in its famous honeyed glow
- The unique warm luminosity that Jerusalem stone is famous for â€” every surface glowing gold
- A vast Mediterranean blue sky with wispy clouds
- A timeless, ancient, multicultural atmosphere â€” layers of 5,000 years of civilization
- Color palette: Jerusalem gold stone, Mediterranean blue, olive green, warm amber, dome gold, terracotta

CLOTHING:
The child is wearing {clothing_description}.

STYLE:
{visual_style}.

COMPOSITION REQUIREMENTS:
- Professional book cover design with clear title space at the top
- Child positioned in lower third, standing on the wall rampart looking over the rooftop panorama
- Epic cinematic scale showing the density and beauty of the walled city
- Golden domes and ancient architecture framing the upper portion of the scene"""


KUDUS_PAGE_PROMPT = """A stunning children's book illustration set in the historic walled Old City of Jerusalem, a UNESCO World Heritage Site.

SCENE ACTION:
A young child {scene_description}.

AUTHENTIC OLD CITY SETTING (vary these elements per scene):
- OTTOMAN WALLS & GATES: The magnificent 16th-century walls built by Suleiman the Magnificent â€” golden limestone crenellated battlements, massive arched gates (Damascus Gate, Jaffa Gate, Lion's Gate), walkways atop the walls with panoramic views, guard towers
- NARROW STONE ALLEYS: Ancient winding cobblestone lanes barely wide enough for two people â€” arched stone passageways, overhead stone bridges connecting buildings, worn limestone steps descending and ascending through the terrain, dappled sunlight filtering through
- THE BAZAAR & SOUQ: Vibrant covered markets bursting with color â€” mountains of colorful spices (turmeric gold, paprika red, za'atar green), hanging copper lanterns, handwoven textiles, olive wood carvings, ceramic tiles with geometric patterns, leather goods, stalls of fresh pomegranates and dates
- ROOFTOP PANORAMA: Flat limestone rooftops stretching in every direction â€” satellite dishes next to ancient domes, laundry lines between buildings, rooftop gardens with herbs, panoramic views of the golden city and surrounding hills
- ARCHAEOLOGICAL LAYERS: Ancient Roman-era stone columns emerging from the ground, excavated pools and cisterns, layers of civilization visible in cross-section walls â€” Roman, Byzantine, Crusader, Ottoman periods stacked upon each other
- FOUR QUARTERS: Distinct neighborhoods each with their own character â€” different architectural styles, market specialties, cultural atmospheres, all connected by the labyrinthine street network
- ARTISAN WORKSHOPS: Traditional craftspeople at work â€” ceramic painters creating geometric tile patterns, olive wood carvers, mosaic artists assembling tiny colored stones, copper smiths hammering lanterns, glassblowers, carpet weavers
- STONE ARCHITECTURE: Iconic Jerusalem stone (meleke limestone) that glows golden in sunlight â€” pointed arches, domed ceilings, ornate carved stone doorways, ancient stone water fountains, decorative mashrabiya lattice windows
- CITADEL & TOWER OF DAVID: The ancient fortress near Jaffa Gate â€” massive stone walls, archaeological museum, panoramic tower views, the moat area
- ANCIENT WATER SYSTEMS: Underground pools, ancient aqueducts, Hezekiah's Tunnel carved through solid rock, cisterns collecting rainwater for millennia

ARCHITECTURAL & HISTORICAL ACCURACY:
- Current walls built 1535-1542 by Ottoman Sultan Suleiman the Magnificent
- Eight historic gates in the city walls, each with its own history and character
- Building material: distinctive Jerusalem limestone (meleke) that glows golden in sunlight
- City area: approximately 0.9 kmÂ² packed with millennia of continuous habitation
- UNESCO World Heritage Site since 1981
- Layers of Canaanite, Israelite, Roman, Byzantine, Islamic Caliphate, Crusader, Mamluk, and Ottoman civilizations
- Four quarters: Muslim, Christian, Armenian, Jewish â€” each with distinct architectural character

LIGHTING OPTIONS (match to scene mood):
- Golden sunrise light making every stone surface glow with famous Jerusalem gold
- Bright midday with deep blue Mediterranean sky and sharp shadows in narrow alleys
- Late afternoon with warm amber light filtering through covered souq corridors
- Magical twilight with lanterns and oil lamps illuminating stone archways

CLOTHING:
The child is wearing {clothing_description}.

STYLE:
{visual_style}.

COMPOSITION:
- Clear focal point on the child in the middle-ground
- Rich, detailed Old City architecture background with atmospheric depth
- Space at bottom for text overlay (25% of image height)
- Vibrant color palette: Jerusalem gold stone, spice market colors, Mediterranean blue, olive green, lantern amber, ceramic blue-white"""


KUDUS_STORY_PROMPT_TR = """Sen Ã¶dÃ¼llÃ¼ Ã§ocuk kitabÄ± yazarÄ± ve KudÃ¼s tarihi/OsmanlÄ±-OrtadoÄŸu kÃ¼ltÃ¼rÃ¼ uzmanÄ±sÄ±n.
Kahraman, yaÅŸ ve eÄŸitsel deÄŸerler yukarÄ±da verilmiÅŸtir. GÃ¶revin: KudÃ¼s Eski Åehir'de geÃ§en bÃ¼yÃ¼lÃ¼ bir macera yazmak.

ğŸ“ KUDÃœS ESKÄ° ÅEHÄ°R â€” KULLANILACAK KÃœLTÃœREL MEKANLAR (hikayeye en az 6 tanesini entegre et):
1. OsmanlÄ± surlarÄ± ve kapÄ±larÄ± â€” Kanuni Sultan SÃ¼leyman'Ä±n 16. yÃ¼zyÄ±lda inÅŸa ettirdiÄŸi gÃ¶rkemli surlar, mazgallÄ± surlarÄ±n Ã¼stÃ¼nden panoramik ÅŸehir manzarasÄ±, 8 tarihi kapÄ±
2. Dar taÅŸ sokaklar â€” iki kiÅŸinin zar zor geÃ§ebileceÄŸi antik arnavut kaldÄ±rÄ±mlÄ± yollar, kemerli taÅŸ geÃ§itler, yÄ±pranmÄ±ÅŸ kireÃ§taÅŸÄ± merdivenler, taÅŸ kÃ¶prÃ¼ler
3. Ã‡arÅŸÄ± ve pazar â€” renk cÃ¼mbÃ¼ÅŸÃ¼ kapalÄ± Ã§arÅŸÄ±lar, baharat daÄŸlarÄ± (zerdeÃ§al, kÄ±rmÄ±zÄ± biber, zahter), asÄ±lÄ± bakÄ±r fenerler, el dokumasÄ± kumaÅŸlar, zeytin aÄŸacÄ± oymalar, seramik karolar, taze nar ve hurmalar
4. Ã‡atÄ± manzarasÄ± â€” altÄ±n rengi dÃ¼z kireÃ§taÅŸÄ± Ã§atÄ±lar, her yÃ¶ne uzanan kubbeler ve kemerler, Ã§atÄ± bahÃ§eleri, panoramik tepe manzarasÄ±
5. Arkeolojik katmanlar â€” yerden yÃ¼kselen Roma dÃ¶nemi sÃ¼tunlarÄ±, kazÄ±lmÄ±ÅŸ havuzlar ve sarnÄ±Ã§lar, kesit duvarlarda gÃ¶rÃ¼nen uygarlÄ±k katmanlarÄ± (Roma, Bizans, HaÃ§lÄ±, OsmanlÄ±)
6. DÃ¶rt mahalle â€” her biri kendine Ã¶zgÃ¼ mimari, pazar ve kÃ¼ltÃ¼rel atmosfere sahip farklÄ± mahalleler, labirent gibi sokak aÄŸÄ±yla birbirine baÄŸlÄ±
7. ZanaatkÃ¢r atÃ¶lyeleri â€” geometrik desen Ã§izen seramikÃ§iler, zeytin aÄŸacÄ± oymacÄ±larÄ±, mozaik ustalarÄ±, bakÄ±rcÄ±lar, cam Ã¼fleyiciler, halÄ± dokuyucularÄ±
8. TaÅŸ mimari â€” gÃ¼neÅŸ Ä±ÅŸÄ±ÄŸÄ±nda altÄ±n gibi parlayan KudÃ¼s taÅŸÄ± (meleke kireÃ§taÅŸÄ±), sivri kemerler, kubbeli tavanlar, iÅŸlemeli taÅŸ kapÄ±lar, taÅŸ Ã§eÅŸmeler, meÅŸrebiye kafes pencereler
9. Kale ve David Kulesi â€” Yafa KapÄ±sÄ± yanÄ±ndaki antik kale, devasa taÅŸ surlar, arkeoloji mÃ¼zesi, panoramik kule manzarasÄ±
10. Antik su sistemleri â€” yeraltÄ± havuzlarÄ±, antik su kemerleri, kaya iÃ§inden oyulmuÅŸ tÃ¼neller, bin yÄ±llÄ±k sarnÄ±Ã§lar

ğŸ­ YARDIMCI KARAKTER (en az biri hikayede olsun):
Bilge Kedi (Eski Åehir'in labirent sokaklarÄ±nÄ± ezbere bilen, her gizli geÃ§idi gÃ¶steren antik kedi),
KonuÅŸan TaÅŸ (surlarÄ±n 500 yÄ±llÄ±k taÅŸÄ±, Kanuni'den beri gÃ¶rdÃ¼klerini anlatan),
NeÅŸeli Baharat TÃ¼ccarÄ± (Ã§arÅŸÄ±daki renkli baharat daÄŸlarÄ±nÄ±n arasÄ±nda sihirli tatlar sunan karakter),
Usta ZanaatkÃ¢r (bin yÄ±llÄ±k mozaik sanatÄ±nÄ± Ã¶ÄŸreten sabÄ±rlÄ± usta)
veya Cesur GÃ¼vercin (surlarÄ±n Ã¼zerinden tÃ¼m ÅŸehri gÃ¶ren, farklÄ± mahallelerin hikayelerini bilen kuÅŸ).
Karakter, ÅŸehrin binlerce yÄ±llÄ±k tarihinden veya kÃ¼ltÃ¼rel zenginliÄŸinden "uyanmÄ±ÅŸ" olabilir.

âš¡ Ã–NEMLÄ° â€” BU BÄ°R GEZÄ° REHBERÄ° DEÄÄ°L, BÄ°R MACERA HÄ°KAYESÄ°!
KudÃ¼s Eski Åehir ARKA PLAN olarak kullan. Hikayenin motorunu MEKANLAR DEÄÄ°L,
Ã§ocuÄŸun Ä°Ã‡ YOLCULUÄU ve eÄŸitsel deÄŸerler oluÅŸtursun.

âŒ YANLIÅ: "Ali surlarÄ± gÃ¶rdÃ¼. Sonra Ã§arÅŸÄ±ya gitti. Sonra dondurma yedi."
âœ… DOÄRU: Ã‡ocuÄŸun bir SORUNU/ZAYIFLIÄI var. Bu sorun Eski Åehir'in bÃ¼yÃ¼lÃ¼ labirent sokaklarÄ±nda
bir MACERA'ya dÃ¶nÃ¼ÅŸÃ¼yor. Her dar geÃ§it farklÄ± bir uygarlÄ±ÄŸÄ±n katmanÄ±na aÃ§Ä±lÄ±yor,
bir taÅŸa dokunduÄŸunda bin yÄ±l Ã¶ncesinin sesleri duyuluyor, Ã§arÅŸÄ±nÄ±n baharatlarÄ±
sihirli kokularla Ã§ocuÄŸu zamanda yolculuÄŸa Ã§Ä±karÄ±yor. Ã‡ocuk kÃ¼ltÃ¼rel Ã§eÅŸitliliÄŸin
ve birlikte yaÅŸamanÄ±n gÃ¼cÃ¼nÃ¼ keÅŸfederken KENDÄ°NÄ° keÅŸfediyor.

ğŸ”‘ EÄÄ°TSEL DEÄER ENTEGRASYONU:
SeÃ§ilen eÄŸitsel deÄŸer hikayenin OLAY Ã–RGÃœSÃœNÃœ belirlemeli:
- FarklÄ±lÄ±klara saygÄ± seÃ§ildiyse â†’ dÃ¶rt mahalle dÃ¶rt farklÄ± kÃ¼ltÃ¼r, Ã§ocuk hepsinin gÃ¼zelliÄŸini gÃ¶rsÃ¼n
- Merak seÃ§ildiyse â†’ arkeolojik katmanlar Ã§ocuÄŸu Ã§eksin, her kazÄ± yeni bir sÄ±r ortaya Ã§Ä±karsÄ±n
- SabÄ±r seÃ§ildiyse â†’ mozaik ustasÄ±ndan sabÄ±rla kÃ¼Ã§Ã¼k taÅŸlarÄ± birleÅŸtirmenin sanatÄ±nÄ± Ã¶ÄŸrensin
- Cesaret seÃ§ildiyse â†’ karanlÄ±k yeraltÄ± tÃ¼nellerinde cesaretle ilerlesin
- PaylaÅŸmak seÃ§ildiyse â†’ Ã§arÅŸÄ±da farklÄ± kÃ¼ltÃ¼rlerden insanlarla paylaÅŸmanÄ±n gÃ¼zelliÄŸini yaÅŸasÄ±n
DeÄŸer sadece "sÃ¶ylenmesin", Ã§ocuk YAÅAYARAK Ã¶ÄŸrensin!

âš ï¸ Ã–NEMLÄ° KISITLAMALAR:
1. Hikayede DÄ°NÄ° RÄ°TÃœEL, Ä°BADET SAHNESÄ° veya DÄ°NÄ° Ã–ÄRETÄ° OLMAMALIDIR.
   Dini yapÄ±lar yalnÄ±zca "mimari ÅŸaheser ve tarihÃ® anÄ±t" olarak sunulsun.
2. Siyasi mesaj, taraf tutma veya gÃ¼ncel Ã§atÄ±ÅŸmalara atÄ±f OLMAMALIDIR.
3. KudÃ¼s "UNESCO DÃ¼nya MirasÄ±, insanlÄ±ÄŸÄ±n ortak kÃ¼ltÃ¼rel hazinesi" perspektifinden anlatÄ±lsÄ±n.
4. Odak: MÄ°MARÄ° gÃ¼zellik, ARKEOLOJÄ°K keÅŸif, Ã‡ARÅI kÃ¼ltÃ¼rÃ¼, ZANAAT sanatÄ± ve KÃœLTÃœREL Ã‡EÅÄ°TLÄ°LÄ°K.
5. FarklÄ± kÃ¼ltÃ¼rlerin bir arada yaÅŸamasÄ±nÄ±n gÃ¼zelliÄŸi vurgulansÄ±n.

ğŸ¨ SAHNE AÃ‡IKLAMASI KURALLARI (Pass-2 iÃ§in ipucu):
Her sahne iÃ§in spesifik KudÃ¼s Eski Åehir lokasyonu ve mimari/arkeolojik detay kullan.
Ã–rn: "Åam KapÄ±sÄ±'nÄ±n dev kemerinin altÄ±ndan geÃ§erken", "Ã‡arÅŸÄ±nÄ±n baharat tezgahlarÄ± arasÄ±nda zerdeÃ§al daÄŸÄ±na dokunurken",
"SurlarÄ±n Ã¼stÃ¼nde mazgallar arasÄ±ndan altÄ±n rengi Ã§atÄ±lara bakarken", "Mozaik ustasÄ±nÄ±n atÃ¶lyesinde kÃ¼Ã§Ã¼k renkli taÅŸlarÄ± yerleÅŸtirirken".
Genel ifadelerden kaÃ§Ä±n ("ÅŸehirde" yerine somut yer adÄ± ve detay kullan)."""


KUDUS_LOCATION_CONSTRAINTS = """Old City of Jerusalem UNESCO World Heritage Site iconic elements (include 1-2 relevant details depending on the scene):
- Ancient city walls built by Suleiman the Magnificent (16th century Ottoman) â€” golden Jerusalem limestone, crenellated battlements
- Narrow winding cobblestone alleys with arched stone passageways and overhead bridges
- The vibrant covered souq/bazaar with spices, crafts, lanterns, and artisan workshops
- Distinctive Jerusalem stone (meleke limestone) glowing golden in sunlight on every surface
- Dense rooftop panorama of domes, arches, and flat stone roofs within the walled city"""


KUDUS_CULTURAL_ELEMENTS = {
    "primary_landmarks": [
        "Ottoman city walls and eight historic gates (Damascus Gate, Jaffa Gate, Lion's Gate)",
        "Golden Dome of the Rock â€” iconic architectural landmark of the skyline",
        "Tower of David / Citadel â€” ancient fortress and archaeological museum",
        "Covered souq bazaars with spice mountains and artisan workshops",
        "Ancient Roman-era archaeological layers visible throughout the city"
    ],
    "secondary_elements": [
        "Narrow winding cobblestone alleys with arched passageways",
        "Four distinct quarters (Muslim, Christian, Armenian, Jewish) â€” cultural mosaic",
        "Artisan workshops (ceramics, olive wood carving, mosaic, copperwork, glassblowing)",
        "Ancient underground water systems and carved tunnels",
        "Rooftop panorama of golden-stone domes and ancient architecture"
    ],
    "cultural_items": [
        "Spice mountains in the bazaar (za'atar, turmeric, sumac, cumin)",
        "Jerusalem stone (meleke limestone) glowing golden in sunlight",
        "Olive wood carvings and handmade ceramic tiles with geometric patterns",
        "Copper lanterns with intricate pierced patterns casting light",
        "Fresh pomegranates, dates, halva, and traditional street foods"
    ],
    "color_palette": "Jerusalem gold limestone, Mediterranean blue sky, spice market colors (turmeric gold, paprika red, za'atar green), olive green, lantern amber, ceramic cobalt blue-white",
    "atmosphere": "ancient, labyrinthine, multicultural, warm golden light, aromatic, timeless, layered civilizations",
    "time_periods": [
        "golden sunrise making Jerusalem stone glow with its famous honeyed light",
        "bright midday with sharp shadows in narrow stone alleys and blue sky above",
        "late afternoon amber light filtering through covered souq corridors with lantern glow",
        "magical twilight with oil lamp and lantern light illuminating ancient stone archways"
    ]
}


KUDUS_CUSTOM_INPUTS = [
    {
        "key": "favorite_quarter",
        "label": "En Merak EttiÄŸi Mahalle",
        "type": "select",
        "options": ["Ã‡arÅŸÄ± ve Baharat SokaÄŸÄ±", "ZanaatkÃ¢r AtÃ¶lyeleri", "Surlar ve KapÄ±lar", "Arkeoloji AlanlarÄ±"],
        "default": "Ã‡arÅŸÄ± ve Baharat SokaÄŸÄ±",
        "required": False,
        "help_text": "Hikayenin en renkli sahnesinin geÃ§eceÄŸi yer"
    },
    {
        "key": "special_discovery",
        "label": "KeÅŸfetmek Ä°stediÄŸi Åey",
        "type": "select",
        "options": ["KayÄ±p Mozaik HaritasÄ±", "Sihirli Baharat Tarifi", "Gizli YeraltÄ± TÃ¼neli", "Antik ZanaatkÃ¢r SÄ±rrÄ±"],
        "default": "KayÄ±p Mozaik HaritasÄ±",
        "required": False,
        "help_text": "Hikayede Ã§ocuÄŸun peÅŸine dÃ¼ÅŸeceÄŸi bÃ¼yÃ¼k gizem"
    },
    {
        "key": "travel_companion",
        "label": "Yol ArkadaÅŸÄ±",
        "type": "select",
        "options": ["Bilge Kedi", "KonuÅŸan TaÅŸ", "NeÅŸeli Baharat TÃ¼ccarÄ±", "Cesur GÃ¼vercin"],
        "default": "Bilge Kedi",
        "required": False,
        "help_text": "Eski Åehir'in labirent sokaklarÄ±nda Ã§ocuÄŸa rehberlik edecek dost"
    }
]


async def create_kudus_scenario():
    """KudÃ¼s Eski Åehir MacerasÄ± senaryosunu oluÅŸtur veya gÃ¼ncelle."""

    print("\n" + "=" * 70)
    print("KUDÃœS ESKÄ° ÅEHÄ°R MACERASI SENARYO OLUÅTURMA")
    print("Master Prompts - PuLID Optimized - Ancient Walled City Wonder")
    print("=" * 70 + "\n")

    async with async_session_factory() as db:
        result = await db.execute(
            select(Scenario).where(Scenario.name.ilike("%KudÃ¼s%"))
        )
        existing = result.scalar_one_or_none()

        if existing:
            print(f"[INFO] Mevcut senaryo bulundu, gÃ¼ncelleniyor... (ID: {existing.id})")
            scenario = existing
        else:
            print("[INFO] Yeni senaryo oluÅŸturuluyor...")
            scenario = Scenario(id=uuid.uuid4())
            db.add(scenario)

        scenario.name = "KudÃ¼s Eski Åehir MacerasÄ±"
        scenario.description = (
            "UNESCO DÃ¼nya MirasÄ± surlarla Ã§evrili antik ÅŸehirde bÃ¼yÃ¼lÃ¼ bir macera! "
            "5.000 yÄ±llÄ±k taÅŸ sokaklarda zaman yolculuÄŸu, sihirli baharat Ã§arÅŸÄ±sÄ± "
            "ve altÄ±n rengi KudÃ¼s taÅŸÄ±nÄ±n Ä±ÅŸÄ±ÄŸÄ±nda kÃ¼ltÃ¼rlerin mozaiÄŸini keÅŸfet!"
        )
        scenario.thumbnail_url = "/scenarios/kudus.jpg"
        scenario.cover_prompt_template = KUDUS_COVER_PROMPT
        scenario.page_prompt_template = KUDUS_PAGE_PROMPT
        scenario.story_prompt_tr = KUDUS_STORY_PROMPT_TR
        scenario.ai_prompt_template = None
        scenario.location_constraints = KUDUS_LOCATION_CONSTRAINTS
        scenario.location_en = "Old City of Jerusalem"
        scenario.cultural_elements = KUDUS_CULTURAL_ELEMENTS
        scenario.theme_key = "kudus"
        scenario.custom_inputs_schema = KUDUS_CUSTOM_INPUTS
        scenario.is_active = True
        scenario.display_order = 9

        await db.commit()

        print("\n[OK] KUDÃœS ESKÄ° ÅEHÄ°R MACERASI OLUÅTURULDU!\n")
        print("-" * 70)
        print("Senaryo DetaylarÄ±:")
        print(f"  - name: {scenario.name}")
        print(f"  - description: {len(scenario.description)} karakter")
        print(f"  - cover_prompt_template: {len(KUDUS_COVER_PROMPT)} karakter")
        print(f"  - page_prompt_template: {len(KUDUS_PAGE_PROMPT)} karakter")
        print(f"  - story_prompt_tr: {len(KUDUS_STORY_PROMPT_TR)} karakter")
        print("  - location_en: Old City of Jerusalem")
        print(f"  - location_constraints: {len(KUDUS_LOCATION_CONSTRAINTS)} karakter")
        print(f"  - cultural_elements: {len(json.dumps(KUDUS_CULTURAL_ELEMENTS))} karakter (JSON)")
        print("  - theme_key: kudus")
        print(f"  - custom_inputs_schema: {len(KUDUS_CUSTOM_INPUTS)} Ã¶zel alan")
        print("-" * 70)

        print("\nÃ–ZEL GÄ°RÄ°Å ALANLARI:")
        for inp in KUDUS_CUSTOM_INPUTS:
            print(f"  - {inp['label']}: {', '.join(inp['options'][:3])}...")

        print("\n" + "=" * 70)
        print("KAPAK PROMPT Ã–NÄ°ZLEME (ilk 500 karakter):")
        print("-" * 70)
        print(KUDUS_COVER_PROMPT[:500] + "...")

        print("\n" + "=" * 70)
        print("STORY_PROMPT_TR Ã–NÄ°ZLEME (ilk 500 karakter):")
        print("-" * 70)
        print(KUDUS_STORY_PROMPT_TR[:500] + "...")

        print("\n" + "=" * 70)
        print("KudÃ¼s Eski Åehir MacerasÄ± senaryosu hazÄ±r!")
        print("Ã‡ocuklar artÄ±k insanlÄ±ÄŸÄ±n en kadim ÅŸehrinde bÃ¼yÃ¼lÃ¼ bir keÅŸfe Ã§Ä±kabilir!")
        print("=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(create_kudus_scenario())


