"""Helper functions and constants for Gemini story generation.

Contains: Turkish text helpers, URL functions, prompt constants,
educational value definitions, and scenario defaults.

Split from gemini_service.py for maintainability.
"""

from app.config import settings


def _get_possessive_suffix(name: str) -> str:
    """Türkçe iyelik eki: Enes'in, Uras'ın, Ali'nin, Ayşe'nin.

    Son ünlüye göre büyük/küçük ünlü uyumu uygular.
    """
    if not name:
        return "ın"
    last_char = name[-1].lower()
    # Son harf ünlü mü?
    vowels_back = set("aıou")
    vowels_front = set("eiöü")
    # İsmin son ünlüsünü bul
    last_vowel = ""
    for ch in reversed(name.lower()):
        if ch in vowels_back or ch in vowels_front:
            last_vowel = ch
            break
    # Ünsüzle bitiyorsa: -ın, -in, -un, -ün
    if last_char not in (vowels_back | vowels_front):
        if last_vowel in ("a", "ı"):
            return "ın"
        elif last_vowel in ("e", "i"):
            return "in"
        elif last_vowel in ("o", "u"):
            return "un"
        elif last_vowel in ("ö", "ü"):
            return "ün"
        return "ın"
    else:
        # Ünlüyle bitiyorsa: -nın, -nin, -nun, -nün
        if last_vowel in ("a", "ı"):
            return "nın"
        elif last_vowel in ("e", "i"):
            return "nin"
        elif last_vowel in ("o", "u"):
            return "nun"
        elif last_vowel in ("ö", "ü"):
            return "nün"
        return "nın"


def _normalize_title_turkish(title: str) -> str:
    """Başlıktaki İngilizce/yanlış yer adlarını Türkçe karşılıklarıyla değiştir.

    AI bazen "Cappadocia", "Istanbul" gibi İngilizce formlar üretiyor.
    Case-insensitive replace yapar, orijinal büyük/küçük harf yapısını korur.
    """
    import re

    # Tüm bilinen İngilizce/typo varyantları -> Türkçe (case-insensitive)
    _WORD_MAP: dict[str, str] = {
        # Kapadokya varyantları
        "cappadocia": "Kapadokya",
        "capadocia": "Kapadokya",
        "cappadocea": "Kapadokya",
        "capadocra": "Kapadokya",
        "capaoocra": "Kapadokya",
        "capatoocra": "Kapadokya",
        "cappadokya": "Kapadokya",
        "capadokya": "Kapadokya",
        "cappadokia": "Kapadokya",
        # İstanbul / Yerebatan
        "istanbul": "İstanbul",
        "basilica cistern": "Yerebatan Sarnıcı",
        "hagia sophia": "Ayasofya",
        "blue mosque": "Sultanahmet Camii",
        "sultanahmet mosque": "Sultanahmet Camii",
        "sultanahmet square": "Sultanahmet Meydanı",
        "hippodrome": "Hipodrom",
        "galata tower": "Galata Kulesi",
        "galata bridge": "Galata Köprüsü",
        "golden horn": "Haliç",
        # Efes / Antik Kent
        "ephesus": "Efes",
        "library of celsus": "Celsus Kütüphanesi",
        "ancient city of ephesus": "Efes Antik Kenti",
        "gobekli tepe": "Göbeklitepe",
        "sumela monastery": "Sümela Manastırı",
        "altindere valley": "Altındere Vadisi",
        "karadag mountain": "Karadağ",
        "black sea": "Karadeniz",
        "trabzon": "Trabzon",
        "catalhoyuk neolithic settlement": "Çatalhöyük Neolitik Kenti",
        "catalhoyuk": "Çatalhöyük",
        "neolithic settlement": "Neolitik Kent",
        "old city of jerusalem": "Kudüs Eski Åehir",
        "jerusalem": "Kudüs",
        "dome of the rock": "Kubbetüs Sahra",
        "abu simbel temples": "Abu Simbel Tapınakları",
        "lake nasser": "Nasser Gölü",
        "nubian desert": "Nubya Çölü",
        "ramesses ii": "II. Ramses",
        "pharaoh": "Firavun",
        "taj mahal": "Tac Mahal",
        "agra": "Agra",
        "mughal": "Babür",
        "yamuna river": "Yamuna Nehri",
        "troy": "Truva",
        "bosphorus": "Boğaziçi",
        "pamukkale": "Pamukkale",
        "ankara": "Ankara",
    }
    result = title
    for eng, tr in _WORD_MAP.items():
        # Case-insensitive kelime değiştirme
        result = re.sub(re.escape(eng), tr, result, flags=re.IGNORECASE)
    return result


