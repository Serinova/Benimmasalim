"""
Efes Antik Kent MacerasÄ± Senaryosu - Master Prompt OluÅŸturma

Bu script, Efes Antik Kent MacerasÄ± senaryosunu profesyonel, tutarlÄ± ve
kÃ¼ltÃ¼rel aÃ§Ä±dan zengin prompt'larla oluÅŸturur veya gÃ¼nceller.

Ã–NEMLÄ° - PuLID UYUMLULUK:
- Fiziksel Ã¶zellikler YASAK (saÃ§, gÃ¶z, ten rengi) - PuLID fotoÄŸraftan alÄ±yor
- {clothing_description} zorunlu - kÄ±yafet tutarlÄ±lÄ±ÄŸÄ± iÃ§in
- Sahne aÃ§Ä±klamalarÄ± ACTION-ONLY - stil StyleConfig'den geliyor
- YÃ¼z kimliÄŸi korunmalÄ± - "Bu kesin benim Ã§ocuÄŸum" hissi

Ã‡alÄ±ÅŸtÄ±rma:
    cd backend
    python -m scripts.create_efes_scenario
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
# EFES ANTÄ°K KENT MACERASI - MASTER PROMPT TEMPLATES
# =============================================================================

# -----------------------------------------------------------------------------
# KAPAK PROMPT TEMPLATE
# -----------------------------------------------------------------------------
# Kapak: Epik, kahramanca poz, Efes'in en ikonik gÃ¶rÃ¼nÃ¼mÃ¼ (Celsus KÃ¼tÃ¼phanesi)
# Format: Dikey (768x1024), poster tarzÄ±, baÅŸlÄ±k alanÄ± yukarÄ±da
# PuLID: YÃ¼z referans fotoÄŸraftan, fiziksel Ã¶zellik yazÄ±lmaz
# -----------------------------------------------------------------------------

EFES_COVER_PROMPT = """A breathtaking children's book cover illustration.

SCENE COMPOSITION:
A young child {scene_description}, standing in wonder before the magnificent Library of Celsus in the ancient city of Ephesus, one of the best-preserved Greco-Roman cities in the world, on the Aegean coast of Turkey.

ICONIC BACKGROUND ELEMENTS (include 2-3 key details):
- The grand two-story facade of the Library of Celsus with its ornate Corinthian columns, carved statues in niches, and triangular/curved pediments
- Marble-paved Curetes Street stretching behind with ancient column ruins on both sides
- Scattered ancient marble columns and capitals with intricate carvings lying artfully on the ground
- The warm golden-white marble characteristic of Ephesus gleaming in sunlight
- Lush Mediterranean vegetation â€” cypress trees, olive groves, wild poppies peeking between stones
- Distant rolling Aegean hillsides with green Mediterranean scrub

LIGHTING & ATMOSPHERE:
- Warm golden hour light casting dramatic shadows through the ancient columns
- Soft Mediterranean sunlight filtering through scattered clouds
- The white marble glowing warmly in golden light
- Sense of grandeur, ancient civilization, and archaeological wonder
- Color palette: warm marble white, golden honey, Mediterranean blue sky, olive green, terracotta accents

CLOTHING:
The child is wearing {clothing_description}.

STYLE:
{visual_style}.

COMPOSITION REQUIREMENTS:
- Professional book cover design with clear title space at the top
- Child positioned in lower third, gazing up at the towering Library of Celsus facade
- Epic cinematic scale emphasizing the monumentality of the ancient architecture
- Balanced composition with Celsus Library columns framing the scene"""


# -----------------------------------------------------------------------------
# Ä°Ã‡ SAYFA PROMPT TEMPLATE
# -----------------------------------------------------------------------------
# Ä°Ã§ Sayfalar: Hikaye anlatÄ±mÄ±, karakter-Ã§evre etkileÅŸimi
# Format: Yatay (1024x768), alt kÄ±sÄ±mda metin alanÄ±
# PuLID: YÃ¼z korunur, kÄ±yafet tutarlÄ±lÄ±ÄŸÄ± Ã¶nemli
# -----------------------------------------------------------------------------

EFES_PAGE_PROMPT = """A stunning children's book illustration set in and around the ancient city of Ephesus, one of the greatest Greco-Roman cities on the Aegean coast of Turkey.

