"""
SÃ¼mela ManastÄ±rÄ± MacerasÄ± Senaryosu - Master Prompt OluÅŸturma

Bu script, SÃ¼mela ManastÄ±rÄ± MacerasÄ± senaryosunu profesyonel, tutarlÄ± ve
kÃ¼ltÃ¼rel aÃ§Ä±dan zengin prompt'larla oluÅŸturur veya gÃ¼nceller.

SÃ¼mela ManastÄ±rÄ±: MS 386 civarÄ± kuruluÅŸ, Trabzon/MaÃ§ka, AltÄ±ndere Vadisi.
1.200 metre yÃ¼kseklikte dik kayalÄ±klara oyulmuÅŸ Bizans daÄŸ manastÄ±rÄ±.
Freskler, Ã§ok katlÄ± yapÄ±, Karadeniz ormanlarÄ±. UNESCO GeÃ§ici Listesi.

Ã–NEMLÄ° - PuLID UYUMLULUK:
- Fiziksel Ã¶zellikler YASAK (saÃ§, gÃ¶z, ten rengi) - PuLID fotoÄŸraftan alÄ±yor
- {clothing_description} zorunlu - kÄ±yafet tutarlÄ±lÄ±ÄŸÄ± iÃ§in
- Sahne aÃ§Ä±klamalarÄ± ACTION-ONLY - stil StyleConfig'den geliyor
- YÃ¼z kimliÄŸi korunmalÄ± - "Bu kesin benim Ã§ocuÄŸum" hissi

Ã‡alÄ±ÅŸtÄ±rma:
    cd backend
    python -m scripts.create_sumela_scenario
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
# SÃœMELA MANASTIRI MACERASI - MASTER PROMPT TEMPLATES
# =============================================================================

# -----------------------------------------------------------------------------
# KAPAK PROMPT TEMPLATE
# -----------------------------------------------------------------------------

SUMELA_COVER_PROMPT = """A breathtaking children's book cover illustration.

SCENE COMPOSITION:
A young child {scene_description}, standing on the ancient stone terrace of SÃ¼mela Monastery (Panagia Sumela), dramatically carved into the sheer cliff face of KaradaÄŸ mountain at 1,200 meters altitude, deep in the lush green AltÄ±ndere Valley near Trabzon on Turkey's Black Sea coast.

ICONIC BACKGROUND ELEMENTS (include 2-3 key details):
- The monastery's multi-story stone and timber facade built directly into the vertical rock face â€” windows and balconies clinging to the cliff
- Ancient frescoes partially visible on the outer rock walls and under arched recesses â€” rich Byzantine colors (deep blue, gold, red ochre)
- Dense, emerald-green Karadeniz (Black Sea) temperate rainforest covering the steep valley below â€” towering spruce, fir, and chestnut trees shrouded in mist
- A dramatic waterfall cascading down the cliff beside the monastery
- The winding stone path and stairs carved into the mountainside leading up to the monastery
- Wisps of mountain fog and low clouds drifting through the valley, partially veiling the forest canopy
- Distant layers of misty green mountains fading into the horizon

LIGHTING & ATMOSPHERE:
- Mystical diffused light filtering through mountain fog and forest canopy
- Dappled sunlight breaking through clouds onto the monastery's stone facade
- Deep greens of the Black Sea forests contrasting with the warm grey-brown of ancient stone
- A sense of hidden wonder â€” a secret place carved into the mountain, discovered after a long climb
- Color palette: emerald green, misty grey, warm stone beige, deep forest green, Byzantine gold and blue accents

CLOTHING:
The child is wearing {clothing_description}.

STYLE:
{visual_style}.

COMPOSITION REQUIREMENTS:
- Professional book cover design with clear title space at the top
- Child positioned in lower third, on the monastery terrace looking out over the misty valley
- Epic cinematic scale showing the cliff-face monastery and the vast forested valley below
- The vertical cliff and monastery facade framing the scene with dramatic height"""


# -----------------------------------------------------------------------------
# Ä°Ã‡ SAYFA PROMPT TEMPLATE
# -----------------------------------------------------------------------------

SUMELA_PAGE_PROMPT = """A stunning children's book illustration set in and around the ancient SÃ¼mela Monastery (Panagia Sumela), carved into the cliff face of KaradaÄŸ mountain in the AltÄ±ndere Valley near Trabzon, Turkey's Black Sea coast.

