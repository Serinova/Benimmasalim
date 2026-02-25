"""
Abu Simbel TapÄ±naklarÄ± MacerasÄ± Senaryosu - Master Prompt OluÅŸturma

Bu script, Abu Simbel TapÄ±naklarÄ± MacerasÄ± senaryosunu profesyonel, tutarlÄ± ve
kÃ¼ltÃ¼rel aÃ§Ä±dan zengin prompt'larla oluÅŸturur veya gÃ¼nceller.

Abu Simbel: MÃ– 1264-1244, II. Ramses, Asvan/MÄ±sÄ±r, UNESCO (1979).
Ä°ki dev kaya tapÄ±naÄŸÄ±, 4 devasa Ramses heykeli, gÃ¼neÅŸ Ä±ÅŸÄ±ÄŸÄ± olayÄ± (22 Åubat/Ekim).
KraliÃ§e Nefertari tapÄ±naÄŸÄ±, Hathor tanrÄ±Ã§asÄ±.
1960'larda UNESCO kurtarma projesiyle 65 metre yukarÄ± taÅŸÄ±ndÄ±.

Ã–NEMLÄ° - PuLID UYUMLULUK:
- Fiziksel Ã¶zellikler YASAK (saÃ§, gÃ¶z, ten rengi) - PuLID fotoÄŸraftan alÄ±yor
- {clothing_description} zorunlu - kÄ±yafet tutarlÄ±lÄ±ÄŸÄ± iÃ§in
- Sahne aÃ§Ä±klamalarÄ± ACTION-ONLY - stil StyleConfig'den geliyor
- YÃ¼z kimliÄŸi korunmalÄ± - "Bu kesin benim Ã§ocuÄŸum" hissi

âš ï¸ Ã–NEMLÄ° KISITLAMA:
- Hikayede DÄ°NÄ° RÄ°TÃœEL veya Ä°BADET SAHNESÄ° OLMAMALIDIR.
- Antik MÄ±sÄ±r tanrÄ±larÄ± MÄ°TOLOJÄ°K KARAKTER / HÄ°KAYE unsuru olarak sunulsun, inanÃ§ olarak deÄŸil.
- Odak: MÄ°MARÄ°, ARKEOLOJÄ°, MÃœHENDÄ°SLÄ°K, GÃœNEÅ IÅIÄI FENOMENÄ°, SANAT ve TARÄ°H.

Ã‡alÄ±ÅŸtÄ±rma:
    cd backend
    python -m scripts.create_abusimbel_scenario
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
# ABU SÄ°MBEL TAPINAKLARI MACERASI - MASTER PROMPT TEMPLATES
# =============================================================================

ABUSIMBEL_COVER_PROMPT = """A breathtaking children's book cover illustration.

SCENE COMPOSITION:
A young child {scene_description}, standing in awe at the base of the colossal facade of the Great Temple of Abu Simbel in southern Egypt, dwarfed by the four enormous seated statues of Pharaoh Ramesses II carved directly into the cliff face.

ICONIC BACKGROUND ELEMENTS (include 2-3 key details):
- The four colossal seated statues of Ramesses II (each ~20 meters tall) carved into the golden sandstone cliff â€” serene pharaonic faces, double crowns of Upper and Lower Egypt, hands resting on knees
- The temple entrance between the two central statues â€” a dark rectangular doorway leading into the mountain
- Smaller statues of royal family members standing between the legs of the colossal figures
- Hieroglyphic carvings and cartouches covering the facade above the entrance
- The golden Nubian desert stretching to the horizon behind, with Lake Nasser's blue waters visible in the distance
- A brilliant Egyptian sun positioned directly above the temple, casting dramatic shadows

LIGHTING & ATMOSPHERE:
- Intense golden Egyptian sunlight illuminating the sandstone facade in warm amber-gold tones
- Deep dramatic shadows cast by the colossal statues creating a sense of immense scale
- The desert air shimmering with heat haze over the distant sands and lake
- A vast cloudless deep blue Egyptian sky contrasting with the golden stone
- Color palette: pharaonic gold sandstone, deep Nile blue, desert amber, sky azure, shadow purple-brown

CLOTHING:
The child is wearing {clothing_description}.

STYLE:
{visual_style}.

