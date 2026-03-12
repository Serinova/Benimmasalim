"""Kudüs Macerası — Eski Şehir keşif macerası.

TİP A: Tek Landmark (Kudüs Eski Şehir). Companion: Güvercin / Serçe.
"""

from app.scenarios._base import CompanionAnchor, ScenarioContent
from app.scenarios._registry import register

KUDUS = register(ScenarioContent(
    theme_key="kudus",
    name="Kudüs Macerası",
    location_en="Old City of Jerusalem",
    default_page_count=22,
    flags={"no_family": False},

    story_prompt_tr="""
# KUDÜS MACERASI — ESKİ ŞEHRİN SIRLARI

## YAPI: {child_name} yanında {animal_friend} ile Kudüs Eski Şehri'nde gizli bir harita bulur ve tarihi mekanları keşfeder. Kültürel zenginlik, barış ve birlikte yaşam vurgusu. Dini hassasiyet: tarafsız, saygılı anlatım.

**BAŞLIK:** "[Çocuk adı]'ın Kudüs Macerası"

---

### Bölüm 1 — Eski Şehir'de İlk Adımlar (Sayfa 1-4)
- {child_name} Kudüs Eski Şehri'nin taş sokaklarında yürüyor, yanında {animal_friend}.
- Bir taş duvardaki çatlakta katlanmış eski bir harita buluyorlar.
- Haritada Eski Şehir'in dört mahallesini gösteren semboller var.
- Her sembol bir bilmeceye karşılık geliyor — çözerse tarihi bir sırra ulaşacak.

### Bölüm 2 — Taş Sokaklar ve Bilmeceler (Sayfa 5-9)
- Dar taş sokaklarda ilerliyor, baharatçı çarşısında renkli tezgahlar.
- İlk bilmece: bir çeşmedeki oyma — su yönünü takip et.
- İkinci bilmece: eski bir kapının üzerindeki taş oymalar.
- {animal_friend} ipuçlarını bulmasına yardım ediyor.

### Bölüm 3 — Zeytin Ağacı ve Barış (Sayfa 10-14)
- Eski bir zeytin ağacının altında üçüncü bilmece — ağacın yaşı binlerce yıl.
- Bilmecenin cevabı: "Barış, sabırla büyür — tıpkı bu ağaç gibi."
- Taş surların üstünden şehrin panoraması — kubbeler, minareler, çan kuleleri birlikte.
- Son bilmece surların içindeki gizli bir odada.

### Bölüm 4 — Sırrın Açılması (Sayfa 15-18)
- Gizli odada eski bir mozaik — tüm medeniyetlerin sembolleri bir arada.
- "Bu şehir herkesin evi" — mozaiğin mesajı.
- Harita tamamen açıldığında tüm yolların birbirine bağlandığını görüyor.

### Bölüm 5 — Kapanış (Sayfa 19-22)
- Gün batımında surlardan şehre bakış — altın ışıkta kubbeler.
- Haritayı güvenli bir yere saklıyor.
- {animal_friend} ile vedalaşma.
- "Kudüs bana herkesi birleştiren bir şey öğretti."

---

## 🚫 KURALLAR
- DİNİ POLEMİK YOK. Tarafsız, saygılı, kültürel zenginlik vurgusu.
- {animal_friend} AYNI görünüm her sayfada.
- Didaktik nasihat YASAK.
- DUYGU: amazed, smiling, determined.

Hikayeyi TAM OLARAK {page_count} sayfa yaz. Her sayfa 1-3 cümle (25-50 kelime).
""",

    cover_prompt_template=(
        'A young child standing before the ancient stone walls of Jerusalem Old City, '
        'wearing {clothing_description}. {scene_description}. '
        'Golden Dome, ancient stone walls, warm sunset light. {STYLE}'
    ),
    page_prompt_template=(
        'A young child {scene_description}, wearing {clothing_description}. '
        'Jerusalem Old City: narrow stone alleys, ancient walls, warm lighting. {STYLE}'
    ),

    outfit_girl=(
        "cream cotton modest dress with delicate olive embroidery, light sage-green linen cardigan, "
        "comfortable brown leather sandals, a small woven shoulder bag, and an olive silk headscarf. "
        "EXACTLY the same outfit on every page."
    ),
    outfit_boy=(
        "light khaki linen shirt with mandarin collar, cream cotton trousers, "
        "brown leather sandals, small canvas messenger bag, and a beige linen flat cap. "
        "EXACTLY the same outfit on every page."
    ),

    companions=[
        CompanionAnchor(
            name_tr="Sevimli Zeytin Dalı Serçesi",
            name_en="tiny olive-brown sparrow with olive branch in its beak",
            species="sparrow",
            appearance="tiny olive-brown sparrow with a small olive branch in its beak",
            short_name="Serçe",
        ),
        CompanionAnchor(
            name_tr="Güvercin Beyazı",
            name_en="small pure white dove",
            species="dove",
            appearance="small pure white dove with gentle dark eyes",
            short_name="Güvercin",
        ),
    ],
    objects=[],

    cultural_elements={
        "primary": ["Jerusalem Old City stone walls", "Ancient olive trees", "Spice market (souk)",
                     "Stone alleys with merchants"],
        "secondary": ["Mosaic art", "Ancient water fountains", "Panoramic view from walls"],
        "atmosphere": "Ancient, peaceful, culturally rich, warm",
        "sensitivity_rules": ["Tarafsız dini anlatım", "NO political references", "Cultural heritage focus"],
    },

    location_constraints=(
        "Pages 1-4: Old City entrance, stone streets. (Wide Shot) "
        "Pages 5-9: Narrow stone alleys, spice market, fountains. (Medium Shot, colorful) "
        "Pages 10-14: Ancient olive garden, city walls panorama. (Wide + Close-up) "
        "Pages 15-18: Hidden room with mosaic. (Close-up, golden light) "
        "Pages 19-22: Sunset from city walls. (Hero Shot, golden hour)"
    ),

    scenario_bible={
        "sensitivity_rules": ["Tarafsız dini anlatım", "NO political references", "Cultural heritage focus"],
    },

    custom_inputs_schema=[
        {"key": "animal_friend", "type": "select", "label": "Yol Arkadaşı",
         "default": "Sevimli Zeytin Dalı Serçesi", "required": True, "companion_ref": True},
    ],
))