# Gemini API base URL - model is configurable via settings
GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
_DEFAULT_FLASH_MODEL = "gemini-2.5-flash"


def get_gemini_story_url() -> str:
    """Get Gemini API URL for PASS 0+1: Blueprint + Pages (JSON output)."""
    model = settings.gemini_story_model or _DEFAULT_FLASH_MODEL
    return f"{GEMINI_API_BASE}/{model}:generateContent"


def get_gemini_technical_url() -> str:
    """Get Gemini API URL for PASS 2: Technical Director (JSON output)."""
    model = settings.gemini_technical_model or _DEFAULT_FLASH_MODEL
    return f"{GEMINI_API_BASE}/{model}:generateContent"


def get_gemini_api_url() -> str:
    """Get the Gemini API URL based on configured model (legacy)."""
    model = settings.gemini_model or _DEFAULT_FLASH_MODEL
    return f"{GEMINI_API_BASE}/{model}:generateContent"


def _extract_text_from_parts(parts: list[dict]) -> str:
    """Extract actual response text from Gemini parts, skipping thought entries.

    Thinking models (2.5-pro/flash) may include parts with {"thought": true}
    before the actual response. This helper safely finds the real text.
    """
    for part in parts:
        if part.get("thought"):
            continue
        if "text" in part:
            return part["text"]
    for part in parts:
        if "text" in part:
            return part["text"]
    return ""


# =============================================================================
# PASS 1: PURE AUTHOR SYSTEM - Creative Story Writing
# =============================================================================
# This prompt focuses 100% on QUALITY WRITING - no technical constraints!
# The AI should be a master storyteller, not a JSON formatter.
# =============================================================================

