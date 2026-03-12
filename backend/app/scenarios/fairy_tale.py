"""Masal Dünyası — Klasik masal kahramanlarıyla macera.

TİP B: Fantastik. Companion: Baykuş / Mini Ejderha.
"""

from app.scenarios._base import CompanionAnchor, ScenarioContent
from app.scenarios._registry import register

FAIRY_TALE = register(ScenarioContent(
    theme_key="fairy_tale_world",
    name="Masal Dünyası Macerası",
    location_en="Fairy Tale World",
    default_page_count=22,
    flags={"no_family": True},

    story_prompt_tr="""
# MASAL DÜNYASI MACERASI — KLASİK MASALLARIN İÇİNDE

## YAPI: {child_name} yanında {animal_friend} ile bir masal kitabının içine giriyor. Farklı masalların dünyalarından geçerek bir bulmaca çözüyor ve masal kitabını kurtarıyor. Her bölüm farklı bir masal dünyası.

**BAŞLIK:** "[Çocuk adı]'ın Masal Dünyası"

---

### Bölüm 1 — Kitabın İçine (Sayfa 1-4)
- {child_name} büyük bir eski masal kitabı buluyor, yanında {animal_friend}.
- Kitabı açınca sayfalar parlıyor — içine çekiliyorlar!
- İlk düşüş: büyülü bir orman. Dev mantarlar, konuşan çiçekler.
- Bir tabela: "Masalların kilidi kırılmış. 3 anahtar bul, kitabı kurtar!"

### Bölüm 2 — Şeker Evi (Sayfa 5-9)
- Dev çikolata ağaçları, marshmallow yollar — tatlı dünyası!
- Kurabiye bir ev — ama terk edilmiş, kırık bir halde.
- Evin içinde ilk anahtar — ama bir bulmaca çözmeli: şeker renklerini doğru sıralama.
- {animal_friend} yuvarlak şekerleri buluyor, {child_name} sıralıyor.
- İlk anahtar — altın rengi bir çiçek anahtarı!

### Bölüm 3 — Ejderha Kalesi (Sayfa 10-14)
- İkinci dünya: taş kale, kuleler, bayraklar. Ortaçağ tarzı.
- Kalede uyuyan dev bir ejderha — dostça! Hapşırınca alev çıkıyor.
- Ejderhanın boynundaki madalyonda ikinci anahtar var — ama kilitli!
- Kilidin bulmacası: 3 taş sembolü doğru sırada basmak.
- {child_name} çözüyor — ikinci anahtar: gümüş yıldız anahtarı!

### Bölüm 4 — Bulutlar Krallığı (Sayfa 15-18)
- Üçüncü dünya: pamuk bulutlar, gökkuşağı köprüler, uçan balinalar.
- Bulut sarayında son anahtar — bir gökkuşağı labirentini geçmeli.
- {animal_friend} yukarıdan yol gösteriyor, {child_name} labirentte ilerliyor.
- Üçüncü anahtar: kristal gökkuşağı anahtarı! Üçü bir araya geliyor.

### Bölüm 5 — Kitabın Kurtuluşu (Sayfa 19-22)
- 3 anahtarı kitabın kilidine koyuyor — sayfalar canlanıyor!
- Tüm masal karakterleri sevinçle kutlama yapıyor.
- Kitaptan dışarı çıkış — oda aynı, kitap önünde açık.
- "Her kitabın içinde bir dünya var. Okumak en büyük macera."

---

## 🚫 KURALLAR
- AİLE YOK. Sahnelerde sadece {child_name} + {animal_friend}.
- {animal_friend} AYNI görünüm her sayfada.
- Korku/şiddet YOK. Eğlenceli, fantastik.
- DUYGU: amazed, smiling, determined.

Hikayeyi TAM OLARAK {page_count} sayfa yaz.
""",

    cover_prompt_template=(
        'A young child stepping into a giant glowing storybook, '
        'wearing {clothing_description}. {scene_description}. '
        'Magical fairy tale world with giant mushrooms, candy houses, floating castles. '
        'Warm fantasy lighting, sparkling particles. {STYLE}'
    ),
    page_prompt_template=(
        'A young child {scene_description}, wearing {clothing_description}. '
        'Fairy tale setting: enchanted forest, candy world, stone castle, cloud kingdom. '
        'Warm magical lighting, sparkles. {STYLE}'
    ),

    outfit_girl=(
        "deep plum velvet cape over a cream medieval-style tunic dress with gold trim, "
        "soft brown leather ankle boots, a small golden crown headband, "
        "a tiny embroidered pouch on a leather belt. "
        "EXACTLY the same outfit on every page."
    ),
    outfit_boy=(
        "forest green hooded short cape over a cream linen tunic with gold buttons, "
        "dark brown leather breeches tucked into soft brown boots, "
        "a small leather adventurer's satchel. "
        "EXACTLY the same outfit on every page."
    ),

    companions=[
        CompanionAnchor(
            name_tr="Konuşan Masal Baykuşu",
            name_en="wise small purple owl with golden spectacles",
            species="owl",
            appearance="wise small purple owl with golden spectacles perched on its beak and bright golden eyes",
            short_name="Baykuş",
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
        "primary": ["Enchanted forest with giant mushrooms", "Candy/gingerbread house",
                     "Medieval stone castle with dragon", "Cloud kingdom with rainbow bridges"],
        "atmosphere": "Magical, whimsical, colorful, fairy tale wonder",
    },

    location_constraints=(
        "Pages 1-4: Book entry, enchanted forest arrival. (Wide Shot, magical) "
        "Pages 5-9: Candy world, gingerbread house. (Medium Shot, colorful) "
        "Pages 10-14: Stone castle, sleeping dragon. (Medium Shot, dramatic) "
        "Pages 15-18: Cloud kingdom, rainbow labyrinth. (Wide Shot, ethereal) "
        "Pages 19-22: Book exit, celebration. (Hero Shot, warm)"
    ),

    scenario_bible={},
    custom_inputs_schema=[
        {"key": "animal_friend", "type": "select", "label": "Masal Dostu",
         "default": "Konuşan Masal Baykuşu", "required": True, "companion_ref": True},
    ],
))
