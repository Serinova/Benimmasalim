"""Kapadokya Macerası — Peri bacalarında keşif ve Göktürk madalyonu.

TİP A: Tek Landmark (Kapadokya bölgesi + Derinkuyu yeraltı şehri)
Companion: Yılkı atı (SABİT — kullanıcıya seçtirilmez)
Obje: Göktürk Madalyonu
"""

from app.scenarios._base import CompanionAnchor, ObjectAnchor, ScenarioContent
from app.scenarios._registry import register

CAPPADOCIA = register(ScenarioContent(
    # ── A: Temel Kimlik ──
    theme_key="cappadocia",
    name="Kapadokya Macerası",

    # ── B: Teknik ──
    location_en="Cappadocia",
    default_page_count=22,
    flags={"no_family": True},

    # ── E: Hikaye Promptu (güçlendirilmiş — ~800 kelime) ──
    story_prompt_tr="""\
# KAPADOKYA MACERASI — PERİ BACALARININ SIRRI

## YAPI: {child_name} TEK BAŞINA, AİLE YOK. Yanında sadece {animal_friend}.

**KRİTİK — METİN UZUNLUĞU:** Her sayfa 1-3 cümle, toplam 25-50 kelime. Kısa tut, sayfaya sığsın.

**KARAKTER:** {child_name} ({child_age} yaşında, {child_gender}). Yardımcı: {animal_friend} — bu bir HAYVAN (at, tilki, kartal veya tavşan). Asla kelebek, peri veya sihirli yaratık DEĞİL. Her sayfada aynı görünüm — DEĞİŞTİRME.

**KARAKTER ARC — İÇ YOLCULUK:**
{child_name} başta biraz çekingen ve yalnız bir çocuk. Yeni yerlerden, karanlık alanlardan tedirgin.
Macera boyunca adım adım cesaret kazanır: önce {animal_friend}'ın yardımıyla, sonra KENDİ BAŞINA.
Hikayenin sonunda {child_name} artık gözleri parlayan, kendine güvenen bir çocuk — ama bu DEĞİŞİM ASLA SÖYLENMELİ, sadece EYLEMLERİYLE hissettirilmeli.

**KRİTİK OBJE:** Hikayedeki tek önemli obje "GÖKTÜRK MADALYONU"dur — altın rengi, güneş motifli, avuç içi büyüklüğünde, deri kordonlu. Bu objeyi ASLA "küre", "kristal", "taş" veya başka bir şeye dönüştürme. Her bahsettiğinde ADI ile an: "Göktürk Madalyonu".

## ⛔ MUTLAK YASAKLAR (BU KURALLARI ÇİĞNEME!)
- Anne, baba, aile üyesi, gezi rehberi, yetişkin YOK.
- BÜYÜ/SİHİR MUTLAK YASAK: Levitasyon (havaya yükselme), uçma, ışınlanma, sihirli ışıklar, parlayan küreler, enerji yayan objeler, havada asılı adacıklar, sihirli ağaçlar YASAK.
- {animal_friend} bir HAYVAN. Kelebek, peri, melek, sihirli yaratık YASAK.
- Göktürk Madalyonu tarihi bir obje. Sihirli güçleri YOKTUR — parlamaz, enerji yaymaz, havaya kaldırmaz.
- Orman, tropikal ada, kristal mağara, büyülü dünya GİBİ KAPADOKYA DIŞI MEKANLAR YASAK. HER SAHNE Kapadokya'da geçmeli.

**AKIŞ (6 BÖLÜM):**

### BÖLÜM 1 — Keşif Çağrısı (Sayfa 1-3) 🎯 Duygu: MERAK + hafif TEDİRGİNLİK
🌍 MEKAN: Göreme Vadisi, peri bacaları, açık hava. GERÇEKÇİ sahne.
- {child_name} Göreme vadisinde yürüyor, peri bacalarını keşfediyor.
- {animal_friend} ile tanışma — hayvan bir kaya oyuğundan çıkıyor, {child_name} önce korkuyor ama hayvan ona yaklaşınca gülümsüyor.
- Bir peri bacasının duvarında garip semboller (at, kuş, güneş) fark ediyorlar. {animal_friend} başıyla işaret ediyor.
- 🔊 Rüzgar peri bacalarının arasından uğuldayarak geçiyor. Toprak nemli ve baharatlı kokuyor.

### BÖLÜM 2 — Yeraltı Dünyası (Sayfa 4-8) 🎯 Duygu: HEYECAN → hafif KORKU
🌍 MEKAN: Derinkuyu yeraltı şehri — taş tüneller, oyma odalar. GERÇEKÇİ sahne.
- Sembolleri takip ederek Derinkuyu yeraltı şehrinin gizli girişini buluyorlar.
- {child_name} karanlık girişte tereddüt ediyor — {animal_friend} cesaretlendiriyor: önden gidiyor, dönüp bakıyor.
- Dar tünellerde ilerliyor, taş kapılar açıyor. "Bunlar ne kadar ağır!" diye fısıldıyor.
- 🔊 Adım sesleri taş duvarlara yankılanıyor. Hava serin ve nemli toprak kokuyor.
- Eski bir odada duvar resimleri (freskler) buluyorlar — at, kuş, güneş motifleri.
- Fresklerin arasında bir harita keşfediliyor — Göktürk Madalyonunun yeri işaretli.
- Tuzaklı bir geçit — {animal_friend} tehlikeyi sezdiğinde çocuğu uyarıyor.
- 🪝 HOOK: "Ama haritadaki son işaret karanlığın en derinini gösteriyordu..."

### BÖLÜM 3 — Madalyon (Sayfa 9-12) 🎯 Duygu: GERİLİM → CESARET → ZAFER
🌍 MEKAN: Derinkuyu gizli odası, tünel çıkışı. GERÇEKÇİ sahne. SİHİR YOK.
- Haritayı takip ederek gizli bir odaya ulaşıyorlar. {child_name} derin nefes alıp karanlığa adım atıyor.
- GÖKTÜRK MADALYONU burada: altın rengi, güneş motifli, avuç içi büyüklüğünde, deri kordonlu.
- "Bu gerçek..." fısıldıyor {child_name}, elleri titriyor ama gözleri parlıyor.
- Madalyonu aldığında tüneller DOĞAL OLARAK sallanıyor (deprem hissi) — acele çıkış gerekiyor!
- {animal_friend} kısa yolu biliyor, çıkışa yönlendiriyor. {child_name} koşarken madalyonu sıkıca tutuyor.

### BÖLÜM 4 — Gökyüzü Macerası (Sayfa 13-16) 🎯 Duygu: ŞAŞkınlık → SEVİNÇ
🌍 MEKAN: Kapadokya açık havası, sıcak hava balonları, peri bacaları manzarası. GERÇEKÇİ sahne.
- Yeraltından çıkınca Kapadokya'nın muhteşem manzarası — sabah ışığı gözlerini kamaştırıyor.
- 🔊 Balonların alev sesi — "Fşşşş!" — gökyüzüne yükseliyorlar (GERÇEK balon, sihir değil).
- Sıcak hava balonlarıyla dolu gökyüzü (sabah saatleri, altın ışık). {animal_friend} balonlara şaşkınlıkla bakıyor.
- Balondan kuşbakışı: Kapadokya vadileri, peri bacaları aşağıda minicik.
- {child_name}: "Bak! Girişi oradan bulmuştuk!" diye aşağıyı gösteriyor. Rüzgar saçlarını savuruyor.
- Balon yere iniyor. {child_name} Göktürk Madalyonunu çıkarıp güneşe tutuyor.

### BÖLÜM 5 — Sırrın Çözümü (Sayfa 17-19) 🎯 Duygu: MERAK → KAVRAYIŞ → GURUR
🌍 MEKAN: Göreme'de açık havada, peri bacaları arasında bir kaya üstünde. GERÇEKÇİ sahne. SİHİR YOK.
⚠️ BU BÖLÜMDE SİHİR/BÜYÜ ASLA YOK. Madalyon sihirli DEĞİL — tarihi bir obje.
- {child_name} güneş ışığında Göktürk Madalyonunu inceliyor. Sembolleri parmağıyla takip ediyor.
- Her sembol Kapadokya'nın farklı bir dönemini anlatıyor: Hitit, Roma, Bizans, Selçuklu, Osmanlı.
- {animal_friend} ile birlikte sembolü deşifre ediyorlar — madalyon bir "koruyucu mühür," sihirli DEĞİL, tarihi bir anı.
- {child_name} madalyonu göğsüne bastırıyor: "Bu sadece altın bir şey değil" diyor, "bu bir söz."

### BÖLÜM 6 — Dönüş ve Gurur (Sayfa 20-22) 🎯 Duygu: HUZUR + GURUR
🌍 MEKAN: Göreme vadisi, peri bacaları, gün batımı. GERÇEKÇİ sahne.
⚠️ BU BÖLÜMDE: Ağaç, orman, ada, kristal, ışık yayan objeler YASAK. Sahne Kapadokya'da.
- Gün batımında Göreme'ye dönüş. 🔊 Güvercinler uçuşuyor, uzaktan ezan sesi.
- {child_name} Göktürk Madalyonunu güvenli bir yerde saklıyor (bir peri bacasının oyuğunda, gelecek nesiller bulsun diye).
- {animal_friend} ile vedalaşma — hayvan burnunu çocuğun eline değdiriyor. {child_name} gülümsüyor: "Seni unutmayacağım."
- {child_name} Göreme vadisine son kez bakıyor, peri bacaları gün batımında altın rengi parıldıyor. Gözlerinde artık tedirginlik değil, gurur var.

---

## 🚫 KURALLAR (ÇİĞNERSEN HİKAYE REDDEDİLİR)
- AİLE/YETİŞKİN YOK. Sahnelerde sadece {child_name} + {animal_friend}.
- BÜYÜ/SİHİR KESİNLİKLE YOK. Madalyon tarihi bir obje, SİHİRLİ DEĞİL. Parlamaz, enerji yaymaz, havaya kaldırmaz.
- {animal_friend} bir HAYVAN. Kelebek, peri, melek, sihirli yaratık YASAK.
- Obje adı her zaman "Göktürk Madalyonu". Küre, kristal, taş DEĞİL.
- {animal_friend} her sayfada AYNI görünüm — renk, boyut, ayırt edici özellik DEĞİŞMEZ.
- Göktürk Madalyonu bulunduktan sonraki her sayfada görünmeli — AYNI tasarım.
- HER SAHNE KAPADOKYA'DA geçmeli — orman, ada, büyülü dünya YASAK.
- İlk sayfa [Sayfa 1] ile başla. Uçak/yolculuk sahnesi YOK.

## ⚠️ YAZIM KURALLARI

❌ YANLIŞ: "{child_name} Göreme vadisini gördü. Vadi volkanik kayalardan oluşmuştur."
✅ DOĞRU: "{child_name}'in ayağının altındaki toprak titredi — kaya duvarın arkasında bir boşluk vardı!"

❌ YANLIŞ: "{child_name} cesaretin önemini anlamıştı."
✅ DOĞRU: "{child_name} derin nefes aldı ve karanlığa ilk adımını attı. Elleri artık titremiyordu."

❌ MUTLAK YASAK: "Küre parladı", "ışık onu havaya kaldırdı", "sihirli bir ormanda buldu kendini"
✅ ZORUNLU: "Göktürk Madalyonunu güneşe tuttu", "peri bacalarının arasında yürüdü"

## 💬 DİYALOG KURALI
Her 3-4 sayfada en az 1 kısa diyalog olmalı. {child_name} ile {animal_friend} arasında jest, ses, bakış üzerinden iletişim kur. Companion konuşamaz ama çocuk ona konuşur ve hayvan tepki verir.

Hikayeyi TAM OLARAK {page_count} sayfa yaz. Her sayfa 1-3 cümle (25-50 kelime).
""",

    # ── F: Görsel Prompt Şablonları (güçlendirilmiş — tek çocuk + Kapadokya kilidi) ──
    cover_prompt_template=(
        'Story "{book_title}". EXACTLY ONE young child standing heroically atop a fairy chimney rock '
        'in Cappadocia, wearing {clothing_description}. {scene_description}. '
        'Panoramic Cappadocia valley with dozens of fairy chimneys, hot air balloons floating '
        'in golden sunrise sky. Warm earth tones — ochre, terracotta, cream. '
        'Dramatic cinematic low-angle hero shot, child in foreground 30%, '
        'landscape filling background 70%. Space for title at top. '
        'ONLY ONE CHILD in the scene, no duplicate children.'
    ),
    page_prompt_template=(
        'EXACTLY ONE young child {scene_description}, wearing {clothing_description}. '
        'IMPORTANT: Only ONE child in the entire image, no second child, no twin, no duplicate. '
        'Setting MUST be Cappadocia, Turkey — fairy chimneys, volcanic tuff formations, or underground tunnels. '
        'EXTERIOR elements: fairy chimney rock formations, Goreme valley, hot air balloons, '
        'volcanic tuff pillars, dusty trail, golden light. '
        'INTERIOR elements: Derinkuyu underground tunnels, carved stone rooms, ancient frescoes, '
        'narrow stone doorways, dim light from ventilation shafts. '
        'ATMOSPHERIC: warm golden light, dust particles in sunbeams, '
        'cool underground shadows, balloon silhouettes on horizon. '
        'NO forest, NO tropical island, NO crystal cave, NO magical glowing trees, NO floating islands. '
        'Shot variety: close-up / medium action / wide epic / interior moody / aerial panoramic. '
        'Composition: full body visible in action, warm earthy palette (ochre, terracotta, cream, golden). '
        'Text overlay space at bottom.'
    ),

    # ── G: Kıyafetler ──
    outfit_girl=(
        "warm coral-orange puffer vest over a cream long-sleeve cotton shirt, "
        "dark brown corduroy pants, sturdy tan hiking boots with red laces, "
        "small olive-green canvas backpack with brass buckles, "
        "a hand-knitted cream wool beanie with a small pompom. "
        "EXACTLY the same outfit on every page."
    ),
    outfit_boy=(
        "forest green quilted vest over a cream henley shirt, "
        "dark khaki cargo pants with side pockets, sturdy brown leather hiking boots, "
        "small olive-green canvas backpack with brass buckles, "
        "a rust-brown flat cap. "
        "EXACTLY the same outfit on every page."
    ),

    # ── G2: Tutarlılık Kartları ──
    companions=[
        CompanionAnchor(
            name_tr="Cesur Yılkı Atı",
            name_en="brave wild Cappadocian horse",
            species="wild horse",
            appearance="small brown wild Cappadocian horse with flowing dark mane, gentle dark eyes, and sturdy short legs",
            short_name="Yılkı",
        ),
        CompanionAnchor(
            name_tr="Sevimli Kapadokya Tilkisi",
            name_en="small reddish-orange Cappadocian fox",
            species="fox",
            appearance="small reddish-orange Cappadocian fox with fluffy tail, bright green eyes, white chest patch, and pointed alert ears",
            short_name="Tilki",
        ),
        CompanionAnchor(
            name_tr="Cesur Dağ Kartalı",
            name_en="brave mountain eagle",
            species="eagle",
            appearance="brave dark brown mountain eagle with wide powerful wingspan, piercing golden eyes, sharp curved beak, and white-tipped tail feathers",
            short_name="Kartal",
        ),
        CompanionAnchor(
            name_tr="Sevimli Step Tavşanı",
            name_en="small sandy-brown steppe rabbit with long ears",
            species="rabbit",
            appearance="small sandy-brown steppe rabbit with long upright ears, white cotton tail, bright curious dark eyes, and soft fluffy fur",
            short_name="Tavşan",
        ),
    ],
    objects=[
        ObjectAnchor(
            name_tr="Göktürk Madalyonu",
            appearance_en=(
                "ancient golden Gokturk medallion with carved sun symbol and small holes, "
                "palm-sized, hanging on a thin brown leather cord"
            ),
            prompt_suffix="holding ancient golden medallion with sun symbol — SAME appearance on every page",
        ),
    ],

    # ── H: Kültürel Elementler ──
    cultural_elements={
        "primary": [
            "fairy chimneys (peri bacaları)",
            "Derinkuyu underground city",
            "hot air balloons",
            "rock-carved churches with frescoes",
        ],
        "secondary": [
            "Göktürk sun symbol motifs",
            "wild Cappadocian horses (yılkı atları)",
            "ancient stone doors with carved symbols",
            "warm volcanic tuff rock formations",
        ],
        "colors": "warm earth tones — ochre, terracotta, cream, golden sunrise",
        "atmosphere": "mysterious, adventurous, ancient, warm",
    },

    # ── C/G3: Lokasyon Kısıtları (sıkılaştırılmış — ZORUNLU) ──
    location_constraints=(
        "CRITICAL: EVERY page MUST show recognizable Cappadocia geological features. "
        "NO forest, NO tropical island, NO crystal cave, NO magical glowing trees. "
        "Pages 1-3: Göreme Valley, fairy chimneys, open landscape (Wide Shot, golden light). "
        "Pages 4-8: Derinkuyu underground city — narrow stone tunnels, carved rooms, frescoes (Low light, Close-up). "
        "Pages 9-12: Hidden chamber deep underground, medallion discovery, tunnel escape (Dramatic light, Medium Shot). "
        "Pages 13-16: Above ground Cappadocia, hot air balloon ride over fairy chimneys, aerial valley views (Wide panoramic, sunrise). "
        "Pages 17-19: Open air on a rock in Göreme, examining medallion under sunlight with fairy chimneys in background (Close-up + Wide). "
        "Pages 20-22: Göreme valley sunset, farewell scene with peri bacaları silhouettes (Hero Shot, warm golden glow). "
        "FORBIDDEN SETTINGS: forest, tropical island, floating island, crystal cave, magical tree, enchanted garden."
    ),

    # ── I: Scenario Bible (güçlendirilmiş) ──
    scenario_bible={
        "companions": [
            {
                "name_tr": "Cesur Yılkı Atı",
                "name_en": "brave wild Cappadocian horse",
                "species": "wild horse",
                "appearance": "small brown wild Cappadocian horse with flowing dark mane",
            },
            {
                "name_tr": "Sevimli Kapadokya Tilkisi",
                "name_en": "small reddish-orange Cappadocian fox",
                "species": "fox",
                "appearance": "small reddish-orange Cappadocian fox with fluffy tail and bright green eyes",
            },
        ],
        "key_objects": [
            {
                "name_tr": "Göktürk Madalyonu",
                "appearance_en": "ancient golden Gokturk medallion with carved sun symbol, palm-sized, on leather cord",
                "prompt_suffix": "holding ancient golden medallion with sun symbol — SAME on every page",
                "NOT_ALLOWED": "sphere, crystal, orb, glowing ball — this is a FLAT MEDALLION",
            },
        ],
        "locations": [
            "Goreme Valley fairy chimneys at sunrise",
            "Derinkuyu Underground City dark tunnels with stone walls",
            "Ancient carved stone door with horse, bird, sun symbols",
            "Hidden fresco room with colorful ancient wall paintings",
            "Hot air balloon basket high above Cappadocia valleys",
            "Rock outcrop in Göreme Valley with peri bacaları background",
            "Goreme landing field at sunset with fairy chimney silhouettes",
        ],
        "FORBIDDEN_locations": [
            "forest", "tropical island", "floating island", "crystal cave",
            "magical tree", "enchanted garden", "underwater", "space",
        ],
        "no_family": True,
        "no_magic": True,
        "child_solo": True,

        "consistency_rules": [
            "Companion appearance must remain IDENTICAL across all pages",
            "Companion is a REAL ANIMAL (horse/fox/eagle/rabbit), NEVER butterfly/fairy/magical creature",
            "Child outfit must remain EXACTLY the same on every page",
            "Key objects maintain consistent appearance throughout — medallion is FLAT, not sphere",
            "NO MAGIC/SUPERNATURAL ELEMENTS: no levitation, no glowing orbs, no energy beams",
            "EVERY page background MUST show Cappadocia features (fairy chimneys, tuff formations, underground tunnels, or hot air balloons)",
            "ONLY ONE CHILD in every scene — no duplicate, no twin, no second child",
        ],
    },

    # ── J: Custom Inputs — SABİT companion (kullanıcıya seçtirilmez) ──
    custom_inputs_schema=[
        {
            "key": "animal_friend",
            "type": "hidden",
            "default": "Cesur Yılkı Atı",
        },
    ],
))
