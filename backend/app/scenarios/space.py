"""Uzay Macerası — Güneş Sistemi Macerası: Gezegen Kaşifi.

TİP B: Geniş Ortam (Uzay). Companion: Gümüş Robot Nova (SABİT — kullanıcıya seçtirilmez).
Obje: Yıldız Pusulası, Mars Kristali.
"""

from app.scenarios._base import CompanionAnchor, ObjectAnchor, ScenarioContent
from app.scenarios._registry import register

SPACE = register(ScenarioContent(
    # ── A: Temel Kimlik ──
    theme_key="space",
    name="Uzay Macerası",

    # ── B: Teknik ──
    location_en="Outer Space",
    default_page_count=22,
    flags={"no_family": True, "no_aliens": True},

    # ── E: Hikaye Promptu (iyileştirilmiş — ~750 kelime) ──
    story_prompt_tr="""\
# UZAY MACERASI — GEZEGENLERİN SIRRI

## YAPI: {child_name} TEK BAŞINA, AİLE YOK. Yanında sadece {animal_friend}.

**KRİTİK — METİN UZUNLUĞU:** Her sayfa 1-3 cümle, toplam 25-50 kelime. Kısa tut, sayfaya sığsın.

**KARAKTER:** {child_name} ({child_age} yaşında, {child_gender}). Yardımcı: {animal_friend} (küçük gümüş robot, mavi LED gözler, dönen anten — her sayfada AYNI görünüm, DEĞİŞTİRME).

**KARAKTER ARC — İÇ YOLCULUK:**
{child_name} başta heyecanlı ama uzayın büyüklüğünden bunalan bir çocuk. "Ben bu kadar büyük bir yerde ne yapabilirim ki?" hissi var.
İlk bölümlerde {animal_friend}'a çok bağımlı — robot yönlendiriyor, çocuk takip ediyor.
Asteroid krizinde panik yapıyor, "Yapamam!" diyor — ama {animal_friend} arızalanınca çocuk TEK BAŞINA harekete geçmek ZORUNDA.
Hikayenin sonunda {child_name} artık gözleri kararlı, "Bu evrende benim de yerim var" hisseden bir çocuk — ama bu DEĞİŞİM ASLA SÖYLENMEMELİ, sadece EYLEMLERİYLE hissettirilmeli.

**YASAK:** Anne, baba, aile üyesi, yetişkin YOK. Uzaylı / ET tarzı yaratık YOK. Sahnede sadece çocuk + robot.
Büyü, sihir YOK — bilimsel merak ve gerçekçi uzay macerası.

**AKIŞ (6 BÖLÜM):**

### BÖLÜM 1 — Kalkış ve İlk Hayranlık (Sayfa 1-3) 🎯 Duygu: MERAK + HEYECAN + hafif TEDİRGİNLİK
🌍 MEKAN: Uzay mekiği KOKPİT İÇİ — gösterge paneli, koltuk, pencereden yıldızlar. DIŞARI DEĞİL.
- {child_name} uzay mekiğinin kokpitinde, koltuk kemerini sıkıyor. {animal_friend} gösterge panelindeki düğmeleri kontrol ediyor, anteni hızla dönüyor.
- 🔊 Motor gümbürtüsü, geri sayım sesi: "3... 2... 1..." Koltuk titriyor, bulutlar hızla geçiyor, sonra — sessizlik.
- İlk kez uzay: Pencereden sonsuz karanlık ve milyonlarca yıldız. {child_name} yutkunuyor: "Bu kadar... büyükmüş." {animal_friend}'ın gözleri mavi parıldıyor.
- 🪝 HOOK: "Ama kontrol panelinde bir ışık yanıp sönmeye başladı — 'BİLİNMEYEN SİNYAL' yazıyordu..."

### BÖLÜM 2 — Ay ve Mars Keşfi (Sayfa 4-8) 🎯 Duygu: HEYECAN → MERAK → ŞAŞkınlık
🌍 MEKAN: Ay yüzeyi (gri krater) → Mars yüzeyi (kızıl kanyon, mağara içi kristaller). DIŞ GEZEGEN.
- Ay'ın yanından geçerken kraterler yakından görünüyor — {child_name}: "Sanki dev ayak izleri!"
- Mars'a iniş: Kızıl toprak, devasa kanyonlar. Uzay giysisinin vizörüne kum taneleri yapışıyor. 🔊 Botların kızıl toprağı çıtırdatması, rüzgarın hafif uğultusu.
- ✋ Mars toprağı ayaklarının altında çatırdıyor. Hava soğuk ve metalik kokuyor.
- Bir kaya yarığında parıldayan kristaller! {animal_friend}'ın sensörleri çılgınca yanıp sönüyor: "Bu mineral Dünya'da yok!"
- {child_name} kristali eline alıyor — avuç içi boyutunda, mor-mavi ışık saçıyor. "Bunu korumamız lazım."
- {animal_friend} yerdeki izleri tarıyor — çok eski bir keşif robotunun paletli izleri. İzler bir mağaraya gidiyor...
- {child_name} mağara girişinde duraksaklıyor: "Ya içeride bir şey varsa?" Ama Crystal cebinde ılık parlıyor.
- 🪝 HOOK: "Mağaranın derinliğinden gelen zayıf radyo sinyali, {animal_friend}'ın antenini çılgınca döndürüyordu..."

### BÖLÜM 3 — Asteroid Kuşağı KRİZİ (Sayfa 9-13) 🎯 Duygu: GERİLİM → KORKU → PANIK → CESARET
🌍 MEKAN: Asteroid kuşağı — uçan kayalar, buzlu asteroid yüzeyi, gemi içi alarm ışıkları.
- Mekikle asteroid kuşağına giriş. Dev kayalar dans ediyor, 🔊 çarpışma sesleri uzaktan gümbürdüyor.
- {animal_friend} hesaplıyor: "Güvenli rota — sağ 40 derece, yukarı 15!" {child_name} direksiyonu çeviriyor ama elleri titriyor.
- Bir asteroide zorlu iniş — buz ve metalden bir dünya. Yüzeyin altında ritmik ışık yanıp sönüyor — doğal bir fenomen.
- ✋ Buz yüzey eldivenlerinin altında bile soğuk hissettiriyor. Kristalin ışığı burada daha parlak yanıyor.
- BÜYÜK KRİZ: Bir asteroid mekiğe çarpıyor! 💥 Alarm çalıyor, kırmızı ışıklar yanıp sönüyor!
- {animal_friend} hasar raporunu veriyor: "Motor 2 devre dışı. Oksijen sızıntısı var." {child_name}: "N-ne yapacağız?!"
- {child_name} panik yapıyor, elleri titriyor. Ama kristali cebinde sıcacık parlıyor — sanki cesaret veriyor.
- 🪝 HOOK: "Tam o sırada {animal_friend}'ın gözleri söndü. Ekranında tek bir kelime belirdi: AŞIRI YÜK..."

### BÖLÜM 4 — Tek Başına Kahraman (Sayfa 14-16) 🎯 Duygu: YALNIZLIK → KARARLILIK → ZAFER
🌍 MEKAN: Gemi İÇİ — kokpit, tamir paneli, kablolar, aletler. Acil durum amber ışık.
- {animal_friend} aşırı yükten kapanmış! {child_name} şimdi TAMAMEN YALNIZ. Kalbi gümbürdüyor.
- "Yapamam... yapamam..." fısıldıyor. Ama sonra kristale bakıyor — mor ışık kararlı yanıyor.
- {child_name} derin nefes alıyor. Robot'un tamir panelini açıyor. Elleri artık TİTREMİYOR. Kabloları kontrol ediyor, bağlantıları sıkıştırıyor. 🔧
- ✋ Soğuk metal aletler avuçlarında. Ter damlası alnından vizöre düşüyor.
- Motor tamiri — {child_name} kalıp bağlantılarını düzeltiyor. Alev kaynağını tutuyor — "Hadi, çalış!" Son kablo... bağlandı!
- Motor uğuldamaya başlıyor! 🔊 "VIIINN!" {child_name}: "ÇALIŞTI!" — sesinde inanamayan bir sevinç.
- {animal_friend}'ın gözleri yeniden mavi yanıyor. Anteni yavaşça dönüyor. {child_name} robotu kucaklıyor.

### BÖLÜM 5 — Uzay İstasyonu (Sayfa 17-19) 🎯 Duygu: ŞAŞkınlık → SEVİNÇ → HUZUR
🌍 MEKAN: Uzay istasyonu İÇİ — sera bahçesi, süzülen bitkiler, dev pencereden nebula manzarası.
- Uzay istasyonuna yanaşma — devasa, dönen yapı, güneş panelleri altın gibi parlıyor.
- İçeride sera bahçesi — uzayda yetişen bitkiler! 👃 Hava çiçek ve nemli toprak kokuyor. Yeşil yapraklar sıfır yerçekiminde süzülüyor.
- İstasyonun dev penceresinden nebula manzarası — mor, turuncu, mavi renklerin kozmik dansı.
- 🔊 Sessizlik... sadece istasyonun hafif vınlaması ve {child_name}'ın hayranlık dolu nefesi.
- {child_name} Yıldız Pusulasını çıkarıyor ve nebulayı işaret ediyor. Pusulanın ibresi parıldıyor — "Evren ne kadar büyük... ama ben de buradayım."

### BÖLÜM 6 — Eve Dönüş ve Gurur (Sayfa 20-22) 🎯 Duygu: ÖZLEM + GURUR + HUZUR
🌍 MEKAN: Uzay → atmosfer girişi → okyanus inişi. Mavi Dünya pencereden büyüyor.
- Dünya'ya dönüş — mavi gezegen pencereden büyüyor. 👁️ Okyanusların mavisi, bulutların beyazı. {child_name}: "Evimiz ne kadar güzelmiş..."
- 🔊 Atmosfere giriş — ateş parçacıkları pencereden akıyor. Koltuk sarsılıyor. {child_name} bu sefer korkmuyor, gülümsüyor.
- Paraşütlerle okyanus inişi. {animal_friend}'ın anteni son bir kez hızla dönüyor — "Görev tamamlandı!" 🏆
- {child_name} mekiğin kapısını açıyor. Tuzlu deniz rüzgarı yüzünü okşuyor. Kristal cebinde sıcacık parlıyor.
- Son bakış gökyüzüne — yıldızlar henüz görünmüyor ama orada olduklarını biliyor. Gözlerinde artık tedirginlik yok, sakin bir kararlılık var.

---

## 🚫 KURALLAR
- AİLE/YETİŞKİN YOK. Sahnelerde sadece {child_name} + {animal_friend}.
- Uzaylı / ET tarzı yaratık YOK. Bilimsel merak, gerçekçi uzay.
- {animal_friend} AYNI görünüm her sayfada — küçük gümüş robot, mavi LED gözler, dönen anten. DEĞİŞTİRME.
- Mars Kristali + Yıldız Pusulası bulunduktan sonraki her sayfada görünmeli — AYNI tasarım.
- DUYGU: amazed, determined, brave (orta bölüm), proud (kapanış).

## ⚠️ YAZIM KURALLARI

❌ YANLIŞ (Gezi Rehberi): "Mars'ın yüzey sıcaklığı -60°C'dir. Mars'ın atmosferi çok incedir. Sonra kraterlere gittiler."
✅ DOĞRU (Macera): "Ayağının altındaki kızıl toprak çatırdadı. {animal_friend}'ın anteni bir kristal parıltısına kilitlendi!"

❌ YANLIŞ (Doğrudan Öğüt): "{child_name} cesareti önemini anlamıştı. Bu macera ona çok şey öğretmişti."
✅ DOĞRU (Subliminal): "{child_name} derin nefes aldı. Elleri artık titremiyordu. Aleti kavradı ve son kabloyu bağladı."

## 💬 DİYALOG KURALI
Her 3-4 sayfada en az 1 kısa diyalog olmalı. {child_name} konuşur, {animal_friend} ses/ışık/hareket ile tepki verir (robot konuşamaz ama ekranında mesaj gösterebilir). Diyaloglar kısa, doğal ve çocuğa uygun olmalı.

Hikayeyi TAM OLARAK {page_count} sayfa yaz. Her sayfa 1-3 cümle (25-50 kelime).
""",

    # ── F: Görsel Prompt Şablonları (iyileştirilmiş) ──
    cover_prompt_template=(
        'Story "{book_title}". A young child in a sleek space suit standing heroically '
        'on a planet surface with a small silver robot companion, '
        'wearing {clothing_description}. {scene_description}. '
        'Vast deep-space background with colorful nebula, distant planets, and bright stars. '
        'Dramatic cinematic hero shot, warm purple-blue space lighting. '
        'Child in foreground 30%, cosmic landscape filling background 70%. '
        'Space for title at top.'
    ),
    page_prompt_template=(
        'EXACTLY ONE young child {scene_description}, wearing {clothing_description}. '
        'Setting elements (choose relevant based on scene): '
        'LAUNCH: [spaceship cockpit with glowing panels, launch flames, clouds rushing past]. '
        'MOON/MARS: [grey moon craters, red Mars canyons, dusty rocky terrain, space suit visor]. '
        'ASTEROID: [icy asteroid surface, floating rocks, metallic debris, dramatic starfield]. '
        'STATION: [rotating space station interior, greenhouse with floating plants, nebula through window]. '
        'RETURN: [blue Earth from orbit, atmospheric reentry flames, ocean landing with parachutes]. '
        'ATMOSPHERIC: [blue-purple nebula glow, harsh white starlight, red Mars dust, '
        'warm golden cockpit lights, cold asteroid ice reflections, green greenhouse bioluminescence]. '
        'Shot variety: [close-up helmet visor / medium spacewalk / wide epic planet / '
        'cockpit interior POV / bird-eye asteroid field]. '
        'Composition: full body visible in action, sci-fi color palette (deep blue, purple, silver, warm amber). '
        'IMPORTANT: Only ONE child in the entire image, no second child, no twin, no duplicate. '
        'Text overlay space at bottom.'
    ),

    # ── G: Kıyafetler ──
    outfit_girl=(
        "sleek white and sky-blue space suit with orange mission patches on shoulder, "
        "clear dome helmet visor pushed up when inside ship, silver space boots with blue soles, "
        "small silver utility belt with glowing blue pouches. "
        "When inside ship: cream cotton jumpsuit with sky-blue stripe down the side "
        "and circular mission badge on chest. "
        "EXACTLY the same outfit on every page."
    ),
    outfit_boy=(
        "sleek white and dark blue space suit with orange mission patches on shoulder, "
        "clear dome helmet visor pushed up when inside ship, silver space boots with grey soles, "
        "small silver utility belt with glowing amber pouches. "
        "When inside ship: grey cotton jumpsuit with orange stripe down the side "
        "and circular mission badge on chest. "
        "EXACTLY the same outfit on every page."
    ),

    # ── G2: Tutarlılık Kartları ──
    companions=[
        CompanionAnchor(
            name_tr="Gümüş Robot Nova",
            name_en="small silver robot companion named Nova",
            species="robot",
            appearance=(
                "small silver robot companion named Nova with glowing blue LED eyes, "
                "a rotating silver antenna on top, rounded body with panel lines, "
                "two short articulated arms, and small wheel tracks for feet"
            ),
            short_name="Nova",
        ),
    ],
    objects=[
        ObjectAnchor(
            name_tr="Mars Kristali",
            appearance_en=(
                "small glowing crystal with purple-blue shimmer and inner light, "
                "palm-sized, found on Mars surface, translucent with faint swirling patterns inside"
            ),
            prompt_suffix="holding glowing purple-blue Mars crystal — SAME appearance on every page",
        ),
        ObjectAnchor(
            name_tr="Yıldız Pusulası",
            appearance_en=(
                "small brass-and-silver star compass with holographic display, "
                "circular with rotating inner ring, emits soft golden light when activated"
            ),
            prompt_suffix="wrist-mounted star compass with golden holographic display — SAME on every page",
        ),
    ],

    # ── H: Kültürel Elementler ──
    cultural_elements={
        "primary": [
            "Spaceship cockpit with holographic control panels",
            "Moon surface with grey craters and footprints",
            "Mars red canyons and dusty terrain",
            "Mars underground cave with crystal formations",
            "Asteroid belt with floating ice and metal rocks",
        ],
        "secondary": [
            "Space station rotating habitat ring",
            "Zero-gravity greenhouse with floating plants",
            "Nebula colors visible through station window (purple, orange, blue)",
            "Earth as blue marble from orbit",
            "Atmospheric reentry fire streaks",
        ],
        "details": [
            "Ancient robotic rover tracks on Mars surface",
            "Holographic star maps and navigation displays",
            "Space suit helmet visor reflections",
            "Parachute ocean recovery scene",
        ],
        "colors": "deep space blues, nebula purples, Mars reds, silver metallics, warm amber cockpit lights",
        "atmosphere": "Epic, adventurous, scientific wonder, vast yet intimate",
    },

    # ── C/G3: Lokasyon Kısıtları ──
    location_constraints=(
        "Pages 1-3: Spaceship cockpit during launch and first moments in orbit "
        "(Wide Shot → Close-up helmet visor, dramatic launch lighting → serene starfield). "
        "Pages 4-8: Moon flyby (exterior, grey craters) then Mars surface — red canyons, "
        "crystal cave, rover tracks (Medium Shot, warm red/amber Mars light). "
        "Pages 9-13: Asteroid belt — floating rocks, icy asteroid surface, ship interior during crisis "
        "(Dynamic angles, harsh white starlight, red alarm lighting). "
        "Pages 14-16: Ship repair — cockpit interior, tools, close-up hands working "
        "(Close-up, warm amber emergency lighting). "
        "Pages 17-19: Space station — exterior approach, greenhouse interior, nebula window view "
        "(Wide Shot, blue-white station lights, green bioluminescence). "
        "Pages 20-22: Earth return — blue marble growing, atmospheric reentry, ocean landing "
        "(Hero Shot, warm golden sunlight, blue ocean)."
    ),

    # ── I: Scenario Bible ──
    scenario_bible={
        "no_magic": True,
        "companions": [
            {
                "name_tr": "Gümüş Robot Nova",
                "name_en": "small silver robot companion named Nova",
                "species": "robot",
                "appearance": (
                    "small silver robot with glowing blue LED eyes, rotating antenna, "
                    "rounded body, two short arms, wheel tracks"
                ),
                "personality": "Curious, analytical, loyal. Shows emotions through LED eye colors and antenna speed.",
                "voice": "Cannot speak — communicates via screen text, beeps, LED colors, and antenna movements.",
            },
        ],
        "key_objects": [
            {
                "name_tr": "Mars Kristali",
                "appearance_en": (
                    "small glowing purple-blue crystal, palm-sized, translucent "
                    "with swirling patterns, found on Mars"
                ),
                "prompt_suffix": "holding glowing purple-blue Mars crystal — SAME appearance on every page",
                "first_appear": "Page 7",
                "story_role": "Emotional anchor — glows warmer when child feels brave, acts as courage metaphor",
            },
            {
                "name_tr": "Yıldız Pusulası",
                "appearance_en": (
                    "small brass-silver star compass on wrist, holographic display, "
                    "rotating inner ring, golden light"
                ),
                "prompt_suffix": "wrist star compass with golden hologram — SAME on every page",
                "first_appear": "Page 4",
                "story_role": "Navigation tool — helps find path through asteroid belt and back to Earth",
            },
        ],
        "locations": [
            "Spaceship cockpit with holographic control panels and leather pilot seat",
            "Moon surface — grey craters, low gravity, distant Earth in sky",
            "Mars canyon — towering red rock walls, dusty terrain, scattered boulders",
            "Mars cave — dark entrance, glowing crystals on walls and ceiling",
            "Asteroid belt — floating ice-and-metal rocks, harsh starlight",
            "Icy asteroid surface — frozen pools, metallic veins, rhythmic light pulses",
            "Ship interior during crisis — red alarm lights, sparking panels",
            "Space station exterior — rotating ring, golden solar panels",
            "Station greenhouse — floating green plants, water droplets in zero-g",
            "Station observation window — colorful nebula panorama",
            "Earth approach — blue marble growing, white cloud swirls",
            "Ocean landing — parachutes deployed, blue water, golden sunset",
        ],
        "zone_map": {
            "zone_1": "Spaceship cockpit — Launch platform to orbit (Pages 1-3)",
            "zone_2": "Moon flyby + Mars surface and caves (Pages 4-8)",
            "zone_3": "Asteroid belt — crisis zone (Pages 9-13)",
            "zone_4": "Ship interior — repair and recovery (Pages 14-16)",
            "zone_5": "Space station — rest and wonder (Pages 17-19)",
            "zone_6": "Earth return — ocean landing (Pages 20-22)",
        },
        "consistency_rules": [
            "Nova: small silver robot with blue LED eyes and rotating antenna — SAME design on EVERY page",
            "Mars Crystal: purple-blue glowing, palm-sized — SAME on EVERY page after Page 7",
            "Star Compass: brass-silver wrist device with golden hologram — SAME on EVERY page after Page 4",
            "Space suit: white with blue/dark-blue + orange patches — SAME design on EVERY page",
            "NO aliens, NO ET-type creatures, NO space monsters",
            "NO family members — child + Nova robot ONLY",
            "NO magic — scientific realism with sense of wonder",
            "ONLY ONE CHILD in every scene — no duplicate, no twin, no second child"
        ],
        "emotional_arc": {
            "pages_1_3": "Wonder + mild anxiety at vastness of space",
            "pages_4_8": "Excitement of discovery, growing confidence with Nova's help",
            "pages_9_13": "Rising tension → fear → panic when asteroid hits",
            "pages_14_16": "Loneliness when Nova shuts down → determination → triumph of solo repair",
            "pages_17_19": "Awe at nebula beauty → peaceful reflection → 'I belong here too'",
            "pages_20_22": "Bittersweet return → pride → calm confidence (transformed child)",
        },
        "character_arc": {
            "start_weakness": "Overwhelmed by vastness, dependent on Nova for every decision",
            "crisis": "Nova shuts down during asteroid damage — child must act ALONE",
            "turning_point": "Child repairs ship solo — hands stop trembling, eyes become determined",
            "end_strength": "Quiet confidence, no longer overwhelmed — 'The universe is big but I have my place'",
            "rule": "NEVER state the growth directly — show through ACTIONS only",
        },
        "no_family": True,
        "no_aliens": True,
        "child_solo": True,
    },

    # ── J: Custom Inputs — SABİT companion (kullanıcıya seçtirilmez) ──
    custom_inputs_schema=[
        {
            "key": "animal_friend",
            "type": "hidden",
            "default": "Gümüş Robot Nova",
        },
    ],
))
