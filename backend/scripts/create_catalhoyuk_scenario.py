"""
Ã‡atalhÃ¶yÃ¼k Neolitik Kenti MacerasÄ± Senaryosu - Master Prompt OluÅŸturma

Bu script, Ã‡atalhÃ¶yÃ¼k Neolitik Kenti MacerasÄ± senaryosunu profesyonel, tutarlÄ± ve
kÃ¼ltÃ¼rel aÃ§Ä±dan zengin prompt'larla oluÅŸturur veya gÃ¼nceller.

Ã‡atalhÃ¶yÃ¼k: MÃ– 7400-6200, Konya/Ã‡umra OvasÄ±, UNESCO DÃ¼nya MirasÄ± (2012).
DÃ¼nyanÄ±n en erken kent Ã¶rneklerinden biri. SokaksÄ±z, Ã§atÄ±dan giriÅŸli evler.
18 yerleÅŸim tabakasÄ±, duvar resimleri, ana tanrÄ±Ã§a figÃ¼rinleri, bereket kÃ¼ltÃ¼.

Ã–NEMLÄ° - PuLID UYUMLULUK:
- Fiziksel Ã¶zellikler YASAK (saÃ§, gÃ¶z, ten rengi) - PuLID fotoÄŸraftan alÄ±yor
- {clothing_description} zorunlu - kÄ±yafet tutarlÄ±lÄ±ÄŸÄ± iÃ§in
- Sahne aÃ§Ä±klamalarÄ± ACTION-ONLY - stil StyleConfig'den geliyor
- YÃ¼z kimliÄŸi korunmalÄ± - "Bu kesin benim Ã§ocuÄŸum" hissi

Ã‡alÄ±ÅŸtÄ±rma:
    cd backend
    python -m scripts.create_catalhoyuk_scenario
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
# Ã‡ATALHÃ–YÃœK NEOLÄ°TÄ°K KENTÄ° MACERASI - MASTER PROMPT TEMPLATES
# =============================================================================

# -----------------------------------------------------------------------------
# KAPAK PROMPT TEMPLATE
# -----------------------------------------------------------------------------
# Kapak: Epik, kahramanca poz, Ã‡atalhÃ¶yÃ¼k'Ã¼n en ikonik gÃ¶rÃ¼nÃ¼mÃ¼
# Format: Dikey (768x1024), poster tarzÄ±, baÅŸlÄ±k alanÄ± yukarÄ±da
# PuLID: YÃ¼z referans fotoÄŸraftan, fiziksel Ã¶zellik yazÄ±lmaz
# -----------------------------------------------------------------------------

CATALHOYUK_COVER_PROMPT = """A breathtaking children's book cover illustration.

SCENE COMPOSITION:
A young child {scene_description}, standing on one of the ancient rooftops of Ã‡atalhÃ¶yÃ¼k, the world's earliest known city, on the vast Konya Plain in central Anatolia, Turkey.

ICONIC BACKGROUND ELEMENTS (include 2-3 key details):
- Dense cluster of ancient mud-brick houses built wall-to-wall with no streets â€” a rooftop cityscape where people walked on roofs
- Wooden ladders poking up from roof openings â€” the only way to enter houses through the ceiling
- Warm earthen walls made of sun-dried mud brick (kerpiÃ§) in ochre, beige, and brown tones
- The vast, flat Ã‡umra Plain (Konya steppe) stretching to the distant Taurus Mountains on the horizon
- Ancient wall paintings visible through some roof openings â€” hunting scenes with deer and bulls
- Smoke wisps rising from hearth openings in the rooftops, signs of daily Neolithic life
- Small rooftop gardens with early cultivated wheat and barley

LIGHTING & ATMOSPHERE:
- Warm golden hour light casting long shadows across the flat rooftop landscape
- The immense Anatolian sky dominating the scene with scattered clouds
- Sense of ancient wonder â€” 9,000 years of history, the dawn of civilization
- Earthy color palette: warm ochre, terracotta, dusty beige, golden straw, deep brown, steppe green
- A feeling of communal warmth â€” this was humanity's first true neighborhood