COMPOSITION REQUIREMENTS:
- Professional book cover design with clear title space at the top
- Child positioned in lower third, emphasizing the overwhelming scale of the 20-meter statues
- The four colossal Ramesses statues filling the frame with monumental grandeur
- Sense of ancient power, mystery, and archaeological wonder"""


ABUSIMBEL_PAGE_PROMPT = """A stunning children's book illustration set at the legendary Abu Simbel Temples in southern Egypt, a UNESCO World Heritage Site.

SCENE ACTION:
A young child {scene_description}.

AUTHENTIC ABU SIMBEL SETTING (vary these elements per scene):
- GREAT TEMPLE FACADE: The iconic cliff-face carved with four colossal seated statues of Ramesses II (~20m tall each) â€” serene pharaonic faces with double crowns, hands on knees, smaller royal family figures between the legs, hieroglyphic cartouches and carved friezes above the entrance
- TEMPLE INTERIOR - HYPOSTYLE HALL: Eight massive Osiride pillars (Ramesses as Osiris) lining the central aisle â€” towering carved figures holding crook and flail, painted ceiling with vulture motifs, dramatic shafts of light from the entrance cutting through the darkness
- INNER SANCTUARY (HOLY OF HOLIES): The deepest chamber with four seated statues (Ra-Horakhty, deified Ramesses, Amun, Ptah) â€” the magical room where sunlight reaches only twice a year, mysterious darkness punctuated by golden light
- SOLAR ALIGNMENT PHENOMENON: The magical moment when sunlight travels 60 meters through the temple corridor to illuminate the inner sanctuary statues â€” a golden beam cutting through darkness, ancient astronomical precision, the "Sun Festival" spectacle
- NEFERTARI'S TEMPLE (SMALL TEMPLE): The elegant smaller temple dedicated to Queen Nefertari and goddess Hathor â€” six standing colossal statues (four Ramesses, two Nefertari) on the facade, Hathor-headed columns inside, beautiful painted reliefs of the queen
- BATTLE RELIEFS: Massive wall carvings depicting the Battle of Kadesh â€” chariots, horses, archers, dramatic action scenes carved in raised relief, ancient Egyptian military art at its finest
- LAKE NASSER & NUBIAN DESERT: The vast artificial lake stretching to the horizon behind the temples â€” deep blue waters against golden desert cliffs, the dramatic landscape of southern Egypt/Nubia
- UNESCO RESCUE SITE: The artificial hill constructed to hold the relocated temples â€” the visible seam where the mountain was reconstructed, a testament to 1960s engineering marvel
- HIEROGLYPHIC WALLS: Every surface covered in carved and painted hieroglyphs â€” cartouches of Ramesses, offering scenes, gods and pharaohs in profile, colorful painted reliefs preserved for 3,000 years
- DESERT APPROACH: The pathway leading to the temples across the Nubian desert â€” golden sand, scattered desert rocks, the temples emerging from the cliff face as you approach, mirages on the horizon

ARCHITECTURAL & HISTORICAL ACCURACY:
- Built circa 1264-1244 BCE by Pharaoh Ramesses II (New Kingdom, 19th Dynasty)
- Great Temple: carved ~33 meters into the cliff, facade ~35 meters wide, ~30 meters tall
- Four seated colossi of Ramesses II: each approximately 20 meters tall
- Small Temple (Nefertari): six standing figures on facade (~10 meters tall each)
- Solar alignment: sunlight illuminates inner sanctuary on Feb 22 and Oct 22 each year
- UNESCO rescue: entire complex cut and relocated 65 meters higher in 1964-1968
- Dedicated to Ra-Horakhty, Amun, Ptah, and the deified Ramesses himself
- Nefertari's temple dedicated to goddess Hathor

LIGHTING OPTIONS (match to scene mood):
- Blazing Egyptian sunrise with the first golden rays striking the colossal facade
- Harsh midday desert sun with deep shadows between the statues and sharp contrasts
- The magical solar alignment beam â€” a single shaft of golden light cutting through 60 meters of darkness to illuminate the sanctuary
- Warm sunset turning the sandstone to deep amber-gold, Lake Nasser reflecting purple and orange

CLOTHING:
The child is wearing {clothing_description}.

STYLE:
{visual_style}.