SCENE ACTION:
A young child {scene_description}.

AUTHENTIC SÃœMELA MONASTERY SETTING (vary these elements per scene):
- CLIFF-FACE MONASTERY: Multi-story stone and timber building clinging to the vertical rock face at 1,200m altitude, arched windows, wooden balconies overlooking the valley, stone stairs connecting levels, narrow corridors carved into the rock
- FRESCOED CHAMBERS: Ancient Byzantine frescoes covering walls and ceilings â€” vivid depictions of biblical scenes in deep blue, gold, red ochre, and earth tones; partially weathered paintings revealing layers of history; arched ceilings with religious iconography
- ROCK-CUT CHAPEL: The main church carved deep into the cliff with vaulted ceilings, frescoed walls, stone altar, flickering candlelight atmosphere, the famous icon niche where the sacred image was kept
- SACRED SPRING: A natural spring emerging from the rock inside the monastery â€” cool, clear water flowing through ancient stone channels, said to have healing properties
- MONASTERY COURTYARD: Stone-paved open area with panoramic views of the valley, ancient well, herb garden remnants, stone benches where monks once meditated
- STONE STAIRWAY & PATH: The dramatic winding approach path through dense forest, ancient stone steps carved into the mountainside, moss-covered walls, wooden bridges over streams
- ALTINDERE VALLEY FOREST: Lush temperate rainforest with towering Caucasian spruce, Oriental beech, chestnuts; mossy boulders, ferns, wildflowers; rushing mountain streams with small waterfalls; rich biodiversity â€” deer, bears (in distance), eagles soaring
- WATERFALLS: Several cascading waterfalls near the monastery â€” the main waterfall beside the cliff, smaller falls along the forest path, water mist creating rainbows in sunlight
- MOUNTAIN PANORAMA: Layers of green KaÃ§kar-range foothills fading into misty distance, low clouds weaving between peaks, occasional glimpse of the Black Sea on the distant horizon

GEOLOGICAL & NATURAL ACCURACY:
- Volcanic andesite cliff face with natural caves and overhangs used by the monastery builders
- Lush Colchic temperate rainforest ecosystem â€” one of the greenest regions in Turkey
- Mountain fog and cloud formations characteristic of the Black Sea climate
- Moss, lichen, and ferns growing on the ancient stone surfaces
- Crystal-clear mountain streams fed by snowmelt and rainfall

LIGHTING OPTIONS (match to scene mood):
- Mystical morning with fog drifting through the valley and soft diffused light
- Bright midday with sunbeams breaking through the forest canopy onto the monastery
- Golden afternoon light illuminating the frescoes through arched windows
- Dramatic sunset with warm light on the cliff face while the valley below is in shadow

CLOTHING:
The child is wearing {clothing_description}.

STYLE:
{visual_style}.

COMPOSITION:
- Clear focal point on the child in the middle-ground
- Rich, detailed monastery and forest background with atmospheric depth
- Space at bottom for text overlay (25% of image height)
- Lush color palette: emerald green, misty grey, warm stone, Byzantine gold and blue, forest earth tones"""


# -----------------------------------------------------------------------------
# AI HÄ°KAYE ÃœRETÄ°M PROMPTU (Gemini Pass-1 iÃ§in)
# -----------------------------------------------------------------------------

SUMELA_STORY_PROMPT_TR = """Sen Ã¶dÃ¼llÃ¼ Ã§ocuk kitabÄ± yazarÄ± ve Karadeniz kÃ¼ltÃ¼rÃ¼/Bizans tarihi uzmanÄ±sÄ±n.
Kahraman, yaÅŸ ve eÄŸitsel deÄŸerler yukarÄ±da verilmiÅŸtir. GÃ¶revin: SÃ¼mela ManastÄ±rÄ± ve AltÄ±ndere Vadisi'nde geÃ§en bÃ¼yÃ¼lÃ¼ bir macera yazmak.

