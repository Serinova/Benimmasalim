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

    # ── E: Hikaye Promptu (iyileştirilmiş — ~650 kelime) ──
    story_prompt_tr="""\
# KAPADOKYA MACERASI — PERİ BACALARININ SIRRI

## YAPI: {child_name} TEK BAŞINA, AİLE YOK. Yanında sadece {animal_friend}.

**KRİTİK — METİN UZUNLUĞU:** Her sayfa 1-3 cümle, toplam 25-50 kelime. Kısa tut, sayfaya sığsın.

**KARAKTER:** {child_name} ({child_age} yaşında, {child_gender}). Yardımcı: {animal_friend} (her sayfada aynı görünüm — DEĞİŞTİRME).

**KARAKTER ARC — İÇ YOLCULUK:**
{child_name} başta biraz çekingen ve yalnız bir çocuk. Yeni yerlerden, karanlık alanlardan tedirgin.
Macera boyunca adım adım cesaret kazanır: önce {animal_friend}'ın yardımıyla, sonra KENDİ BAŞINA.
Hikayenin sonunda {child_name} artık gözleri parlayan, kendine güvenen bir çocuk — ama bu DEĞİŞİM ASLA SÖYLENMELİ, sadece EYLEMLERİYLE hissettirilmeli.

**YASAK:** Anne, baba, aile üyesi, gezi rehberi, yetişkin YOK. "NO ADULTS" kuralı: sahnede sadece çocuk + hayvan arkadaş. Büyü, sihir, peri yok — gerçekçi macera.

**AKIŞ (6 BÖLÜM):**

### BÖLÜM 1 — Keşif Çağrısı (Sayfa 1-3) 🎯 Duygu: MERAK + hafif TEDİRGİNLİK
- {child_name} Göreme vadisinde yürüyor, peri bacalarını keşfediyor.
- {animal_friend} ile tanışma — hayvan bir kaya oyuğundan çıkıyor, {child_name} önce korkuyor ama hayvan ona yaklaşınca gülümsüyor.
- Bir peri bacasının duvarında garip semboller (at, kuş, güneş) fark ediyorlar. {animal_friend}: "Gel, bak şuna!" der gibi başıyla işaret ediyor.
- 🔊 Rüzgar peri bacalarının arasından uğuldayarak geçiyor. Toprak nemli ve baharatlı kokuyor.

### BÖLÜM 2 — Yeraltı Dünyası (Sayfa 4-8) 🎯 Duygu: HEYECAN → hafif KORKU
- Sembolleri takip ederek Derinkuyu yeraltı şehrinin gizli girişini buluyorlar.
- {child_name} karanlık girişte tereddüt ediyor — {animal_friend} cesaretlendiriyor: önden gidiyor, dönüp bakıyor.
- Dar tünellerde ilerliyor, taş kapılar açıyor. "Bunlar ne kadar ağır!" diye fısıldıyor.
- 🔊 Adım sesleri taş duvarlara yankılanıyor. Hava serin ve nemli toprak kokuyor.
- Eski bir odada duvar resimleri (freskler) buluyorlar — at, kuş, güneş motifleri.
- Fresklerin arasında bir harita keşfediliyor — Göktürk madalyonunun yeri işaretli.
- Tuzaklı bir geçit — {animal_friend} tehlikeyi sezdiğinde çocuğu uyarıyor.
- 🪝 HOOK: "Ama haritadaki son işaret karanlığın en derinini gösteriyordu..."

### BÖLÜM 3 — Madalyon (Sayfa 9-12) 🎯 Duygu: GERİLİM → CESARET → ZAFER
- Haritayı takip ederek gizli bir odaya ulaşıyorlar. {child_name} derin nefes alıp karanlığa adım atıyor — bu sefer KENDİ kararı.
- Göktürk Madalyonu burada: altın rengi, güneş motifli, avuç içi büyüklüğünde, deri kordonlu.
- "Bu gerçek..." fısıldıyor {child_name}, elleri titriyor ama gözleri parlıyor.
- Madalyonu aldığında tüneller sallanıyor — acele çıkış gerekiyor!
- {animal_friend} kısa yolu biliyor, çıkışa yönlendiriyor. {child_name} koşarken madalyonu sıkıca tutuyor.

### BÖLÜM 4 — Gökyüzü Macerası (Sayfa 13-16) 🎯 Duygu: ŞAŞkınlık → SEVİNÇ
- Yeraltından çıkınca Kapadokya'nın muhteşem manzarası — sabah ışığı gözlerini kamaştırıyor.
- 🔊 Balonların alev sesi — "Fşşşş!" — gökyüzüne yükseliyorlar. {child_name}: "İnanılmaz!" diye haykırıyor.
- Sıcak hava balonlarıyla dolu gökyüzü (sabah saatleri, altın ışık). {animal_friend} balonlara şaşkınlıkla bakıyor.
- Balonla uçuş: Kapadokya vadileri kuşbakışı, peri bacaları aşağıda minicik.
- {child_name}: "Bak! Girişi oradan bulmuştuk!" diye aşağıyı gösteriyor. Rüzgar saçlarını savuruyor.
- 🪝 HOOK: "Ama madalyon cebinde garip bir şekilde ısınmaya başlamıştı..."

### BÖLÜM 5 — Sırrın Çözümü (Sayfa 17-19) 🎯 Duygu: MERAK → KAVRAYIŞ → GURUR
- Madalyonun üzerindeki semboller güneş ışığına tutulunca parıldıyor.
- Her sembol Kapadokya'nın farklı bir dönemini anlatıyor: Hitit, Roma, Bizans, Selçuklu, Osmanlı.
- {animal_friend} ile birlikte sembolü deşifre ediyorlar — madalyon bir "koruyucu mühür."
- {child_name} madalyonu göğsüne bastırıyor: "Bu sadece altın bir şey değil" diyor, "bu bir söz."

### BÖLÜM 6 — Dönüş ve Gurur (Sayfa 20-22) 🎯 Duygu: HUZUR + GURUR
- Gün batımında Göreme'ye dönüş. 🔊 Güvercinler uçuşuyor, uzaktan ezan sesi.
- Madalyonu güvenli bir yerde saklıyor (bir peri bacasının oyuğunda, gelecek nesiller bulsun diye).
- {animal_friend} ile vedalaşma — hayvan burnunu çocuğun eline değdiriyor. {child_name} gülümsüyor: "Seni unutmayacağım."
- {child_name} vadiye son kez bakıyor. Gözlerinde artık tedirginlik değil, parlak bir ışık var. Madalyon cebinde sıcacık.

---

## 🚫 KURALLAR
- AİLE/YETİŞKİN YOK. Sahnelerde sadece {child_name} + {animal_friend}. Baloncu kısa, dolaylı.
- Büyü/sihir YOK. Madalyon tarihi bir obje, sihirli değil.
- {animal_friend} her sayfada AYNI görünüm — renk, boyut, ayırt edici özellik DEĞİŞMEZ.
- Madalyon bulunduktan sonraki her sayfada görünmeli — AYNI tasarım.
- İlk sayfa [Sayfa 1] ile başla. Uçak/yolculuk sahnesi YOK.

## ⚠️ YAZIM KURALLARI

❌ YANLIŞ (Gezi Rehberi): "{child_name} Göreme vadisini gördü. Vadi volkanik kayalardan oluşmuştur. Sonra Derinkuyu'ya gitti."
✅ DOĞRU (Macera): "{child_name}'in ayağının altındaki toprak titredi — kaya duvarın arkasında bir boşluk vardı!"

❌ YANLIŞ (Doğrudan Öğüt): "{child_name} cesaretin önemini anlamıştı. Bu macera ona çok şey öğretmişti."
✅ DOĞRU (Subliminal): "{child_name} derin nefes aldı ve karanlığa ilk adımını attı. Elleri artık titremiyordu."

## 💬 DİYALOG KURALI
Her 3-4 sayfada en az 1 kısa diyalog olmalı. {child_name} ile {animal_friend} arasında jest, ses, bakış üzerinden iletişim kur. Companion konuşamaz ama çocuk ona konuşur ve hayvan tepki verir.

Hikayeyi TAM OLARAK {page_count} sayfa yaz. Her sayfa 1-3 cümle (25-50 kelime).
""",

    # ── F: Görsel Prompt Şablonları (iyileştirilmiş) ──
    cover_prompt_template=(
        'Story "{book_title}". A young child standing heroically atop a fairy chimney rock '
        'in Cappadocia, wearing {clothing_description}. {scene_description}. '
        'Panoramic Cappadocia valley with dozens of fairy chimneys, hot air balloons floating '
        'in golden sunrise sky. Warm earth tones — ochre, terracotta, cream. '
        'Dramatic cinematic low-angle hero shot, child in foreground 30%, '
        'landscape filling background 70%. Space for title at top.'
    ),
    page_prompt_template=(
        'A young child {scene_description}, wearing {clothing_description}. '
        'Setting elements (choose relevant based on scene): '
        'EXTERIOR: [fairy chimney rock formations, Goreme valley panorama, hot air balloons, '
        'volcanic tuff pillars, dusty hiking trail, golden sunrise/sunset light]. '
        'INTERIOR: [Derinkuyu underground tunnels, carved stone rooms, ancient frescoes on walls, '
        'narrow stone doorways, carved ventilation shafts with dim light]. '
        'ATMOSPHERIC: [warm golden light filtering through rock, dust particles in sunbeams, '
        'cool blue underground shadows, distant balloon silhouettes, wind-swept landscape]. '
        'Shot variety: [close-up detail / medium action / wide epic / interior moody / aerial panoramic]. '
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
            appearance="small reddish-orange Cappadocian fox with fluffy tail, bright green eyes, and white chest patch",
            short_name="Tilki",
        ),
        CompanionAnchor(
            name_tr="Cesur Dağ Kartalı",
            name_en="brave mountain eagle",
            species="eagle",
            appearance="brave dark brown mountain eagle with wide wingspan and piercing golden eyes",
            short_name="Kartal",
        ),
        CompanionAnchor(
            name_tr="Sevimli Step Tavşanı",
            name_en="small sandy-brown steppe rabbit with long ears",
            species="rabbit",
            appearance="small sandy-brown steppe rabbit with long ears and white cotton tail",
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

    # ── C/G3: Lokasyon Kısıtları ──
    location_constraints=(
        "Pages 1-3: Göreme Valley, fairy chimneys, open landscape (Wide Shot, golden light). "
        "Pages 4-8: Derinkuyu underground city — narrow stone tunnels, carved rooms, frescoes (Low light, Close-up). "
        "Pages 9-12: Hidden chamber, medallion discovery, tunnel escape (Dramatic light, Medium Shot). "
        "Pages 13-16: Above ground, hot air balloon ride, aerial Cappadocia views (Wide panoramic, sunrise). "
        "Pages 17-19: Open air, examining medallion in sunlight, historical revelation (Close-up + Wide). "
        "Pages 20-22: Göreme sunset, farewell scene (Hero Shot, warm golden glow)."
    ),

    # ── I: Scenario Bible ──
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
            },
        ],
        "locations": [
            "Goreme Valley fairy chimneys at sunrise",
            "Derinkuyu Underground City dark tunnels with stone walls",
            "Ancient carved stone door with horse, bird, sun symbols",
            "Hidden fresco room with colorful ancient wall paintings",
            "Hot air balloon basket high above Cappadocia valleys",
            "Goreme landing field at sunset",
        ],
        "no_family": True,
        "no_magic": True,
        "child_solo": True,
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