COMPOSITION:
- Clear focal point on the child in the middle-ground
- Monumental scale of ancient Egyptian architecture creating dramatic sense of wonder
- Space at bottom for text overlay (25% of image height)
- Vibrant color palette: pharaonic gold sandstone, Nile blue, desert amber, hieroglyph colors (red, blue, gold, green), shadow purple"""


ABUSIMBEL_STORY_PROMPT_TR = """Sen Ã¶dÃ¼llÃ¼ Ã§ocuk kitabÄ± yazarÄ± ve Antik MÄ±sÄ±r tarihi/arkeoloji uzmanÄ±sÄ±n.
Kahraman, yaÅŸ ve eÄŸitsel deÄŸerler yukarÄ±da verilmiÅŸtir. GÃ¶revin: Abu Simbel TapÄ±naklarÄ±'nda geÃ§en bÃ¼yÃ¼lÃ¼ bir macera yazmak.

ğŸ“ ABU SÄ°MBEL TAPINAKLARI â€” KULLANILACAK KÃœLTÃœREL MEKANLAR (hikayeye en az 6 tanesini entegre et):
1. BÃ¼yÃ¼k TapÄ±nak cephesi â€” kayaya oyulmuÅŸ 4 devasa oturan II. Ramses heykeli (her biri ~20 metre), Ã§ift taÃ§lÄ± firavun yÃ¼zleri, hiyeroglif kartuÅŸlar, kraliyet ailesi heykelleri
2. Hipostil salon â€” 8 devasa Osiris sÃ¼tunu (Ramses formunda), tavan kanatlarÄ±, giriÅŸ Ä±ÅŸÄ±ÄŸÄ±nÄ±n karanlÄ±ÄŸÄ± yaran dramatik Ä±ÅŸÄ±k demetleri
3. Kutsal oda (en iÃ§ oda) â€” 4 oturan heykel (Ra-Horakhty, tanrÄ±sallaÅŸtÄ±rÄ±lmÄ±ÅŸ Ramses, Amun, Ptah), yÄ±lda sadece iki kez gÃ¼neÅŸ Ä±ÅŸÄ±ÄŸÄ±nÄ±n ulaÅŸtÄ±ÄŸÄ± gizemli oda
4. GÃ¼neÅŸ Ä±ÅŸÄ±ÄŸÄ± olayÄ± â€” her yÄ±l 22 Åubat ve 22 Ekim'de gÃ¼neÅŸ Ä±ÅŸÄ±ÄŸÄ±nÄ±n 60 metre tapÄ±nak koridorundan geÃ§erek kutsal odadaki heykelleri aydÄ±nlatmasÄ±, antik astronomik hassasiyet
5. Nefertari TapÄ±naÄŸÄ± â€” KraliÃ§e Nefertari ve Hathor tanrÄ±Ã§asÄ±na adanmÄ±ÅŸ zarif kÃ¼Ã§Ã¼k tapÄ±nak, 6 ayakta duran dev heykel, Hathor baÅŸlÄ± sÃ¼tunlar, kraliÃ§enin gÃ¼zel kabartmalarÄ±
6. SavaÅŸ kabartmalarÄ± â€” KadeÅŸ SavaÅŸÄ±'nÄ± gÃ¶steren devasa duvar oymalarÄ±, savaÅŸ arabalarÄ±, atlar, okÃ§ular, yÃ¼ksek kabartma tekniÄŸiyle dramatik aksiyon sahneleri
7. Nasser GÃ¶lÃ¼ ve Nubya Ã‡Ã¶lÃ¼ â€” tapÄ±naÄŸÄ±n arkasÄ±ndaki devasa yapay gÃ¶l, derin mavi sular ile altÄ±n rengi Ã§Ã¶l kayalÄ±klarÄ±, gÃ¼ney MÄ±sÄ±r'Ä±n dramatik manzarasÄ±
8. UNESCO kurtarma alanÄ± â€” tapÄ±naklarÄ±n 65 metre yukarÄ± taÅŸÄ±ndÄ±ÄŸÄ± yapay tepe, modern mÃ¼hendisliÄŸin en bÃ¼yÃ¼k baÅŸarÄ±larÄ±ndan biri
9. Hiyeroglif duvarlar â€” her yÃ¼zeyi kaplayan oyma ve boyalÄ± hiyeroglifler, Ramses kartuÅŸlarÄ±, tanrÄ± ve firavun tasvirleri, 3.000 yÄ±ldÄ±r korunmuÅŸ renkli kabartmalar
10. Ã‡Ã¶l yaklaÅŸÄ±mÄ± â€” Nubya Ã§Ã¶lÃ¼nden tapÄ±naklara giden yol, altÄ±n kum, kayalÄ±klar, yaklaÅŸtÄ±kÃ§a kaya yÃ¼zÃ¼nden beliren devasa tapÄ±nak cephesi, ufuktaki serap

