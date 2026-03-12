"""Sultanahmet'te Zamanın Fısıltısı — İstanbul tarihi yarımadam macerası.

TİP A: Tek Landmark (Sultanahmet Meydanı). Zaman kırpışmaları.
Companion: Güvercin / Sokak Kedisi
Obje: Mekanik Ses Çarkı
"""

from app.scenarios._base import CompanionAnchor, ObjectAnchor, ScenarioContent
from app.scenarios._registry import register

SULTANAHMET = register(ScenarioContent(
    theme_key="sultanahmet",
    name="Sultanahmet'te Zamanın Fısıltısı",
    location_en="Sultanahmet Mosque (Blue Mosque)",
    default_page_count=22,
    flags={"no_family": False},

    story_prompt_tr="""
# SULTANAHMET'TE ZAMANIN FISILTISI: GİZEMLİ MACERA

## YAPI: {child_name} yanında {animal_friend} ile Sultanahmet'te eski bir "ses çarkı" bulur, tarihi zaman kırpışmaları yaşar ve kayıp bir emaneti bulur. Heyecanlı, gizemli, tempolu. Tam ışınlanma yok — kısa anlarda eski zamanlar üst üste biniyor.

**BAŞLIK:** "[Çocuk adı]'ın Zamanın Fısıltısı: Sultanahmet"

---

### Bölüm 1 — Gizemli Çark (Sayfa 1-3)
- {child_name} akşamüzeri Sultanahmet Meydanı'nda, yanında {animal_friend}. Yerde eski bir rehber kitap ve içinde pirinç mekanik ses çarkı buluyor.
- Çarkı çevirdiğinde ince bir melodi — etraf bir an eski zamanmış gibi titriyor!
- Güvercinler havalanıyor, kitaptan harita parçası uçuyor. El yapımı haritada 3 işaret: çeşme, kapı kemeri, taş desen.

### Bölüm 2 — Zaman Kırpışması (Sayfa 4-6)
- Haritadaki işaretleri takip ederek çeşmeye koşuyor. Çarkı çevirince kalabalık bir anlığına Osmanlı kıyafetli insanlara dönüşüyor!
- Koşan birinin elinden küçük mühür kılıfı düşüyor. Görüntü günümüze dönüyor ama düşme noktası kayda geçti.

### Bölüm 3 — Kayıp Görev (Sayfa 7-10)
- Taş desenlerin köşesinde mühür kılıfı — ama içi boş!
- Rehber: "Sergiye ait önemli mühür kayboldu!" — görev net.
- Haritadaki ikinci işaret: kapı kemeri. Zaman dalgasıyla yeni bir bulmaca (Lale, Dalga, Yıldız oymalarını sırala).

### Bölüm 4 — Gölgenin Oyunu (Sayfa 11-14)
- Sıralama çözüldü — haritada yeni ok: "Gölge nereye düşerse..."
- Güneş batmadan gölge çizgisini takip. Eski ahşap bankın altında gizli kese!
- İçinde mührün yarısı — ama parça kırık, diğer yarı eksik.

### Bölüm 5 — Birleşen Yapboz (Sayfa 15-18)
- Çarkı ters çeviriyor — geçmişte mührün savrulma anını izliyor.
- Günümüze dönüp turist dükkanlarında nostaljik çanta püskülü yanında diğer parçayı buluyor.
- İki parçayı birleştirince haritadaki semboller altın gibi parlıyor!

### Bölüm 6 — Geriye Kalan İmza (Sayfa 19-21)
- Mührü sergiye tam zamanında ulaştırıyor. "Büyük bir felaketin önüne geçtin!"
- Ses çarkı son kez ninni gibi çalıyor — eski zamanlardan selam.
- Çark susuyor, çantada parlayan küçük bir yıldız çizimi kalıyor.

---

## 🚫 KURALLAR
- {animal_friend} AYNI görünüm her sayfada.
- Dini/siyasi referans YOK. Dış mekan odaklı.
- HOOK: Her sayfanın sonu merak uyandırmalı.
- AKTİF KAHRAMAN: "İzledi, baktı" değil → "koştu, atladı, kavradı."
- DUYGU: amazed, smiling, determined.

Hikayeyi TAM OLARAK {page_count} sayfa yaz.
""",

    cover_prompt_template=(
        'An {child_age}-year-old {child_gender} named {child_name} with {hair_description}, '
        'wearing {clothing_description}. {scene_description}. Child holding a small mechanical music '
        'wheel glowing golden. Sultanahmet Square with Hagia Sophia dome silhouetted against amber '
        'sunset, white pigeons mid-flight. Warm cinematic golden hour lighting. Low-angle: child 30%, '
        'Ottoman skyline 70%. Regal warm palette: amber gold, Ottoman blue tile, ivory marble. {STYLE}'
    ),
    page_prompt_template=(
        'An {child_age}-year-old {child_gender} named {child_name} with {hair_description}, '
        'wearing {clothing_description}. {scene_description}. Elements: [Sultanahmet Square, historic '
        'stone pavements, archways, stone fountains, warm sunset, pigeons]. Cinematic action lighting, '
        'detailed stone texture. Dynamic action pose. No eye contact with camera. {STYLE}'
    ),

    outfit_girl=(
        "graceful knee-length A-line skirt in deep navy brocade fabric, cream-white high-collar "
        "Victorian blouse with delicate lace cuffs and pearl buttons, tailored double-breasted velvet "
        "vest in deep burgundy, polished dark navy T-strap mary-jane flats, a small embroidered evening "
        "satchel with golden clasp, and a delicate gold hair bow. EXACTLY the same outfit on every page."
    ),
    outfit_boy=(
        "crisp white Wing-collar dress shirt with a slim navy cravat tie, tailored charcoal tweed "
        "double-breasted vest with brass buttons, slim-fit dark charcoal wool trousers, polished "
        "mahogany oxford shoes, a classic charcoal newsboy flat cap, and a golden pocket watch chain. "
        "EXACTLY the same outfit on every page."
    ),

    companions=[
        CompanionAnchor(
            name_tr="Minik Beyaz Güvercin",
            name_en="small pure white dove",
            species="dove",
            appearance="small pure white dove with gentle dark eyes",
            short_name="Beyaz Güvercin",
        ),
        CompanionAnchor(
            name_tr="Tombul Sokak Kedisi",
            name_en="chubby orange and white Istanbul street cat",
            species="cat",
            appearance="chubby fluffy orange and white Istanbul street cat with lazy amber eyes",
            short_name="Sokak Kedisi",
        ),
    ],
    objects=[
        ObjectAnchor(
            name_tr="Mekanik Ses Çarkı",
            appearance_en="small brass mechanical music wheel with tiny gears and warm golden glow",
            prompt_suffix="holding small brass music wheel glowing golden — SAME on every page",
        ),
    ],

    cultural_elements={
        "primary": [
            "Historic stone pavements and narrow Ottoman alleyways",
            "Soaring ancient arched doorways",
            "Ancient carved stone municipal fountains (çeşme)",
            "Warm sunset lighting, sweeping shadows",
        ],
        "secondary": ["Large flocks of white pigeons taking flight", "Ottoman blue tile accents hidden in stonework"],
        "values": ["Problem Solving", "Tracking", "Historical Empathy", "Patience"],
        "atmosphere": "Adventurous, mysterious, fast-paced investigation, sunset magic",
        "sensitivity_rules": ["NO worship close-ups", "Exterior focus", "NO religious figure depictions"],
    },

    location_constraints=(
        "Pages 1-3: Sultanahmet Square, wide sunset skyline. (Wide Shot) "
        "Pages 4-6: Ancient stone fountain. (Medium Shot, golden backlight) "
        "Pages 7-10: Ottoman archways and carved stone walls. (Low Angle, texture) "
        "Pages 11-14: Long shadows on cobblestone near wooden bench. (Close-up, dramatic) "
        "Pages 15-18: Historic tourist bazaar in evening glow. (Dynamic Wide, colorful) "
        "Pages 19-21: Majestic square, twilight. (Epic Hero Shot)"
    ),

    scenario_bible={
        "tone_rules": ["Indiana Jones tarzı heyecanlı macera", "Gizemli ama korkunç değil"],
        "puzzle_types": ["Sembol eşleştirme", "Gölge takip etme", "Harita okuma"],
        "cultural_facts": [
            "Sultanahmet Meydanı Roma Hipodromu üzerine inşa edilmiştir",
            "Dikilitaş M.Ö. 1450 Mısır eseri",
            "Alman Çeşmesi 1901 hediyesi",
        ],
    },

    custom_inputs_schema=[
        {"key": "animal_friend", "type": "select", "label": "Meydan Dostu",
         "default": "Minik Beyaz Güvercin", "required": True, "companion_ref": True},
    ],
))