SCENE ACTION:
A young child {scene_description}.

AUTHENTIC EPHESUS SETTING (vary these elements per scene):
- LIBRARY OF CELSUS: Grand two-story marble facade with four female wisdom statues (Sophia, Arete, Ennoia, Episteme), ornate Corinthian columns, carved reliefs, and monumental entrance
- GREAT THEATRE: Massive 25,000-seat amphitheatre carved into the hillside, semicircular seating rows, dramatic stage building with columns, overlooking the ancient harbor road
- CURETES STREET: Marble-paved main boulevard lined with columns, mosaic sidewalks, carved reliefs, ancient shop fronts, and honorific statues
- TERRACE HOUSES: Luxurious Roman villas with stunning floor mosaics, colorful frescoes on walls, private courtyards with fountains, heating systems under floors
- TEMPLE OF ARTEMIS: Remnants of one of the Seven Wonders of the Ancient World, single standing column, scattered marble fragments, reflecting the former grandeur
- HADRIAN'S TEMPLE: Elegant small temple with ornate arch featuring Tyche (goddess of fortune) relief, Corinthian columns, and detailed mythological friezes
- MARBLE STREET & AGORA: Wide stone-paved commercial roads, ancient marketplace with column-lined stoas, stone merchant stalls
- HARBOR STREET (ARCADIAN WAY): Grand colonnaded avenue leading to the ancient harbor, once lit by oil lamps at night, column capitals with carved eagles

ARCHAEOLOGICAL & HISTORICAL ACCURACY:
- White and golden marble surfaces worn smooth by centuries
- Intricate mosaic floors with geometric and mythological patterns
- Column drums and capitals scattered artfully around the site
- Ancient Greek and Latin inscriptions carved into stone
- Mediterranean climate vegetation: olive trees, cypress, wild herbs growing between ruins
- Distant view of Aegean Sea from hilltop locations

LIGHTING OPTIONS (match to scene mood):
- Golden Mediterranean morning with warm light on marble facades
- Bright midday with deep blue Aegean sky and crisp column shadows
- Warm sunset casting amber and rose light through ancient arches
- Soft overcast day with mystical atmosphere and dramatic ruins

CLOTHING:
The child is wearing {clothing_description}.

STYLE:
{visual_style}.

COMPOSITION:
- Clear focal point on the child in the middle-ground
- Rich, detailed Ephesus background with soft bokeh on distant Aegean landscape
- Space at bottom for text overlay (25% of image height)
- Warm, inviting color palette: marble white, golden honey, Mediterranean blue, olive green, terracotta"""


# -----------------------------------------------------------------------------
# AI HÄ°KAYE ÃœRETÄ°M PROMPTU (Gemini Pass-1 iÃ§in)
# Sistemle uyumlu: Placeholder kullanÄ±lmaz. Kahraman, yaÅŸ, eÄŸitsel deÄŸerler
# ana promptta zaten verilir. Bu blok sadece Efes Ã¶zel talimatlarÄ±nÄ± iÃ§erir.
# -----------------------------------------------------------------------------

EFES_STORY_PROMPT_TR = """Sen Ã¶dÃ¼llÃ¼ Ã§ocuk kitabÄ± yazarÄ± ve Efes/antik Ã§aÄŸ uzmanÄ±sÄ±n.
Kahraman, yaÅŸ ve eÄŸitsel deÄŸerler yukarÄ±da verilmiÅŸtir. GÃ¶revin: Efes Antik Kenti'nde geÃ§en bÃ¼yÃ¼lÃ¼ bir macera yazmak.

