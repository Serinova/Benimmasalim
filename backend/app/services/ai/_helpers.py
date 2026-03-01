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
# EDUCATIONAL VALUES INTEGRATION - The Heart of Every Story
# =============================================================================
# These values MUST drive the plot, not just be mentioned!
# =============================================================================

EDUCATIONAL_VALUE_PROMPTS = {
    # ============ NEW: Learning Outcome Categories ============
    # Eğitim & Doğa
    "doğa": {
        "theme": "DOÄA VE HAYVAN SEVGİSİ (Nature & Animal Love)",
        "instruction": """Çocuk DOÄAYI VE HAYVANLARI SEVMEYI ÖÄRENMELİ!
        - Bir hayvanla özel bir bağ kurmalı (kuş, tavşan, sincap, böcek...)
        - Doğanın güzelliklerini keşfetmeli: "Kelebeğin kanatları gökkuşağı gibi parlıyordu!"
        - Hayvana yardım etme fırsatı bulmalı: yaralı kuş, aç sincap, kaybolmuş yavru
        - Doğayı korumanın önemini anlamalı: "Bu orman herkesin evi"
        ÖRNEK SAHNE: Yaralı bir kuşu iyileştirip özgürlüğüne kavuşturur.""",
    },
    "doga ve hayvan sevgisi": {
        "theme": "DOÄA VE HAYVAN SEVGİSİ",
        "instruction": """Çocuk DOÄAYI VE HAYVANLARI SEVMEYI ÖÄRENMELİ!
        - Bir hayvanla dostluk kurmalı ve ona yardım etmeli
        - Doğanın güzelliklerini keşfetmeli ve korumanın önemini anlamalı
        - Hayvanlarla iletişim kurup onları anlamalı
        ÖRNEK SAHNE: Ormanda kaybolmuş bir yavru hayvanı ailesine kavuşturur.""",
    },
    "kitap": {
        "theme": "KİTAP OKUMA SEVGİSİ (Love of Reading)",
        "instruction": """Çocuk KİTAPLARIN BÜYÜLÜ DÜNYASINI KEÅFETMELİ!
        - Bir kitap okurken içine çekilmeli: "Sayfalar arasında kayboldu..."
        - Kitaptaki karakterlerle özdeşleşmeli
        - Okumanın verdiği bilgi ve hayal gücünün değerini anlamalı
        - Kitap sayesinde bir sorunu çözmeli
        ÖRNEK SAHNE: Eski bir kitaptaki haritayı takip ederek hazine bulur.""",
    },
    "kitap okuma sevgisi": {
        "theme": "KİTAP OKUMA SEVGİSİ",
        "instruction": """Çocuk kitapların büyülü dünyasını keşfetmeli!
        - Kitap okurken hayal gücü canlanmalı
        - Kitaptaki bilgi sayesinde bir macera çözmeli
        ÖRNEK SAHNE: Büyülü bir kitap onu fantastik bir dünyaya götürür.""",
    },
    "ekran": {
        "theme": "EKRAN SÜRESİ DENGESİ (Screen Time Balance)",
        "instruction": """Çocuk EKRAN DIÅINDA AKTİVİTELERİN KEYFİNİ KEÅFETMELİ!
        - Tablet/TV yerine doğada oynamanın eğlencesini bulmalı
        - Arkadaşlarla gerçek oyunların tadını çıkarmalı
        - Hayal gücüyle oynamanın zenginliğini keşfetmeli
        - Ekransız zamanın ne kadar değerli olduğunu anlamalı
        ÖRNEK SAHNE: Tableti bırakıp bahçede kelebek kovalar ve daha mutlu olur.""",
    },
    "ekran suresi dengesi": {
        "theme": "EKRAN SÜRESİ DENGESİ",
        "instruction": """Çocuk tablet/TV dışındaki aktivitelerin keyfini keşfetmeli!
        - Doğada oynamanın, arkadaşlarla oyunun tadını çıkarmalı
        ÖRNEK SAHNE: Ekranı kapatıp dışarıda harika bir macera yaşar.""",
    },
    "merak ve kesfetmek": {
        "theme": "MERAK VE KEÅFETMEK",
        "instruction": """Çocuk SORU SORMALI VE DÜNYAYI KEÅFETMELİ!
        - "Bu neden böyle?", "Nasıl çalışıyor?" soruları
        - Her köşede yeni bir keşif yapma heyecanı
        - Araştırarak öğrenmenin tadını çıkarmalı
        ÖRNEK SAHNE: Gizemli bir kapıyı merakla açar ve yeni bir dünya bulur.""",
    },
    "cevre temizligi": {
        "theme": "ÇEVRE TEMİZLİÄİ (Environmental Cleanliness)",
        "instruction": """Çocuk ÇEVREYİ TEMİZ TUTMANIN ÖNEMİNİ ÖÄRENMELİ!
        - Çöpü doğru yere atmanın önemini görmeli
        - Temiz bir çevrenin hayvanlar ve insanlar için değerini anlamalı
        - Çevreyi kirletmenin sonuçlarını görmeli
        - Temizlik kahramanı olmalı
        ÖRNEK SAHNE: Parkı temizleyerek hayvanların evini kurtarır.""",
    },
    # Öz Bakım
    "dis fircalama": {
        "theme": "DİÅ FIRÇALAMA ALIÅKANLIÄI",
        "instruction": """Çocuk DİÅ FIRÇALAMANIN ÖNEMİNİ ÖÄRENMELİ!
        - Diş fırçalamanın eğlenceli yanlarını keşfetmeli
        - Temiz dişlerin gücünü hissetmeli
        ÖRNEK SAHNE: Diş perisi ile tanışır ve dişlerinin önemini öğrenir.""",
    },
    "saglikli beslenme": {
        "theme": "SAÄLIKLI BESLENME",
        "instruction": """Çocuk SEBZE VE MEYVELERİN GÜCÜNÜ KEÅFETMELİ!
        - Sağlıklı yiyeceklerin verdiği enerjiyi hissetmeli
        - Sebze ve meyvelerin lezzetini keşfetmeli
        ÖRNEK SAHNE: Havuç yiyerek süper güç kazanır.""",
    },
    "duzenli uyku": {
        "theme": "DÜZENLİ UYKU",
        "instruction": """Çocuk VAKTİNDE UYUMANIN ÖNEMİNİ ÖÄRENMELİ!
        - Uykusuz kalmanın zorluğunu yaşamalı
        - İyi uykunun verdiği enerjiyi keşfetmeli
        ÖRNEK SAHNE: Rüyalar diyarında harika maceralar yaşar.""",
    },
    "tuvalet egitimi": {
        "theme": "TUVALET EÄİTİMİ / VÜCUDUNU DİNLEME",
        "instruction": """Çocuk VÜCUDUNUN SİNYALLERİNİ DİNLEMEYİ ve KONTROL etmeyi öğrenmeli!
        HİKAYE YAPI ÖNERİSİ:
        1) Çocuk tuvaletinin geldiğini hisseder ama oyunu/maceryı bölmek istemez → "Sonra yaparım" der.
        2) Sıkışıklık GİDEREK ARTAR — bacaklarını sıkar, zıplar, rahatsız olur.
        3) KRİZ ANI: Çok geç kalır → utanç verici bir durum yaşar (altına kaçırır, ıslanır).
        4) Bir MENTOR, metafor ile öğretir (örnek: delikli testi — tutmazsan sızar).
        5) Çocuk öğrenir: "Vücudum sinyal verdiğinde hemen gitmeliyim!"
        6) Tekrar tuvaleti gelir → bu sefer HEMEN gider → gurur duyar.
        âŒ YASAKLAR: Utandırıcı sahneleri AÅAÄI düşürücü yapma, NORMAL ve öğretici tut.
        ✅ MESAJ: "Vücudunu dinleyen çocuk en güçlü çocuktur."
        ÖRNEK METAFOR: Delikli bir testi → parmağını basmadan koşarsan su akar.""",
    },
    "el yikama": {
        "theme": "EL YIKAMA VE HİJYEN",
        "instruction": """Çocuk TEMİZLİK ALIÅKANLIKLARINI ÖÄRENMELİ!
        - El yıkamanın mikropları nasıl yok ettiğini görmeli
        - Temiz ellerin sağlık getirdiğini anlamalı
        ÖRNEK SAHNE: Ellerini yıkayarak görünmez mikrop canavarlarını yener.""",
    },
    # Sosyal Beceriler
    "paylasma": {
        "theme": "PAYLAÅMAK GÜZELDİR",
        "instruction": """Çocuk PAYLAÅMANIN MUTLULUÄUNU KEÅFETMELİ!
        - Sevdiği bir şeyi paylaşma fırsatı bulmalı
        - Paylaşmanın verdiği iç huzuru yaşamalı
        ÖRNEK SAHNE: Son kurabiyesini arkadaşıyla paylaşır ve daha mutlu olur.""",
    },
    "ozur dilemek": {
        "theme": "ÖZÜR DİLEMEK",
        "instruction": """Çocuk HATA YAPINCA ÖZÜR DİLEMEYİ ÖÄRENMELİ!
        - Bir hata yapıp üzülmeli
        - Özür dilemenin cesaretini göstermeli
        - Özür dilemenin ilişkileri nasıl düzelttiğini görmeli
        ÖRNEK SAHNE: Arkadaşını üzdükten sonra özür diler ve barışırlar.""",
    },
    "kardes sevgisi": {
        "theme": "KARDEÅ SEVGİSİ",
        "instruction": """Çocuk KARDEÅİYLE İYİ GEÇİNMEYİ ÖÄRENMELİ!
        - Kardeşiyle bir çatışma yaşamalı
        - Kardeşinin değerini anlamalı
        - Birlikte daha güçlü olduklarını keşfetmeli
        ÖRNEK SAHNE: Kardeşiyle birlikte çalışarak zor bir görevi başarır.""",
    },
    "arkadaslik kurmak": {
        "theme": "ARKADAÅLIK KURMAK",
        "instruction": """Çocuk YENİ ARKADAÅLAR EDİNMEYİ ÖÄRENMELİ!
        - Yeni biriyle tanışma fırsatı bulmalı
        - İlk adımı atmanın heyecanını yaşamalı
        - Arkadaşlığın değerini keşfetmeli
        ÖRNEK SAHNE: Çekingen bir çocuğa yaklaşır ve harika bir arkadaş kazanır.""",
    },
    # Kişisel Gelişim
    "cesaret ve ozguven": {
        "theme": "CESARET VE ÖZGÜVEN",
        "instruction": """Çocuk KORKULARINI YENMEYI VE KENDİNE GÜVENMEYI ÖÄRENMELİ!
        - Bir korkuyla yüzleşmeli
        - İçindeki cesareti keşfetmeli
        - "Ben yapabilirim!" demeli ve başarmalı
        ÖRNEK SAHNE: Yükseklik korkusunu yenerek zirveye ulaşır.""",
    },
    "sabirli olmak": {
        "theme": "SABIRLI OLMAK",
        "instruction": """Çocuk BEKLEMENİN GÜZELLİÄİNİ ÖÄRENMELİ!
        - Bir şeyi hemen isteyip beklemek zorunda kalmalı
        - Sabırsızlıkla mücadele etmeli
        - Beklemenin ödülünü almalı
        ÖRNEK SAHNE: Sabırla bekleyerek en güzel çiçeğin açmasını görür.""",
    },
    "hata yapmaktan korkmamak": {
        "theme": "HATA YAPMAKTAN KORKMAMAK",
        "instruction": """Çocuk HATALARDAN ÖÄRENMEYİ KEÅFETMELİ!
        - Bir hata yapmalı ve üzülmeli
        - Hatasından ders çıkarmalı
        - Tekrar denemeli ve başarmalı
        ÖRNEK SAHNE: Düşüp kalkar, her seferinde daha iyi yapar.""",
    },
    "liderlik": {
        "theme": "LİDERLİK",
        "instruction": """Çocuk SORUMLULUK ALMAYI VE YOL GÖSTERMEYİ ÖÄRENMELİ!
        - Bir grubu yönetme fırsatı bulmalı
        - Zorluklarda önderlik etmeli
        - Başkalarına ilham vermeli
        ÖRNEK SAHNE: Kaybolmuş arkadaşlarını güvenli yere yönlendirir.""",
    },
    "duygularini ifade etme": {
        "theme": "DUYGULARINI İFADE ETME",
        "instruction": """Çocuk DUYGULARINI SAÄLIKLI ÅEKİLDE ANLATMAYI ÖÄRENMELİ!
        - Güçlü bir duygu yaşamalı (üzüntü, kızgınlık, sevinç)
        - Bu duyguyu doğru kelimelerle ifade etmeli
        - Duygularını paylaşmanın rahatlığını hissetmeli
        ÖRNEK SAHNE: Üzgün olduğunu söyleyerek arkadaşından destek alır.""",
    },
    # Turkish names (from UI)
    "cesaret": {
        "theme": "CESARET (Bravery)",
        "instruction": """Çocuk bir KORKUYLA YÜZLEÅMELİ ve onu yenmeli!
        HİKAYE YAPI ÖNERİSİ:
        1) Çocuk güçlü görünür ama aslında gizli bir korkusu var (karanlık, yükseklik, böcek vb).
        2) Korktuğu durumla KARÅILAÅIR — kaçmak ister.
        3) KRİZ: Kaçmaya çalışır ama kaçamaz → korku zirve yapar.
        4) Mentor öğretir: "Cesaret korkmamak değil, korkuna rağmen adım atmaktır."
        5) Çocuk EL FENERİ/IÅIK metaforu ile korkuyla yüzleşir → korkulan şey zararsızmış!
        6) "Korkup kaçmak yerine, ışık tutup bakmayı öğrendim."
        âŒ Cesaret = pervasızlık DEÄİL. Akıllı cesaret = önce düşün, sonra adım at.
        ÖRNEK METAFOR: El feneri → karanlığa ışık tut → korkulan şey sadece bir gölge.""",
    },
    "paylaşma": {
        "theme": "PAYLAÅMA (Sharing)",
        "instruction": """Çocuk değerli bir şeyi BAÅKALARIYLA PAYLAÅMALI!
        - Yiyeceğini, oyuncağını veya keşfini biriyle paylaşır
        - Önce paylaşmak istemeyebilir: "Ama bu benim..." diye düşündü
        - Sonra paylaşmanın mutluluğunu keşfeder
        - Paylaştıkça daha mutlu olduğunu anlar
        ÖRNEK SAHNE: Aç bir kuşla son bisküvisini paylaşır.""",
    },
    "merak": {
        "theme": "MERAK (Curiosity)",
        "instruction": """Çocuk SORU SORMALI ve ARAÅTIRMALI!
        - "Bu ne olabilir?", "Acaba neden böyle?" soruları
        - Keşfetme tutkusu: her köşeye bakmak, dokunmak, koklamak
        - Cevapları bulmak için çaba gösterir
        - Öğrenmenin heyecanını yaşar
        ÖRNEK SAHNE: Gizemli bir kapıyı/tüneli keşfetmek için içeri girer.""",
    },
    "sabır": {
        "theme": "SABIR (Patience)",
        "instruction": """Çocuk SABIRLI OLMAYI ve BEKLEMEYI öğrenmeli!
        HİKAYE YAPI ÖNERİSİ:
        1) Çocuk sabırsız — her şeyi HEMEN ister, bekleyemez.
        2) Sabırsızlık yüzünden bir şeyi MAHVEDER (çiçeği erken koparır, hamuru erken açar).
        3) KRİZ: Acelecilik sonucu kaybeder, üzülür.
        4) Mentor öğretir: "Acele eden tırtıl kelebeğe dönüşemez."
        5) Çocuk BEKLER → sabırla bekleyince harika sonuç elde eder.
        6) "Beklemek zor ama sonucu harika!"
        ÖRNEK METAFOR: Çömlek yapımı → acele edersen kırılır, sabırla şekil alır.""",
    },
    "yardımseverlik": {
        "theme": "YARDIM ETME (Helpfulness)",
        "instruction": """Çocuk BİRİNE YARDIM ETMELİ!
        - Zor durumda olan birini/bir hayvanı görür
        - Yardım etmeye karar verir (kolay olmasa bile)
        - Yardım ederken zorluklarla karşılaşır
        - Yardım etmenin iç huzurunu yaşar
        ÖRNEK SAHNE: Kaybolan bir yavru hayvanı ailesine kavuşturur.""",
    },
    "dürüstlük": {
        "theme": "DÜRÜSTLÜK (Honesty)",
        "instruction": """Çocuk DOÄRUYU SÖYLEME SEÇİMİYLE karşılaşmalı!
        - Yalan söylemek kolay olurdu ama...
        - Doğruyu söylemenin zorluğu
        - Dürüst olmanın sonuçlarını yaşar
        - Dürüstlüğün getirdiği güven ve saygı
        ÖRNEK SAHNE: Kırdığı bir şeyi itiraf etmek zorunda kalır.""",
    },
    "özgüven": {
        "theme": "ÖZGÜVEN (Self-confidence)",
        "instruction": """Çocuk KENDİNE GÜVENMEYI ÖÄRENMELİ!
        - Başta "Ben yapamam" düşüncesi
        - Küçük başarılar kazanır
        - "Ben bunu başarabilirim!" keşfi
        - Kendi gücünü keşfeder
        ÖRNEK SAHNE: Herkesin yapamayacağını söylediği bir şeyi başarır.""",
    },
    "empati": {
        "theme": "EMPATİ (Empathy)",
        "instruction": """Çocuk BAÅKASININ HİSLERİNİ ANLAMALI!
        - Üzgün/korkmuş birini görür
        - "Acaba nasıl hissediyor?" diye düşünür
        - Onun yerine kendini koyar
        - Anlayış ve destek gösterir
        ÖRNEK SAHNE: Ağlayan bir çocuğu teselli eder.""",
    },
    "sorumluluk": {
        "theme": "SORUMLULUK (Responsibility)",
        "instruction": """Çocuk BİR GÖREV ÜSTLENMELİ!
        - Önemli bir sorumluluk alır
        - Zorluklarla karşılaşsa da vazgeçmez
        - Görevini tamamlar
        - Sorumluluğun gururunu yaşar
        ÖRNEK SAHNE: Bir hayvana/bitkiye bakmayı üstlenir.""",
    },
    # English names (fallback)
    "bravery": {
        "theme": "CESARET",
        "instruction": "Çocuk bir korkuyla yüzleşmeli ve cesaretle aşmalı.",
    },
    "sharing": {
        "theme": "PAYLAÅMA",
        "instruction": "Çocuk değerli bir şeyi başkalarıyla paylaşmalı.",
    },
    "curiosity": {"theme": "MERAK", "instruction": "Çocuk sorular sormalı ve keşfetmeli."},
    "patience": {
        "theme": "SABIR",
        "instruction": "Çocuk beklemek zorunda kalmalı ve sabrın değerini öğrenmeli.",
    },
    "kindness": {"theme": "İYİLİK", "instruction": "Çocuk birine iyilik yapmalı."},
    "honesty": {
        "theme": "DÜRÜSTLÜK",
        "instruction": "Çocuk doğruyu söyleme seçimiyle karşılaşmalı.",
    },
}

