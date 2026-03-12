"""Sümela'nın Kayıp Mührü — Manastırda bulmaca macerası.

TİP A: Tek Landmark (Sümela Manastırı). Hardcoded companion: Fındık (sincap).
Obje: Bronz Madalyon
"""

from app.scenarios._base import CompanionAnchor, ObjectAnchor, ScenarioContent
from app.scenarios._registry import register

SUMELA = register(ScenarioContent(
    theme_key="sumela",
    name="Sümela'nın Kayıp Mührü",
    location_en="Sümela Monastery",
    default_page_count=22,
    flags={"no_family": False},

    story_prompt_tr="""
# SÜMELA'NIN KAYIP MÜHRÜ: GİZEMLİ MACERA

## YAPI: {child_name} sevimli sincabı Fındık eşliğinde Sümela Manastırı'nda eski bir bronz madalyon bulur, zaman yolculuğu yapar ve kayıp bir el yazmasını kurtarmak için bulmaca çözer. Atmosferik, heyecanlı, korkutucu değil.

**BAŞLIK:** "[Çocuk adı]'ın Kayıp Mührü: Sümela"

---

### Bölüm 1 — Gizemli Madalyon (Sayfa 1-3)
- {child_name} Altındere Vadisi'nde, yanında Fındık. Hediyelik eşya dükkanında eski bronz madalyon buluyor.
- Madalyonda üç sembol: kartal, anahtar, spiral. Dokunduğunda "tık" diye atıyor.
- Sümela'ya çıkan dik taş yolda rüzgar sertleşiyor, sis sarıyor. Madalyondan çınlama sesi.

### Bölüm 2 — Zaman Kapısı (Sayfa 4-6)
- Manastır içinde silik freksin yanında madalyonla aynı şekilde bir oyuk fark ediyor.
- Madalyonu oyuğa yerleştiriyor — ışık seli, "Vuuuş!" sesi.
- Eski dönemdeki manastır: mum ışıkları, telaşlı insanlar. "Kayıp el yazması yok olursa bilgimiz biter!"

### Bölüm 3 — İpuçlarının Peşinde (Sayfa 7-10)
- Spiral ipucuyla gizli koridor bulma. Dar taş merdivenlere açılan karanlık geçit.
- Üç sembollu ağır kapı — doğru sıralama bulmacası. Fındık duvardaki spirale pençesiyle dokunuyor.
- "Yüksekte uçan, ortada dönen, aşağıyı açan..." sıralamayı çözüyor.

### Bölüm 4 — Gizemli Takip (Sayfa 11-14)
- Gizli depo odası — el yazması burada değil! Su damlası sesi izleniyor.
- Gizemli bir gölge takip ediyor. Hızlı adımlar, çatlak taşlardan atlama.
- Dar uçurum köprüsü — Fındık çantada sığınıyor, {child_name} rüzgarda geçiyor.

### Bölüm 5 — Bulmacanın Sonu (Sayfa 15-18)
- Devasa eski tahta sandık — anahtar sembolü parladığında gizli çıkıntıda gerçek anahtar.
- El yazması bulundu ama sayfalar kopuk ve karışık! Hız bulmacası.
- Fındık sayfaları tutuyor, {child_name} kartal-spiral dizilimlerinden sırayı çözüyor.

### Bölüm 6 — Geri Dönüş (Sayfa 19-21)
- El yazmasını ulaştırıyor. Yazıcı mühür izi basıyor — gurur ve şaşkınlık.
- Madalyon ısınıyor — dönüş kapısı! Rüzgar fırtınaya dönüşmüş, kapı kapanıyor.
- Koşarak madalyonu yuvasında çeviriyor — flaş! Günümüze dönüş. Avucunda mühür izi yadigar.

---

## 🚫 KURALLAR
- Fındık = HER SAYFADA AYNI: "a small, cute hazelnut-brown squirrel with a bushy fluffy tail, bright curious eyes, and tiny agile paws"
- Dini figür/ibadet detayı YOK. Mimari gizem odaklı.
- HOOK: Her sayfanın son cümlesi merak uyandırmalı.
- DUYGU: amazed, smiling, determined.

Hikayeyi TAM OLARAK {page_count} sayfa yaz.
""",

    cover_prompt_template=(
        'An {child_age}-year-old {child_gender} named {child_name} with {hair_description}, '
        'wearing {clothing_description}. {scene_description}. Sumela Monastery carved into a sheer '
        'cliff face at 1200m altitude. Misty Altindere Valley pine forest below. Child holding an '
        'ancient bronze amulet with golden glow. Dramatic low-angle. Moody adventure palette: '
        'deep forest greens, slate grey rock, warm bronze glow, ethereal white mist. {STYLE}'
    ),
    page_prompt_template=(
        'An {child_age}-year-old {child_gender} named {child_name} with {hair_description}, '
        'wearing {clothing_description}. {scene_description}. Elements: [Sumela Monastery interiors, '
        'stone stairs, misty forest mountains, cliffside architecture, fresco walls, candlelight]. '
        'Cinematic action lighting, warm golden glow, detailed ancient stone texture. Dynamic action '
        'pose, expressive emotion. No eye contact with camera. {STYLE}'
    ),

    outfit_girl=(
        "rich dark forest-green thick knit cardigan with colorful folk embroidery trim, "
        "a cream cotton blouse underneath, dark walnut-brown A-line midi skirt with subtle plaid, "
        "sturdy dark brown leather lace-up hiking boots with thick wool socks, "
        "a colorful woven headband, and a rustic leather satchel. "
        "EXACTLY the same outfit on every page."
    ),
    outfit_boy=(
        "chunky dark navy cable-knit fisherman sweater with wide rolled collar, "
        "rugged charcoal-grey climbing trousers with reinforced knees, "
        "sturdy dark brown leather mountain boots, a flat charcoal herringbone tweed kasket cap, "
        "and a worn dark leather crossbody messenger bag. "
        "EXACTLY the same outfit on every page."
    ),

    # Hardcoded companion — no user selection
    companions=[
        CompanionAnchor(
            name_tr="Fındık",
            name_en="small cute hazelnut-brown squirrel",
            species="squirrel",
            appearance="small cute hazelnut-brown squirrel with a bushy fluffy tail, bright curious eyes, and tiny agile paws",
            short_name="Fındık",
        ),
    ],
    objects=[
        ObjectAnchor(
            name_tr="Bronz Madalyon",
            appearance_en="ancient bronze amulet/medallion with eagle, key, and spiral symbols, warm golden glow",
            prompt_suffix="holding ancient bronze amulet with three symbols — SAME on every page",
        ),
    ],

    cultural_elements={
        "primary": [
            "Altındere Valley dense pine forest and misty mountain paths",
            "Steep ancient stone steps carved into the cliff",
            "Byzantine rock-carved monastery — stone arches, terraces, hidden rooms",
            "Ancient fresco walls with faded mysterious symbols",
        ],
        "secondary": [
            "Mountain peaks with deep valley drops and fog",
            "Hidden stone corridors lit by flickering candlelight",
            "Narrow cliff-edge stone bridge with wind",
        ],
        "values": ["Courage", "Intelligence", "Puzzle Solving", "Discovery"],
        "atmosphere": "Adventurous, mysterious, hidden passages, monastery",
        "sensitivity_rules": ["NO religious figure depictions", "NO worship details", "Architecture and mystery focus"],
    },

    location_constraints=(
        "Pages 1-3: Altındere Valley, forested stone path. (Wide Shot, misty) "
        "Pages 4-6: Monastery entrance, fresco wall, hidden niche. (Medium Shot, candlelight) "
        "Pages 7-10: Dark narrow corridors, carved stone door puzzle. (Close-up, dramatic shadows) "
        "Pages 11-14: Hidden storage room, cliff-edge bridge. (Low Angle, vertigo) "
        "Pages 15-18: Secret chamber with chest and page puzzle. (Close-up, golden glow) "
        "Pages 19-21: Running back, time-flash return. (Epic Wide Shot, mist clearing)"
    ),

    scenario_bible={
        "side_character": {
            "name": "Fındık", "type": "squirrel",
            "appearance": "small cute hazelnut-brown squirrel with bushy fluffy tail, bright curious eyes",
        },
        "tone_rules": [
            "Dini figür veya ibadet detayı YOK — mimari gizem odaklı",
            "Bulmaca ve zeka odaklı engeller",
            "Rüzgar, sis ve taş mimari ile atmosfer yaratma",
        ],
    },

    custom_inputs_schema=[],  # No companion selection — Fındık is hardcoded
))