ğŸ“ EFES ANTÄ°K KENTÄ° â€” KULLANILACAK KÃœLTÃœREL MEKANLAR (hikayeye en az 6 tanesini entegre et):
1. Celsus KÃ¼tÃ¼phanesi â€” devasa iki katlÄ± mermer cephe, bilgelik heykelleri (Sophia, Arete, Ennoia, Episteme), antik dÃ¼nyanÄ±n en bÃ¼yÃ¼k kÃ¼tÃ¼phanelerinden biri
2. BÃ¼yÃ¼k Tiyatro â€” 25.000 kiÅŸilik dev amfi tiyatro, akustik harikasÄ±, sahne binasÄ±, gladyatÃ¶r gÃ¶sterileri
3. Kuretes Caddesi â€” mermer dÃ¶ÅŸeli ana bulvar, sÃ¼tunlar, mozaikler, antik dÃ¼kkanlar, onur heykelleri
4. YamaÃ§ Evler â€” zengin RomalÄ±larÄ±n lÃ¼ks villalarÄ±, taban mozaikleri, renkli duvar freskleri, Ã¶zel avlular
5. Artemis TapÄ±naÄŸÄ± â€” DÃ¼nyanÄ±n Yedi HarikasÄ±'ndan biri, tek ayakta kalan sÃ¼tun, antik dÃ¼nyanÄ±n en Ã¼nlÃ¼ tapÄ±naÄŸÄ±
6. Hadrian TapÄ±naÄŸÄ± â€” zarif kemer, Tyche kabartmasÄ±, mitolojik frizler, Korint sÃ¼tunlarÄ±
7. Mermer Cadde ve Agora â€” taÅŸ dÃ¶ÅŸeli ticaret yollarÄ±, sÃ¼tunlu stoa, taÅŸ tezgahlar
8. Liman Caddesi (Arkadian Yol) â€” gÃ¶rkemli sÃ¼tunlu bulvar, antik limana giden yol, gece yaÄŸ lambalarÄ±
9. Meryem Ana Evi â€” BÃ¼lbÃ¼ldaÄŸÄ±'nÄ±n huzurlu yamaÃ§larÄ±nda, zeytin aÄŸaÃ§larÄ± arasÄ±nda
10. Efes Arkeoloji MÃ¼zesi â€” Artemis heykeli, gladyatÃ¶r kabartmalarÄ±, altÄ±n sikkeler, antik takÄ±lar

ğŸ­ YARDIMCI KARAKTER (en az biri hikayede olsun):
Bilge BaykuÅŸ (Athena'nÄ±n kutsal kuÅŸu), Cesur Yunus (Ege Denizi'nden), MeraklÄ± Kedi (antik Efes sokaklarÄ±ndan),
NeÅŸeli KaplumbaÄŸa (mozaiklerden esinlenmiÅŸ) veya KonuÅŸan Mermer Heykel. Hayvan veya heykel,
antik dÃ¶nemden "uyanmÄ±ÅŸ" olabilir. Ã‡ocuk macerayÄ± bu dostuyla yaÅŸasÄ±n.

âš¡ Ã–NEMLI â€” BU BÄ°R GEZÄ° REHBERÄ° DEÄÄ°L, BÄ°R MACERA HÄ°KAYESÄ°!
Efes mekanlarÄ± ARKA PLAN olarak kullan. Hikayenin motorunu MEKANLAR DEÄÄ°L,
Ã§ocuÄŸun Ä°Ã‡ YOLCULUÄU ve eÄŸitsel deÄŸerler oluÅŸtursun.