# Default values when none selected
DEFAULT_EDUCATIONAL_VALUES = ["merak", "cesaret"]

# ---------------------------------------------------------------------------
# Scenario → default value fallback (when user selects no learning outcome)
# ---------------------------------------------------------------------------
# Keys: scenario.theme_key OR lowered substring of scenario.name
SCENARIO_DEFAULT_VALUE: dict[str, str] = {
    # Location-based
    "cappadocia": "cesaret",
    "kapadokya": "cesaret",
    "ephesus": "merak",
    "efes": "merak",
    "pamukkale": "sabır",
    "troy": "cesaret",
    "truva": "cesaret",
    "antalya": "merak",
    "istanbul": "merak",
    "yerebatan": "merak",
    "mardin": "empati",
    "nemrut": "sabır",
    "sumela": "cesaret",
    "sultanahmet": "merak",
    "galata": "cesaret",
    "kudus": "empati",
    "kudüs": "empati",
    "gobeklitepe": "merak",
    "göbeklitepe": "merak",
    "catalhoyuk": "merak",
    "çatalhöyük": "merak",
    "abusimbel": "merak",
    "tacmahal": "sabır",
    # Theme-based fallbacks
    "adventure": "cesaret",
    "macera": "cesaret",
    "discovery": "merak",
    "kesif": "merak",
    "keşif": "merak",
    "friendship": "empati",
    "dostluk": "empati",
    "puzzle": "sabır",
    "bulmaca": "sabır",
    "space": "cesaret",
    "uzay": "cesaret",
    "underwater": "merak",
    "denizalti": "merak",
}


