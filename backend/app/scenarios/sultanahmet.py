"""Sultanahmet'te Zamanın Fısıltısı — İstanbul tarihi yarımadam macerası.

TİP A: Tek Landmark (Sultanahmet Meydanı). Zaman kırpışmaları.
Companion: Minik Beyaz Güvercin (SABİT — kullanıcıya seçtirilmez)
Obje: Mekanik Ses Çarkı
"""

from app.scenarios._base import CompanionAnchor, ObjectAnchor, ScenarioContent
from app.scenarios._registry import register

SULTANAHMET = register(ScenarioContent(
    theme_key="sultanahmet",
    name="Sultanahmet'te Zamanın Fısıltısı",
    location_en="Sultanahmet Square, Historic Peninsula, Istanbul",
    default_page_count=22,
    flags={"no_family": False},

    # ── E: Hikaye Promptu (iyileştirilmiş — ~850 kelime) ──
    story_prompt_tr="""\
# SULTANAHMET'TE ZAMANIN FISILTISI: GİZEMLİ MACERA

## YAPI: {child_name} yanında {animal_friend} ile Sultanahmet'te eski bir "ses çarkı" bulur, tarihi zaman kırpışmaları yaşar ve kayıp bir emaneti bulur. Heyecanlı, gizemli, tempolu. Tam ışınlanma yok — kısa anlarda eski zamanlar üst üste biniyor.

**BAŞLIK:** "[Çocuk adı]'ın Zamanın Fısıltısı: Sultanahmet". Alt başlık EKLEME.

**KARAKTER:** {child_name} ({child_age} yaşında, {child_gender}). Yardımcı: {animal_friend} — küçük, bembeyaz, pırıl pırıl gözlü bir güvercin. Her sayfada AYNI görünüm, DEĞİŞTİRME.

**KARAKTER ARC — İÇ YOLCULUK:**
{child_name} başta eski eşyalara dokunmaktan çekiniyor — "Ya kırarım? Ya bozulursa?" Taş kaldırımlarda yürürken bile dikkatli, tedirgin.
{animal_friend} yanında olunca rahatlar ama BÜYÜK kararları henüz kendisi alamıyor — çarkı çevirmek için bile güvercine bakıp onay arıyor.
Macera boyunca adım adım güven kazanır: önce {animal_friend}'ın yardımıyla (haritadaki işareti bulma), sonra KENDİ KARARIYLA (gölge çizgisini yalnız takip etme, zaman dalgasına rağmen mühür parçasını kavrama).
Sonunda {child_name} gözlerinde artık çekingenlik değil, parlak bir kararlılık var — ama bu DEĞİŞİM ASLA SÖYLENMEZ, sadece EYLEMLERİYLE hissettirilir.

**YASAK:** Dini figür/ibadet detayı YOK — MİMARİ GİZEM odaklı. Korku/şiddet YASAK. Cami içi sahnesi YOK — dış mekan ve tarihi yapı odaklı.

---

### Bölüm 1 — Gizemli Çark (Sayfa 1-4) 🎯 Duygu: MERAK + hafif TEDİRGİNLİK
🌍 MEKAN: Sultanahmet Meydanı, Dikilitaş, kaldırım. GERÇEKÇİ sahne. SİHİR YOK.
- {child_name} akşamüzeri Sultanahmet Meydanı'nda yürüyor. 🔊 Güvercinlerin kanat çırpışları, uzaktan tramvay zili, çocuk kahkahaları. Dikilitaş'ın devasa gölgesi kaldırıma uzanıyor. 👃 Simit arabasından sıcak susam kokusu geliyor.
- {animal_friend} kaldırım taşlarının arasında bir şey gagalıyor — eski bir rehber kitap! İçinden pirinç bir mekanik ses çarkı düşüyor. {child_name} eğilip alıyor, elleri biraz titriyor: "Dikkatli olmalıyım, çok eski görünüyor..." ✋ Çarkın dişlileri parmak uçlarında pürüzlü ve soğuk.
- Çarkı yavaşça çevirdiğinde ince bir melodi yükseliyor — 🔊 tınnn tınnn tınnn! Etraf bir an titriyor, taşlar eski zamanmış gibi parlıyor! {animal_friend} heyecanla kanatlarını çırpıp omzuna konuyor.
- Güvercinler sürü halinde havalanıyor, kitaptan el yapımı bir harita parçası uçuyor! {child_name} havada yakalıyor. Haritada üç işaret var: çeşme, kapı kemeri, taş desen. "Bu bir hazine haritası mı?" diye fısıldıyor.
🪝 HOOK: Haritadaki ilk işaret — eski taş çeşme — güneşin altında altın gibi parlıyordu...

---

### Bölüm 2 — Zaman Kırpışması (Sayfa 5-8) 🎯 Duygu: HEYECAN → ŞAŞKINLIK
🌍 MEKAN: Alman Çeşmesi, Arasta Çarşısı, taş sokaklar. GERÇEKÇİ sahne.
- Haritadaki ilk işareti takip ediyorlar. Alman Çeşmesi'nin altın mozaikli kubbesinin altında duruyorlar. 🔊 Su şırıltısı, güvercin sesleri. ✋ Mermer sütun soğuk ve pürüzsüz.
- {child_name} çarkı tekrar çevirince — FLAŞ! Kalabalık bir anlığına değişiyor: Osmanlı kaftanlı insanlar, atlar, ahşap arabalar! {animal_friend} şaşkınlıkla bir daire çizip geri omzuna konuyor. {child_name} gözlerini kocaman açıyor: "Sen de gördün mü bunu?!"
- Koşan birinin elinden küçük bir mühür kılıfı düşüyor — ama görüntü günümüze dönüyor! {child_name} düşme noktasını haritaya işaretliyor. "Hızlı olmalıyız {animal_friend}, ipucu kaybolmadan!"
- {animal_friend} süzülerek Arasta Çarşısı yönünü gösteriyor. 👃 Baharat kokuları, eski deri ve çam reçinesi havada karışıyor. Dar taş sokakta {child_name} koşarak ilerliyor — artık çarkı tutarken elleri TİTREMİYOR.
🪝 HOOK: Mühür kılıfını buldular — ama kapağını açtığında içi BOMBOŞ'tu!

---

### Bölüm 3 — Kayıp Görev (Sayfa 9-12) 🎯 Duygu: GERİLİM → KEŞF
🌍 MEKAN: Hipodrom kalıntıları, Osmanlı kemer kapı, taş oymalar. GERÇEKÇİ sahne.
- Taş desenlerin köşesinde mühür kılıfı duruyor — ama içi boş! {child_name} hayal kırıklığıyla kılıfı çevirip bakıyor. {animal_friend} kılıfın içini gagalıyor ve minik bir kağıt parçası çıkarıyor! "Aferin sana!" diye sevinçle söylüyor {child_name}.
- Kağıtta Osmanlıca bir not: "Sergiye ait önemli mühür kayboldu!" — görev artık net. {child_name} haritadaki ikinci işarete bakıyor: kapı kemeri. "İkinci ipucu orada olmalı."
- Hipodrom kalıntılarının yanından geçerken çark cebinde titriyor. 🔊 Uzaktan yankılanan nallar, su satıcısının sesi... Zaman kırpışması! Bir anlığına taş sütunların etrafında renkli kumaşlar, bayraklar ve kalabalık bir pazar canlanıyor. ✋ Rüzgar yüzüne eski zamanların tozunu fısıldıyor.
- Kapı kemerinin altında duruyor. Kemerdeki oymaları inceliyor — Lale, Dalga, Yıldız desenleri! "Bunları sıralamamız lazım" diyor kararlı bir sesle. {animal_friend} Lale oymayı gagalıyor — doğru başlangıç! {child_name} sırayla Dalga ve Yıldız'a basıyor. 🔊 Tıkk... tıkk... KLIK!
🪝 HOOK: Taşlar arasından gizli bir bölme açıldı — içinden haritada olmayan yeni bir ok işareti parlıyordu!

---

### Bölüm 4 — Gölgenin Oyunu (Sayfa 13-16) 🎯 Duygu: ADRENALİN → CESARET
🌍 MEKAN: Dikilitaş gölgesi, Arnavut kaldırım, eski ahşap bank. GERÇEKÇİ sahne.
- Yeni ok işareti: "Gölge nereye düşerse, emanet orada gizlidir." {child_name} başını kaldırıp güneşe bakıyor. Akşam güneşi alçalmış, gölgeler uzamış! "Güneş batmadan bulmalıyız!" diye koşmaya başlıyor.
- Dikilitaş'ın devasa gölgesi Arnavut kaldırımda uzun bir çizgi oluşturmuş. {child_name} gölge çizgisini takip ediyor — {animal_friend} havada süzülerek yön gösteriyor. 🔊 Ayak sesleri taş kaldırımda yankılanıyor, kalbi hızla çarpıyor.
- Gölge çizgisi eski bir ahşap bankın altına uzanıyor! {child_name} dizlerinin üzerine çöküp bakıyor. ✋ Soğuk taş, ıslak toprak, parmakları bir keseye dokunuyor! "BULDUM!" diye bağırıyor. {animal_friend} sevinçle etrafında daireler çiziyor.
- Kesenin içinde mührün YARISI var — pirinç, ağır, üzerinde hilal ve yıldız oyması. Ama parça kırık, diğer yarısı eksik. {child_name} mühür parçasını avucunda sıkıyor, gözleri kararlı: "Diğer yarıyı da bulacağız." {animal_friend} omzuna konup başını {child_name}'in yanağına yasıyor — sanki "Seninleyim" diyor.
🪝 HOOK: Çark cebinde ANI bir melodi çalmaya başladı — diğer parça yakınlarda mı?

---

### Bölüm 5 — Birleşen Yapboz (Sayfa 17-19) 🎯 Duygu: ÇÖZÜM → ZAFER
🌍 MEKAN: Arasta Çarşısı dükkanları. GERÇEKÇİ sahne.
- Çarkı ters çevirince zaman dalgası daha güçlü geliyor! 🔊 VUUUŞ! Bir anlığına geçmişte mührün ikiye ayrılıp savrulma anını görüyor — bir parça bankın altına, diğeri bir seyyar tüccarın tezgahına düşüyor.
- Günümüze dönüp Arasta Çarşısı'nın turistik dükkanlarında arıyorlar. {animal_friend} bir dükkanın camına konup gagasıyla tık tık vuruyor. {child_name} içeri bakıyor — nostaljik çanta püsküllerinin arasında pirinç bir parça parlıyor! "İşte orada!" 👃 Dükkan eski ahşap ve nane yağı kokuyor.
- Dükkancı amca gülümsüyor: "Bu parçayı yıllardır kimse sormamıştı!" {child_name} iki parçayı yan yana koyuyor. ✋ Parçalar mıknatıs gibi birbirine çekiliyor — KLIK! Mühür TAMAMLANDI! Haritadaki tüm semboller altın gibi parlıyor! {animal_friend} mutlulukla kanatlarını açıp havada bir tur atıyor.
🪝 HOOK: Ama çark son kez titriyor — emaneti teslim etmek için vakitleri daralıyor!

---

### Bölüm 6 — Geriye Kalan İmza (Sayfa 20-22) 🎯 Duygu: HEYECAN → HUZUR + GURUR
🌍 MEKAN: Sultanahmet Meydanı, Ayasofya silueti, akşam. GERÇEKÇİ sahne.
- Koşuyorlar! {child_name} mührü avucunda sıkıca tutarak Sultanahmet Meydanı'na doğru koşuyor. {animal_friend} önden süzülerek yol açıyor. 🔊 Güvercinler kanat çırpıyor, akşam ezanı yankılanıyor, adımları taş kaldırımda tıkırdıyor.
- Meydanın köşesindeki geçici sergi çadırına ulaşıyor — nefes nefese! Sergi görevlisi gözlerine inanamıyor: "Bu... bu kayıp Osmanlı mührü! Yıllardır arıyorduk!" {child_name} mührü uzatıyor, avuçları sıcacık. "Sultanahmet onu bize teslim etti" diyor gülümseyerek.
- Akşam güneşi Ayasofya'nın kubbesini altın rengine boyarken, {child_name} bankta oturuyor. Ses çarkı cebinde son kez ninni gibi bir melodi çalıyor — 🔊 tınnn... tınnn... Sanki eski zamanlardan bir selam, bir teşekkür. Sonra çark susuyor.
- {child_name} {animal_friend}'a bakıp gülümsüyor. Güvercin omzuna konmuş, gözlerini kapatmış, huzurla soluk alıp veriyor. Çantasında küçük bir yıldız çizimi parlıyor — çarkın son hediyesi. {child_name} ufka bakıyor, gözlerinde artık çekingenlik yok, parlak bir ışık var. "Bir dahaki macera nereye olacak acaba?"

---

## 🚫 KURALLAR
- {animal_friend} = küçük bembeyaz güvercin, nazik koyu gözlü. HER SAYFADA AYNI görünüm — DEĞİŞTİRME.
- Mekanik Ses Çarkı = küçük pirinç çark, altın parıltılı. HER SAYFADA AYNI.
- Dini figür/ibadet detayı YOK. Cami içi YOK. Dış mekan ve tarihi yapı odaklı.
- Korku/şiddet/gore YASAK.

## ⚠️ YAZIM KURALLARI

❌ YANLIŞ (Gezi Rehberi): "{child_name} Sultanahmet Meydanı'na geldi. Meydan Roma Hipodromu üzerine inşa edilmiştir ve Dikilitaş M.Ö. 1450 Mısır eseridir."
✅ DOĞRU (Macera): "Dikilitaş'ın devasa gölgesi kaldırıma uzanmıştı — {child_name} gölge çizgisini takip etmeye başladı, çünkü gölge nereye düşerse emanet orada gizliydi!"

❌ YANLIŞ (Doğrudan Öğüt): "{child_name} tarihin ne kadar değerli olduğunu kavradı. Sabırlı olmanın önemini öğrenmişti."
✅ DOĞRU (Subliminal): "Mühür parçaları birleştiğinde haritadaki semboller altın gibi parladı — {child_name}'in avuçları sıcacıktı ve elleri artık titremiyordu."

## 💬 DİYALOG KURALI
Her 3-4 sayfada en az 1-2 kısa diyalog. {child_name} {animal_friend}'a konuşur, güvercin kanatlarını çırparak, gagasıyla dokunarak veya başını yaslayarak tepki verir.

## 🎭 DUYGU AKIŞI
amazed → excited → worried → determined → triumphant → peaceful

Hikayeyi TAM OLARAK {page_count} sayfa yaz. Her sayfa 2-4 cümle, akıcı ve macera dolu.
""",

    # ── F: Görsel Prompt Şablonları ──
    cover_prompt_template=(
        'EXACTLY ONE {child_age}-year-old {child_gender} named {child_name} with {hair_description}, '
        'wearing {clothing_description}. {scene_description}. Child holding a small mechanical music '
        'wheel glowing golden. Sultanahmet Square with Hagia Sophia dome silhouetted against amber '
        'sunset, white pigeons mid-flight. Warm cinematic golden hour lighting. Low-angle: child 30%, '
        'Ottoman skyline 70%. Regal warm palette: amber gold, Ottoman blue tile, ivory marble. {STYLE}'
    ),
    page_prompt_template=(
        'An {child_age}-year-old {child_gender} named {child_name} with {hair_description}, '
        'wearing {clothing_description}. {scene_description}. '
        'EXTERIOR elements: [Sultanahmet Square stone pavements, Ottoman arched doorways, '
        'carved stone fountains, Obelisk of Theodosius, cobblestone alleys, Arasta Bazaar]. '
        'INTERIOR elements: [Historic bazaar shops, lantern-lit corridors, old wooden displays]. '
        'ATMOSPHERIC: [golden hour amber sunset, long dramatic shadows on cobblestone, '
        'white pigeon flocks in flight, warm light on ancient stone, evening glow]. '
        'IMPORTANT: Only ONE child in the entire image, no second child, no twin, no duplicate. '
        'Shot variety: Wide establishing / Medium action / Close-up detail / Low angle hero. '
        'Color palette: amber gold, Ottoman blue tile, ivory marble, warm sunset orange, '
        'deep burgundy accents. '
        'Cinematic golden hour lighting, detailed ancient stone texture. '
        'Dynamic action pose, expressive emotion. No eye contact with camera. {STYLE}'
    ),

    # ── G: Kıyafetler ──
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

    # ── G2: Tutarlılık Kartları ──
    companions=[
        CompanionAnchor(
            name_tr="Minik Beyaz Güvercin",
            name_en="small pure white dove with gentle dark eyes",
            species="dove",
            appearance="small pure white dove with gentle dark eyes, soft pearly feathers, delicate outstretched wings, and a petite coral beak",
            short_name="Beyaz Güvercin",
        ),
    ],
    objects=[
        ObjectAnchor(
            name_tr="Mekanik Ses Çarkı",
            appearance_en="small brass mechanical music wheel with tiny gears and warm golden glow",
            prompt_suffix="holding small brass music wheel glowing golden — SAME on every page",
        ),
    ],

    # ── H: Kültürel Elementler ──
    cultural_elements={
        "primary": [
            "Historic stone pavements and narrow Ottoman alleyways",
            "Soaring ancient arched doorways with carved stone details",
            "Ancient carved stone municipal fountains (çeşme)",
            "Warm amber sunset lighting with sweeping dramatic shadows",
            "The Obelisk of Theodosius (Dikilitaş) — towering ancient Egyptian granite",
            "German Fountain (Alman Çeşmesi) — ornate octagonal dome with gold mosaics",
            "Arasta Bazaar — historic Ottoman stone shopping arcade",
            "Hagia Sophia silhouette against sunset sky (exterior only)",
            "Roman Hippodrome remnants — stone columns, carved reliefs",
            "Cobblestone alleys with overhanging wooden Ottoman balconies",
        ],
        "secondary": [
            "Large flocks of white pigeons taking flight in golden light",
            "Ottoman blue tile accents hidden in stonework",
            "Simit vendors with traditional glass carts",
            "Historic tram bells ringing in the distance",
        ],
        "values": ["Problem Solving", "Tracking", "Historical Empathy", "Patience", "Courage"],
        "atmosphere": "Adventurous, mysterious, fast-paced investigation, golden hour sunset magic",
        "sensitivity_rules": [
            "NO worship close-ups",
            "Exterior focus ONLY — no mosque interior",
            "NO religious figure depictions",
            "NO political symbols or references",
        ],
    },

    # ── C/G3: Lokasyon Kısıtları ──
    location_constraints=(
        "Pages 1-4: Sultanahmet Square, wide sunset skyline, Obelisk shadow. (Wide Shot, golden hour) "
        "Pages 5-8: German Fountain, Arasta Bazaar entrance, narrow stone alleys. (Medium Shot, golden backlight) "
        "Pages 9-12: Hippodrome remnants, Ottoman archway with carved stone walls. (Low Angle, texture detail) "
        "Pages 13-16: Long shadows on cobblestone, old wooden bench, narrow alleys. (Close-up, dramatic shadows) "
        "Pages 17-19: Historic Arasta Bazaar shops, evening glow, colorful displays. (Dynamic Wide, warm interior) "
        "Pages 20-22: Majestic Sultanahmet Square, Hagia Sophia twilight silhouette. (Epic Hero Shot, panoramic)"
    ),

    # ── I: Scenario Bible (zenginleştirilmiş — Sümela formatı) ──
    scenario_bible={
        "no_magic": True,
        "companion_pack": {
            "beyaz_guvercin": {
                "species": "dove",
                "appearance_en": "small pure white dove with gentle dark eyes, soft feathers, and delicate wings",
                "role": "Meydanın kadim sakini, ipuçlarını gagasıyla bulan, havadan süzülerek yön gösteren",
            },
        },
        "key_objects": {
            "mekanik_ses_carki": {
                "appearance_en": "small brass mechanical music wheel with tiny gears and warm golden glow",
                "first_page": 1,
                "last_page": 22,
                "prompt_suffix": "holding small brass music wheel glowing golden — SAME on every page",
            },
            "muhur": {
                "appearance_en": "ornate brass Ottoman seal/stamp with crescent and star carving, palm-sized",
                "first_page": 7,
                "last_page": 21,
                "prompt_suffix": "carrying ornate brass Ottoman seal — SAME appearance once found",
            },
        },
        "side_characters": {
            "dukkanci_amca": {
                "outfit_en": "elderly Turkish bazaar shopkeeper in cream linen shirt, dark brown wool vest with brass buttons, round spectacles",
                "appears_on": [18],
                "rule": "SAME outfit on every appearance",
            },
            "sergi_gorevlisi": {
                "outfit_en": "museum curator in tailored dark navy blazer with golden heritage pin, white shirt",
                "appears_on": [21],
                "rule": "SAME outfit on every appearance",
            },
        },
        "location_zone_map": {
            "sultanahmet_square": "pages 1-4, 20-22",
            "german_fountain_arasta": "pages 5-8",
            "hippodrome_archways": "pages 9-12",
            "shadow_trail_bench": "pages 13-16",
            "bazaar_shops": "pages 17-19",
        },
        "tone_rules": [
            "Indiana Jones tarzı heyecanlı macera — çocuk versiyonu",
            "Gizemli ama korkunç değil — merak ve keşif odaklı",
            "Zaman kırpışmaları KISA anlık — tam ışınlanma yok",
            "Osmanlı atmosferi dış mekan ve sokak hayatından verilir",
        ],
        "puzzle_types": ["Sembol sıralama (Lale-Dalga-Yıldız)", "Gölge takip etme", "Harita okuma", "Parça birleştirme"],
        "cultural_facts": [
            "Sultanahmet Meydanı Roma Hipodromu üzerine inşa edilmiştir",
            "Dikilitaş M.Ö. 1450 Mısır eseri — dünyanın en eski dikili taşlarından",
            "Alman Çeşmesi 1901 yılında II. Wilhelm hediyesi olarak yapılmıştır",
            "Arasta Çarşısı 17. yüzyıl Osmanlı ticaret geleneğini yansıtır",
        ],
        "consistency_rules": [
            "White dove companion MUST have EXACTLY the same pure white appearance on EVERY page",
            "Brass music wheel MUST have the same golden glow and tiny gears on pages 1-22",
            "Ottoman seal MUST have the same crescent-star carving once found (pages 7-22)",
            "Child's outfit MUST NOT change during time flickers",
            "ONLY ONE CHILD in every scene — no duplicate, no twin, no second child",
            "NO magic, NO supernatural powers — time flickers are brief sensory flashes, NOT actual teleportation",
            "Setting MUST be Sultanahmet/Historic Peninsula Istanbul — no forest, no tropical island",
        ],
    
        "companions": "see_scenario_companions_list",
        "locations": "see_location_constraints",
    },

    # ── J: Custom Inputs — SABİT companion ──
    custom_inputs_schema=[
        {
            "key": "animal_friend",
            "type": "hidden",
            "default": "Minik Beyaz Güvercin",
        },
    ],
))
