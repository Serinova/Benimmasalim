"""
Tac Mahal MacerasÄ± Senaryosu - Master Prompt OluÅŸturma

Bu script, Tac Mahal MacerasÄ± senaryosunu profesyonel, tutarlÄ± ve
kÃ¼ltÃ¼rel aÃ§Ä±dan zengin prompt'larla oluÅŸturur veya gÃ¼nceller.

Tac Mahal: 1632-1653, Åah Cihan, Agra/Hindistan, UNESCO (1983).
Beyaz mermer tÃ¼rbe, BabÃ¼r mimarisi, pietra dura taÅŸ kakma sanatÄ±.
4 minare, Ã‡arbaÄŸ bahÃ§eleri, Yamuna Nehri kÄ±yÄ±sÄ±.
Yeni Yedi Harika, ~73 metre yÃ¼kseklik, 20.000+ zanaatkÃ¢r.

Ã–NEMLÄ° - PuLID UYUMLULUK:
- Fiziksel Ã¶zellikler YASAK (saÃ§, gÃ¶z, ten rengi) - PuLID fotoÄŸraftan alÄ±yor
- {clothing_description} zorunlu - kÄ±yafet tutarlÄ±lÄ±ÄŸÄ± iÃ§in
- Sahne aÃ§Ä±klamalarÄ± ACTION-ONLY - stil StyleConfig'den geliyor
- YÃ¼z kimliÄŸi korunmalÄ± - "Bu kesin benim Ã§ocuÄŸum" hissi

âš ï¸ Ã–NEMLÄ° KISITLAMA:
- Hikayede DÄ°NÄ° RÄ°TÃœEL veya Ä°BADET SAHNESÄ° OLMAMALIDIR.
- Tac Mahal "aÅŸkÄ±n ve sanatÄ±n anÄ±tÄ±, mimari ÅŸaheser" olarak sunulsun.
- Odak: MÄ°MARÄ°, ZANAAT SANATI, BAHÃ‡ECÄ°LÄ°K, SÄ°METRÄ° ve SEVGÄ° TEMASI.

Ã‡alÄ±ÅŸtÄ±rma:
    cd backend
    python -m scripts.create_tacmahal_scenario
"""

import asyncio
import json
import os
import sys
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import select
from app.core.database import async_session_factory
from app.models.scenario import Scenario


# =============================================================================
# TAC MAHAL MACERASI - MASTER PROMPT TEMPLATES
# =============================================================================

TACMAHAL_COVER_PROMPT = """A breathtaking children's book cover illustration.

SCENE COMPOSITION:
A young child {scene_description}, standing on the long reflecting pool pathway of the Charbagh gardens, gazing in wonder at the magnificent Taj Mahal rising before them in Agra, India.

ICONIC BACKGROUND ELEMENTS (include 2-3 key details):
- The Taj Mahal's iconic white marble dome and four slender minarets rising against a dramatic sky â€” the world's most famous monument of love
- The grand central onion dome (~73 meters tall) flanked by four smaller chattri domes
- Four elegant marble minarets slightly tilted outward at the corners
- The long reflecting pool (water channel) stretching from the child toward the Taj, creating a perfect mirror reflection of the monument
- Symmetrical Charbagh (four-part) Mughal gardens with manicured lawns, cypress trees, and flowering beds on either side
- The grand red sandstone gateway (Darwaza-i-Rauza) framing the scene from behind

LIGHTING & ATMOSPHERE:
- Magical golden sunrise or sunset light making the white marble glow with warm pink-gold tones
- The famous color-changing quality of the marble â€” catching warm hues from the sky
- A soft misty atmosphere over the Yamuna River behind the Taj
- Perfect mirror reflection of the Taj in the still water of the reflecting pool
- Color palette: luminous white marble, warm pink-gold sky, emerald garden green, reflecting pool blue-silver, red sandstone accents

CLOTHING:
The child is wearing {clothing_description}.

STYLE:
{visual_style}.

COMPOSITION REQUIREMENTS:
- Professional book cover design with clear title space at the top
- Child positioned in lower third, on the reflecting pool pathway looking toward the Taj
- The Taj Mahal centered and majestic, filling the upper portion of the image
- Perfect symmetry emphasized â€” the reflecting pool creating a mirror image
- Sense of wonder, beauty, and timeless love"""