CLOTHING:
The child is wearing {clothing_description}.

STYLE:
{visual_style}.

COMPOSITION REQUIREMENTS:
- Professional book cover design with clear title space at the top
- Child positioned in lower third, standing on a rooftop looking out over the ancient city
- Epic cinematic scale showing the vast rooftop city and the endless Konya Plain beyond
- Ladders and roof openings framing the scene, giving depth and archaeological character"""


# -----------------------------------------------------------------------------
# Ä°Ã‡ SAYFA PROMPT TEMPLATE
# -----------------------------------------------------------------------------
# Ä°Ã§ Sayfalar: Hikaye anlatÄ±mÄ±, karakter-Ã§evre etkileÅŸimi
# Format: Yatay (1024x768), alt kÄ±sÄ±mda metin alanÄ±
# PuLID: YÃ¼z korunur, kÄ±yafet tutarlÄ±lÄ±ÄŸÄ± Ã¶nemli
# -----------------------------------------------------------------------------

CATALHOYUK_PAGE_PROMPT = """A stunning children's book illustration set in and around the ancient Neolithic city of Ã‡atalhÃ¶yÃ¼k, the world's earliest known urban settlement, on the Konya Plain of central Anatolia, Turkey.

SCENE ACTION:
A young child {scene_description}.

AUTHENTIC Ã‡ATALHÃ–YÃœK SETTING (vary these elements per scene):
- ROOFTOP CITYSCAPE: Dense mud-brick houses with flat roofs built wall-to-wall with no streets, ladders connecting rooftops to interiors, smoke from hearths, rooftop activity areas where people gathered, cooked, and socialized
- HOUSE INTERIORS: Warm plastered walls with vivid wall paintings (hunting scenes, geometric patterns, handprints), raised sleeping platforms along walls, central hearth with cooking area, storage bins with early wheat and barley, obsidian tools and bone implements neatly arranged
- WALL PAINTINGS: Extraordinary murals showing massive bulls (aurochs) with huge horns, deer hunts with running human figures, geometric patterns in red ochre, vulture scenes, leopard motifs, the world's oldest known landscape painting (erupting Hasan DaÄŸÄ± volcano)
- MOTHER GODDESS FIGURINES: Small clay figurines of seated women (ana tanrÄ±Ã§a) â€” the famous Ã‡atalhÃ¶yÃ¼k mother goddess sitting on a throne flanked by leopards, fertility symbols, carved stone and clay statuettes
- BURIAL CUSTOMS: Platforms under which ancestors were buried beneath the house floor (children can discover "the house remembers everyone who lived here"), painted skulls, burial gifts
- CRAFT AREAS: Obsidian mirror-making workshops, flint knapping areas, basket weaving with early textiles, pottery with geometric designs, bead-making from colored stones
- KONYA PLAIN LANDSCAPE: Vast flat steppe with golden grasses, distant snow-capped Taurus Mountains, the ancient Ã‡arÅŸamba River meandering through the plain, flocks of cranes and storks
- ARCHAEOLOGICAL EXCAVATION: Modern protective shelter over the ancient mound, excavation trenches revealing 18 layers of settlement, carefully exposed walls and artifacts, walkways for visitors

HISTORICAL & ARCHAEOLOGICAL ACCURACY:
- Mud-brick (kerpiÃ§) construction with thick plastered walls, replastered many times over centuries
- No streets or ground-level doors â€” all movement was across rooftops and down ladders
- Houses rebuilt on top of older houses, creating 18 distinct settlement layers spanning 1,200 years
- Egalitarian society with no apparent hierarchy â€” all houses roughly the same size
- Early agriculture: domesticated wheat, barley, lentils; herded sheep and goats alongside hunting wild aurochs and deer
- MÃ– 7400-6200 dating â€” predates Egyptian pyramids by 4,000 years

