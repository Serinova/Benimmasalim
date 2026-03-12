"""Abu Simbel'in Güneş Sırrı — Antik Mısır tapınak macerası.

TİP A: Tek Landmark (Abu Simbel Tapınağı). Companion: Altın Çöl Şahini (SABİT).
Objeler: Güneş Diski Madalyonu, Hiyeroglif Haritası
"""

from app.scenarios._base import CompanionAnchor, ObjectAnchor, ScenarioContent
from app.scenarios._registry import register

ABUSIMBEL = register(ScenarioContent(
    # ── A: Temel Kimlik ──
    theme_key="abusimbel",
    name="Abu Simbel'in Güneş Sırrı",

    # ── B: Teknik ──
    location_en="Abu Simbel, Egypt",
    default_page_count=22,
    flags={"no_family": True},

    # ── E: Hikaye Promptu (~750 kelime) ──
    story_prompt_tr="""\
# ABU SİMBEL'İN GÜNEŞ SIRRI — ANTİK MISIR TAPINAĞINDA MACERA

## YAPI: {child_name} TEK BAŞINA, AİLE YOK. Yanında sadece Horus (altın tüylü küçük çöl şahini).

**KRİTİK — METİN UZUNLUĞU:** Her sayfa 1-3 cümle, toplam 25-50 kelime. Kısa tut, sayfaya sığsın.

**KARAKTER:** {child_name} ({child_age} yaşında, {child_gender}). Yardımcı: Horus — küçük altın tüylü çöl şahini, keskin amber gözler, kanat uçları koyu kahverengi. Her sayfada AYNI görünüm — DEĞİŞTİRME.

**KARAKTER ARC — İÇ YOLCULUK:**
{child_name} başta tarihi "sıkıcı taşlar" olarak gören, geçmişe ilgisiz bir çocuk. \
Abu Simbel'in devasa heykelleri karşısında küçüklüğünü hissediyor ve tedirginleşiyor. \
Tapınağın derinliklerinde hiyeroglifleri çözmeye başlayınca tarihin canlı ve heyecanlı olduğunu keşfediyor. \
Doruk noktasında karanlık iç odada güneş ışığını yönlendirmek için TEK BAŞINA çalışıyor — Horus yardım EDEMEZ. \
Hikayenin sonunda {child_name} artık tarihe saygıyla ve merakla bakan bir çocuk — ama bu DEĞİŞİM ASLA SÖYLENMEMELİ, sadece EYLEMLERİYLE hissettirilmeli.

**YASAK:** Anne, baba, aile, rehber, yetişkin YOK. Büyü/sihir YOK — ışık fenomeni doğal optiktir. Mumya, lanet, korku YOK.

---

### BÖLÜM 1 — Tapınağın Kapısında (Sayfa 1-4) 🎯 Duygu: MERAK + KÜÇÜKLÜK HİSSİ
🌍 MEKAN: Abu Simbel DIŞ CEPHE — çöl kumu, 4 dev Ramses heykeli, tapınak giriş kapısı. İÇERİ DEĞİL.
- {child_name} sıcak çöl kumlarında yürüyor. Güneş tepede, kum altın gibi parlıyor. Önde devasa Abu Simbel tapınağı yükseliyor.
- Dört dev Ramses heykeli kapının iki yanında — her biri bir bina yüksekliğinde! {child_name} başını kaldırıp bakıyor, ağzı açık kalıyor.
- 🔊 Çöl rüzgarı kumları savuruyor, uzaktan bir şahin çığlığı. Horus gökyüzünden süzülerek {child_name}'in koluna konuyor.
- ✋ Heykelin ayağındaki taşa dokunuyor — sıcak, pürüzlü, binlerce yıllık. "Ne kadar büyükler..." fısıldıyor.
- Tapınağın kapısında kazınmış hiyeroglifler — bazıları güneş diski, bazıları kuş figürü. Horus gagasıyla bir güneş diskini dürüyor.
- {child_name} dikkatle bakıyor — güneş diskleri bir çeşit yol gösterici gibi, içeri doğru sıralanmış!
- 🪝 HOOK: "Güneş diskleri tapınağın karanlık içine doğru sıralanıyordu — sanki bir sırrı gösteriyorlardı..."

### BÖLÜM 2 — Sütunlu Salon (Sayfa 5-9) 🎯 Duygu: HEYECAN → KEŞİF COŞKUSU
🌍 MEKAN: Tapınak İÇİ — sütunlu salon, hiyeroglif duvarlar, loş ışık huzmesi. DIŞ CEPHE DEĞİL.
- Tapınağın içine giriş — birden serin ve loş. Devasa sütunlar, duvarlarında savaş sahneleri ve tanrı figürleri.
- 🔊 Adımları taş zeminde yankılanıyor. 👃 Hava eski taş ve kuru toprak kokuyor. Horus kanatlarını gergin tutuyor.
- Duvardaki bir panelde hiyeroglifler arasında bir harita! {child_name} parmaklarıyla izliyor — tapınağın iç odalarını gösteren bir plan.
- "Bu bir harita!" diyor heyecanla. ✋ Kabartma hiyeroglifler parmaklarının altında pürüzlü, derin kazınmış.
- Haritadaki bir güneş sembolü tapınağın en derin odasını işaret ediyor — "Güneş Odası."
- Sütunların arasında yürürken duvarlardaki resimler hikaye anlatıyor — Firavun'un güneş tanrısına hediye sunması, Nil'in taşması, hasadın bereketi.
- Horus endişeyle çığlık atıyor — karanlık bir koridorun ağzındalar. İçeriden hafif bir ışık yansıması geliyor.
- 🪝 HOOK: "Koridorun sonundaki ışık titreşiyordu — sanki güneş taşın içine hapsolmuş gibi..."

### BÖLÜM 3 — Karanlık Koridor (Sayfa 10-14) 🎯 Duygu: GERİLİM → KORKU → CESARET
🌍 MEKAN: Tapınak İÇİ — dar taş koridor, bronz aynalar, düşük tavan. Çok karanlık.
- Karanlık koridor — duvarlar daralıyor, tavan alçalıyor. 🔊 Kendi nefes sesi ve kalp atışı. Hava serin ve durgun.
- {child_name} duraksıyor. Karanlıktan korkuyor — ama haritadaki güneş odası çok yakın.
- Horus omzundan havalanıp koridorda ilerliyor, amber gözleri karanlıkta parlıyor. "Tamam, geliyorum" diyor {child_name}, sesi titriyor.
- Duvarlarda bronz aynalar — eski Mısırlıların ışığı yönlendirmek için kullandığı! Bazıları eğik, bazıları düşmüş.
- {child_name} bir aynayı yerden kaldırıyor — ✋ ağır ve soğuk, kenarları oymalı. Kapıdan sızan ışığı yakalıyor ve koridora yansıtıyor!
- "İşe yarıyor!" Bir aynadan diğerine ışığı zıplatarak koridoru aydınlatıyor. Horus sevinçle çığlık atıyor.
- Koridorun sonunda ağır bir taş kapı — üzerinde güneş diski kabartması. Kapının yanındaki bir yuvada eski bir madalyon!
- Altın güneş diski madalyonu — merkezinde berrak bir kristal, etrafında hiyeroglifler. {child_name} boynuna takıyor.
- 🪝 HOOK: "Madalyondaki kristal güneş ışığını yakaladığında, taş kapıdaki güneş diski parlamaya başladı..."

### BÖLÜM 4 — Güneş Odası (Sayfa 15-18) 🎯 Duygu: ŞAŞKınlık → HAYRANLIK → KEŞİF
🌍 MEKAN: Tapınak EN DERİN ODA — altın kaplı duvarlar, 4 tanrı heykeli, yıldız haritaslı tavan. Gökkuşağı ışık.
- Taş kapı açılıyor — içeride küçük ama muhteşem bir oda! Duvarlarda altın kaplama, tavanda yıldız haritası.
- Odanın merkezinde dört heykel — dört tanrı figürü yan yana oturuyor. Birinin kucağında boş bir oyuk!
- {child_name} madalyonu çıkarıyor — kristal tam oyuğa uyuyor! Yerleştirince tavan deliğinden bir güneş ışını sızıyor.
- Işın kristale vuruyor ve odayı GÖKKUŞAĞI renklerine boyuyor! Duvarlar altın, kırmızı, mavi ışıkla parlıyor.
- 👃 Hava amber ve tütsü kokuyor. 🔊 Sessizlik — sadece ışığın sıcaklığı hissediliyor.
- {child_name}'in gözleri dolmak üzere — ama mutluluktan. "Bu... muhteşem" fısıldıyor.
- Horus altın ışıkta kanatlarını açıyor — tüyleri ateş gibi parlıyor. Sanki tapınağın koruyucu ruhu.
- 🪝 HOOK: "Güneş ışığı yavaş yavaş kayarken, {child_name} bu anın sonsuza kadar sürmeyeceğini biliyordu..."

### BÖLÜM 5 — Gün Batımı ve Veda (Sayfa 19-22) 🎯 Duygu: HUZUR → GURUR
🌍 MEKAN: Tapınak DIŞI — çöl gün batımı, kırmızı-altın kum, dev heykellerin gölgeleri. İÇERİ DEĞİL.
- Güneş kayıyor, oda yavaşça karanlığa gömülüyor. {child_name} madalyonu yuvadan çıkarıp boynuna geri takıyor.
- Koridordan çıkış — bu sefer karanlıktan korkmuyor. Aynalardan sızan son ışıklarla yolunu buluyor.
- Tapınağın dışına çıkıyor — gün batımı! Çöl kırmızı ve altın renklerine boyanmış. Dev heykeller gölgelerini uzatıyor.
- Horus kolundan havalanıp tapınağın üzerinde tur atıyor — sonra geri gelip omzuna konuyor. Gagasıyla kulağını dürtüyor.
- {child_name} Ramses heykellerine bakıyor — artık "sıkıcı taşlar" değil. Her çizgide bir hikaye, her sembolde bir sır.
- Madalyon göğsünde sıcacık parlıyor. Çöl rüzgarı yüzünü yalıyor, kumlar altın gibi parıldıyor.
- Arkasına son bir kez bakıyor — tapınak gün batımında dev bir gölge gibi duruyor.
- "Horus son kez çığlık attı ve güneşe doğru süzüldü — belki başka bir kaşifi bekliyordu, binlerce yıldır olduğu gibi..."

---

## 🚫 KURALLAR
- AİLE/YETİŞKİN/REHBER YOK. Sahnelerde sadece {child_name} + Horus (şahin).
- Büyü/sihir YOK — güneş ışığı doğal optik fenomen.
- Mumya, lanet, korku YOK. Macera odaklı.
- Horus her sayfada AYNI görünüm — altın tüyler, amber gözler — DEĞİŞMEZ.
- Güneş Diski Madalyonu bulunduktan sonra her sayfada görünmeli — AYNI altın tasarım.
- İlk sayfa [Sayfa 1] ile başla.

## ⚠️ YAZIM KURALLARI

❌ YANLIŞ (Gezi Rehberi): "{child_name} Abu Simbel tapınağını gördü. Tapınak M.Ö. 1264'te yapılmıştır."
✅ DOĞRU (Macera): "{child_name} başını kaldırdı — dört dev heykel gökyüzüne bakıyordu. Ayak parmakları bile {child_name}'den büyüktü!"

❌ YANLIŞ (Doğrudan Öğüt): "{child_name} tarihin ne kadar önemli olduğunu anlamıştı."
✅ DOĞRU (Subliminal): "{child_name} heykellere baktı — artık sıkıcı taşlar değildi. Her çizgide bir hikaye gizliydi."

## 💬 DİYALOG KURALI
Her 3-4 sayfada en az 1 kısa diyalog. {child_name} Horus'a konuşur, Horus çığlık atarak, gagasıyla dürtülerek, kanat çırparak tepki verir.

## ⛔ İÇERİK YASAKLARI
- Anne, baba, aile YASAK (no_family)
- Dini kutsallık atfı YASAK (antik Mısır mitolojisi tarihî anlatım olarak OK)
- Gezi rehberi formatı YASAK
- Mumya, lanet, korkunç tuzak YASAK

Hikayeyi TAM OLARAK {page_count} sayfa yaz. Her sayfa 1-3 cümle (25-50 kelime).
""",

    # ── F: Görsel Prompt Şablonları ──
    cover_prompt_template=(
        'Story "{book_title}". A young child standing before the colossal Abu Simbel temple, '
        'wearing {clothing_description}. {scene_description}. '
        'A small golden hawk perched on the child\'s arm. '
        'Four massive Ramesses II seated statues flanking the temple entrance, '
        'golden desert sand, deep blue sky, warm amber sunlight. '
        'Cinematic wide shot, child small in foreground 20%, temple 80%. '
        'Rich golden and amber tones. '
        'Space for title at top. {STYLE}'
    ),
    page_prompt_template=(
        'EXACTLY ONE young child {scene_description}, wearing {clothing_description}. '
        'Setting elements (choose relevant based on scene): '
        'EXTERIOR: [colossal Abu Simbel temple facade with four giant Ramesses statues, '
        'golden desert sand dunes, deep blue sky, harsh sunlight, dramatic shadows]. '
        'COLUMNED HALL: [massive stone pillars with carved war scenes and Egyptian gods, '
        'dim interior with light shafts, hieroglyphic walls, cool stone atmosphere]. '
        'DARK CORRIDOR: [narrow stone corridor with bronze mirrors on walls, '
        'minimal light, hieroglyphic carvings, low ceiling, mysterious shadows]. '
        'SUN SANCTUARY: [small golden-walled chamber with four deity statues, '
        'star map on ceiling, rainbow light from crystal, warm amber glow]. '
        'SUNSET: [Abu Simbel silhouette against red-orange sunset sky, '
        'long dramatic shadows on golden sand, warm cinematic light]. '
        'Shot variety: [close-up hieroglyphs / medium action / wide temple panoramic / '
        'interior dramatic lighting / low-angle hero / silhouette sunset]. '
        'IMPORTANT: Only ONE child in the entire image, no second child, no twin, no duplicate. '
        'Composition: full body visible, ancient Egypt palette (golden amber, desert sand, '
        'deep blue, bronze, warm terracotta). Text overlay space at bottom. {STYLE}'
    ),

    # ── G: Kıyafetler ──
    outfit_girl=(
        "cream linen short-sleeve tunic with golden scarab embroidery at collar, "
        "tan cotton wide-leg trousers, sturdy brown leather sandals with ankle straps, "
        "a small canvas crossbody satchel, golden scarab hair pin, "
        "lightweight linen scarf tied as headband. "
        "EXACTLY the same outfit on every page."
    ),
    outfit_boy=(
        "cream linen henley shirt with rolled-up sleeves, "
        "tan cotton cargo shorts with leather belt and brass buckle, "
        "sturdy brown leather sandals with ankle straps, "
        "a small canvas crossbody satchel, "
        "lightweight tan linen cap with wide brim. "
        "EXACTLY the same outfit on every page."
    ),

    # ── G2: Tutarlılık Kartları ──
    companions=[
        CompanionAnchor(
            name_tr="Altın Çöl Şahini",
            name_en="small golden desert hawk",
            species="hawk",
            appearance=(
                "small golden-feathered desert hawk with sharp amber eyes, "
                "dark brown wing tips, compact powerful build, regal posture"
            ),
            short_name="Horus",
        ),
    ],
    objects=[
        ObjectAnchor(
            name_tr="Güneş Diski Madalyonu",
            appearance_en=(
                "golden sun disk medallion with clear crystal center, "
                "hieroglyphic inscriptions around the edge, palm-sized, "
                "hanging on a thin golden chain"
            ),
            prompt_suffix=(
                "wearing golden sun disk medallion with crystal center on golden chain "
                "— SAME appearance on every page"
            ),
        ),
        ObjectAnchor(
            name_tr="Hiyeroglif Haritası",
            appearance_en=(
                "carved stone wall panel showing temple floor plan "
                "with hieroglyphic labels and sun disk markers, "
                "ancient relief carving on limestone"
            ),
            prompt_suffix=(
                "near carved stone map panel with hieroglyphic temple plan "
                "— SAME appearance on every page"
            ),
        ),
    ],

    # ── H: Kültürel Elementler ──
    cultural_elements={
        "primary": [
            "Abu Simbel temple facade with four colossal Ramesses II statues",
            "Egyptian hieroglyphic wall carvings and reliefs",
            "Bronze mirrors for light redirection in dark corridors",
            "Inner sanctuary with four deity statues (sun alignment)",
            "Desert landscape with golden sand dunes",
        ],
        "secondary": [
            "Massive stone pillars with carved war scenes",
            "Scarab beetle and Eye of Horus motifs",
            "Ancient Egyptian star map on ceiling",
            "Solar alignment phenomenon (February 22 / October 22)",
            "Nile river scenes in wall paintings",
            "Amber and incense atmosphere in inner chambers",
        ],
        "colors": "golden amber, desert sand, deep lapis blue, bronze, warm terracotta",
        "atmosphere": "Ancient, monumental, mysterious, sun-worshipping, awe-inspiring",
    },

    # ── C/G3: Lokasyon Kısıtları ──
    location_constraints=(
        "Pages 1-4: Abu Simbel exterior — colossal Ramesses statues, "
        "desert sand, harsh sunlight (Wide panoramic, low-angle awe). "
        "Pages 5-9: Columned hall interior — massive pillars, hieroglyphic walls, "
        "dim light shafts, stone map discovery (Medium Shot, dramatic lighting). "
        "Pages 10-14: Dark corridor — narrow passage, bronze mirrors, "
        "light redirection puzzle, medallion discovery (Close-up dramatic, low-key). "
        "Pages 15-18: Sun sanctuary — golden chamber, deity statues, "
        "crystal light show, rainbow reflections (Wide interior, warm golden). "
        "Pages 19-22: Exit and sunset — temple silhouette, golden desert, "
        "farewell (Hero Shot, cinematic sunset, warm amber)."
    ),

    # ── I: Scenario Bible ──
    scenario_bible={
        "companion": {
            "name": "Horus (Altın Çöl Şahini)",
            "personality": (
                "Asil, keskin gözlü, koruyucu bir çöl şahini. Tehlike sezince çığlık atar, "
                "sevinince kanatlarını açıp gösterir. Karanlık koridorda amber gözleri "
                "karanlıkta parlayarak yol gösterir. Güneş odasında yardım EDEMEZ — "
                "çocuk kristali TEK BAŞINA yerleştirir."
            ),
            "role": "Yol gösterici ve koruyucu, ama kriz anında pasif",
            "visual_lock": (
                "Small golden hawk, amber eyes, dark brown wing tips, "
                "regal posture — EVERY PAGE SAME"
            ),
        },
        "key_objects": {
            "madalyon": {
                "name": "Güneş Diski Madalyonu",
                "description": (
                    "Karanlık koridorun sonundaki yuvada bulunan altın madalyon. Merkezindeki "
                    "kristal güneş ışığını yakalar ve güneş odasını aydınlatır."
                ),
                "first_appear": "Sayfa 13",
                "visual_lock": "Golden sun disk medallion with crystal center on chain — SAME on every page",
            },
            "harita": {
                "name": "Hiyeroglif Haritası",
                "description": "Sütunlu salondaki duvarda kazınmış tapınak planı. Güneş Odası'nın yerini gösterir.",
                "first_appear": "Sayfa 7",
                "visual_lock": "Carved stone panel with temple floor plan — SAME on every page",
            },
        },
        "zones": {
            "exterior": "Sıcak, devasa, göz alıcı — altın kum, dev heykeller, mavi gökyüzü",
            "columned_hall": "Serin, loş, görkemli — dev sütunlar, hiyeroglifler, ışık huzmesi",
            "dark_corridor": "Karanlık, dar, gerilimli — bronz aynalar, soğuk taş, sesler",
            "sun_sanctuary": "Sıcak, altın, büyüleyici — tanrı heykelleri, gökkuşağı ışığı, amber kokusu",
            "sunset_exterior": "Huzurlu, sıcak — kırmızı gün batımı, dev gölgeler, altın çöl",
        },
        "emotional_arc": {
            "S1-S4": "Merak + küçüklük hissi (devasa tapınak ve heykeller)",
            "S5-S9": "Heyecan + keşif coşkusu (sütunlu salon, harita bulma, hiyeroglifler canlı)",
            "S10-S14": "Gerilim → korku → cesaret (karanlık koridor, ayna bulmacası, madalyon)",
            "S15-S18": "Şaşkınlık + hayranlık + keşif (güneş odası, gökkuşağı ışık şovu)",
            "S19-S22": "Huzur + gurur (gün batımı, tapınağa saygı, veda)",
        },
        "consistency_rules": [
            "Horus HER sayfada aynı altın tüy + amber göz + koyu kanat uçları görünüm",
            "Güneş Diski Madalyonu bulunduktan sonra HER sayfada boyunda aynı tasarım",
            "Tapınak dışında güneş SICAK ve PARLAK, içerde SERIN ve LOŞ",
            "Karanlık koridorda tek ışık kaynağı bronz aynalardan yansıyan güneş ışığı",
            "Güneş odasında kristal sayesinde gökkuşağı yansımaları",
            "Çocuğun keten kıyafeti TÜM SAYFALARDA birebir aynı",
            "ONLY ONE CHILD in every scene — no duplicate, no twin, no second child",
            "NO magic, NO supernatural powers — realistic adventure only"
        ],
        "no_family": True,
        "no_magic": True,
    
        "companions": "see_scenario_companions_list",
        "locations": "see_location_constraints",
    },

    # ── J: Custom Inputs — SABİT companion ──
    custom_inputs_schema=[
        {
            "key": "animal_friend",
            "type": "hidden",
            "default": "Altın Çöl Şahini",
        },
    ],
))