def _resolve_default_value_for_scenario(scenario) -> str:
    """Pick a sensible default value when the user selected no learning outcome."""
    theme_key = (getattr(scenario, "theme_key", None) or "").lower().strip()
    name = (getattr(scenario, "name", None) or "").lower().strip()

    # 1) Exact theme_key match
    if theme_key and theme_key in SCENARIO_DEFAULT_VALUE:
        return SCENARIO_DEFAULT_VALUE[theme_key]

    # 2) Substring match against scenario name
    for key, value in SCENARIO_DEFAULT_VALUE.items():
        if key in name or key in theme_key:
            return value

    # 3) Ultimate fallback
    return "cesaret"


# ---------------------------------------------------------------------------
# Value emotion beats — 3-act arc for narrative injection
# ---------------------------------------------------------------------------
VALUE_EMOTION_BEATS: dict[str, dict[str, str]] = {
    "cesaret": {
        "hesitation": "Çocuk karşısındaki zorluğu görünce bir an duraksıyor, tedirgin ama meraklı.",
        "attempt": "Korkusuna rağmen cesur bir adım atıyor, denemeye karar veriyor.",
        "mastery": "Başardığını fark edince içi sevinçle doluyor — cesaretin gücünü hissediyor.",
    },
    "merak": {
        "hesitation": "Çocuk ilginç bir şey fark ediyor ama henüz yaklaşmaya çekiniyor.",
        "attempt": "Merakına yenik düşüp araştırmaya başlıyor, sorular soruyor.",
        "mastery": "Keşfettiği şey onu hayrete düşürüyor — soru sormanın güzelliğini anlıyor.",
    },
    "sabır": {
        "hesitation": "Çocuk sonucu hemen göremeyince huzursuzlanıyor.",
        "attempt": "Sabırla beklemeyi ve adım adım ilerlemeyi deniyor.",
        "mastery": "Sabrının karşılığını alınca beklemenin değerini kavrıyor.",
    },
    "empati": {
        "hesitation": "Çocuk birinin üzgün olduğunu fark ediyor ama ne yapacağını bilmiyor.",
        "attempt": "Kendini karşısındakinin yerine koyarak yardım etmeye çalışıyor.",
        "mastery": "Küçük bir jesti büyük bir fark yarattığında empatiyi hissediyor.",
    },
    "paylaşma": {
        "hesitation": "Çocuk sahip olduğu güzel şeyi paylaşmak konusunda kararsız.",
        "attempt": "Paylaşmaya karar veriyor, ilk adımı atıyor.",
        "mastery": "Paylaşmanın her iki tarafı da mutlu ettiğini görüyor.",
    },
    "özgüven": {
        "hesitation": "Çocuk 'ben yapamam' diye düşünüyor, kendinden şüphe ediyor.",
        "attempt": "Küçük bir adım atarak kendini deniyor.",
        "mastery": "Başarınca 'ben yapabilirmişim!' diyerek özgüveni büyüyor.",
    },
    "yardımseverlik": {
        "hesitation": "Çocuk yardıma ihtiyacı olan birini görüyor ama çekingen.",
        "attempt": "Yardım eli uzatıyor, küçük de olsa bir katkıda bulunuyor.",
        "mastery": "Yardımının etkisini görünce iç huzur ve mutluluk duyuyor.",
    },
    "dürüstlük": {
        "hesitation": "Çocuk doğruyu söylemek ile saklamak arasında kalıyor.",
        "attempt": "Zor olsa da doğruyu söylemeyi seçiyor.",
        "mastery": "Dürüstlüğünün güven ve saygı getirdiğini hissediyor.",
    },
    "sorumluluk": {
        "hesitation": "Çocuk üstlendiği görevin zorluğunu görünce vazgeçmek istiyor.",
        "attempt": "Sorumluluğunu hatırlayarak devam etmeye karar veriyor.",
        "mastery": "Görevi tamamlayınca gurur ve başarma duygusu yaşıyor.",
    },
}