TACMAHAL_PAGE_PROMPT = """A stunning children's book illustration set at the magnificent Taj Mahal complex in Agra, India, a UNESCO World Heritage Site and one of the New Seven Wonders of the World.

SCENE ACTION:
A young child {scene_description}.

AUTHENTIC TAC MAHAL SETTING (vary these elements per scene):
- TAJ MAHAL EXTERIOR: The iconic white Makrana marble monument with its grand central onion dome (~73m), four smaller chattri pavilion domes, four elegant minarets slightly tilted outward, the raised marble platform (plinth), and intricate pietra dura inlay work on every surface â€” semi-precious stones (lapis lazuli blue, carnelian red, jade green, turquoise) forming floral arabesque patterns
- REFLECTING POOL & GARDENS: The long central water channel (nahr) creating a perfect mirror reflection, the four-part Charbagh garden divided by raised marble walkways, manicured lawns with cypress trees, flowering shrubs, birdsong-filled air, fountains along the central channel
- GREAT GATEWAY (DARWAZA-I-RAUZA): The grand red sandstone and marble entry gate with calligraphic inscriptions, the dramatic "reveal" moment when the Taj first appears through the archway, inlaid marble panels, domed chattri pavilions atop the gate
- INTERIOR CHAMBER: The octagonal central chamber with the ornate cenotaphs of Shah Jahan and Mumtaz Mahal behind delicate marble lattice screens (jali), pierced marble allowing soft filtered light, echoing acoustics that carry whispers for 28 seconds, intricate pietra dura floral patterns covering every surface
- PIETRA DURA WORKSHOPS: Close-up scenes of the incredible stone inlay art â€” artisans fitting tiny pieces of semi-precious stones (lapis lazuli, carnelian, jasper, turquoise, onyx) into carved marble channels to create flowers, vines, and geometric patterns
- MARBLE JALI SCREENS: The exquisite pierced marble lattice work â€” geometric patterns carved from single marble slabs allowing dappled light to filter through, creating lace-like shadows on the floor
- MINARETS: The four 40-meter-tall marble minarets at the corners of the plinth â€” octagonal in cross-section with balconies, slightly tilted outward (designed to fall away from the tomb in an earthquake)
- YAMUNA RIVER BANK: The view from behind the Taj looking over the Yamuna River â€” the riverbank terrace, the "Moonlight Garden" (Mehtab Bagh) across the river, boats on the water, herons and kingfishers along the bank
- RED SANDSTONE BUILDINGS: The flanking mosque (to the west) and jawab/guest house (to the east) â€” red sandstone with white marble domes, providing perfect symmetry to the complex
- CALLIGRAPHY PANELS: Ornate calligraphic inscriptions inlaid in black marble on white â€” flowing scripts decorating doorways and arches, the visual effect of letters growing larger at height to appear uniform from ground level

ARCHITECTURAL & HISTORICAL ACCURACY:
- Built 1632-1653 by Mughal Emperor Shah Jahan for his wife Mumtaz Mahal
- Architect: Ustad Ahmad Lahauri (attributed)
- Material: White Makrana marble from Rajasthan, red sandstone, 28 types of semi-precious stones from across Asia
- Height: ~73 meters to top of finial
- Workers: 20,000+ artisans and laborers from across the Mughal Empire and beyond
- UNESCO World Heritage Site since 1983, one of the New Seven Wonders of the World
- Mughal architectural style: fusion of Persian, Islamic, and Indian design traditions
- The marble changes color: pinkish at dawn, white during day, golden at sunset, silvery blue under moonlight

LIGHTING OPTIONS (match to scene mood):
- Magical sunrise with pink-gold light making the marble glow warm rose â€” mist over the Yamuna
- Bright midday with brilliant white marble against deep blue sky, sharp shadows from minarets
- Golden sunset turning the Taj amber-gold, the reflecting pool ablaze with color
- Moonlit night with the marble glowing ethereal silvery-blue, stars above the dome

CLOTHING:
The child is wearing {clothing_description}.

STYLE:
{visual_style}.

COMPOSITION:
- Clear focal point on the child in the middle-ground
- Majestic Taj Mahal architecture creating a sense of symmetry, beauty, and wonder
- Space at bottom for text overlay (25% of image height)
- Vibrant color palette: luminous white marble, pietra dura jewel tones (lapis blue, carnelian red, jade green), garden emerald, sky azure, sunset pink-gold, red sandstone warm"""