LIGHTING OPTIONS (match to scene mood):
- Warm morning light filtering through a roof opening into a painted interior
- Bright midday sun on the golden rooftop city with vast blue sky
- Amber sunset casting long shadows across the rooftop landscape toward distant mountains
- Warm firelight from a central hearth illuminating wall paintings with dancing shadows

CLOTHING:
The child is wearing {clothing_description}.

STYLE:
{visual_style}.

COMPOSITION:
- Clear focal point on the child in the middle-ground
- Rich, detailed Ã‡atalhÃ¶yÃ¼k background with authentic Neolithic elements
- Space at bottom for text overlay (25% of image height)
- Warm, earthy color palette: ochre, terracotta, dusty beige, golden straw, deep brown"""


# -----------------------------------------------------------------------------
# AI HÄ°KAYE ÃœRETÄ°M PROMPTU (Gemini Pass-1 iÃ§in)
# -----------------------------------------------------------------------------

CATALHOYUK_STORY_PROMPT_TR = """Sen ödüllü çocuk kitabı yazarı ve Çatalhöyük/Neolitik dönem uzmanısın.
Kahraman, yaş ve eğitsel değerler yukarıda verilmiştir. Görevin: Çatalhöyük Neolitik Kenti'nde geçen büyülü bir macera yazmak.

📍 ÇATALHÖYÜK — KULLANILACAK KÜLTÜREL MEKANLAR (hikayeye en az 6 tanesini entegre et):
1. Çatı üstü şehir manzarası — sokaksız, bitişik evler, çatıdan çatıya yürüyüş, merdivenlerle eve giriş
2. Duvar resimleri odası — dev boğa (aurochs) resimleri, geyik avı sahneleri, kırmızı el izleri, dünyanın en eski manzara resmi (Hasan Dağı volkanı)
3. Antik bereket figürini — 9.000 yıllık kadın heykeli, insanlığın en eski sanat eserlerinden biri
4. Obsidyen ayna atölyesi — volkanik camdan yapılmış parlak aynalar, taş alet yapımı, Neolitik teknoloji
5. Ev içi — sıvalı duvarlar, yükseltilmiş uyku platformları, merkezi ocak, depolama bölmeleri, buğday ve arpa çuvalları
6. Çumra Ovası — uçsuz bucaksız step, Toros Dağları silüeti, Çarşamba Nehri, turna ve leylek sürüleri
7. Kazı alanı — koruma çatısı altında 18 tabaka yerleşim katmanı, tabaka tabaka tarih
8. Dokuma ve boncuk atölyesi — erken tekstil, renkli taş boncuklar, sepet örme
9. Topluluk buluşma alanı — çatı üstü toplantı yeri, paylaşım ve iş birliği
10. Gizli geçitler — evlerin altında ataların hatıra alanları, renkli boncuklar ve el sanatları eserleri

🎭 YARDIMCI KARAKTER (en az biri hikayede olsun):
Bilge Boğa (duvar resminden canlanan aurochs), Kurnaz Leopar (Neolitik çağdan canlanan, mağara duvarından çıkmış),
Meraklı Turna (göç eden kuş, dünyayı tanıyan), Parlak Ayna Ruhu (obsidyen aynadan yansıyan gizemli dost)
veya Sevimli Koyun (ilk evcilleştirilen hayvanlardan). Karakter, Neolitik dönemden "uyanmış" olabilir.

⚡ ÖNEMLI — BU BİR GEZİ REHBERİ DEĞİL, BİR MACERA HİKAYESİ!
Çatalhöyük mekanları ARKA PLAN olarak kullan. Hikayenin motorunu MEKANLAR DEĞİL,
çocuğun İÇ YOLCULUĞU ve eğitsel değerler oluştursun.

