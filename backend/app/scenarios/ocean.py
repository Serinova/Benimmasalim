"""Okyanus Macerası — Derin deniz keşfi.

TİP B: Geniş Ortam (Okyanus). Companion: Yunus / Deniz Kaplumbağası.
"""

from app.scenarios._base import CompanionAnchor, ScenarioContent
from app.scenarios._registry import register

OCEAN = register(ScenarioContent(
    theme_key="ocean",
    name="Okyanus Macerası",
    location_en="Deep Ocean",
    default_page_count=22,
    flags={"no_family": True},

    story_prompt_tr="""
# OKYANUS MACERASI — DERİN DENİZ KEŞFİ

## YAPI: {child_name} yanında {animal_friend} ile denizaltı aracında okyanusun derinliklerini keşfediyor. Mercan resifleri, batık gemi, derin deniz yaratıkları, biyolüminesans. Okyanus koruma mesajı — macera yoluyla.

**BAŞLIK:** "[Çocuk adı]'ın Okyanus Macerası"

---

### Bölüm 1 — Dalış (Sayfa 1-4)
- {child_name} denizaltı aracına biniyor, yanında {animal_friend}.
- Su yüzeyinin altına dalış — ışık değişiyor, mavi tonlar.
- İlk mercan resifi — renkli balıklar, deniz yıldızları.
- Bir mercan arasında parıldayan bir şey — eski bir pusula.

### Bölüm 2 — Batık Gemi (Sayfa 5-9)
- Pusulayı takip ederek batık bir gemiye ulaşıyorlar.
- Geminin içinde keşif — mürekkepli şişeler, eski haritalar, sandıklar.
- Bir sandıkta kristal bir küre — okyanusun haritası!
- Kürenin içinde ışıklar yanıyor — derinlerdeki bir şeyi gösteriyor.
- {animal_friend} heyecanla yol gösteriyor.

### Bölüm 3 — Derin Deniz (Sayfa 10-14)
- Daha derine dalış — karanlık, soğuk.
- Biyolüminesans yaratıklar — parıldayan jellyfish, anglerfish.
- Devasa bir deniz mağarası — içeride eski yapılar!
- Yapıların duvarlarında okyanus motifleri — balıklar, dalgalar.
- Kristal küre burada bir yuvaya oturuyor — tıklama sesi!

### Bölüm 4 — Gizli Bahçe (Sayfa 15-18)
- Küre yerine oturunca mağara aydınlanıyor — devasa bir sualtı bahçesi!
- Dev su bitkileri, renkli mercanlar, biolüminesans.
- Burası "okyanusun kalbi" — tüm akıntılar buradan başlıyor.
- Bahçedeki eski yapılar canlanıyor — sular berraklaşıyor, hayvanlar toplanıyor.

### Bölüm 5 — Yüzeye Dönüş (Sayfa 19-22)
- Kristal küreyi geri alıyor — hatıra olarak.
- Yüzeye çıkış — ışık artıyor, mavi-yeşil tonlar.
- Su yüzeyinde gün batımı — turuncu ışıkta okyanus parıldıyor.
- "Okyanusun derinliğinde bir dünya var. Onu korumak bize bağlı."

---

## 🚫 KURALLAR
- AİLE YOK. Sahnelerde sadece {child_name} + {animal_friend}.
- {animal_friend} AYNI görünüm her sayfada.
- Korkunç/tehlikeli deniz yaratıkları YOK (köpekbalığı saldırısı vb.).
- DUYGU: amazed, smiling, determined.

Hikayeyi TAM OLARAK {page_count} sayfa yaz.
""",

    cover_prompt_template=(
        'A young child in a small submarine window looking out at a colorful coral reef, '
        'wearing {clothing_description}. {scene_description}. '
        'Underwater scene with tropical fish, coral, light beams from above. {STYLE}'
    ),
    page_prompt_template=(
        'A young child {scene_description}, wearing {clothing_description}. '
        'Underwater ocean setting: coral reefs, deep sea, bioluminescence, shipwreck. '
        'Blue and teal lighting, underwater caustics. {STYLE}'
    ),

    outfit_girl=(
        "sky-blue wetsuit with white wave pattern down the sides, "
        "a small waterproof utility belt, clear diving goggles pushed up on forehead, "
        "aquamarine water shoes. EXACTLY the same outfit on every page."
    ),
    outfit_boy=(
        "navy-blue wetsuit with orange stripe accents, "
        "a small waterproof utility belt, clear diving goggles pushed up on forehead, "
        "dark blue water shoes. EXACTLY the same outfit on every page."
    ),

    companions=[
        CompanionAnchor(
            name_tr="Dostça Yunus",
            name_en="friendly bottlenose dolphin",
            species="dolphin",
            appearance="friendly grey bottlenose dolphin with bright intelligent eyes and a permanent smile",
            short_name="Yunus",
        ),
        CompanionAnchor(
            name_tr="Bilge Deniz Kaplumbağası",
            name_en="wise old sea turtle",
            species="sea turtle",
            appearance="wise old green sea turtle with a mossy shell and gentle brown eyes",
            short_name="Kaplumbağa",
        ),
    ],
    objects=[],

    cultural_elements={
        "primary": ["Coral reef ecosystem", "Sunken ship interior", "Deep sea bioluminescence",
                     "Submarine exploration"],
        "secondary": ["Crystal sphere ocean map", "Ancient underwater structures", "Giant kelp forest"],
        "atmosphere": "Mysterious, serene, deep blue, wonder",
    },

    location_constraints=(
        "Pages 1-4: Surface dive, coral reef. (Wide Shot, bright blue) "
        "Pages 5-9: Sunken ship interior. (Medium Shot, green-blue) "
        "Pages 10-14: Deep ocean, bioluminescent cave. (Dark, glowing creatures) "
        "Pages 15-18: Hidden underwater garden. (Wide, magical light) "
        "Pages 19-22: Ascent to surface, sunset. (Hero Shot, golden-blue)"
    ),

    scenario_bible={},
    custom_inputs_schema=[
        {"key": "animal_friend", "type": "select", "label": "Deniz Dostu",
         "default": "Dostça Yunus", "required": True, "companion_ref": True},
    ],
))
