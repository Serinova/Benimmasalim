"""Amazon'un Gizli Çağrısı — Yağmur ormanı macerası.

TİP B: Geniş Ortam (Amazon Yağmur Ormanı). Companion: Papağan / Maymun.
"""

from app.scenarios._base import CompanionAnchor, ScenarioContent
from app.scenarios._registry import register

AMAZON = register(ScenarioContent(
    theme_key="amazon",
    name="Amazon'un Gizli Çağrısı",
    location_en="Amazon Rainforest",
    default_page_count=22,
    flags={"no_family": False},

    story_prompt_tr="""
# AMAZON'UN GİZLİ ÇAĞRISI — YAĞMUR ORMANI MACERASI

## YAPI: {child_name} yanında {animal_friend} ile Amazon yağmur ormanını keşfediyor. Dev ağaçlar, gizli nehirler, gizemli hayvanlar. Doğayı koruma ve ekosistem mesajı — ama didaktik değil, macera yoluyla.

**BAŞLIK:** "[Çocuk adı]'ın Amazon Macerası"

---

### Bölüm 1 — Ormana Giriş (Sayfa 1-4)
- {child_name} Amazon yağmur ormanının kenarında. Devasa ağaçlar, asılı sarmaşıklar.
- {animal_friend} ile tanışma — bir ağaç dalından atlayarak/uçarak geliyor.
- Garip bir ses duyuluyor — ormanın derinliklerinden çağırıyor gibi.
- İçeriye doğru yola koyuluyorlar — ışık azalıyor, sesler artıyor.

### Bölüm 2 — Nehir Macerası (Sayfa 5-9)
- Geniş bir Amazon nehrine ulaşıyorlar. Dev nilüferler (Victoria amazonica).
- Nilüferlerin üzerinden atlayarak karşıya geçme — {animal_friend} rehber.
- Nehirde pembe yunus görüyorlar — dostça!
- Bir şelaleye ulaşıyorlar — arkasında gizli bir geçit var.
- Geçitten gizli bir vadiye ulaşıyorlar.

### Bölüm 3 — Gizli Vadi (Sayfa 10-14)
- Gizli vadide hiç görülmemiş bitkiler, parıldayan mantarlar, renkli kelebekler.
- Eski bir taş yapı — kayıp bir medeniyet kalıntısı.
- Yapının ortasında bir taş kabartma — ormanın haritası.
- Haritada bir işaret: ormanın "kalbi" — su kaynağı.
- {animal_friend} endişeli — su azalmış!

### Bölüm 4 — Su Kaynağı (Sayfa 15-18)
- Su kaynağına yürüyüş — devrilmiş dev ağaç suyu tıkamış!
- Birlikte çalışarak dalları kaldırıyorlar, küçük kanallar açıyorlar.
- Su tekrar akıyor! Orman canlanıyor — çiçekler açıyor, kuşlar ötmeye başlıyor.
- Taş kabartmadaki sembol parlıyor — görev tamamlandı.

### Bölüm 5 — Kapanış (Sayfa 19-22)
- Gizli vadiden çıkış — orman artık daha canlı.
- {animal_friend} ile vedalaşma ama "burada her zaman seni bekliyor olacağım."
- Ormanın kenarında son bakış — yeşilin binlerce tonu.
- "Amazon bana doğanın ne kadar güçlü ve kırılgan olduğunu gösterdi."

---

## 🚫 KURALLAR
- {animal_friend} AYNI görünüm her sayfada.
- Büyü/sihir YOK — doğa muhteşemliği yeterli.
- Korku/şiddet YOK.
- DUYGU: amazed, smiling, determined.

Hikayeyi TAM OLARAK {page_count} sayfa yaz.
""",

    cover_prompt_template=(
        'A young child standing in a lush Amazon rainforest clearing, '
        'wearing {clothing_description}. {scene_description}. '
        'Massive jungle trees, hanging vines, colorful macaw parrots flying. '
        'Dappled green sunlight through canopy. {STYLE}'
    ),
    page_prompt_template=(
        'A young child {scene_description}, wearing {clothing_description}. '
        'Amazon rainforest setting: giant trees, vines, exotic plants, river, waterfall. '
        'Dappled green and golden light. Cinematic. {STYLE}'
    ),

    outfit_girl=(
        "olive-green cotton explorer vest with many pockets over a cream long-sleeve tee, "
        "khaki adventure shorts with cargo pockets, sturdy brown hiking boots, "
        "a wide-brim khaki sun hat with a red bandana tied around it, "
        "small canvas backpack. EXACTLY the same outfit on every page."
    ),
    outfit_boy=(
        "tan cotton safari shirt with rolled-up sleeves, dark green cargo shorts, "
        "sturdy brown hiking boots, a khaki baseball cap with a leaf emblem, "
        "small green canvas backpack. EXACTLY the same outfit on every page."
    ),

    companions=[
        CompanionAnchor(
            name_tr="Renkli Papağan",
            name_en="colorful scarlet macaw parrot",
            species="macaw parrot",
            appearance="colorful scarlet macaw parrot with bright red, blue and yellow feathers",
            short_name="Papağan",
        ),
        CompanionAnchor(
            name_tr="Minik Maymun",
            name_en="small playful spider monkey",
            species="monkey",
            appearance="small playful brown spider monkey with long curly tail and bright curious eyes",
            short_name="Maymun",
        ),
    ],
    objects=[],

    cultural_elements={
        "primary": ["Giant kapok trees and hanging vines", "Amazon river and tributaries",
                     "Giant Victoria water lilies", "Exotic wildlife (toucans, monkeys, pink dolphins)"],
        "secondary": ["Hidden waterfall with cave behind", "Ancient stone ruins in jungle",
                      "Bioluminescent mushrooms", "Colorful butterflies and frogs"],
        "atmosphere": "Lush, mysterious, adventurous, vibrant green",
    },

    location_constraints=(
        "Pages 1-4: Rainforest edge and entry. (Wide Shot, green canopy) "
        "Pages 5-9: Amazon river, lily pads, waterfall. (Medium Shot, water reflections) "
        "Pages 10-14: Hidden valley, ancient ruins, stone map. (Close-up, mystical light) "
        "Pages 15-18: Water source, restoration. (Medium Shot, action) "
        "Pages 19-22: Forest exit, vibrant sunset. (Hero Shot, golden-green)"
    ),

    scenario_bible={
        "companions": [
            {"name_tr": "Renkli Papağan", "species": "macaw parrot",
             "appearance_en": "colorful scarlet macaw parrot with bright red, blue and yellow feathers"},
            {"name_tr": "Minik Maymun", "species": "monkey",
             "appearance_en": "small playful brown spider monkey with long curly tail"},
        ],
    },

    custom_inputs_schema=[
        {"key": "animal_friend", "type": "select", "label": "Orman Dostu",
         "default": "Renkli Papağan", "required": True, "companion_ref": True},
    ],
))