❌ YANLIŞ: "Ece duvar resimlerini gördü. Sonra figürine baktı. Sonra kazı alanını gezdi."
✅ DOĞRU: Çocuğun bir SORUNU/ZAYIFLIĞI var. Bu sorun Çatalhöyük'ün gizemli mekanlarında
bir MACERA'ya dönüşüyor. Duvar resimleri "canlanıyor", obsidyen aynalar geçmişi gösteriyor,
Antik bereket figürini çocuğa 9.000 yıl öncesinden bir bilgelik fısıldıyor.
Çocuk insanlığın ilk komşuluğunu keşfederken KENDİNİ keşfediyor.

🔑 EĞİTSEL DEĞER ENTEGRASYONU:
Seçilen eğitsel değer hikayenin OLAY ÖRGÜSÜNÜ belirlemeli:
- Paylaşmak seçildiyse → Çatalhöyük'ün eşitlikçi toplumu bunu yaşatsın, çocuk bencillikten paylaşıma geçsin
- İş birliği seçildiyse → sokaksız şehirde herkes birbirine bağlı, çocuk tek başına yapamaz, birlikte başarsın
- Cesaret seçildiyse → gizemli geçitten geçerek antik katmanları keşfetmek zorunda kalsın
- Merak seçildiyse → obsidyen ayna geçmişi göstersin, çocuğun soruları onu daha derin gizemlere götürsün
- Sabır seçildiyse → duvar resmi yapmak sabır ister, çocuk acele edince resim bozulsun
Değer sadece "söylenmesin", çocuk YAŞAYARAK öğrensin!

⚠️ ÖNEMLİ KISITLAMA:
Hikayede DİNİ RİTÜEL veya İBADET SAHNESİ OLMAMALIDIR.
Çatalhöyük'ün gizemi arkeolojik, bilimsel ve insani merak perspektifinden işlensin.
Gömü gelenekleri "ataları hatırlama ve saygı" olarak sunulsun, korku veya karanlık öğe olmasın.
Antik bereket figürini "arkeolojik eser ve sanat" perspektifinden, dini obje olarak DEĞİL.

