"""Masal Dünyası — Klasik masal dünyalarında bulmaca macerası.

TİP C: Fantastik. Companion: Konuşan Masal Baykuşu (SABİT).
Objeler: Altın Çiçek Anahtarı, Gümüş Yıldız Anahtarı, Kristal Gökkuşağı Anahtarı
"""

from app.scenarios._base import CompanionAnchor, ObjectAnchor, ScenarioContent
from app.scenarios._registry import register

FAIRY_TALE = register(ScenarioContent(
    # ── A: Temel Kimlik ──
    theme_key="fairy_tale_world",
    name="Masal Dünyası Macerası",

    # ── B: Teknik ──
    location_en="Fairy Tale World",
    default_page_count=22,
    flags={"no_family": True},

    # ── E: Hikaye Promptu (iyileştirilmiş — ~750 kelime) ──
    story_prompt_tr="""\
# MASAL DÜNYASI MACERASI — KLASİK MASALLARIN İÇİNDE

## YAPI: {child_name} TEK BAŞINA, AİLE YOK. Yanında sadece Bilge (küçük mor baykuş, altın gözlüklü).

**KRİTİK — METİN UZUNLUĞU:** Her sayfa 1-3 cümle, toplam 25-50 kelime. Kısa tut, sayfaya sığsın.

**KARAKTER:** {child_name} ({child_age} yaşında, {child_gender}). Yardımcı: Bilge — küçük mor tüylü baykuş, gagasının üzerinde minik altın gözlükler, parlak altın gözler. Her sayfada AYNI görünüm — DEĞİŞTİRME.

**KARAKTER ARC — İÇ YOLCULUK:**
{child_name} başta kitapları sadece resimlere bakan, okuma zahmetinden kaçınan bir çocuk. \
Hikayelerin içine düştüğünde her bulmacayı çözmek için ipuçlarını OKUMASI gerekiyor. \
Her çözdüğü anahtar bulmacasıyla hem macera ilerliyor hem de harflerin/kelimelerin gücünü keşfediyor. \
Doruk noktasında bulut labirentinde Bilge KAYBOLUR — {child_name} ipuçlarını TEK BAŞINA okuyup yol bulmalı. \
Hikayenin sonunda {child_name} artık kitaplara bambaşka bakan bir çocuk — ama bu DEĞİŞİM ASLA SÖYLENMEMELİ, sadece EYLEMLERİYLE hissettirilmeli.

**YASAK:** Anne, baba, aile üyesi, öğretmen YOK. Korku/şiddet YOK — eğlenceli, fantastik. Gezi rehberi formatı YOK.

---

### BÖLÜM 1 — Kitabın İçine (Sayfa 1-4) 🎯 Duygu: MERAK + ŞAŞKINLIK
- {child_name} odasında tozlu bir raf arasında büyük, eski bir masal kitabı buluyor. Kapağı kabartma, kenarları altın yaldızlı.
- ✋ Kitabın kapağına dokunuyor — kabartmalar pürüzlü ve sıcak, sayfalar eski kağıt kokuyor.
- Kitabı açıp ilk sayfaya parmağını koyuyor — sayfalar parıldamaya başlıyor! "Ne oluyor?!" diyor {child_name}, gözleri kocaman.
- 🔊 Sayfalardan fısıltılar yükseliyor, rüzgar gibi bir ses çekiyor — ve birden HER ŞEY dönüyor!
- {child_name} büyülü bir ormanda buluyor kendini — dev mantarlar, konuşan çiçekler, pamuk bulutlar. Bilge bir ağaç dalından süzülüp omzuna konuyor.
- Bir tahta tabela: "Masalların kilidi kırılmış. 3 anahtar bul, kitabı kurtar!" Bilge gözlüklerini düzeltiyor: "Hıhı, büyük iş."
- 🪝 HOOK: "İlk anahtar şeker kokulu bir yolun sonundaydı — ama yol birdenbire iki kola ayrılıyordu..."

### BÖLÜM 2 — Şeker Evi (Sayfa 5-9) 🎯 Duygu: HEYECAN → EĞLENCELİ GERİLİM
- Dev çikolata ağaçları, marshmallow taşlar, lolipop çiçekler — tatlı dünyası! 👃 Her yer karamel ve vanilya kokuyor.
- {child_name}: "Her şey yenilebilir mi?!" Bilge kanatlarını sallıyor: "Dokunmadan önce düşün."
- Kurabiye bir ev — ama terk edilmiş, çatısı çökmüş, kapısı aralık. ✋ Kapı kolunu tutuyor — kurabiye, sıcak ve gevrek.
- Evin içinde şeker renkli bloklar ve bir kilit. Duvarda yazı: "Renkleri gökkuşağı sırasına diz." Bilge okuyamıyor — karanlık çok fazla.
- {child_name} pencerenin kepenğini açıyor — ışık giriyor! Bloklardaki harfleri okuyabiliyor: K-I-R-M-I-Z-I, T-U-R-U-N-C-U...
- Bir bir yerleştiriyor — kırmızı, turuncu, sarı, yeşil, mavi, mor. 🔊 Tıklama sesi! Kilit açılıyor.
- İçinden altın rengi bir çiçek anahtarı! Yaprak şeklinde, parlıyor. {child_name} "Bir tane daha!" diyor gülümseyerek.
- 🪝 HOOK: "Ama ikinci anahtar şeker dünyasında değildi — harita taş bir kalenin kulelerine doğru uzanıyordu..."

### BÖLÜM 3 — Ejderha Kalesi (Sayfa 10-14) 🎯 Duygu: GERİLİM → KORKU → CESARET
- İkinci dünya: devasa taş kale, gotik kuleler, rüzgarda dalgalanan bayraklar. 🔊 Rüzgar uluyor, zincirler şıngırdıyor.
- Kale kapısı açık — içeride dev bir ejderha uyuyor! Mor pulları parıldıyor, burunlarından duman çıkıyor.
- {child_name} donup kalıyor. Kalbi küt küt atıyor. Bilge kulağına fısıldıyor: "Sakin. Uyuyor."
- Ejderhanın boynundaki madalyonda ikinci anahtar var — ama madalyonun kilidi sembollerle kaplı!
- Duvardaki taş kabartmalarda 3 sembol: güneş, ay, yıldız. "Hangi sıra?" fısıldıyor {child_name}. Bilge sessiz — cevabı bilmiyor.
- {child_name} tavanı inceliyor — mozaikte gece gökyüzü: önce güneş batar, sonra ay doğar, sonra yıldızlar belirir!
- Sembolleri sırayla basıyor — güneş, ay, yıldız. Madalyon açılıyor! Gümüş yıldız anahtarı! 🔊 Ama ejderha kıpırdıyor — hapşırarak alevler fışkırtıyor!
- {child_name} sıçrayarak kaçıyor — arkasında sıcak hava dalgası. Dışarıya çıkınca gülmeye başlıyor: "Ah! Bu heyecanlıydı!"
- 🪝 HOOK: "Son anahtar yukarıda bir yerdeydi — bulutların arasında, gökkuşağının ötesinde..."

### BÖLÜM 4 — Bulutlar Krallığı (Sayfa 15-18) 🎯 Duygu: HAYRANLIK → ENDİŞE → KARLILIK
- Üçüncü dünya: pamuk bulutların üstünde yürüyorlar! 🔊 Rüzgar fısıltısı, uzaktan çan sesleri. Gökkuşağı köprüleri, uçan balinalar.
- {child_name}: "Bulutların üstünde yürüyorum!" ✋ Bulut yumuşak ve serin, ayak batıyor ama düşmüyor.
- Bulut sarayına giriyorlar — kristal duvarlar, gökkuşağı yansımaları. Son anahtar bir labirentin ortasında!
- Bilge yukarıdan rehberlik etmek için uçuyor — ama bulut duvarı onu kapatıyor! "Bilge!" diye sesleniyor {child_name}. Cevap yok.
- {child_name} yalnız. Duvarlarda yazılar: "Sağa dön", "Geri git", "Yukarı bak." İpuçlarını okuması gerek — bu sefer yardım YOK.
- Her kavşakta durup okuyor. Dudakları kıpırdıyor: "Sol... yol... açık..." Adım adım labirentin merkezine ulaşıyor.
- Ortada kristal gökkuşağı anahtarı! Dokunduğunda tüm labirent eriyip kayboluyor. Bilge hemen omzuna konuyor: "Beni merak ettin mi?"
- 🪝 HOOK: "Üç anahtar bir araya gelince avuçlarında titreşmeye başladı — bir şeyi bekliyorlardı..."

### BÖLÜM 5 — Kitabın Kurtuluşu (Sayfa 19-22) 🎯 Duygu: SEVİNÇ → HUZUR → GURUR
- Büyülü ormana geri dönüyorlar — tahtada şimdi bir kilit var, 3 anahtar deliği!
- {child_name} anahtarları sırayla takıyor — altın çiçek, gümüş yıldız, kristal gökkuşağı. 🔊 Her anahtar dönüşünde müzik gibi bir ses.
- Sayfalar canlanıyor — masal karakterleri resimlerden fırlıyor! Kutlama, konfeti, müzik.
- 🔊 Kahkahalar, alkışlar, müzik kutusunun melodisi. {child_name} alkışlıyor, gözleri parlıyor.
- Bilge {child_name}'in başının üzerinde tur atıyor, altın gözlükleri parıldıyor.
- Bir anda ışıklar sarıyor — oda. Kitap önünde açık, sayfalar hâlâ hafifçe parlıyor.
- {child_name} kitabı kucağına alıyor. Sayfaları yavaşça çeviriyor — bu sefer resimlere değil, kelimelere bakıyor.
- "Bilge son kez göz kırptı sayfanın köşesinden — belki başka bir kitapta yine karşılaşırlardı..."

---

## 🚫 KURALLAR
- AİLE/YETİŞKİN/ÖĞRETMEN YOK. Sahnelerde sadece {child_name} + Bilge (baykuş).
- Bilge her sayfada AYNI görünüm — mor tüyler, altın gözlükler, altın gözler — DEĞİŞMEZ.
- Her anahtar bulunduktan sonra görünmeli — AYNI tasarım.
- Korku/şiddet YOK. Eğlenceli, fantastik. Ejderha DOSTÇA ve komik.
- İlk sayfa [Sayfa 1] ile başla.

## ⚠️ YAZIM KURALLARI

❌ YANLIŞ (Gezi Rehberi): "{child_name} şeker evine gitti. Hansel ve Gretel masalında da böyle bir ev vardır."
✅ DOĞRU (Macera): "Kapı kolunu kavradı — kurabiye, sıcak ve gevrek. İçeriden tatlı bir karamel kokusu süzülüyordu."

❌ YANLIŞ (Doğrudan Öğüt): "{child_name} okumanın ne kadar önemli olduğunu anladı."
✅ DOĞRU (Subliminal): "{child_name} sayfaları çevirdi — bu sefer resimlere değil, kelimelere baktı."

❌ YANLIŞ (Pasif Kahraman): "Bilge her şeyi çözüp {child_name}'e gösterdi."
✅ DOĞRU (Aktif Kahraman): "{child_name} durup okudu. Dudakları kıpırdıyordu: 'Sol... yol... açık...'"

## 💬 DİYALOG KURALI
Her 3-4 sayfada en az 1 kısa diyalog. {child_name} ve Bilge konuşabilir (Bilge kısa, bilge ve bazen komik cümleler kurar).

## ⛔ İÇERİK YASAKLARI
- Anne, baba, aile YASAK (no_family)
- Dini/siyasi referans YASAK
- Gezi rehberi formatı YASAK
- Gerçek korku/şiddet YASAK (komik gerilim OK)

Hikayeyi TAM OLARAK {page_count} sayfa yaz. Her sayfa 1-3 cümle (25-50 kelime).
""",

    # ── F: Görsel Prompt Şablonları (iyileştirilmiş) ──
    cover_prompt_template=(
        'Story "{book_title}". A young child stepping into a giant glowing storybook, '
        'wearing {clothing_description}. {scene_description}. '
        'A small purple owl with golden spectacles perched on the child\'s shoulder. '
        'Magical fairy tale landscape: giant mushrooms, candy houses in distance, '
        'floating castle above clouds, sparkling golden particles in the air. '
        'Warm fantasy lighting, golden glow from the book pages. '
        'Cinematic wide shot, child 30%, magical world 70%. '
        'Space for title at top. {STYLE}'
    ),
    page_prompt_template=(
        'A young child {scene_description}, wearing {clothing_description}. '
        'Setting elements (choose relevant based on scene): '
        'ENCHANTED FOREST: [giant colorful mushrooms, talking flowers, fairy dust particles, '
        'soft magical sunlight, wooden signpost]. '
        'CANDY WORLD: [chocolate trees, marshmallow stones, lollipop flowers, '
        'gingerbread house with icing roof, caramel rivers]. '
        'DRAGON CASTLE: [gothic stone castle with towers and flags, sleeping purple dragon, '
        'torch-lit corridors, stone mosaic ceiling, medallion]. '
        'CLOUD KINGDOM: [cotton cloud ground, rainbow bridges, crystal palace walls, '
        'flying whales in distance, rainbow light refractions]. '
        'CELEBRATION: [fairy tale characters cheering, confetti, musical notes in air, '
        'glowing storybook pages, warm golden light]. '
        'Shot variety: [close-up puzzle solving / medium action / wide fantasy panoramic / '
        'interior moody castle / low-angle hero / bird-eye cloud view]. '
        'Composition: full body visible, fantasy palette (deep plum, warm gold, candy pink, '
        'crystal blue, enchanted green). Text overlay space at bottom. {STYLE}'
    ),

    # ── G: Kıyafetler ──
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

    # ── G2: Tutarlılık Kartları ──
    companions=[
        CompanionAnchor(
            name_tr="Konuşan Masal Baykuşu",
            name_en="wise small purple owl with golden spectacles",
            species="owl",
            appearance=(
                "wise small purple owl with golden spectacles perched on its beak, "
                "bright golden eyes, soft purple-lavender feathers, tiny size"
            ),
            short_name="Bilge",
        ),
    ],
    objects=[
        ObjectAnchor(
            name_tr="Altın Çiçek Anahtarı",
            appearance_en=(
                "golden flower-shaped key with petal details, "
                "warm golden glow, small enough for a child's palm"
            ),
            prompt_suffix="holding golden flower-shaped key — SAME appearance on every page",
        ),
        ObjectAnchor(
            name_tr="Gümüş Yıldız Anahtarı",
            appearance_en=(
                "silver star-shaped key with crescent moon detail, "
                "cool silver shimmer, small enough for a child's palm"
            ),
            prompt_suffix="holding silver star-shaped key — SAME appearance on every page",
        ),
        ObjectAnchor(
            name_tr="Kristal Gökkuşağı Anahtarı",
            appearance_en=(
                "crystal rainbow-colored key with prismatic light refraction, "
                "transparent with rainbow shimmer, small enough for a child's palm"
            ),
            prompt_suffix="holding crystal rainbow key with prismatic light — SAME appearance on every page",
        ),
    ],

    # ── H: Kültürel Elementler ──
    cultural_elements={
        "primary": [
            "Enchanted magical forest with giant mushrooms and talking flowers",
            "Candy and gingerbread house with chocolate trees",
            "Medieval stone castle with friendly sleeping dragon",
            "Cloud kingdom with rainbow bridges and crystal palace",
            "Giant glowing storybook portal between worlds",
        ],
        "secondary": [
            "Marshmallow stepping stones and lollipop flowers",
            "Stone mosaic ceiling depicting night sky (sun, moon, stars)",
            "Flying whales above cloud kingdom",
            "Rainbow labyrinth with written clues on walls",
            "Fairy tale characters celebrating with confetti",
            "Wooden signpost with riddle at crossroads",
        ],
        "colors": "deep plum, warm gold, candy pink, crystal blue, enchanted green, rainbow prismatic",
        "atmosphere": "Magical, whimsical, colorful, fairy tale wonder, playful adventure",
    },

    # ── C/G3: Lokasyon Kısıtları ──
    location_constraints=(
        "Pages 1-4: Room → enchanted forest entry through glowing book — "
        "giant mushrooms, talking flowers, wooden signpost (Wide Shot, magical warm light). "
        "Pages 5-9: Candy world — chocolate trees, gingerbread house interior, "
        "color puzzle blocks (Medium Shot, saturated candy colors). "
        "Pages 10-14: Stone castle — sleeping dragon hall, torch-lit corridors, "
        "symbol puzzle on wall, escaping dragon sneeze (Medium dramatic + Close-up puzzle). "
        "Pages 15-18: Cloud kingdom — cotton cloud ground, crystal palace, "
        "rainbow labyrinth, child ALONE reading clues (Wide ethereal + Close-up reading). "
        "Pages 19-22: Return to enchanted forest → room — key ceremony, "
        "celebration, book closing (Hero Shot, warm golden glow)."
    ),

    # ── I: Scenario Bible ──
    scenario_bible={
        "companion": {
            "name": "Bilge (Konuşan Masal Baykuşu)",
            "personality": (
                "Bilge, kısa ve öz konuşan, bazen komik yorumlar yapan küçük bir baykuş. "
                "Tehlike anında sessizleşir, çocuğu gözleriyle takip eder. Bulut labirentinde "
                "KAYBOLUR — çocuk ipuçlarını TEK BAŞINA okuyarak yol bulmalı. "
                "Sevinçli anlarda kanatlarını çırpar ve 'Hıhı!' der."
            ),
            "role": "Bilge yol arkadaşı, ama kriz anında kayıp",
            "visual_lock": "Small purple owl, golden spectacles on beak, golden eyes — EVERY PAGE SAME",
        },
        "key_objects": {
            "anahtar_1": {
                "name": "Altın Çiçek Anahtarı",
                "description": "Şeker evindeki renk bulmacasını çözünce bulunan ilk anahtar. Çiçek şeklinde, altın rengi.",
                "first_appear": "Sayfa 8-9",
                "visual_lock": "Golden flower-shaped key — SAME on every page",
            },
            "anahtar_2": {
                "name": "Gümüş Yıldız Anahtarı",
                "description": "Ejderha kalesindeki sembol bulmacasını çözünce bulunan ikinci anahtar. Yıldız şeklinde, gümüş.",
                "first_appear": "Sayfa 13",
                "visual_lock": "Silver star-shaped key — SAME on every page",
            },
            "anahtar_3": {
                "name": "Kristal Gökkuşağı Anahtarı",
                "description": "Bulut labirentinin merkezinde bulunan son anahtar. Gökkuşağı renkleri, kristal.",
                "first_appear": "Sayfa 17",
                "visual_lock": "Crystal rainbow key — SAME on every page",
            },
        },
        "zones": {
            "enchanted_forest": "Büyülü, sıcak, merak uyandırıcı — dev mantarlar, konuşan çiçekler, altın ışık",
            "candy_world": "Renkli, tatlı, eğlenceli — çikolata ağaçlar, marshmallow taşlar, karamel kokusu",
            "dragon_castle": "Dramatik, gerilimli, gotik — taş duvarlar, meşale ışığı, uyuyan ejderha",
            "cloud_kingdom": "Rüya gibi, hafif, büyüleyici — pamuk bulutlar, kristal saray, gökkuşağı",
            "celebration": "Neşeli, sıcak, kapanış — konfeti, müzik, altın ışık, kitap sayfaları",
        },
        "emotional_arc": {
            "S1-S4": "Merak + şaşkınlık (kitaba çekilme, büyülü orman keşfi)",
            "S5-S9": "Heyecan + eğlenceli gerilim (şeker evi bulmacası, ilk anahtar)",
            "S10-S14": "Gerilim → korku → cesaret (ejderha kalesi, sembol bulmacası, kaçış)",
            "S15-S18": "Hayranlık → endişe → kararlılık (bulut krallığı, Bilge kayıp, yalnız bulmaca)",
            "S19-S22": "Sevinç + huzur + gurur (kitap kurtuluyor, kutlama, gerçek dünyaya dönüş)",
        },
        "consistency_rules": [
            "Bilge (baykuş) HER sayfada aynı mor tüy + altın gözlük + altın göz görünüm",
            "Her anahtar bulunduktan sonra sonraki tüm sayfalarda görünmeli",
            "Altın Çiçek = sıcak altın, Gümüş Yıldız = soğuk gümüş, Kristal Gökkuşağı = prizma renkleri",
            "Ejderha DOSTÇA — korkunç değil, komik (hapşırınca alev çıkarır)",
            "Bulut labirentinde Bilge KAYIP — çocuk YALNIZ",
            "Çocuğun ortaçağ tarzı kıyafeti TÜM SAYFALARDA birebir aynı",
        ],
        "no_family": True,
    
        "companions": "see_scenario_companions_list",
        "locations": "see_location_constraints",
    },

    # ── J: Custom Inputs — SABİT companion ──
    custom_inputs_schema=[
        {
            "key": "animal_friend",
            "type": "hidden",
            "default": "Konuşan Masal Baykuşu",
        },
    ],
))
