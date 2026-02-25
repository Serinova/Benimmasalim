"""
GÃ¶beklitepe MacerasÄ± Senaryosu - Master Prompt OluÅŸturma

Bu script, GÃ¶beklitepe MacerasÄ± senaryosunu profesyonel, tutarlÄ± ve
kÃ¼ltÃ¼rel aÃ§Ä±dan zengin prompt'larla oluÅŸturur veya gÃ¼nceller.

Ã–NEMLÄ° - PuLID UYUMLULUK:
- Fiziksel Ã¶zellikler YASAK (saÃ§, gÃ¶z, ten rengi) - PuLID fotoÄŸraftan alÄ±yor
- {clothing_description} zorunlu - kÄ±yafet tutarlÄ±lÄ±ÄŸÄ± iÃ§in
- Sahne aÃ§Ä±klamalarÄ± ACTION-ONLY - stil StyleConfig'den geliyor
- YÃ¼z kimliÄŸi korunmalÄ± - "Bu kesin benim Ã§ocuÄŸum" hissi

Ã‡alÄ±ÅŸtÄ±rma:
    cd backend
    python -m scripts.create_gobeklitepe_scenario
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
# GÃ–BEKLÄ°TEPE MACERASI - MASTER PROMPT TEMPLATES
# =============================================================================

# -----------------------------------------------------------------------------
# KAPAK PROMPT TEMPLATE
# -----------------------------------------------------------------------------
# Kapak: Epik, kahramanca poz, GÃ¶beklitepe'nin en ikonik gÃ¶rÃ¼nÃ¼mÃ¼
# Format: Dikey (768x1024), poster tarzÄ±, baÅŸlÄ±k alanÄ± yukarÄ±da
# PuLID: YÃ¼z referans fotoÄŸraftan, fiziksel Ã¶zellik yazÄ±lmaz
# -----------------------------------------------------------------------------

GOBEKLITEPE_COVER_PROMPT = """A breathtaking children's book cover illustration.

SCENE COMPOSITION:
A young child {scene_description}, standing in awe before the ancient megalithic pillars of GÃ¶beklitepe, the world's oldest known temple, in southeastern Turkey.

ICONIC BACKGROUND ELEMENTS (include 2-3 key details):
- Massive T-shaped limestone pillars (3-5 meters tall) with intricate animal carvings â€” foxes, lions, snakes, and birds etched into the stone
- Circular stone enclosures with concentric rings of pillars, partially excavated from the earth
- The vast Harran Plain stretching to the horizon under a dramatic sky
- Rolling golden-brown hills of the ÅanlÄ±urfa steppe landscape
- Ancient stone walls connecting the pillars, showing the earliest known architecture
- Scattered wildflowers and dry grasses around the archaeological site

LIGHTING & ATMOSPHERE:
- Magical golden hour light casting long dramatic shadows from the towering pillars
- Warm amber and honey tones across the ancient limestone
- A vast, epic sky with scattered clouds lit by the setting or rising sun
- Sense of deep mystery and ancient wonder â€” 12,000 years of history
- Warm earth tones: golden sandstone, dusty amber, sage green, sky blue

CLOTHING:
The child is wearing {clothing_description}.

STYLE:
{visual_style}.

COMPOSITION REQUIREMENTS:
- Professional book cover design with clear title space at the top
- Child positioned in lower third, looking up at the massive pillars with wonder
- Epic cinematic scale showing the monumentality of the ancient pillars
- Balanced composition with T-shaped pillars framing the scene"""


# -----------------------------------------------------------------------------
# Ä°Ã‡ SAYFA PROMPT TEMPLATE
# -----------------------------------------------------------------------------
# Ä°Ã§ Sayfalar: Hikaye anlatÄ±mÄ±, karakter-Ã§evre etkileÅŸimi
# Format: Yatay (1024x768), alt kÄ±sÄ±mda metin alanÄ±
# PuLID: YÃ¼z korunur, kÄ±yafet tutarlÄ±lÄ±ÄŸÄ± Ã¶nemli
# -----------------------------------------------------------------------------

GOBEKLITEPE_PAGE_PROMPT = """A stunning children's book illustration set in and around the ancient site of GÃ¶beklitepe, the world's oldest temple, in southeastern Turkey.