ğŸ“ SÃœMELA MANASTIRI â€” KULLANILACAK KÃœLTÃœREL MEKANLAR (hikayeye en az 6 tanesini entegre et):
1. KayalÄ±k manastÄ±r cephesi â€” 1.200 metre yÃ¼kseklikte dik kayalara oyulmuÅŸ Ã§ok katlÄ± yapÄ±, taÅŸ merdivenler, ahÅŸap balkonlar, vadiye bakan kemerli pencereler
2. Fresk odalarÄ± â€” duvarlarÄ± ve tavanlarÄ± kaplayan Bizans freskleri, derin mavi, altÄ±n ve kÄ±rmÄ±zÄ± toprak tonlarÄ±nda kutsal sahneler, yÃ¼zyÄ±llarÄ±n izini taÅŸÄ±yan boya katmanlarÄ±
3. Kayaya oyulmuÅŸ ÅŸapel â€” ana kilise, tonozlu tavan, taÅŸ sunak, mumlarÄ±n titrek Ä±ÅŸÄ±ÄŸÄ±, kutsal ikon niÅŸi
4. Kutsal su kaynaÄŸÄ± â€” kayadan Ã§Ä±kan berrak doÄŸal kaynak, antik taÅŸ kanallardan akan soÄŸuk su, ÅŸifalÄ± olduÄŸuna inanÄ±lan pÄ±nar
5. ManastÄ±r avlusu â€” taÅŸ dÃ¶ÅŸeli aÃ§Ä±k alan, vadinin panoramik manzarasÄ±, eski kuyu, taÅŸ oturma yerleri
6. Orman patikasÄ± â€” yoÄŸun yeÅŸil Karadeniz ormanÄ± iÃ§inden geÃ§en antik taÅŸ yol, yosunlu duvarlar, ahÅŸap kÃ¶prÃ¼ler, dere geÃ§itleri
7. AltÄ±ndere Vadisi ormanÄ± â€” dev ladin ve kÃ¶knar aÄŸaÃ§larÄ±, kestaneler, eÄŸreltiotlarÄ±, yabanÃ§iÃ§ekleri, geyikler, kartallar
8. Åelaleler â€” manastÄ±rÄ±n yanÄ±nda kayalÄ±klardan dÃ¶kÃ¼len ana ÅŸelale, patika boyunca kÃ¼Ã§Ã¼k Ã§aÄŸlayanlar, su sisi ve gÃ¶kkuÅŸaklarÄ±
9. DaÄŸ panoramasÄ± â€” sis arasÄ±ndan gÃ¶rÃ¼nen yeÅŸil KaÃ§kar sÄ±radaÄŸlarÄ±, alÃ§ak bulutlar, uzakta Karadeniz'in parÄ±ltÄ±sÄ±
10. TaÅŸ merdiven yolu â€” manastÄ±ra tÄ±rmanÄ±rken yÃ¼zlerce basamaklÄ± antik taÅŸ merdiven, her dÃ¶nemeÃ§te yeni bir manzara

ğŸ­ YARDIMCI KARAKTER (en az biri hikayede olsun):
Bilge Kartal (vadinin tepesinden her ÅŸeyi gÃ¶ren, manastÄ±rÄ±n eski koruyucusu), MeraklÄ± Sincap (ormanÄ±n her kÃ¶ÅŸesini bilen neÅŸeli rehber),
Gizemli Geyik (sis iÃ§inden beliren, kutsal kaynaÄŸÄ±n sÄ±rrÄ±nÄ± bilen), KonuÅŸan Ã‡eÅŸme Ruhu (kutsal kaynak suyundan doÄŸan, yÃ¼zyÄ±llarÄ±n hikayesini anlatan)
veya Cesur DaÄŸ KeÃ§isi (kayalÄ±klarda zÄ±playan, manastÄ±rÄ±n gizli geÃ§itlerini gÃ¶steren).
Karakter, Karadeniz ormanlarÄ±ndan veya manastÄ±rÄ±n tarihinden "uyanmÄ±ÅŸ" olabilir.

âš¡ Ã–NEMLI â€” BU BÄ°R GEZÄ° REHBERÄ° DEÄÄ°L, BÄ°R MACERA HÄ°KAYESÄ°!
SÃ¼mela mekanlarÄ± ARKA PLAN olarak kullan. Hikayenin motorunu MEKANLAR DEÄÄ°L,
Ã§ocuÄŸun Ä°Ã‡ YOLCULUÄU ve eÄŸitsel deÄŸerler oluÅŸtursun.