ğŸ­ YARDIMCI KARAKTER (en az biri hikayede olsun):
Bilge Scarab BÃ¶ceÄŸi (gÃ¼neÅŸin sÄ±rrÄ±nÄ± bilen, tapÄ±naÄŸÄ±n en karanlÄ±k kÃ¶ÅŸelerinde Ä±ÅŸÄ±k yolu gÃ¶steren altÄ±n kanatlÄ± bÃ¶cek),
KonuÅŸan Hiyeroglif (duvardan ayrÄ±lÄ±p canlanabilen, 3.000 yÄ±llÄ±k hikayeleri anlatan hiyeroglif figÃ¼r),
Cesur Nil BalÄ±kÃ§Ä±l KuÅŸu (Nasser GÃ¶lÃ¼'nden tapÄ±naÄŸa uÃ§an, Nil'in sÄ±rlarÄ±nÄ± bilen zarif kuÅŸ),
NeÅŸeli Kum Kedisi (Ã§Ã¶l kedisi, tapÄ±naÄŸÄ±n gizli odalarÄ±nÄ± ve tÃ¼nellerini bilen kÃ¼Ã§Ã¼k rehber)
veya Bilge Taş Yontucu Sesi (3.000 yıl önce heykelleri oymuş antik ustanın anısı, sanatın ve sabrın sırrını öğreten).
Karakter, tapÄ±naÄŸÄ±n 3.000 yÄ±llÄ±k tarihinden veya Antik MÄ±sÄ±r'Ä±n bÃ¼yÃ¼lÃ¼ dÃ¼nyasÄ±ndan "uyanmÄ±ÅŸ" olabilir.

âš¡ Ã–NEMLÄ° â€” BU BÄ°R GEZÄ° REHBERÄ° DEÄÄ°L, BÄ°R MACERA HÄ°KAYESÄ°!
Abu Simbel TapÄ±naklarÄ± ARKA PLAN olarak kullan. Hikayenin motorunu MEKANLAR DEÄÄ°L,
Ã§ocuÄŸun Ä°Ã‡ YOLCULUÄU ve eÄŸitsel deÄŸerler oluÅŸtursun.

âŒ YANLIÅ: "Ali tapÄ±naÄŸa girdi. Heykelleri gÃ¶rdÃ¼. Sonra Ã§Ä±ktÄ±."
âœ… DOÄRU: Ã‡ocuÄŸun bir SORUNU/ZAYIFLIÄI var. Bu sorun Abu Simbel'in devasa tapÄ±naÄŸÄ±nda
bir MACERA'ya dÃ¶nÃ¼ÅŸÃ¼yor. KaranlÄ±k koridorda yÃ¼rÃ¼rken hiyeroglifler canlanÄ±yor,
gÃ¼neÅŸ Ä±ÅŸÄ±ÄŸÄ± olayÄ± Ã§ocuÄŸu 3.000 yÄ±l Ã¶ncesine taÅŸÄ±yor, Ramses'in dev heykelleri
arasÄ±nda kendini kÃ¼Ã§Ã¼cÃ¼k hissederken BÃœYÃœK ÅŸeyler baÅŸarmayÄ± Ã¶ÄŸreniyor.
Ã‡ocuk antik mÃ¼hendisliÄŸin ve sabrÄ±n gÃ¼cÃ¼nÃ¼ keÅŸfederken KENDÄ°NÄ° keÅŸfediyor.