SCENE ACTION:
A young child {scene_description}.

AUTHENTIC GÃ–BEKLITEPE SETTING (vary these elements per scene):
- T-SHAPED PILLARS: Massive limestone megaliths (3-5m tall) with carved reliefs of animals â€” foxes, wild boars, lions, vultures, scorpions, snakes, cranes â€” each carving tells an ancient story
- CIRCULAR ENCLOSURES: Concentric stone rings partially excavated, showing layers of 12,000-year history, connecting walls between pillars
- ARCHAEOLOGICAL DETAILS: Carefully excavated trenches, stone benches between pillars, carved stone bowls, flint tools, ancient grinding stones
- HARRAN PLAIN LANDSCAPE: Rolling golden steppe hills, distant mountains, vast open sky, pistachio orchards, olive groves
- ÅANLIURFA ELEMENTS: Traditional stone-cut houses, the famous BalÄ±klÄ±gÃ¶l (Sacred Fish Pool) with its mosque and courtyard, bazaar alleys with copper crafts
- MUSEUM ARTIFACTS: The Urfa Man statue (world's oldest life-size human sculpture), stone animal figurines, carved totems, obsidian tools

GEOLOGICAL & HISTORICAL ACCURACY:
- Limestone bedrock of the GermuÅŸ Mountains ridge
- Ancient tool marks visible on pillar surfaces
- Partially buried enclosures showing excavation layers
- Stone quarry areas with unfinished pillars still in the bedrock
- Predates Stonehenge by 6,000 years â€” sense of primordial antiquity

LIGHTING OPTIONS (match to scene mood):
- Golden sunrise illuminating the pillar carvings with warm side-light
- Bright midday with deep blue sky and cotton clouds over the steppe
- Warm sunset with dramatic amber light and long pillar shadows
- Mystical starlit night with the Milky Way arching over the ancient pillars

CLOTHING:
The child is wearing {clothing_description}.

STYLE:
{visual_style}.

COMPOSITION:
- Clear focal point on the child in the middle-ground
- Rich, detailed GÃ¶beklitepe background with soft bokeh on distant steppe
- Space at bottom for text overlay (25% of image height)
- Warm, inviting color palette: sandstone gold, amber, sage, terracotta"""


# -----------------------------------------------------------------------------
# AI HÄ°KAYE ÃœRETÄ°M PROMPTU (Gemini Pass-1 iÃ§in)
# Sistemle uyumlu: Placeholder kullanÄ±lmaz. Kahraman, yaÅŸ, eÄŸitsel deÄŸerler
# ana promptta zaten verilir. Bu blok sadece GÃ¶beklitepe Ã¶zel talimatlarÄ±nÄ± iÃ§erir.
# -----------------------------------------------------------------------------

GOBEKLITEPE_STORY_PROMPT_TR = """Sen Ã¶dÃ¼llÃ¼ Ã§ocuk kitabÄ± yazarÄ± ve GÃ¶beklitepe/arkeoloji uzmanÄ±sÄ±n.
Kahraman, yaÅŸ ve eÄŸitsel deÄŸerler yukarÄ±da verilmiÅŸtir. GÃ¶revin: GÃ¶beklitepe'de geÃ§en bÃ¼yÃ¼lÃ¼ bir macera yazmak.

ğŸ“ GÃ–BEKLÄ°TEPE â€” KULLANILACAK KÃœLTÃœREL MEKANLAR (hikayeye en az 6 tanesini entegre et):
1. T-biÃ§imli dev dikilitaÅŸlar â€” hayvan kabartmalarÄ± (tilki, aslan, yÄ±lan, akbaba, akrep), her taÅŸÄ±n bir hikayesi var
2. Dairesel taÅŸ yapÄ±lar â€” iÃ§ iÃ§e halkalar, dÃ¼nyanÄ±n en eski tapÄ±naÄŸÄ±, 12.000 yÄ±llÄ±k gizem
3. TaÅŸ ocaÄŸÄ± alanÄ± â€” yarÄ±m kalmÄ±ÅŸ dev dikilitaÅŸlar hÃ¢lÃ¢ ana kayaya baÄŸlÄ±, antik taÅŸ ustalarÄ±
4. Arkeolojik kazÄ± alanlarÄ± â€” tabaka tabaka tarih, topraktan Ã§Ä±kan sÄ±rlar
5. ÅanlÄ±urfa Arkeoloji MÃ¼zesi â€” Urfa AdamÄ± (dÃ¼nyanÄ±n en eski insan heykeli), taÅŸ figÃ¼rinler, obsidyen aletler
6. BalÄ±klÄ±gÃ¶l (Kutsal BalÄ±k GÃ¶lÃ¼) â€” efsanevi kutsal balÄ±klar, tarihi havuz, huzurlu bahÃ§e
7. Harran KÃ¼mbet Evleri â€” konik toprak evler, antik Harran Ãœniversitesi kalÄ±ntÄ±larÄ±
8. GÃ¶beklitepe tepesi â€” Harran OvasÄ±'na hakim panoramik manzara, gÃ¶kyÃ¼zÃ¼ gÃ¶zlemi
9. ÅanlÄ±urfa Ã§arÅŸÄ±sÄ± â€” bakÄ±rcÄ±lar, baharat satÄ±cÄ±larÄ±, geleneksel el sanatlarÄ±
10. Karahantepe â€” GÃ¶beklitepe'nin "kardeÅŸ" arkeolojik alanÄ±, yeni keÅŸifler

ğŸ­ YARDIMCI KARAKTER (en az biri hikayede olsun):
Bilge Tilki (dikilitaÅŸtaki tilki kabartmasÄ±ndan esinlenmiÅŸ), Cesur Akbaba, Gizemli YÄ±lan,
MeraklÄ± Akrep veya KonuÅŸan Turna kuÅŸu. Hayvan, dikilitaÅŸlardaki kabartmalardan "canlanmÄ±ÅŸ" olabilir.
Ã‡ocuk macerayÄ± bu dostuyla yaÅŸasÄ±n. YardÄ±mcÄ± karakter MENTOR rolÃ¼ Ã¼stlenebilir.

âš¡ Ã–NEMLI â€” BU BÄ°R GEZÄ° REHBERÄ° DEÄÄ°L, BÄ°R MACERA HÄ°KAYESÄ°!
GÃ¶beklitepe mekanlarÄ± ARKA PLAN olarak kullan. Hikayenin motorunu MEKANLAR DEÄÄ°L,
Ã§ocuÄŸun Ä°Ã‡ YOLCULUÄU ve eÄŸitsel deÄŸerler oluÅŸtursun.

âŒ YANLIÅ: "Ali dikilitaÅŸlarÄ± gÃ¶rdÃ¼. Sonra mÃ¼zeye gitti. Sonra balÄ±klara baktÄ±."
âœ… DOÄRU: Ã‡ocuÄŸun bir SORUNU/ZAYIFLIÄI var. Bu sorun GÃ¶beklitepe'nin gizemli mekanlarÄ±nda
bir MACERA'ya dÃ¶nÃ¼ÅŸÃ¼yor. DikilitaÅŸlardaki hayvan kabartmalarÄ± "canlanÄ±yor" ve Ã§ocuÄŸa
12.000 yÄ±l Ã¶ncesinden gelen bir bilgelik Ã¶ÄŸretiyor. Ã‡ocuk antik gizemi Ã§Ã¶zerken KENDÄ°NÄ° keÅŸfediyor.

ğŸ”‘ EÄÄ°TSEL DEÄER ENTEGRASYONU:
SeÃ§ilen eÄŸitsel deÄŸer hikayenin OLAY Ã–RGÃœSÃœNÃœ belirlemeli:
- Cesaret seÃ§ildiyse â†’ Ã§ocuÄŸun korkusu olsun, karanlÄ±k yeraltÄ± geÃ§itlerinden geÃ§mek zorunda kalsÄ±n
- SabÄ±r seÃ§ildiyse â†’ Ã§ocuk acele etsin, arkeolojik bulmacayÄ± Ã§Ã¶zmek iÃ§in sabretmesi gereksin
- PaylaÅŸmak seÃ§ildiyse â†’ Ã§ocuk keÅŸfettiÄŸi sÄ±rrÄ± paylaÅŸarak herkesin faydalanmasÄ±nÄ± saÄŸlasÄ±n
- Merak seÃ§ildiyse â†’ Ã§ocuÄŸun sorularÄ± onu daha derin gizemlere gÃ¶tÃ¼rsÃ¼n
DeÄŸer sadece "sÃ¶ylenmesin", Ã§ocuk YAÅAYARAK Ã¶ÄŸrensin!

âš ï¸ Ã–NEMLÄ° KISITLAMA:
Hikayede DÄ°NÄ° RÄ°TÃœEL veya Ä°BADET SAHNESI OLMAMALIDIR.
GÃ¶beklitepe'nin gizemi arkeolojik ve bilimsel merak perspektifinden iÅŸlensin.
Ã‡ocuk doÄŸal oluÅŸumlarÄ±, antik yapÄ±larÄ±, hayvan kabartmalarÄ±nÄ± ve kÃ¼ltÃ¼rel mirasÄ± keÅŸfetsin.

ğŸ¨ SAHNE AÃ‡IKLAMASI KURALLARI (Pass-2 iÃ§in ipucu):
Her sahne iÃ§in spesifik GÃ¶beklitepe lokasyonu ve arkeolojik detay kullan.
Ã–rn: "Enclosure D'nin dev tilki kabartmalÄ± dikilitaÅŸlarÄ± Ã¶nÃ¼nde", "ÅanlÄ±urfa MÃ¼zesi'nde Urfa AdamÄ± heykeli karÅŸÄ±sÄ±nda",
"BalÄ±klÄ±gÃ¶l'Ã¼n huzurlu sularÄ±nda kutsal balÄ±klarÄ± izlerken", "taÅŸ ocaÄŸÄ±nda yarÄ±m kalmÄ±ÅŸ dev dikilitaÅŸÄ±n yanÄ±nda".
Genel ifadelerden kaÃ§Ä±n ("GÃ¶beklitepe'de", "taÅŸlarÄ±n yanÄ±nda" yerine somut yer adÄ± ve detay kullan)."""


# -----------------------------------------------------------------------------
# LOKASYON KISITLAMALARI
# -----------------------------------------------------------------------------

GOBEKLITEPE_LOCATION_CONSTRAINTS = """GÃ¶beklitepe iconic elements (include 1-2 relevant details depending on the scene):
- T-shaped megalithic pillars with animal relief carvings (fox, lion, snake, vulture, scorpion)
- Circular stone enclosures showing the world's oldest known temple architecture
- Harran Plain steppe landscape with golden-brown rolling hills
- Archaeological excavation details (layers, trenches, tools)
- ÅanlÄ±urfa regional cultural elements (stone houses, sacred fish pool, copper crafts)"""


# -----------------------------------------------------------------------------
# KÃœLTÃœREL ELEMENTLER (JSON)
# -----------------------------------------------------------------------------

GOBEKLITEPE_CULTURAL_ELEMENTS = {
    "primary_landmarks": [
        "T-shaped megalithic pillars with animal carvings",
        "circular stone enclosures (Enclosure A, B, C, D)",
        "Harran Plain panoramic vista from the hilltop",
        "ÅanlÄ±urfa Archaeological Museum (Urfa Man statue)",
        "BalÄ±klÄ±gÃ¶l (Sacred Fish Pool)"
    ],
    "secondary_elements": [
        "stone quarry with unfinished pillars still in bedrock",
        "Harran beehive houses (kÃ¼mbet evler)",
        "Karahantepe sister site",
        "ancient grinding stones and flint tools",
        "ÅanlÄ±urfa historic bazaar"
    ],
    "cultural_items": [
        "animal relief carvings on pillars (fox, vulture, scorpion, snake, crane)",
        "Urfa Man statue replica (world's oldest human sculpture)",
        "obsidian tools and stone bowls",
        "traditional copper crafts from ÅanlÄ±urfa bazaar",
        "local pistachio and pomegranate motifs"
    ],
    "color_palette": "golden sandstone, warm amber, dusty terracotta, sage green steppe, deep sky blue, sunset oranges",
    "atmosphere": "ancient, mysterious, awe-inspiring, archaeological wonder, timeless",
    "time_periods": [
        "golden sunrise casting side-light on pillar carvings",
        "bright midday with blue sky over the steppe",
        "amber sunset with long pillar shadows",
        "starlit night with Milky Way over the ancient temple"
    ]
}


# -----------------------------------------------------------------------------
# Ã–ZEL GÄ°RÄ°Å ALANLARI (Custom Inputs)
# -----------------------------------------------------------------------------

GOBEKLITEPE_CUSTOM_INPUTS = [
    {
        "key": "favorite_animal",
        "label": "En SevdiÄŸi DikilitaÅŸ HayvanÄ±",
        "type": "select",
        "options": ["Tilki", "Aslan", "YÄ±lan", "Akbaba", "Akrep", "Turna KuÅŸu"],
        "default": "Tilki",
        "required": False,
        "help_text": "Hikayede bu hayvan dikilitaÅŸtan canlanacak ve Ã§ocuÄŸa rehberlik edecek"
    },
    {
        "key": "special_discovery",
        "label": "KeÅŸfetmek Ä°stediÄŸi Åey",
        "type": "select",
        "options": ["Gizli YeraltÄ± OdasÄ±", "KayÄ±p DikilitaÅŸ", "Antik Harita", "Sihirli TaÅŸ FigÃ¼rini"],
        "default": "Gizli YeraltÄ± OdasÄ±",
        "required": False,
        "help_text": "Hikayede Ã§ocuÄŸun keÅŸfedeceÄŸi bÃ¼yÃ¼k sÄ±r"
    },
    {
        "key": "travel_companion",
        "label": "Yol ArkadaÅŸÄ±",
        "type": "select",
        "options": ["Bilge Tilki", "Cesur Akbaba", "MeraklÄ± Akrep", "Gizemli YÄ±lan"],
        "default": "Bilge Tilki",
        "required": False,
        "help_text": "GÃ¶beklitepe'de Ã§ocuÄŸa eÅŸlik edecek dikilitaÅŸ hayvan arkadaÅŸ"
    }
]


async def create_gobeklitepe_scenario():
    """GÃ¶beklitepe MacerasÄ± senaryosunu oluÅŸtur veya gÃ¼ncelle."""

    print("\n" + "=" * 70)
    print("GÃ–BEKLÄ°TEPE MACERASI SENARYO OLUÅTURMA")
    print("Master Prompts - PuLID Optimized - Archaeological Wonder")
    print("=" * 70 + "\n")

    async with async_session_factory() as db:
        # Mevcut senaryoyu kontrol et
        result = await db.execute(
            select(Scenario).where(Scenario.name.ilike("%GÃ¶beklitepe%"))
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
        scenario.name = "GÃ¶beklitepe MacerasÄ±"
        scenario.description = (
            "DÃ¼nyanÄ±n en eski tapÄ±naÄŸÄ± GÃ¶beklitepe'de 12.000 yÄ±llÄ±k bir gizemi Ã§Ã¶z! "
            "Dev dikilitaÅŸlarÄ±n hayvan kabartmalarÄ± canlanÄ±yor, antik taÅŸ ustalarÄ± fÄ±sÄ±ldÄ±yor. "
            "ÅanlÄ±urfa'nÄ±n bÃ¼yÃ¼lÃ¼ topraklarÄ±nda arkeolojik bir macera seni bekliyor!"
        )
        scenario.thumbnail_url = "/scenarios/gobeklitepe.jpg"
        scenario.cover_prompt_template = GOBEKLITEPE_COVER_PROMPT
        scenario.page_prompt_template = GOBEKLITEPE_PAGE_PROMPT
        # V2: story_prompt_tr Ã¶ncelikli
        scenario.story_prompt_tr = GOBEKLITEPE_STORY_PROMPT_TR
        scenario.ai_prompt_template = None  # V2 story_prompt_tr kullanÄ±yor
        scenario.location_constraints = GOBEKLITEPE_LOCATION_CONSTRAINTS
        scenario.location_en = "GÃ¶beklitepe"
        scenario.cultural_elements = GOBEKLITEPE_CULTURAL_ELEMENTS
        scenario.theme_key = "gobeklitepe"
        scenario.custom_inputs_schema = GOBEKLITEPE_CUSTOM_INPUTS
        scenario.is_active = True
        scenario.display_order = 3

        await db.commit()

        print("\n[OK] GÃ–BEKLÄ°TEPE MACERASI OLUÅTURULDU!\n")
        print("-" * 70)
        print("Senaryo DetaylarÄ±:")
        print(f"  - name: {scenario.name}")
        print(f"  - description: {len(scenario.description)} karakter")
        print(f"  - cover_prompt_template: {len(GOBEKLITEPE_COVER_PROMPT)} karakter")
        print(f"  - page_prompt_template: {len(GOBEKLITEPE_PAGE_PROMPT)} karakter")
        print(f"  - story_prompt_tr: {len(GOBEKLITEPE_STORY_PROMPT_TR)} karakter")
        print("  - location_en: GÃ¶beklitepe")
        print(f"  - location_constraints: {len(GOBEKLITEPE_LOCATION_CONSTRAINTS)} karakter")
        print(f"  - cultural_elements: {len(json.dumps(GOBEKLITEPE_CULTURAL_ELEMENTS))} karakter (JSON)")
        print("  - theme_key: gobeklitepe")
        print(f"  - custom_inputs_schema: {len(GOBEKLITEPE_CUSTOM_INPUTS)} Ã¶zel alan")
        print("-" * 70)

        # Custom inputs preview
        print("\nÃ–ZEL GÄ°RÄ°Å ALANLARI:")
        for inp in GOBEKLITEPE_CUSTOM_INPUTS:
            print(f"  - {inp['label']}: {', '.join(inp['options'][:3])}...")

        # Prompt previews
        print("\n" + "=" * 70)
        print("KAPAK PROMPT Ã–NÄ°ZLEME (ilk 500 karakter):")
        print("-" * 70)
        print(GOBEKLITEPE_COVER_PROMPT[:500] + "...")

        print("\n" + "=" * 70)
        print("SAYFA PROMPT Ã–NÄ°ZLEME (ilk 500 karakter):")
        print("-" * 70)
        print(GOBEKLITEPE_PAGE_PROMPT[:500] + "...")

        print("\n" + "=" * 70)
        print("STORY_PROMPT_TR Ã–NÄ°ZLEME (ilk 500 karakter):")
        print("-" * 70)
        print(GOBEKLITEPE_STORY_PROMPT_TR[:500] + "...")

        print("\n" + "=" * 70)
        print("GÃ¶beklitepe MacerasÄ± senaryosu hazÄ±r!")
        print("Ã‡ocuklar artÄ±k 12.000 yÄ±llÄ±k gizemi keÅŸfedebilir!")
        print("=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(create_gobeklitepe_scenario())