# V3: Short hidden lesson for narrative (value_message) and recurring visual in every image (value_visual_motif)
VALUE_MESSAGE_TR: dict[str, str] = {
    "özgüven": "Küçük adımlarla kendine güven kazanır.",
    "cesaret": "Korkuya rağmen adım atmanın gücünü keşfeder.",
    "merak": "Soru sormak ve keşfetmek harika sonuçlar getirir.",
    "sabır": "Beklemek zor olsa da sonucu güzeldir.",
    "paylaşma": "Paylaşmak her iki tarafı da mutlu eder.",
    "yardımseverlik": "Yardım etmek iç huzur verir.",
    "dürüstlük": "Doğruyu söylemek güven ve saygı getirir.",
    "empati": "Başkasının hislerini anlamak ilişkileri güçlendirir.",
    "sorumluluk": "Üstlendiğimiz görevleri tamamlamak bizi gururlandırır.",
}

VALUE_VISUAL_MOTIF_EN: dict[str, str | None] = {
    "özgüven": "a small golden confidence charm bracelet visible on the child's wrist",
    "cesaret": "a subtle glowing courage symbol on the child's necklace or pocket",
    "merak": "a tiny curiosity compass or star charm on the child's bag",
    "sabır": "a small hourglass or seed charm visible in the scene",
    "paylaşma": "a shared-item motif (e.g. two hands reaching for the same object) subtly present",
    "yardımseverlik": "a gentle helping-hand symbol or band on the child's wrist",
    "dürüstlük": "a clear crystal or truth symbol subtly in frame",
    "empati": "a heart or warmth symbol charm visible in the scene",
    "sorumluluk": "a small key or badge of responsibility on the child",
    "diş fırçalama": "a sparkly toothbrush charm hanging from the child's bag",
    "sağlıklı beslenme": "a tiny fruit basket charm on the child's belt",
    "düzenli uyku": "a crescent moon charm on the child's necklace",
    "tuvalet eğitimi": None,
    "el yıkama": "tiny soap bubble stickers on the child's sleeve",
    "hata yapmaktan korkmamak": "a small puzzle piece charm on the child's pocket",
    "liderlik": "a small star badge on the child's chest",
    "duygularını ifade etme": "a tiny rainbow heart pin on the child's collar",
    "özür dilemek": "a small olive branch charm on the child's bag",
    "kardeş sevgisi": "matching friendship bracelets on the child's wrist",
    "arkadaşlık kurmak": "a tiny handshake charm on the child's necklace",
    "kitap okuma sevgisi": "a miniature book charm hanging from the child's bag",
    "ekran süresi dengesi": "a small nature-leaf pin on the child's shirt",
    "doğa ve hayvan sevgisi": "a small green leaf or paw print charm on the child's bag",
    "çevre temizliği": "a tiny recycle symbol pin on the child's shirt",
}


