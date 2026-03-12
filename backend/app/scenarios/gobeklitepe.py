"""Göbeklitepe Macerası — 12.000 yıl öncesine zaman yolculuğu.

TİP C: Fantastik (zaman yolculuğu). Tek başına, aile yok.
Companion: Cesur Step Tilkisi (SABİT — kullanıcıya seçtirilmez)
Obje: Kutsal Oyma Taşı
"""

from app.scenarios._base import CompanionAnchor, ObjectAnchor, ScenarioContent
from app.scenarios._registry import register

GOBEKLITEPE = register(ScenarioContent(
    # ── A: Temel Kimlik ──
    theme_key="gobeklitepe",
    name="Göbeklitepe Macerası",

    # ── B: Teknik ──
    location_en="Göbeklitepe",
    default_page_count=22,
    flags={"no_family": True},

    # ── E: Hikaye Promptu (iyileştirilmiş — ~850 kelime) ──
    story_prompt_tr="""\
# GÖBEKLİTEPE MACERASI — TARİHE DOKUNUŞ

## YAPI: {child_name} yanında {animal_friend} ile Göbeklitepe'de dolaşır. Rehber rotası DEĞİL — macera. Gizli bir geçit keşfeder; geçitten geçince 12.000 yıl öncesine gider. Orada izler, gizlenir, avcı-toplayıcılara yardım eder, bir sorun çözer, tarihe dokunur; sonra geçitten geri dönüp bugüne gelir.

**BAŞLIK:** Kitap adı sadece "[Çocuk adı]'ın Göbeklitepe Macerası" olmalı. Alt başlık EKLEME.

**KARAKTER:** {child_name} ({child_age} yaşında, {child_gender}). Yardımcı: {animal_friend} (her sayfada aynı görünüm — DEĞİŞTİRME).

**KARAKTER ARC — İÇ YOLCULUK:**
{child_name} başta yeni ve bilinmeyen yerlerden biraz çekiniyor. Dev taşlar onu büyülüyor ama karanlık geçide girmekten tedirgin.
Macera boyunca adım adım cesaret kazanır: önce {animal_friend}'ın desteğiyle, sonra KENDİ KARARIYLA.
Hikayenin sonunda {child_name} gözlerinde artık tedirginlik değil, parlak bir ışık var — ama bu DEĞİŞİM ASLA SÖYLENMEZ, sadece EYLEMLERİYLE hissettirilir.

**YASAK:** Anne, baba, aile üyesi YOK. Rehber yok. Korku/şiddet YASAK. Büyü/sihir YOK — geçit doğal bir zaman anomalisi.

---

### Bölüm 1 — Göbeklitepe'de İlk Adımlar (Sayfa 1-4) 🎯 Duygu: MERAK + hafif TEDİRGİNLİK
- {child_name} yanında {animal_friend} ile Şanlıurfa'da, Göbeklitepe arkeolojik alanına gelir. Biraz çekiniyor — ilk kez böyle eski, dev taşlarla dolu bir yerde.
- 🔊 Rüzgar bozkırdan esiyor, kuru toprak kokusu. Dev T-sütunlarını ilk gördüğünde duraksayıp gözlerini kocaman açar. "Bunlar gerçekten 12.000 yaşında mı?" diye fısıldar. {animal_friend} kulağını dikip heyecanla kuyruk/kanat sallar.
- Taşların etrafında dolaşırken {animal_friend} birden durup bir yöne bakar — taşların arasında gizli bir geçit fark ederler. "Buraya bak! Bu geçit daha önce var mıydı?"
- {child_name} bir an tereddüt eder — karanlık ve serin görünüyor. Ama {animal_friend} cesaretlendirmek ister gibi yanına gelip burnunu eline sürtüyor. Derin nefes alır: "Hazır mısın? İçeri giriyoruz!"
🪝 HOOK: Ama geçidin öbür tarafında onları neler bekliyor?

---

### Bölüm 2 — Geçit: 12.000 Yıl Öncesine (Sayfa 5-8) 🎯 Duygu: HEYECAN → ŞAŞKInlık
- Geçitte yürürler; ışık değişir, sesler farklılaşır. 🔊 Adım sesleri taş duvarlara yankılanıyor. Hava nemli toprak ve küflü taş kokuyor. {animal_friend} tedirginleşir ama {child_name}'in yanından ayrılmaz.
- Çıktıklarında manzara tamamen değişmiştir: aynı tepe ama inşaat hâlinde! İnsanlar dev taşları halatlarla çekiyor. "İnanabiliyor musun? Zaman değişti!" diye haykırır {child_name}, gözleri parlayarak.
- Gizlenirler, bir taş bloğun arkasından izlerler. 🔊 İnsanlar birbirine seslenirken, taşlar sürtünme sesiyle yerde kayıyor. {child_name} heyecanını zor bastırır: "İşte 12.000 yıl önce insanlar böyle bir şey inşa etmiş!"
- Tam o an bir çocuk yaşında avcı-toplayıcı onlara doğru yürür — göz göze gelirler! Kavga yok, korku yok; sadece merak dolu bir bakışma. Avcı-toplayıcı çocuk {child_name}'e bir parça kuru meyve uzatır — tadı tatlı ve topraksı.
🪝 HOOK: Ama henüz asıl macerayı görmüş değiller...

---

### Bölüm 3 — Sırrı Yerine Koyma (Sayfa 9-12) 🎯 Duygu: GERİLİM → CESARET → ZAFER
- Taşların arkasında kalıp avcı-toplayıcıların günlük işlerini izlerler.
- Yaşlı bir şefin endişeli yüzünü görürler. Şef, T-sütununun üzerindeki özel bir yuvaya oturması gereken kutsal oyma taşını bulamamaktadır.
- {animal_friend} burnuyla otları karıştırırken bir şeye takılır! Kutsal oyma taşı oradaymış! {child_name} bu sefer tereddüt ETMİYOR — cesaret toplayıp görünmeden taşı alıyor ve T-sütunundaki o küçük gediğe YERLEŞTİRİYOR. Elleri artık titremiyordu.
- "Onlara yardım ettik!" fısıldıyor, gözlerinde gurur. {animal_friend} sevinçle sıçrıyor.
🪝 HOOK: Şef geri döndüğünde taşı yerinde görecek — ama {child_name} ve {animal_friend} gizlenmişler...

---

### Bölüm 4 — Dairesel Yapı ve Hayvan Kabartmaları (Sayfa 13-16) 🎯 Duygu: MERAK → VEDAlaşma
- Dairesel taş yapının etrafında sessizce dolaşırlar. Hayvan kabartmaları: tilki, aslan, yılan, akbaba. {child_name} parmağıyla kabartmayı takip eder. 🔊 Parmağı altında taşın soğuk ve pürüzlü dokusu.
- {animal_friend} bir kabartmanın önünde birden durur — tilki kabartmasına bakıp şaşkınlıkla kafasını eğer! Sanki kendini tanımış gibi! {child_name} kahkahayla güler: "Bu sen misin yoksa?"
- Avcı-toplayıcı çocuk tekrar belirir! El işaretiyle selamlaşırlar. Ama tam o an arka taraftaki taşlar gürültüyle sallanır — bir engel! Dar bir çıkış yolundan koşarak geçmeleri gerekiyor.
- Geçide girerler; son bir kez arkalarına bakarlar — avcı-toplayıcı çocuk uzaktan el sallar. {child_name} gülümseyerek el sallar.
🪝 HOOK: Geçit onları geri getirecek mi?

---

### Bölüm 5 — Bugüne Dönüş (Sayfa 17-20) 🎯 Duygu: ŞAŞKInlık → KAVRAYIŞ
- Geçitten çıkınca her şey tekrar bugünkü hâline dönmüştür. {child_name} bir an duraksayıp etrafına bakar: "Gerçek miydi yoksa hayal mi?" 🔊 Uzaktan bir kuş ötüyor, rüzgar kuru otları sallıyor.
- O kutsal oyma taşının tam olarak az önce yerleştirdikleri yerde, 12.000 yıldır durduğunu fark edince gözleri büyür. Parmağını taşa dokunduruyor — sıcak, güneşten ısınmış.
- Gün batımının altın ışığı dikilitaşları boyar. {child_name} ile {animal_friend} alandan ayrılırken son bir kez arkalarına dönerler.

### Bölüm 6 — Kapanış (Sayfa 21-22) 🎯 Duygu: HUZUR + GURUR
- Harran Ovası'nın altın bozkırında yürürler. {child_name} {animal_friend}'a bakıp gülümsüyor: "Biz iyi bir ekibiz."
- Son adımını atarken ufka bakıyor. Gözlerinde artık tedirginlik yok — parlak, meraklı bir ışık var. "Bir dahaki macera nereye olacak acaba?"

---

## 🚫 KURALLAR
- AİLE YOK. Sahnelerde sadece {child_name} + {animal_friend}.
- {animal_friend} her sayfada AYNI görünüm — DEĞİŞTİRME.
- Kutsal oyma taşı sayfa 9-12'de AYNI görünüm.
- Kıyafet zaman yolculuğunda bile DEĞİŞMEZ.
- Korku/şiddet/gore YASAK.

## ⚠️ YAZIM KURALLARI

❌ YANLIŞ (Gezi Rehberi): "{child_name} Göbeklitepe'ye geldi. Göbeklitepe M.Ö. 10.000 yılında inşa edilmiştir. T-sütunları 3-5 metre boyundadır."
✅ DOĞRU (Macera): "{child_name}'in ayağı bir taşa takıldı — ama bu sıradan bir taş değildi. Üzerinde garip semboller vardı!"

❌ YANLIŞ (Doğrudan Öğüt): "{child_name} tarihin ne kadar önemli olduğunu anlamıştı. Bu macera ona çok şey öğretmişti."
✅ DOĞRU (Subliminal): "{child_name} parmağını taşın üzerindeki kabartmaya dokundurdu. 12.000 yıl önceki biri de tam buraya dokunmuştu."

## 💬 DİYALOG KURALI
Her 3-4 sayfada en az 1-2 kısa diyalog. {child_name} ile {animal_friend} arasında jest, ses, bakış üzerinden iletişim. Companion konuşamaz ama çocuk ona konuşur ve hayvan tepki verir.

Hikayeyi TAM OLARAK {page_count} sayfa yaz. Her sayfa 2-4 cümle, akıcı ve macera dolu.
""",

    # ── F: Görsel Prompt Şablonları ──
    cover_prompt_template=(
        'An {child_age}-year-old {child_gender} named {child_name} with {hair_description}, '
        'wearing {clothing_description}. {scene_description}. Ancient Gobeklitepe T-shaped megalithic '
        'pillars with animal carvings in background, amazed expression. Harran Plain steppe, '
        'warm cinematic lighting on limestone, rich stone texture. Wide shot: child 30%, ancient '
        'pillars 70%. Epic archaeological wonder atmosphere. {STYLE}'
    ),
    page_prompt_template=(
        'An {child_age}-year-old {child_gender} named {child_name} with {hair_description}, '
        'wearing {clothing_description}. {scene_description}. Elements: [T-pillars: 3-5m limestone '
        'megaliths, animal carvings (fox, lion, snake, vulture) / Circular enclosures: stone rings / '
        'Harran Plain: golden steppe / Stone quarry: unfinished pillars in bedrock]. Cinematic action '
        'lighting, warm golden glow, detailed ancient stone texture. Dynamic action pose, expressive '
        'emotion on face (amazed, determined, smiling). No eye contact with camera. {STYLE}'
    ),

    # ── G: Kıyafetler ──
    outfit_girl=(
        "beige cotton field shirt with button-down collar and chest pocket, olive green cargo pants "
        "with side pockets, tan leather ankle boots, wide-brim sand-colored canvas sun hat, "
        "small khaki field bag crossbody. EXACTLY the same outfit on every page — same beige shirt, "
        "same olive cargo pants, same sun hat."
    ),
    outfit_boy=(
        "stone beige safari-style shirt with flap pockets, khaki cargo pants with button-flap "
        "pockets, brown leather work boots, tan canvas explorer hat, small olive field satchel "
        "across body. EXACTLY the same outfit on every page — same beige shirt, same khaki cargo, "
        "same explorer hat."
    ),

    # ── G2: Tutarlılık Kartları ──
    companions=[
        CompanionAnchor(
            name_tr="Cesur Step Tilkisi",
            name_en="brave steppe fox",
            species="fox",
            appearance="small reddish-brown steppe fox with bushy tail, bright amber eyes, pointed ears, and a white-tipped snout",
            short_name="Step Tilkisi",
        ),
        CompanionAnchor(
            name_tr="Step Kartalı",
            name_en="majestic dark brown steppe eagle",
            species="eagle",
            appearance="majestic dark brown steppe eagle with golden-tipped feathers, piercing amber eyes, broad powerful wings, and sharp curved talons",
            short_name="Step Kartalı",
        ),
        CompanionAnchor(
            name_tr="Neolitik Keçi",
            name_en="small brown Neolithic wild goat kid",
            species="goat",
            appearance="small brown Neolithic wild goat kid with curved tiny horns, a white chest patch, soft woolly coat, and curious dark eyes",
            short_name="Neolitik Keçi",
        ),
        CompanionAnchor(
            name_tr="Yabani Kedi",
            name_en="small striped tawny wildcat",
            species="wildcat",
            appearance="small striped tawny wildcat with bright green eyes, a bushy ringed tail, pointed tufted ears, and silent soft paws",
            short_name="Yabani Kedi",
        ),
    ],
    objects=[
        ObjectAnchor(
            name_tr="Kutsal Oyma Taşı",
            appearance_en=(
                "sacred small carved stone tablet with ancient geometric sun symbols, "
                "palm-sized, weathered cream limestone"
            ),
            prompt_suffix="holding a sacred small carved stone tablet with geometric symbols — SAME on every page",
        ),
    ],

    # ── H: Kültürel Elementler ──
    cultural_elements={
        "primary": [
            "T-shaped megalithic pillars (3-5m tall limestone)",
            "Animal relief carvings (fox, lion, snake, vulture, scorpion)",
            "Circular stone enclosures (concentric rings)",
            "Stone quarry with unfinished pillars in bedrock",
            "Harran Plain golden steppe landscape",
        ],
        "secondary": [
            "Ancient hunter-gatherer construction techniques",
            "Secret passage/cave entrance between stones",
            "Sacred carved stone placed in T-pillar niche",
            "Warm sandstone and amber tones in sunset light",
            "Archaeological dig site atmosphere",
        ],
        "values": ["Curiosity", "Cooperation", "History appreciation", "Scientific thinking"],
        "atmosphere": "Ancient, mysterious, archaeological wonder",
    },

    # ── C/G3: Lokasyon Kısıtları ──
    location_constraints=(
        "Pages 1-4: Göbeklitepe archaeological site exterior, T-shaped pillars, golden steppe. (Wide Shot, epic) "
        "Pages 5-8: Inside the secret passage and emerging into 12,000 years ago. (Medium Shot, dramatic) "
        "Pages 9-12: Ancient construction site, hunter-gatherers working. (Close-up, detailed stone texture) "
        "Pages 13-16: Circular stone enclosures with animal carvings. (Low Angle, mystical) "
        "Pages 17-20: Returning through passage to modern day. (Wide Shot, warm sunset) "
        "Pages 21-22: Sunset departure, epic final look at pillars. (Hero Shot, golden hour)"
    ),

    # ── I: Scenario Bible ──
    scenario_bible={
        "companion_pack": {
            "cesur_step_tilkisi": {
                "species": "fox",
                "appearance_en": "small reddish-brown steppe fox with bushy tail and bright eyes",
                "role": "Çocuğun cesur keşif arkadaşı, geçidi ilk fark eden",
            },
            "step_kartali": {
                "species": "eagle",
                "appearance_en": "majestic dark brown steppe eagle with golden-tipped feathers and piercing amber eyes",
                "role": "Tepeden izleyen kahraman, T-sütunlarının üzerine konan akıllı rehber",
            },
            "neolitik_keci": {
                "species": "goat",
                "appearance_en": "small brown Neolithic wild goat kid with curved tiny horns and a white chest patch",
                "role": "Avcı-toplayıcı çağından kalma neşeli dost",
            },
            "yabani_kedi": {
                "species": "wildcat",
                "appearance_en": "small striped tawny wildcat with green eyes and a bushy ringed tail",
                "role": "Sessiz ve gizemli keşif arkadaşı",
            },
        },
        "key_objects": {
            "kutsal_oyma_tasi": {
                "appearance_en": "sacred small carved stone tablet with ancient geometric sun symbols, palm-sized",
                "first_page": 9,
                "last_page": 12,
                "prompt_suffix": "holding sacred carved stone tablet with geometric symbols — SAME on every page",
            },
        },
        "side_characters": {
            "avci_toplayici_sef": {
                "outfit_en": "elderly hunter-gatherer chief in dark brown animal hide robe with bone necklace and grey beard",
                "appears_on": [9, 10, 11, 12],
                "rule": "SAME outfit and appearance on every page",
            },
            "avci_toplayici_cocuk": {
                "outfit_en": "young hunter-gatherer child in light brown deer hide tunic with short dark hair",
                "appears_on": [8, 13, 14, 15],
                "rule": "SAME outfit and appearance on every page",
            },
        },
        "location_zone_map": {
            "modern_site": "pages 1-4, 17-22",
            "passage": "pages 4-5, 16-17",
            "ancient_12000": "pages 5-16",
        },
        "consistency_rules": [
            "Companion animal MUST have EXACTLY the same species, color, and size on EVERY page",
            "Sacred carved stone tablet MUST have the same geometric patterns on pages 9-12",
            "Child's explorer outfit MUST NOT change between time periods",
        ],
    
        "companions": "see_scenario_companions_list",
        "locations": "see_location_constraints",
    },

    # ── J: Custom Inputs — SABİT companion (kullanıcıya seçtirilmez) ──
    custom_inputs_schema=[
        {
            "key": "animal_friend",
            "type": "hidden",
            "default": "Cesur Step Tilkisi",
        },
    ],
))