TACMAHAL_STORY_PROMPT_TR = """Sen Ã¶dÃ¼llÃ¼ Ã§ocuk kitabÄ± yazarÄ± ve BabÃ¼r Ä°mparatorluÄŸu tarihi/Hint-Ä°slam mimarisi uzmanÄ±sÄ±n.
Kahraman, yaÅŸ ve eÄŸitsel deÄŸerler yukarÄ±da verilmiÅŸtir. GÃ¶revin: Tac Mahal ve Ã§evresinde geÃ§en bÃ¼yÃ¼lÃ¼ bir macera yazmak.

ğŸ“ TAC MAHAL â€” KULLANILACAK KÃœLTÃœREL MEKANLAR (hikayeye en az 6 tanesini entegre et):
1. Tac Mahal dÄ±ÅŸ cephe â€” beyaz Makrana mermeri, dev soÄŸan kubbe (~73m), 4 zarif minare, yarÄ± deÄŸerli taÅŸ kakmalar (pietra dura), Ã§iÃ§ek arabeskler
2. YansÄ±ma havuzu ve bahÃ§eler â€” Ã‡arbaÄŸ (dÃ¶rt parÃ§a) BabÃ¼r bahÃ§esi, uzun su kanalÄ±nda Tac Mahal'in ayna yansÄ±masÄ±, Ã§Ä±nar ve servi aÄŸaÃ§larÄ±, Ã§iÃ§ek tarhlarÄ±, fÄ±skiyeler
3. BÃ¼yÃ¼k KapÄ± (Darwaza-i-Rauza) â€” kÄ±rmÄ±zÄ± kumtaÅŸÄ± ve mermer giriÅŸ kapÄ±sÄ±, kapÄ±nÄ±n kemerinden Tac Mahal'in ilk kez belirdiÄŸi bÃ¼yÃ¼lÃ¼ an, hat yazÄ±larÄ±
4. Ä°Ã§ oda â€” sekizgen merkez oda, Åah Cihan ve MÃ¼mtaz Mahal'in sÃ¼slemeli sanduklarÄ±, zarif mermer kafes (jali) perdeler, fÄ±sÄ±ltÄ±larÄ±n 28 saniye yankÄ±landÄ±ÄŸÄ± akustik
5. Pietra dura taÅŸ kakma sanatÄ± â€” yarÄ± deÄŸerli taÅŸlar (lapis lazuli mavisi, akik kÄ±rmÄ±zÄ±sÄ±, yeÅŸim yeÅŸili, turkuaz) kÃ¼Ã§Ã¼cÃ¼k parÃ§alar halinde mermere kakÄ±larak Ã§iÃ§ek ve bitki desenleri oluÅŸturma sanatÄ±
6. Mermer jali kafes iÅŸÃ§iliÄŸi â€” tek mermer bloktan oyulmuÅŸ geometrik dantel desenleri, Ä±ÅŸÄ±ÄŸÄ±n kafesten sÃ¼zÃ¼lÃ¼p yerde desen oluÅŸturmasÄ±
7. Minareler â€” 4 kÃ¶ÅŸede 40 metrelik sekizgen minareler, balkonlu, hafifÃ§e dÄ±ÅŸa eÄŸik (depremde tÃ¼rbeden uzaÄŸa dÃ¼ÅŸecek ÅŸekilde tasarlanmÄ±ÅŸ)
8. Yamuna Nehri kÄ±yÄ±sÄ± â€” Tac Mahal'in arkasÄ±ndan nehir manzarasÄ±, Mehtab Bagh (Ay IÅŸÄ±ÄŸÄ± BahÃ§esi) karÅŸÄ± kÄ±yÄ±da, tekneler, balÄ±kÃ§Ä±l kuÅŸlarÄ±
9. KÄ±rmÄ±zÄ± kumtaÅŸÄ± yapÄ±lar â€” batÄ±daki cami ve doÄŸudaki simetrik misafir binasÄ± (jawab), kÄ±rmÄ±zÄ± kumtaÅŸÄ± Ã¼zerine beyaz mermer kubbeler
10. Hat sanatÄ± panelleri â€” siyah mermer kakmayla beyaz mermer Ã¼zerine yazÄ±lmÄ±ÅŸ hat yazÄ±larÄ±, yÃ¼ksekliÄŸe gÃ¶re bÃ¼yÃ¼tÃ¼lmÃ¼ÅŸ harfler (alttan bakÄ±nca eÅŸit gÃ¶rÃ¼nsÃ¼n diye)

ğŸ­ YARDIMCI KARAKTER (en az biri hikayede olsun):
Bilge Tavus KuÅŸu (bahÃ§elerde yaÅŸayan, tÃ¼ylerindeki renklerin pietra dura taÅŸlarÄ±yla eÅŸleÅŸtiÄŸi gÃ¶rkemli kuÅŸ),
KonuÅŸan Mermer Ã‡iÃ§ek (duvardan canlanabilen pietra dura Ã§iÃ§ek, 400 yÄ±ldÄ±r gÃ¼zelliÄŸin sÄ±rrÄ±nÄ± saklayan),
NeÅŸeli Maymun (bahÃ§elerde ve minare balkonlarÄ±nda oynayan, her gizli kÃ¶ÅŸeyi bilen meraklÄ± makak maymunu),
Bilge Taş Kakmacı Sesi (yüzlerce yıl önce en güzel çiçek desenini yapmış ustanın anısı, sabrın ve sanatın sırrını öğreten)
veya Cesur YusufÃ§uk (Yamuna Nehri'nden bahÃ§e fÄ±skiyelerine uÃ§an, suyun ve Ä±ÅŸÄ±ÄŸÄ±n dansÄ±nÄ± bilen Ä±ÅŸÄ±ltÄ±lÄ± bÃ¶cek).
Karakter, Tac Mahal'in 400 yÄ±llÄ±k tarihinden veya BabÃ¼r sanatÄ±nÄ±n bÃ¼yÃ¼lÃ¼ dÃ¼nyasÄ±ndan "uyanmÄ±ÅŸ" olabilir.

âš¡ Ã–NEMLÄ° â€” BU BÄ°R GEZÄ° REHBERÄ° DEÄÄ°L, BÄ°R MACERA HÄ°KAYESÄ°!
Tac Mahal ARKA PLAN olarak kullan. Hikayenin motorunu MEKANLAR DEÄÄ°L,
Ã§ocuÄŸun Ä°Ã‡ YOLCULUÄU ve eÄŸitsel deÄŸerler oluÅŸtursun.

âŒ YANLIÅ: "Ali Tac Mahal'i gÃ¶rdÃ¼. Ã‡ok gÃ¼zeldi. Sonra bahÃ§ede gezdi."
âœ… DOÄRU: Ã‡ocuÄŸun bir SORUNU/ZAYIFLIÄI var. Bu sorun Tac Mahal'in bÃ¼yÃ¼lÃ¼ dÃ¼nyasÄ±nda
bir MACERA'ya dÃ¶nÃ¼ÅŸÃ¼yor. BÃ¼yÃ¼k KapÄ±'dan geÃ§erken her ÅŸey deÄŸiÅŸiyor,
pietra dura Ã§iÃ§ekleri canlanÄ±p Ã§ocuÄŸu sihirli bir yolculuÄŸa Ã§Ä±karÄ±yor,
mermerin gÃ¼n doÄŸumunda pembe, gÃ¼n batÄ±mÄ±nda altÄ±n, ay Ä±ÅŸÄ±ÄŸÄ±nda gÃ¼mÃ¼ÅŸe dÃ¶nÃ¼ÅŸmesi
Ã§ocuÄŸa deÄŸiÅŸimin gÃ¼zelliÄŸini ve sevginin gÃ¼cÃ¼nÃ¼ Ã¶ÄŸretiyor. Ã‡ocuk simetrinin,
sabrÄ±n ve gÃ¼zelliÄŸin sÄ±rrÄ±nÄ± keÅŸfederken KENDÄ°NÄ° keÅŸfediyor.

ğŸ”‘ EÄÄ°TSEL DEÄER ENTEGRASYONU:
SeÃ§ilen eÄŸitsel deÄŸer hikayenin OLAY Ã–RGÃœSÃœNÃœ belirlemeli:
- SabÄ±r seÃ§ildiyse â†’ pietra dura ustasÄ± gibi kÃ¼Ã§Ã¼cÃ¼k taÅŸlarÄ± tek tek yerleÅŸtirme, 21 yÄ±llÄ±k inÅŸaat sabrÄ±
- Sevgi seÃ§ildiyse â†’ Åah Cihan'Ä±n MÃ¼mtaz Mahal'e olan sevgisi, sevdiklerimiz iÃ§in yapÄ±lanlar
- Merak seÃ§ildiyse â†’ mermerin renk deÄŸiÅŸtirme sÄ±rrÄ±, hat yazÄ±larÄ±nÄ±n perspektif hilesi, akustik yankÄ±
- Hayal gÃ¼cÃ¼ seÃ§ildiyse â†’ yansÄ±ma havuzundaki ters dÃ¼nya, mermer Ã§iÃ§eklerin canlanmasÄ±
- Ä°ÅŸ birliÄŸi seÃ§ildiyse â†’ 20.000 zanaatkÃ¢rÄ±n birlikte Ã§alÄ±ÅŸmasÄ±, farklÄ± Ã¼lkelerden gelen taÅŸlar
DeÄŸer sadece "sÃ¶ylenmesin", Ã§ocuk YAÅAYARAK Ã¶ÄŸrensin!

âš ï¸ Ã–NEMLÄ° KISITLAMALAR:
1. Hikayede DÄ°NÄ° RÄ°TÃœEL veya Ä°BADET SAHNESÄ° OLMAMALIDIR.
   Cami yapÄ±sÄ± yalnÄ±zca "mimari simetri unsuru" olarak geÃ§sin.
2. Tac Mahal "aÅŸkÄ±n ve sanatÄ±n anÄ±tÄ±, mimari ÅŸaheser" olarak sunulsun.
3. Hat yazÄ±larÄ± "kaligrafi sanatÄ±" perspektifinden (dini metin olarak deÄŸil).
4. Odak: MÄ°MARÄ° GÃœZELLÄ°K, ZANAAT SANATI (pietra dura), SÄ°METRÄ°, SEVGÄ° ve SABIR.

ğŸ¨ SAHNE AÃ‡IKLAMASI KURALLARI (Pass-2 iÃ§in ipucu):
Her sahne iÃ§in spesifik Tac Mahal lokasyonu ve mimari/sanatsal detay kullan.
Ã–rn: "BÃ¼yÃ¼k KapÄ±'nÄ±n kemerinden Tac Mahal'i ilk kez gÃ¶rdÃ¼ÄŸÃ¼ an nefesi kesilerek",
"YansÄ±ma havuzunun baÅŸÄ±nda mermerin suda baÅŸ aÅŸaÄŸÄ± yansÄ±masÄ±na dokunurken",
"Pietra dura Ã§iÃ§eÄŸinin kÃ¼Ã§Ã¼cÃ¼k lapis lazuli yapraklarÄ±nÄ± parmaÄŸÄ±yla hissederken",
"Minare balkonundan gÃ¼n batÄ±mÄ±nda altÄ±n rengi Tac Mahal'e bakarken".
Genel ifadelerden kaÃ§Ä±n ("Tac Mahal'de" yerine somut yer adÄ± ve detay kullan)."""