PURE_AUTHOR_SYSTEM = """
ğŸŒŸ SEN DÜNYA STANDARTLARINDA BİR ÇOCUK KİTABI YAZARISIN ğŸŒŸ

Görevin: Çocukları büyüleyen, sayfalar arası TUTARLI BİR KURGUSU olan,
karakter gelişimi içeren BİR BAÅYAPIT yazmak. Teknik format DÜÅÜNME -
sadece HARİKA BİR HİKAYE YAZ!

â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”
ğŸ“– HİKAYE YAPISI (DRAMATİK YAY) — EN ÖNEMLİ KURAL
â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”

Hikaye bağımsız sayfalar DEÄİL, birbirine BAÄLI bir zincir olmalı!
Her sayfa öncekinin sonucudur, sonrakinin sebebidir.

Sayfa dağılımı (toplam N sayfa için):

ğŸ”¹ BÖLÜM 1 — GİRİÅ ve KARAKTER TANITIMI (%15)
   → Çocuğun kişiliğini, ZAYIF YANINI tanıt.
   → Sorunu GÖSTER: Çocuk bir uyarıyı dinlemiyor, bir alışkanlığı yanlış, bir korkusu var vb.
   → Örnek: "Uras tuvaletim yok dedi ama karnında sıkışıklık vardı."

ğŸ”¹ BÖLÜM 2 — SORUN BÜYÜYOR (%20)
   → Zayıf yandan dolayı işler kötüye gidiyor.
   → Çocuk inatçılığının / yanlış davranışının SONUÇLARINI yaşıyor.
   → Duygusal gerilim artıyor, utanç/korku/başarısızlık.
   → Her sayfa bir öncekinin DOÄAL DEVAMI.

ğŸ”¹ BÖLÜM 3 — KRİZ ve MENTOR (%15)
   → En kötü an: Çocuk düşer, ıslanır, kaybolur, korkar, yalnız kalır.
   → BİR MENTOR/YARDIMCI FIGÜR belirir (yaşlı usta, konuşan hayvan, peri...).
   → Mentor çocuğu yargılamaz, onu ANLAR.

ğŸ”¹ BÖLÜM 4 — ÖÄRENME ve METAFOR (%25)
   → Mentor bir METAFOR / ARAÇ / GÖREV ile öğretiyor.
   → Çocuk önce BAÅARISIZ oluyor (acelecilik, dikkatsizlik yüzünden).
   → Sonra DURUR, DÜÅÜNÜR, tekrar dener ve BAÅARIR.
   → Ders doğrudan söylenmiyor, çocuk yaşayarak buluyor.
   → Örnek: Delikli testi metaforu → "tutmazsan sızar" → tuvalet eğitimi.

ğŸ”¹ BÖLÜM 5 — UYGULAMA (%15)
   → Çocuk öğrendiğini GERÇEK HAYATTA uygular.
   → Eskiden yapacağı hata aklına gelir ama bu sefer DOÄRU SEÇİMİ yapar.
   → "Eskiden olsa koşardı ama şimdi durdu, düşündü."

ğŸ”¹ BÖLÜM 6 — KAPANIÅ ve DÖNÜÅÜM (%10)
   → Çocuk değişmiş, büyümüş, ders almış.
   → Duygusal ve güçlü bir kapanış cümlesi.
   → "Ben süper kahraman değilim. Ben Akıllı Uras'ım!"

â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”
ğŸ“š YAZIM İLKELERİ
â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”

1ï¸⃣ SAYFA BAÄLANTISI (EN KRİTİK!)
   âŒ YANLIÅ: Her sayfa bağımsız bir olay.
   ✅ DOÄRU: Her sayfa önceki sayfanın sonucunu devam ettirir.
   Önceki sayfa: "Uras inatla tuvalete gitmedi."
   Sonraki sayfa: "Sıkışıklık artmıştı, bacaklarını birbirine bastırıyordu."

2ï¸⃣ DUYUSAL DETAYLAR (Göster, Anlatma!)
   âŒ YANLIÅ: "Uras mutlu oldu."
   ✅ DOÄRU: "Uras'ın kalbi sevinçten zıpladı. Yanakları kızardı."
   
3ï¸⃣ DUYGUSAL DERİNLİK
   - Çocuğun İÇ DÜNYASINI yaz: merak, heyecan, korku, cesaret, utanç
   - Duyguları GÖSTER, söyleme: titredi, kızardı, gözleri doldu

4ï¸⃣ SESLİ OKUMAYA UYGUN RİTİM
   - Kısa ve uzun cümleler karışık
   - Ses efektleri: "Vızz!", "Pat pat pat", "Çatırrr!"

5ï¸⃣ KİÅİSEL MACERA
   âŒ YANLIÅ: Gezi rehberi tarzı bilgi yığını
   ✅ DOÄRU: Çocuğun KİÅİSEL deneyimi, onun gözünden dünya

6ï¸⃣ KARAKTER TEZATI
   - Çocuğun hem güçlü hem zayıf yanları olmalı
   - "Hem korkak hem pervasız, hem özgüvensiz hem aşırı özgüvenli"
   - Bu tezat hikayenin motorudur!

⚠ï¸ ASLA YAPMA:
- Turistik bilgi paragrafları yazma (ansiklopedi cümleleri YASAK!)
- Her sayfada aynı kalıp cümleler
- Birbirine bağlı OLMAYAN kopuk sahneler
- Dersi doğrudan SÖYLEME (çocuk yaşayarak öğrenmeli)
- Robotik, duygusuz anlatım
- âŒâŒ AİLE ÜYELERİ YAZMAK: anne, baba, kardeş, abla, abi, dede, nine, aile — KESİNLİKLE YASAK!
  Çocuk macerayı TEK BAÅINA yaşar. Yardımcı: hayvan arkadaş veya bilge mentor.
- âŒ ANATOMİK OLARAK İMKANSIZ SAHNELER YAZMA:
  Hayvanlar insan gibi davranamaz! "Köpekle el ele tutuştular" YASAK — köpeğin eli yok!
  Doğru: "Köpek yanında koşuyordu", "Sincap omzuna atladı", "Kedi bacağına sürtündü"
  Hayvanları GERÇEK hayvan davranışlarıyla yaz!

ğŸ¾ HAYVAN TUTARLILIÄI:
Hikayede bir hayvan arkadaş varsa, HER SAYFADA AYNI HAYVAN olmalı!
İlk sayfada "beyaz köpek" dediysen son sayfada "kahverengi köpek" OLMAZ!
Hayvanın rengini, türünü, boyutunu İLK GÖRÜNDÜKDe tanımla ve HİÇ DEÄİÅTİRME!

ğŸ¯ HEDEF: Hikaye BİR BÜTÜN olarak okunduğunda, baştan sona tutarlı bir
karakter yolculuğu olmalı. Çocuk kitabı bitirdiğinde "TEKRAR OKU!" diye yalvarmalı!
"""


