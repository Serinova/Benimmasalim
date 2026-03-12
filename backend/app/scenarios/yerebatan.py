"""Yerebatan'ın Kayıp Işığı — İstanbul yeraltı sarnıcı macerası.

TİP A: Tek Landmark (Yerebatan Sarnıcı + çevresi). Companion: Gizemli Sarnıç Kedisi (SABİT).
Objeler: Medusa Madalyonu, Antik Su Haritası
"""

from app.scenarios._base import CompanionAnchor, ObjectAnchor, ScenarioContent
from app.scenarios._registry import register

YEREBATAN = register(ScenarioContent(
    # ── A: Temel Kimlik ──
    theme_key="yerebatan",
    name="Yerebatan'ın Kayıp Işığı",

    # ── B: Teknik ──
    location_en="Basilica Cistern, Istanbul",
    default_page_count=22,
    flags={"no_family": True},

    # ── E: Hikaye Promptu (~750 kelime) ──
    story_prompt_tr="""\
# YEREBATAN'IN KAYIP IŞIĞI — İSTANBUL YERALTI MACERASI

## YAPI: {child_name} TEK BAŞINA, AİLE YOK. Yanında sadece Gölge (siyah-beyaz sarnıç kedisi, parlak yeşil gözlü).

**KRİTİK — METİN UZUNLUĞU:** Her sayfa 1-3 cümle, toplam 25-50 kelime. Kısa tut, sayfaya sığsın.

**KARAKTER:** {child_name} ({child_age} yaşında, {child_gender}). Yardımcı: Gölge — siyah-beyaz tüylü sarnıç kedisi, parlak yeşil gözler, sessiz patiler, zarif duruş. Her sayfada AYNI görünüm — DEĞİŞTİRME.

**KARAKTER ARC — İÇ YOLCULUK:**
{child_name} başta karanlık yeraltı mekanlarından ve sudan korkan, dar yerlerden tedirgin olan bir çocuk. \
Yerebatan'ın sütunları arasında ilerledikçe karanlığın aslında güzel, suyun aslında sakinleştirici olduğunu keşfediyor. \
Doruk noktasında Medusa başı'nın olduğu en derin bölümde su seviyesi yükselir — çıkış yolunu TEK BAŞINA bulmalı — Gölge karanlıkta görünmez olur. \
Hikayenin sonunda {child_name} artık karanlıktan korkmayan, sessizliği dinlemeyi bilen bir çocuk — ama bu DEĞİŞİM ASLA SÖYLENMEMELİ, sadece EYLEMLERİYLE hissettirilmeli.

**YASAK:** Anne, baba, aile, rehber YOK. Büyü/sihir YOK — suyun ve ışığın doğal oyunu. Korkunç yaratık, canavar YOK. Medusa "mitolojik heykel" olarak geçer, canlı değil.

---

### BÖLÜM 1 — Sarnıca İniş (Sayfa 1-4) 🎯 Duygu: MERAK + TEDİRGİNLİK
- {child_name} Sultanahmet'te eski bir binanın kapısından giriyor. Taş merdivenler aşağıya iniyor — her adımda hava serinliyor.
- 🔊 Su damlaları yankılanıyor, uzaktan hafif bir akıntı sesi. 👃 Nemli, serin, yosunlu taş kokusu. ✋ Duvar soğuk ve kaygan.
- Merdivenin sonunda devasa bir yeraltı mekanı açılıyor — yüzlerce sütun suyun üzerinde! Kırmızımsı ışıklar sütunlara yansıyor.
- {child_name} nefesini tutuyor. "Burası... bir saray gibi" fısıldıyor. Ayağının dibinden bir kedi süzülüyor — Gölge!
- Siyah-beyaz kedi yeşil gözlerle {child_name}'e bakıyor, sessizce sütunların arasına yürüyor — takip et der gibi.
- {child_name} yutkunuyor, kalbi hızlanıyor. Suya bakmamaya çalışıyor ama su her yerde — sütunların altında, ayaklarının kenarında.
- 🪝 HOOK: "Gölge bir sütunun arkasında kayboldu — ama tuhaf olan, sütunun üzerindeki semboller hafifçe parlıyordu..."

### BÖLÜM 2 — Sütunlar Arası (Sayfa 5-9) 🎯 Duygu: HEYECAN → KEŞİF COŞKUSU
- Sütunların arasında yürüyor — her biri farklı! Bazıları düz, bazıları oymalı, bazılarında kuş ve yaprak motifleri.
- 🔊 Her adımda su şıpırtısı, sütunlardan ters yansıyan kendi ayak sesleri. Gölge sessizce yanında, patileri ıslak taşta iz bırakmıyor.
- Bir sütunun tabanında hiyeroglif benzeri kazımalar — ama Bizans dönemi! Bir su haritası: sarnıcın gizli bölümlerini gösteren bir plan.
- "Bu bir harita!" diyor {child_name}, parmaklarıyla izlerken. ✋ Oyma derinlikleri pürüzlü, bazı bölümler su ile dolmuş.
- Haritada üç işaret: "gözyaşı sütunu", "ters Medusa başı" ve "kayıp ışık kaynağı."
- {child_name} gözyaşı sütununa doğru ilerliyor — sütunun gövdesinden sürekli su sızıyor, gözyaşı gibi! ✋ Dokunuyor — su ılık ve yumuşak.
- Suyun sızdığı yerden bir madalyon çıkıyor! Bronz, Medusa başı kabartmalı, ortasında yeşil bir taş.
- {child_name} madalyonu boynuna takıyor. Gölge onaylarcasına başını sallıyor — ya da belki sadece kendini temizliyordur.
- 🪝 HOOK: "Madalyon yeşil bir ışık saçmaya başladı — ve aynı renk ışık sarnıcın en derininden yanıt veriyordu..."

### BÖLÜM 3 — Medusa'nın Bölgesi (Sayfa 10-14) 🎯 Duygu: GERİLİM → KORKU → CESARET
- Sarnıcın en derin köşesine doğru ilerliyor — sütunlar sıklaşıyor, tavan alçalıyor, su derinleşiyor.
- 🔊 Kendi nefes sesi ve su damlaları — başka hiç ses yok. Gölge'nin yeşil gözleri karanlıkta iki küçük fener gibi parlıyor.
- İki devasa taş blok! Birinin üzerinde yan dönmüş, diğerinin üzerinde ters duran Medusa başı! Taştan ama yüz ifadeleri canlı gibi.
- {child_name} irkiliyor — ama bunlar sadece heykel, taşa kazınmış. "Korkma" diyor kendine, sesi yankılanıyor.
- Ters Medusa başının altında su seviyesi yükseliyor — yavaş yavaş! 🔊 Su gürültüsü artıyor, dalgacıklar ayak bileklerine ulaşıyor.
- Gölge karanlığa karışıyor — siyah-beyaz tüyleri gölgelerde görünmez oluyor! "Gölge!" diye sesleniyor {child_name}. Cevap yok.
- {child_name} yalnız, su yükseliyor. Derin nefes alıyor. Madalyonun yeşil ışığını yukarı tutuyor.
- Yeşil ışıkta duvardaki bir geçit beliriyor! Dar ama kuru. {child_name} kenara tırmanıp geçide sığınıyor.
- 🪝 HOOK: "Geçidin sonundaki ışık sıcak ve altın rengiydi — sarnıcın bilinen bölümlerinden değildi bu..."

### BÖLÜM 4 — Kayıp Işık Kaynağı (Sayfa 15-18) 🎯 Duygu: ŞAŞKınlık → HAYRANLIK
- Geçitten küçük bir gizli odaya giriyor — tavan yüksek, duvarlarda Bizans mozaikleri! Altın, mavi, kırmızı tesseralar ışıldıyor.
- Odanın ortasında eski bir mermer çeşme — çeşmenin ortasında cam bir lamba yuvası. Madalyon tam yuvaya uyuyor!
- {child_name} madalyonu yerleştirince yeşil ışık mozaiklerden yansıyor — tüm oda canlı bir resim gibi parlıyor!
- Mozaiklerde İstanbul'un hikayesi: balıkçılar, gemiler, kubbeler, at arabaları — yüzyıllar önce şehrin kalbinde.
- 👃 Hava serin ve temiz — yeraltı pınarının taze suyu. 🔊 Çeşmeden hafif bir su melodisi yükseliyor.
- {child_name}'in gözleri parlıyor. "Burası... şehrin hafızası" fısıldıyor. Gölge sessizce yanına geliyor, patisiyle dizine dokunuyor.
- Mozaikler yavaşça kararıyor — ışık azalıyor ama {child_name}'in kalbinde sıcaklık kalıyor.

### BÖLÜM 5 — Yüzeye Çıkış (Sayfa 19-22) 🎯 Duygu: HUZUR → GURUR
- Madalyonu yuvadan çıkarıp boynuna geri takıyor — hatıra olarak.
- Geçitten geri dönüş — su çekilmiş! Medusa başları sakin ve sessiz. {child_name} bu sefer duraksıyor ve bakıyor — korkmuyor.
- Sütunların arasından çıkış merdivenleri — yukarıya doğru, ışığa doğru. Gölge önden gidiyor, kuyruğu havada.
- 🔊 Kapıdan çıkınca Sultanahmet'in sesi: martılar, tramvay, çocuk kahkahaları, ezan sesi uzaktan.
- Güneş! Yüzünü yalıyor, sıcak ve parlak. {child_name} gözlerini kısıyor ve gülümsüyor. Yeraltından yüzeye çıkmanın güzelliği.
- Gölge Sultanahmet Meydanı'na doğru yürüyor, bir kez dönüp bakıyor — yeşil gözler son kez parlıyor.
- {child_name} madalyona dokunuyor — hâlâ hafif ılık. Sarnıcın kapısına bakıyor.
- "Sultanahmet'i dolduran güneşin altında, kimse bilmiyordu — birkaç metre aşağıda, yüzlerce sütun hâlâ fısıldıyordu..."

---

## 🚫 KURALLAR
- AİLE/YETİŞKİN/REHBER YOK. Sahnelerde sadece {child_name} + Gölge (kedi).
- Büyü/sihir YOK — su ve ışık doğal.
- Medusa = tarihi taş heykel, canlı değil, korkunç yapma.
- Gölge her sayfada AYNI görünüm — siyah-beyaz tüy, yeşil gözler — DEĞİŞMEZ.
- Medusa Madalyonu bulunduktan sonra her sayfada görünmeli — AYNI bronz+yeşil taş.
- İlk sayfa [Sayfa 1] ile başla.

## ⚠️ YAZIM KURALLARI

❌ YANLIŞ (Gezi Rehberi): "{child_name} Yerebatan Sarnıcı'nı gördü. Sarnıç 532 yılında Justinianus tarafından yaptırılmıştır."
✅ DOĞRU (Macera): "Merdivenin sonunda devasa bir yeraltı mekanı açıldı — yüzlerce sütun suyun üzerinde yükseliyordu!"

❌ YANLIŞ (Doğrudan Öğüt): "{child_name} karanlıktan korkmaması gerektiğini öğrendi."
✅ DOĞRU (Subliminal): "{child_name} Medusa başlarına baktı — bu sefer korkmuyor, sadece taşın güzelliğini görüyordu."

## 💬 DİYALOG KURALI
Her 3-4 sayfada en az 1 kısa diyalog. {child_name} Gölge'ye veya kendine konuşur. Gölge sessiz — patisiyle dokunarak, yeşil gözleriyle bakarak, süzülerek tepki verir.

## ⛔ İÇERİK YASAKLARI
- Anne, baba, aile YASAK (no_family)
- Korkunç yaratık, canavar YASAK
- Gezi rehberi formatı YASAK
- Medusa'yı korkunç/canlı gösterme YASAK

Hikayeyi TAM OLARAK {page_count} sayfa yaz. Her sayfa 1-3 cümle (25-50 kelime).
""",

    # ── F: Görsel Prompt Şablonları ──
    cover_prompt_template=(
        'Story "{book_title}". A young child standing among the illuminated columns '
        'of the Basilica Cistern, wearing {clothing_description}. {scene_description}. '
        'A black and white cat with bright green eyes sitting at the child\'s feet. '
        'Hundreds of ancient stone columns rising from shallow water, '
        'warm reddish-golden spotlights reflecting on water surface, '
        'mysterious underground atmosphere. '
        'Cinematic wide shot, child 25%, columns and water 75%. '
        'Space for title at top. {STYLE}'
    ),
    page_prompt_template=(
        'A young child {scene_description}, wearing {clothing_description}. '
        'Setting elements (choose relevant based on scene): '
        'ENTRANCE: [stone staircase descending underground, cool damp air, '
        'dim amber lighting, ancient stone walls with moisture]. '
        'COLUMN HALL: [hundreds of ancient stone columns from water, '
        'warm reddish spotlights reflecting on still water surface, '
        'Corinthian and Doric capitals, carved bird and leaf motifs]. '
        'MEDUSA AREA: [two massive Medusa head stone blocks as column bases, '
        'one sideways one upside down, deeper water, darker atmosphere, '
        'dramatic green-amber lighting]. '
        'HIDDEN CHAMBER: [small Byzantine mosaic room with golden-blue tesserae, '
        'marble fountain with lamp niche, green light from medallion, '
        'ancient city scenes in mosaic]. '
        'SURFACE: [Sultanahmet Square exterior, bright sunlight, blue mosque silhouette, '
        'seagulls, old cobblestones, transition from dark underground to bright day]. '
        'Shot variety: [close-up column detail / medium action / wide underground panoramic / '
        'low-angle dramatic / intimate mosaic room / bright exit contrast]. '
        'Composition: full body visible, cistern palette (warm amber, deep shadow, '
        'reddish gold, mossy green, Byzantine gold-blue). '
        'Text overlay space at bottom. {STYLE}'
    ),

    # ── G: Kıyafetler ──
    outfit_girl=(
        "burgundy corduroy pinafore dress over a cream turtleneck sweater, "
        "dark brown leather lace-up boots, a small vintage leather satchel, "
        "a thin burgundy headband with small bronze clasp. "
        "EXACTLY the same outfit on every page."
    ),
    outfit_boy=(
        "dark green corduroy jacket with brass buttons over a cream cable-knit sweater, "
        "dark navy trousers, brown leather lace-up boots, "
        "a small canvas messenger bag with bronze buckle. "
        "EXACTLY the same outfit on every page."
    ),

    # ── G2: Tutarlılık Kartları ──
    companions=[
        CompanionAnchor(
            name_tr="Gizemli Sarnıç Kedisi",
            name_en="mysterious black and white cat with bright green eyes",
            species="cat",
            appearance=(
                "elegant black and white tuxedo cat with bright emerald green eyes, "
                "silent soft paws, graceful posture, small and agile"
            ),
            short_name="Gölge",
        ),
    ],
    objects=[
        ObjectAnchor(
            name_tr="Medusa Madalyonu",
            appearance_en=(
                "bronze medallion with Medusa head relief carving, "
                "glowing green gemstone in center, on thin bronze chain, palm-sized"
            ),
            prompt_suffix=(
                "wearing bronze Medusa medallion with green gemstone on chain "
                "— SAME appearance on every page"
            ),
        ),
        ObjectAnchor(
            name_tr="Antik Su Haritası",
            appearance_en=(
                "carved Byzantine-era stone relief on column base showing "
                "cistern floor plan with water channels and marked locations"
            ),
            prompt_suffix=(
                "near carved stone cistern map with Byzantine markings "
                "— SAME appearance on every page"
            ),
        ),
    ],

    # ── H: Kültürel Elementler ──
    cultural_elements={
        "primary": [
            "Basilica Cistern with 336 marble columns from water",
            "Two Medusa head stone blocks as column bases (sideways and upside-down)",
            "Gözyaşı (Weeping) column with constant water seepage",
            "Byzantine mosaic art with golden tesserae",
            "Underground water reservoir engineering of 6th century",
        ],
        "secondary": [
            "Corinthian and Doric column capitals with carved motifs",
            "Warm reddish spotlight reflections on still water surface",
            "Roman-era carved fish and peacock motifs on columns",
            "Ancient marble fountain niche in hidden chamber",
            "Sultanahmet Square above ground contrast with underground mystery",
            "Stray cats of Istanbul as living guardians of historic sites",
        ],
        "colors": "warm amber, deep shadow, reddish gold, mossy green, Byzantine gold-blue, emerald green",
        "atmosphere": "Underground, mysterious, water reflections, Ottoman/Byzantine, silent and ancient",
    },

    # ── C/G3: Lokasyon Kısıtları ──
    location_constraints=(
        "Pages 1-4: Cistern entrance and descent — stone stairs, first view of "
        "massive column hall, cat appearance (Wide Shot, dramatic reveal). "
        "Pages 5-9: Column hall exploration — different column styles, water map discovery, "
        "weeping column, medallion discovery (Medium Shot + Close-up detail). "
        "Pages 10-14: Medusa area — deeper section, darker, rising water, "
        "two Medusa head blocks, child alone, escape through hidden passage "
        "(Close-up dramatic, dark atmosphere, green light). "
        "Pages 15-18: Hidden Byzantine mosaic room — small chamber with golden mosaics, "
        "marble fountain, medallion placement, city history reveal "
        "(Wide interior, warm golden-green glow). "
        "Pages 19-22: Return to surface — water receded, calm cistern, stair ascent, "
        "bright Sultanahmet exit, farewell (Contrast dark→light, Hero Shot, warm)."
    ),

    # ── I: Scenario Bible ──
    scenario_bible={
        "companion": {
            "name": "Gölge (Gizemli Sarnıç Kedisi)",
            "personality": (
                "Sessiz, zarif, gizemli bir kedi. Konuşmaz, miyavlamaz — sadece patisiyle "
                "dokunur, yeşil gözleriyle bakar, süzülerek yol gösterir. Medusa bölgesinde "
                "karanlığa karışıp KAYBOLUR — çocuk tek başına kalır. Aniden tekrar "
                "belirir — sanki hep oradaymış gibi."
            ),
            "role": "Sessiz yol gösterici, ama kriz anında kayıp",
            "visual_lock": (
                "Black and white tuxedo cat, bright emerald green eyes, "
                "silent soft paws — EVERY PAGE SAME"
            ),
        },
        "key_objects": {
            "madalyon": {
                "name": "Medusa Madalyonu",
                "description": (
                    "Gözyaşı sütunundan çıkan bronz madalyon. Medusa başı kabartmalı, "
                    "ortasında yeşil taş. Gizli mozaik odasının lamba yuvasına uyuyor."
                ),
                "first_appear": "Sayfa 8-9",
                "visual_lock": "Bronze Medusa medallion with green gemstone on chain — SAME on every page",
            },
            "harita": {
                "name": "Antik Su Haritası",
                "description": (
                    "Bir sütunun tabanında kazınmış Bizans dönemi sarnıç planı. "
                    "Üç önemli noktayı işaretler: gözyaşı sütunu, Medusa başları, kayıp ışık kaynağı."
                ),
                "first_appear": "Sayfa 6-7",
                "visual_lock": "Carved stone cistern floor plan — SAME on every page",
            },
        },
        "zones": {
            "entrance": "Geçiş, iniş, serin — taş merdivenler, damla sesleri, nem",
            "column_hall": "Görkemli, gizemli, yansımalar — yüzlerce sütun, kırmızımsı ışıklar, durgun su",
            "medusa_area": "Karanlık, gerilimli, derin — devasa taş başlar, yükselen su, yalnızlık",
            "hidden_chamber": "Sıcak, altın, büyüleyici — Bizans mozaikleri, mermer çeşme, yeşil ışık",
            "surface": "Parlak, sıcak, kontrast — Sultanahmet güneşi, martılar, şehir sesleri",
        },
        "emotional_arc": {
            "S1-S4": "Merak + tedirginlik (yeraltına iniş, devasa mekan, su korkusu)",
            "S5-S9": "Heyecan + keşif coşkusu (sütunlar, su haritası, gözyaşı sütunu, madalyon)",
            "S10-S14": "Gerilim → korku → cesaret (Medusa bölgesi, su yükseliyor, Gölge kayıp, kaçış)",
            "S15-S18": "Şaşkınlık + hayranlık (gizli mozaik odası, şehrin hafızası)",
            "S19-S22": "Huzur + gurur (yüzeye çıkış, güneş, karanlık korkusu geçmiş)",
        },
        "consistency_rules": [
            "Gölge (kedi) HER sayfada aynı siyah-beyaz tüy + yeşil göz görünüm",
            "Medusa Madalyonu bulunduktan sonra HER sayfada boyunda aynı bronz tasarım",
            "Sarnıç içinde ışık KIZIMSZ-AMBER, gizli odada YEŞİL-ALTIN",
            "Medusa başları sadece taş heykel — korkutucu yapma, tarihi anlatım",
            "Yeraltından yüzeye geçişte karanlık → aydınlık kontrast",
            "Çocuğun kıyafeti TÜM SAYFALARDA birebir aynı",
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
            "default": "Gizemli Sarnıç Kedisi",
        },
    ],
))