TACMAHAL_LOCATION_CONSTRAINTS = """Taj Mahal UNESCO World Heritage Site iconic elements (include 1-2 relevant details depending on the scene):
- The luminous white Makrana marble dome and four slender minarets of the Taj Mahal
- Charbagh (four-part) Mughal gardens with reflecting pool creating mirror image of the monument
- Intricate pietra dura stone inlay work â€” semi-precious stones forming floral arabesque patterns on marble
- Pierced marble jali lattice screens creating lace-like light patterns
- Perfect bilateral symmetry in every element of the complex"""


TACMAHAL_CULTURAL_ELEMENTS = {
    "primary_landmarks": [
        "Taj Mahal â€” white marble dome (~73m), four minarets, pietra dura inlay",
        "Charbagh gardens with central reflecting pool (mirror reflection)",
        "Great Gateway (Darwaza-i-Rauza) â€” dramatic first reveal of the Taj",
        "Interior chamber with marble jali screens and cenotaphs",
        "Pietra dura stone inlay art â€” semi-precious stones in marble"
    ],
    "secondary_elements": [
        "Four minarets (40m each, slightly tilted outward for earthquake safety)",
        "Yamuna River bank and Mehtab Bagh (Moonlight Garden) across the river",
        "Red sandstone mosque and jawab flanking the Taj for symmetry",
        "Calligraphic inscriptions in black marble inlay on white",
        "Marble color changes: pink at dawn, white midday, gold sunset, silver moonlight"
    ],
    "cultural_items": [
        "Pietra dura semi-precious stones (lapis lazuli, carnelian, jade, turquoise, onyx)",
        "Marble jali (pierced lattice) screens creating dappled light patterns",
        "Mughal garden design with cypress trees and flowering beds",
        "Indian peacocks displaying iridescent tail feathers in the gardens",
        "Traditional Agra marble craftsmanship continuing 400-year-old techniques"
    ],
    "color_palette": "luminous white marble, pietra dura jewel tones (lapis blue, carnelian red, jade green, turquoise), garden emerald, sky azure, sunset pink-gold, red sandstone warm, reflecting pool silver-blue",
    "atmosphere": "serene, symmetrical, luminous, romantic, majestic, jewel-like detail against vast white marble, garden paradise",
    "time_periods": [
        "magical sunrise with pink-gold light making the marble glow warm rose, mist over Yamuna",
        "bright midday with brilliant white marble against deep blue sky, sharp minaret shadows",
        "golden sunset turning the Taj amber-gold, reflecting pool ablaze with color",
        "moonlit night with marble glowing ethereal silvery-blue, stars above the dome"
    ]
}


