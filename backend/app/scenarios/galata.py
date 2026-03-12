"""Galata'nın Kayıp Işık Haritası — Galata Kulesi'nde ışık bulmacası.

TİP A: Tek Landmark (Galata Kulesi + Beyoğlu). Companion yok.
Obje: Işık Haritası Parşömeni
Yan Rol: Yaşlı Fenerci (2-3 sayfada)
"""

from app.scenarios._base import ObjectAnchor, ScenarioContent
from app.scenarios._registry import register

GALATA = register(ScenarioContent(
    # ── A: Temel Kimlik ──
    theme_key="galata",
    name="Galata'nın Kayıp Işık Haritası",

    # ── B: Teknik ──
    location_en="Galata Tower",
    default_page_count=22,
    flags={"no_family": True},

    # ── E: Hikaye Promptu (iyileştirilmiş — ~750 kelime) ──
    story_prompt_tr="""\
# GALATA'NIN KAYIP IŞIK HARİTASI

## YAPI: {child_name} Galata Kulesi'nde eski bir parşömen buluyor — "Işık Haritası." \
Haritadaki sembolleri takip ederek Galata, Karaköy ve Beyoğlu sokaklarında ışık bulmacaları çözüyor. \
Sihir yok — optik illüzyonlar, yansımalar ve İstanbul'un gerçek tarihi mekanları.

**BAŞLIK:** "[Çocuk adı]'ın Kayıp Işık Haritası: Galata"

**KRİTİK — METİN UZUNLUĞU:** Her sayfa 1-3 cümle, toplam 25-50 kelime. Kısa tut, sayfaya sığsın.

**KARAKTER:** {child_name} ({child_age} yaşında, {child_gender}). Bu senaryoda hayvan arkadaş YOK — {child_name} macerayı TEK BAŞINA yaşıyor.

**KARAKTER ARC — İÇ YOLCULUK:**
{child_name} başta kalabalık sokaklardan çekinen, yalnız başına bir şey başarabileceğinden emin olmayan bir çocuk. \
Her çözdüğü bulmaca ile biraz daha cesaretleniyor. Doruk noktasında karanlık Tünel geçidine TEK BAŞINA giriyor. \
Hikayenin sonunda gözleri parlıyor — İstanbul'un ışığını sadece kendisi keşfetmiş. \
Bu DEĞİŞİM ASLA SÖYLENMEMELİ, sadece EYLEMLERİYLE hissettirilmeli.

**YAN ROL — YAŞLI FENERCİ:** Galata Kulesi'nin tepesinde, eski fenerleri temizleyen yaşlı bir adam. \
Sayfada sadece 2-3 cümlelik yer alır: ilk karşılaşma (S2-3) ve son vedalaşma (S20). \
Kıyafeti: "elderly man in brown leather apron and white cotton shirt, round spectacles" — DEĞİŞMEZ.

---

### BÖLÜM 1 — Kule'de Keşif (Sayfa 1-4) 🎯 Duygu: MERAK + hafif TEDİRGİNLİK
- {child_name} Galata Kulesi'nin dar taş merdivenlerini tırmanıyor. Nefes nefese ama meraklı.
- 🔊 Adımları taş basamaklarda yankılanıyor. Duvarlardan serin, nemli bir taş kokusu geliyor.
- Kulenin tepesinde yaşlı fenerci fenerleri parlatıyor. {child_name}'e kısa bir bakış atıp gülümsüyor: "Dikkatli bak, bu duvarlar konuşur."
- {child_name} taş duvardaki çatlağa parmaklarını sokuyor — içeride katlanmış eski bir parşömen! Kalbi hızla çarpıyor.
- ✋ Parşömen pürüzlü ve kırılgan, kenarları sararmış. Güneş ışığına tutunca semboller altın renkli parlıyor — bir harita!
- Haritada 5 işaret: her biri İstanbul'un farklı ışık yansımalarına karşılık geliyor.
- 🪝 HOOK: "Ama haritadaki ilk sembol kulenin tam karşısını gösteriyordu — aşağıda, dar sokaklarda bir yerde..."

### BÖLÜM 2 — Karaköy'de İpuçları (Sayfa 5-9) 🎯 Duygu: HEYECAN → hafif ENDİŞE
- {child_name} kuleden iniyor, dar Galata sokaklarına dalıyor. 🔊 Uzaktan martı çığlıkları, yakından kedi miyavlamaları.
- 👃 Hava taze simit ve deniz kokusuyla karışık. Parke taşlar ayağının altında ıslak ve kaygan.
- İlk işaret: eski bir çeşmenin pirinç aynasında yansıyan güneş ışığı. Ama ayna kırık — ışığı doğru yere yönlendirmesi gerekiyor!
- {child_name} elindeki parşömeni ayna gibi kullanıyor — yansıma gizli bir avlunun duvarını aydınlatıyor. İkinci sembol burada!
- "Yapıyorum... gerçekten yapıyorum!" diye fısıldıyor {child_name}, gözleri parlayarak.
- Balıkçılarla dolu Karaköy rıhtımı — 🔊 balıkçı teknelerinin halatları gıcırdıyor, dalga sesleri.
- Denizden yansıyan ışık üçüncü ipucunu gösteriyor ama tam o sırada büyük bir dalga parşömeni ıslatacak!
- {child_name} parşömeni göğsüne bastırıp geri sıçrıyor. Kalbi küt küt atıyor. Kıl payı kurtardı.
- 🪝 HOOK: "Parşömen her çözülen sembolle biraz daha renkleniyor... ama dördüncü işaret en kalabalık caddedeydi."

### BÖLÜM 3 — Beyoğlu'nda Kovalamaca (Sayfa 10-14) 🎯 Duygu: GERİLİM → KORKU → CESARET
- İstiklal Caddesi'nde kalabalık arasında ilerliyor. 🔊 Tramvay zili çalıyor — "Dıng dıng dıng!"
- Kırmızı tramvay geçerken camında anlık bir yansıma — dördüncü sembol! Ama tramvay hızla uzaklaşıyor.
- {child_name} kalabalığı yararak tramvayın arkasından koşuyor: "Dur! Durun!" Nefes nefese, bacakları ağrıyor.
- Tramvayın durduğu noktada sembolün izini buluyor — ama iz Tünel'e, karanlık yeraltı geçidine gidiyor.
- {child_name} girişte duruyor. Karanlık ve sessiz. Yutkunuyor. "Yapabilirim" diye mırıldanıyor, sesi titriyor.
- Derin bir nefes alıp adım atıyor. ✋ Soğuk taş duvarları avuçlarıyla hissediyor, karanlıkta ilerliyor.
- 🔊 Kendi ayak sesleri yankılanıyor, uzaktan belli belirsiz su damlama sesi.
- Eski duvardaki mozaiklerin arasında beşinci ve son ipucu! Parmakları dokunduğunda mozaik altın gibi parlıyor.
- Parşömen tamamen renkleniyor! Son mesaj beliriyor: "Geri dön. Cevap başladığın yerde."
- 🪝 HOOK: "Ama güneş batmak üzereydi — Kule'ye geri dönmek için çok az zamanı vardı..."

### BÖLÜM 4 — Kule'ye Dönüş (Sayfa 15-18) 🎯 Duygu: KARARLILIK → ŞAŞkınlık → KAVRAYIŞ
- {child_name} sokaklarda koşuyor, gölgeler uzuyor, gökyüzü turuncuya dönüyor.
- Galata Kulesi'ne geri tırmanıyor — bu sefer merdivenleri iki iki çıkıyor, artık nefes nefese değil, KARALI.
- Kulenin tepesinde parşömeni büyük pencereye tutuyor. Son ışık parşömenden geçiyor ve —
- Bütün İstanbul üzerinde devasa bir ışık haritası beliriyor! Her işaret bir tarihi öyküye karşılık: Ceneviz tacirleri, Osmanlı sanatkarları, Cumhuriyet'in yeni ışıkları.
- {child_name}'in ağzı açık kalıyor. Gözleri dolmak üzere — ama mutluluktan.
- 🔊 Akşam ezanı uzaktan yükseliyor, martılar son turlarını atıyor, hava tuzlu deniz kokuyor.

### BÖLÜM 5 — Kapanış (Sayfa 19-22) 🎯 Duygu: HUZUR → GURUR
- Gün batımında kuleden İstanbul manzarası — altın, kırmızı, mor ışıklar suyun üzerinde dans ediyor.
- Yaşlı fenerci gülümseyerek yaklaşıyor: "Haritayı buldun demek. Uzun zamandır biri bulsun diye bekliyordu."
- {child_name}: "Bunu ben mi saklayayım?" Fenerci başını sallıyor: "Ya da bir dahaki kaşif bulsun diye yerine koy."
- {child_name} parşömeni kulenin taşına geri saklıyor — gelecek kaşifler bulsun.
- Son basamağı inerken cebindeki eller sıcacık. Dudaklarında bir gülümseme. Şehir ışıklarla yanıyorken arkasına bakıyor.
- Bir dahaki macera belki başka bir çocuğu bekliyor — tam şimdi, kulenin tepesinde, taşların arasında.

---

## 🚫 KURALLAR
- Hayvan arkadaş / companion YOK. {child_name} macerayı TEK BAŞINA yaşıyor.
- Yaşlı fenerci sadece Sayfa 2-3 ve Sayfa 20'de görünür, kısa konuşur.
- Sihir/büyü YOK — optik illüzyonlar ve gerçek ışık yansımaları.
- Didaktik nasihat YASAK. Gezi rehberi formatı YASAK.
- DUYGU: amazed, smiling, determined, anxious, proud, curious.
- IŞIK odaklı atmosfer: golden hour, reflections, light beams, shadows, sunset.
- İlk sayfa [Sayfa 1] ile başla. Uçak/yolculuk sahnesi YOK.

## ⚠️ YAZIM KURALLARI

❌ YANLIŞ (Gezi Rehberi): "{child_name} Galata Kulesi'ni gördü. Kule 14. yüzyılda Cenevizliler tarafından yapılmıştır. Sonra Karaköy'e gitti."
✅ DOĞRU (Macera): "{child_name} taş duvardaki çatlağa parmaklarını soktu — içeride katlanmış eski bir parşömen!"

❌ YANLIŞ (Doğrudan Öğüt): "{child_name} cesaretin önemini anlamıştı. Bu macera ona çok şey öğretmişti."
✅ DOĞRU (Subliminal): "{child_name} derin bir nefes aldı ve karanlık geçide adım attı. Elleri artık titremiyordu."

## ⚠️ TUTARLILIK KURALLARI
🗝️ ÖNEMLİ OBJE: "Işık Haritası Parşömeni" = ancient folded parchment with light-reactive symbols. TÜM SAYFALARDA AYNI görünüm.
👗 KIYAFET: {clothing_description} tüm sayfalarda DEĞİŞMEZ.
👤 YAN ROL: Yaşlı fenerci = elderly man in brown leather apron, round spectacles. HER göründüğünde AYNI.

## 💬 DİYALOG KURALI
Her 3-4 sayfada en az 1 kısa diyalog olmalı. {child_name} kendi kendine konuşabilir (fısıltı, şaşkınlık). \
Yaşlı fenerci ile 2 kısa diyalog (S2-3 ve S20). Diyaloglar kısa, çocuk diline uygun.

Hikayeyi TAM OLARAK {page_count} sayfa yaz. Her sayfa 1-3 cümle (25-50 kelime).
""",

    # ── F: Görsel Prompt Şablonları (zenginleştirilmiş) ──
    cover_prompt_template=(
        'Story "{book_title}". A young child standing at the top of Galata Tower '
        'with Istanbul panorama behind, wearing {clothing_description}. {scene_description}. '
        'Galata Tower stone walls, Istanbul skyline with minarets and Bosphorus. '
        'Golden sunset light beams streaming through tower window, warm cinematic atmosphere. '
        'Dramatic hero shot, child in foreground 30%, city panorama 70%. '
        'Space for title at top.'
    ),
    page_prompt_template=(
        'A young child {scene_description}, wearing {clothing_description}. '
        'Setting elements (choose relevant based on scene): '
        'TOWER: [Galata Tower interior stone spiral staircase, medieval stone walls, '
        'panoramic windows with Istanbul view, old oil lanterns]. '
        'STREETS: [narrow Galata cobblestone streets, Ottoman-era stone buildings, '
        'old brass fountain, hidden courtyard with ivy walls]. '
        'HARBOR: [Karaköy fishing harbor, wooden boats, seagulls, Bosphorus waves, '
        'fishermen silhouettes]. '
        'AVENUE: [İstiklal Avenue crowd, red nostalgic tramway, ornate European buildings]. '
        'TUNNEL: [Tünel underground passage, old mosaic walls, dim lamplight, stone arch ceiling]. '
        'ATMOSPHERIC: [golden sunset light on stone, warm reflections on wet cobblestones, '
        'dramatic shadows in narrow streets, light beams through windows, '
        'silhouette against orange sky]. '
        'Shot variety: [close-up detail / medium action / wide panoramic / '
        'interior moody / low-angle hero / bird-eye Istanbul]. '
        'Composition: full body visible, warm palette (golden, amber, terracotta, deep blue). '
        'Text overlay space at bottom.'
    ),

    # ── G: Kıyafetler ──
    outfit_girl=(
        "soft lavender wool peacoat with silver buttons, cream cable-knit turtleneck sweater, "
        "dark navy pleated skirt, black patent leather ankle boots, "
        "a small vintage leather crossbody bag, and a lavender beret. "
        "EXACTLY the same outfit on every page."
    ),
    outfit_boy=(
        "camel-brown wool blazer with elbow patches, white button-down oxford shirt, "
        "dark navy chino trousers, brown leather chelsea boots, "
        "a small canvas messenger bag, and a brown flat cap. "
        "EXACTLY the same outfit on every page."
    ),

    # ── G2: Tutarlılık Kartları ──
    companions=[],  # No companion — child solo adventure
    objects=[
        ObjectAnchor(
            name_tr="Işık Haritası Parşömeni",
            appearance_en=(
                "ancient folded parchment map with light-reactive golden symbols "
                "that glow in sunlight, yellowed edges, palm-sized, fragile texture"
            ),
            prompt_suffix="holding ancient parchment with glowing light symbols — SAME on every page",
        ),
    ],

    # ── H: Kültürel Elementler ──
    cultural_elements={
        "primary": [
            "Galata Tower (14th century Genoese watchtower)",
            "Karaköy fishing harbor and brass fountains",
            "İstiklal Avenue and nostalgic red tramway",
            "Tünel (historic underground funicular, 1875)",
        ],
        "secondary": [
            "Old Genoese stone walls with carved symbols",
            "Bosphorus golden light reflections on water",
            "Istanbul sunset panorama from tower top",
            "Ottoman-era hidden courtyards with ivy walls",
            "Ancient mosaic walls in underground passages",
            "Traditional simit vendors and street cats",
            "Wet cobblestone reflections after rain",
            "Old brass oil lanterns in tower staircase",
        ],
        "colors": "warm golden, amber, terracotta, deep sunset orange, twilight purple",
        "atmosphere": "Mysterious, light-filled, urban solo adventure, cinematic Istanbul",
    },

    # ── C/G3: Lokasyon Kısıtları ──
    location_constraints=(
        "Pages 1-4: Galata Tower interior — spiral staircase, stone walls, top panoramic view. "
        "(Close-up climbing → Wide panoramic from top, golden morning light). "
        "Pages 5-9: Karaköy streets — narrow cobblestone alleys, old fountain, harbor dock. "
        "(Medium street-level shots, warm reflections, medium-wide harbor view). "
        "Pages 10-14: Beyoğlu — İstiklal Avenue crowd, tramway, Tünel underground dark passage. "
        "(Dynamic chase shots, low-angle Tünel interior, dramatic light/shadow contrast). "
        "Pages 15-18: Return to Galata Tower top — sunset light through window. "
        "(Wide panoramic, dramatic sunset backlighting, silhouette shots). "
        "Pages 19-22: Sunset farewell from tower — Istanbul skyline glowing. "
        "(Hero Shot golden hour, close-up emotional face, wide final panorama)."
    ),

    # ── I: Scenario Bible ──
    scenario_bible={
        "key_objects": [
            {
                "name_tr": "Işık Haritası Parşömeni",
                "appearance_en": (
                    "ancient folded parchment map with light-reactive golden symbols, "
                    "yellowed edges, palm-sized, fragile texture"
                ),
                "first_appear": 3,
                "last_appear": 21,
                "prompt_suffix": "holding ancient parchment with glowing light symbols — SAME on every page",
            },
        ],
        "side_characters": [
            {
                "name_tr": "Yaşlı Fenerci",
                "outfit_en": "elderly man in brown leather apron and white cotton shirt, round spectacles",
                "appears_on": [2, 3, 20],
                "role": "Mysterious lantern keeper who knows about the map",
            },
        ],
        "locations": [
            "Galata Tower stone spiral staircase with dim lantern light",
            "Tower top panoramic gallery with Istanbul view",
            "Narrow Galata cobblestone streets with cat silhouettes",
            "Old brass fountain with broken mirror in hidden courtyard",
            "Karaköy harbor dock with fishing boats and seagulls",
            "İstiklal Avenue with red tramway and crowd",
            "Tünel underground passage with ancient mosaic walls",
            "Galata Tower window at sunset with golden light beams",
        ],
        "no_companion": True,
        "child_solo": True,
    
        "consistency_rules": [
            "Companion appearance must remain IDENTICAL across all pages",
            "Child outfit must remain EXACTLY the same on every page",
            "Key objects maintain consistent appearance throughout",
        ],
    },

    # ── J: Custom Inputs — companion yok ──
    custom_inputs_schema=[],
))