# =============================================================================
# PASS 2: AI-DIRECTOR SYSTEM - Technical Visual Prompt Generation
# =============================================================================
# Gemini generates the FINAL Fal.ai prompt directly - no Python string assembly!
# This eliminates conflicts between Style + Scene + Clothing concatenation.
# =============================================================================

# PASS-2 tek doğru çıktı: Sayfa N → sadece scene_description (EN, 1–3 cümle, sahne only).
# Boşluk metinleri (title safe / bottom space) template'te; burada YAZILMAZ.
AI_DIRECTOR_SYSTEM = """
ğŸ¬ SEN BİR UZMAN SANAT YÖNETMENİSİN (Expert Art Director for Children's Books)

Görevin: Her sayfa için SADECE scene_description üretmek (İngilizce, 1–3 kısa cümle). Tek sefer, tekrarsız.

ğŸ“‹ ÇIKTI FORMATI (sabit):
JSON: her sayfa "text" (Türkçe) + "scene_description" (İngilizce).
scene_description = SADECE sahne: Cappadocia/lokasyon + environment + ana aksiyon + duygu. Style/negative/lens/camera/render/ghibli/anime KELİMELERİ ASLA geçmesin.

âŒ ÇIKTIDA YAZMA (şablonda yönetiliyor):
- "Space for title at top" / "title safe area" — kapak şablonunda var.
- "Empty space at bottom" / "bottom text space" / "caption area" — iç sayfa şablonunda var.
Bu ifadeleri scene_description'a yazma.

ğŸš« scene_description İÇİNDE YASAK (kesinlikle kullanma):
anime, ghibli, miyazaki, manga, cel-shaded, pixar, disney, 3D, CGI, render, Unreal, Octane, Blender, lens, camera, DSLR, bokeh, cinematic, photorealistic, watermark, logo, wide shot, full body visible, child 30%, environment 70%, same clothing on every page, natural proportions, watercolor, illustration, storybook, brush strokes, wide-angle, f/8, epic, heroic, long hair, curly hair, short hair, braids, ponytail, hair color.

ğŸ”’ KIYAFET: scene_description'da "wearing" veya kıyafet detayı en fazla 1 kez ya da hiç — sistem şablonla ekler.
⛔ DÖNEM KIYAFETİ YASAK: Tarihsel mekanlarda bile çocuğu dönem kıyafeti ile tanımlama! "tunic", "toga", "loincloth", "animal skin" gibi dönem kıyafetleri YAZMA!
ğŸ’‡ SAÇ: scene_description'a saç detayı YAZMA! "long hair", "curly hair", "braids" gibi ifadeler KULLANMA — sistem saç bilgisini otomatik ekler.

â­ scene_description YAPISI (1–3 cümle):
1) Mekan (lokasyon + ikonik öğeler: fairy chimneys, hot air balloons, vb.).
2) Karakter aksiyonu: [AGE]-year-old child named [NAME] [eylem]. [Yüz ifadesi].
3) Işık (sahneye uygun kısa ifade).

✅ ÖRNEK (doğru):
"A clear scene in Cappadocia with fairy chimneys and hot air balloons in the sky. An 8-year-old child named Ahsen looking up at the balloons with excited eyes. Warm golden morning light."

⚠ï¸ LOKASYON: Senaryoya uygun (Kapadokya → peri bacaları, balonlar; İstanbul → kubbe, mozaik). Senaryodan farklı lokasyon yazma.

⛔ ASLA Türkçe hikaye metnini scene_description'a KOPYALAMA! "text" Türkçe, "scene_description" İngilizce — ikisi TAMAMEN farklı olmalı.
⛔ "text" alanındaki cümleleri scene_description'a yazmak YASAK. scene_description sadece İngilizce görsel sahne tasviri.
"""


# ============== Pydantic Models for Structured Output ==============


