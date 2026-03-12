"""Dinozorlar Alemi: Kayıp Yuva — Prehistorik dünya macerası.

TİP C: Fantastik (zaman yolculuğu + prehistorik dünya keşfi).
Companion: Minik Bebek Dinozor (SABİT — kullanıcıya seçtirilmez)
Obje: Parıldayan Kehribar Fosil
"""

from app.scenarios._base import CompanionAnchor, ObjectAnchor, ScenarioContent
from app.scenarios._registry import register

DINOSAUR = register(ScenarioContent(
    # ── A: Temel Kimlik ──
    theme_key="dinosaur",
    name="Dinozorlar Alemi: Kayıp Yuva",

    # ── B: Teknik ──
    location_en="Prehistoric World",
    default_page_count=22,
    flags={"no_family": True},

    # ── E: Hikaye Promptu (iyileştirilmiş — ~850 kelime) ──
    story_prompt_tr="""\
# DİNOZORLAR ALEMİ: KAYIP YUVA — TARİH ÖNCESİ MACERA

## YAPI: {child_name} bir doğa tarihi müzesinde parıldayan bir kehribar fosile dokunuyor ve 66 milyon yıl öncesine ışınlanıyor. Yanında {animal_friend} ile prehistorik dünyayı keşfediyor, kayıp bir bebek dinozoru yuvasına kavuşturuyor ve fosili geri koyarak bugüne dönüyor. Bilimsel hayranlık ve doğa sevgisi odaklı — korkunç değil, büyüleyici.

**BAŞLIK:** "[Çocuk adı]'ın Dinozor Macerası"

**KRİTİK — METİN UZUNLUĞU:** Her sayfa 2-4 cümle, toplam 30-55 kelime. Kısa tut, sayfaya sığsın.

**KARAKTER:** {child_name} ({child_age} yaşında, {child_gender}). Yardımcı: {animal_friend} (her sayfada aynı görünüm — DEĞİŞTİRME).

**KARAKTER ARC — İÇ YOLCULUK:**
{child_name} başta doğaya karşı biraz kayıtsız bir çocuk — müzeyi sıkıcı buluyor, fosillere "sadece taş" gözüyle bakıyor.
Prehistorik dünyaya geçince doğanın büyüklüğü karşısında önce küçülüyor, ürküyor.
Macera boyunca adım adım doğayla bağ kurar: önce {animal_friend}'ın cesaretlendirmesiyle, sonra KENDİ KARARIYLA.
Hikayenin sonunda {child_name} müzedeki fosillere artık "sadece taş" olarak bakmıyor — gözleri hayranlıkla parlıyor. Ama bu DEĞİŞİM ASLA SÖYLENMELİ, sadece EYLEMLERİYLE hissettirilmeli.

**YASAK:** Anne, baba, aile üyesi, yetişkin YOK. "NO ADULTS" kuralı: sahnelerde sadece çocuk + {animal_friend}. Kanlı/korkunç dinozor sahnesi YOK. T-Rex bile hayranlık uyandırıcı — tehdit değil.

**AKIŞ (6 BÖLÜM):**

### BÖLÜM 1 — Müzede Keşif (Sayfa 1-3) 🎯 Duygu: SIKINTI → MERAK
- {child_name} bir doğa tarihi müzesinde, sıkılmış yüzüyle dinozor iskeletlerine bakıyor. "Bunlar sadece eski kemikler" diye düşünüyor. {animal_friend} çantasından kafasını çıkarıp merakla etrafa bakınıyor.
- 🔊 Müzenin sessizliğinde ayak sesleri yankılanıyor. Havada eski ahşap ve toz kokusu. Bir vitrin dikkatini çekiyor — içinde kehribar renkli bir fosil var ve garip bir ışık saçıyor.
- {child_name} cama yaklaşıyor; fosil PARILDIYIYOR. "Bu normal değil..." diye fısıldıyor. {animal_friend} heyecanla sıçrayıp vitrine yaklaşıyor. {child_name} elini uzatıp dokunuyor — parmakları kehribara değdiğinde IŞIK SELİ! Etraf bulanıklaşıyor...
🪝 HOOK: Ayağının altındaki mermer zemin birden nemli toprağa dönüştü...

---

### BÖLÜM 2 — Prehistorik Dünyaya Geçiş (Sayfa 4-7) 🎯 Duygu: ŞAŞKINLIK → hafif KORKU
- VIIIZ! Gözlerini açtığında HER ŞEY DEĞİŞMİŞ. Devasa eğrelti otları, ağaç tepelerine uzanan kozalaklı çamlar, sıcak nemli hava. 🔊 Böcek vızıltıları, uzaktan kuş çığlıkları — ama bunlar tanıdık kuşlar değil. Hava baharatlı, ıslak toprak ve çürüyen yaprak kokuyor.
- {child_name} bir an donakalıyor — "Neredeyiz?" Sesi titriyor. {animal_friend} yanına sokulup bacağına yaslanıyor, cesaretlendirmek ister gibi. "Tamam, korkma. Birlikte çözeriz" diye fısıldıyor ama elleri titriyor.
- Devasa bir Diplodocus sürüsü uzakta — boyunları ağaç tepelerini aşıyor! {child_name}'in ağzı açık kalıyor. "İnanılmaz... Gerçek dinozorlar!" 🔊 Yeri titreten adım sesleri, yaprakların hışırtısı.
- {animal_friend} merakla bir eğrelti otunun altına dalıp koşuyor — {child_name}'i de peşinden sürüklüyor.
🪝 HOOK: Ama eğreltilerin arasından küçük, acı acı çığlıklar geliyordu...

---

### BÖLÜM 3 — Kayıp Yuva (Sayfa 8-11) 🎯 Duygu: EMPATİ → KARARLILIK
- Çığlıkların kaynağını buluyorlar: küçük bir bebek Triceratops, devrilmiş bir kütüğün altında sıkışmış! Gözleri kocaman ve korkudan titriyor. "Aman! Yardım etmeliyiz!" diyor {child_name}, bu sefer SESİ TİTREMİYOR.
- Kütük çok ağır — {child_name} var gücüyle itiyor ama kımıldamıyor. {animal_friend} bir dal bulup kaldıraç olarak kullanmayı gösteriyor! {child_name}: "Dahisin sen!" Dalı kütüğün altına yerleştirip bastırıyor — kütük devrildi!
- Bebek Triceratops kurtulunca {child_name}'e yaklaşıp burnunu eline sürtüyor. "Yuvan nerede küçük?" {animal_friend} yerde izler fark ediyor — büyük Triceratops ayak izleri! Sürünün yolu.
- 🔊 Uzaktan gök gürültüsü — ama bu yıldırım değil. Uzaktaki volkan hafif duman çıkarıyor. "Acele etmeliyiz" diyor {child_name}, bebek dinozorun yanında yürümeye başlıyor.
🪝 HOOK: Ama izler bir nehir kıyısına gelince kesiliyordu...

---

### BÖLÜM 4 — T-Rex Karşılaşması (Sayfa 12-15) 🎯 Duygu: GERİLİM → CESARET → RAHATLA
- Nehir kıyısında izleri arıyorlar. 🔊 Yaprak yiyen bir Stegosaurus nehrin öbür tarafında — zırhlı sırtı güneşte parlıyor. Pteranodon'lar gökyüzünde süzülüyorlar, kanatları rüzgarı kesiyor.
- Birden YER TİTRİYOR. Ağır adım sesleri! Dev bir gölge ağaçların arasından beliriyor — T-REX! {child_name} donup kalıyor, yutkunuyor. {animal_friend} çırpınarak çantaya sığınıyor.
- Ama T-Rex onlara bakmıyor bile — nehirden su içiyor! Devasa başı suya eğilirken güneş ışığı pullu derisinde parlıyor. {child_name} derin nefes alıyor: "Korkma, bize ilgilenmiyor. Sadece susuz." Sessizce, eğrelti otlarının arasından GİZLENEREK geçiyorlar — {child_name} bebek dinozorun ağzını eliyle kapatıyor.
- T-Rex başını kaldırıp burnunu havaya diktiğinde... nefeslerini TUTUYORLAR. Kalp atışları kulaklarında. Sonra T-Rex dönüp ormana dalıyor. {child_name}: "Gittiii..." diye fısıldıyor, bacakları titreyerek ama GÜLÜMSEYEREK. {animal_friend} çantadan başını çıkarıp utangaçça bakıyor.
🪝 HOOK: Volkan biraz daha yakından duman çıkarıyordu ve hava ısınmaya başlamıştı...

---

### BÖLÜM 5 — Yuva Bulunuyor (Sayfa 16-19) 🎯 Duygu: HEYECAN → SEVİNÇ → ACELECİLİK
- Nehri geçtikten sonra izler tekrar beliriyor — daha taze! Bebek Triceratops heyecanla koşmaya başlıyor, {child_name} peşinden. {animal_friend} ağaç dallarından sıçrayarak yol gösteriyor.
- 🔊 Uzaktan boğuk böğürme sesleri — Triceratops sürüsü! Açık bir ovada, dev eğrelti otlarının arasında anne Triceratops ve sürüsü! Bebek dinozor çığlık atarak annesine koşuyor. Anne Triceratops başını eğip bebeğini burnuyla itiyor — KAVUŞTULAR!
- {child_name}'in gözleri doluyor ama gülümsüyor. "Evine döndün küçük" diye fısıldıyor. {animal_friend} çocuğun omzuna çıkıp başını yanağına yasıyor. Sürü çevresinde topraktan toz bulutları kalkıyor, 🔊 memnun böğürmeler yankılanıyor.
- Volkan daha aktif — lav parıltıları gökyüzünü turuncu boyuyor. Kehribar fosil CEBİNDE ISINIYOR! "Dönüş zamanı!" diyor {child_name}. {animal_friend} ile fosili parıldayan bir kaya platformuna koyuyorlar. Etraf ışıkla dolmaya başlıyor...
🪝 HOOK: Işık her yanı sardığında {child_name}'in ayaklarının altında yine mermer zemin belirdi...

---

### BÖLÜM 6 — Müzeye Dönüş (Sayfa 20-22) 🎯 Duygu: ŞAŞkınlık → HUZUR + GURUR
- Müzeye geri dönüş — her şey normal, dinozor iskeleti yerli yerinde. 🔊 Müzenin sessizliği, uzaktan ziyaretçi sesleri. Ama avucunda küçük bir trilobit fosili var — sıcacık, gerçek!
- {child_name} vitrindeki kehribar fosile bakıyor — artık parıldamıyor. Sonra dev Diplodocus iskeletine yürüyor, iskeleti BAŞTAN SONA inceliyor. Parmağıyla bilgi tabelasını okuyor. Gözleri parlıyor. "Bunların bir zamanlar GERÇEKTEN yaşadığını biliyorum artık" diye fısıldıyor. Ama SÖYLEMİYOR bunu — sadece GÜLÜMSÜYOR.
- Son sahne: {child_name} müzeden çıkarken güneş ışığı yüzüne vuruyor. {animal_friend} omzunda, avucundaki trilobit fosili sıcacık parlıyor. Cebine koyup gülümsüyor. "Bir dahaki sefer nereye gideriz acaba?" diye fısıldıyor {animal_friend}'a. Adımları artık daha kararlı, gözlerinde meraklı bir ışık var.

---

## 🚫 KURALLAR
- AİLE/YETİŞKİN YOK. Sahnelerde sadece {child_name} + {animal_friend} + dinozorlar.
- Büyü/sihir YOK. Fosil doğal bir zaman anomalisi.
- {animal_friend} her sayfada AYNI görünüm — renk, boyut, boynuz, göz DEĞİŞMEZ.
- Kehribar fosil bulunduktan sonraki her sayfada görünmeli — AYNI tasarım.
- Korkunç/kanlı dinozor sahneleri YASAK. T-Rex bile "hayranlık uyandıran" — tehdit değil.
- Kıyafet zaman yolculuğunda bile DEĞİŞMEZ.

## ⚠️ YAZIM KURALLARI

❌ YANLIŞ (Gezi Rehberi): "{child_name} Diplodocus'u gördü. Diplodocus 27 metre uzunluğunda otçul bir dinozordur. Sonra Stegosaurus'u gördü."
✅ DOĞRU (Macera): "{child_name}'in ayağının altındaki toprak titredi — dev bir gölge ağaçların arasından belirdi!"

❌ YANLIŞ (Doğrudan Öğüt): "{child_name} doğanın ne kadar güzel olduğunu anlamıştı. Bu macera ona çok şey öğretmişti."
✅ DOĞRU (Subliminal): "{child_name} dev iskeletin altında durdu. Parmağı bilgi tabelasının üzerinde geziniyor, gözleri parlıyordu."

## 💬 DİYALOG KURALI
Her 3-4 sayfada en az 1-2 kısa diyalog. {child_name} ile {animal_friend} arasında jest, ses, bakış üzerinden iletişim. Companion konuşamaz ama çocuk ona konuşur ve hayvan tepki verir.

Hikayeyi TAM OLARAK {page_count} sayfa yaz. Her sayfa 2-4 cümle (30-55 kelime), akıcı ve macera dolu.
""",

    # ── F: Görsel Prompt Şablonları (iyileştirilmiş) ──
    cover_prompt_template=(
        'Story "{book_title}". A young child standing heroically before a massive friendly '
        'Diplodocus dinosaur in a lush prehistoric jungle, wearing {clothing_description}. '
        '{scene_description}. Towering prehistoric ferns and conifers, an erupting volcano '
        'glowing orange in the far distance, warm dramatic golden-hour light. '
        'Epic cinematic low-angle hero shot: child and baby dinosaur companion in foreground 30%, '
        'prehistoric landscape filling background 70%. '
        'Color palette: amber, forest green, volcanic orange, warm gold. '
        'Space for title at top. {STYLE}'
    ),
    page_prompt_template=(
        'A young child {scene_description}, wearing {clothing_description}. '
        'Setting elements (choose relevant based on scene): '
        'MUSEUM: [natural history museum hall with dinosaur skeletons, glass display cases, '
        'marble floor, warm overhead lighting, fossil exhibits]. '
        'EXTERIOR PREHISTORIC: [giant prehistoric ferns, towering conifers, volcanic mountains, '
        'warm humid atmosphere with mist, rivers, open plains with grazing dinosaurs]. '
        'DINOSAURS: [friendly Diplodocus herd with long necks, baby Triceratops with big eyes, '
        'Pteranodon soaring in sky, Stegosaurus at river, T-Rex silhouette in trees]. '
        'DRAMATIC: [volcanic eruption glow, lava rivers in distance, dark dense primordial forest, '
        'amber light through giant fern canopy]. '
        'ATMOSPHERIC: [warm prehistoric mist, golden light filtering through ferns, '
        'volcanic ash glow on horizon, dust particles in sunbeams, humid tropical air]. '
        'Shot variety: [close-up detail / medium action / wide epic / dramatic low-angle / aerial]. '
        'Composition: full body visible in action, warm prehistoric palette '
        '(amber, forest green, volcanic orange, warm gold). '
        'Text overlay space at bottom. {STYLE}'
    ),

    # ── G: Kıyafetler ──
    outfit_girl=(
        "warm amber-brown leather explorer vest over a cream long-sleeve cotton T-shirt, "
        "olive-brown cargo pants with reinforced knee patches, sturdy brown hiking boots "
        "with thick soles, a wide-brim khaki adventure hat with a small dinosaur pin, "
        "small canvas satchel across body. "
        "EXACTLY the same outfit on every page."
    ),
    outfit_boy=(
        "tan khaki explorer shirt with rolled sleeves and chest pocket, "
        "dark brown cargo shorts with side pockets, "
        "sturdy brown leather hiking boots with thick soles, "
        "a khaki baseball cap with a small dinosaur pin, "
        "small brown leather backpack with brass buckles. "
        "EXACTLY the same outfit on every page."
    ),

    # ── G2: Tutarlılık Kartları ──
    companions=[
        CompanionAnchor(
            name_tr="Minik Bebek Dinozor",
            name_en="tiny friendly baby triceratops",
            species="baby dinosaur",
            appearance=(
                "tiny friendly light green baby triceratops with big curious brown eyes, "
                "small rounded horns, a cream-colored frill, and stubby legs"
            ),
            short_name="Bebek Dino",
        ),
    ],
    objects=[
        ObjectAnchor(
            name_tr="Kehribar Fosil",
            appearance_en=(
                "ancient glowing amber fossil with a preserved trilobite inside, "
                "palm-sized, warm golden glow, teardrop shape"
            ),
            prompt_suffix=(
                "holding glowing amber fossil with trilobite inside — "
                "SAME appearance on every page"
            ),
        ),
    ],

    # ── H: Kültürel Elementler ──
    cultural_elements={
        "primary": [
            "Natural history museum with dinosaur skeletons and fossil exhibits",
            "Diplodocus herd — long-necked herbivores, necks reaching treetops",
            "Baby Triceratops lost from herd — big eyes, small horns, scared",
            "T-Rex encounter at river — massive but not threatening, drinking water",
            "Active volcano with lava glow in distance — urgency driver",
        ],
        "secondary": [
            "Pteranodon sky patrol — soaring on thermals above prehistoric forest",
            "Stegosaurus at river — armored plates gleaming in sun",
            "Giant prehistoric ferns and conifers — towering canopy",
            "Trilobite fossils — ancient sea creatures preserved in stone",
            "Triceratops mother-baby reunion — emotional payoff",
        ],
        "colors": "warm prehistoric palette — amber, forest green, volcanic orange, warm gold",
        "atmosphere": "Awe-inspiring, prehistoric, adventurous, warm, scientifically grounded",
        "values": ["Empathy", "Courage", "Nature appreciation", "Problem-solving"],
    },

    # ── C/G3: Lokasyon Kısıtları ──
    location_constraints=(
        "Pages 1-3: Natural history museum interior — dinosaur skeletons, glass cases, warm light. "
        "(Medium Shot, warm indoor lighting, reflections on marble floor) "
        "Pages 4-7: Transition to prehistoric world — giant ferns, humid mist, Diplodocus herd. "
        "(Wide Shot, lush green, golden mist, epic scale) "
        "Pages 8-11: Dense fern forest — baby Triceratops rescue, following tracks. "
        "(Close-up emotional, medium action, warm forest floor light) "
        "Pages 12-15: River crossing, T-Rex encounter — tense hiding in ferns. "
        "(Dramatic low-angle, T-Rex silhouette, warm amber light through canopy) "
        "Pages 16-19: Open plains — Triceratops herd reunion, volcano active in background. "
        "(Wide panoramic, warm golden/orange, emotional medium shots) "
        "Pages 20-22: Museum return — sunset light through windows, warm nostalgic glow. "
        "(Medium Shot, warm golden, hero shot at exit)"
    ),

    # ── I: Scenario Bible ──
    scenario_bible={
        "companion_pack": {
            "minik_bebek_dinozor": {
                "species": "baby dinosaur",
                "appearance_en": (
                    "tiny friendly light green baby triceratops with big curious brown eyes, "
                    "small rounded horns, a cream-colored frill, and stubby legs"
                ),
                "role": (
                    "Çocuğun macera arkadaşı — meraklı, bazen tökezleyen, "
                    "böceklerden korkan ama cesur bebek dinozor. "
                    "Tehlike anında çocuğun çantasına/bacağına sığınır."
                ),
            },
        },
        "key_objects": {
            "kehribar_fosil": {
                "appearance_en": (
                    "ancient glowing amber fossil with preserved trilobite inside, "
                    "palm-sized, warm golden glow, teardrop shape"
                ),
                "first_page": 3,
                "last_page": 21,
                "prompt_suffix": (
                    "holding glowing amber fossil with trilobite — "
                    "SAME on every page"
                ),
            },
        },
        "side_characters": {
            "bebek_triceratops_kayip": {
                "outfit_en": (
                    "small scared baby Triceratops with green-brown skin, "
                    "tiny horns, big frightened eyes"
                ),
                "appears_on": [8, 9, 10, 11, 16, 17, 18],
                "rule": "SAME appearance on every page — NOT the companion",
            },
            "anne_triceratops": {
                "outfit_en": (
                    "large adult Triceratops with dark green-brown skin, "
                    "large curved horns, protective posture"
                ),
                "appears_on": [17, 18],
                "rule": "SAME appearance on every page",
            },
        },
        "location_zone_map": {
            "museum": "pages 1-3, 20-22",
            "prehistoric_forest": "pages 4-11",
            "river_trex": "pages 12-15",
            "open_plains_volcano": "pages 16-19",
        },
        "consistency_rules": [
            "Baby dinosaur companion MUST have EXACTLY the same light green skin, "
            "brown eyes, small horns, and cream frill on EVERY page",
            "Amber fossil MUST have the same golden glow and teardrop shape on pages 3-21",
            "Child's explorer outfit MUST NOT change between time periods",
            "T-Rex is NOT threatening — drinking water, ignoring child",
            "Volcano is ALWAYS in background during prehistoric scenes — increasing activity",
        ],
    
        "companions": "see_scenario_companions_list",
        "locations": "see_location_constraints",
    },

    # ── J: Custom Inputs — SABİT companion (kullanıcıya seçtirilmez) ──
    custom_inputs_schema=[
        {
            "key": "animal_friend",
            "type": "hidden",
            "default": "Minik Bebek Dinozor",
        },
    ],
))