def _normalize_value_key(name: str) -> str:
    """Normalize outcome name for value lookup (özgüven <-> ozguven)."""
    t = (name or "").lower().strip()
    for tr, ascii_ in (("ö", "o"), ("ü", "u"), ("ı", "i"), ("ğ", "g"), ("ş", "s"), ("ç", "c")):
        t = t.replace(tr, ascii_)
    return t


def get_value_visual_motif_for_outcomes(outcomes: list) -> str | None:
    """Return the first matching value_visual_motif for the selected outcomes (V3 injection)."""
    for outcome in outcomes or []:
        name = (getattr(outcome, "name", None) or str(outcome)).lower().strip()
        name_norm = _normalize_value_key(name)
        for key, motif in VALUE_VISUAL_MOTIF_EN.items():
            if motif is None:
                continue
            key_norm = _normalize_value_key(key)
            if key in name or name in key or key_norm in name_norm or name_norm in key_norm:
                return motif
    return None


def get_value_message_tr_for_outcomes(outcomes: list) -> str | None:
    """Return the first matching value_message (TR) for narrative injection."""
    for outcome in outcomes or []:
        name = (getattr(outcome, "name", None) or str(outcome)).lower().strip()
        name_norm = _normalize_value_key(name)
        for key, msg in VALUE_MESSAGE_TR.items():
            key_norm = _normalize_value_key(key)
            if key in name or name in key or key_norm in name_norm or name_norm in key_norm:
                return msg
    return None