ğŸ”‘ EÄÄ°TSEL DEÄER ENTEGRASYONU:
SeÃ§ilen eÄŸitsel deÄŸer hikayenin OLAY Ã–RGÃœSÃœNÃœ belirlemeli:
- Azim seÃ§ildiyse â†’ 20 yÄ±l sÃ¼ren tapÄ±nak inÅŸaatÄ±, bir taÅŸ bir taÅŸ sabrÄ±n zaferi
- Merak seÃ§ildiyse â†’ gÃ¼neÅŸ Ä±ÅŸÄ±ÄŸÄ± olayÄ±nÄ±n bilimsel sÄ±rrÄ±, astronomik hassasiyet Ã§ocuÄŸu Ã§eksin
- Cesaret seÃ§ildiyse â†’ 60 metre karanlÄ±k koridorda ilerlemek, bilinmeyene adÄ±m atmak
- Hayal gÃ¼cÃ¼ seÃ§ildiyse â†’ hiyeroglifler canlanÄ±p hikayeler anlatsÄ±n, duvarlar konuÅŸsun
- Ä°ÅŸ birliÄŸi seÃ§ildiyse â†’ UNESCO kurtarma projesi, tÃ¼m dÃ¼nyanÄ±n birlikte Ã§alÄ±ÅŸmasÄ±
DeÄŸer sadece "sÃ¶ylenmesin", Ã§ocuk YAÅAYARAK Ã¶ÄŸrensin!

âš ï¸ Ã–NEMLÄ° KISITLAMALAR:
1. Hikayede DÄ°NÄ° RÄ°TÃœEL veya Ä°BADET SAHNESÄ° OLMAMALIDIR.
   Antik MÄ±sÄ±r tanrÄ±larÄ± "mitolojik figÃ¼rler ve heykel sanatÄ±" olarak sunulsun, inanÃ§ olarak deÄŸil.
2. TapÄ±nak "antik mÃ¼hendislik harikasÄ± ve sanat ÅŸaheseri" olarak sunulsun.
3. GÃ¼neÅŸ Ä±ÅŸÄ±ÄŸÄ± olayÄ± "astronomi ve matematik dahiliÄŸi" perspektifinden.
4. Ramses ve Nefertari "tarihÃ® lider ve kraliÃ§e" olarak, dini figÃ¼r olarak deÄŸil.
5. UNESCO kurtarma projesi "insanlÄ±ÄŸÄ±n ortak mirasÄ±" ve "uluslararasÄ± iÅŸ birliÄŸi" vurgusuyla.

