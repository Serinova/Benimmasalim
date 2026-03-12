"""Oyuncak Dünyası — Minyatür oyuncak macerası.

TİP C: Fantastik. Companion: Pelüş Ayıcık (SABİT).
Objeler: Parıldayan Oyuncak Kutusu, Altın Çark Anahtarı
"""

from app.scenarios._base import CompanionAnchor, ObjectAnchor, ScenarioContent
from app.scenarios._registry import register

TOY_WORLD = register(ScenarioContent(
    # ── A: Temel Kimlik ──
    theme_key="toy_world",
    name="Oyuncak Dünyası Macerası",

    # ── B: Teknik ──
    location_en="Toy World",
    default_page_count=22,
    flags={"no_family": True},

    # ── E: Hikaye Promptu (iyileştirilmiş — ~750 kelime) ──
    story_prompt_tr="""\
# OYUNCAK DÜNYASI MACERASI — MİNYATÜR DÜNYADA DEV MACERA

## YAPI: {child_name} TEK BAŞINA, AİLE YOK. Yanında sadece Ponçik (altın kahverengi pelüş ayıcık, kırmızı papyonlu).

**KRİTİK — METİN UZUNLUĞU:** Her sayfa 1-3 cümle, toplam 25-50 kelime. Kısa tut, sayfaya sığsın.

**KARAKTER:** {child_name} ({child_age} yaşında, {child_gender}). Yardımcı: Ponçik — küçük, altın kahverengi pelüş ayıcık, kırmızı papyon, düğme gözler, yumuşak tüylü. Her sayfada AYNI görünüm — DEĞİŞTİRME.

**KARAKTER ARC — İÇ YOLCULUK:**
{child_name} başta oyuncaklarını sadece dağıtıp bırakan, onlara dikkat etmeyen bir çocuk. \
Oyuncak dünyasına girince onların da "duyguları" olduğunu keşfediyor — bozuk çarklar acı veriyor, tamir mutluluk getiriyor. \
Doruk noktasında büyük tamir mekanizması çok karmaşık — Ponçik yardım EDEMEZ (pelüş parmakları tutamaz). \
{child_name} kendi aklı ve sabrıyla çarkları tamir ediyor. \
Hikayenin sonunda oyuncaklarına bambaşka bakıyor — ama bu DEĞİŞİM ASLA SÖYLENMEMELİ, sadece EYLEMLERİYLE hissettirilmeli.

**YASAK:** Anne, baba, aile üyesi YOK. Korku/şiddet YOK — neşeli, renkli, hayal gücü dolu.

---

### BÖLÜM 1 — Küçülme (Sayfa 1-4) 🎯 Duygu: MERAK + ŞAŞKINLIK
🌍 MEKAN: Çocuk ODASI → küçülmüş ODA (dev oyuncaklar, LEGO duvarları, devasa halı). BÜYÜLÜ.
- {child_name} odasında oyuncakları dağınık yerde. Ponçik rafta, düğme gözleriyle bakıyor.
- Dolabın arkasında eski bir oyuncak kutusu — üzerinde yıldız desenleri, kenarları altın boyalı. {child_name} kapağı açıyor.
- 🔊 Tıng! Kutudan ışık fışkırıyor — her şey dönmeye başlıyor! {child_name}: "Noluyor?!" diye bağırıyor.
- Gözlerini açtığında DEV boyutta oyuncaklar! LEGO blokları duvar gibi yüksek, tahta tren rayları otoyol genişliğinde.
- ✋ Yerdeki halı şimdi çim gibi tüylü, devasa. Ponçik yanında — artık {child_name} ile aynı boyda! Düğme gözleri parlıyor.
- "Ponçik! Sen... hareket ediyorsun!" diyor {child_name}, ağzı açık. Ponçik pelüş kollarını sallıyor ve sırıtıyor.
- Oyuncak kutusundan altın renkli bir çark anahtarı düşüyor — parlıyor. {child_name} cebine koyuyor.
- 🪝 HOOK: "LEGO şehrinden gelen tuhaf bir vızıltı duyuluyordu — ama şehrin ışıkları yanıp sönüyordu..."

### BÖLÜM 2 — LEGO Şehri (Sayfa 5-9) 🎯 Duygu: HEYECAN → KEŞİF COŞKUSU → ENDİŞE
🌍 MEKAN: LEGO ŞEHRİ İÇİ — renkli blok binalar, saat kulesi, oyuncak askerler, tren istasyonu. Oda değil.
- LEGO şehrine giriyorlar — minik evler, mağazalar, parklar. Her şey renkli bloklardan! Oyuncak askerler devriye geziyor.
- 🔊 Küçük kurmalı müzik kutusu sesi, ama YANLIŞ çalıyor — notalar atlıyor, ritim bozuk. Askerler de yavaş hareket ediyor.
- "Bir şey bozulmuş" diyor {child_name}. Ponçik endişeyle kulağını çekiştiriyor.
- Şehrin ortasındaki saat kulesine tırmanıyorlar — ✋ LEGO blokları tırtıklı ve sert, her basamak bir blok yüksekliğinde.
- Saat kulesinin tepesinden bakınca tüm oyuncak dünyası görünüyor: LEGO şehir, kristal göl, peluş dağlar — ama dağın tepesindeki dev çark DURMUŞ.
- "O çark durmuşsa her şey bozuk!" diyor {child_name}. Askerlerin biri yavaşça başını sallıyor — evet.
- Tahta tren istasyonuna koşuyorlar — tren de yavaşlamış ama hâlâ çalışıyor! Atlayıp biniyorlar.
- 🔊 Tren tekerleklerinin ritmik takırtısı, tahta rayların çıtırtısı. Pencereden kristal göl parlıyor.
- 🪝 HOOK: "Tren peluş dağlara doğru tırmanırken gittikçe yavaşlıyordu — durur muydu?"

### BÖLÜM 3 — Peluş Dağları (Sayfa 10-14) 🎯 Duygu: GERİLİM → KARARLILIK → ŞAŞKınlık
🌍 MEKAN: PELUŞ DAĞ TEPESİ — kumaş dağlar, dev çark mekanizması, pamuk bulutlar. LEGO şehri değil.
- Tren durdu! Son durağı — peluş dağların eteği. Dağlar kumaştan, yumuşak, renkli. Pamuk bulutlar, düğme güneş.
- ✋ Peluş dağı tırmanmak ilginç — ayak batıyor, yumuşak, sıcak. Ponçik yuvarlanarak çıkıyor, {child_name} gülüyor.
- Dağın tepesinde devasa bir mekanizma — dev dişli çarklar, yaylar, kurma anahtarları. ANA ÇARK durmuş!
- Mekanizmanın yanında bir yazı: "Üç çarkı doğru sıraya diz. Küçük büyüğü döndürür." {child_name} çarkları inceliyor.
- Ponçik yardım etmeye çalışıyor — ama pelüş parmakları metal çarkları kavrayamıyor! Üzgün bakıyor.
- {child_name}: "Endişelenme Ponçik, ben hallederim." Kolları sıvıyor, derin bir nefes alıyor.
- İlk çark — en küçüğü yerleştiriyor. ✋ Metal soğuk ve ağır, kaygan. Parmakları sızlıyor ama bırakmıyor.
- İkinci çark — doğru yuvaya oturuyor! 🔊 Klik! Bir hareketlenme başlıyor.
- 🪝 HOOK: "Üçüncü çarkı takarken altın çark anahtarı cebinde ısınmaya başladı..."

### BÖLÜM 4 — Büyük Canlanma (Sayfa 15-18) 🎯 Duygu: KEŞİF → PATLAMALI SEVİNÇ
🌍 MEKAN: TÜM OYUNCAK DÜNYASI — canlanan mekanizma, ışıklar, trenler, kutlama. Her yer canlı.
- {child_name} cebinden altın çark anahtarını çıkarıyor — tam üçüncü çarkın yerine uyuyor! Takıyor ve çeviriyor.
- 🔊 Vınnn! Tüm mekanizma dönmeye başlıyor — çarklar birbirine geçiyor, yaylar titreşiyor, müzik yükseliyor!
- Oyuncak dünyası CANLANIYOR! Işıklar yanıyor, trenler çalışıyor, müzik kutuları doğru çalıyor, askerler koşuyor.
- 👃 Hava pamuk şeker ve ahşap kokuyor. 🔊 Müzik, kahkahalar, tren düdükleri, çan sesleri — şenlik!
- Tüm oyuncaklar kutlama yapıyor — LEGO adamlar dans ediyor, oyuncak askerler geçit yapıyor, peluşlar sarılıyor.
- Ponçik sevinçle zıplıyor, pelüş kollarını açıyor, {child_name}'in boynuna sarılıyor. {child_name} gülümsüyor, gözleri parlıyor.
- Düğme güneş daha parlak yanıyor, pamuk bulutlar altın rengine dönüyor. Tüm dünya dans ediyor.
- 🪝 HOOK: "Oyuncak kutusu tekrar parıldamaya başlamıştı — eve dönme zamanıydı..."

### BÖLÜM 5 — Normal Boyuta Dönüş (Sayfa 19-22) 🎯 Duygu: HUZUR → GURUR → BİLGELİK
🌍 MEKAN: Çocuk ODASI gerçek boyut — oyuncaklar yerde, rafükları yerli yerinde, güneş pencereden.
- Parıldayan oyuncak kutusu yere iniyor — kapağı açılıyor, ışık yükseliyor.
- {child_name} Ponçik'e bakıyor. "Seni unutmayacağım" diyor. Ponçik düğme gözleriyle göz kırpıyor — ya da belki sadece ışık öyle yansımıştı.
- Işık sarıyor — ve oda. Normal boyut. Her şey yerli yerinde.
- {child_name} yere bakıyor — oyuncaklar hâlâ dağınık. Ama bu sefer farklı hissediyorlar.
- Yavaşça eğilip her oyuncağı yerleştirmeye başlıyor — LEGO'ları kutusuna, askerleri sıraya, treni rayına.
- ✋ Ponçik'i eline alıyor — yumuşak, sıcak, tanıdık. Rafın en güzel yerine koyuyor. Papyonunu düzeltiyor.
- Oyuncak kutusunun kapağı kapalı, yıldız desenleri hafifçe parlıyor. {child_name} gülümsüyor.
- "Ponçik'in düğme gözleri bir an parlıyor gibi oldu — ama belki sadece pencereden gelen güneşti..."

---

## 🚫 KURALLAR
- AİLE/YETİŞKİN YOK. Sahnelerde sadece {child_name} + Ponçik (pelüş ayıcık).
- Ponçik her sayfada AYNI görünüm — altın kahverengi pelüş, kırmızı papyon, düğme gözler — DEĞİŞMEZ.
- Altın Çark Anahtarı bulunduktan sonra her sayfada görünmeli — AYNI altın çark tasarım.
- Korku/şiddet YOK. Neşeli, renkli, sıcak.
- İlk sayfa [Sayfa 1] ile başla.

## ⚠️ YAZIM KURALLARI

❌ YANLIŞ (Gezi Rehberi): "{child_name} LEGO şehrini gördü. LEGO 1958'de icat edilmiştir."
✅ DOĞRU (Macera): "LEGO blokları duvar gibi yüksekti — {child_name} dev bir kapıdan içeri adım attı."

❌ YANLIŞ (Doğrudan Öğüt): "{child_name} oyuncaklarına dikkat etmenin önemli olduğunu anladı."
✅ DOĞRU (Subliminal): "{child_name} her oyuncağı yavaşça yerine koydu — LEGO'ları kutusuna, askerleri sıraya."

❌ YANLIŞ (Pasif Kahraman): "Ponçik çarkları tamir etti ve {child_name} izledi."
✅ DOĞRU (Aktif Kahraman): "Kollarını sıvadı, çarkı kavradı — metal soğuk ve ağırdı ama bırakmadı."

## 💬 DİYALOG KURALI
Her 3-4 sayfada en az 1 kısa diyalog. {child_name} konuşur, Ponçik pelüş kollarını sallayarak, zıplayarak tepki verir. Ponçik konuşamaz.

## ⛔ İÇERİK YASAKLARI
- Anne, baba, aile YASAK (no_family)
- Dini/siyasi referans YASAK
- Gezi rehberi formatı YASAK
- Korku/şiddet YASAK

Hikayeyi TAM OLARAK {page_count} sayfa yaz. Her sayfa 1-3 cümle (25-50 kelime).
""",

    # ── F: Görsel Prompt Şablonları (iyileştirilmiş) ──
    cover_prompt_template=(
        'Story "{book_title}". A tiny child standing in a giant colorful toy world, '
        'wearing {clothing_description}. {scene_description}. '
        'A fluffy golden-brown teddy bear with red bow tie standing next to the child. '
        'Giant LEGO buildings, wooden train tracks as roads, plush mountains in background, '
        'button sun in sky, sparkling toy box nearby. '
        'Bright cheerful lighting, saturated playful colors. '
        'Cinematic wide shot, child 30%, toy world 70%. '
        'Space for title at top. {STYLE}'
    ),
    page_prompt_template=(
        'A tiny child {scene_description}, wearing {clothing_description}. '
        'Setting elements (choose relevant based on scene): '
        'KIDS ROOM: [messy toy-filled room, shelves with toys, carpet floor, '
        'glowing star-patterned toy box, warm bedroom lighting]. '
        'LEGO CITY: [giant colorful LEGO block buildings, LEGO soldier figures, '
        'tiny shops and parks made of bricks, clock tower, bright primary colors]. '
        'TRAIN: [wooden toy train on wooden tracks, miniature landscape passing by, '
        'crystal lake reflections, rhythmic motion]. '
        'PLUSH MOUNTAINS: [plush fabric mountains in pink and purple, cotton cloud sky, '
        'button sun, soft texture ground, giant gear mechanism at peak]. '
        'CELEBRATION: [all toy types dancing together, LEGO soldiers marching, '
        'confetti, music notes in air, bright festive lighting]. '
        'Shot variety: [close-up detail / medium action / wide panoramic / '
        'interior room / low-angle hero / bird-eye toy world]. '
        'IMPORTANT: Only ONE child in the entire image, no second child, no twin, no duplicate. '
        'Composition: full body visible, toy palette (bright yellow, candy red, LEGO blue, '
        'plush pink, wooden brown, golden accents). Text overlay space at bottom. {STYLE}'
    ),

    # ── G: Kıyafetler ──
    outfit_girl=(
        "bright coral-pink dungarees over a white polka-dot long-sleeve tee, "
        "colorful rainbow-striped knee socks, bright yellow canvas sneakers, "
        "a small star-shaped hair clip, tiny red backpack. "
        "EXACTLY the same outfit on every page."
    ),
    outfit_boy=(
        "bright blue bib overalls over a red-and-white striped crew-neck tee, "
        "colorful mismatched socks, bright green canvas sneakers, "
        "a small propeller beanie hat, tiny yellow backpack. "
        "EXACTLY the same outfit on every page."
    ),

    # ── G2: Tutarlılık Kartları ──
    companions=[
        CompanionAnchor(
            name_tr="Pelüş Ayıcık",
            name_en="fluffy teddy bear plushie",
            species="teddy bear plushie",
            appearance=(
                "fluffy golden-brown teddy bear plushie with a red bow tie, "
                "sewn button eyes, soft fuzzy fur, small and child-sized"
            ),
            short_name="Ponçik",
        ),
    ],
    objects=[
        ObjectAnchor(
            name_tr="Parıldayan Oyuncak Kutusu",
            appearance_en=(
                "wooden toy box with golden star patterns on lid, "
                "brass hinges, glowing warm light from inside when opened"
            ),
            prompt_suffix=(
                "star-patterned wooden toy box with golden glow "
                "— SAME appearance on every page"
            ),
        ),
        ObjectAnchor(
            name_tr="Altın Çark Anahtarı",
            appearance_en=(
                "small golden gear-shaped winding key with ornate teeth, "
                "warm golden glow, fits in a child's palm"
            ),
            prompt_suffix=(
                "holding golden gear-shaped winding key "
                "— SAME appearance on every page"
            ),
        ),
    ],

    # ── H: Kültürel Elementler ──
    cultural_elements={
        "primary": [
            "Giant LEGO city with colorful block buildings",
            "Wooden train tracks and miniature trains",
            "Plush fabric mountains with cotton clouds and button sun",
            "Giant gear mechanism with dişli çarklar and springs",
            "Star-patterned magical toy box portal",
        ],
        "secondary": [
            "LEGO toy soldier figures on patrol",
            "Crystal lake with marble-smooth surface",
            "Music box melody playing through the world",
            "Toy celebration with all types dancing together",
            "Messy-to-tidy kid's room transformation",
            "Pelüş character expressions through button eyes",
        ],
        "colors": "bright yellow, candy red, LEGO blue, plush pink, wooden brown, golden star accents",
        "atmosphere": "Cheerful, colorful, imaginative, playful, warm nostalgic",
    },

    # ── C/G3: Lokasyon Kısıtları ──
    location_constraints=(
        "Pages 1-4: Kid's room → shrinking → giant toy world entry — "
        "messy room, glowing toy box, enormous toys (Medium Shot → Wide Shot, bright). "
        "Pages 5-9: LEGO city and train — colorful block buildings, clock tower, "
        "wooden train ride, crystal lake view (Wide panoramic + Medium action). "
        "Pages 10-14: Plush mountains — soft fabric terrain, cotton clouds, "
        "broken gear mechanism, child working on repair (Medium dramatic + Close-up hands). "
        "Pages 15-18: Big revival — world coming alive, lights, music, "
        "celebration parade, dance (Wide festive panoramic, saturated colors). "
        "Pages 19-22: Return to normal size — room, toys placed carefully, "
        "toy box closing, warm sunset light (Medium intimate, warm golden)."
    ),

    # ── I: Scenario Bible ──
    scenario_bible={
        "companion": {
            "name": "Ponçik (Pelüş Ayıcık)",
            "personality": (
                "Sevimli, meraklı, tonton bir pelüş ayıcık. Sevinince zıplar, endişelenince "
                "kulağını çekiştirir. Tamir krizinde yardım EDEMEZ — pelüş parmakları "
                "metal çarkları kavrayamaz. Çocuğa sarılarak moral verir."
            ),
            "role": "Duygusal destek ve komik anlar, ama kriz anında güçsüz",
            "visual_lock": (
                "Golden-brown fluffy teddy bear, red bow tie, button eyes, "
                "soft fuzzy fur — EVERY PAGE SAME"
            ),
        },
        "key_objects": {
            "kutu": {
                "name": "Parıldayan Oyuncak Kutusu",
                "description": (
                    "Yıldız desenli eski oyuncak kutusu. Açılınca ışık fışkırır ve küçültme/büyütme "
                    "geçidini açar. Giriş ve çıkış portalı."
                ),
                "first_appear": "Sayfa 2",
                "last_appear": "Sayfa 21",
                "visual_lock": "Wooden toy box with golden stars — SAME on every page",
            },
            "anahtar": {
                "name": "Altın Çark Anahtarı",
                "description": (
                    "Oyuncak kutusundan düşen altın dişli çark anahtarı. Dev mekanizmanın "
                    "üçüncü ve son çarkına tam uyuyor."
                ),
                "first_appear": "Sayfa 4",
                "visual_lock": "Golden gear-shaped winding key — SAME on every page",
            },
        },
        "zones": {
            "kids_room": "Gerçek dünya, sıcak, tanıdık — dağınık→düzenli dönüşüm",
            "lego_city": "Renkli, düzenli, canlı — blok evler, askerler, saat kulesi",
            "train_ride": "Ritmik, huzurlu, manzaralı — tahta raylar, kristal göl",
            "plush_mountains": "Yumuşak, sıcak, komik — kumaş dağlar, pamuk bulutlar",
            "mechanism": "Dramatik, gerilimli, teknik — dev çarklar, yaylar, metal",
            "celebration": "Neşeli, parlak, müzikal — tüm oyuncaklar dans ediyor",
        },
        "emotional_arc": {
            "S1-S4": "Merak + şaşkınlık (küçülme, dev oyuncak dünyası)",
            "S5-S9": "Heyecan + keşif coşkusu + endişe (LEGO şehri, bozuk müzik, tren yolculuğu)",
            "S10-S14": "Gerilim → kararlılık → şaşkınlık (çark tamiri, Ponçik yardım edemez)",
            "S15-S18": "Patlayıcı sevinç (dünya canlanıyor, kutlama, müzik)",
            "S19-S22": "Huzur + gurur + bilgelik (normal boyut, oyuncakları dikkatle yerleştirme)",
        },
        "consistency_rules": [
            "Ponçik HER sayfada aynı altın kahverengi + kırmızı papyon + düğme göz görünüm",
            "Altın Çark Anahtarı bulunduktan sonra HER sayfada cepte veya elde aynı tasarım",
            "Oyuncak Kutusu giriş (S2-4) ve çıkış (S19-21) sahnelerinde AYNI tasarım",
            "LEGO şehri bozukken ışıklar sönük, tamir sonrası parlak ve canlı",
            "Müzik kutusu bozukken yanlış nota, tamir sonrası doğru melodi",
            "Çocuğun renkli kıyafeti TÜM SAYFALARDA birebir aynı",
            "ONLY ONE CHILD in every scene — no duplicate, no twin, no second child"
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
            "default": "Pelüş Ayıcık",
        },
    ],
))
