"""Amazon'un Gizli Çağrısı — Yağmur ormanı macerası.

TİP B: Geniş Ortam (Amazon Yağmur Ormanı). Companion: Renkli Papağan (SABİT).
Objeler: Antik Taş Harita, Doğa Madalyonu
"""

from app.scenarios._base import CompanionAnchor, ObjectAnchor, ScenarioContent
from app.scenarios._registry import register

AMAZON = register(ScenarioContent(
    # ── A: Temel Kimlik ──
    theme_key="amazon",
    name="Amazon'un Gizli Çağrısı",

    # ── B: Teknik ──
    location_en="Amazon Rainforest",
    default_page_count=22,
    flags={"no_family": True},

    # ── E: Hikaye Promptu (iyileştirilmiş — ~750 kelime) ──
    story_prompt_tr="""\
# AMAZON'UN GİZLİ ÇAĞRISI — YAĞMUR ORMANI MACERASI

## YAPI: {child_name} TEK BAŞINA, AİLE YOK. Yanında sadece Kızıl (renkli kızıl macaw papağan).

**KRİTİK — METİN UZUNLUĞU:** Her sayfa 1-3 cümle, toplam 25-50 kelime. Kısa tut, sayfaya sığsın.

**KARAKTER:** {child_name} ({child_age} yaşında, {child_gender}). Yardımcı: Kızıl — parlak kırmızı, mavi ve sarı tüylü macaw papağan, parlak siyah gözleri ve kıvrık gagasıyla. Her sayfada AYNI görünüm — DEĞİŞTİRME.

**KARAKTER ARC — İÇ YOLCULUK:**
{child_name} başta ormanın büyüklüğünden ve karanlığından bunalan, doğaya uzak bir şehir çocuğu. \
Kalabalık bitki örtüsü, garip sesler ve bilinmeyen yaratıklar onu tedirgin ediyor. \
Macera boyunca ormanla bağ kurmayı öğreniyor: dalları tanıyor, sesleri çözümlüyor, hayvanlarla iletişim kuruyor. \
Doruk noktasında dev ağacın tıkalı su kaynağını TEK BAŞINA açıyor — Kızıl yardım EDEMEZ, çocuk kendi gücüyle çözer. \
Hikayenin sonunda {child_name} artık ormandan korkmayan, doğanın dilini anlayan bir çocuk — ama bu DEĞİŞİM ASLA SÖYLENMEMELİ, sadece EYLEMLERİYLE hissettirilmeli.

**YASAK:** Anne, baba, aile üyesi, rehber, yetişkin YOK. Sahnelerde sadece çocuk + papağan. Büyü/sihir YOK — doğanın muhteşemliği yeterli. Tehlikeli yılan/jaguar saldırısı YOK.

---

### BÖLÜM 1 — Ormana Giriş (Sayfa 1-4) 🎯 Duygu: MERAK + hafif TEDİRGİNLİK
🌍 MEKAN: Orman KENARI → orman İÇİ giriş — devasa ağaçlar, sarmaşıklar, benekli ışık. SİHİR YOK.
- {child_name} Amazon yağmur ormanının kenarında duruyor. Devasa ağaçlar gökyüzünü kapatmış, yüzlerce yeşil ton birbiriyle yarışıyor.
- 🔊 Kuş cıvıltıları, uzak maymun çığlıkları, yaprakların hışırtısı. 👃 Hava ıslak toprak, yosun ve tropikal çiçek kokuyor.
- Bir ağaç dalından renkli bir papağan süzülüyor — Kızıl! Kanat çırparak {child_name}'in omzuna konuyor. Gagasıyla kulağını dürtüyor.
- {child_name} gülümseyerek Kızıl'a bakıyor: "Yolu biliyor musun?" Kızıl kanatlarını açıp ormanın derinliklerine doğru süzülüyor.
- ✋ {child_name} sarmaşıklardan birini kavrayarak içeri adım atıyor — ayağının altında ıslak yapraklar, nemli ve kaygan.
- Adım adım ilerlerken ışık azalıyor, gölgeler derinleşiyor. Kalbi hızlanıyor ama merak onu çekiyor.
- 🪝 HOOK: "Karanlık yaprak örtüsünün arasından garip bir ışık süzülüyordu — sanki orman onları çağırıyormuş gibi..."

### BÖLÜM 2 — Nehir ve Keşif (Sayfa 5-9) 🎯 Duygu: HEYECAN → ŞAŞKınlık
🌍 MEKAN: Geniş Amazon NEHRİ — dev nilüferler, pembe yunuslar, nehir kıyısında taş harita. Orman içi değil.
- Ormandan çıkıyorlar — geniş bir Amazon nehri! Güneş suyun üzerinde dans ediyor, dev Victoria nilüferleri su yüzeyinde.
- {child_name} nilüferlerin üzerinden atlayarak karşıya geçmeye çalışıyor — Kızıl yukarıdan rehberlik ediyor: "Kak-kak!" diye çığlık atıyor tehlikeli olanları göstermek için.
- ✋ Nilüferin üzeri kaygan ve serin. {child_name} dengesini kaybediyor — kollarını açarak son an durmanı başarıyor! Kalbi küt küt atıyor.
- Nehirde pembe yunuslar süzülüyor — {child_name} ağzı açık izliyor: "Gerçekten pembe!" fısıldıyor.
- Nehrin kenarında, kök sarmaşıkları arasında eski bir taş levha — üzerinde kazınmış semboller, bir harita! Yosunları temizleyince ormanın derinliklerindeki bir noktayı gösteriyor.
- 🔊 Uzaktan bir şelale sesi yükseliyor. Taş harita tam o yöne işaret ediyor.
- 🪝 HOOK: "Haritadaki son sembol bir kalp şeklindeydi — ve şelalenin arkasını işaret ediyordu..."

### BÖLÜM 3 — Gizli Vadi (Sayfa 10-14) 🎯 Duygu: GİZEM → KEŞİF COŞKUSU → ENDİŞE
🌍 MEKAN: Şelale ARKASI geçit → GİZLİ VADİ — biyoüminesans mantarlar, antik taş yapı kalıntıları. Nehir değil.
- Şelaleye ulaşıyorlar — su perdesi parıldıyor. {child_name} derin bir nefes alıp su perdesinin arkasına geçiyor. ✋ Soğuk su yüzünü yalıyor.
- Arkada gizli bir geçit! Kayalık tünel — duvarlar parıldayan yosunlarla kaplı, doğal biyolüminesans ışıkla aydınlanıyor.
- Tünelden çıkınca gizli bir vadi — hiç görülmemiş bitkiler! Parıldayan mantarlar, dev kelebekler, turkuaz çiçekler.
- 👃 Hava bal ve vanilya kokuyor. 🔊 Kuşlar müzik gibi ötüyor, su damlaları ritim tutuyor.
- Vadinin merkezinde eski bir taş yapı — kayıp bir medeniyetin kalıntısı. Duvarlarında hayvan kabartmaları, yaprak motifleri.
- Yapının ortasında bir taş sunak — üzerinde altın renkli bir madalyon! Yaprak ve hayvan motifleriyle süslü, ortasında yeşil bir taş parlıyor.
- Kızıl endişeyle gagasını yapıya sürüyor. Bir şeyler yanlış — 🔊 ormandaki kuş sesleri kesilmiş, sessizlik çökmüş.
- {child_name} madalyonu alıyor — madalyon titreşiyor. "Orman susuyor" diyor {child_name}, sesi endişeli.
- 🪝 HOOK: "Taş haritadaki son işaret — su kaynağı — madalyonun gösterdiği yöndeydi, ama orman neden susmuştu?"

### BÖLÜM 4 — Su Kaynağı Krizi (Sayfa 15-18) 🎯 Duygu: KORKU → CESARET → KARLILIK
🌍 MEKAN: Dev KAPOK AĞACI dibi — tıkalı su kaynağı, kuruyan toprak, çatl ak dallar. Vadi değil.
- Madalyonun yönlendirmesiyle ilerlerken orman değişiyor — yapraklar solmuş, toprak çatlamış. {child_name} yutkunuyor.
- Dev bir kapok ağacının dipine ulaşıyorlar — ağacın kökleri arasından çıkan su kaynağı bir kaya ve dal yığınıyla tıkanmış!
- Kızıl telaşla etrafta uçuyor ama dalları kaldıracak gücü yok. 🔊 {child_name}'in nefes sesi, kendi kalp atışı, çıtırdayan dallar.
- {child_name} duraksıyor. Elleri titriyor. "Ben yapabilirim" diyor sessizce, ama sesi titriyor.
- Derin bir nefes alıyor ve çalışmaya başlıyor — dalları teker teker çekiyor, taşları yuvarllıyor. ✋ Eller çamurlu, tırnaklarda toprak, avuçlar sızlıyor.
- Son kaya yerinden oynuyor — su fışkırıyor! Berrak, soğuk, canlı su topraktan yükseliyor.
- 🔊 Birden kuş sesleri geri dönüyor. Yapraklar canlanıyor. Orman "nefes alıyor."
- 🪝 HOOK: "Madalyon avucunda sıcacık titreşirken, ormanın tamamı yavaş yavaş yeşile dönmeye başlıyordu..."

### BÖLÜM 5 — Ormanın Şarkısı (Sayfa 19-22) 🎯 Duygu: SEVİNÇ → HUZUR → GURUR
🌍 MEKAN: Canlı yeşil orman → orman KENAR gün batımı — turuncu-mor gökyüzü. Nehir/vadi değil.
- Orman yeniden canlanıyor — çiçekler açıyor, kelebekler uçuşuyor, maymunlar daldan dala atlıyor. 🔊 Her yerde yaşam sesleri.
- Kızıl sevinçle takla atıyor havada — tüyleri güneşte altın gibi parlıyor. {child_name} gülümseyerek alkışlıyor.
- Madalyonun ortasındaki yeşil taş güneş ışığında parlıyor — {child_name} onu dikkatle boynuna takıyor.
- Gizli vadiden çıkış yolu — bu sefer orman tanıdık geliyor. Yaprakların hışırtısını, kuş seslerini anlıyor.
- Ormanın kenarında gün batımı — gökyüzü turuncu ve mor renklerle boyanmış. {child_name} duraksıyor, arkasına bakıyor.
- Kızıl omzuna konuyor, gagasıyla saçını dürtüyor. {child_name} gülümsüyor.
- Son gülümsemesiyle ormana bakıyor. Madalyon göğsünde sıcacık atıyor. Orman fısıldıyor — ya da belki sadece rüzgar.
- "Kızıl bir kez daha kanat çırpıp ağaçların arasına süzüldü — belki yarın yeni bir çağrı gelirdi..."

---

## 🚫 KURALLAR
- AİLE/YETİŞKİN YOK. Sahnelerde sadece {child_name} + Kızıl (papağan).
- Büyü/sihir YOK — doğanın muhteşemliği yeterli. Biyolüminesans doğal.
- Kızıl her sayfada AYNI görünüm — kırmızı-mavi-sarı tüyler, siyah gözler — DEĞİŞMEZ.
- Taş Harita bulunduktan sonraki her sayfada görünmeli — AYNI yosunlu taş tasarım.
- Doğa Madalyonu bulunduktan sonra her sayfada görünmeli — AYNI altın+yeşil taş.
- Tehlikeli hayvan saldırısı YOK (jaguar, yılan saldırısı yasak).
- İlk sayfa [Sayfa 1] ile başla. Uçak/yolculuk sahnesi YOK.

## ⚠️ YAZIM KURALLARI

❌ YANLIŞ (Gezi Rehberi): "{child_name} Amazon ormanını gördü. Amazon ormanları dünyanın akciğerleridir. Sonra nehre gitti."
✅ DOĞRU (Macera): "Sarmaşıkları kavrayarak öne atıldı — ayağının altındaki yaprak tabakası çatırdadı ve karanlık yaprak örtüsünden garip bir ışık süzüldü!"

❌ YANLIŞ (Doğrudan Öğüt): "{child_name} doğayı korumanın ne kadar önemli olduğunu anladı. Bu macera ona çok şey öğretmişti."
✅ DOĞRU (Subliminal): "{child_name} son kayayı yerinden oynattığında su fışkırdı — orman yeniden nefes almaya başladı."

❌ YANLIŞ (Pasif Kahraman): "{child_name} Kızıl'ın arkasından gitti. Papağan her şeyi gösterdi."
✅ DOĞRU (Aktif Kahraman): "{child_name} dalları teker teker çekti, taşları yuvarladı — elleri çamurlu, ama gözleri kararlıydı."

## 💬 DİYALOG KURALI
Her 3-4 sayfada en az 1 kısa diyalog olmalı. {child_name} Kızıl'a konuşur, Kızıl kanat çırparak, gagasıyla dürtürek, "kak-kak" diye seslenerek tepki verir.

## ⛔ İÇERİK YASAKLARI
- Anne, baba, aile üyesi, rehber YASAK (no_family)
- Dini/siyasi referans YASAK
- Gezi rehberi formatı YASAK
- Tehlikeli hayvan saldırısı YASAK

Hikayeyi TAM OLARAK {page_count} sayfa yaz. Her sayfa 1-3 cümle (25-50 kelime).
""",

    # ── F: Görsel Prompt Şablonları (iyileştirilmiş) ──
    cover_prompt_template=(
        'Story "{book_title}". A young child standing in a lush Amazon rainforest clearing, '
        'wearing {clothing_description}. {scene_description}. '
        'A colorful scarlet macaw parrot perched on the child\'s shoulder. '
        'Massive jungle trees with huge buttress roots, hanging vines, '
        'colorful macaw parrots flying overhead, dappled green-golden sunlight '
        'streaming through the dense canopy. '
        'Cinematic wide shot, child in foreground 30%, jungle 70%. '
        'Rich tropical greens, warm golden light. '
        'Space for title at top. {STYLE}'
    ),
    page_prompt_template=(
        'EXACTLY ONE young child {scene_description}, wearing {clothing_description}. '
        'Setting elements (choose relevant based on scene): '
        'FOREST ENTRY: [massive Amazon trees with buttress roots, hanging vines and lianas, '
        'dense understory ferns, dappled green sunlight through canopy, misty forest floor]. '
        'RIVER: [wide Amazon river with golden reflections, giant Victoria water lilies, '
        'pink river dolphins swimming, tropical riverbank with palm trees]. '
        'WATERFALL: [cascading waterfall with mist spray, moss-covered rocks, '
        'hidden cave behind water curtain, rainbow in the mist]. '
        'HIDDEN VALLEY: [bioluminescent mushrooms, giant butterflies, turquoise flowers, '
        'ancient stone ruins with leaf carvings, mossy altar]. '
        'KAPOK TREE: [massive kapok tree with spread roots, dry cracked earth vs flowing water, '
        'renewal and green growth spreading]. '
        'Shot variety: [close-up detail / medium action / wide panoramic / '
        'interior cave moody / low-angle hero / bird-eye canopy]. '
        'IMPORTANT: Only ONE child in the entire image, no second child, no twin, no duplicate. '
        'Composition: full body visible, tropical palette (emerald green, golden sunlight, '
        'earth brown, turquoise, warm amber). Text overlay space at bottom. {STYLE}'
    ),

    # ── G: Kıyafetler ──
    outfit_girl=(
        "olive-green cotton explorer vest with many pockets over a cream long-sleeve tee, "
        "khaki adventure shorts with cargo pockets, sturdy brown hiking boots, "
        "a wide-brim khaki sun hat with a red bandana tied around it, "
        "small canvas backpack. EXACTLY the same outfit on every page."
    ),
    outfit_boy=(
        "tan cotton safari shirt with rolled-up sleeves, dark green cargo shorts, "
        "sturdy brown hiking boots, a khaki baseball cap with a leaf emblem, "
        "small green canvas backpack. EXACTLY the same outfit on every page."
    ),

    # ── G2: Tutarlılık Kartları ──
    companions=[
        CompanionAnchor(
            name_tr="Renkli Papağan",
            name_en="colorful scarlet macaw parrot",
            species="macaw parrot",
            appearance=(
                "colorful scarlet macaw parrot with bright red, blue and yellow feathers, "
                "shiny black eyes, curved dark beak, and long tail feathers"
            ),
            short_name="Kızıl",
        ),
    ],
    objects=[
        ObjectAnchor(
            name_tr="Antik Taş Harita",
            appearance_en=(
                "ancient moss-covered stone tablet with carved symbols showing "
                "a map of the deep forest with a heart-shaped marker, palm-sized"
            ),
            prompt_suffix=(
                "carrying ancient moss-covered stone tablet with carved symbols "
                "— SAME appearance on every page"
            ),
        ),
        ObjectAnchor(
            name_tr="Doğa Madalyonu",
            appearance_en=(
                "golden medallion with leaf and animal motifs around the edge, "
                "a glowing green gemstone in the center, hanging on a vine cord"
            ),
            prompt_suffix=(
                "wearing golden medallion with green gemstone on vine cord around neck "
                "— SAME appearance on every page"
            ),
        ),
    ],

    # ── H: Kültürel Elementler ──
    cultural_elements={
        "primary": [
            "Giant kapok trees with massive buttress roots",
            "Amazon river with Victoria water lilies",
            "Hidden waterfall with cave passage behind",
            "Bioluminescent mushrooms and giant butterflies",
            "Ancient stone ruins with nature carvings",
        ],
        "secondary": [
            "Pink river dolphins in the Amazon river",
            "Dense vine-covered canopy blocking sunlight",
            "Moss-covered stone altar in hidden valley",
            "Tropical orchids and turquoise flowers",
            "Spider monkeys swinging through trees",
            "Scarlet macaw parrots in flocks",
            "Giant kapok tree water source at roots",
        ],
        "colors": "emerald green, golden sunlight, earth brown, turquoise, warm amber, moss green",
        "atmosphere": "Lush, mysterious, adventurous, vibrant green, alive and breathing",
    },

    # ── C/G3: Lokasyon Kısıtları ──
    location_constraints=(
        "Pages 1-4: Rainforest edge and entry — massive trees, hanging vines, "
        "dim light through canopy (Wide Shot, green shadows → dappled light). "
        "Pages 5-9: Amazon river crossing — giant lily pads, pink dolphins, "
        "waterfall discovery, stone tablet map (Medium Shot, water reflections, golden). "
        "Pages 10-14: Hidden valley through waterfall cave — bioluminescent plants, "
        "ancient ruins, medallion discovery (Close-up mystical + Wide valley panoramic). "
        "Pages 15-18: Kapok tree water source crisis — dry cracked earth, blocked spring, "
        "child working alone, water restoration (Medium action shots, dramatic). "
        "Pages 19-22: Forest revival, sunset exit — vibrant greens returning, "
        "golden sunset through canopy (Hero Shot, warm golden-green)."
    ),

    # ── I: Scenario Bible ──
    scenario_bible={
        "companion": {
            "name": "Kızıl (Renkli Papağan)",
            "personality": (
                "Neşeli, meraklı, uyarıcı bir macaw papağan. Tehlike görünce yüksek sesle "
                "'kak-kak' diye bağırır, sevinince havada takla atar, çocuğun omzuna konup "
                "gagasıyla saçını dürtüler. Su kaynağı krizinde yardım EDEMEZ — çocuk tek "
                "başına çözer."
            ),
            "role": "Yol gösterici ve duygusal destek, ama kriz anında güçsüz",
            "visual_lock": (
                "Scarlet macaw — bright red, blue, yellow feathers, shiny black eyes, "
                "curved dark beak — EVERY PAGE SAME"
            ),
        },
        "key_objects": {
            "harita": {
                "name": "Antik Taş Harita",
                "description": (
                    "Nehir kenarında bulunan yosunlu taş levha. Üzerinde kazınmış semboller "
                    "ormanın derinliklerindeki gizli vadiyi ve su kaynağını gösterir."
                ),
                "first_appear": "Sayfa 8-9",
                "visual_lock": "Moss-covered stone tablet with carved symbols — SAME on every page",
            },
            "madalyon": {
                "name": "Doğa Madalyonu",
                "description": (
                    "Gizli vadideki antik sunaktan alınan altın madalyon. Yaprak ve hayvan "
                    "motifleriyle süslü, ortasında yeşil taş parlıyor. Su kaynağı ile bağlantılı."
                ),
                "first_appear": "Sayfa 13",
                "visual_lock": "Golden medallion with green gemstone on vine cord — SAME on every page",
            },
        },
        "zones": {
            "forest_edge": "Geniş, aydınlık, merak uyandıran — devasa ağaçlar, sarmaşıklar, ıslak toprak kokusu",
            "river": "Açık, parlak, şaşırtıcı — altın su yansımaları, dev nilüferler, pembe yunuslar",
            "waterfall_cave": "Karanlık, gizemli, keşif dolu — soğuk su spreyi, parıldayan yosunlar",
            "hidden_valley": "Büyüleyici, canlı, renkli — biyolüminesans, turkuaz çiçekler, antik kalıntılar",
            "kapok_tree": "Dramatik, gerilimli, dönüm noktası — kurumuş toprak vs canlı su",
            "sunset_exit": "Huzurlu, sıcak — altın gün batımı, yeşillerin geri dönüşü, orman sesleri",
        },
        "emotional_arc": {
            "S1-S4": "Merak + hafif tedirginlik (ormanın büyüklüğü, bilinmezlik)",
            "S5-S9": "Heyecan + şaşkınlık (nehir geçişi, pembe yunuslar, taş harita keşfi)",
            "S10-S14": "Gizem + keşif coşkusu + artan endişe (gizli vadi, madalyon, orman susuyor)",
            "S15-S18": "Korku → cesaret → kararlılık (su kaynağı tıkalı, çocuk TEK BAŞINA çözer)",
            "S19-S22": "Sevinç + huzur + gurur (orman canlanıyor, madalyon sıcacık, veda)",
        },
        "consistency_rules": [
            "Kızıl (papağan) HER sayfada aynı kırmızı-mavi-sarı tüy + siyah göz görünüm",
            "Antik Taş Harita bulunduktan sonra HER sayfada aynı yosunlu taş tasarım",
            "Doğa Madalyonu bulunduktan sonra HER sayfada aynı altın+yeşil taş tasarım",
            "Orman derinleştikçe ışık AZALIR, gizli vadide biyolüminesans ARTAR",
            "Su kaynağı açıldıktan sonra orman CANLANIR (kurumuş→yeşil geçişi)",
            "Çocuğun kaşif kıyafeti TÜM SAYFALARDA birebir aynı",
            "ONLY ONE CHILD in every scene — no duplicate, no twin, no second child",
            "NO magic, NO supernatural powers — realistic adventure only"
        ],
        "no_family": True,
        "no_magic": True,
    
        "companions": "see_scenario_companions_list",
        "locations": "see_location_constraints",
    },

    # ── J: Custom Inputs — SABİT companion (kullanıcıya seçtirilmez) ──
    custom_inputs_schema=[
        {
            "key": "animal_friend",
            "type": "hidden",
            "default": "Renkli Papağan",
        },
    ],
))
