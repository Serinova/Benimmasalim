"""Oyuncak Dünyası — Minyatür oyuncak macerası.

TİP B: Fantastik. Companion: Pelüş Ayıcık / Mini Ejderha.
"""

from app.scenarios._base import CompanionAnchor, ScenarioContent
from app.scenarios._registry import register

TOY_WORLD = register(ScenarioContent(
    theme_key="toy_world",
    name="Oyuncak Dünyası Macerası",
    location_en="Toy World",
    default_page_count=22,
    flags={"no_family": True},

    story_prompt_tr="""
# OYUNCAK DÜNYASI MACERASI — MİNYATÜR DÜNYADA DEV MACERA

## YAPI: {child_name} yanında {animal_friend} ile küçülüp oyuncak dünyasına giriyor. LEGO şehirleri, tahta tren yolları, peluş dağları. Oyuncaklar canlı! Eğlenceli, renkli, hayal gücü dolu.

**BAŞLIK:** "[Çocuk adı]'ın Oyuncak Dünyası"

---

### Bölüm 1 — Küçülme (Sayfa 1-4)
- {child_name} odasında oyuncaklarıyla oynuyor. {animal_friend} yanında.
- Bir oyuncak kutusu parlıyor — dokunduğunda küçülmeye başlıyor!
- Oyuncaklar DEV boyutta! LEGO blokları tepeler, tahta raylar otoyollar.
- Minik bir {child_name} dev bir LEGO şehrinin kapısından giriyor.

### Bölüm 2 — LEGO Şehri (Sayfa 5-9)
- LEGO evleri, mağazaları, parkları — her şey renkli bloklar!
- Oyuncak askerler devriye geziyor — dostça, meraklı.
- Tahta tren geçiyor — {child_name} atlayıp biniyor!
- Tren kristal bir gölün kıyısına varıyor — su mermer gibi pürüzsüz.
- {animal_friend} suyun üzerinde yansımasını görüyor — başka bir dünya!

### Bölüm 3 — Peluş Dağları (Sayfa 10-14)
- Peluş kumaştan dağlar — yumuşak, renkli.
- Pamuk bulutlar ve düğme güneş.
- Dağın tepesinde devasa bir bozuk oyuncak var — çarkları durmuş!
- "Bu oyuncak tüm dünyayı çalıştırıyor! Tamir etmeliyiz!"
- {animal_friend} ile birlikte küçük çarkları yerine takıyorlar.

### Bölüm 4 — Büyük Tamir (Sayfa 15-18)
- Son çark takıldığında tüm oyuncak dünyası canlanıyor!
- Işıklar yanıyor, müzik çalıyor, trenler çalışıyor.
- Tüm oyuncaklar kutlama yapıyor — LEGO adamlar, peluşlar, tahtalar.
- {child_name} kahraman!

### Bölüm 5 — Normal Boyuta Dönüş (Sayfa 19-22)
- Oyuncak kutusu tekrar parlıyor — büyüme zamanı!
- Normal boyuta dönüş — oda aynı.
- Oyuncaklara bakıyor — "Onların da kendi dünyaları var."
- {animal_friend} ile gülümseme. "Her oyuncağın bir hikayesi var."

---

## 🚫 KURALLAR
- AİLE YOK. Sahnelerde sadece {child_name} + {animal_friend}.
- {animal_friend} AYNI görünüm her sayfada.
- Korku/şiddet YOK. Neşeli, renkli, hayal gücü dolu.
- DUYGU: amazed, smiling, determined.

Hikayeyi TAM OLARAK {page_count} sayfa yaz.
""",

    cover_prompt_template=(
        'A tiny child standing in a giant colorful toy world with LEGO buildings, '
        'wearing {clothing_description}. {scene_description}. '
        'Colorful blocks, wooden trains, plush mountains, button sun. {STYLE}'
    ),
    page_prompt_template=(
        'A tiny child {scene_description}, wearing {clothing_description}. '
        'Toy world: LEGO buildings, wooden rails, plush mountains, button details. '
        'Bright cheerful lighting, saturated colors. {STYLE}'
    ),

    outfit_girl=(
        "bright coral-pink dungarees over a white polka-dot long-sleeve tee, "
        "colorful rainbow-striped knee socks, bright yellow canvas sneakers, "
        "a small star-shaped hair clip, tiny red backpack. "
        "EXACTLY the same outfit on every page."
    ),
    outfit_boy=(
        "bright blue bib overalls over a red-and-white striped crew-neck tee, "
        "colorful mismatched socks, bright green canvas sneakers, "
        "a small propeller beanie hat, tiny yellow backpack. "
        "EXACTLY the same outfit on every page."
    ),

    companions=[
        CompanionAnchor(
            name_tr="Pelüş Ayıcık",
            name_en="fluffy teddy bear plushie",
            species="teddy bear plushie",
            appearance="fluffy golden-brown teddy bear plushie with a red bow tie and button eyes",
            short_name="Ayıcık",
        ),
        CompanionAnchor(
            name_tr="Parıltılı Mini Ejderha",
            name_en="tiny sparkling dragon",
            species="tiny dragon",
            appearance="tiny sparkling purple dragon with iridescent wings and green glowing eyes",
            short_name="Mini Ejderha",
        ),
    ],
    objects=[],

    cultural_elements={
        "primary": ["LEGO city with colorful blocks", "Wooden train tracks and trains",
                     "Plush mountains with cotton clouds", "Button sun and button stars"],
        "atmosphere": "Cheerful, colorful, imaginative, playful",
    },

    location_constraints=(
        "Pages 1-4: Kid's room, shrinking, toy world entry. (Medium Shot, bright) "
        "Pages 5-9: LEGO city, train ride, crystal lake. (Wide Shot, colorful) "
        "Pages 10-14: Plush mountains, broken toy mechanism. (Medium Shot, warm) "
        "Pages 15-18: Celebration, world alive again. (Wide Shot, vibrant) "
        "Pages 19-22: Return to normal size. (Medium Shot, warm)"
    ),

    scenario_bible={},
    custom_inputs_schema=[
        {"key": "animal_friend", "type": "select", "label": "Oyuncak Dostu",
         "default": "Pelüş Ayıcık", "required": True, "companion_ref": True},
    ],
))