âŒ YANLIÅ: "AyÅŸe manastÄ±rÄ± gÃ¶rdÃ¼. Sonra fresklere baktÄ±. Sonra ÅŸelaleye gitti."
âœ… DOÄRU: Ã‡ocuÄŸun bir SORUNU/ZAYIFLIÄI var. Bu sorun SÃ¼mela'nÄ±n gizemli mekanlarÄ±nda
bir MACERA'ya dÃ¶nÃ¼ÅŸÃ¼yor. Freskler "hareket ediyor", kutsal kaynak fÄ±sÄ±ldÄ±yor,
sis iÃ§inden gizemli bir geyik beliriyor. Ã‡ocuk bu daÄŸ manastÄ±rÄ±nÄ±n sÄ±rlarÄ±nÄ±
keÅŸfederken KENDÄ°NÄ° keÅŸfediyor.

ğŸ”‘ EÄÄ°TSEL DEÄER ENTEGRASYONU:
SeÃ§ilen eÄŸitsel deÄŸer hikayenin OLAY Ã–RGÃœSÃœNÃœ belirlemeli:
- Cesaret seÃ§ildiyse â†’ Ã§ocuÄŸun yÃ¼kseklik korkusu olsun, kayalÄ±k merdivenlerden Ã§Ä±kmak zorunda kalsÄ±n
- SabÄ±r seÃ§ildiyse â†’ Ã§ocuk acele etsin, ormandaki patikada kaybolsun, doÄŸru yolu bulmak iÃ§in sabretmesi gereksin
- DoÄŸa sevgisi seÃ§ildiyse â†’ Ã§ocuk baÅŸta ormanÄ± fark etmesin, macera boyunca doÄŸanÄ±n bÃ¼yÃ¼sÃ¼nÃ¼ keÅŸfetsin
- Merak seÃ§ildiyse â†’ fresklerdeki bir ipucu Ã§ocuÄŸu daha derin bir gizeme gÃ¶tÃ¼rsÃ¼n
- Azim seÃ§ildiyse â†’ manastÄ±ra ulaÅŸmak iÃ§in yorucu tÄ±rmanÄ±ÅŸtan vazgeÃ§mek istesin ama devam etsin
DeÄŸer sadece "sÃ¶ylenmesin", Ã§ocuk YAÅAYARAK Ã¶ÄŸrensin!

âš ï¸ Ã–NEMLÄ° KISITLAMA:
Hikayede DÄ°NÄ° RÄ°TÃœEL veya Ä°BADET SAHNESÄ° OLMAMALIDIR.
ManastÄ±r, "daÄŸa oyulmuÅŸ gizemli antik yapÄ±" olarak sunulsun.
Freskler SANAT ESERÄ° olarak, dini merasim olarak DEÄÄ°L.
Kutsal kaynak "doÄŸanÄ±n bÃ¼yÃ¼sÃ¼" olarak, dini obje olarak DEÄÄ°L.
Ã‡ocuk mimariyi, doÄŸayÄ±, sanatÄ± ve tarihsel mirasÄ± keÅŸfetsin.

