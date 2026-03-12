"""Uzay Macerası — Galaksi keşif yolculuğu.

TİP B: Geniş Ortam (Uzay). Companion: Robot Nova / Mini Ejderha.
"""

from app.scenarios._base import CompanionAnchor, ScenarioContent
from app.scenarios._registry import register

SPACE = register(ScenarioContent(
    theme_key="space",
    name="Uzay Macerası",
    location_en="Outer Space",
    default_page_count=22,
    flags={"no_family": True},

    story_prompt_tr="""
# UZAY MACERASI — GALAKSİ KEŞFİ

## YAPI: {child_name} yanında {animal_friend} ile uzay mekiğinde galaksiyi keşfediyor. Gezegenler, yıldızlar, asteroid kuşağı, uzay istasyonu. Bilim odaklı ama eğlenceli macera.

**BAŞLIK:** "[Çocuk adı]'ın Uzay Macerası"

---

### Bölüm 1 — Kalkış (Sayfa 1-4)
- {child_name} uzay mekiğinde hazırlık yapıyor, yanında {animal_friend}.
- Geri sayım — 3, 2, 1... fırlatma! Koltukta sarsılma, bulutları geçiş.
- Uzayın karanlığı ve yıldızlar — ilk kez sıfır yerçekimi!
- Dünya pencereden küçülüyor — "Evimiz ne kadar güzelmiş!"

### Bölüm 2 — Ay ve Mars (Sayfa 5-9)
- Ay'ın yakınından geçiş — kraterler, gri yüzey.
- Mars'a iniş — kızıl toprak, kanyon, uzay giysisi.
- Bir Mars kayasında garip kristaller — parıldıyor!
- {animal_friend} bir iz buluyor — eski bir araç izi mi?
- İzi takip ediyorlar — eski bir keşif robotu kalıntısı.

### Bölüm 3 — Asteroid Kuşağı (Sayfa 10-14)
- Mekikle asteroid kuşağına giriş — kayalar dans ediyor.
- Bir asteroide iniş — buzdan ve metalden bir dünya.
- Buz altında ışıklar — doğal bir fenomen.
- Mekik bir asteroide çarpıyor! Hafif hasar. Tamir lazım.
- {animal_friend} ile birlikte tamir — takım çalışması.

### Bölüm 4 — Uzay İstasyonu (Sayfa 15-18)
- Uzay istasyonuna yanaşma — devasa, dönen yapı.
- İçeride sera bahçesi — uzayda yetişen bitkiler!
- İstasyonun penceresinden nebula (bulutsu) manzarası — renklerin dansı.
- İstasyonun bilgisayarından Dünya'ya mesaj gönderiyor.

### Bölüm 5 — Dönüş (Sayfa 19-22)
- Dünya'ya dönüş yolculuğu — mavi gezegen büyüyor.
- Atmosfere giriş — ateş topu gibi.
- Paraşütlerle iniş — okyanustan kurtarma.
- "Uzay muazzam ama ev gibisi yok. Bir gün yine gideceğim!"

---

## 🚫 KURALLAR
- AİLE YOK. Sahnelerde sadece {child_name} + {animal_friend}.
- {animal_friend} AYNI görünüm her sayfada.
- Uzaylı / ET tarzı yaratıklar YOK.
- DUYGU: amazed, smiling, determined.

Hikayeyi TAM OLARAK {page_count} sayfa yaz.
""",

    cover_prompt_template=(
        'A young child in a sleek space suit floating in front of a spaceship window, '
        'wearing {clothing_description}. {scene_description}. '
        'Deep space background with stars, nebula, and distant planets. '
        'Dramatic space lighting, blue and purple hues. {STYLE}'
    ),
    page_prompt_template=(
        'A young child {scene_description}, wearing {clothing_description}. '
        'Space setting: spaceship interior, planet surfaces, asteroid field, space station. '
        'Cinematic sci-fi lighting. {STYLE}'
    ),

    outfit_girl=(
        "sleek white and sky-blue space suit with mission patches, clear helmet visor, "
        "silver space boots, small utility belt with pouches. When inside ship: "
        "cream cotton jumpsuit with blue stripe and mission badge. "
        "EXACTLY the same outfit on every page."
    ),
    outfit_boy=(
        "sleek white and dark blue space suit with mission patches, clear helmet visor, "
        "silver space boots, small utility belt with pouches. When inside ship: "
        "grey cotton jumpsuit with orange stripe and mission badge. "
        "EXACTLY the same outfit on every page."
    ),

    companions=[
        CompanionAnchor(
            name_tr="Gümüş Robot Nova",
            name_en="small silver robot companion named Nova",
            species="robot",
            appearance="small silver robot companion named Nova with blue LED eyes and a rotating antenna",
            short_name="Nova",
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
        "primary": ["Spaceship cockpit and windows", "Moon craters", "Mars red canyons",
                     "Asteroid field", "Space station with rotating habitat"],
        "secondary": ["Nebula colors", "Zero gravity scenes", "Earth from space"],
        "atmosphere": "Epic, adventurous, scientific wonder, vast",
    },

    location_constraints=(
        "Pages 1-4: Spaceship launchpad and orbit. (Wide Shot, dramatic) "
        "Pages 5-9: Moon flyby and Mars surface. (Medium Shot, red/grey) "
        "Pages 10-14: Asteroid belt, icy asteroid surface. (Dynamic, dramatic lighting) "
        "Pages 15-18: Space station interior and exterior. (Wide Shot, blue-white) "
        "Pages 19-22: Earth return, ocean landing. (Hero Shot, blue marble)"
    ),

    scenario_bible={},
    custom_inputs_schema=[
        {"key": "animal_friend", "type": "select", "label": "Uzay Dostu",
         "default": "Gümüş Robot Nova", "required": True, "companion_ref": True},
    ],
))