âŒ YANLIÅ: "Ali Celsus KÃ¼tÃ¼phanesi'ni gÃ¶rdÃ¼. Sonra tiyatroya gitti. Sonra YamaÃ§ Evler'i gezdi."
âœ… DOÄRU: Ã‡ocuÄŸun bir SORUNU/ZAYIFLIÄI var. Bu sorun Efes'in bÃ¼yÃ¼lÃ¼ antik mekanlarÄ±nda
bir MACERA'ya dÃ¶nÃ¼ÅŸÃ¼yor. Mermer heykeller "canlanÄ±yor", mozaikler sÄ±rlar fÄ±sÄ±ldÄ±yor ve Ã§ocuk
2.000 yÄ±llÄ±k bilgeliÄŸi keÅŸfederken KENDÄ°NÄ° keÅŸfediyor.

ğŸ”‘ EÄÄ°TSEL DEÄER ENTEGRASYONU:
SeÃ§ilen eÄŸitsel deÄŸer hikayenin OLAY Ã–RGÃœSÃœNÃœ belirlemeli:
- Cesaret seÃ§ildiyse â†’ Ã§ocuÄŸun korkusu olsun, BÃ¼yÃ¼k Tiyatro'nun karanlÄ±k sahne arkasÄ±na girmek zorunda kalsÄ±n
- SabÄ±r seÃ§ildiyse â†’ Ã§ocuk acele etsin, mozaik bulmacayÄ± Ã§Ã¶zmek iÃ§in sabretmesi gereksin
- PaylaÅŸmak seÃ§ildiyse â†’ Ã§ocuk keÅŸfettiÄŸi bilgeliÄŸi baÅŸkalarÄ±yla paylaÅŸarak herkesin faydalanmasÄ±nÄ± saÄŸlasÄ±n
- Merak seÃ§ildiyse â†’ Ã§ocuÄŸun sorularÄ± onu Celsus KÃ¼tÃ¼phanesi'nin gizli odalarÄ±na gÃ¶tÃ¼rsÃ¼n
DeÄŸer sadece "sÃ¶ylenmesin", Ã§ocuk YAÅAYARAK Ã¶ÄŸrensin!

âš ï¸ Ã–NEMLÄ° KISITLAMA:
Hikayede DÄ°NÄ° RÄ°TÃœEL veya Ä°BADET SAHNESI OLMAMALIDIR.
Efes'in gizemi tarihsel, arkeolojik ve bilimsel merak perspektifinden iÅŸlensin.
Ã‡ocuk antik mimariyi, sanatÄ±, mÃ¼hendisliÄŸi ve kÃ¼ltÃ¼rel mirasÄ± keÅŸfetsin.