def build_educational_prompt(outcomes: list) -> str:
    """Build a strong educational values prompt section.

    Args:
        outcomes: List of outcome objects (with name attribute) or strings

    Returns:
        Formatted prompt section for educational values
    """
    if not outcomes:
        outcomes = DEFAULT_EDUCATIONAL_VALUES

    value_sections = []

    for outcome in outcomes:
        # Get the value name
        if hasattr(outcome, "name"):
            value_name = outcome.name.lower().strip()
        elif hasattr(outcome, "ai_prompt") and outcome.ai_prompt:
            # Use ai_prompt if available
            value_sections.append(f"ğŸ“Œ {outcome.ai_prompt}")
            continue
        else:
            value_name = str(outcome).lower().strip()

        # Look up in our educational prompts
        matched = False
        for key, data in EDUCATIONAL_VALUE_PROMPTS.items():
            if key in value_name or value_name in key:
                value_sections.append(f"""
ğŸ“Œ {data["theme"]}:
{data["instruction"]}
""")
                matched = True
                break

        # Fallback for unmatched values
        if not matched:
            value_sections.append(f"""
ğŸ“Œ {value_name.upper()}:
Bu değer hikayenin ANA TEMASINI oluşturmalı!
Çocuk bu değeri YAÅAYARAK öğrenmeli - sadece söz olarak değil, eylem olarak!
""")

    if not value_sections:
        # Ultimate fallback
        value_sections = [
            """
ğŸ“Œ MERAK VE KEÅİF:
Çocuk dünyayı keşfetmenin heyecanını yaşamalı!
Her köşede yeni bir sürpriz, her adımda yeni bir öğrenim fırsatı.
"""
        ]

    return "\n".join(value_sections)


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