TACMAHAL_CUSTOM_INPUTS = [
    {
        "key": "favorite_moment",
        "label": "En BÃ¼yÃ¼lÃ¼ An",
        "type": "select",
        "options": ["GÃ¼n DoÄŸumunda Pembe Tac Mahal", "YansÄ±ma Havuzundaki Ayna DÃ¼nya", "Pietra Dura Ã‡iÃ§eklerinin CanlanmasÄ±", "Ay IÅŸÄ±ÄŸÄ±nda GÃ¼mÃ¼ÅŸ Tac Mahal"],
        "default": "GÃ¼n DoÄŸumunda Pembe Tac Mahal",
        "required": False,
        "help_text": "Hikayenin en bÃ¼yÃ¼lÃ¼ sahnesinin Ä±ÅŸÄ±k atmosferi"
    },
    {
        "key": "special_discovery",
        "label": "KeÅŸfetmek Ä°stediÄŸi Åey",
        "type": "select",
        "options": ["KayÄ±p Pietra Dura TaÅŸÄ±", "FÄ±sÄ±ltÄ± Kubbesinin SÄ±rrÄ±", "Usta KakmacÄ±nÄ±n Gizli Deseni", "YansÄ±ma Havuzunun Ã–teki DÃ¼nyasÄ±"],
        "default": "KayÄ±p Pietra Dura TaÅŸÄ±",
        "required": False,
        "help_text": "Hikayede Ã§ocuÄŸun peÅŸine dÃ¼ÅŸeceÄŸi bÃ¼yÃ¼k gizem"
    },
    {
        "key": "travel_companion",
        "label": "Yol ArkadaÅŸÄ±",
        "type": "select",
        "options": ["Bilge Tavus KuÅŸu", "KonuÅŸan Mermer Ã‡iÃ§ek", "NeÅŸeli Maymun", "Cesur YusufÃ§uk"],
        "default": "Bilge Tavus KuÅŸu",
        "required": False,
        "help_text": "Tac Mahal'in bahÃ§elerinde Ã§ocuÄŸa eÅŸlik edecek bÃ¼yÃ¼lÃ¼ dost"
    }
]


