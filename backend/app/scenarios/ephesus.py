"""Efes'in Zaman Kapısı — Antik Efes'te su kemeri macerası.

TİP C: Fantastik (zaman yolculuğu). Indiana Jones tarzı.
Companion: Efes Kedisi (SABİT — kullanıcıya seçtirilmez)
Obje: Gizemli Taş Tablet
"""

from app.scenarios._base import CompanionAnchor, ObjectAnchor, ScenarioContent
from app.scenarios._registry import register

EPHESUS = register(ScenarioContent(
    theme_key="ephesus",
    name="Efes'in Zaman Kapısı",
    location_en="Ephesus",
    default_page_count=22,
    flags={"no_family": False},

    # ── E: Hikaye Promptu (iyileştirilmiş — ~850 kelime) ──
    story_prompt_tr="""\
# EFES'İN ZAMAN KAPISI — ANTİK MACERA

## YAPI: {child_name} yanında {animal_friend} ile Efes Antik Kenti'nde gizemli bir taş bularak zaman yolculuğu yapar ve Roma dönemindeki Efes'te su kemerinin bozulmasını çözer. Indiana Jones tarzı tempolu, heyecanlı, gizem dolu. Korkutucu veya kanlı DEĞİL ama adrenalin VAR.

**BAŞLIK:** Kapak başlığı "[Çocuk adı]'ın Zaman Kapısı: Efes" olmalı. Alt başlık EKLEME.

**KARAKTER:** {child_name} ({child_age} yaşında, {child_gender}). Yardımcı: {animal_friend} (her sayfada AYNI görünüm — DEĞİŞTİRME).

**KARAKTER ARC — İÇ YOLCULUK:**
{child_name} başta eski harabelerde biraz tedirgin — taşlar çok büyük, gölgeler çok uzun, her şey çok eski.
{animal_friend} yanında olunca rahatlar ama BÜYÜK kararları kendisi alamaz henüz.
Macera boyunca adım adım cesaret kazanır: önce {animal_friend}'ın desteğiyle, sonra KENDİ KARARIYLA (su vanasına taşı yerleştirme kararı).
Hikayenin sonunda {child_name} gözlerinde artık tedirginlik değil, parlak bir ışık var — ama bu DEĞİŞİM ASLA SÖYLENMEZ, sadece EYLEMLERİYLE hissettirilir.

**YASAK:** Korku/şiddet YASAK. Büyü/sihir YOK — taş doğal bir zaman anomalisi. Didaktik nasihat YASAK.

---

### Bölüm 1 — Gizemli Keşif (Sayfa 1-3) 🎯 Duygu: MERAK + hafif TEDİRGİNLİK
🌍 MEKAN: EFES ören yeri DIŞ — mermer sütunlar, Celsus Kütüphanesi cephesi, taş yol. SİHİR YOK.
- {child_name} yanında {animal_friend} ile Efes harabeleri arasında yürür. 🔊 Ayakları altında çıtırdayan mermer kırıntıları, uzaktan ağustosböceği sesi. Kuru ot ve sıcak taş kokusu.
- Biraz çekiniyor — dev sütunlar koskocaman, gölgeler uzun. {animal_friend} ama rahat, mermer bir sütunun çevresinde tırmalanıyor / süzülüyor, {child_name}'i cesaretlendirmek ister gibi.
- Harabelerde gezerken {child_name}'in ayağı bir taşa takılır. Sıradan bir taş değil — üzerinde antik semboller parlamaya başlar! "Bu da ne?" diye fısıldar. {animal_friend} merakla yaklaşıp koklayarak inceliyor.
- Çantasına koyup yürümeye devam ederler. Mermer yoldan dev sütunlar arasından geçerken taş yeniden titremeye başlar. {animal_friend} kulağını dikip bir yöne bakar...
🪝 HOOK: Taş neden titriyor? {animal_friend} neyi duydu?

---

### Bölüm 2 — Zaman Kapısı (Sayfa 4-6) 🎯 Duygu: HEYECAN → ŞAŞKINLIK
🌍 MEKAN: ANTİK EFES İÇİ — canlı mermer cadde, Helenistik dükkanlar, hareketli pazar. Modern ören yeri değil.
- Celsus Kütüphanesi'nin önüne gelirler. {animal_friend} bir sütundaki boşluğa doğru ilerler — tam taşın şekline uyan bir yuva! "Nasıl gördün bunu?" der {child_name} şaşkınlıkla.
- Bir an tereddüt eder — ya tehlikeli bir şey olursa? Ama {animal_friend} cesaretlendirmek ister gibi yanına gelip burnunu eline sürter. {child_name} cesaretini toplar ve taşı yuvasına yerleştirir.
- GOZ KAMAŞTIRICI IŞIK! 🔊 Taş zemine sürtünme sesi, derin bir uğultu. Gözlerini açtığında HER ŞEY DEĞİŞMİŞ: turistler gitmiş, etrafta antik Roma pazar yeri, tunik giymiş insanlar, at arabaları! "İnanabiliyor musun? Zamanda yolculuk yaptık!" diye haykırır.
🪝 HOOK: Ama bu antik şehirde bir şeyler YANLIŞ gidiyor — çeşmeler kurumuş!

---

### Bölüm 3 — Kuruyan Çeşmeler (Sayfa 7-9) 🎯 Duygu: ENDİŞE → KARARLLIK
🌍 MEKAN: Celsus Kütüphanesi İÇİ + kuruyan çeşme yakını — taş kanal, su izleri. Cadde değil.
- Pazar yerinde panik var. Genç bir Romalı çırak koşarak geçer: "Su kemeri bozuldu! Şehrin çeşmeleri durdu!" 🔊 Kuru taş kanallardan boş damla sesleri yankılanıyor.
- {child_name} çırağın peşine düşer, {animal_friend} hemen yanında. Kurumuş taş kanallarını inceler. Parmaklarını kanalın içinden geçirir — kuru, tozlu, sıcak.
- Tabletteki sembollerin su kanalının üzerindeki işaretlerle AYNI olduğunu fark eder! "Bu taş buranın haritası olabilir!" {animal_friend} heyecanla sıçrar / kanat çırpar.
🪝 HOOK: Semboller bir yolu gösteriyor — ama o yol karanlık bir tünele açılıyor...

---

### Bölüm 4 — Antik Bulmaca ve Kovalamaca (Sayfa 10-13) 🎯 Duygu: GERİLİM → ADRENALİN
🌍 MEKAN: YERALTI GEÇİDİ — taş tünel, su kanalları, dim meşale ışığı. Yüzey değil.
- 🔊 Adımları taş duvarlara yankılanıyor. Hava nemli ve küflü. {animal_friend} öncü olur — karanlıkta gözleri parlayan bir rehber.
- 3 sütundaki sembolleri hizalayan bulmacayı çözer, gizli bakım tüneli açılır! {child_name} bu sefer TEREDDÜT ETMİYOR — hemen içeri dalıyor.
- Kovalamaca — dar geçit, tavandan tozlar, kapı kapanıyor! {animal_friend} son anda altından kayarak geçer. {child_name} de peşinden! "Az kalsın sıkışıyorduk!" diye nefes nefese güler.
- Devasa su vanası mekanizmasını bulur — tek başına çeviremeyecek kadar büyük. 🔊 Metal gıcırtısı, taş sürtünmesi.
🪝 HOOK: Vanayı nasıl çevirecekler?

---

### Bölüm 5 — Mühendislik ve Başarı (Sayfa 14-17) 🎯 Duygu: ÇÖZÜM → ZAFER
🌍 MEKAN: SU KEMERİ alanı — antik su mekaniği, taş vanalar, tıkalı kanal. Yeraltı değil.
- Antik usta yetişir: "Bu vanayı tek kişi çeviremez." {child_name} etrafına bakınır — bir direk ve halat! Kaldıraç planı kurar. {animal_friend} halatı yakalar / çeker / taşır.
- Birlikte vana döner! 🔊 Metal gıcırtısı ve sonra... SU SESİ! Ama yeni bir sorun: çatlak var ve su yanlış kanala kaçıyor!
- Kilit taşı eksik. {child_name} bir an düşünür — sonra avucuna bakar. KENDİ TAŞI! "Bu taş... tam buraya uyuyor!" Ellerini uzatır ve taşı kanala YERLEŞTİRİR. Elleri artık titremiyordu.
- 🔊 Su gürül gürül doğru kanala akıyor! Büyük alkış kopar. Usta hayret içinde: "Sen nasıl bir çocuksun!" {animal_friend} sevinçle dans eder / süzülür.
🪝 HOOK: Su geldi — ama zaman tüneli de kapanıyor olabilir!

---

### Bölüm 6 — İz Bırakmak ve Günümüze Dönüş (Sayfa 18-22) 🎯 Duygu: MİNNET → HUZUR + GURUR
🌍 MEKAN: MODERN ören yeri dönüş — taş kalıntılar, gün batımı, sessiz antik tiyatro. Antik canlı şehir değil.
- Pazar yerine gürül gürül su geliyor. Herkes minnettar. Romalı çırak {child_name}'e bir parça bal ikram eder — tadı tatlı ve çiçek kokulu.
- Çantasındaki TAŞ YOK artık — su kanalına yerleştirdi! Ama {animal_friend} avucunu yalar / gagalar ve {child_name} avucunda küçük bir iz görür — eski çağdan kalma bir hatıra işareti.
- Gün batımının altın ışığı antik mermer sütunları boyar. {child_name} ile {animal_friend} modern dünyanın harabeleri arasında yürürler. {child_name} {animal_friend}'a bakıp gülümser: "Biz iyi bir ekibiz."
- Son adımını atarken ufka bakıyor. Gözlerinde artık tedirginlik yok — parlak, meraklı bir ışık var. "Bir dahaki macera nereye olacak acaba?"

---

## 🚫 KURALLAR
- {animal_friend} her sayfada AYNI tutarlı görünüm. DEĞİŞTİRME!
- Kıyafet zaman yolculuğunda bile DEĞİŞMEZ.
- Korku/şiddet/gore YASAK.

## ⚠️ YAZIM KURALLARI

❌ YANLIŞ (Gezi Rehberi): "{child_name} Efes'e geldi. Celsus Kütüphanesi M.S. 117 yılında inşa edilmiştir ve 12.000 rulo barındırıyordu."
✅ DOĞRU (Macera): "{child_name}'in ayağı bir taşa takıldı — ama bu sıradan bir taş değildi. Üzerinde garip semboller parlıyordu!"

❌ YANLIŞ (Doğrudan Öğüt): "{child_name} tarih sayesinde çok şey öğrendiğini anladı. Mühendislik harika bir bilimdi."
✅ DOĞRU (Subliminal): "{child_name} taşı kanala yerleştirdi. 2000 yıl önceki biri de tam aynı hareketi yapmıştı."

## 💬 DİYALOG KURALI
Her 3-4 sayfada en az 1-2 kısa diyalog. {child_name} {animal_friend}' ile jest/ses/bakış üzerinden iletişim kurar. Companion konuşamaz ama çocuk ona konuşur ve hayvan tepki verir.

Hikayeyi TAM OLARAK {page_count} sayfa yaz. Her sayfa 2-4 cümle, akıcı ve macera dolu.
""",

    # ── F: Görsel Prompt Şablonları ──
    cover_prompt_template=(
        'EXACTLY ONE {child_age}-year-old {child_gender} named {child_name} with {hair_description}, '
        'wearing {clothing_description}. {scene_description}. Magnificent Library of Celsus facade '
        'with tall Corinthian columns, a glowing time-rift portal shimmering between the ancient '
        'pillars. Golden hour Aegean sunlight, warm rim lighting. Low-angle hero shot: child 25% '
        'foreground, towering Greco-Roman architecture 75%. Rich warm palette: honey gold, ivory '
        'marble, terracotta, deep azure sky. {STYLE}'
    ),
    page_prompt_template=(
        'An {child_age}-year-old {child_gender} named {child_name} with {hair_description}, '
        'wearing {clothing_description}. {scene_description}. '
        'EXTERIOR elements: [Ancient Ephesus ruins, sun-bleached marble columns, Curetes Street, '
        'golden steppe hills, dried grass, azure Aegean sky]. '
        'INTERIOR elements: [Hidden aqueduct tunnels, stone mechanisms, Roman market stalls, '
        'ancient water channels, lever and rope contraptions]. '
        'ATMOSPHERIC: [dust motes floating in golden sunbeams, warm marble texture, cicada ambiance]. '
        'IMPORTANT: Only ONE child in the entire image, no second child, no twin, no duplicate. '
        'Shot variety: Wide establishing / Medium action / Close-up detail / Low angle hero. '
        'Color palette: honey gold, ivory marble, terracotta, olive green, deep azure. '
        'Cinematic action lighting, warm golden glow, detailed marble texture. '
        'Dynamic action pose, expressive emotion. No eye contact with camera. {STYLE}'
    ),

    # ── G: Kıyafetler ──
    outfit_girl=(
        "breezy sky-blue linen wide-leg palazzo pants with a subtle white stripe, a crisp white "
        "linen peasant blouse with delicate floral hand-embroidery along the neckline, a natural "
        "woven straw hat with a sky-blue ribbon band, comfortable woven leather espadrille sandals "
        "with ankle ties, and a small wicker shoulder bag. EXACTLY the same outfit on every page."
    ),
    outfit_boy=(
        "light sky-blue and white horizontal-striped linen button-down shirt, cream off-white "
        "lightweight chino pants, comfortable natural canvas espadrille slip-on shoes, a navy canvas "
        "sailor cap with a small anchor badge, and a small olive leather crossbody satchel. "
        "EXACTLY the same outfit on every page."
    ),

    # ── G2: Tutarlılık Kartları ──
    companions=[
        CompanionAnchor(
            name_tr="Efes Kedisi",
            name_en="sleek gray and white Ephesus street cat",
            species="cat",
            appearance="sleek gray and white Ephesus street cat with amber eyes and a small notch on the left ear",
            short_name="Efes Kedisi",
        ),
    ],
    objects=[
        ObjectAnchor(
            name_tr="Gizemli Antik Taş",
            appearance_en="mysterious cracked stone tablet with glowing ancient Greek symbols, palm-sized",
            prompt_suffix="holding mysterious cracked stone tablet with ancient symbols — SAME on every page",
        ),
    ],

    # ── H: Kültürel Elementler ──
    cultural_elements={
        "primary": [
            "Celsus Library (12,000 scrolls, two-story facade)",
            "Great Theater (25,000 capacity, carved into hillside)",
            "Curetes Street (marble colonnaded street)",
            "Ancient Water Aqueducts and Fountains",
        ],
        "secondary": [
            "Hidden maintenance tunnels beneath the aqueduct",
            "Ancient lever mechanism of rope and timber",
            "Mysterious carved stone tablet with glowing symbols",
            "Sunlit marble dust floating in Aegean breeze",
        ],
        "values": ["Courage", "Problem Solving", "Engineering", "Historical awareness"],
        "atmosphere": "Ancient, mysterious, action-packed, time-travel, Greco-Roman",
    },

    # ── C/G3: Lokasyon Kısıtları ──
    location_constraints=(
        "Pages 1-3: Modern Ephesus ruins exterior, sun-bleached marble. (Wide Shot, golden hour) "
        "Pages 4-6: Library of Celsus, time-portal light rift. (Medium Shot, dramatic) "
        "Pages 7-9: Ancient Roman Curetes Street market, dried fountains. (Wide + Close-up) "
        "Pages 10-13: Hidden tunnel beneath the aqueduct, dark stone. (Close-up, dramatic lighting) "
        "Pages 14-17: Water aqueduct system, lever mechanism, water flow. (Medium Shot, action) "
        "Pages 18-22: Ancient marketplace celebration, sunset, return to modern ruins. (Wide Shot, warm glow)"
    ),

    # ── I: Scenario Bible ──
    scenario_bible={
        "no_magic": True,
        "companion_pack": {
            "efes_kedisi": {
                "species": "cat",
                "appearance_en": "sleek gray and white Ephesus street cat with amber eyes and a small notch on the left ear",
                "role": "Çocuğun keşif arkadaşı, karanlık tünellerde gözleri parlayan rehber",
            },
        },
        "key_objects": {
            "gizemli_tas": {
                "appearance_en": "mysterious cracked stone tablet with glowing ancient Greek symbols, palm-sized",
                "first_page": 1,
                "last_page": 17,
                "prompt_suffix": "holding mysterious cracked stone tablet — SAME on every page",
            },
        },
        "side_characters": {
            "romali_cirak": {
                "outfit_en": "young Roman apprentice in off-white linen tunic with brown leather belt and sandals",
                "appears_on": [7, 8, 9, 18, 19],
                "rule": "SAME outfit and appearance on every page",
            },
            "antik_usta": {
                "outfit_en": "elderly Roman master engineer in dark brown toga with grey beard and worn leather tool belt",
                "appears_on": [14, 15, 16, 17],
                "rule": "SAME outfit and appearance on every page",
            },
        },
        "location_zone_map": {
            "modern_ruins": "pages 1-3, 20-22",
            "time_portal": "pages 3-4, 18-19",
            "ancient_ephesus": "pages 4-17",
        },
        "consistency_rules": [
            "Companion cat MUST have EXACTLY the same gray-white color, amber eyes, and ear notch on EVERY page",
            "Stone tablet MUST have the same crack pattern and Greek symbols on pages 1-17",
            "Child's modern outfit MUST NOT change between time periods",
            "Roman characters MUST wear the same tunic/toga on every appearance",
            "ONLY ONE CHILD in every scene — no duplicate, no twin, no second child",
            "NO magic, NO supernatural powers — realistic adventure only"
        ],
    
        "companions": "see_scenario_companions_list",
        "locations": "see_location_constraints",
    },

    # ── J: Custom Inputs — SABİT companion (kullanıcıya seçtirilmez) ──
    custom_inputs_schema=[
        {
            "key": "animal_friend",
            "type": "hidden",
            "default": "Efes Kedisi",
        },
    ],
))