ğŸ¨ SAHNE AÃ‡IKLAMASI KURALLARI (Pass-2 iÃ§in ipucu):
Her sahne iÃ§in spesifik SÃ¼mela lokasyonu ve doÄŸal/mimari detay kullan.
Ã–rn: "ManastÄ±rÄ±n taÅŸ balkonundan sis kaplÄ± AltÄ±ndere Vadisi'ne bakarken",
"Fresk odasÄ±nda mavi-altÄ±n renk tonlarÄ±ndaki duvar resminin Ã¶nÃ¼nde",
"Yosunlu taÅŸ merdivenlerde tÄ±rmanÄ±rken ÅŸelale sesini duyarak",
"Kutsal kaynaÄŸÄ±n berrak suyuna dokunurken".
Genel ifadelerden kaÃ§Ä±n ("manastÄ±rda" yerine somut yer adÄ± ve detay kullan)."""


# -----------------------------------------------------------------------------
# LOKASYON KISITLAMALARI
# -----------------------------------------------------------------------------

SUMELA_LOCATION_CONSTRAINTS = """SÃ¼mela Monastery iconic elements (include 1-2 relevant details depending on the scene):
- Cliff-face monastery facade built into vertical rock at 1,200m altitude
- Lush Black Sea temperate rainforest (AltÄ±ndere Valley) with towering spruces and mist
- Byzantine frescoes in deep blue, gold, and red ochre tones
- Mountain fog, waterfalls, and dramatic vertical landscape
- Ancient stone stairways and paths through dense forest"""


# -----------------------------------------------------------------------------
# KÃœLTÃœREL ELEMENTLER (JSON)
# -----------------------------------------------------------------------------

SUMELA_CULTURAL_ELEMENTS = {
    "primary_landmarks": [
        "cliff-face monastery facade (multi-story stone/timber at 1,200m)",
        "Byzantine frescoed chambers (deep blue, gold, red ochre)",
        "rock-cut chapel with vaulted ceilings and icon niche",
        "sacred spring emerging from the rock",
        "AltÄ±ndere Valley panoramic viewpoint from monastery terrace"
    ],
    "secondary_elements": [
        "ancient stone stairway approach through forest",
        "waterfalls cascading beside the monastery cliff",
        "monastery courtyard with ancient well",
        "forest path with moss-covered walls and wooden bridges",
        "KaÃ§kar mountain range misty panorama"
    ],
    "cultural_items": [
        "Byzantine frescoes (religious scenes, figures in medieval style)",
        "stone-carved architectural details (arches, columns, niches)",
        "natural spring water channels carved in stone",
        "Karadeniz flora: spruce, beech, chestnut, rhododendron, ferns",
        "mountain wildlife: eagles, deer, squirrels, mountain goats"
    ],
    "color_palette": "emerald green, misty grey-white, warm stone beige, deep forest green, Byzantine gold and ultramarine blue, red ochre fresco accents",
    "atmosphere": "mystical, hidden, enchanted, forest-shrouded, vertigo-inducing, ancient and serene",
    "time_periods": [
        "mystical foggy morning with diffused light through the forest",
        "bright midday with sunbeams onto the monastery facade",
        "golden afternoon light illuminating frescoes through arched windows",
        "dramatic sunset with warm light on cliff face, valley in shadow"
    ]
}


# -----------------------------------------------------------------------------
# Ã–ZEL GÄ°RÄ°Å ALANLARI (Custom Inputs)
# -----------------------------------------------------------------------------

SUMELA_CUSTOM_INPUTS = [
    {
        "key": "favorite_place",
        "label": "En SevdiÄŸi Gizemli Mekan",
        "type": "select",
        "options": ["Fresk OdasÄ±", "Kutsal Kaynak", "TaÅŸ Balkon", "Åelale YanÄ±"],
        "default": "Fresk OdasÄ±",
        "required": False,
        "help_text": "Hikayenin en bÃ¼yÃ¼lÃ¼ sahnesi bu mekanda geÃ§ecek"
    },
    {
        "key": "special_discovery",
        "label": "KeÅŸfetmek Ä°stediÄŸi Åey",
        "type": "select",
        "options": ["Gizli Fresk OdasÄ±", "KayÄ±p Ä°kon", "Sihirli Kaynak Suyu", "Gizemli YeraltÄ± GeÃ§idi"],
        "default": "Gizli Fresk OdasÄ±",
        "required": False,
        "help_text": "Hikayede Ã§ocuÄŸun keÅŸfedeceÄŸi bÃ¼yÃ¼k sÄ±r"
    },
    {
        "key": "travel_companion",
        "label": "Yol ArkadaÅŸÄ±",
        "type": "select",
        "options": ["Bilge Kartal", "MeraklÄ± Sincap", "Gizemli Geyik", "Cesur DaÄŸ KeÃ§isi"],
        "default": "Bilge Kartal",
        "required": False,
        "help_text": "SÃ¼mela'da Ã§ocuÄŸa eÅŸlik edecek orman arkadaÅŸÄ±"
    }
]


async def create_sumela_scenario():
    """SÃ¼mela ManastÄ±rÄ± MacerasÄ± senaryosunu oluÅŸtur veya gÃ¼ncelle."""

    print("\n" + "=" * 70)
    print("SÃœMELA MANASTIRI MACERASI SENARYO OLUÅTURMA")
    print("Master Prompts - PuLID Optimized - Mountain Monastery Wonder")
    print("=" * 70 + "\n")

    async with async_session_factory() as db:
        # Mevcut senaryoyu kontrol et
        result = await db.execute(
            select(Scenario).where(Scenario.name.ilike("%SÃ¼mela%"))
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
        scenario.name = "SÃ¼mela ManastÄ±rÄ± MacerasÄ±"
        scenario.description = (
            "Karadeniz'in sisli ormanlarÄ±nda, 1.200 metre yÃ¼kseklikte kayalara oyulmuÅŸ gizemli manastÄ±rÄ± keÅŸfet! "
            "Canlanan freskler, fÄ±sÄ±ldayan kutsal kaynak ve sis iÃ§inden beliren geyik. "
            "AltÄ±ndere Vadisi'nin bÃ¼yÃ¼lÃ¼ ormanlarÄ±nda unutulmaz bir macera seni bekliyor!"
        )
        scenario.thumbnail_url = "/scenarios/sumela.jpg"
        scenario.cover_prompt_template = SUMELA_COVER_PROMPT
        scenario.page_prompt_template = SUMELA_PAGE_PROMPT
        # V2: story_prompt_tr Ã¶ncelikli
        scenario.story_prompt_tr = SUMELA_STORY_PROMPT_TR
        scenario.ai_prompt_template = None  # V2 story_prompt_tr kullanÄ±yor
        scenario.location_constraints = SUMELA_LOCATION_CONSTRAINTS
        scenario.location_en = "SÃ¼mela Monastery"
        scenario.cultural_elements = SUMELA_CULTURAL_ELEMENTS
        scenario.theme_key = "sumela"
        scenario.custom_inputs_schema = SUMELA_CUSTOM_INPUTS
        scenario.is_active = True
        scenario.display_order = 6

        await db.commit()

        print("\n[OK] SÃœMELA MANASTIRI MACERASI OLUÅTURULDU!\n")
        print("-" * 70)
        print("Senaryo DetaylarÄ±:")
        print(f"  - name: {scenario.name}")
        print(f"  - description: {len(scenario.description)} karakter")
        print(f"  - cover_prompt_template: {len(SUMELA_COVER_PROMPT)} karakter")
        print(f"  - page_prompt_template: {len(SUMELA_PAGE_PROMPT)} karakter")
        print(f"  - story_prompt_tr: {len(SUMELA_STORY_PROMPT_TR)} karakter")
        print("  - location_en: SÃ¼mela Monastery")
        print(f"  - location_constraints: {len(SUMELA_LOCATION_CONSTRAINTS)} karakter")
        print(f"  - cultural_elements: {len(json.dumps(SUMELA_CULTURAL_ELEMENTS))} karakter (JSON)")
        print("  - theme_key: sumela")
        print(f"  - custom_inputs_schema: {len(SUMELA_CUSTOM_INPUTS)} Ã¶zel alan")
        print("-" * 70)

        # Custom inputs preview
        print("\nÃ–ZEL GÄ°RÄ°Å ALANLARI:")
        for inp in SUMELA_CUSTOM_INPUTS:
            print(f"  - {inp['label']}: {', '.join(inp['options'][:3])}...")

        # Prompt previews
        print("\n" + "=" * 70)
        print("KAPAK PROMPT Ã–NÄ°ZLEME (ilk 500 karakter):")
        print("-" * 70)
        print(SUMELA_COVER_PROMPT[:500] + "...")

        print("\n" + "=" * 70)
        print("SAYFA PROMPT Ã–NÄ°ZLEME (ilk 500 karakter):")
        print("-" * 70)
        print(SUMELA_PAGE_PROMPT[:500] + "...")

        print("\n" + "=" * 70)
        print("STORY_PROMPT_TR Ã–NÄ°ZLEME (ilk 500 karakter):")
        print("-" * 70)
        print(SUMELA_STORY_PROMPT_TR[:500] + "...")

        print("\n" + "=" * 70)
        print("SÃ¼mela ManastÄ±rÄ± MacerasÄ± senaryosu hazÄ±r!")
        print("Ã‡ocuklar artÄ±k Karadeniz'in gizemli daÄŸ manastÄ±rÄ±nÄ± keÅŸfedebilir!")
        print("=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(create_sumela_scenario())


