"""Sümela'nın Kayıp Mührü — Manastırda bulmaca macerası.

TİP A: Tek Landmark (Sümela Manastırı).
Companion: Fındık — sincap (SABİT — kullanıcıya seçtirilmez)
Obje: Bronz Madalyon
"""

from app.scenarios._base import CompanionAnchor, ObjectAnchor, ScenarioContent
from app.scenarios._registry import register

SUMELA = register(ScenarioContent(
    theme_key="sumela",
    name="Sümela'nın Kayıp Mührü",
    location_en="Sümela Monastery",
    default_page_count=22,
    flags={"no_family": False},

    # ── E: Hikaye Promptu (iyileştirilmiş — ~900 kelime) ──
    story_prompt_tr="""\
# SÜMELA'NIN KAYIP MÜHRÜ — GİZEMLİ MACERA

## YAPI: {child_name} sevimli sincabı {animal_friend} eşliğinde Sümela Manastırı'nda eski bir bronz madalyon bulur, zaman yolculuğu yapar ve kayıp bir el yazmasını kurtarmak için bulmaca çözer. Atmosferik, heyecanlı, korkutucu değil.

**BAŞLIK:** "[Çocuk adı]'ın Kayıp Mührü: Sümela". Alt başlık EKLEME.

**KARAKTER:** {child_name} ({child_age} yaşında, {child_gender}). Yardımcı: {animal_friend} — her sayfada AYNI görünüm, DEĞİŞTİRME.

**KARAKTER ARC — İÇ YOLCULUK:**
{child_name} başta yüksekten ve karanlık yerlerden biraz korkuyor — manastır uçuruma oyulmuş, merdivenler dar ve taşlar ıslak.
{animal_friend} yanında olunca rahatlar ama BÜYÜK kararları henüz kendisi alamıyor.
Macera boyunca adım adım cesaret kazanır: önce {animal_friend}'ın yardımıyla (spiral ipucunu bulma), sonra KENDİ KARARIYLA (rüzgarlı köprüden geçme, el yazmasının sayfalarını birleştirme).
Sonunda {child_name} gözlerinde artık korku değil, parlak bir ışık var — ama bu DEĞİŞİM ASLA SÖYLENMEZ, sadece EYLEMLERİYLE hissettirilir.

**YASAK:** Dini figür/ibadet detayı YOK — MİMARİ GİZEM odaklı. Korku/şiddet YASAK.

---

### Bölüm 1 — Gizemli Madalyon (Sayfa 1-3) 🎯 Duygu: MERAK + hafif TEDİRGİNLİK
- {child_name} Altındere Vadisi'nde yürüyor. 🔊 Derin vadi, çam ormanı, kuş sesleri, ıslak yaprak kokusu. Sis parmaklarını soğuk gibi dokunuyor.
- Hediyelik eşya dükkanında eski bronz madalyon buluyor — üzerinde üç sembol: kartal, anahtar, spiral. Dokunduğunda "tık" diye atıyor. "Bu nedir?" diye fısıldar. {animal_friend} merakla omzuna tırmanıp madalyona burnunu sürter.
- Sümela'ya çıkan dik taş yolda rüzgar sertleşiyor, sis sarıyor. {child_name} biraz çekiniyor — yol çok dik ve taşlar ıslak. Ama {animal_friend} çoktan ileride, dal daldan sıçrayarak yol gösteriyor! "Tamam tamam, geliyorum!" diye gülerek peşinden koşuyor.
🪝 HOOK: Madalyon cebinde sıcacık titremeye başlıyor — bir şeyi göstermek istiyor...

---

### Bölüm 2 — Zaman Kapısı (Sayfa 4-6) 🎯 Duygu: HEYECAN → ŞAŞKINLIK
- Manastır içinde silik fresk duvarlarının arasında — hava eski taş ve balmumu kokuyor. {child_name} madalyondaki sembolün aynısını duvardaki oyukta görüyor! "Bak {animal_friend}, aynı şekil!"
- Bir an tereddüt eder — ya tehlikeli bir şey olursa? {animal_friend} cesaretlendirmek ister gibi omzunda hafifçe pençesiyle sıkıyor. {child_name} madalyonu oyuğa yerleştiriyor — IŞIK SELİ! 🔊 "Vuuuş!" sesi, taşlar titriyor.
- Gözlerini açtığında HER ŞEY DEĞİŞMİŞ: mum ışıkları, telaşlı insanlar! Bir yazıcı koşarak geçiyor: "Kayıp el yazması yok olursa bilgimiz biter!" {child_name} {animal_friend}'a bakıyor: "Biz yardım edebiliriz!"
🪝 HOOK: Ama el yazması nerede? Ve onu bulmak için ne kadar zamanları var?

---

### Bölüm 3 — İpuçlarının Peşinde (Sayfa 7-10) 🎯 Duygu: GERİLİM → KEŞF
- Spiral ipucu! {animal_friend} duvardaki spirale pençesiyle dokunuyor — gizli bir koridor açılıyor! "Sen nasıl gördün bunu?" diye şaşırır {child_name}. {animal_friend} kuyruğunu sallayarak ilerliyor.
- Dar taş merdivenlere açılan karanlık geçit. 🔊 Su damlaları yankılanıyor, ✋ taşlar soğuk ve kaygan. {child_name} derin nefes alıp ilerliyor — artık tereddüt etmiyor.
- Üç sembollu ağır kapı — doğru sıralama bulmacası! {child_name} düşünüyor... "Yüksekte uçan — kartal! Ortada dönen — spiral! Aşağıyı açan — anahtar!" Sembolleri sırayla basıyor.
- 🔊 Ağır taş kapı gıcırdayarak açılıyor! {animal_friend} sevinçle sıçrıyor. "İlk bulmaca çözüldü!" diyor {child_name}, gözleri parlayarak.
🪝 HOOK: Ama kapının arkasında bekledikleri şey değil, boş bir oda var...

---

### Bölüm 4 — Gizemli Takip (Sayfa 11-14) 🎯 Duygu: ADRENALİN → CESARET
- Gizli depo odası — el yazması burada DEĞİL! 🔊 Uzaktan su damlası sesi... bir yöne doğru çekiyor. {animal_friend} kulağını dikip sesi takip ediyor.
- Dar koridorlarda koşuyorlar — gizemli bir gölge onları takip ediyor! Hızlı adımlar, çatlak taşlardan atlama. {child_name} korkmuyor artık, KOŞUYOR.
- Dar uçurum köprüsü! Aşağıda derin vadi, rüzgar saçlarını savuruyor. {animal_friend} çantaya sığınıyor, başını dışarı çıkarıp endişeyle bakıyor. {child_name} derin nefes alıyor: "Sen bende güvendesin. Ben geçebilirim." Ve geçiyor — ELLERI TİTREMİYOR ARTIK.
- Köprünün öbür tarafında gizli bir oda! Devasa eski tahta sandık duruyor.
🪝 HOOK: Sandıkta el yazması var mı?

---

### Bölüm 5 — Bulmacanın Sonu (Sayfa 15-18) 🎯 Duygu: ÇÖZÜM → ZAFER
- Anahtar sembolü parladığında gizli çıkıntıda gerçek bir anahtar! {child_name} sandığı açıyor — EL YAZMASI BURADA! Ama sayfalar kopuk ve karışık.
- Hız bulmacası! {animal_friend} sayfaları küçük pençeleriyle tutuyor, {child_name} kartal-spiral dizilimlerinden doğru sırayı çözüyor. 🔊 Kağıtların hışırtısı, eski mürekkep kokusu — zamanın kendisinin kokusu gibi.
- "Tamam! Son sayfa da yerinde!" {child_name} el yazmasını tamamlıyor. {animal_friend} sevinçle kuyruğunu sallıyor ve {child_name}'in omzuna atlayıp yanağını sürter.
- El yazmasını yazıcıya ulaştırıyor. Yazıcı hayret içinde gülümsüyor ve bir mühür basıyor — avuçlarına sıcak balmumu dokunuyor, 👅 tadı tatlı ve reçinemsi.
🪝 HOOK: Ama madalyon ısınıyor — dönüş kapısı kapanıyor olabilir!

---

### Bölüm 6 — Geri Dönüş (Sayfa 19-22) 🎯 Duygu: HEYECAN → HUZUR + GURUR
- Madalyon ISINIYOR — dönüş kapısı! Rüzgar fırtınaya dönüşmüş. "Koşmalıyız {animal_friend}!" 🔊 Rüzgar uğultusu, taşların çatırdaması.
- Koridorlardan koşuyorlar. {animal_friend} yol gösteriyor, dal daldan sıçrayarak. {child_name} artık karanlık koridorlardan KORKMUYOR — hızlı ve kararlı.
- Madalyonu yuvasında çeviriyor — FLAŞ! 🔊 Sessizlik. Gözlerini açtığında modern manastırda, güneş ışığı freskleri aydınlatıyor. Avucunda mühür izi yadigâr kalmış.
- {child_name} {animal_friend}'a bakıp gülümsüyor: "Biz iyi bir ekibiz." {animal_friend} başını {child_name}'in avucuna yasıyor. Son adımını atarken ufka bakıyor — gözlerinde artık korku yok, parlak bir ışık var. "Bir dahaki macera nereye olacak acaba?"

---

## 🚫 KURALLAR
- {animal_friend} = HER SAYFADA AYNI görünüm — DEĞİŞTİRME.
- Dini figür/ibadet detayı YOK. Mimari gizem odaklı.
- Korku/şiddet/gore YASAK.

## ⚠️ YAZIM KURALLARI

❌ YANLIŞ (Gezi Rehberi): "{child_name} Sümela Manastırı'na geldi. Manastır M.S. 386 yılında kurulmuş ve 1200 metre yükseklikte kayalara oyulmuştur."
✅ DOĞRU (Macera): "Taş merdivenlerden yukarı tırmandıkça sis kalınlaştı. {child_name}'in avucundaki madalyon titremeye başladı!"

❌ YANLIŞ (Doğrudan Öğüt): "{child_name} cesaretin ne kadar önemli olduğunu anladı. Bulmaca çözmek beyni geliştirirdi."
✅ DOĞRU (Subliminal): "{child_name} son bulmaca parçasını yerine koydu. Eller artık titremiyordu."

## 💬 DİYALOG KURALI
Her 3-4 sayfada en az 1-2 kısa diyalog. {child_name} {animal_friend}'a konuşur, sincap jest/ses ile tepki verir.

Hikayeyi TAM OLARAK {page_count} sayfa yaz. Her sayfa 2-4 cümle, akıcı ve macera dolu.
""",

    # ── F: Görsel Prompt Şablonları ──
    cover_prompt_template=(
        'An {child_age}-year-old {child_gender} named {child_name} with {hair_description}, '
        'wearing {clothing_description}. {scene_description}. Sumela Monastery carved into a sheer '
        'cliff face at 1200m altitude. Misty Altindere Valley pine forest below. Child holding an '
        'ancient bronze amulet with golden glow. Dramatic low-angle hero shot: child 25% foreground, '
        'cliff monastery 75%. Moody adventure palette: deep forest greens, slate grey rock, warm '
        'bronze glow, ethereal white mist. {STYLE}'
    ),
    page_prompt_template=(
        'An {child_age}-year-old {child_gender} named {child_name} with {hair_description}, '
        'wearing {clothing_description}. {scene_description}. '
        'EXTERIOR elements: [Altindere Valley pine forest, misty mountain paths, steep stone stairs, '
        'cliff-carved monastery facade, stone terraces]. '
        'INTERIOR elements: [Faded fresco walls, candlelit stone corridors, hidden passages, '
        'carved stone doors with symbols, ancient wooden chests]. '
        'ATMOSPHERIC: [mountain mist, flickering candlelight, wet stone surfaces, moss on ancient walls]. '
        'Shot variety: Wide establishing / Medium action / Close-up detail / Low angle vertigo. '
        'Color palette: deep forest green, slate grey, warm bronze, cream, ethereal white mist. '
        'Cinematic atmospheric lighting, detailed ancient stone texture. '
        'Dynamic pose, expressive emotion. No eye contact with camera. {STYLE}'
    ),

    # ── G: Kıyafetler ──
    outfit_girl=(
        "rich dark forest-green thick knit cardigan with colorful folk embroidery trim, "
        "a cream cotton blouse underneath, dark walnut-brown A-line midi skirt with subtle plaid, "
        "sturdy dark brown leather lace-up hiking boots with thick wool socks, "
        "a colorful woven headband, and a rustic leather satchel. "
        "EXACTLY the same outfit on every page."
    ),
    outfit_boy=(
        "chunky dark navy cable-knit fisherman sweater with wide rolled collar, "
        "rugged charcoal-grey climbing trousers with reinforced knees, "
        "sturdy dark brown leather mountain boots, a flat charcoal herringbone tweed kasket cap, "
        "and a worn dark leather crossbody messenger bag. "
        "EXACTLY the same outfit on every page."
    ),

    # ── G2: Tutarlılık Kartları ──
    companions=[
        CompanionAnchor(
            name_tr="Fındık",
            name_en="small cute hazelnut-brown squirrel",
            species="squirrel",
            appearance="small cute hazelnut-brown squirrel with a bushy fluffy tail, bright curious eyes, and tiny agile paws",
            short_name="Fındık",
        ),
    ],
    objects=[
        ObjectAnchor(
            name_tr="Bronz Madalyon",
            appearance_en="ancient bronze amulet/medallion with eagle, key, and spiral symbols, warm golden glow",
            prompt_suffix="holding ancient bronze amulet with three symbols — SAME on every page",
        ),
    ],

    # ── H: Kültürel Elementler ──
    cultural_elements={
        "primary": [
            "Altındere Valley dense pine forest and misty mountain paths",
            "Steep ancient stone steps carved into the cliff",
            "Byzantine rock-carved monastery — stone arches, terraces, hidden rooms",
            "Ancient fresco walls with faded mysterious symbols",
        ],
        "secondary": [
            "Mountain peaks with deep valley drops and fog",
            "Hidden stone corridors lit by flickering candlelight",
            "Narrow cliff-edge stone bridge with wind",
            "Ancient wooden chests with symbol locks",
        ],
        "values": ["Courage", "Intelligence", "Puzzle Solving", "Discovery"],
        "atmosphere": "Adventurous, mysterious, hidden passages, monastery",
        "sensitivity_rules": ["NO religious figure depictions", "NO worship details", "Architecture and mystery focus"],
    },

    # ── C/G3: Lokasyon Kısıtları ──
    location_constraints=(
        "Pages 1-3: Altındere Valley, forested stone path, mist. (Wide Shot, misty) "
        "Pages 4-6: Monastery entrance, fresco wall, hidden niche. (Medium Shot, candlelight) "
        "Pages 7-10: Dark narrow corridors, carved stone door puzzle. (Close-up, dramatic shadows) "
        "Pages 11-14: Hidden storage room, cliff-edge bridge. (Low Angle, vertigo) "
        "Pages 15-18: Secret chamber with chest and page puzzle. (Close-up, golden glow) "
        "Pages 19-22: Running back, time-flash return, sunlit modern monastery. (Epic Wide Shot, mist clearing)"
    ),

    # ── I: Scenario Bible (genişletilmiş) ──
    scenario_bible={
        "companion_pack": {
            "findik": {
                "species": "squirrel",
                "appearance_en": "small cute hazelnut-brown squirrel with a bushy fluffy tail, bright curious eyes, and tiny agile paws",
                "role": "Çocuğun cesur keşif arkadaşı, gizli ipuçlarını bulan, dallarda yol gösteren",
            },
        },
        "key_objects": {
            "bronz_madalyon": {
                "appearance_en": "ancient bronze amulet with eagle, key, and spiral symbols, warm golden glow",
                "first_page": 2,
                "last_page": 21,
                "prompt_suffix": "holding ancient bronze amulet with three symbols — SAME on every page",
            },
        },
        "side_characters": {
            "yazici": {
                "outfit_en": "elderly monastery scribe in dark brown hooded wool robe with ink-stained hands",
                "appears_on": [6, 18, 19],
                "rule": "SAME outfit and appearance on every page",
            },
        },
        "location_zone_map": {
            "altindere_valley": "pages 1-3, 21-22",
            "monastery_entrance": "pages 4-6, 19-21",
            "hidden_corridors": "pages 7-14",
            "secret_chamber": "pages 15-18",
        },
        "tone_rules": [
            "Dini figür veya ibadet detayı YOK — mimari gizem odaklı",
            "Bulmaca ve zeka odaklı engeller",
            "Rüzgar, sis ve taş mimari ile atmosfer yaratma",
        ],
        "consistency_rules": [
            "Squirrel companion MUST have EXACTLY the same hazelnut-brown color and bushy tail on EVERY page",
            "Bronze amulet MUST have the same three symbols (eagle, key, spiral) on pages 2-21",
            "Child's modern outfit MUST NOT change between time periods",
        ],
    },

    # ── J: Custom Inputs — SABİT companion ──
    custom_inputs_schema=[
        {
            "key": "animal_friend",
            "type": "hidden",
            "default": "Fındık",
        },
    ],
))