ğŸ¨ SAHNE AÃ‡IKLAMASI KURALLARI (Pass-2 iÃ§in ipucu):
Her sahne iÃ§in spesifik Abu Simbel lokasyonu ve mimari/arkeolojik detay kullan.
Ã–rn: "Ramses'in 20 metrelik dev heykelinin ayaklarÄ±nÄ±n dibinde baÅŸÄ±nÄ± kaldÄ±rÄ±p yukarÄ± bakarken",
"KaranlÄ±k tapÄ±nak koridorunda gÃ¼neÅŸ Ä±ÅŸÄ±ÄŸÄ± demetinin altÄ±n gibi parladÄ±ÄŸÄ± anda",
"Nefertari TapÄ±naÄŸÄ±'nÄ±n Hathor baÅŸlÄ± sÃ¼tunlarÄ± arasÄ±nda kraliÃ§enin kabartmasÄ±na dokunurken",
"Ã‡Ã¶l kumlarÄ±ndan beliren tapÄ±nak cephesini ilk kez uzaktan gÃ¶rÃ¼rken".
Genel ifadelerden kaÃ§Ä±n ("tapÄ±nakta" yerine somut yer adÄ± ve detay kullan)."""


ABUSIMBEL_LOCATION_CONSTRAINTS = """Abu Simbel Temples UNESCO World Heritage Site iconic elements (include 1-2 relevant details depending on the scene):
- Four colossal seated statues of Ramesses II (~20m tall each) carved into the cliff face â€” pharaonic crowns, serene faces, hieroglyphic cartouches
- Temple interior with Osiride pillars, hieroglyphic walls, and dramatic light shafts cutting through darkness
- The golden Nubian desert landscape and Lake Nasser's blue waters in the background
- Distinctive warm golden sandstone of ancient Egyptian monuments
- Sense of monumental scale â€” the child dwarfed by 3,000-year-old colossal architecture"""


ABUSIMBEL_CULTURAL_ELEMENTS = {
    "primary_landmarks": [
        "Great Temple facade with four colossal Ramesses II statues (~20m tall)",
        "Hypostyle hall with eight Osiride pillars and painted ceiling",
        "Inner sanctuary with solar alignment phenomenon (Feb 22 & Oct 22)",
        "Nefertari's Small Temple with Hathor-headed columns",
        "Battle of Kadesh wall reliefs â€” ancient military art masterpiece"
    ],
    "secondary_elements": [
        "Lake Nasser and Nubian desert landscape",
        "UNESCO rescue relocation site (1964-1968 engineering marvel)",
        "Hieroglyphic walls with 3,000-year-old painted reliefs",
        "Desert approach path with temples emerging from cliff face",
        "Pharaonic cartouches and carved friezes on every surface"
    ],
    "cultural_items": [
        "Egyptian double crown (pschent) on Ramesses statues",
        "Scarab beetle motifs symbolizing the sun",
        "Ankh (key of life) symbols carved in stone",
        "Lotus and papyrus column designs",
        "Painted vulture and cobra ceiling motifs (wadjet and nekhbet)"
    ],
    "color_palette": "pharaonic gold sandstone, Nile deep blue, desert amber, hieroglyph colors (Egyptian red, lapis blue, gold leaf, malachite green), shadow purple-brown, sky azure",
    "atmosphere": "monumental, awe-inspiring, ancient, sun-baked, mysterious interior darkness contrasting with blazing exterior light, archaeological wonder",
    "time_periods": [
        "blazing Egyptian sunrise with first golden rays striking the colossal facade",
        "harsh midday desert sun with deep shadows between statues and sharp contrasts",
        "the magical solar alignment â€” a golden beam cutting through 60m of darkness",
        "warm sunset turning sandstone to deep amber-gold, Lake Nasser reflecting purple and orange"
    ]
}


ABUSIMBEL_CUSTOM_INPUTS = [
    {
        "key": "favorite_moment",
        "label": "En HeyecanlÄ± An",
        "type": "select",
        "options": ["GÃ¼neÅŸ IÅŸÄ±ÄŸÄ± OlayÄ±", "Dev Heykelleri Ä°lk GÃ¶rme", "KaranlÄ±k Koridorda YÃ¼rÃ¼yÃ¼ÅŸ", "Ã‡Ã¶lden TapÄ±naÄŸÄ±n Belirmesi"],
        "default": "GÃ¼neÅŸ IÅŸÄ±ÄŸÄ± OlayÄ±",
        "required": False,
        "help_text": "Hikayenin en bÃ¼yÃ¼lÃ¼ sahnesinin konusu"
    },
    {
        "key": "special_discovery",
        "label": "KeÅŸfetmek Ä°stediÄŸi Åey",
        "type": "select",
        "options": ["Ramses'in Gizli OdasÄ±", "KayÄ±p Hiyeroglif HaritasÄ±", "Nefertari'nin Sihirli AynasÄ±", "GÃ¼neÅŸin Matematiksel SÄ±rrÄ±"],
        "default": "Ramses'in Gizli OdasÄ±",
        "required": False,
        "help_text": "Hikayede Ã§ocuÄŸun peÅŸine dÃ¼ÅŸeceÄŸi bÃ¼yÃ¼k gizem"
    },
    {
        "key": "travel_companion",
        "label": "Yol ArkadaÅŸÄ±",
        "type": "select",
        "options": ["Bilge Scarab BÃ¶ceÄŸi", "KonuÅŸan Hiyeroglif", "Cesur Nil KuÅŸu", "NeÅŸeli Kum Kedisi"],
        "default": "Bilge Scarab BÃ¶ceÄŸi",
        "required": False,
        "help_text": "TapÄ±naÄŸÄ±n derinliklerinde Ã§ocuÄŸa eÅŸlik edecek antik dost"
    }
]


async def create_abusimbel_scenario():
    """Abu Simbel TapÄ±naklarÄ± MacerasÄ± senaryosunu oluÅŸtur veya gÃ¼ncelle."""

    print("\n" + "=" * 70)
    print("ABU SÄ°MBEL TAPINAKLARI MACERASI SENARYO OLUÅTURMA")
    print("Master Prompts - PuLID Optimized - Ancient Egyptian Wonder")
    print("=" * 70 + "\n")

    async with async_session_factory() as db:
        result = await db.execute(
            select(Scenario).where(Scenario.name.ilike("%Abu Simbel%"))
        )
        existing = result.scalar_one_or_none()

        if existing:
            print(f"[INFO] Mevcut senaryo bulundu, gÃ¼ncelleniyor... (ID: {existing.id})")
            scenario = existing
        else:
            print("[INFO] Yeni senaryo oluÅŸturuluyor...")
            scenario = Scenario(id=uuid.uuid4())
            db.add(scenario)

        scenario.name = "Abu Simbel TapÄ±naklarÄ± MacerasÄ±"
        scenario.description = (
            "Antik MÄ±sÄ±r'Ä±n en gÃ¶rkemli tapÄ±naÄŸÄ±nda 3.000 yÄ±llÄ±k bir macera! "
            "20 metrelik dev firavun heykelleri, gÃ¼neÅŸ Ä±ÅŸÄ±ÄŸÄ±nÄ±n sÄ±rrÄ±, "
            "canlanan hiyeroglifler ve Nubya Ã§Ã¶lÃ¼nÃ¼n bÃ¼yÃ¼lÃ¼ dÃ¼nyasÄ±!"
        )
        scenario.thumbnail_url = "/scenarios/abusimbel.jpg"
        scenario.cover_prompt_template = ABUSIMBEL_COVER_PROMPT
        scenario.page_prompt_template = ABUSIMBEL_PAGE_PROMPT
        scenario.story_prompt_tr = ABUSIMBEL_STORY_PROMPT_TR
        scenario.ai_prompt_template = None
        scenario.location_constraints = ABUSIMBEL_LOCATION_CONSTRAINTS
        scenario.location_en = "Abu Simbel Temples"
        scenario.cultural_elements = ABUSIMBEL_CULTURAL_ELEMENTS
        scenario.theme_key = "abusimbel"
        scenario.custom_inputs_schema = ABUSIMBEL_CUSTOM_INPUTS
        scenario.is_active = True
        scenario.display_order = 10

        await db.commit()

        print("\n[OK] ABU SÄ°MBEL TAPINAKLARI MACERASI OLUÅTURULDU!\n")
        print("-" * 70)
        print("Senaryo DetaylarÄ±:")
        print(f"  - name: {scenario.name}")
        print(f"  - description: {len(scenario.description)} karakter")
        print(f"  - cover_prompt_template: {len(ABUSIMBEL_COVER_PROMPT)} karakter")
        print(f"  - page_prompt_template: {len(ABUSIMBEL_PAGE_PROMPT)} karakter")
        print(f"  - story_prompt_tr: {len(ABUSIMBEL_STORY_PROMPT_TR)} karakter")
        print("  - location_en: Abu Simbel Temples")
        print(f"  - location_constraints: {len(ABUSIMBEL_LOCATION_CONSTRAINTS)} karakter")
        print(f"  - cultural_elements: {len(json.dumps(ABUSIMBEL_CULTURAL_ELEMENTS))} karakter (JSON)")
        print("  - theme_key: abusimbel")
        print(f"  - custom_inputs_schema: {len(ABUSIMBEL_CUSTOM_INPUTS)} Ã¶zel alan")
        print("-" * 70)

        print("\nÃ–ZEL GÄ°RÄ°Å ALANLARI:")
        for inp in ABUSIMBEL_CUSTOM_INPUTS:
            print(f"  - {inp['label']}: {', '.join(inp['options'][:3])}...")

        print("\n" + "=" * 70)
        print("KAPAK PROMPT Ã–NÄ°ZLEME (ilk 500 karakter):")
        print("-" * 70)
        print(ABUSIMBEL_COVER_PROMPT[:500] + "...")

        print("\n" + "=" * 70)
        print("STORY_PROMPT_TR Ã–NÄ°ZLEME (ilk 500 karakter):")
        print("-" * 70)
        print(ABUSIMBEL_STORY_PROMPT_TR[:500] + "...")

        print("\n" + "=" * 70)
        print("Abu Simbel TapÄ±naklarÄ± MacerasÄ± senaryosu hazÄ±r!")
        print("Ã‡ocuklar artÄ±k 3.000 yÄ±llÄ±k firavun tapÄ±naÄŸÄ±nda bÃ¼yÃ¼lÃ¼ bir keÅŸfe Ã§Ä±kabilir!")
        print("=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(create_abusimbel_scenario())