async def create_tacmahal_scenario():
    """Tac Mahal MacerasÄ± senaryosunu oluÅŸtur veya gÃ¼ncelle."""

    print("\n" + "=" * 70)
    print("TAC MAHAL MACERASI SENARYO OLUÅTURMA")
    print("Master Prompts - PuLID Optimized - Mughal Marble Wonder")
    print("=" * 70 + "\n")

    async with async_session_factory() as db:
        result = await db.execute(
            select(Scenario).where(Scenario.name.ilike("%Tac Mahal%"))
        )
        existing = result.scalar_one_or_none()

        if existing:
            print(f"[INFO] Mevcut senaryo bulundu, gÃ¼ncelleniyor... (ID: {existing.id})")
            scenario = existing
        else:
            print("[INFO] Yeni senaryo oluÅŸturuluyor...")
            scenario = Scenario(id=uuid.uuid4())
            db.add(scenario)

        scenario.name = "Tac Mahal MacerasÄ±"
        scenario.description = (
            "DÃ¼nyanÄ±n en gÃ¼zel anÄ±tÄ±nda beyaz mermer ve yarÄ± deÄŸerli taÅŸlarla sÃ¼slÃ¼ bÃ¼yÃ¼lÃ¼ bir macera! "
            "GÃ¼n doÄŸumunda pembeye, gÃ¼n batÄ±mÄ±nda altÄ±na dÃ¶nen Tac Mahal'de "
            "simetrinin, sabrÄ±n ve sevginin sÄ±rrÄ±nÄ± keÅŸfet!"
        )
        scenario.thumbnail_url = "/scenarios/tacmahal.jpg"
        scenario.cover_prompt_template = TACMAHAL_COVER_PROMPT
        scenario.page_prompt_template = TACMAHAL_PAGE_PROMPT
        scenario.story_prompt_tr = TACMAHAL_STORY_PROMPT_TR
        scenario.ai_prompt_template = None
        scenario.location_constraints = TACMAHAL_LOCATION_CONSTRAINTS
        scenario.location_en = "Taj Mahal"
        scenario.cultural_elements = TACMAHAL_CULTURAL_ELEMENTS
        scenario.theme_key = "tacmahal"
        scenario.custom_inputs_schema = TACMAHAL_CUSTOM_INPUTS
        scenario.is_active = True
        scenario.display_order = 11

        await db.commit()

        print("\n[OK] TAC MAHAL MACERASI OLUÅTURULDU!\n")
        print("-" * 70)
        print("Senaryo DetaylarÄ±:")
        print(f"  - name: {scenario.name}")
        print(f"  - description: {len(scenario.description)} karakter")
        print(f"  - cover_prompt_template: {len(TACMAHAL_COVER_PROMPT)} karakter")
        print(f"  - page_prompt_template: {len(TACMAHAL_PAGE_PROMPT)} karakter")
        print(f"  - story_prompt_tr: {len(TACMAHAL_STORY_PROMPT_TR)} karakter")
        print("  - location_en: Taj Mahal")
        print(f"  - location_constraints: {len(TACMAHAL_LOCATION_CONSTRAINTS)} karakter")
        print(f"  - cultural_elements: {len(json.dumps(TACMAHAL_CULTURAL_ELEMENTS))} karakter (JSON)")
        print("  - theme_key: tacmahal")
        print(f"  - custom_inputs_schema: {len(TACMAHAL_CUSTOM_INPUTS)} Ã¶zel alan")
        print("-" * 70)

        print("\nÃ–ZEL GÄ°RÄ°Å ALANLARI:")
        for inp in TACMAHAL_CUSTOM_INPUTS:
            print(f"  - {inp['label']}: {', '.join(inp['options'][:3])}...")

        print("\n" + "=" * 70)
        print("Tac Mahal MacerasÄ± senaryosu hazÄ±r!")
        print("Ã‡ocuklar artÄ±k dÃ¼nyanÄ±n en gÃ¼zel anÄ±tÄ±nda bÃ¼yÃ¼lÃ¼ bir keÅŸfe Ã§Ä±kabilir!")
        print("=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(create_tacmahal_scenario())