🎨 SAHNE AÇIKLAMASI KURALLARI (Pass-2 için ipucu):
Her sahne için spesifik Çatalhöyük lokasyonu ve Neolitik detay kullan.
Örn: "Duvar resimlerinin kırmızı boğa figürüyle kaplı iç odada", "Çatı üstünden Çumra Ovası'na bakarken",
"Obsidyen ayna atölyesinde parlak taş aletlerin arasında", "Antik bereket heykelinin bulunduğu sergi nişinin önünde".
Genel ifadelerden kaçın ("Çatalhöyük'te" yerine somut yer adı ve detay kullan)."""


# -----------------------------------------------------------------------------
# LOKASYON KISITLAMALARI
# -----------------------------------------------------------------------------

CATALHOYUK_LOCATION_CONSTRAINTS = """Ã‡atalhÃ¶yÃ¼k Neolithic city iconic elements (include 1-2 relevant details depending on the scene):
- Dense mud-brick houses with flat roofs, no streets, entry through roof openings via ladders
- Vivid wall paintings (aurochs bulls, hunting scenes, geometric patterns, handprints)
- Warm earthen/plastered interior walls with Neolithic domestic elements
- Vast Konya/Ã‡umra Plain steppe landscape with distant Taurus Mountains
- Archaeological excavation details (settlement layers, protective shelter, exposed walls)"""


# -----------------------------------------------------------------------------
# KÃœLTÃœREL ELEMENTLER (JSON)
# -----------------------------------------------------------------------------

CATALHOYUK_CULTURAL_ELEMENTS = {
    "primary_landmarks": [
        "rooftop cityscape with no streets (entry via ladders through roof)",
        "wall paintings room (aurochs bulls, deer hunts, Hasan DaÄŸÄ± volcano painting)",
        "Mother Goddess figurine (seated woman flanked by leopards)",
        "obsidian mirror and tool workshop",
        "18-layer archaeological excavation under protective shelter"
    ],
    "secondary_elements": [
        "mud-brick (kerpiÃ§) house interiors with raised sleeping platforms",
        "central hearth and cooking area",
        "Ã‡umra Plain panorama with distant Taurus Mountains",
        "textile weaving and bead-making craft areas",
        "burial platforms beneath house floors"
    ],
    "cultural_items": [
        "Mother Goddess figurine (ana tanrÄ±Ã§a, fertility symbol)",
        "aurochs horn installations (bucrania) mounted on walls",
        "obsidian mirrors and flint tools",
        "red ochre wall paintings and geometric patterns",
        "early cultivated wheat, barley, and lentil seeds"
    ],
    "color_palette": "warm ochre, terracotta, dusty beige, golden straw, deep brown, steppe green, red ochre accents",
    "atmosphere": "ancient, communal, warm, earthy, mysterious, dawn-of-civilization wonder",
    "time_periods": [
        "warm morning light through roof opening into painted interior",
        "bright midday on golden rooftop city with vast blue sky",
        "amber sunset across rooftop landscape toward distant mountains",
        "warm firelight from central hearth illuminating wall paintings"
    ]
}


# -----------------------------------------------------------------------------
# Ã–ZEL GÄ°RÄ°Å ALANLARI (Custom Inputs)
# -----------------------------------------------------------------------------

CATALHOYUK_CUSTOM_INPUTS = [
    {
        "key": "favorite_painting",
        "label": "En SevdiÄŸi Duvar Resmi",
        "type": "select",
        "options": ["Dev BoÄŸa (Aurochs)", "Geyik AvÄ± Sahnesi", "Volkan ManzarasÄ±", "KÄ±rmÄ±zÄ± El Ä°zleri"],
        "default": "Dev BoÄŸa (Aurochs)",
        "required": False,
        "help_text": "Hikayede bu duvar resmi canlanacak ve Ã§ocuÄŸa rehberlik edecek"
    },
    {
        "key": "special_discovery",
        "label": "KeÅŸfetmek Ä°stediÄŸi Åey",
        "type": "select",
        "options": ["Gizli YeraltÄ± KatmanÄ±", "KayÄ±p Ana TanrÄ±Ã§a FigÃ¼rini", "Sihirli Obsidyen Ayna", "Antik BuÄŸday Tohumu"],
        "default": "Sihirli Obsidyen Ayna",
        "required": False,
        "help_text": "Hikayede Ã§ocuÄŸun keÅŸfedeceÄŸi bÃ¼yÃ¼k sÄ±r"
    },
    {
        "key": "travel_companion",
        "label": "Yol ArkadaÅŸÄ±",
        "type": "select",
        "options": ["Bilge BoÄŸa", "Kurnaz Leopar", "MeraklÄ± Turna", "Parlak Ayna Ruhu"],
        "default": "Bilge BoÄŸa",
        "required": False,
        "help_text": "Ã‡atalhÃ¶yÃ¼k'te Ã§ocuÄŸa eÅŸlik edecek Neolitik hayvan arkadaÅŸ"
    }
]


async def create_catalhoyuk_scenario():
    """Ã‡atalhÃ¶yÃ¼k Neolitik Kenti MacerasÄ± senaryosunu oluÅŸtur veya gÃ¼ncelle."""

    print("\n" + "=" * 70)
    print("Ã‡ATALHÃ–YÃœK NEOLÄ°TÄ°K KENTÄ° MACERASI SENARYO OLUÅTURMA")
    print("Master Prompts - PuLID Optimized - Dawn of Civilization")
    print("=" * 70 + "\n")

    async with async_session_factory() as db:
        # Mevcut senaryoyu kontrol et
        result = await db.execute(
            select(Scenario).where(Scenario.name.ilike("%Ã‡atalhÃ¶yÃ¼k%"))
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
        scenario.name = "Ã‡atalhÃ¶yÃ¼k Neolitik Kenti MacerasÄ±"
        scenario.description = (
            "Ä°nsanlÄ±ÄŸÄ±n ilk ÅŸehrinde 9.000 yÄ±llÄ±k bir maceraya atÄ±l! "
            "Ã‡atÄ±dan girilen evler, canlanan duvar resimleri, obsidyen aynalar ve Ana TanrÄ±Ã§a'nÄ±n sÄ±rlarÄ±. "
            "Konya OvasÄ±'nda Neolitik dÃ¼nyanÄ±n bÃ¼yÃ¼lÃ¼ kapÄ±larÄ± seni bekliyor!"
        )
        scenario.thumbnail_url = "/scenarios/catalhoyuk.jpg"
        scenario.cover_prompt_template = CATALHOYUK_COVER_PROMPT
        scenario.page_prompt_template = CATALHOYUK_PAGE_PROMPT
        # V2: story_prompt_tr Ã¶ncelikli
        scenario.story_prompt_tr = CATALHOYUK_STORY_PROMPT_TR
        scenario.ai_prompt_template = None  # V2 story_prompt_tr kullanÄ±yor
        scenario.location_constraints = CATALHOYUK_LOCATION_CONSTRAINTS
        scenario.location_en = "Ã‡atalhÃ¶yÃ¼k"
        scenario.cultural_elements = CATALHOYUK_CULTURAL_ELEMENTS
        scenario.theme_key = "catalhoyuk"
        scenario.custom_inputs_schema = CATALHOYUK_CUSTOM_INPUTS
        scenario.is_active = True
        scenario.display_order = 5

        await db.commit()

        print("\n[OK] Ã‡ATALHÃ–YÃœK NEOLÄ°TÄ°K KENTÄ° MACERASI OLUÅTURULDU!\n")
        print("-" * 70)
        print("Senaryo DetaylarÄ±:")
        print(f"  - name: {scenario.name}")
        print(f"  - description: {len(scenario.description)} karakter")
        print(f"  - cover_prompt_template: {len(CATALHOYUK_COVER_PROMPT)} karakter")
        print(f"  - page_prompt_template: {len(CATALHOYUK_PAGE_PROMPT)} karakter")
        print(f"  - story_prompt_tr: {len(CATALHOYUK_STORY_PROMPT_TR)} karakter")
        print("  - location_en: Ã‡atalhÃ¶yÃ¼k")
        print(f"  - location_constraints: {len(CATALHOYUK_LOCATION_CONSTRAINTS)} karakter")
        print(f"  - cultural_elements: {len(json.dumps(CATALHOYUK_CULTURAL_ELEMENTS))} karakter (JSON)")
        print("  - theme_key: catalhoyuk")
        print(f"  - custom_inputs_schema: {len(CATALHOYUK_CUSTOM_INPUTS)} Ã¶zel alan")
        print("-" * 70)

        # Custom inputs preview
        print("\nÃ–ZEL GÄ°RÄ°Å ALANLARI:")
        for inp in CATALHOYUK_CUSTOM_INPUTS:
            print(f"  - {inp['label']}: {', '.join(inp['options'][:3])}...")

        # Prompt previews
        print("\n" + "=" * 70)
        print("KAPAK PROMPT Ã–NÄ°ZLEME (ilk 500 karakter):")
        print("-" * 70)
        print(CATALHOYUK_COVER_PROMPT[:500] + "...")

        print("\n" + "=" * 70)
        print("SAYFA PROMPT Ã–NÄ°ZLEME (ilk 500 karakter):")
        print("-" * 70)
        print(CATALHOYUK_PAGE_PROMPT[:500] + "...")

        print("\n" + "=" * 70)
        print("STORY_PROMPT_TR Ã–NÄ°ZLEME (ilk 500 karakter):")
        print("-" * 70)
        print(CATALHOYUK_STORY_PROMPT_TR[:500] + "...")

        print("\n" + "=" * 70)
        print("Ã‡atalhÃ¶yÃ¼k Neolitik Kenti MacerasÄ± senaryosu hazÄ±r!")
        print("Ã‡ocuklar artÄ±k 9.000 yÄ±llÄ±k insanlÄ±ÄŸÄ±n ilk ÅŸehrini keÅŸfedebilir!")
        print("=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(create_catalhoyuk_scenario())


