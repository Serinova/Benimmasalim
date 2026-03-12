"""Çatalhöyük'ün Çatı Yolu — Neolitik köy macerası.

TİP C: Fantastik (zaman yolculuğu). 9.000 yıl öncesi.
Companion: Köpek (SABİT — kullanıcıya seçtirilmez)
Obje: Obsidyen Ayna
"""

from app.scenarios._base import CompanionAnchor, ObjectAnchor, ScenarioContent
from app.scenarios._registry import register

CATALHOYUK = register(ScenarioContent(
    theme_key="catalhoyuk",
    name="Çatalhöyük'ün Çatı Yolu",
    location_en="Çatalhöyük",
    default_page_count=22,
    flags={"no_family": False},

    # ── E: Hikaye Promptu (iyileştirilmiş — ~900 kelime) ──
    story_prompt_tr="""\
# ÇATALHÖYÜK'ÜN ÇATI YOLU — NEOLİTİK KÖY MACERASI

## YAPI: {child_name} yanında {animal_friend} ile Çatalhöyük kazı alanında gezerken gizemli bir obsidyen ayna bulur. Aynaya dokunduğunda 9.000 yıl öncesine gider. Kapısız evler, çatıdan girişler, duvar resimleri, obsidyen aletler. Neolitik köy yaşamını keşfeder, kutsal odadaki aynanın yerini bulur, köy halkına yardım eder ve günümüze döner.

**BAŞLIK:** Kitap adı "[Çocuk adı]'ın Çatalhöyük Macerası" olmalı. Alt başlık EKLEME.

**KARAKTER:** {child_name} ({child_age} yaşında, {child_gender}). Yardımcı: {animal_friend} (her sayfada AYNI görünüm — DEĞİŞTİRME).

**KARAKTER ARC — İÇ YOLCULUK:**
{child_name} başta yeni yerlerden çekiniyor — kazı alanı ıssız ve biraz ürkütücü, derin çukurlar var.
{animal_friend} yanına gelince rahatlar ama büyük kararları henüz kendisi alamıyor.
Macera boyunca adım adım cesaret kazanır: önce {animal_friend}'ın desteğiyle (çatıya tırmanma), sonra KENDİ KARARIYLA (aynayı kutsal odaya yerleştirme).
Hikayenin sonunda {child_name} gözlerinde artık çekingenlik değil, parlak bir ışık var — ama bu DEĞİŞİM ASLA SÖYLENMEZ, sadece EYLEMLERİYLE hissettirilir.

**YASAK:** Korku/şiddet YASAK. Büyü/sihir YOK — ayna doğal bir zaman anomalisi. Didaktik nasihat YASAK.

---

### Bölüm 1 — Kazı Alanı (Sayfa 1-4) 🎯 Duygu: MERAK + hafif TEDİRGİNLİK
- {child_name} Çatalhöyük arkeolojik kazı alanına gelir. 🔊 Rüzgar bozkırdan esiyor, kuru toprak ve sıcak taş kokusu. Toprak duvarlar, eski temel kalıntıları. Biraz çekiniyor — derin çukurlar var, etraf ıssız.
- {animal_friend} kazı alanının kenarında belirir! Kuyruk sallayarak / merakla {child_name}'e yaklaşır. "Sen de mi burayı merak ediyorsun?" diye gülümser {child_name}. {animal_friend} burnunu eline sürtüyor.
- Birlikte dolaşırken {animal_friend} bir çukura atlar ve bir şeye bakar — parıldayan siyah bir taş! {child_name} eğilip alır: küçük, cilalı bir obsidyen ayna. "Bu çok eski görünüyor..." Üzerindeki yansıma tuhaf, titreşiyor.
- {child_name} parmağını aynaya dokunduruyor — 🔊 derin bir uğultu, etraf bulanıklaşıyor! {animal_friend} hemen yanına sokuluyor. Gözlerini açtığında HER ŞEY DEĞİŞMİŞ...
🪝 HOOK: Etraf bambaşka — bu neresi?

---

### Bölüm 2 — Çatıdan Giren Evler (Sayfa 5-9) 🎯 Duygu: ŞAŞKINLIK → HEYECAN
- Etrafta sıralı kerpiç evler — ama KAPI YOK! Herkes çatılardan tahta merdivenleri kullanarak giriyor. "Bu evlerin kapısı yok!" diye haykırır {child_name}. {animal_friend} şaşkınlıkla kulağını dikip etrafa bakıyor.
- Bir evin çatısına tırmanması gerekiyor — {child_name} bir an tereddüt eder. Ama {animal_friend} çoktan tırmanmış, yukarıdan bakıp havlayarak / miyavlayarak cesaret veriyor! {child_name} gülümseyerek merdivene yapışıyor.
- İçeri baktığında hayranlıkla duraksıyor: duvarlarda kırmızı ve siyah boyayla çizilmiş av sahneleri! Küçük bir ocak, yanında tahıl sepetleri. 🔊 Ocağın çıtırdama sesi ve hamurun taze kokusu. ✋ Duvarın yüzeyine dokunuyor — sıcak, pürüzlü, toprak hissedilen kerpiç.
- Neolitik çocuklarla karşılaşma! Obsidyen aletlerle bir şeyler yapıyorlar. Bir çocuk {child_name}'e yaklaşıp avuçlarında küçük bir ekmek parçası uzatıyor — tadı basit ama sıcak ve buğdaylı. {animal_friend} de payını istiyor! 😂
- {animal_friend} muhteşem bir boğa başı kabartmasının önünde durup başını eğerek bakıyor — sanki saygı duyuyor! {child_name} kahkahayla güler: "Sen sanat eleştirmeni misin?"
🪝 HOOK: Ama bu köyde bir şeyler eksik — yaşlı kadının endişeli yüzü ne anlama geliyor?

---

### Bölüm 3 — Boğa Kabartması ve Gizem (Sayfa 10-14) 🎯 Duygu: GİZEM → CESARET → ZAFER
- Büyük bir eve girerler — devasa boğa başı kabartması iki yanı süslüyor. Kutsal bir yer olduğu hissediliyor. 🔊 İçeride derin bir sessizlik var, sadece uzaktan çocukların sesleri.
- Yaşlı bir kadın duvara kırmızı toprağıyla resim yapıyor — {child_name} büyülenmiş gibi izliyor. "Nasıl bu kadar güzel çizebiliyorsunuz?" der sessizce. Kadın gülümseyip elini uzatıyor, {child_name}'e toprak boyayı gösteriyor.
- Ama kadının yüzünde endişe var — kutsal odadaki özel nişte bir boşluk! Bir şey eksik. {child_name} avucundaki obsidyen aynaya bakıyor — AYNI BOYUT, AYNI ŞEKİL! "Bu... buraya mı ait?"
- {child_name} bu sefer TEREDDÜT ETMİYOR. Aynayı uzanıp gediğe YERLEŞTİRİYOR. 🔊 Duvardaki boyalar bir an parıldıyor! Kadın hayret içinde gülümsüyor.
- "Yerine koyduk!" diyor {child_name}, gözlerinde gurur. Köy halkı kutlama yapıyor — 🔊 el çırpma, neşeli sesler. {animal_friend} sevinçle dans ediyor!
🪝 HOOK: Ama artık geri dönme zamanı — ayna yerinde, geçiş kapanıyor olabilir!

---

### Bölüm 4 — Dönüş (Sayfa 15-18) 🎯 Duygu: VEDA → KAVRAYIŞ
- {animal_friend} geçiş noktasını gösteriyor — kazı alanına dönen bir ışık. "Geri dönme zamanı geldi," der {child_name} sessizce.
- Neolitik çocukla vedalaşma — çocuk küçük bir obsidyen parça hediye ediyor. {child_name} gülümseyerek alıyor: "Seni unutmayacağım."
- Işığa doğru yürürler. 🔊 Geçidin uğultusu ve sonra... sessizlik. Modern kazı alanında geri döndüler!
- {child_name} avucundaki obsidyen parçaya bakıyor. Sonra etrafa — vitrindeki kartta yazıyor: "Obsidyen ayna, M.Ö. 7000." Gözleri kocaman açılıyor. "Gerçekti!"
🪝 HOOK: 9.000 yıldır burada duran şeye az önce dokunmuştu...

---

### Bölüm 5 — Kapanış (Sayfa 19-22) 🎯 Duygu: HUZUR + GURUR
- Gün batımında kazı alanını son kez geziyor. 🔊 Ağustosböcekleri, uzakta bir çoban düdüğü. Altın ışık toprak duvarları boyuyor.
- {child_name} {animal_friend}'a bakıp parmağını dudağına koyuyor: "Bu bizim sırrımız." {animal_friend} anlayışla kuyruk sallıyor / başını {child_name}'in eline yasıyor.
- Avucundaki obsidyen parçayı sıkıyor. 🔊 Taşın pürüzsüz yüzeyi sıcakmış — güneşten mi, yoksa 9.000 yıllık bir hatıradan mı?
- Son adımını atarken ufka bakıyor. Gözlerinde artık çekingenlik yok — parlak, meraklı bir ışık var. "Bir dahaki macera nereye olacak acaba?"

---

## 🚫 KURALLAR
- AİLE karelerde GÖRÜNMESİN. Sahnelerde sadece {child_name} + {animal_friend}.
- {animal_friend} her sayfada AYNI görünüm — DEĞİŞTİRME.
- Obsidyen ayna bulunduktan sonra AYNI tasarım.
- Korku/şiddet/gore YASAK.

## ⚠️ YAZIM KURALLARI

❌ YANLIŞ (Gezi Rehberi): "{child_name} Çatalhöyük'e geldi. Çatalhöyük dünyanın en eski yerleşim yerlerinden biridir ve M.Ö. 7500'e tarihlenir."
✅ DOĞRU (Macera): "{child_name}'in ayağı bir taşa takıldı — ama bu sıradan bir taş değildi. Yüzeyi ayna gibi parlıyordu!"

❌ YANLIŞ (Doğrudan Öğüt): "{child_name} insanların eskiden de sanat yaptığını öğrendi. Tarih çok önemliydi."
✅ DOĞRU (Subliminal): "{child_name} parmağını duvar resmine dokundurdu. 9.000 yıl önceki biri de tam buraya dokunmuştu."

## 💬 DİYALOG KURALI
Her 3-4 sayfada en az 1-2 kısa diyalog. {child_name} {animal_friend}'a konuşur, hayvan jest/ses ile tepki verir.

Hikayeyi TAM OLARAK {page_count} sayfa yaz. Her sayfa 2-4 cümle, akıcı ve macera dolu.
""",

    # ── F: Görsel Prompt Şablonları (genişletilmiş) ──
    cover_prompt_template=(
        'An {child_age}-year-old {child_gender} named {child_name} with {hair_description}, '
        'wearing {clothing_description}. {scene_description}. Ancient Neolithic Catalhoyuk mudbrick '
        'houses with rooftop entries and wooden ladders, bull head relief on wall. '
        'Golden sunset light on warm earthy tones. Low-angle hero shot: child 30% foreground, '
        'mudbrick village 70%. Rich palette: terracotta, ochre, warm brown, goldenhour. {STYLE}'
    ),
    page_prompt_template=(
        'An {child_age}-year-old {child_gender} named {child_name} with {hair_description}, '
        'wearing {clothing_description}. {scene_description}. '
        'EXTERIOR elements: [Catalhoyuk mudbrick houses, rooftop ladders, golden steppe, '
        'archaeological excavation trenches, dry grass]. '
        'INTERIOR elements: [Wall paintings (red-black hunting scenes, geometric patterns), '
        'bull head reliefs (bucrania), clay oven, grain baskets, obsidian tools]. '
        'ATMOSPHERIC: [warm earth tones, dust motes in shaft of light, mudbrick texture]. '
        'Shot variety: Wide establishing / Medium action / Close-up detail / Low angle hero. '
        'Color palette: terracotta, ochre, warm brown, cream, burnt sienna, golden hour glow. '
        'Cinematic warm lighting, detailed earthy texture. '
        'Dynamic pose, expressive emotion. No eye contact with camera. {STYLE}'
    ),

    # ── G: Kıyafetler ──
    outfit_girl=(
        "warm terracotta-colored cotton tunic dress with natural rope belt, "
        "cream linen leggings, soft brown leather ankle boots, "
        "small woven reed basket slung over shoulder, a braided leather headband. "
        "EXACTLY the same outfit on every page."
    ),
    outfit_boy=(
        "ochre-colored linen shirt with wooden button collar, "
        "dark brown cotton trousers tucked into soft leather moccasin boots, "
        "a woven jute crossbody bag, a small round leather cap. "
        "EXACTLY the same outfit on every page."
    ),

    # ── G2: Tutarlılık Kartları — SABİT companion ──
    companions=[
        CompanionAnchor(
            name_tr="Köpek",
            name_en="small playful sandy-brown village dog",
            species="dog",
            appearance="small playful sandy-brown village dog with floppy ears, a short wagging tail, warm brown eyes, and a dusty tan muzzle",
            short_name="Köy Köpeği",
        ),
    ],
    objects=[
        ObjectAnchor(
            name_tr="Obsidyen Ayna",
            appearance_en="small polished black obsidian mirror with iridescent sheen, palm-sized, smooth oval shape",
            prompt_suffix="holding polished black obsidian mirror — SAME appearance on every page",
        ),
    ],

    # ── H: Kültürel Elementler ──
    cultural_elements={
        "primary": [
            "Mudbrick houses without doors (rooftop entry via wooden ladders)",
            "Wall paintings (red-black hunting scenes, geometric patterns)",
            "Obsidian tools and polished mirrors",
            "Bull head reliefs (bucrania) on interior walls",
            "First agricultural settlements — grain, bread, pottery",
        ],
        "secondary": [
            "Grain storage baskets and clay ovens",
            "Ladders between rooftops — rooftop life",
            "Archaeological excavation site with trenches",
            "Natural earth pigments for wall painting (red ochre, charcoal)",
        ],
        "values": ["Curiosity", "Creativity", "Community", "Courage", "History appreciation"],
        "atmosphere": "Ancient, warm, communal, mysterious, archaeological wonder",
    },

    # ── C/G3: Lokasyon Kısıtları ──
    location_constraints=(
        "Pages 1-4: Çatalhöyük archaeological dig site, trenches, dry steppe. (Wide Shot, warm) "
        "Pages 5-9: Ancient Neolithic village — rooftop life, mudbrick interiors, wall paintings. (Medium Shot) "
        "Pages 10-14: Sacred room with bull reliefs, wall paintings, obsidian niche. (Close-up, warm light) "
        "Pages 15-18: Return transition, modern dig site. (Medium Shot, golden light) "
        "Pages 19-22: Modern dig site at sunset, steppe horizon. (Hero Shot, golden hour)"
    ),

    # ── I: Scenario Bible (genişletilmiş) ──
    scenario_bible={
        "companion_pack": {
            "kopek": {
                "species": "dog",
                "appearance_en": "small playful sandy-brown village dog with floppy ears and a short tail",
                "role": "Çocuğun sadık keşif arkadaşı, çukurlarda obje bulan, çatıya ilk tırmanan cesur dost",
            },
        },
        "key_objects": {
            "obsidyen_ayna": {
                "appearance_en": "small polished black obsidian mirror with iridescent sheen, palm-sized",
                "first_page": 3,
                "last_page": 14,
                "prompt_suffix": "holding polished black obsidian mirror — SAME on every page",
            },
        },
        "side_characters": {
            "neolitik_cocuk": {
                "outfit_en": "young Neolithic child in simple cream-colored woven tunic with leather cord belt",
                "appears_on": [8, 9, 16, 17],
                "rule": "SAME outfit and appearance on every page",
            },
            "yasli_kadin": {
                "outfit_en": "elderly Neolithic woman in dark brown woven robe with red ochre stains on hands",
                "appears_on": [11, 12, 13, 14],
                "rule": "SAME outfit and appearance on every page",
            },
        },
        "location_zone_map": {
            "modern_dig_site": "pages 1-4, 15-22",
            "time_transition": "pages 4-5, 15",
            "ancient_village": "pages 5-14",
        },
        "consistency_rules": [
            "Companion dog MUST have EXACTLY the same sandy-brown color, floppy ears, and short tail on EVERY page",
            "Obsidian mirror MUST have the same black iridescent surface on pages 3-14",
            "Child's modern outfit MUST NOT change between time periods",
            "Neolithic characters MUST wear the same woven tunic on every appearance",
            "Wall paintings MUST use same red-black color scheme in all interior scenes",
        ],
    
        "companions": "see_scenario_companions_list",
        "locations": "see_location_constraints",
    },

    # ── J: Custom Inputs — SABİT companion ──
    custom_inputs_schema=[
        {
            "key": "animal_friend",
            "type": "hidden",
            "default": "Köpek",
        },
    ],
))