ğŸ¨ SAHNE AÃ‡IKLAMASI KURALLARI (Pass-2 iÃ§in ipucu):
Her sahne iÃ§in spesifik Efes lokasyonu ve arkeolojik detay kullan.
Ã–rn: "Celsus KÃ¼tÃ¼phanesi'nin Sophia heykeli Ã¶nÃ¼nde", "BÃ¼yÃ¼k Tiyatro'nun en Ã¼st sÄ±rasÄ±ndan Ege'ye bakarken",
"YamaÃ§ Evler'in mozaik dÃ¶ÅŸemeli salonunda", "Kuretes Caddesi'nin mermer kaldÄ±rÄ±mlarÄ±nda yÃ¼rÃ¼rken".
Genel ifadelerden kaÃ§Ä±n ("Efes'te", "sÃ¼tunlarÄ±n yanÄ±nda" yerine somut yer adÄ± ve detay kullan)."""


# -----------------------------------------------------------------------------
# LOKASYON KISITLAMALARI
# -----------------------------------------------------------------------------

EFES_LOCATION_CONSTRAINTS = """Ephesus ancient city iconic elements (include 1-2 relevant details depending on the scene):
- Greco-Roman marble architecture: columns, pediments, arches, carved reliefs
- Library of Celsus facade or similar monumental structures
- Marble-paved streets and ancient column ruins
- Mediterranean vegetation (olive trees, cypress, wild herbs)
- Aegean coastal landscape visible from hilltop locations"""


# -----------------------------------------------------------------------------
# KÃœLTÃœREL ELEMENTLER (JSON)
# -----------------------------------------------------------------------------

EFES_CULTURAL_ELEMENTS = {
    "primary_landmarks": [
        "Library of Celsus (grand two-story marble facade)",
        "Great Theatre (25,000-seat amphitheatre)",
        "Curetes Street (marble-paved boulevard)",
        "Terrace Houses (Roman villas with mosaics)",
        "Temple of Artemis (one of Seven Wonders)"
    ],
    "secondary_elements": [
        "Hadrian's Temple (ornate arch with Tyche relief)",
        "Harbor Street / Arcadian Way (colonnaded avenue)",
        "Ancient Agora (marketplace with stoas)",
        "Gate of Augustus (monumental entrance)",
        "Ephesus Archaeological Museum"
    ],
    "cultural_items": [
        "wisdom statues (Sophia, Arete, Ennoia, Episteme)",
        "floor mosaics with geometric and mythological patterns",
        "Corinthian column capitals with acanthus leaf carvings",
        "ancient oil lamps and ceramic vessels",
        "gladiator reliefs and theatrical masks"
    ],
    "color_palette": "warm marble white, golden honey, Mediterranean blue sky, olive green, terracotta, Aegean turquoise",
    "atmosphere": "grand, ancient, civilized, sun-drenched, historically rich, Mediterranean warmth",
    "time_periods": [
        "golden Mediterranean morning with warm marble glow",
        "bright midday with deep blue Aegean sky",
        "amber sunset through ancient arches and columns",
        "soft twilight with mystical atmosphere among the ruins"
    ]
}


# -----------------------------------------------------------------------------
# Ã–ZEL GÄ°RÄ°Å ALANLARI (Custom Inputs)
# -----------------------------------------------------------------------------

EFES_CUSTOM_INPUTS = [
    {
        "key": "favorite_place",
        "label": "En SevdiÄŸi Antik Mekan",
        "type": "select",
        "options": ["Celsus KÃ¼tÃ¼phanesi", "BÃ¼yÃ¼k Tiyatro", "YamaÃ§ Evler", "Artemis TapÄ±naÄŸÄ±"],
        "default": "Celsus KÃ¼tÃ¼phanesi",
        "required": False,
        "help_text": "Hikayenin en Ã¶nemli sahnesi bu mekanda geÃ§ecek"
    },
    {
        "key": "special_discovery",
        "label": "KeÅŸfetmek Ä°stediÄŸi Åey",
        "type": "select",
        "options": ["Gizli KÃ¼tÃ¼phane OdasÄ±", "KayÄ±p Mozaik Harita", "Antik AltÄ±n Sikke", "Sihirli Mermer Heykel"],
        "default": "Gizli KÃ¼tÃ¼phane OdasÄ±",
        "required": False,
        "help_text": "Hikayede Ã§ocuÄŸun keÅŸfedeceÄŸi bÃ¼yÃ¼k sÄ±r"
    },
    {
        "key": "travel_companion",
        "label": "Yol ArkadaÅŸÄ±",
        "type": "select",
        "options": ["Bilge BaykuÅŸ", "Cesur Yunus", "MeraklÄ± Kedi", "NeÅŸeli KaplumbaÄŸa"],
        "default": "Bilge BaykuÅŸ",
        "required": False,
        "help_text": "Efes'te Ã§ocuÄŸa eÅŸlik edecek antik hayvan arkadaÅŸ"
    }
]


async def create_efes_scenario():
    """Efes Antik Kent MacerasÄ± senaryosunu oluÅŸtur veya gÃ¼ncelle."""

    print("\n" + "=" * 70)
    print("EFES ANTÄ°K KENT MACERASI SENARYO OLUÅTURMA")
    print("Master Prompts - PuLID Optimized - Greco-Roman Wonder")
    print("=" * 70 + "\n")

    async with async_session_factory() as db:
        # Mevcut senaryoyu kontrol et
        result = await db.execute(
            select(Scenario).where(Scenario.name.ilike("%Efes%"))
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
        scenario.name = "Efes Antik Kent MacerasÄ±"
        scenario.description = (
            "Antik dÃ¼nyanÄ±n en gÃ¶rkemli ÅŸehri Efes'te 2.000 yÄ±llÄ±k bir maceraya atÄ±l! "
            "Celsus KÃ¼tÃ¼phanesi'nin bilgelik heykelleri canlanÄ±yor, mozaikler sÄ±rlar fÄ±sÄ±ldÄ±yor. "
            "Ege'nin bÃ¼yÃ¼lÃ¼ kÄ±yÄ±larÄ±nda arkeolojik bir keÅŸif seni bekliyor!"
        )
        scenario.thumbnail_url = "/scenarios/efes.jpg"
        scenario.cover_prompt_template = EFES_COVER_PROMPT
        scenario.page_prompt_template = EFES_PAGE_PROMPT
        # V2: story_prompt_tr Ã¶ncelikli
        scenario.story_prompt_tr = EFES_STORY_PROMPT_TR
        scenario.ai_prompt_template = None  # V2 story_prompt_tr kullanÄ±yor
        scenario.location_constraints = EFES_LOCATION_CONSTRAINTS
        scenario.location_en = "Ephesus"
        scenario.cultural_elements = EFES_CULTURAL_ELEMENTS
        scenario.theme_key = "ephesus"
        scenario.custom_inputs_schema = EFES_CUSTOM_INPUTS
        scenario.is_active = True
        scenario.display_order = 4

        await db.commit()

        print("\n[OK] EFES ANTÄ°K KENT MACERASI OLUÅTURULDU!\n")
        print("-" * 70)
        print("Senaryo DetaylarÄ±:")
        print(f"  - name: {scenario.name}")
        print(f"  - description: {len(scenario.description)} karakter")
        print(f"  - cover_prompt_template: {len(EFES_COVER_PROMPT)} karakter")
        print(f"  - page_prompt_template: {len(EFES_PAGE_PROMPT)} karakter")
        print(f"  - story_prompt_tr: {len(EFES_STORY_PROMPT_TR)} karakter")
        print("  - location_en: Ephesus")
        print(f"  - location_constraints: {len(EFES_LOCATION_CONSTRAINTS)} karakter")
        print(f"  - cultural_elements: {len(json.dumps(EFES_CULTURAL_ELEMENTS))} karakter (JSON)")
        print("  - theme_key: ephesus")
        print(f"  - custom_inputs_schema: {len(EFES_CUSTOM_INPUTS)} Ã¶zel alan")
        print("-" * 70)

        # Custom inputs preview
        print("\nÃ–ZEL GÄ°RÄ°Å ALANLARI:")
        for inp in EFES_CUSTOM_INPUTS:
            print(f"  - {inp['label']}: {', '.join(inp['options'][:3])}...")

        # Prompt previews
        print("\n" + "=" * 70)
        print("KAPAK PROMPT Ã–NÄ°ZLEME (ilk 500 karakter):")
        print("-" * 70)
        print(EFES_COVER_PROMPT[:500] + "...")

        print("\n" + "=" * 70)
        print("SAYFA PROMPT Ã–NÄ°ZLEME (ilk 500 karakter):")
        print("-" * 70)
        print(EFES_PAGE_PROMPT[:500] + "...")

        print("\n" + "=" * 70)
        print("STORY_PROMPT_TR Ã–NÄ°ZLEME (ilk 500 karakter):")
        print("-" * 70)
        print(EFES_STORY_PROMPT_TR[:500] + "...")

        print("\n" + "=" * 70)
        print("Efes Antik Kent MacerasÄ± senaryosu hazÄ±r!")
        print("Ã‡ocuklar artÄ±k 2.000 yÄ±llÄ±k antik kenti keÅŸfedebilir!")
        print("=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(create_efes_scenario())


