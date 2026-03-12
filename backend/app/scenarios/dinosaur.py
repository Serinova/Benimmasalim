"""Dinozor Macerası — Prehistorik dünya keşfi.

TİP C: Fantastik (zaman yolculuğu). Companion: Bebek Dinozor / Pelüş Ayıcık.
"""

from app.scenarios._base import CompanionAnchor, ScenarioContent
from app.scenarios._registry import register

DINOSAUR = register(ScenarioContent(
    theme_key="dinosaur",
    name="Dinozor Macerası",
    location_en="Prehistoric World",
    default_page_count=22,
    flags={"no_family": True},

    story_prompt_tr="""
# DİNOZOR MACERASI — TARİH ÖNCESİ DÜNYA

## YAPI: {child_name} yanında {animal_friend} ile prehistorik dünyaya gidiyor. Dev dinozorlar, volkanlar, ormanlar. Bilimsel doğruluk önemli. Korkunç değil, hayranlık veren.

**BAŞLIK:** "[Çocuk adı]'ın Dinozor Macerası"

---

### Bölüm 1 — Prehistorik Dünya (Sayfa 1-4)
- {child_name} bir doğa tarih müzesinde, yanında {animal_friend}.
- Bir dinozor iskeleti sergisinde tuhaf bir fosil parıldıyor — dokunuyor!
- Etraf bulanıklaşıyor — VIIIZ! 66 milyon yıl öncesinde!
- Devasa eğrelti otları, dev böcekler, sıcak ve nemli hava.

### Bölüm 2 — Otçullarla Tanışma (Sayfa 5-9)
- Diplodocus sürüsü — boyunları ağaç tepelerine uzanıyor!
- Triceratops ailesi — bebek triceratops çocukla arkadaş oluyor.
- Pteranodon'lar gökyüzünde süzülüyor.
- Bir nehir kenarında yaprak yiyen Stegosaurus.
- {animal_friend} ile birlikte doğayı gözlemliyorlar.

### Bölüm 3 — T-Rex Karşılaşması (Sayfa 10-14)
- Uzaktan gürültü — adım sesleri! T-Rex!
- Ama T-Rex tehlikeli değil burada — avlanıyor ama çocuğa ilgilenmiyor.
- Gizlenmek zorundalar — dev eğrelti otlarının arasında.
- T-Rex geçiyor — nefes tutma anı, sonra rahatla (calm).
- Volkan uzaktan duman çıkarıyor — acele etmeli!

### Bölüm 4 — Volkan (Sayfa 15-18)
- Volkan daha aktif — lav nehirleri kıyılarda.
- Fosili geri götürmeli — dönüş noktası volkanın yakınında!
- {animal_friend} yolu buluyor — güvenli bir geçit.
- Fosili parıldayan kayaya koyuyor — zaman geçişi başlıyor!

### Bölüm 5 — Dönüş (Sayfa 19-22)
- Müzeye geri dönüş — her şey normal, dino iskeleti aynı yerde.
- Ama avucunda küçük bir trilobit fosili var — gerçekti!
- Müzedeki dinozorları artık farklı gözlerle görüyor.
- "66 milyon yıl önce dünya bambaşkaydı. Ama doğa hep muhteşem."

---

## 🚫 KURALLAR
- AİLE YOK. Sahnelerde sadece {child_name} + {animal_friend}.
- {animal_friend} AYNI görünüm her sayfada.
- Korkunç/kanlı dinozor sahneleri YOK. Hayranlık, merak odaklı.
- DUYGU: amazed, smiling, determined.

Hikayeyi TAM OLARAK {page_count} sayfa yaz.
""",

    cover_prompt_template=(
        'A young child standing before a massive friendly Diplodocus dinosaur in a prehistoric jungle, '
        'wearing {clothing_description}. {scene_description}. '
        'Lush prehistoric ferns, erupting volcano in distance, warm dramatic light. {STYLE}'
    ),
    page_prompt_template=(
        'A young child {scene_description}, wearing {clothing_description}. '
        'Prehistoric setting: giant ferns, dinosaurs, volcanoes, primordial forest. '
        'Warm dramatic cinematic lighting. {STYLE}'
    ),

    outfit_girl=(
        "warm amber-brown leather explorer vest over a cream T-shirt, "
        "olive-brown cargo pants with knee patches, sturdy brown hiking boots, "
        "a wide-brim khaki adventure hat, small canvas satchel. "
        "EXACTLY the same outfit on every page."
    ),
    outfit_boy=(
        "tan khaki explorer shirt with rolled sleeves, dark brown cargo shorts, "
        "sturdy brown leather hiking boots with thick soles, "
        "a khaki baseball cap with dinosaur pin, small brown leather backpack. "
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
            name_tr="Minik Bebek Dinozor",
            name_en="tiny friendly baby triceratops",
            species="baby dinosaur",
            appearance="tiny friendly light green baby triceratops with big curious eyes and small horns",
            short_name="Bebek Dino",
        ),
    ],
    objects=[],

    cultural_elements={
        "primary": ["Diplodocus and Triceratops herds", "T-Rex sighting", "Active volcano",
                     "Prehistoric giant ferns and ancient trees"],
        "secondary": ["Pteranodon sky patrol", "Stegosaurus at river", "Trilobite fossils"],
        "atmosphere": "Awe-inspiring, prehistoric, adventurous, warm",
    },

    location_constraints=(
        "Pages 1-4: Museum and time-transition to prehistoric world. (Medium Shot) "
        "Pages 5-9: Open plains with herbivore dinosaurs. (Wide Shot, lush green) "
        "Pages 10-14: Dense prehistoric forest, T-Rex encounter. (Close-up, dramatic) "
        "Pages 15-18: Near volcano, return path. (Wide, warm red/orange) "
        "Pages 19-22: Museum return. (Medium Shot, warm)"
    ),

    scenario_bible={},
    custom_inputs_schema=[
        {"key": "animal_friend", "type": "select", "label": "Macera Arkadaşı",
         "default": "Pelüş Ayıcık", "required": True, "companion_ref": True},
    ],
))
