"""Gemini AI service for story generation with TWO-PASS GENERATION strategy.

TWO-PASS GENERATION STRATEGY:
=============================
PASS 1 - "Pure Author" (gemini-1.5-pro):
  - Focus: 100% on creative writing
  - Output: Beautiful, emotional, immersive story TEXT ONLY
  - No JSON, no image prompts, no technical constraints
  - Goal: Let the AI be a GREAT WRITER

PASS 2 - "Technical Director" (gemini-2.5-flash):
  - Input: The beautiful story from Pass 1
  - Focus: Split into pages, generate visual prompts
  - Output: Structured JSON with visual prompts
  - Goal: Format the story for production

This separation restores story QUALITY while maintaining technical requirements.
"""

import json
import time
from typing import TYPE_CHECKING

import httpx
import structlog
from pydantic import BaseModel, Field

from app.config import settings
from app.core.exceptions import AIServiceError, ContentPolicyError
from app.core.rate_limit import rate_limit_retry
from app.core.sanitizer import (
    sanitize_for_prompt,
)
from app.models.learning_outcome import LearningOutcome
from app.models.scenario import Scenario
from app.services.ai.llm_output_repair import (
    extract_and_repair_json as _enhanced_extract_json,
)
from app.services.ai.llm_output_repair import (
    repair_blueprint as _repair_blueprint,
)
from app.services.ai.llm_output_repair import (
    repair_pages as _repair_pages,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


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
        "old city of jerusalem": "Kudüs Eski Şehir",
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
🌟 SEN DÜNYA STANDARTLARINDA BİR ÇOCUK KİTABI YAZARISIN 🌟

Görevin: Çocukları büyüleyen, sayfalar arası TUTARLI BİR KURGUSU olan,
karakter gelişimi içeren BİR BAŞYAPIT yazmak. Teknik format DÜŞÜNME -
sadece HARİKA BİR HİKAYE YAZ!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📖 HİKAYE YAPISI (DRAMATİK YAY) — EN ÖNEMLİ KURAL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Hikaye bağımsız sayfalar DEĞİL, birbirine BAĞLI bir zincir olmalı!
Her sayfa öncekinin sonucudur, sonrakinin sebebidir.

Sayfa dağılımı (toplam N sayfa için):

🔹 BÖLÜM 1 — GİRİŞ ve KARAKTER TANITIMI (%15)
   → Çocuğun kişiliğini, ZAYIF YANINI tanıt.
   → Sorunu GÖSTER: Çocuk bir uyarıyı dinlemiyor, bir alışkanlığı yanlış, bir korkusu var vb.
   → Örnek: "Uras tuvaletim yok dedi ama karnında sıkışıklık vardı."

🔹 BÖLÜM 2 — SORUN BÜYÜYOR (%20)
   → Zayıf yandan dolayı işler kötüye gidiyor.
   → Çocuk inatçılığının / yanlış davranışının SONUÇLARINI yaşıyor.
   → Duygusal gerilim artıyor, utanç/korku/başarısızlık.
   → Her sayfa bir öncekinin DOĞAL DEVAMI.

🔹 BÖLÜM 3 — KRİZ ve MENTOR (%15)
   → En kötü an: Çocuk düşer, ıslanır, kaybolur, korkar, yalnız kalır.
   → BİR MENTOR/YARDIMCI FIGÜR belirir (yaşlı usta, konuşan hayvan, peri...).
   → Mentor çocuğu yargılamaz, onu ANLAR.

🔹 BÖLÜM 4 — ÖĞRENME ve METAFOR (%25)
   → Mentor bir METAFOR / ARAÇ / GÖREV ile öğretiyor.
   → Çocuk önce BAŞARISIZ oluyor (acelecilik, dikkatsizlik yüzünden).
   → Sonra DURUR, DÜŞÜNÜR, tekrar dener ve BAŞARIR.
   → Ders doğrudan söylenmiyor, çocuk yaşayarak buluyor.
   → Örnek: Delikli testi metaforu → "tutmazsan sızar" → tuvalet eğitimi.

🔹 BÖLÜM 5 — UYGULAMA (%15)
   → Çocuk öğrendiğini GERÇEK HAYATTA uygular.
   → Eskiden yapacağı hata aklına gelir ama bu sefer DOĞRU SEÇİMİ yapar.
   → "Eskiden olsa koşardı ama şimdi durdu, düşündü."

🔹 BÖLÜM 6 — KAPANIŞ ve DÖNÜŞÜM (%10)
   → Çocuk değişmiş, büyümüş, ders almış.
   → Duygusal ve güçlü bir kapanış cümlesi.
   → "Ben süper kahraman değilim. Ben Akıllı Uras'ım!"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📚 YAZIM İLKELERİ
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1️⃣ SAYFA BAĞLANTISI (EN KRİTİK!)
   ❌ YANLIŞ: Her sayfa bağımsız bir olay.
   ✅ DOĞRU: Her sayfa önceki sayfanın sonucunu devam ettirir.
   Önceki sayfa: "Uras inatla tuvalete gitmedi."
   Sonraki sayfa: "Sıkışıklık artmıştı, bacaklarını birbirine bastırıyordu."

2️⃣ DUYUSAL DETAYLAR (Göster, Anlatma!)
   ❌ YANLIŞ: "Uras mutlu oldu."
   ✅ DOĞRU: "Uras'ın kalbi sevinçten zıpladı. Yanakları kızardı."
   
3️⃣ DUYGUSAL DERİNLİK
   - Çocuğun İÇ DÜNYASINI yaz: merak, heyecan, korku, cesaret, utanç
   - Duyguları GÖSTER, söyleme: titredi, kızardı, gözleri doldu

4️⃣ SESLİ OKUMAYA UYGUN RİTİM
   - Kısa ve uzun cümleler karışık
   - Ses efektleri: "Vızz!", "Pat pat pat", "Çatırrr!"

5️⃣ KİŞİSEL MACERA
   ❌ YANLIŞ: Gezi rehberi tarzı bilgi yığını
   ✅ DOĞRU: Çocuğun KİŞİSEL deneyimi, onun gözünden dünya

6️⃣ KARAKTER TEZATI
   - Çocuğun hem güçlü hem zayıf yanları olmalı
   - "Hem korkak hem pervasız, hem özgüvensiz hem aşırı özgüvenli"
   - Bu tezat hikayenin motorudur!

⚠️ ASLA YAPMA:
- Turistik bilgi paragrafları yazma (ansiklopedi cümleleri YASAK!)
- Her sayfada aynı kalıp cümleler
- Birbirine bağlı OLMAYAN kopuk sahneler
- Dersi doğrudan SÖYLEME (çocuk yaşayarak öğrenmeli)
- Robotik, duygusuz anlatım
- ❌❌ AİLE ÜYELERİ YAZMAK: anne, baba, kardeş, abla, abi, dede, nine, aile — KESİNLİKLE YASAK!
  Çocuk macerayı TEK BAŞINA yaşar. Yardımcı: hayvan arkadaş veya bilge mentor.
- ❌ ANATOMİK OLARAK İMKANSIZ SAHNELER YAZMA:
  Hayvanlar insan gibi davranamaz! "Köpekle el ele tutuştular" YASAK — köpeğin eli yok!
  Doğru: "Köpek yanında koşuyordu", "Sincap omzuna atladı", "Kedi bacağına sürtündü"
  Hayvanları GERÇEK hayvan davranışlarıyla yaz!

🐾 HAYVAN TUTARLILIĞI:
Hikayede bir hayvan arkadaş varsa, HER SAYFADA AYNI HAYVAN olmalı!
İlk sayfada "beyaz köpek" dediysen son sayfada "kahverengi köpek" OLMAZ!
Hayvanın rengini, türünü, boyutunu İLK GÖRÜNDÜKDe tanımla ve HİÇ DEĞİŞTİRME!

🎯 HEDEF: Hikaye BİR BÜTÜN olarak okunduğunda, baştan sona tutarlı bir
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
        "theme": "DOĞA VE HAYVAN SEVGİSİ (Nature & Animal Love)",
        "instruction": """Çocuk DOĞAYI VE HAYVANLARI SEVMEYI ÖĞRENMELİ!
        - Bir hayvanla özel bir bağ kurmalı (kuş, tavşan, sincap, böcek...)
        - Doğanın güzelliklerini keşfetmeli: "Kelebeğin kanatları gökkuşağı gibi parlıyordu!"
        - Hayvana yardım etme fırsatı bulmalı: yaralı kuş, aç sincap, kaybolmuş yavru
        - Doğayı korumanın önemini anlamalı: "Bu orman herkesin evi"
        ÖRNEK SAHNE: Yaralı bir kuşu iyileştirip özgürlüğüne kavuşturur.""",
    },
    "doga ve hayvan sevgisi": {
        "theme": "DOĞA VE HAYVAN SEVGİSİ",
        "instruction": """Çocuk DOĞAYI VE HAYVANLARI SEVMEYI ÖĞRENMELİ!
        - Bir hayvanla dostluk kurmalı ve ona yardım etmeli
        - Doğanın güzelliklerini keşfetmeli ve korumanın önemini anlamalı
        - Hayvanlarla iletişim kurup onları anlamalı
        ÖRNEK SAHNE: Ormanda kaybolmuş bir yavru hayvanı ailesine kavuşturur.""",
    },
    "kitap": {
        "theme": "KİTAP OKUMA SEVGİSİ (Love of Reading)",
        "instruction": """Çocuk KİTAPLARIN BÜYÜLÜ DÜNYASINI KEŞFETMELİ!
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
        "instruction": """Çocuk EKRAN DIŞINDA AKTİVİTELERİN KEYFİNİ KEŞFETMELİ!
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
        "theme": "MERAK VE KEŞFETMEK",
        "instruction": """Çocuk SORU SORMALI VE DÜNYAYI KEŞFETMELİ!
        - "Bu neden böyle?", "Nasıl çalışıyor?" soruları
        - Her köşede yeni bir keşif yapma heyecanı
        - Araştırarak öğrenmenin tadını çıkarmalı
        ÖRNEK SAHNE: Gizemli bir kapıyı merakla açar ve yeni bir dünya bulur.""",
    },
    "cevre temizligi": {
        "theme": "ÇEVRE TEMİZLİĞİ (Environmental Cleanliness)",
        "instruction": """Çocuk ÇEVREYİ TEMİZ TUTMANIN ÖNEMİNİ ÖĞRENMELİ!
        - Çöpü doğru yere atmanın önemini görmeli
        - Temiz bir çevrenin hayvanlar ve insanlar için değerini anlamalı
        - Çevreyi kirletmenin sonuçlarını görmeli
        - Temizlik kahramanı olmalı
        ÖRNEK SAHNE: Parkı temizleyerek hayvanların evini kurtarır.""",
    },
    # Öz Bakım
    "dis fircalama": {
        "theme": "DİŞ FIRÇALAMA ALIŞKANLIĞI",
        "instruction": """Çocuk DİŞ FIRÇALAMANIN ÖNEMİNİ ÖĞRENMELİ!
        - Diş fırçalamanın eğlenceli yanlarını keşfetmeli
        - Temiz dişlerin gücünü hissetmeli
        ÖRNEK SAHNE: Diş perisi ile tanışır ve dişlerinin önemini öğrenir.""",
    },
    "saglikli beslenme": {
        "theme": "SAĞLIKLI BESLENME",
        "instruction": """Çocuk SEBZE VE MEYVELERİN GÜCÜNÜ KEŞFETMELİ!
        - Sağlıklı yiyeceklerin verdiği enerjiyi hissetmeli
        - Sebze ve meyvelerin lezzetini keşfetmeli
        ÖRNEK SAHNE: Havuç yiyerek süper güç kazanır.""",
    },
    "duzenli uyku": {
        "theme": "DÜZENLİ UYKU",
        "instruction": """Çocuk VAKTİNDE UYUMANIN ÖNEMİNİ ÖĞRENMELİ!
        - Uykusuz kalmanın zorluğunu yaşamalı
        - İyi uykunun verdiği enerjiyi keşfetmeli
        ÖRNEK SAHNE: Rüyalar diyarında harika maceralar yaşar.""",
    },
    "tuvalet egitimi": {
        "theme": "TUVALET EĞİTİMİ / VÜCUDUNU DİNLEME",
        "instruction": """Çocuk VÜCUDUNUN SİNYALLERİNİ DİNLEMEYİ ve KONTROL etmeyi öğrenmeli!
        HİKAYE YAPI ÖNERİSİ:
        1) Çocuk tuvaletinin geldiğini hisseder ama oyunu/maceryı bölmek istemez → "Sonra yaparım" der.
        2) Sıkışıklık GİDEREK ARTAR — bacaklarını sıkar, zıplar, rahatsız olur.
        3) KRİZ ANI: Çok geç kalır → utanç verici bir durum yaşar (altına kaçırır, ıslanır).
        4) Bir MENTOR, metafor ile öğretir (örnek: delikli testi — tutmazsan sızar).
        5) Çocuk öğrenir: "Vücudum sinyal verdiğinde hemen gitmeliyim!"
        6) Tekrar tuvaleti gelir → bu sefer HEMEN gider → gurur duyar.
        ❌ YASAKLAR: Utandırıcı sahneleri AŞAĞI düşürücü yapma, NORMAL ve öğretici tut.
        ✅ MESAJ: "Vücudunu dinleyen çocuk en güçlü çocuktur."
        ÖRNEK METAFOR: Delikli bir testi → parmağını basmadan koşarsan su akar.""",
    },
    "el yikama": {
        "theme": "EL YIKAMA VE HİJYEN",
        "instruction": """Çocuk TEMİZLİK ALIŞKANLIKLARINI ÖĞRENMELİ!
        - El yıkamanın mikropları nasıl yok ettiğini görmeli
        - Temiz ellerin sağlık getirdiğini anlamalı
        ÖRNEK SAHNE: Ellerini yıkayarak görünmez mikrop canavarlarını yener.""",
    },
    # Sosyal Beceriler
    "paylasma": {
        "theme": "PAYLAŞMAK GÜZELDİR",
        "instruction": """Çocuk PAYLAŞMANIN MUTLULUĞUNU KEŞFETMELİ!
        - Sevdiği bir şeyi paylaşma fırsatı bulmalı
        - Paylaşmanın verdiği iç huzuru yaşamalı
        ÖRNEK SAHNE: Son kurabiyesini arkadaşıyla paylaşır ve daha mutlu olur.""",
    },
    "ozur dilemek": {
        "theme": "ÖZÜR DİLEMEK",
        "instruction": """Çocuk HATA YAPINCA ÖZÜR DİLEMEYİ ÖĞRENMELİ!
        - Bir hata yapıp üzülmeli
        - Özür dilemenin cesaretini göstermeli
        - Özür dilemenin ilişkileri nasıl düzelttiğini görmeli
        ÖRNEK SAHNE: Arkadaşını üzdükten sonra özür diler ve barışırlar.""",
    },
    "kardes sevgisi": {
        "theme": "KARDEŞ SEVGİSİ",
        "instruction": """Çocuk KARDEŞİYLE İYİ GEÇİNMEYİ ÖĞRENMELİ!
        - Kardeşiyle bir çatışma yaşamalı
        - Kardeşinin değerini anlamalı
        - Birlikte daha güçlü olduklarını keşfetmeli
        ÖRNEK SAHNE: Kardeşiyle birlikte çalışarak zor bir görevi başarır.""",
    },
    "arkadaslik kurmak": {
        "theme": "ARKADAŞLIK KURMAK",
        "instruction": """Çocuk YENİ ARKADAŞLAR EDİNMEYİ ÖĞRENMELİ!
        - Yeni biriyle tanışma fırsatı bulmalı
        - İlk adımı atmanın heyecanını yaşamalı
        - Arkadaşlığın değerini keşfetmeli
        ÖRNEK SAHNE: Çekingen bir çocuğa yaklaşır ve harika bir arkadaş kazanır.""",
    },
    # Kişisel Gelişim
    "cesaret ve ozguven": {
        "theme": "CESARET VE ÖZGÜVEN",
        "instruction": """Çocuk KORKULARINI YENMEYI VE KENDİNE GÜVENMEYI ÖĞRENMELİ!
        - Bir korkuyla yüzleşmeli
        - İçindeki cesareti keşfetmeli
        - "Ben yapabilirim!" demeli ve başarmalı
        ÖRNEK SAHNE: Yükseklik korkusunu yenerek zirveye ulaşır.""",
    },
    "sabirli olmak": {
        "theme": "SABIRLI OLMAK",
        "instruction": """Çocuk BEKLEMENİN GÜZELLİĞİNİ ÖĞRENMELİ!
        - Bir şeyi hemen isteyip beklemek zorunda kalmalı
        - Sabırsızlıkla mücadele etmeli
        - Beklemenin ödülünü almalı
        ÖRNEK SAHNE: Sabırla bekleyerek en güzel çiçeğin açmasını görür.""",
    },
    "hata yapmaktan korkmamak": {
        "theme": "HATA YAPMAKTAN KORKMAMAK",
        "instruction": """Çocuk HATALARDAN ÖĞRENMEYİ KEŞFETMELİ!
        - Bir hata yapmalı ve üzülmeli
        - Hatasından ders çıkarmalı
        - Tekrar denemeli ve başarmalı
        ÖRNEK SAHNE: Düşüp kalkar, her seferinde daha iyi yapar.""",
    },
    "liderlik": {
        "theme": "LİDERLİK",
        "instruction": """Çocuk SORUMLULUK ALMAYI VE YOL GÖSTERMEYİ ÖĞRENMELİ!
        - Bir grubu yönetme fırsatı bulmalı
        - Zorluklarda önderlik etmeli
        - Başkalarına ilham vermeli
        ÖRNEK SAHNE: Kaybolmuş arkadaşlarını güvenli yere yönlendirir.""",
    },
    "duygularini ifade etme": {
        "theme": "DUYGULARINI İFADE ETME",
        "instruction": """Çocuk DUYGULARINI SAĞLIKLI ŞEKİLDE ANLATMAYI ÖĞRENMELİ!
        - Güçlü bir duygu yaşamalı (üzüntü, kızgınlık, sevinç)
        - Bu duyguyu doğru kelimelerle ifade etmeli
        - Duygularını paylaşmanın rahatlığını hissetmeli
        ÖRNEK SAHNE: Üzgün olduğunu söyleyerek arkadaşından destek alır.""",
    },
    # Turkish names (from UI)
    "cesaret": {
        "theme": "CESARET (Bravery)",
        "instruction": """Çocuk bir KORKUYLA YÜZLEŞMELİ ve onu yenmeli!
        HİKAYE YAPI ÖNERİSİ:
        1) Çocuk güçlü görünür ama aslında gizli bir korkusu var (karanlık, yükseklik, böcek vb).
        2) Korktuğu durumla KARŞILAŞIR — kaçmak ister.
        3) KRİZ: Kaçmaya çalışır ama kaçamaz → korku zirve yapar.
        4) Mentor öğretir: "Cesaret korkmamak değil, korkuna rağmen adım atmaktır."
        5) Çocuk EL FENERİ/IŞIK metaforu ile korkuyla yüzleşir → korkulan şey zararsızmış!
        6) "Korkup kaçmak yerine, ışık tutup bakmayı öğrendim."
        ❌ Cesaret = pervasızlık DEĞİL. Akıllı cesaret = önce düşün, sonra adım at.
        ÖRNEK METAFOR: El feneri → karanlığa ışık tut → korkulan şey sadece bir gölge.""",
    },
    "paylaşma": {
        "theme": "PAYLAŞMA (Sharing)",
        "instruction": """Çocuk değerli bir şeyi BAŞKALARIYLA PAYLAŞMALI!
        - Yiyeceğini, oyuncağını veya keşfini biriyle paylaşır
        - Önce paylaşmak istemeyebilir: "Ama bu benim..." diye düşündü
        - Sonra paylaşmanın mutluluğunu keşfeder
        - Paylaştıkça daha mutlu olduğunu anlar
        ÖRNEK SAHNE: Aç bir kuşla son bisküvisini paylaşır.""",
    },
    "merak": {
        "theme": "MERAK (Curiosity)",
        "instruction": """Çocuk SORU SORMALI ve ARAŞTIRMALI!
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
        "instruction": """Çocuk DOĞRUYU SÖYLEME SEÇİMİYLE karşılaşmalı!
        - Yalan söylemek kolay olurdu ama...
        - Doğruyu söylemenin zorluğu
        - Dürüst olmanın sonuçlarını yaşar
        - Dürüstlüğün getirdiği güven ve saygı
        ÖRNEK SAHNE: Kırdığı bir şeyi itiraf etmek zorunda kalır.""",
    },
    "özgüven": {
        "theme": "ÖZGÜVEN (Self-confidence)",
        "instruction": """Çocuk KENDİNE GÜVENMEYI ÖĞRENMELİ!
        - Başta "Ben yapamam" düşüncesi
        - Küçük başarılar kazanır
        - "Ben bunu başarabilirim!" keşfi
        - Kendi gücünü keşfeder
        ÖRNEK SAHNE: Herkesin yapamayacağını söylediği bir şeyi başarır.""",
    },
    "empati": {
        "theme": "EMPATİ (Empathy)",
        "instruction": """Çocuk BAŞKASININ HİSLERİNİ ANLAMALI!
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
        "theme": "PAYLAŞMA",
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
            value_sections.append(f"📌 {outcome.ai_prompt}")
            continue
        else:
            value_name = str(outcome).lower().strip()

        # Look up in our educational prompts
        matched = False
        for key, data in EDUCATIONAL_VALUE_PROMPTS.items():
            if key in value_name or value_name in key:
                value_sections.append(f"""
📌 {data["theme"]}:
{data["instruction"]}
""")
                matched = True
                break

        # Fallback for unmatched values
        if not matched:
            value_sections.append(f"""
📌 {value_name.upper()}:
Bu değer hikayenin ANA TEMASINI oluşturmalı!
Çocuk bu değeri YAŞAYARAK öğrenmeli - sadece söz olarak değil, eylem olarak!
""")

    if not value_sections:
        # Ultimate fallback
        value_sections = [
            """
📌 MERAK VE KEŞİF:
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
🎬 SEN BİR UZMAN SANAT YÖNETMENİSİN (Expert Art Director for Children's Books)

Görevin: Her sayfa için SADECE scene_description üretmek (İngilizce, 1–3 kısa cümle). Tek sefer, tekrarsız.

📋 ÇIKTI FORMATI (sabit):
JSON: her sayfa "text" (Türkçe) + "scene_description" (İngilizce).
scene_description = SADECE sahne: Cappadocia/lokasyon + environment + ana aksiyon + duygu. Style/negative/lens/camera/render/ghibli/anime KELİMELERİ ASLA geçmesin.

❌ ÇIKTIDA YAZMA (şablonda yönetiliyor):
- "Space for title at top" / "title safe area" — kapak şablonunda var.
- "Empty space at bottom" / "bottom text space" / "caption area" — iç sayfa şablonunda var.
Bu ifadeleri scene_description'a yazma.

🚫 scene_description İÇİNDE YASAK (kesinlikle kullanma):
anime, ghibli, miyazaki, manga, cel-shaded, pixar, disney, 3D, CGI, render, Unreal, Octane, Blender, lens, camera, DSLR, bokeh, cinematic, photorealistic, watermark, logo, wide shot, full body visible, child 30%, environment 70%, same clothing on every page, natural proportions, watercolor, illustration, storybook, brush strokes, wide-angle, f/8, epic, heroic, long hair, curly hair, short hair, braids, ponytail, hair color.

🔒 KIYAFET: scene_description'da "wearing" veya kıyafet detayı en fazla 1 kez ya da hiç — sistem şablonla ekler.
⛔ DÖNEM KIYAFETİ YASAK: Tarihsel mekanlarda bile çocuğu dönem kıyafeti ile tanımlama! "tunic", "toga", "loincloth", "animal skin" gibi dönem kıyafetleri YAZMA!
💇 SAÇ: scene_description'a saç detayı YAZMA! "long hair", "curly hair", "braids" gibi ifadeler KULLANMA — sistem saç bilgisini otomatik ekler.

⭐ scene_description YAPISI (1–3 cümle):
1) Mekan (lokasyon + ikonik öğeler: fairy chimneys, hot air balloons, vb.).
2) Karakter aksiyonu: [AGE]-year-old child named [NAME] [eylem]. [Yüz ifadesi].
3) Işık (sahneye uygun kısa ifade).

✅ ÖRNEK (doğru):
"A clear scene in Cappadocia with fairy chimneys and hot air balloons in the sky. An 8-year-old child named Ahsen looking up at the balloons with excited eyes. Warm golden morning light."

⚠️ LOKASYON: Senaryoya uygun (Kapadokya → peri bacaları, balonlar; İstanbul → kubbe, mozaik). Senaryodan farklı lokasyon yazma.

⛔ ASLA Türkçe hikaye metnini scene_description'a KOPYALAMA! "text" Türkçe, "scene_description" İngilizce — ikisi TAMAMEN farklı olmalı.
⛔ "text" alanındaki cümleleri scene_description'a yazmak YASAK. scene_description sadece İngilizce görsel sahne tasviri.
"""


# ============== Pydantic Models for Structured Output ==============


class PageContent(BaseModel):
    """Single page content with text and scene description (NO STYLE - style added later)."""

    page_number: int = Field(..., ge=0, le=64, description="Sayfa numarası (0=Kapak)")
    text: str = Field(..., min_length=10, description="Sayfa metni (Türkçe)")
    scene_description: str = Field(
        ..., min_length=50, description="Scene description (English) - NO STYLE!"
    )


class StoryResponse(BaseModel):
    """Complete story structure with all pages - AI-Director mode."""

    title: str = Field(..., min_length=3, description="Hikaye başlığı")
    pages: list[PageContent] = Field(..., min_length=3, description="Kapak + sayfalar")


class FinalPageContent(BaseModel):
    """Final page content ready for Fal.ai - with style composed."""

    page_number: int
    text: str
    scene_description: str  # Raw scene from Gemini (no style)
    visual_prompt: str = ""  # Final prompt = scene + style (composed once); empty if two-phase
    negative_prompt: str = ""  # V3: pre-built negative prompt (skip downstream recomposition)
    v3_composed: bool = False  # True when V3 pipeline already composed the prompt
    v3_enhancement_skipped: bool = False  # True when enhance_all_pages failed but page is still usable
    page_type: str = "inner"  # "cover" | "dedication" | "inner" | "backcover"
    page_index: int = 0  # 0-based position in the book (cover=0, first inner=1, ...)
    story_page_number: int | None = None  # 1-based story page (cover/dedication/backcover=None, inner=1..N)
    composer_version: str = "v3"  # V3 single source of truth
    pipeline_version: str = "v3"  # V3 single source of truth


class PageManifestEntry(BaseModel):
    """Single page entry in the book manifest."""

    page_type: str  # "cover" | "dedication" | "story" | "backcover"
    page_index: int  # 0-based position in the physical book
    story_page_number: int | None = None  # 1-based story number (None for non-story pages)
    story_text: str = ""  # Turkish text for this page
    image_prompt: str = ""  # V3 visual prompt
    negative_prompt: str = ""  # Negative prompt for image generation
    image_id: str = ""  # Filled after image generation
    composer_version: str = "v3"
    pipeline_version: str = "v3"
    prompt_hash: str = ""  # SHA-256 prefix for dedup/audit


class PageManifest(BaseModel):
    """Full book page manifest — single source of truth for page ordering.

    Standard V3 ordering:
        [0] Cover
        [1] Dedication
        [2..N+1] Story pages 1..N
        [N+2] Back cover

    Example for 22-page story:
        [0] cover, [1] dedication, [2..23] story 1..22, [24] backcover = 25 pages total
    """

    title: str
    child_name: str
    pipeline_version: str = "v3"
    style_tag: str = ""
    total_physical_pages: int = 0
    story_page_count: int = 0
    pages: list[PageManifestEntry] = Field(default_factory=list)

    # Traceability fields (filled by PipelineTracer)
    trace_id: str = ""
    scenario_id: str = ""
    style_id: str = ""
    value_id: str = ""
    seed: int | None = None
    provider: str = ""

    @classmethod
    def from_final_pages(
        cls,
        *,
        title: str,
        child_name: str,
        final_pages: list["FinalPageContent"],
        pipeline_version: str = "v3",
        style_tag: str = "",
        include_dedication: bool = True,
        include_backcover: bool = True,
    ) -> "PageManifest":
        """Build manifest from generated FinalPageContent list.

        Inserts dedication and back cover slots if requested.
        """
        entries: list[PageManifestEntry] = []
        idx = 0

        from app.core.pipeline_events import compute_prompt_hash

        # Extract AI-generated dedication text from front_matter page (if any)
        _ai_dedication_text = ""
        for fp in final_pages:
            if fp.page_type == "front_matter":
                _ai_dedication_text = fp.text or ""
                break

        _backcover_from_final: "PageManifestEntry | None" = None

        for fp in final_pages:
            # Skip front_matter pages — they're represented by the dedication slot
            if fp.page_type == "front_matter":
                continue
            # backcover collected separately; appended at end
            if fp.page_type == "backcover":
                _backcover_from_final = PageManifestEntry(
                    page_type="backcover",
                    page_index=0,  # filled below
                    story_page_number=None,
                    story_text="",
                    image_prompt=fp.visual_prompt,
                    negative_prompt=fp.negative_prompt,
                    composer_version=fp.composer_version,
                    pipeline_version=fp.pipeline_version,
                    prompt_hash=compute_prompt_hash(fp.visual_prompt) if fp.visual_prompt else "",
                )
                continue

            _phash = compute_prompt_hash(fp.visual_prompt) if fp.visual_prompt else ""
            if fp.page_type == "cover":
                entries.append(PageManifestEntry(
                    page_type="cover",
                    page_index=idx,
                    story_page_number=None,
                    story_text=fp.text,
                    image_prompt=fp.visual_prompt,
                    negative_prompt=fp.negative_prompt,
                    composer_version=fp.composer_version,
                    pipeline_version=fp.pipeline_version,
                    prompt_hash=_phash,
                ))
                idx += 1
                if include_dedication:
                    entries.append(PageManifestEntry(
                        page_type="dedication",
                        page_index=idx,
                        story_page_number=None,
                        story_text=_ai_dedication_text,
                        pipeline_version=fp.pipeline_version,
                    ))
                    idx += 1
            else:
                entries.append(PageManifestEntry(
                    page_type="story",
                    page_index=idx,
                    story_page_number=fp.story_page_number,
                    story_text=fp.text,
                    image_prompt=fp.visual_prompt,
                    negative_prompt=fp.negative_prompt,
                    composer_version=fp.composer_version,
                    pipeline_version=fp.pipeline_version,
                    prompt_hash=_phash,
                ))
                idx += 1

        if include_backcover:
            if _backcover_from_final is not None:
                # Use the AI-generated back cover prompt from V3 pipeline
                _backcover_from_final.page_index = idx
                entries.append(_backcover_from_final)
            else:
                entries.append(PageManifestEntry(
                    page_type="backcover",
                    page_index=idx,
                    story_page_number=None,
                    pipeline_version=pipeline_version,
                ))
            idx += 1

        story_count = sum(1 for e in entries if e.page_type == "story")
        return cls(
            title=title,
            child_name=child_name,
            pipeline_version=pipeline_version,
            style_tag=style_tag,
            total_physical_pages=len(entries),
            story_page_count=story_count,
            pages=entries,
        )


# ============== Gemini Service ==============


class GeminiService:
    """Service for generating stories using Google Gemini with TWO-PASS GENERATION.

    TWO-PASS STRATEGY:
    =================
    PASS 1 - "Pure Author" (gemini-1.5-pro):
      - 100% creative focus
      - Beautiful, emotional stories
      - No JSON, no technical constraints

    PASS 2 - "Technical Director" (gemini-2.5-flash):
      - Takes the beautiful story
      - Splits into pages
      - Generates visual prompts
      - Outputs structured JSON

    DYNAMIC PROMPT SUPPORT:
    ======================
    When a database session is provided, prompts can be loaded dynamically from
    the PromptTemplate table, allowing admins to modify prompts without code changes.
    Falls back to hardcoded constants if DB lookup fails.
    """

    def __init__(self, db_session: "AsyncSession | None" = None):
        """
        Initialize GeminiService.

        Args:
            db_session: Optional database session for dynamic prompt loading.
                        If not provided, uses hardcoded prompt constants.
        """
        self.api_key = settings.gemini_api_key
        self.timeout = 180.0  # seconds (32-page stories need more time, especially with 2.5-flash reasoning)
        self._db = db_session

        # TWO-PASS MODEL CONFIGURATION
        self.story_model = getattr(settings, "gemini_story_model", None) or _DEFAULT_FLASH_MODEL
        self.technical_model = (
            getattr(settings, "gemini_technical_model", None) or _DEFAULT_FLASH_MODEL
        )
        self.model = settings.gemini_model or _DEFAULT_FLASH_MODEL

        self.story_temperature = settings.gemini_story_temperature or 0.92  # Higher for creativity
        self.scene_temperature = settings.gemini_scene_temperature or 0.7

        # Shared httpx client — reuses TCP connections across Gemini calls
        self._http_client: httpx.AsyncClient | None = None

        # Initialize PromptTemplateService for dynamic prompts
        self._prompt_service = None

        logger.info(
            "GeminiService initialized with TWO-PASS strategy",
            story_model=self.story_model,
            technical_model=self.technical_model,
            story_temperature=self.story_temperature,
            dynamic_prompts_enabled=db_session is not None,
        )

    def _get_gemini_client(self) -> httpx.AsyncClient:
        """Lazy-init shared httpx client for Gemini API calls."""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                timeout=self.timeout,
                limits=httpx.Limits(
                    max_connections=100,
                    max_keepalive_connections=20,
                    keepalive_expiry=60,
                ),
            )
        return self._http_client

    async def _get_prompt(self, key: str, fallback: str) -> str:
        """
        Get prompt content from database or fallback to hardcoded constant.

        This enables dynamic prompt management via admin panel while maintaining
        safety through hardcoded fallbacks.

        Args:
            key: Prompt key (e.g., "PURE_AUTHOR_SYSTEM")
            fallback: Hardcoded fallback prompt

        Returns:
            Prompt content string
        """
        if self._db is None:
            # No database session - use hardcoded fallback
            return fallback

        try:
            # Lazy import to avoid circular dependencies
            if self._prompt_service is None:
                from app.services.prompt_template_service import get_prompt_service

                self._prompt_service = get_prompt_service()

            return await self._prompt_service.get_prompt(
                db=self._db,
                key=key,
                fallback=fallback,
            )
        except Exception as e:
            logger.warning(
                "Failed to fetch dynamic prompt, using fallback",
                key=key,
                error=str(e),
            )
            return fallback

    def _extract_and_repair_json(self, raw_text: str) -> dict | list:
        """Extract and repair JSON from Gemini response.

        Uses the enhanced extractor from llm_output_repair, with the
        original implementation as fallback for backward-compat.
        """
        return _enhanced_extract_json(raw_text)

    @staticmethod
    def _dedupe_style(visual_style: str) -> str:
        """Remove duplicate style phrases (e.g. Pixar, DreamWorks) so style is applied once only."""
        if not visual_style or len(visual_style.strip()) < 3:
            return visual_style.strip() if visual_style else "children's book illustration"
        seen_lower: set[str] = set()
        # Split by comma and paren, normalize
        parts: list[str] = []
        for raw in visual_style.replace("(", ",").replace(")", ",").split(","):
            token = raw.strip()
            if not token:
                continue
            key = token.lower()
            if key in seen_lower:
                continue
            seen_lower.add(key)
            parts.append(token)
        return ", ".join(parts) if parts else visual_style.strip()

    # Hardcoded fallback keywords — used when DB keywords_tr/keywords_en are empty
    _FALLBACK_KEYWORDS: dict[str, list[str]] = {
        "diş fırçalama": ["brush", "toothbrush", "teeth", "diş", "fırça", "fırçalama"],
        "paylaşma": ["paylaş", "share", "birlikte", "together", "paylaşma"],
        "sabır": ["sabır", "patience", "bekle", "wait", "sabırlı", "patient"],
        "cesaret": ["cesaret", "courage", "brave", "korku", "cesur", "fear"],
        "temizlik": ["temiz", "clean", "yıka", "wash", "temizlik", "cleaning"],
        "özür dileme": ["özür", "sorry", "apologize", "af", "affet", "forgive"],
        "sorumluluk": ["sorumluluk", "responsibility", "sorumlu", "responsible", "görev"],
        "empati": ["empati", "empathy", "anlayış", "hisset", "compassion"],
        "doğa sevgisi": ["doğa", "nature", "ağaç", "tree", "çiçek", "flower", "bitki"],
        "yardımlaşma": ["yardım", "help", "yardımlaş", "helping", "yardımsever"],
    }

    # Hardcoded fallback visual hints — used when DB visual_hints_en is empty
    _FALLBACK_VISUAL_HINTS: dict[str, list[str]] = {
        "diş fırçalama": ["toothbrush", "tooth-brushing moment", "brushing teeth"],
        "paylaşma": ["sharing toys", "sharing food", "giving to friend"],
        "sabır": ["waiting patiently", "calm expression"],
        "cesaret": ["brave stance", "overcoming fear"],
        "temizlik": ["washing hands", "cleaning up"],
        "özür dileme": ["apologizing to friend", "saying sorry"],
        "sorumluluk": ["taking care of pet", "doing chores"],
        "empati": ["comforting friend", "showing kindness"],
        "doğa sevgisi": ["planting tree", "caring for nature"],
        "yardımlaşma": ["helping others", "lending a hand"],
    }

    @staticmethod
    def _get_learning_outcome_keywords(outcomes: list) -> list[str]:
        """Derive search keywords from outcome names for story validation.

        Priority: DB keywords_tr/keywords_en fields > hardcoded fallback dictionary.
        """
        keywords: list[str] = []
        for outcome in outcomes:
            # 1. Try DB fields first
            db_keywords_tr = getattr(outcome, "keywords_tr", None) or ""
            db_keywords_en = getattr(outcome, "keywords_en", None) or ""
            if db_keywords_tr:
                keywords.extend([k.strip() for k in db_keywords_tr.split(",") if k.strip()])
            if db_keywords_en:
                keywords.extend([k.strip() for k in db_keywords_en.split(",") if k.strip()])
            # 2. Fallback: hardcoded dictionary (match by partial name)
            if not db_keywords_tr and not db_keywords_en:
                name = (getattr(outcome, "name", None) or str(outcome)).lower()
                for key, vals in GeminiService._FALLBACK_KEYWORDS.items():
                    if key in name or any(k in name for k in key.split()):
                        keywords.extend(vals)
                        break
        return list(dict.fromkeys(keywords))  # dedupe, preserve order

    @staticmethod
    def _get_learning_outcome_visual_hints(outcomes: list) -> list[str]:
        """Visual hints for image prompts — at least one scene should visualise the outcome.

        Priority: DB visual_hints_en field > hardcoded fallback dictionary.
        """
        hints: list[str] = []
        for outcome in outcomes:
            # 1. Try DB field first
            db_hints = getattr(outcome, "visual_hints_en", None) or ""
            if db_hints:
                hints.extend([h.strip() for h in db_hints.split(",") if h.strip()])
            else:
                # 2. Fallback: hardcoded dictionary
                name = (getattr(outcome, "name", None) or str(outcome)).lower()
                for key, vals in GeminiService._FALLBACK_VISUAL_HINTS.items():
                    if key in name or any(k in name for k in key.split()):
                        hints.extend(vals)
                        break
        return list(dict.fromkeys(hints))

    @staticmethod
    def _story_reflects_learning_outcomes(
        story_text: str,
        keywords: list[str],
        min_occurrences: int = 2,
    ) -> bool:
        """True if story text contains learning-outcome keywords at least min_occurrences times (case-insensitive)."""
        if not keywords:
            return True
        text_lower = story_text.lower()
        total = sum(text_lower.count(kw.lower()) for kw in keywords)
        return total >= min_occurrences

    async def _build_educational_prompt_dynamic(self, outcomes: list) -> str:
        """
        Build educational values prompt with dynamic DB lookup.

        This async version fetches individual educational value prompts from the
        database, allowing admins to modify educational value instructions without
        code changes.

        Falls back to the hardcoded EDUCATIONAL_VALUE_PROMPTS dictionary if:
        - No database session is available
        - The prompt is not found in the database

        Args:
            outcomes: List of outcome objects (with name attribute) or strings

        Returns:
            Formatted prompt section for educational values
        """
        if not outcomes:
            outcomes = DEFAULT_EDUCATIONAL_VALUES

        value_sections = []

        for outcome in outcomes:
            # Get the value name/key
            if hasattr(outcome, "name"):
                value_name = outcome.name.lower().strip()
                # Prefer ai_prompt (verbatim) so learning outcome is enforced
                if hasattr(outcome, "ai_prompt_instruction") and outcome.ai_prompt_instruction:
                    value_sections.append(f"📌 {outcome.ai_prompt_instruction}")
                    continue
                elif hasattr(outcome, "ai_prompt") and outcome.ai_prompt:
                    value_sections.append(f"📌 {outcome.ai_prompt}")
                    continue
            else:
                value_name = str(outcome).lower().strip()

            # Try to normalize the key (remove diacritics for DB lookup)
            normalized_key = (
                value_name.replace("ş", "s")
                .replace("ı", "i")
                .replace("ö", "o")
                .replace("ü", "u")
                .replace("ğ", "g")
                .replace("ç", "c")
            )

            # Try DB lookup first
            db_prompt_key = f"EDUCATIONAL_{normalized_key}"
            db_prompt = await self._get_prompt(db_prompt_key, "")

            if db_prompt:
                value_sections.append(db_prompt)
                continue

            # Fall back to hardcoded dictionary
            matched = False
            for key, data in EDUCATIONAL_VALUE_PROMPTS.items():
                if key in value_name or value_name in key:
                    value_sections.append(f"""
📌 {data["theme"]}:
{data["instruction"]}
""")
                    matched = True
                    break

            # Fallback for unmatched values
            if not matched:
                value_sections.append(f"""
📌 {value_name.upper()}:
Bu değer hikayenin ANA TEMASINI oluşturmalı!
Çocuk bu değeri YAŞAYARAK öğrenmeli - sadece söz olarak değil, eylem olarak!
""")

        if not value_sections:
            # Ultimate fallback
            value_sections = [
                """
📌 MERAK VE KEŞİF:
Çocuk dünyayı keşfetmenin heyecanını yaşamalı!
Her köşede yeni bir sürpriz, her adımda yeni bir öğrenim fırsatı.
"""
            ]

        return "\n".join(value_sections)

    # =========================================================================
    # PASS 1: PURE AUTHOR - Creative Story Writing
    # =========================================================================

    async def _pass1_write_story(
        self,
        scenario: Scenario,
        outcomes: list[LearningOutcome],
        child_name: str,
        child_age: int,
        child_gender: str,
        page_count: int = 16,
        cultural_elements: dict | None = None,
        extra_instructions: str = "",
    ) -> str:
        """
        PASS 1: Pure Author - Generate beautiful story TEXT ONLY.

        Uses prompt_engine.story_prompt_composer for task prompt; PURE_AUTHOR_SYSTEM from DB.
        extra_instructions: appended to task (e.g. no_family retry strengthening).
        """
        child_name = sanitize_for_prompt(child_name, max_length=50, field_name="child_name")

        from app.prompt_engine import compose_story_prompt

        task_prompt = compose_story_prompt(
            scenario, outcomes, child_name, child_age, child_gender, page_count
        )
        if extra_instructions:
            task_prompt = task_prompt + "\n\n" + extra_instructions.strip()

        cultural_prompt = ""
        if cultural_elements:
            primary = cultural_elements.get("primary", [])
            colors = cultural_elements.get("colors", "")
            cultural_prompt = f"""
🎨 KÜLTÜREL ELEMENTLER:
Atmosfer elementleri: {", ".join(primary) if primary else "Genel"}
Renk paleti: {colors if colors else "Doğal"}
Bu elementleri hikayeye doğal şekilde yedir.
"""
            logger.info("SCENARIO TEMPLATE: Using cultural_elements", elements=cultural_elements)

        system_prompt = await self._get_prompt("PURE_AUTHOR_SYSTEM", PURE_AUTHOR_SYSTEM)
        author_prompt = system_prompt + "\n\n" + task_prompt
        if cultural_prompt:
            author_prompt += "\n\n" + cultural_prompt

        import asyncio as _asyncio_p1

        story_url = get_gemini_story_url()
        _p1_max_retries = 3
        _p1_base_wait = 10  # seconds

        for _p1_attempt in range(_p1_max_retries):
            try:
                logger.info(
                    "PASS 1: Pure Author - Writing story",
                    model=self.story_model,
                    temperature=self.story_temperature,
                    child_name=child_name,
                    scenario=scenario.name if scenario else "?",
                    attempt=_p1_attempt + 1,
                )

                client = self._get_gemini_client()
                response = await client.post(
                    f"{story_url}?key={self.api_key}",
                    json={
                        "contents": [{"parts": [{"text": author_prompt}]}],
                        "generationConfig": {
                            "temperature": self.story_temperature,
                            "topK": 64,
                            "topP": 0.95,
                            "maxOutputTokens": 32000,
                        },
                        "safetySettings": [
                            {
                                "category": "HARM_CATEGORY_HARASSMENT",
                                "threshold": "BLOCK_MEDIUM_AND_ABOVE",
                            },
                            {
                                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                                "threshold": "BLOCK_MEDIUM_AND_ABOVE",
                            },
                            {
                                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                                "threshold": "BLOCK_MEDIUM_AND_ABOVE",
                            },
                            {
                                "category": "HARM_CATEGORY_HATE_SPEECH",
                                "threshold": "BLOCK_MEDIUM_AND_ABOVE",
                            },
                        ],
                    },
                )
                response.raise_for_status()

                data = response.json()
                parts = data["candidates"][0]["content"]["parts"]
                story_text = _extract_text_from_parts(parts)

                logger.info(
                    "PASS 1 Complete: Story written",
                    story_length=len(story_text),
                    preview=story_text[:200] + "...",
                )

                return story_text

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429 and _p1_attempt < _p1_max_retries - 1:
                    wait = _p1_base_wait * (2 ** _p1_attempt)
                    logger.warning(
                        "PASS 1 rate limited (429) — retrying",
                        attempt=_p1_attempt + 1,
                        wait_seconds=wait,
                    )
                    await _asyncio_p1.sleep(wait)
                    continue
                logger.error("PASS 1 Failed (HTTP)", error=str(e))
                raise AIServiceError("Gemini", f"Hikaye yazılamadı: {str(e)}")
            except Exception as e:
                logger.error("PASS 1 Failed", error=str(e))
                raise AIServiceError("Gemini", f"Hikaye yazılamadı: {str(e)}")

        raise AIServiceError("Gemini", "Hikaye yazma tüm denemelerde başarısız (rate limit).")

    # =========================================================================
    # PASS 2: TECHNICAL DIRECTOR - Format & Scene Descriptions
    # =========================================================================

    async def _pass2_format_story(
        self,
        story_text: str,
        child_name: str,
        child_age: int,
        child_gender: str,
        visual_character_description: str = "",
        scenario_name: str = "",
        location_constraints: str = "",
        fixed_outfit: str = "",
        expected_page_count: int = 0,
    ) -> StoryResponse:
        """
        PASS 2: Technical Director - Format story and generate SCENE DESCRIPTIONS.

        ⚠️ IMPORTANT: This generates scene_description WITHOUT style!
        Style is added later in _compose_visual_prompts (SINGLE SOURCE OF TRUTH).

        Takes the beautiful story from Pass 1 and:
        - Splits into pages
        - Generates scene descriptions for each page (NO STYLE!)
        - Outputs structured JSON

        Args:
            story_text: Beautiful story from Pass 1
            visual_character_description: DOUBLE LOCKING character description
            scenario_name: Scenario name for location context
            location_constraints: Required location elements from scenario
            fixed_outfit: Consistent clothing for all pages (outfit lock)

        Returns:
            StoryResponse with pages and scene descriptions (NO STYLE!)
        """
        # ========== INPUT SANITIZATION (Security) ==========
        child_name = sanitize_for_prompt(child_name, max_length=50, field_name="child_name")

        # Use "child" instead of "boy/girl" to prevent diffusion model from
        # overriding PuLID face reference with a generic gendered archetype.
        clothing = (fixed_outfit or "").strip()

        # Character description for scene descriptions
        if visual_character_description:
            char_desc = sanitize_for_prompt(
                visual_character_description, max_length=300, field_name="char_desc"
            )
        else:
            char_desc = f"a {child_age}-year-old child named {child_name}"

        # ========== LOCATION CONSTRAINTS FROM SCENARIO ==========
        location_hint = ""
        if location_constraints:
            location_hint = f"""
📍 LOKASYON KISITLAMALARI (HER SAHNEDE KULLAN!):
{location_constraints}
ASLA bu lokasyon dışında mekan yazma!
"""

        # Scenario context
        scenario_hint = ""
        if scenario_name:
            scenario_hint = f"""
🗺️ SENARYO: {scenario_name}
Tüm sahneler bu senaryoya uygun olmalı!
"""

        # ========== DYNAMIC PROMPT LOADING ==========
        # Fetch system prompt from database (with hardcoded fallback)
        director_system = await self._get_prompt("AI_DIRECTOR_SYSTEM", AI_DIRECTOR_SYSTEM)

        technical_prompt = f"""{director_system}
{scenario_hint}
{location_hint}

🎬 TEKNİK YÖNETMENLİK GÖREVİN:

Aşağıdaki güzel hikayeyi al ve TEKNİK FORMATA dönüştür.
HİKAYE METNİNİ DEĞİŞTİRME - sadece sayfalara böl ve SAHNE TANIMI ekle!

📏 SAYFA SAYISI KURALI (ÇOK ÖNEMLİ!):
Hikayeyi TAM {expected_page_count if expected_page_count > 0 else 'uygun sayıda'} sayfaya böl.
{'KAPAK (page_number: 0) + İÇ SAYFALAR (page_number: 1 ile ' + str(expected_page_count - 1) + ').' if expected_page_count > 0 else ''}
{'TOPLAM ' + str(expected_page_count) + ' adet page objesi döndür — ne eksik ne fazla!' if expected_page_count > 0 else ''}

⚠️ ÖNEMLİ: scene_description içinde STYLE OLMAYACAK!
Style (Pixar, anime, watercolor vb.) ayrıca eklenecek - sen SADECE sahneyi tarif et!

📖 HİKAYE:
{story_text}

📚 KİTAP ADI KURALI (ÇOK ÖNEMLİ!):
title alanına KİŞİSELLEŞTİRİLMİŞ kitap adı yaz! Çocuğun adını İÇERMELİ!
✅ DOĞRU örnekler: "{child_name}'ın Kapadokya Macerası", "{child_name}'ın Büyülü Yolculuğu", "{child_name} ve Peri Bacaları"
❌ YANLIŞ: "Hikaye", "Masal", "Macera", "Bir Hikaye" — bunlar YASAK!

📋 ÇIKTI FORMATI (JSON):
⛔ KAPAK KURALI (KESİNLİKLE UYULACAK):
- page_number=0 "text" alanına SADECE kitap başlığını yaz — "title" alanıyla AYNI olmalı!
- page_number=0 "text" alanına HİÇBİR HİKAYE CÜMLESİ YAZMA! Hikaye page_number=1'den başlar.
- page_number=1 = hikayenin GERÇEK 1. sayfası (ilk paragraf buraya gelir)
{{
  "title": "{child_name}'ın Büyülü Macerası",
  "pages": [
    {{
      "page_number": 0,
      "text": "{child_name}'ın Büyülü Macerası",
      "scene_description": "[LOCATION]. A {child_age}-year-old child named {child_name} [ACTION]. Warm light. Clear sky in upper third for title."
    }},
    {{
      "page_number": 1,
      "text": "Hikayenin İLK PARAGRAFI (giriş) — [SAYFA 1] ile başlayan metin. DEĞİŞTİRME!",
      "scene_description": "[LOCATION and setting]. A {child_age}-year-old child named {child_name} [ACTION]. [LIGHTING]."
    }},
    ... (page 2, 3, ... tüm iç sayfalar)
  ]
}}

⭐ KARAKTER KİMLİĞİ (Referans — scene_description'a KOPYALAMA, sadece isim ve aksiyon yaz):
Çocuğun kimliği: "{char_desc}"
Bu bilgiyi scene_description'a YAZMA — sistem karakter bloğunu şablonla otomatik ekler.
scene_description'da sadece "{child_name}" ismini kullan, fiziksel tanım YAZMA.

👔 KIYAFET: scene_description'a kıyafet YAZMA! Sistem "{clothing}" kıyafetini şablonla otomatik ekler.
Sadece aksesuar/ekipman yazabilirsin: sırt çantası, büyüteç, harita vb.
⛔ DÖNEM KIYAFETİ YASAK: Tarihsel mekanlarda bile çocuğu dönem kıyafeti ile TANIMLAMAYACAKSIN! "wearing tunic", "animal skin wrap", "toga", "loincloth" gibi dönem kıyafetleri YAZMA! Çocuk KENDİ günlük kıyafetlerini giyer — sistem bunu yönetir.

💇 SAÇ: scene_description'a saç tasviri YAZMA! Sistem saç bilgisini şablonla otomatik ekler. "long hair", "curly hair", "braids" gibi saç ifadeleri KULLANMA!

❌ SCENE_DESCRIPTION İÇİNDE BUNLAR OLMAYACAK:
- Pixar, Disney, Ghibli, anime, cartoon, watercolor gibi STYLE kelimeleri
- "Children's book illustration", "storybook style" gibi ifadeler
- Art style referansları

✅ SCENE_DESCRIPTION (tekrarsız, 2–4 cümle — görselde hikaye detayı zengin olsun):
- Fiziksel mekan ve ortam detayları (lokasyon kısıtlamalarına uygun; ikonik öğeler: bacalar, balonlar, mağara girişi vb.)
- Karakter AKSİYONU ve POZ (en önemli)
- Hikayedeki nesneler/aksesuarlar/evcil hayvan (sincap, kedi, çanta, büyüteç vb.) sahneye dahil et
- Işık (sahneye uygun kısa ifade; sen seç)
- Kompozisyon/çerçeve YAZMA: "wide shot", "full body visible", "child 30%", "environment 70%", "natural proportions", "same clothing on every page" — sistem bunları TEK SEFER ekler. Sen yazma!
- Sinematik/lens YOK: wide-angle, f/8, cinematic, epic YOK

🎬 AKSİYON KURALI (ÇOK ÖNEMLİ!):
Çocuk HER SAHNEDE aktif olmalı — sadece durup bakmak YASAK!
Hikayedeki eylemleri sahne açıklamasına YANSIT:
- Hikayede kaplumbağa görüyorsa → "kneeling down to gently touch a small turtle"
- Hikayede balık izliyorsa → "leaning over the railing to watch the fish swimming below"
- Hikayede mağara keşfediyorsa → "stepping into a dark cave entrance holding a lantern"
- Hikayede balona biniyorsa → "leaning excitedly over the basket edge of a hot air balloon"
- Hikayede harita buluyorsa → "unrolling an old map on a stone surface, eyes wide"
Çocuğun yüz ifadesi hikayeyle uyumlu olmalı (merak, heyecan, şaşkınlık, korku vb.)

🐿️ ÖNEMLİ GÖRSEL ÖĞELER (Hikaye–görsel uyumu):
Hikayedeki önemli öğeleri scene_description'a MUTLAKA dahil et: evcil hayvanlar (sincap, kedi, kaplumbağa vb.), çantalar, eşyalar, aksesuarlar.
Örn: Omuzda sincap varsa "with a small pet squirrel on her shoulder" ekle. Çantada büyüteç varsa "with a magnifying glass in her backpack" ekle.

🐾 HAYVAN TUTARLILIĞI (ÇOK KRİTİK!):
Hikayede bir hayvan arkadaş varsa, scene_description'da HER SAYFADA AYNI FİZİKSEL TANIMI kullan!
İlk göründüğü sayfadaki tanımı (renk, tür, boyut) birebir KOPYALA ve her sayfada tekrarla.
Örnek: İlk sayfa "a small white fluffy dog with brown ears" → TÜM sayfalarda aynısını yaz!
ASLA sayfalar arasında hayvanın rengini, boyutunu, türünü DEĞİŞTİRME!

⚠️ ANATOMİK DOĞRULUK:
Hayvanlar insan gibi davranamaz. "holding hands with a dog" YASAKDIR — köpeğin eli yok!
Doğru: "running alongside the dog", "the dog trotting beside the child", "petting the dog"
Hayvanları GERÇEK hayvan davranışlarıyla tanımla!

⚠️ KRİTİK KURALLAR:
1. HİKAYE METNİNİ DEĞİŞTİRME! Yazarın yazdığını koru!
2. scene_description zengin ama tekrarsız: mekan + ortam detayları + aksiyon + önemli nesneler/evcil hayvan + ışık (2–4 cümle). Görselde hikaye detayı net görünsün. Işığı sahneye göre sen seç. Aynı fikri iki kez yazma!
3. scene_description içinde STYLE ve KOMPOZİSYON YOK: "2D", "3D", "Pixar", "illustration", "watercolor", "storybook", "wide shot", "full body visible", "child 30%", "same clothing on every page", "natural proportions" YAZMA — sistem ekler!
4. Lokasyon MUTLAKA senaryo kısıtlamalarına uygun!
5. Kapak (page 0) için: scene_description iç sayfalarla AYNI TONDA olmalı — çocuk bir aksiyon/sahne içinde, lokasyon arka planda. "A breathtaking panoramic view" gibi EPIK/PANORAMIK ifadeler KULLANMA! İç sayfayla aynı format: mekan + çocuğun aksiyonu + ışık. Üst kısım açık gökyüzü/boşluk olsun.
6. scene_description SADECE İNGİLİZCE! Türkçe (Geniş çekim, Altta metin alanı vb.) KULLANMA!
7. ⛔ scene_description'a ASLA Türkçe hikaye metnini KOPYALAMA! "text" alanındaki Türkçe metin ile "scene_description" tamamen FARKLI olmalı. scene_description = İngilizce görsel sahne tasviri. text = Türkçe hikaye metni. ASLA birbirinin kopyası olmasın!
8. ⛔ Kapak (page 0) "text" alanına SADECE kişiselleştirilmiş Türkçe KİTAP BAŞLIĞI yaz ("{child_name}" + senaryo adı). ASLA "Hikaye", "Masal" gibi genel isimler koyma! Kapak sayfasına HİKAYE METNİ (paragraf, giriş, cümle) YAZMA — kapakta sadece başlık gösterilir, hikaye metni orada kullanılmaz.
9. ⛔ Hikaye metni MUTLAKA sayfa 1'den başlar. İlk paragrafı (giriş) page 1 "text" alanına koy. Böylece kitap açıldığında 1. sayfa hikayenin başlangıcı olur; kapakta yazdığın metin boşta kalmaz.

ŞİMDİ JSON DÖNDÜR:"""

        import asyncio as _asyncio

        technical_url = get_gemini_technical_url()
        _pass2_max_retries = 4
        _pass2_base_wait = 8  # saniye — free tier 15 RPM; kısa beklemeler yetmiyor

        raw_text = ""
        for _p2_attempt in range(_pass2_max_retries):
            try:
                logger.info(
                    "PASS 2: Technical Director - Formatting",
                    model=self.technical_model,
                    story_length=len(story_text),
                    attempt=_p2_attempt + 1,
                )

                client = self._get_gemini_client()
                response = await client.post(
                    f"{technical_url}?key={self.api_key}",
                    json={
                        "contents": [{"parts": [{"text": technical_prompt}]}],
                        "generationConfig": {
                            "temperature": 0.5,
                            "topK": 40,
                            "topP": 0.9,
                            "maxOutputTokens": 65536,
                            "responseMimeType": "application/json",
                        },
                        "safetySettings": [
                            {
                                "category": "HARM_CATEGORY_HARASSMENT",
                                "threshold": "BLOCK_MEDIUM_AND_ABOVE",
                            },
                            {
                                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                                "threshold": "BLOCK_MEDIUM_AND_ABOVE",
                            },
                            {
                                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                                "threshold": "BLOCK_MEDIUM_AND_ABOVE",
                            },
                            {
                                "category": "HARM_CATEGORY_HATE_SPEECH",
                                "threshold": "BLOCK_MEDIUM_AND_ABOVE",
                            },
                        ],
                    },
                )
                response.raise_for_status()

                data = response.json()
                parts = data["candidates"][0]["content"]["parts"]
                raw_text = _extract_text_from_parts(parts)

                story_data = self._extract_and_repair_json(raw_text)
                story_response = StoryResponse(**story_data)

                actual_count = len(story_response.pages)
                logger.info(
                    "PASS 2 Complete: Story formatted",
                    title=story_response.title,
                    page_count=actual_count,
                    expected_page_count=expected_page_count,
                )

                # Page count validation — retry if mismatch (tolerance ±1)
                if expected_page_count > 0:
                    diff = actual_count - expected_page_count
                    if abs(diff) > 1 and _p2_attempt < _pass2_max_retries - 1:
                        logger.warning(
                            "PASS 2 page count mismatch — retrying",
                            expected=expected_page_count,
                            actual=actual_count,
                            attempt=_p2_attempt + 1,
                        )
                        await _asyncio.sleep(2)
                        continue
                    if diff > 0:
                        logger.warning(
                            "PASS 2 trimming excess pages",
                            expected=expected_page_count,
                            actual=actual_count,
                            trimmed=diff,
                        )
                        story_response.pages = story_response.pages[:expected_page_count]
                    elif diff < 0:
                        logger.warning(
                            "PASS 2 page count shortage (accepted after retries)",
                            expected=expected_page_count,
                            actual=actual_count,
                            shortage=abs(diff),
                        )

                # ── Kapak sayfası metin düzeltmesi ──
                # AI bazen page_number=0'a hikaye metni koyuyor. Eğer kapak metni
                # başlıkla eşleşmiyorsa (hikaye paragrafı ise), o metni page_number=1
                # olarak öne ekle ve diğer sayfaları kaydır — böylece 1. sayfa metni kaybolmaz.
                _cover_page = next((p for p in story_response.pages if p.page_number == 0), None)
                if _cover_page and story_response.title:
                    _cover_text = (_cover_page.text or "").strip()
                    _title_text = story_response.title.strip()
                    # Kapak metni başlıkla eşleşmiyorsa ve 30 karakterden uzunsa hikaye metnidir
                    _is_story_text = (
                        _cover_text != _title_text
                        and len(_cover_text) > 30
                        and not _cover_text.lower().startswith(_title_text[:10].lower())
                    )
                    if _is_story_text:
                        logger.warning(
                            "COVER_TEXT_IS_STORY: page_number=0 contains story text, rescuing as page 1",
                            cover_text_preview=_cover_text[:80],
                            title=_title_text,
                        )
                        # Kapak metnini başlıkla düzelt
                        _cover_page.text = _title_text
                        # Kurtarılan metni page_number=1 olarak öne ekle.
                        # scene_description olarak mevcut page_number=1'inkini kullan (varsa),
                        # yoksa kapak sahnesini kullan (görsel üretimde yine de çalışır).
                        _existing_p1 = next((p for p in story_response.pages if p.page_number == 1), None)
                        _rescued_scene = (
                            _existing_p1.scene_description if _existing_p1 else _cover_page.scene_description
                        )
                        _rescued_page = PageContent(
                            page_number=1,
                            text=_cover_text,
                            scene_description=_rescued_scene,
                        )
                        _other_pages = [p for p in story_response.pages if p.page_number != 0]
                        # Kaydır: her sayfanın page_number'ını +1 artır
                        for _p in _other_pages:
                            _p.page_number += 1
                        # Yeni listeyi oluştur: kapak + kurtarılan sayfa + diğerleri
                        story_response.pages = (
                            [_cover_page, _rescued_page] + _other_pages
                        )
                        logger.info(
                            "COVER_TEXT_RESCUED: page count after rescue",
                            page_count=len(story_response.pages),
                        )

                return story_response

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429 and _p2_attempt < _pass2_max_retries - 1:
                    wait = _pass2_base_wait * (2 ** _p2_attempt)
                    logger.warning(
                        "PASS 2 rate limited (429) — retrying",
                        attempt=_p2_attempt + 1,
                        wait_seconds=wait,
                    )
                    await _asyncio.sleep(wait)
                    continue
                logger.error("PASS 2 Failed (HTTP)", error=str(e))
                raise AIServiceError("Gemini", f"Teknik formatlama başarısız: {str(e)}")

            except json.JSONDecodeError as e:
                logger.error(
                    "PASS 2 JSON Parse Error",
                    error=str(e),
                    raw_preview=raw_text[-500:] if raw_text else "N/A",
                )
                raise AIServiceError("Gemini", "Hikaye formatlanamadı.")
            except Exception as e:
                logger.error("PASS 2 Failed", error=str(e))
                raise AIServiceError("Gemini", f"Teknik formatlama başarısız: {str(e)}")

        raise AIServiceError("Gemini", "Teknik formatlama tüm denemelerde başarısız (rate limit).")

    def _build_child_description(
        self,
        child_name: str,
        child_age: int,
        child_gender: str | None,
    ) -> str:
        """Build English child description for visual prompts.

        Uses 'child' instead of 'boy/girl' to let PuLID face reference
        determine gender — avoids generic gendered archetype overriding likeness.
        """
        return f"a {child_age} year old child named {child_name}"

    # Prompt leakage: template/instruction text must never end up in visual_prompt for Fal.ai
    # Turkish style/composition phrases that must NEVER appear in scene_description (FAL expects English)
    TURKISH_LEAKAGE = (
        "2 boyutlu",
        "çocuk resimli kitap",
        "karikatür illüstrasyonu",
        "Altta metin alanı",
        "Geniş çekim",
        "çerçevenin %30",
        "STİL:",
        "orta kalınlıkta kontürlü",
        "sadeleştirilmiş şekiller",
        "yumuşak pastel",
        "ince detaylar",
    )
    CONTAMINATION_MARKERS = (
        "GİRDİ DEĞİŞKENLERİ",
        '"pages":',
        "Sen, ödüllü",
        "Sen, odullu",  # ASCII fallback
        "ÇIKTI FORMATI",
        "Görevin:",
        "**GİRDİ",
        "**ÇIKTI",
        "KÜLTÜREL RUHUNU",
        "Görsel Stil:",
        "Sayfa Sayısı:",
        "HİKAYE RUHU VE TEMALAR",
        "HİKAYE AKIŞI",
        "GÖRSEL PROMPT KURALLARI",
        "ÇIKTI FORMATI (JSON)",
    )
    # PASS-2 scene_description'da olmaması gereken ifadeler (template/lens/style). Otomatik silinir.
    FORBIDDEN_IN_SCENE = (
        "space for title",
        "title safe area",
        "empty space at bottom",
        "empty space at bottom for captions",
        "bottom text space",
        "caption area",
        "watermark",
        "logo",
        "lens",
        "camera",
        "dslr",
        "bokeh",
        "cinematic",
        "photorealistic",
        "render",
        "cgi",
        "anime",
        "ghibli",
        "miyazaki",
        "manga",
        "cel-shaded",
        "pixar",
        "disney",
        "unreal",
        "octane",
        "blender",
        "full bady",  # Gemini typo; kompozisyon şablonda "full body when scene allows"
        "full body visible",  # scene'de olmasın, COMPOSITION_RULES ekliyor
    )
    MAX_VISUAL_PROMPT_LENGTH = 1200

    def _is_visual_prompt_contaminated(self, prompt: str) -> bool:
        """True if prompt contains instruction/template text (must not be sent to Fal.ai)."""
        if not prompt:
            return True
        if len(prompt) > self.MAX_VISUAL_PROMPT_LENGTH:
            return True
        prompt_lower = prompt.lower()
        for marker in self.CONTAMINATION_MARKERS:
            if marker in prompt or marker.lower() in prompt_lower:
                return True
        return False

    # Style phrases that Gemini sometimes leaks INTO scene_description.
    # These must be stripped because style is injected later at compose.
    STYLE_LEAK_PHRASES = [
        # 2D / picture-book tokens
        "2D children's picture-book cartoon illustration",
        "2D children's picture-book",
        "children's picture-book cartoon illustration",
        "clean crisp lineart with medium outlines",
        "clean crisp lineart",
        "simplified shapes",
        "soft pastel color palette",
        "smooth soft shading with gentle gradients",
        "smooth soft shading",
        "subtle paper texture",
        "warm soft ambient light",
        "storybook illustration feel",
        "foreground/midground/background layering",
        "NO cinematic look",
        "NO film still",
        "NO lens terms",
        "NO volumetric effects",
        "NO dramatic contrast",
        # 3D / Pixar tokens
        "Pixar Animation Studios",
        "pixar-inspired",
        "3D animated children's book",
        "3D rendered illustration",
        "subsurface scattering",
        "smooth polished 3D",
        "gentle global illumination",
        # Watercolor tokens
        "watercolor painting on textured paper",
        "visible wet brush strokes",
        "paint bleeding at edges",
        # Default storybook
        "soft children's book illustration",
        "warm pastel colors",
        "storybook art",
        "cozy lighting",
    ]

    def _sanitize_scene_description(self, scene_desc: str) -> str:
        """Remove instruction/template/style leakage from scene_description. PASS-2 çıktı zorunlu temizlik."""
        if not scene_desc:
            return "A child in an adventure scene."
        import re as _re

        # Very long scene_desc is almost certainly template leakage
        if len(scene_desc) > 1500:
            scene_desc = scene_desc[:1500]
        scene_lower = scene_desc.lower()
        earliest = len(scene_desc)
        # Strip Turkish style/composition text (FAL expects English only)
        for phrase in self.TURKISH_LEAKAGE:
            idx = scene_desc.find(phrase)
            if idx == -1:
                idx = scene_lower.find(phrase.lower())
            if idx != -1 and idx < earliest:
                earliest = idx
        for marker in self.CONTAMINATION_MARKERS:
            idx = (
                scene_desc.find(marker)
                if marker in scene_desc
                else scene_lower.find(marker.lower())
            )
            if idx != -1 and idx < earliest:
                earliest = idx
        if earliest < len(scene_desc):
            scene_desc = scene_desc[:earliest].strip()

        # Strip FORBIDDEN_IN_SCENE (template/lens/style — tek kaynak template'te)
        for phrase in self.FORBIDDEN_IN_SCENE:
            pattern = _re.compile(_re.escape(phrase), _re.IGNORECASE)
            scene_desc = pattern.sub("", scene_desc)
        # Strip leaked style phrases (case-insensitive)
        for phrase in self.STYLE_LEAK_PHRASES:
            pattern = _re.compile(_re.escape(phrase), _re.IGNORECASE)
            scene_desc = pattern.sub("", scene_desc)
        # Clean up messy punctuation left after stripping
        scene_desc = _re.sub(r"\.{2,}", ".", scene_desc)
        scene_desc = _re.sub(r",\s*,", ",", scene_desc)
        scene_desc = _re.sub(r"\s{2,}", " ", scene_desc)
        scene_desc = scene_desc.strip().strip(",").strip(".")
        scene_desc = scene_desc.strip()

        if not scene_desc or len(scene_desc) < 20:
            return "A child in an adventure scene."

        # ── Türkçe metin tespiti ──
        # Gemini bazen Türkçe hikaye metnini scene_description'a kopyalıyor.
        # Türkçe'ye özgü karakterler (ş, ğ, ı, İ, Ş, Ğ) ve yaygın Türkçe kelimeler tespit et.
        _TURKISH_SPECIFIC_CHARS = set("\u015f\u011f\u0131\u015e\u011e\u0130")  # ş ğ ı Ş Ğ İ
        _turkish_char_count = sum(1 for ch in scene_desc if ch in _TURKISH_SPECIFIC_CHARS)

        # 2+ Türkçe-özel karakter = kesinlikle Türkçe metin
        if _turkish_char_count >= 2:
            logger.warning(
                "Turkish text detected in scene_description (%d Turkish chars), replacing with fallback",
                _turkish_char_count,
                original=scene_desc[:120],
            )
            return "A child in an adventure scene."

        # Türkçe placeholder kontrolü — kısa placeholder metinleri
        _TURKISH_PLACEHOLDERS = [
            "kapak için", "kapak metni", "kısa metin", "hikaye metni",
            "sayfa metni", "başlık", "açıklama",
            "cover text placeholder",  # Pass-2 örneğinden kopyalanan placeholder
        ]
        scene_lower_check = scene_desc.lower()
        for _tp in _TURKISH_PLACEHOLDERS:
            if _tp in scene_lower_check:
                logger.warning(
                    "Placeholder detected in scene_description, replacing with fallback",
                    original=scene_desc[:120],
                )
                return "A child in an adventure scene."

        # Yaygın Türkçe kelime kontrolü (3+ Türkçe kelime = muhtemelen Türkçe)
        _TURKISH_COMMON = [
            "bir ", "ile ", "için ", "diye ", "gibi ", "ama ", "çok ",
            "dedi", "oldu", "geld", "gitt", "bakt", "koştu", "gördü",
            "fısıldadı", "mırıldandı", "söyledi", "sordu",
        ]
        _tr_word_count = sum(1 for w in _TURKISH_COMMON if w in scene_lower_check)
        if _tr_word_count >= 3:
            logger.warning(
                "Turkish words detected in scene_description (%d matches), replacing",
                _tr_word_count,
                original=scene_desc[:120],
            )
            return "A child in an adventure scene."

        return scene_desc[:800]

    def _compose_visual_prompts(
        self,
        story_response: StoryResponse,
        scenario: Scenario,
        child_name: str,
        child_description: str,
        visual_style: str,
        fixed_outfit: str = "",
        learning_outcome_visual_hints: list[str] | None = None,
        cover_template_en: str = "",
        inner_template_en: str = "",
    ) -> list[FinalPageContent]:
        """
        Compose SCENE-ONLY visual prompts (NO style tokens). Style is injected at image API call only.

        Scenario templates are INPUT-only (for Gemini). visual_prompt = scene + outfit + composition
        (location, scene_description, text space at top/bottom). No 2D/3D/Pixar/Ghibli/Children's book illustration.

        Args:
            story_response: Raw story response with scene_description (no style!)
            scenario: Scenario WITH prompt templates
            child_name: Child's name
            child_description: Full child description
            visual_style: Ignored here; style is applied at image generation (single point).
            fixed_outfit: Consistent clothing for all pages
            learning_outcome_visual_hints: If set, at least one page must include one hint (e.g. toothbrush)

        Returns:
            List of pages with scene-only visual_prompt (no style tokens)
        """
        if getattr(settings, "book_pipeline_version", "3") == "3":
            raise AIServiceError(
                "Gemini",
                "V2 _compose_visual_prompts is disabled when BOOK_PIPELINE_VERSION=3. Use V3 pipeline only.",
            )
        # =====================================================================
        # STYLE INDEPENDENCE: visual_prompt = scene + outfit + composition ONLY.
        # Style (2D/3D/Pixar/Ghibli/Children's book illustration) is added only
        # at image API call via compose_visual_prompt(..., style_text=request.visual_style).
        # =====================================================================

        location_constraints = getattr(scenario, "location_constraints", "") or ""
        cultural_elements = getattr(scenario, "cultural_elements", None)

        logger.info(
            "[VISUAL] COMPOSE VISUAL PROMPTS - scene-only (no style tokens)",
            scenario_name=scenario.name if scenario else "unknown",
            has_location_constraints=bool(location_constraints),
            has_cultural_elements=bool(cultural_elements),
            fixed_outfit=fixed_outfit,
        )

        # Define location keywords for contamination check
        LOCATION_KEYWORDS: dict[str, list[str]] = {
            "cappadocia": [
                "cappadocia",
                "kapadokya",
                "fairy chimney",
                "peri bacasi",
                "hot air balloon",
            ],
            "istanbul": [
                "istanbul",
                "bosphorus",
                "galata",
                "hagia sophia",
                "ayasofya",
                "blue mosque",
                "sultanahmet",
                "hippodrome",
            ],
            "yerebatan": [
                "basilica cistern",
                "yerebatan",
                "medusa head",
            ],
            "gobeklitepe": ["gobekli tepe", "gobeklitepe", "urfa"],
            "catalhoyuk": ["catalhoyuk", "neolithic", "neolitik", "konya plain"],
            "sumela": ["sumela", "sumela monastery", "altindere", "karadag", "trabzon monastery"],
            "ephesus": ["ephesus", "efes", "celsus", "library of celsus"],
            "kudus": ["jerusalem", "kudus", "dome of the rock", "old city walls", "jerusalem stone"],
            "abusimbel": ["abu simbel", "ramesses", "ramses", "nefertari", "nubian", "lake nasser"],
            "tacmahal": ["taj mahal", "tac mahal", "agra", "mughal", "yamuna"],
            "underwater": ["underwater", "ocean", "coral", "fish", "mermaid"],
            "space": ["space station", "galaxy", "nebula", "asteroid", "spaceship"],
        }

        # Themes sharing a parent city — don't cross-flag each other
        _ISTANBUL_THEMES: set[str] = {"istanbul", "yerebatan", "sultanahmet", "galata"}
        COMPATIBLE_THEMES: dict[str, set[str]] = dict.fromkeys(_ISTANBUL_THEMES, _ISTANBUL_THEMES)

        # Style keywords that should NOT be in scene_description
        STYLE_KEYWORDS = [
            "pixar",
            "disney",
            "ghibli",
            "anime",
            "cartoon",
            "watercolor",
            "illustration",
            "3d render",
            "cel-shaded",
            "storybook",
            "children's book illustration",
        ]

        # Determine scenario theme: prefer DB theme_key, fallback to name-based detection
        scenario_theme = getattr(scenario, "theme_key", None) or None
        if not scenario_theme:
            scenario_lower = scenario.name.lower() if scenario else ""
            if "kapadokya" in scenario_lower or "cappadocia" in scenario_lower:
                scenario_theme = "cappadocia"
            elif "yerebatan" in scenario_lower or "cistern" in scenario_lower:
                scenario_theme = "yerebatan"
            elif "efes" in scenario_lower or "ephesus" in scenario_lower:
                scenario_theme = "ephesus"
            elif "göbeklitepe" in scenario_lower or "gobeklitepe" in scenario_lower:
                scenario_theme = "gobeklitepe"
            elif "çatalhöyük" in scenario_lower or "catalhoyuk" in scenario_lower:
                scenario_theme = "catalhoyuk"
            elif "sümela" in scenario_lower or "sumela" in scenario_lower:
                scenario_theme = "sumela"
            elif "sultanahmet" in scenario_lower:
                scenario_theme = "sultanahmet"
            elif "galata" in scenario_lower:
                scenario_theme = "galata"
            elif "kudüs" in scenario_lower or "kudus" in scenario_lower or "jerusalem" in scenario_lower:
                scenario_theme = "kudus"
            elif "abu simbel" in scenario_lower or "abusimbel" in scenario_lower:
                scenario_theme = "abusimbel"
            elif "tac mahal" in scenario_lower or "tacmahal" in scenario_lower:
                scenario_theme = "tacmahal"
            elif "istanbul" in scenario_lower:
                scenario_theme = "istanbul"
            elif "uzay" in scenario_lower or "space" in scenario_lower:
                scenario_theme = "space"
            elif "deniz" in scenario_lower or "underwater" in scenario_lower:
                scenario_theme = "underwater"

        final_pages = []

        for page in story_response.pages:
            scene_desc = self._sanitize_scene_description(page.scene_description)
            scene_lower = scene_desc.lower()

            # ==================== CONTAMINATION CHECKS ====================
            contamination_flags = []

            # Check 1: Location contamination (wrong scenario elements)
            allowed_themes = COMPATIBLE_THEMES.get(scenario_theme or "", {scenario_theme or ""})
            for theme, keywords in LOCATION_KEYWORDS.items():
                if theme not in allowed_themes:
                    for kw in keywords:
                        if kw in scene_lower:
                            contamination_flags.append(
                                f"LOCATION:{kw.upper()}_IN_{scenario_theme.upper() if scenario_theme else 'UNKNOWN'}"
                            )

            # Check 2: Style leaked into scene_description (should be style-free!)
            for style_kw in STYLE_KEYWORDS:
                if style_kw in scene_lower:
                    contamination_flags.append(f"STYLE_LEAK:{style_kw.upper()}")

            # Check 3: Duplicate scene starters
            if scene_lower.count("a wide-angle") > 1:
                contamination_flags.append("DUPLICATE_SCENE_STARTER")

            if contamination_flags:
                logger.warning(
                    "PROMPT CONTAMINATION DETECTED!",
                    page=page.page_number,
                    scenario=scenario.name if scenario else "unknown",
                    contamination=contamination_flags,
                    scene_preview=scene_desc[:150],
                )

            # ==================== COMPOSE FINAL PROMPT ====================
            # SINGLE SOURCE OF TRUTH: Use scenario templates OR fallback
            is_cover = page.page_number == 0

            # Build cultural background hint if available
            cultural_hint = ""
            if cultural_elements:
                primary = cultural_elements.get("primary", [])
                if primary:
                    cultural_hint = f" Background elements: {', '.join(primary[:3])}."

            from app.prompt_engine import compose_visual_prompt
            from app.prompt_engine.constants import (
                DEFAULT_COVER_TEMPLATE_EN,
                DEFAULT_INNER_TEMPLATE_EN,
            )

            location_en = getattr(scenario, "location_en", None) or ""
            scene_text = (scene_desc + cultural_hint).strip()
            if location_en:
                scene_text = f"{location_en} setting. {scene_text}".strip()

            # ── Kapak sayfası: İç sayfayla AYNI yapıda template kullan ──
            # Senaryo cover_prompt_template'leri farklı yapıda (uzun/epik) olduğu
            # için kapak-iç sayfa tutarsızlığına neden oluyordu. Artık kapak da
            # DEFAULT_COVER_TEMPLATE_EN kullanır: "A young child wearing ... {scene_description}."
            # COMPOSITION_RULES normalize_safe_area_and_composition tarafından eklenir.
            if is_cover:
                template_en = cover_template_en or DEFAULT_COVER_TEMPLATE_EN
                logger.info(
                    "Using unified cover template (same structure as inner pages)",
                    source="db_param" if cover_template_en else "default_constant",
                )
            else:
                # Senaryo page_prompt_template varsa iç sayfalar için kullan
                _scenario_page_tpl = (
                    getattr(scenario, "page_prompt_template", None) or ""
                ).strip()
                if (
                    _scenario_page_tpl
                    and "{scene_description}" in _scenario_page_tpl
                    and len(_scenario_page_tpl) < 500
                ):
                    # Sadece kisa/hafif template'ler compose_visual_prompt ile uyumlu.
                    # Agir template'ler (1500+ char) kendi COMPOSITION/STYLE bolumleri
                    # iceriyor ve composer ile cifte sarma + uzunluk asimi yapiyorlar.
                    template_en = _scenario_page_tpl.replace("{visual_style}", "")
                    logger.info(
                        "Using scenario page_prompt_template for inner page",
                        scenario=scenario.name if scenario else "?",
                        template_preview=template_en[:120],
                    )
                else:
                    template_en = inner_template_en or DEFAULT_INNER_TEMPLATE_EN

            visual_prompt, _ = compose_visual_prompt(
                scene_description=scene_text,
                is_cover=is_cover,
                template_en=template_en,
                clothing_description=fixed_outfit,
                story_title=story_response.title if is_cover else "",
            )
            if self._is_visual_prompt_contaminated(visual_prompt):
                logger.warning(
                    "[VISUAL] visual_prompt contaminated after build - using minimal safe prompt",
                    page=page.page_number,
                )
                visual_prompt, _ = compose_visual_prompt(
                    scene_description="A child in an adventure scene.",
                    is_cover=is_cover,
                    template_en=template_en,
                    clothing_description=fixed_outfit,
                    story_title=story_response.title if is_cover else "",
                )

            # ==================== ENFORCE LOCATION CONSTRAINTS ====================
            if location_constraints:
                # Check if location is already in prompt
                loc_lower = location_constraints.lower()
                prompt_lower = visual_prompt.lower()
                # Only inject if missing (check first few words of constraint)
                loc_keywords = [w.strip() for w in loc_lower.split(",")[:2] if len(w.strip()) > 3]
                missing_loc = not any(kw in prompt_lower for kw in loc_keywords)
                if missing_loc:
                    # Truncate long constraints to avoid drowning clothing tokens
                    loc_short = (
                        location_constraints[:200].rsplit(" ", 1)[0]
                        if len(location_constraints) > 200
                        else location_constraints
                    )
                    visual_prompt = f"{visual_prompt} Setting: {loc_short}."
                    logger.info(f"📍 INJECTED location_constraints into page {page.page_number}")

            # Determine page metadata: cover vs inner
            is_cover_page = page.page_number == 0
            current_page_index = len(final_pages)  # 0-based position in book
            story_pn: int | None = None if is_cover_page else page.page_number

            # Create final page content (scene-only; no style tokens)
            final_pages.append(
                FinalPageContent(
                    page_number=page.page_number,
                    text=page.text,
                    scene_description=scene_desc,
                    visual_prompt=visual_prompt,  # Scene-only: style added at image API
                    page_type="cover" if is_cover_page else "inner",
                    page_index=current_page_index,
                    story_page_number=story_pn,
                    composer_version="v3",
                    pipeline_version="v3",
                )
            )

            logger.info(
                "PROMPT COMPOSED (scene-only)",
                page=page.page_number,
                page_type="cover" if is_cover_page else "inner",
                page_index=current_page_index,
                story_page_number=story_pn,
                pipeline_version="v3",
                scene_preview=scene_desc[:80] + "...",
                final_length=len(visual_prompt),
                contamination=contamination_flags if contamination_flags else "CLEAN",
            )

        # ==================== LEARNING OUTCOME VISUAL: at least one page with hint ====================
        if learning_outcome_visual_hints:
            prompt_lowers = [fp.visual_prompt.lower() for fp in final_pages]
            any_has_hint = any(
                any(h.lower() in p for h in learning_outcome_visual_hints) for p in prompt_lowers
            )
            if not any_has_hint:
                # Inject first hint into first inner page (page_number 1)
                inject_phrase = f" including a {learning_outcome_visual_hints[0]}"
                for fp in final_pages:
                    if fp.page_number == 1:
                        fp.visual_prompt = (
                            fp.visual_prompt.rstrip(". ") + inject_phrase + "."
                        ).strip()
                        if len(fp.visual_prompt) > self.MAX_VISUAL_PROMPT_LENGTH:
                            fp.visual_prompt = fp.visual_prompt[: self.MAX_VISUAL_PROMPT_LENGTH]
                        logger.info(
                            "[VISUAL] Injected learning outcome hint into page 1",
                            hint=learning_outcome_visual_hints[0],
                        )
                        break

        return final_pages

    # =========================================================================
    # V3: BLUEPRINT PIPELINE — 2-pass with structured blueprint
    # =========================================================================

    async def _pass0_generate_blueprint(
        self,
        *,
        child_name: str,
        child_age: int,
        child_description: str,
        location_key: str,
        location_display_name: str,
        visual_style: str,
        magic_items: list[str],
        page_count: int,
        scenario: Scenario,
        book_title: str = "",
        value_name: str = "",
    ) -> dict:
        """PASS-0: Generate story blueprint JSON.

        Returns the parsed blueprint dict with page roles, cultural hooks,
        magic item distribution, and visual briefs.
        """
        import asyncio as _asyncio_bp

        from app.prompt_engine.blueprint_prompt import (
            BLUEPRINT_SYSTEM_PROMPT,
            build_blueprint_task_prompt,
        )
        from app.prompt_engine.scenario_bible import get_scenario_bible

        # Resolve scenario bible
        db_bible = getattr(scenario, "scenario_bible", None)
        bible = get_scenario_bible(location_key, db_bible=db_bible)

        system_prompt = await self._get_prompt(
            "BLUEPRINT_SYSTEM_PROMPT", BLUEPRINT_SYSTEM_PROMPT
        )

        # Extract story structure from scenario (hikaye yapısı, zone progression, epic moments)
        story_structure = getattr(scenario, "story_prompt_tr", "") or ""
        
        task_prompt = build_blueprint_task_prompt(
            child_name=child_name,
            child_age=child_age,
            child_description=child_description,
            location_key=location_key,
            location_display_name=location_display_name,
            visual_style=visual_style,
            magic_items=magic_items,
            page_count=page_count,
            bible=bible,
            book_title=book_title,
            value_name=value_name,
            story_structure=story_structure,  # YENİ: Senaryo yapısını blueprint'e dahil et
        )

        full_prompt = system_prompt + "\n\n" + task_prompt

        blueprint_url = get_gemini_story_url()
        max_retries = 3
        base_wait = 10

        for attempt in range(max_retries):
            try:
                logger.info(
                    "PASS-0: Generating blueprint",
                    model=self.story_model,
                    page_count=page_count,
                    location=location_key,
                    attempt=attempt + 1,
                )

                client = self._get_gemini_client()
                response = await client.post(
                    f"{blueprint_url}?key={self.api_key}",
                    json={
                        "contents": [{"parts": [{"text": full_prompt}]}],
                        "generationConfig": {
                            "temperature": 0.7,
                            "topK": 40,
                            "topP": 0.90,
                            "maxOutputTokens": 16000,
                            "responseMimeType": "application/json",
                        },
                        "safetySettings": [
                            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                        ],
                    },
                )
                response.raise_for_status()

                data = response.json()
                parts = data["candidates"][0]["content"]["parts"]
                raw_text = _extract_text_from_parts(parts)
                blueprint = self._extract_and_repair_json(raw_text)

                # Gemini bazen array döndürebilir — dict'e wrap et
                if isinstance(blueprint, list):
                    logger.warning(
                        "PASS-0: Blueprint as list, wrapping to dict",
                        list_len=len(blueprint),
                    )
                    blueprint = {"pages": blueprint}

                # Page count pre-check: retry if mismatch and retries remain
                bp_pages = blueprint.get("pages", [])
                if len(bp_pages) != page_count and attempt < max_retries - 1:
                    logger.warning(
                        "PASS-0: Blueprint page count mismatch, retrying",
                        expected=page_count,
                        got=len(bp_pages),
                        attempt=attempt + 1,
                    )
                    await _asyncio_bp.sleep(base_wait * (attempt + 1))
                    continue

                # Full schema repair (page count, story_arc, act, emotional_state…)
                blueprint, bp_repairs = _repair_blueprint(blueprint, page_count)
                if bp_repairs:
                    logger.info(
                        "PASS-0: Blueprint repaired",
                        repairs=bp_repairs,
                    )

                logger.info(
                    "PASS-0: Blueprint generated",
                    title=blueprint.get("title", ""),
                    pages=len(blueprint.get("pages", [])),
                    repairs_count=len(bp_repairs),
                )
                return blueprint

            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 429 and attempt < max_retries - 1:
                    wait = base_wait * (attempt + 1)
                    logger.warning("PASS-0: Rate limited, waiting", wait=wait)
                    await _asyncio_bp.sleep(wait)
                    continue
                raise AIServiceError(
                    "Gemini",
                    f"Blueprint oluşturulamadı (HTTP {exc.response.status_code})",
                    reason_code="BLUEPRINT_HTTP_FAIL",
                ) from exc
            except (KeyError, IndexError, json.JSONDecodeError) as exc:
                if attempt < max_retries - 1:
                    await _asyncio_bp.sleep(base_wait)
                    continue
                raise AIServiceError(
                    "Gemini",
                    f"Blueprint JSON ayrıştırma hatası: {type(exc).__name__}",
                    reason_code="BLUEPRINT_PARSE_FAIL",
                ) from exc

        raise AIServiceError(
            "Gemini",
            "Blueprint tüm denemelerde oluşturulamadı.",
            reason_code="BLUEPRINT_ALL_RETRIES_EXHAUSTED",
        )

    async def _pass1_generate_pages(
        self,
        *,
        blueprint: dict,
        child_name: str,
        child_age: int,
        child_description: str,
        visual_style: str,
        location_display_name: str,
        magic_items: list[str],
        page_count: int,
        outcomes: list | None = None,
        location_constraints: str = "",
        skip_visual_prompts: bool = False,
    ) -> list[dict]:
        """PASS-1: Generate story pages with text_tr + image_prompt_en + negative_prompt_en.

        Takes the blueprint from PASS-0 and produces the final page content.
        outcomes: used for V3 value_message_tr injection into narrative.
        """
        import asyncio as _asyncio_pg

        from app.prompt_engine import (
            PAGE_GENERATION_SYSTEM_PROMPT,
            build_page_task_prompt,
        )
        from app.prompt_engine.style_adapter import get_style_instructions_for_prompt

        style_instructions = get_style_instructions_for_prompt(visual_style)
        value_message_tr = get_value_message_tr_for_outcomes(outcomes or [])

        # Resolve 3-beat emotion arc for the selected value
        value_emotion_beats: dict[str, str] | None = None
        if value_message_tr:
            for outcome in outcomes or []:
                _name = (getattr(outcome, "name", None) or str(outcome)).lower().strip()
                _name_norm = _normalize_value_key(_name)
                for key, beats in VALUE_EMOTION_BEATS.items():
                    if key in _name or _name in key or _normalize_value_key(key) in _name_norm:
                        value_emotion_beats = beats
                        break
                if value_emotion_beats:
                    break

        system_prompt = await self._get_prompt(
            "PAGE_GENERATION_SYSTEM_PROMPT", PAGE_GENERATION_SYSTEM_PROMPT
        )

        task_prompt = build_page_task_prompt(
            blueprint_json=blueprint,
            child_name=child_name,
            child_age=child_age,
            child_description=child_description,
            visual_style=visual_style,
            style_instructions=style_instructions,
            location_display_name=location_display_name,
            location_constraints=location_constraints,
            magic_items=magic_items,
            page_count=page_count,
            value_message_tr=value_message_tr,
            value_emotion_beats=value_emotion_beats,
            skip_visual_prompts=skip_visual_prompts,
        )

        full_prompt = system_prompt + "\n\n" + task_prompt

        pages_url = get_gemini_story_url()
        max_retries = 3
        base_wait = 10

        for attempt in range(max_retries):
            try:
                logger.info(
                    "PASS-1: Generating story pages",
                    model=self.story_model,
                    page_count=page_count,
                    attempt=attempt + 1,
                )

                client = self._get_gemini_client()
                response = await client.post(
                    f"{pages_url}?key={self.api_key}",
                    json={
                        "contents": [{"parts": [{"text": full_prompt}]}],
                        "generationConfig": {
                            "temperature": self.story_temperature,
                            "topK": 64,
                            "topP": 0.95,
                            "maxOutputTokens": 32000,
                            "responseMimeType": "application/json",
                        },
                        "safetySettings": [
                            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                        ],
                    },
                )
                response.raise_for_status()

                data = response.json()
                parts = data["candidates"][0]["content"]["parts"]
                raw_text = _extract_text_from_parts(parts)

                # Parse — may be a JSON array or object with "pages" key
                parsed = self._extract_and_repair_json(raw_text)
                if isinstance(parsed, list):
                    pages = parsed
                elif isinstance(parsed, dict) and "pages" in parsed:
                    pages = parsed["pages"]
                elif isinstance(parsed, dict):
                    pages = [parsed]
                else:
                    pages = []

                # Retry if too few pages and retries remain
                if len(pages) < page_count and attempt < max_retries - 1:
                    logger.warning(
                        "PASS-1: Page count mismatch, retrying",
                        expected=page_count,
                        got=len(pages),
                        attempt=attempt + 1,
                    )
                    await _asyncio_pg.sleep(base_wait * (attempt + 1))
                    continue

                # Full schema repair (pad missing, fill empty fields from blueprint)
                pages, pg_repairs = _repair_pages(pages, blueprint, page_count, skip_visual_prompts)
                if pg_repairs:
                    logger.info(
                        "PASS-1: Pages repaired",
                        repairs=pg_repairs,
                    )

                # Post-validation: check story quality
                _short_pages = [
                    p["page"] for p in pages
                    if len((p.get("text_tr") or "").strip()) < 30
                ]
                if _short_pages:
                    logger.warning(
                        "PASS-1: Short text pages detected",
                        short_pages=_short_pages,
                        total=len(pages),
                    )

                _last_text = (pages[-1].get("text_tr") or "").strip() if pages else ""
                _has_closure = any(
                    kw in _last_text.lower()
                    for kw in ["gülümsedi", "mutlu", "döndü", "veda", "ayrıl",
                               "hatırla", "öğren", "gurur", "teşekkür", "sarıl",
                               "eve", "geri", "sonunda", "artık"]
                ) if _last_text else False

                logger.info(
                    "PASS-1: Story pages generated",
                    pages=len(pages),
                    repairs_count=len(pg_repairs),
                    short_page_count=len(_short_pages),
                    has_closure_keywords=_has_closure,
                )
                return pages

            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 429 and attempt < max_retries - 1:
                    wait = base_wait * (attempt + 1)
                    logger.warning("PASS-1: Rate limited, waiting", wait=wait)
                    await _asyncio_pg.sleep(wait)
                    continue
                raise AIServiceError(
                    "Gemini",
                    f"Sayfa üretimi başarısız (HTTP {exc.response.status_code})",
                    reason_code="PAGE_HTTP_FAIL",
                ) from exc
            except (KeyError, IndexError, json.JSONDecodeError) as exc:
                if attempt < max_retries - 1:
                    await _asyncio_pg.sleep(base_wait)
                    continue
                raise AIServiceError(
                    "Gemini",
                    f"Sayfa JSON ayrıştırma hatası: {type(exc).__name__}",
                    reason_code="PAGE_PARSE_FAIL",
                ) from exc

        raise AIServiceError(
            "Gemini",
            "Sayfa üretimi tüm denemelerde başarısız.",
            reason_code="PAGE_ALL_RETRIES_EXHAUSTED",
        )

    @rate_limit_retry(service="gemini", max_attempts=2, timeout_attempts=1)
    async def generate_story_v3(
        self,
        scenario: Scenario,
        child_name: str,
        child_age: int,
        child_gender: str | None,
        outcomes: list[LearningOutcome],
        visual_style: str = "children's book illustration, soft colors",
        visual_character_description: str = "",
        page_count: int = 16,
        fixed_outfit: str = "",
        magic_items: list[str] | None = None,
        leading_prefix_override: str | None = None,
        style_block_override: str | None = None,
        generate_visual_prompts: bool = True,
    ) -> tuple[StoryResponse, list[FinalPageContent], str, dict]:
        """Generate a personalized story using V3 BLUEPRINT PIPELINE.

        V3 APPROACH:
        ============
        PASS-0 - "Blueprint Architect":
          - Generates structured plan (page roles, cultural hooks, magic items)
          - Output: Blueprint JSON

        PASS-1 - "Story Writer + Art Director":
          - Follows blueprint, generates text_tr + image_prompt_en + negative_prompt_en
          - Output: Pages JSON

        Validation:
          - Magic item count, cultural fact uniqueness, safety, family ban

        Returns:
            Tuple of (StoryResponse, list[FinalPageContent], fixed_outfit, blueprint_json)
        """
        import asyncio as _asyncio_v3

        from app.core.pipeline_events import PipelineTracer, mask_photo_url

        tracer = PipelineTracer.for_order(
            pipeline_version="v3",
            requested_page_count=page_count,
        )
        tracer.pipeline_start(
            scenario_id=str(getattr(scenario, "id", "") or ""),
            style_id="",
            child_photo_hash=mask_photo_url(visual_character_description[:8] if visual_character_description else None),
        )

        logger.info(
            "Starting V3 BLUEPRINT story generation",
            trace_id=tracer.trace_id,
            scenario=scenario.name,
            child_name=child_name,
            page_count=page_count,
            magic_items=magic_items,
        )

        # Resolve location info — SINGLE SOURCE: scenario only; normalize for anchors
        from app.prompt_engine.scenario_bible import normalize_location_key_for_anchors
        _raw_loc = getattr(scenario, "theme_key", None) or getattr(scenario, "location_en", "") or scenario.name
        location_key = normalize_location_key_for_anchors(str(_raw_loc or ""))
        location_display_name = getattr(scenario, "location_en", None) or scenario.name
        logger.info(
            "V3_LOCATION_RESOLVED",
            trace_id=tracer.trace_id,
            scenario_id=str(getattr(scenario, "id", "")),
            scenario_name=getattr(scenario, "name", ""),
            location_key=location_key,
            location_display_name=location_display_name,
        )
        child_description = visual_character_description or ""

        # =================================================================
        # FACE ANALYSIS: convert photo URL → text description
        # =================================================================
        # trials.py passes child_photo_url as visual_character_description.
        # The URL is needed for PuLID (image reference), but CharacterBible
        # and blueprint need a *text* description to parse hair/skin/eye
        # tokens.  Run face analyzer once and reuse the result.
        _child_photo_url: str = ""
        if child_description and child_description.strip().startswith(("http://", "https://")):
            _child_photo_url = child_description.strip()
            try:
                from app.services.ai.face_analyzer_service import get_face_analyzer
                _face_analyzer = get_face_analyzer()
                child_description = await _face_analyzer.analyze_for_ai_director(
                    image_source=_child_photo_url,
                    child_name=child_name,
                    child_age=child_age,
                    child_gender=(child_gender or "erkek"),
                )
                logger.info(
                    "FACE_ANALYSIS_COMPLETE",
                    trace_id=tracer.trace_id,
                    description_preview=child_description[:120],
                )
            except Exception as _fa_err:
                logger.warning(
                    "Face analysis failed — pipeline continues without appearance tokens",
                    trace_id=tracer.trace_id,
                    error=str(_fa_err),
                )
                child_description = ""

        # =====================================================================
        # VALUE FALLBACK: default value when user selected no learning outcome
        # =====================================================================
        if not outcomes:
            _fallback_value = _resolve_default_value_for_scenario(scenario)
            logger.info(
                "VALUE_FALLBACK_APPLIED",
                scenario_name=getattr(scenario, "name", ""),
                fallback_value=_fallback_value,
            )

            class _FallbackOutcome:
                def __init__(self, name: str):
                    self.name = name
                    self.ai_prompt = name
                    self.ai_prompt_instruction = None
                    self.banned_words_tr = None

                @property
                def effective_ai_instruction(self) -> str:
                    return self.ai_prompt_instruction or self.ai_prompt or self.name

            outcomes = [_FallbackOutcome(_fallback_value)]

        # =====================================================================
        # PASS-0: BLUEPRINT
        # =====================================================================
        # Extract primary value name for blueprint hints
        _primary_value_name = ""
        if outcomes:
            _primary_value_name = (getattr(outcomes[0], "name", None) or str(outcomes[0])).strip()

        _p0_start = time.monotonic()
        try:
            blueprint = await self._pass0_generate_blueprint(
                child_name=child_name,
                child_age=child_age,
                child_description=child_description,
                location_key=location_key,
                location_display_name=location_display_name,
                visual_style=visual_style,
                magic_items=magic_items or [],
                page_count=page_count,
                scenario=scenario,
                value_name=_primary_value_name,
            )
            tracer.story_pass0_ok(
                page_count=len(blueprint.get("pages", [])),
                latency_ms=(time.monotonic() - _p0_start) * 1000,
            )
        except Exception as _p0_err:
            tracer.story_pass0_fail(error=str(_p0_err))
            tracer.pipeline_fail(
                error_code="PASS0_GEMINI_ERROR",
                error=str(_p0_err),
            )
            raise

        # Minimal buffer — token bucket handles rate limiting
        await _asyncio_v3.sleep(1)

        # =====================================================================
        # PASS-1: STORY PAGES
        # =====================================================================
        _p1_start = time.monotonic()
        try:
            pages = await self._pass1_generate_pages(
                blueprint=blueprint,
                child_name=child_name,
                child_age=child_age,
                child_description=child_description,
                visual_style=visual_style,
                location_display_name=location_display_name,
                magic_items=magic_items or [],
                page_count=page_count,
                outcomes=outcomes,
                location_constraints=getattr(scenario, "location_constraints", "") or "",
                skip_visual_prompts=not generate_visual_prompts,
            )
            tracer.story_pass1_ok(
                page_count=len(pages),
                latency_ms=(time.monotonic() - _p1_start) * 1000,
            )
        except Exception as _p1_err:
            tracer.story_pass1_fail(error=str(_p1_err))
            tracer.pipeline_fail(
                error_code="PASS1_GEMINI_ERROR",
                error=str(_p1_err),
            )
            raise

        # =====================================================================
        # VALIDATION → FIX → RE-VALIDATE (text + basic structure)
        # =====================================================================
        from app.prompt_engine.story_validators import (
            apply_all_fixes,
            validate_story_output,
        )

        report = validate_story_output(
            pages=pages,
            blueprint=blueprint,
            magic_items=magic_items or [],
            expected_page_count=page_count,
        )

        if not report.all_passed:
            pages, fix_summary = apply_all_fixes(pages)

            if fix_summary:
                logger.info(
                    "V3 auto-fixer applied corrections",
                    fixes=fix_summary,
                )
                report = validate_story_output(
                    pages=pages,
                    blueprint=blueprint,
                    magic_items=magic_items or [],
                    expected_page_count=page_count,
                )

            if not report.all_passed:
                logger.warning(
                    "V3 story validation still has failures after auto-fix",
                    failures=[f.code for f in report.failures],
                )

        # =====================================================================
        # VISUAL PROMPT ENHANCEMENT (CharacterBible + SceneDirector + Safety)
        # =====================================================================
        from app.prompt_engine.character_bible import build_character_bible
        from app.prompt_engine.style_adapter import adapt_style
        from app.prompt_engine.visual_prompt_builder import enhance_all_pages
        from app.prompt_engine.visual_prompt_validator import autofix as autofix_visual_prompts
        from app.prompt_engine.visual_prompt_validator import (
            validate_all as validate_visual_prompts,
        )

        child_gender_str = child_gender or "erkek"

        # Extract companion (side_character) from blueprint for consistency
        _side_char = blueprint.get("side_character") or {}
        _companion_name = _side_char.get("name", "")
        _companion_type = _side_char.get("type", "")  # e.g. "sincap" / "squirrel"
        _companion_appearance = _side_char.get("appearance", "")

        # Extract child outfit + hair from blueprint (V3 outfit lock)
        _child_outfit_block = blueprint.get("child_outfit") or {}
        _blueprint_outfit = _child_outfit_block.get("description_en", "").strip()
        _blueprint_hair = _child_outfit_block.get("hair_style_en", "").strip()
        # Öncelik: senaryo kıyafeti (fixed_outfit) > blueprint kıyafeti > cinsiyet default'u
        # NOT: fixed_outfit boş string ("") olabilir — .strip() ile kontrol et
        _fixed_outfit_clean = (fixed_outfit or "").strip()
        _effective_outfit = _fixed_outfit_clean or _blueprint_outfit
        if not _effective_outfit:
            # Senaryo veya blueprint kıyafeti yoksa cinsiyet bazlı fallback
            if child_gender_str in ("girl", "kiz", "female"):
                _effective_outfit = "a colorful adventure dress and comfortable sneakers"
            else:
                _effective_outfit = "an adventure jacket with comfortable pants and sneakers"
        logger.info(
            "OUTFIT_LOCKED",
            source="scenario" if _fixed_outfit_clean else ("blueprint" if _blueprint_outfit else "default"),
            outfit=_effective_outfit[:80],
            fixed_outfit_raw=bool(_fixed_outfit_clean),
        )

        character_bible = build_character_bible(
            child_name=child_name,
            child_age=child_age,
            child_gender=child_gender_str,
            child_description=child_description,
            fixed_outfit=_effective_outfit,
            hair_style=_blueprint_hair,
            companion_name=_companion_name,
            companion_species=_companion_type,
            companion_appearance=_companion_appearance,
        )

        logger.info(
            "CHARACTER_BIBLE_BUILT",
            trace_id=tracer.trace_id,
            appearance_tokens=character_bible.appearance_tokens,
            identity_anchor=character_bible.identity_anchor,
            hair_style=character_bible.hair_style,
            negative_preview=character_bible.negative_tokens[:100],
        )

        if _companion_name:
            _final_appearance = ""
            if character_bible.companion:
                _final_appearance = character_bible.companion.appearance
            logger.info(
                "Companion locked in CharacterBible",
                companion_name=_companion_name,
                companion_species=_companion_type,
                companion_appearance=_final_appearance,
            )

        value_visual_motif = get_value_visual_motif_for_outcomes(outcomes)

        from app.prompt_engine.constants import LIKENESS_HINT_WHEN_REFERENCE
        _has_child_photo = bool(_child_photo_url)
        _likeness = LIKENESS_HINT_WHEN_REFERENCE if _has_child_photo else ""

        _enhancement_skipped = False
        enhanced_report = None
        _pages_before_enhance = [dict(p) for p in pages]

        _enhance_start = time.monotonic()
        try:
            enhancement_result = enhance_all_pages(
                pages=pages,
                blueprint=blueprint,
                character_bible=character_bible,
                visual_style=visual_style,
                location_key=location_key,
                value_visual_motif=value_visual_motif,
                likeness_hint=_likeness,
                has_pulid=_has_child_photo,
                leading_prefix_override=leading_prefix_override,
                style_block_override=style_block_override,
            )
            pages = enhancement_result["pages"]
            tracer.prompt_enhance_ok(
                page_count=len(pages),
                latency_ms=(time.monotonic() - _enhance_start) * 1000,
            )

            # Visual prompt validation + auto-fix (V3: shot conflict + value motif checks)
            style_mapping = adapt_style(visual_style)
            visual_validation = validate_visual_prompts(
                pages, character_bible, style_mapping, value_visual_motif=value_visual_motif
            )
            if not visual_validation.passed:
                auto_fixes = autofix_visual_prompts(pages, character_bible, style_mapping, visual_validation)
                visual_validation.auto_fixed = auto_fixes
                logger.info("Visual prompt auto-fix applied", fixes=len(auto_fixes))

            # Post-enhancement story-level validation
            enhanced_report = validate_story_output(
                pages=pages,
                blueprint=blueprint,
                magic_items=magic_items or [],
                expected_page_count=page_count,
                character_prompt_block=character_bible.prompt_block,
            )

            if not enhanced_report.all_passed:
                logger.warning(
                    "V3 post-enhancement validation has warnings",
                    failures=[f.code for f in enhanced_report.failures],
                )
        except Exception as _enhance_err:
            _enhancement_skipped = True
            pages = _pages_before_enhance
            tracer.prompt_enhance_fail(error=str(_enhance_err))
            logger.error(
                "V3 enhance_all_pages FAILED — using raw pages (graceful degradation)",
                trace_id=tracer.trace_id,
                error=str(_enhance_err),
                error_type=type(_enhance_err).__name__,
                page_count=len(pages),
            )
            # Minimal fallback: inject identity anchor + outfit lock + hair lock
            # into raw pages so PuLID mode still has basic character grounding.
            _fb_id = character_bible.identity_anchor_minimal if _has_child_photo else character_bible.identity_anchor
            _fb_outfit = f"OUTFIT LOCK: {character_bible.outfit_en}" if character_bible.outfit_en else ""
            _fb_hair = f"HAIR: {character_bible.hair_style}" if character_bible.hair_style else ""
            _fb_neg = (
                "low quality, blurry, extra limbs, deformed hands, "
                "scary, horror, text, watermark, logo, "
                "different outfit, different hairstyle, outfit change"
            )
            for _p in pages:
                _raw_prompt = (_p.get("image_prompt_en") or "").strip()
                if _raw_prompt and _fb_id and _fb_id not in _raw_prompt:
                    _fb_tokens = ", ".join(t for t in [_fb_id, _fb_hair, _fb_outfit] if t)
                    _p["image_prompt_en"] = f"{_fb_tokens}, {_raw_prompt}"
                if not _p.get("negative_prompt"):
                    _p["negative_prompt"] = _fb_neg
            logger.info(
                "Enhancement fallback: injected minimal identity + outfit lock",
                page_count=len(pages),
            )

        # =====================================================================
        # CONVERT TO StoryResponse + FinalPageContent
        # =====================================================================
        title = blueprint.get("title", "")
        if not title:
            _suffix = _get_possessive_suffix(child_name)
            title = f"{child_name}'{_suffix} Büyülü Macerası"

        title = _normalize_title_turkish(title)

        # Determine outfit (CharacterBible is the source of truth now)
        # CharacterBible'da _effective_outfit var; fixed_outfit boş string olabilir
        if not (fixed_outfit or "").strip():
            fixed_outfit = character_bible.outfit_en

        from app.prompt.book_context import BookContext as _BCtx
        from app.prompt.negative_builder import build_negative
        from app.prompt_engine import resolve_style as _resolve_style
        from app.prompt_engine.visual_prompt_builder import build_cover_prompt

        # Pre-build the full inner-page negative once for all pages in this book.
        # LLM (Pass-1) only outputs "bad quality, blurry, text, watermark".
        # We merge that with the proper style + character-consistency negative.
        _style_config = _resolve_style(visual_style or "")
        _neg_ctx = _BCtx.build(
            child_name=child_name,
            child_age=child_age,
            child_gender=child_gender or "",
            style_modifier=visual_style or "",
            face_reference_url="ref" if _has_child_photo else "",
        )
        _base_inner_negative = build_negative(_neg_ctx)

        story_pages: list[PageContent] = []
        final_pages: list[FinalPageContent] = []

        # =====================================================================
        # STEP 1: Synthesize COVER page
        #   page_index=0, page_number=0, story_page_number=None
        #   Cover is image-only — text = title (no story paragraph)
        # =====================================================================
        # build_cover_prompt returns (gemini_scene, flux_prompt, negative_prompt).
        # We use flux_prompt as visual_prompt to preserve clothing consistency.
        cover_scene, _cover_flux_prompt, cover_negative = build_cover_prompt(
            character_bible=character_bible,
            visual_style=visual_style,
            location_key=location_key,
            location_constraints=getattr(scenario, "location_constraints", "") or "",
            story_title=title,
            blueprint=blueprint,
            value_visual_motif=value_visual_motif,
            likeness_hint=_likeness,
            has_pulid=_has_child_photo,
        )

        logger.info(
            "V3_COVER_GENERATED",
            page_index=0,
            page_type="cover",
            composer_version="v3",
            COVER_GENERATED=True,
            COVER_SCENE_LENGTH=len(cover_scene),
        )

        story_pages.append(PageContent(
            page_number=0,
            text=title,
            scene_description=cover_scene[:200],
        ))
        final_pages.append(FinalPageContent(
            page_number=0,
            text=title,
            scene_description=cover_scene[:200],
            visual_prompt=_cover_flux_prompt or cover_scene,
            negative_prompt=cover_negative,
            v3_composed=True,
            v3_enhancement_skipped=_enhancement_skipped,
            page_type="cover",
            page_index=0,
            story_page_number=None,
            composer_version="v3",
            pipeline_version="v3",
        ))

        # =====================================================================
        # STEP 2: Process inner pages
        #   LLM pages are 1-indexed (page 1..page_count).
        #   page_index = 1..N (position in book after cover)
        #   story_page_number = same as LLM page number (1..N)
        #
        #   Dedication (page 1, role="dedication"):
        #     - page_type="front_matter", NO image generation
        #     - Carries only text, no visual_prompt needed
        # =====================================================================
        _FRONT_MATTER_ROLES = {"dedication"}
        bp_pages_list = blueprint.get("pages", [])
        bp_role_by_page: dict[int, str] = {}
        for bp in bp_pages_list:
            bp_role_by_page[bp.get("page", 0)] = bp.get("role", "")

        inner_count = 0
        for page_data in pages:
            llm_page_num = page_data.get("page", 0)
            # Kapak (page 0) zaten STEP 1'de eklendi; blueprint sayfa 0'ı atla, 1. sayfa metni ilk iç sayfada kalsın
            if llm_page_num == 0:
                continue
            text_tr = page_data.get("text_tr", "")
            image_prompt_en = page_data.get("image_prompt_en", "")
            _llm_neg = (page_data.get("negative_prompt_en") or "").strip()
            # Merge LLM negative with the proper full negative (LLM output is minimal)
            if _llm_neg and _llm_neg not in _base_inner_negative:
                negative_prompt_en = f"{_base_inner_negative}, {_llm_neg}"
            else:
                negative_prompt_en = _base_inner_negative

            scene_desc = image_prompt_en[:200] if image_prompt_en else ""

            # Determine page_type from blueprint role
            bp_role = bp_role_by_page.get(llm_page_num, "")
            if bp_role in _FRONT_MATTER_ROLES:
                page_type = "front_matter"
            else:
                page_type = "inner"
                inner_count += 1

            # page_index = position in book (cover=0, so inner starts at 1)
            current_page_index = len(final_pages)  # cover is already at index 0

            story_pages.append(PageContent(
                page_number=llm_page_num,
                text=text_tr,
                scene_description=scene_desc,
            ))

            # Use the fully composed FLUX-style prompt (image_prompt_en) because it contains 
            # the clothing description integrated into the sentence (e.g., "A young boy... wearing...").
            # Using the bare gemini_scene causes clothing consistency loss because the image generator
            # when skip_compose=True relies on the prompt being fully composed.
            gemini_scene = page_data.get("gemini_scene", "")
            final_prompt = image_prompt_en or gemini_scene

            logger.info(
                "V3_PAGE_PIPELINE_STATS",
                page_index=current_page_index,
                story_page_number=llm_page_num,
                page_type=page_type,
                composer_version="v3",
                v3_composed=True,
                skip_compose=True,
                scene_length=len(final_prompt),
                used_gemini_scene=bool(gemini_scene),
                negative_length=len(negative_prompt_en),
            )

            final_pages.append(FinalPageContent(
                page_number=llm_page_num,
                text=text_tr,
                scene_description=scene_desc,
                visual_prompt=final_prompt,
                negative_prompt=negative_prompt_en,
                v3_composed=True,
                v3_enhancement_skipped=_enhancement_skipped,
                page_type=page_type,
                page_index=current_page_index,
                story_page_number=llm_page_num,
                composer_version="v3",
                pipeline_version="v3",
            ))

        # =====================================================================
        # STEP 3: Synthesize BACK COVER page
        #   page_type="backcover", page_index=last+1
        #   Back cover gets an AI-generated image (like front cover) with closing scene.
        #   Bottom 35% is clear for text/QR overlay in render_back_cover().
        # =====================================================================
        try:
            from app.prompt_engine.visual_prompt_builder import build_back_cover_prompt
            _bc_scene, _bc_flux_prompt, _bc_negative = build_back_cover_prompt(
                character_bible=character_bible,
                visual_style=visual_style,
                location_key=location_key,
                story_title=title,
                blueprint=blueprint,
                value_visual_motif=value_visual_motif,
                likeness_hint=_likeness,
                has_pulid=_has_child_photo,
            )
            _bc_page_index = len(final_pages)
            final_pages.append(FinalPageContent(
                page_number=999,  # sentinel — not a story page
                text="",
                scene_description=_bc_scene[:200],
                visual_prompt=_bc_flux_prompt or _bc_scene,
                negative_prompt=_bc_negative,
                v3_composed=True,
                v3_enhancement_skipped=_enhancement_skipped,
                page_type="backcover",
                page_index=_bc_page_index,
                story_page_number=None,
                composer_version="v3",
                pipeline_version="v3",
            ))
            logger.info("V3_BACK_COVER_GENERATED", page_index=_bc_page_index)
        except Exception as _bc_err:
            logger.warning("V3_BACK_COVER_PROMPT_FAILED", error=str(_bc_err))

        # =====================================================================
        # GUARDS
        # =====================================================================
        # 1) Cover must be present at position 0
        if not final_pages or final_pages[0].page_type != "cover":
            raise AIServiceError("V3 pipeline FAILED: cover page (page_index=0) is missing — aborting")

        # 2) All pages must have pipeline_version=v3 AND composer_version=v3
        non_v3 = [p for p in final_pages if p.pipeline_version != "v3" or p.composer_version != "v3"]
        if non_v3:
            raise AIServiceError(
                f"V3 pipeline FAILED: {len(non_v3)} pages have pipeline/composer version != 'v3' — aborting"
            )

        # 3) Inner page count: page_count = kapak + iç sayfalar; kapak döngüde atlandığı için iç = page_count - 1 - front_matter
        front_matter_count = sum(1 for p in final_pages if p.page_type == "front_matter")
        expected_inner = page_count - 1 - front_matter_count
        if inner_count != expected_inner:
            logger.warning(
                "V3 inner page count mismatch",
                expected=expected_inner,
                actual=inner_count,
                front_matter=front_matter_count,
            )

        story_response = StoryResponse(title=title, pages=story_pages)

        # Location contamination check: fail if any prompt contains wrong-city keywords (e.g. Istanbul in Kapadokya story)
        # Exclude backcover page — its closing scene may not reference the location keyword.
        from app.prompt_engine.qa_checks import run_qa_checks
        _qa_pages = [p.model_dump() for p in final_pages if p.page_type != "backcover"]
        _qa_report = run_qa_checks(
            final_pages=_qa_pages,
            expected_location_key=location_key,
        )
        _loc_failures = (_qa_report.get("checks") or {}).get("location_contamination", {}).get("failures") or []
        if _loc_failures:
            raise AIServiceError(
                "V3 pipeline",
                f"Location contamination: prompts must not contain wrong-city keywords. Failures: {_loc_failures[:3]}",
            )

        tracer.pipeline_complete(
            page_count=len(final_pages),
            enhancement_skipped=_enhancement_skipped,
        )

        logger.info(
            "V3 BLUEPRINT story generation complete",
            trace_id=tracer.trace_id,
            title=title,
            total_pages=len(final_pages),
            cover_present=True,
            front_matter_count=front_matter_count,
            inner_count=inner_count,
            child_name=child_name,
            validation_passed=report.all_passed,
            visual_enhancement_passed=enhanced_report.all_passed if enhanced_report else False,
        )

        return story_response, final_pages, fixed_outfit, blueprint

    @rate_limit_retry(service="gemini", max_attempts=2, timeout_attempts=1)
    async def generate_story_structured(
        self,
        scenario: Scenario,
        child_name: str,
        child_age: int,
        child_gender: str | None,
        outcomes: list[LearningOutcome],
        visual_style: str = "children's book illustration, soft colors",
        visual_character_description: str = "",  # DOUBLE LOCKING!
        page_count: int = 16,  # Number of story pages (from product settings)
        fixed_outfit: str = "",  # Consistent clothing for all pages
        magic_items: list[str] | None = None,  # V3: magic items
        requested_version: str | None = None,  # "v3" to force V3, None = auto (feature flag)
        leading_prefix_override: str | None = None,
        style_block_override: str | None = None,
        generate_visual_prompts: bool = True,  # False = story text only (for two-phase generation)
    ) -> tuple[StoryResponse, list[FinalPageContent], str, dict | None]:
        """Generate a personalized story.

        Supports TWO modes:
        - V3 Blueprint Pipeline (USE_BLUEPRINT_PIPELINE=true or requested_version="v3")
        - V2 Legacy (default): 2-pass Pure Author + Technical Director

        Returns:
            4-tuple: (StoryResponse, list[FinalPageContent], fixed_outfit, blueprint_json | None)
            blueprint_json is the PASS-0 blueprint dict when V3 is used, None for V2.

        Raises:
            AIServiceError: If generation fails, or if requested_version="v3" but V3 didn't run.
            Non-V3 requests are blocked by policy.
        """
        pipeline_cfg = getattr(settings, "book_pipeline_version", "3")
        # V3 is the only supported pipeline.
        use_v3 = True
        if requested_version == "v2":
            raise AIServiceError(
                "V2_LABEL_BLOCKED: expected v3"
            )
        if pipeline_cfg != "3":
            raise AIServiceError(
                "BOOK_PIPELINE_VERSION must be '3'. Current value is invalid."
            )

        if use_v3:
            from app.core.pipeline_version import prompt_builder_name_for_version

            _builder_name = prompt_builder_name_for_version("v3")
            logger.info(
                "Dispatching to V3 Blueprint Pipeline",
                requested_version=requested_version,
                book_pipeline_version=pipeline_cfg,
                prompt_builder_name=_builder_name,
            )
            logger.info(
                "PROMPT_BUILDER_SELECTED",
                pipeline_version="v3",
                builder_name=_builder_name,
                requested_version=requested_version,
            )
            story_response, final_pages, outfit, blueprint = await self.generate_story_v3(
                scenario=scenario,
                child_name=child_name,
                child_age=child_age,
                child_gender=child_gender,
                outcomes=outcomes,
                visual_style=visual_style,
                visual_character_description=visual_character_description,
                page_count=page_count,
                fixed_outfit=fixed_outfit,
                magic_items=magic_items,
                leading_prefix_override=leading_prefix_override,
                style_block_override=style_block_override,
                generate_visual_prompts=generate_visual_prompts,
            )

            # Hard fail: if caller explicitly requested v3, verify every page
            if requested_version == "v3":
                bad = [p for p in final_pages if p.pipeline_version != "v3"]
                if bad:
                    raise AIServiceError(
                        f"requested_version='v3' but {len(bad)} pages have "
                        f"pipeline_version != 'v3' — aborting"
                    )

            return story_response, final_pages, outfit, blueprint

        # Legacy branch intentionally disabled (V3 single source of truth)
        gender_term = child_gender or "erkek"

        logger.info(
            "Starting TWO-PASS story generation (V2 legacy)",
            scenario=scenario.name,
            child_name=child_name,
            pass1_model=self.story_model,
            pass2_model=self.technical_model,
        )

        # =====================================================================
        # PASS 1: PURE AUTHOR - Write beautiful story
        # ⚠️ SCENARIO TEMPLATES NOW INTEGRATED!
        # =====================================================================

        # Extract scenario template fields — V2 prefers story_prompt_tr, falls back to ai_prompt_template
        ai_prompt_template = (
            getattr(scenario, "story_prompt_tr", None)
            or getattr(scenario, "ai_prompt_template", None)
            or ""
        )
        location_constraints = getattr(scenario, "location_constraints", None) or ""
        cultural_elements = getattr(scenario, "cultural_elements", None)

        # V2: Merge location_en into location_constraints (don't discard either)
        v2_location_en = getattr(scenario, "location_en", None) or ""
        if v2_location_en:
            location_prefix = f"Tüm sahneler {v2_location_en} bölgesinde geçmeli."
            if location_constraints:
                # Merge: prepend location_en if not already present
                if v2_location_en.lower() not in location_constraints.lower():
                    location_constraints = f"{location_prefix} {location_constraints}"
            else:
                location_constraints = location_prefix

        logger.info(
            "[TEMPLATE] SCENARIO TEMPLATES CHECK (V2)",
            scenario_name=scenario.name,
            has_story_prompt_tr=bool(getattr(scenario, "story_prompt_tr", None)),
            has_ai_prompt_template=bool(getattr(scenario, "ai_prompt_template", None)),
            has_location_en=bool(v2_location_en),
            has_location_constraints=bool(location_constraints),
            has_cultural_elements=bool(cultural_elements),
            ai_prompt_preview=ai_prompt_template[:80] if ai_prompt_template else "NONE",
        )

        # V2: Extract no_family flag (compose_story_prompt already adds no_family constraint)
        v2_flags = getattr(scenario, "flags", None) or {}
        v2_no_family = v2_flags.get("no_family", False)

        # V2: no_family banned words list — use word-boundary regex to avoid
        # false positives (e.g. "abi" matching inside "sabırsız", "kabiliye")
        import re as _re

        from app.prompt_engine.constants import NO_FAMILY_BANNED_WORDS_TR

        _no_family_words = [
            w.strip().lower() for w in NO_FAMILY_BANNED_WORDS_TR.split(",") if w.strip()
        ]
        # Pre-compile word-boundary patterns for each banned word
        _no_family_patterns = {
            w: _re.compile(r"(?<![a-zA-ZçğıöşüÇĞİÖŞÜ])" + _re.escape(w) + r"(?![a-zA-ZçğıöşüÇĞİÖŞÜ])", _re.IGNORECASE)
            for w in _no_family_words
        }

        learning_keywords = self._get_learning_outcome_keywords(outcomes)
        max_pass1_attempts = 2  # Reduced from 4: free tier 15 RPM → her retry 3 Gemini çağrısı
        story_text = ""
        extra_no_family = ""
        for pass1_attempt in range(max_pass1_attempts):
            # Rate limit koruması: ardışık PASS 1 çağrıları arası bekleme
            if pass1_attempt > 0:
                import asyncio as _asyncio_retry
                _retry_delay = 15  # 15s — free tier 15 RPM; önceki çağrı RPM'i tüketmiş olabilir
                logger.info(
                    "[STORY-GEN] Waiting before Pass1 retry to avoid rate limit",
                    delay_seconds=_retry_delay,
                    attempt=pass1_attempt + 1,
                )
                await _asyncio_retry.sleep(_retry_delay)

            story_text = await self._pass1_write_story(
                scenario=scenario,
                outcomes=outcomes,
                child_name=child_name,
                child_age=child_age,
                child_gender=gender_term,
                page_count=page_count,
                cultural_elements=cultural_elements,
                extra_instructions=extra_no_family,
            )

            # --- check learning outcomes ---
            learning_ok = not learning_keywords or self._story_reflects_learning_outcomes(
                story_text, learning_keywords, min_occurrences=2
            )
            if not learning_ok:
                logger.warning(
                    "[STORY-GEN] Learning outcome not reflected, regenerating Pass1",
                    attempt=pass1_attempt + 1,
                    keywords=learning_keywords,
                )

            # --- Aile kelimeleri kontrolü: Sadece senaryo no_family=true ise uygula
            family_ok = True
            if v2_no_family:
                violations = [w for w, pat in _no_family_patterns.items() if pat.search(story_text)]
                if violations:
                    family_ok = False
                    logger.warning(
                        "[STORY-GEN] aile kelimesi ihlali — yasaklı kelimeler bulundu (no_family aktif)",
                        attempt=pass1_attempt + 1,
                        violations=violations,
                        story_preview=story_text[:200],
                    )
                    if not extra_no_family:
                        extra_no_family = (
                            "\n\n🚫🚫 KESİNLİKLE AİLE KELİMELERİ YASAKLI: "
                            f"{', '.join(_no_family_words)}. "
                            "Bu kelimeleri HİÇBİR ŞEKİLDE kullanma!"
                        )

            if learning_ok and family_ok:
                break

        # Post-loop validation
        if learning_keywords and not self._story_reflects_learning_outcomes(
            story_text, learning_keywords, min_occurrences=2
        ):
            logger.warning(
                "[STORY-GEN] Learning outcome still under-represented after retries",
                keywords=learning_keywords,
            )
        # Aile kuralı sadece no_family senaryolarda uygulanır
        if v2_no_family:
            final_violations = [w for w, pat in _no_family_patterns.items() if pat.search(story_text)]
            if final_violations:
                logger.error(
                    "[STORY-GEN] aile kelimesi HARD FAIL — no_family senaryo",
                    violations=final_violations,
                    story_preview=story_text[:300],
                )
                raise ContentPolicyError(
                    f"Hikaye aile kelimeleri içeriyor ({', '.join(final_violations)}). "
                    f"{max_pass1_attempts} deneme sonrasında temiz bir hikaye oluşturulamadı. "
                    "Lütfen farklı bir senaryo veya stil deneyin.",
                )

        # =====================================================================
        # PASS 2: TECHNICAL DIRECTOR - Format and generate SCENE DESCRIPTIONS
        # ⚠️ NOTE: Style is NOT passed here! It's added in _compose_visual_prompts
        # =====================================================================

        # Rate limit koruması: PASS 1 hemen ardından PASS 2 çağrılırsa free tier'da
        # 429 tetiklenir. 15 RPM = 4s/request ama retry'lar RPM'i tüketmiş olabilir.
        import asyncio as _asyncio
        await _asyncio.sleep(10)  # Free tier: 15 RPM; PASS 1 retry'ları sonrası güvenli aralık

        # Get location constraints from scenario (if available)
        location_constraints = ""
        if hasattr(scenario, "location_constraints") and scenario.location_constraints:
            location_constraints = scenario.location_constraints

        logger.info(
            "PASS 2: Generating scene descriptions (NO STYLE)",
            scenario_name=scenario.name,
            has_location_constraints=bool(location_constraints),
        )

        # Determine outfit BEFORE Pass 2 so Gemini + compose use same clothing
        if not fixed_outfit:
            if child_gender == "kiz":
                fixed_outfit = "a colorful adventure dress and comfortable sneakers"
            else:
                fixed_outfit = "an adventure jacket with comfortable pants and sneakers"

        story_response = await self._pass2_format_story(
            story_text=story_text,
            child_name=child_name,
            child_age=child_age,
            child_gender=gender_term,
            visual_character_description=visual_character_description,
            scenario_name=scenario.name,
            location_constraints=location_constraints,
            fixed_outfit=fixed_outfit,
            expected_page_count=page_count,
        )

        logger.info(
            "👕 OUTFIT CONSISTENCY",
            fixed_outfit=fixed_outfit,
            source="provided" if fixed_outfit else "default",
        )

        # Load prompt templates from DB for visual prompt composition
        from app.prompt_engine.constants import (
            DEFAULT_COVER_TEMPLATE_EN as _COVER_CONST,
        )
        from app.prompt_engine.constants import (
            DEFAULT_INNER_TEMPLATE_EN as _INNER_CONST,
        )

        _db_cover_tpl = ""
        _db_inner_tpl = ""
        if self._db is not None:
            try:
                if self._prompt_service is None:
                    from app.services.prompt_template_service import get_prompt_service
                    self._prompt_service = get_prompt_service()
                _db_cover_tpl = await self._prompt_service.get_template_en(
                    self._db, "COVER_TEMPLATE", _COVER_CONST
                )
                _db_inner_tpl = await self._prompt_service.get_template_en(
                    self._db, "INNER_TEMPLATE", _INNER_CONST
                )
            except Exception as _tpl_err:
                logger.warning("Failed to load DB templates for compose", error=str(_tpl_err))

        # Compose final pages (with optional learning-outcome visual hint, e.g. toothbrush)
        learning_visual_hints = self._get_learning_outcome_visual_hints(outcomes)
        final_pages = self._compose_visual_prompts(
            story_response=story_response,
            scenario=scenario,
            child_name=child_name,
            child_description=visual_character_description
            or self._build_child_description(child_name, child_age, child_gender),
            visual_style=visual_style,
            fixed_outfit=fixed_outfit,
            learning_outcome_visual_hints=learning_visual_hints or None,
            cover_template_en=_db_cover_tpl,
            inner_template_en=_db_inner_tpl,
        )

        # ==================== TITLE FALLBACK ====================
        # Gemini bazen generic title üretiyor ("Hikaye", "Masal" vb.)
        # Bu durumda çocuğun adı + senaryo adıyla kişiselleştirilmiş title oluştur
        _GENERIC_TITLES = {
            "hikaye", "masal", "hikâye", "öykü", "macera", "story",
            "bir hikaye", "bir masal", "yeni hikaye", "güzel hikaye",
        }
        _raw_title = (story_response.title or "").strip()
        if _raw_title.lower() in _GENERIC_TITLES or len(_raw_title) < 4:
            scenario_name = getattr(scenario, "name", "") or ""
            # "Kapadokya Macerası" -> "Kapadokya Macerası"
            # "Enes" + "Kapadokya Macerası" -> "Enes'in Kapadokya Macerası"
            if scenario_name:
                _suffix = _get_possessive_suffix(child_name)
                new_title = f"{child_name}'{_suffix} {scenario_name}"
            else:
                _suffix = _get_possessive_suffix(child_name)
                new_title = f"{child_name}'{_suffix} Büyülü Macerası"
            story_response.title = new_title
            logger.warning(
                "Generic title replaced with personalized title",
                original_title=_raw_title,
                new_title=new_title,
            )

        # ==================== TITLE TURKISH NORMALIZATION ====================
        # AI bazen İngilizce yer adları kullanıyor — Türkçe'ye çevir
        story_response.title = _normalize_title_turkish(story_response.title)

        logger.info(
            "TWO-PASS story generation complete",
            title=story_response.title,
            page_count=len(final_pages),
            child_name=child_name,
            fixed_outfit=fixed_outfit,
        )

        if requested_version == "v3":
            raise AIServiceError(
                "requested_version='v3' but pipeline ran V2 (feature flag is off) — aborting"
            )
        if pipeline_cfg == "3":
            raise AIServiceError(
                "BOOK_PIPELINE_VERSION=3 but V2 pipeline ran — aborting (single source: V3)"
            )

        return story_response, final_pages, fixed_outfit, None

    # =========================================================================
    # LEGACY: Single-pass generation (kept for backward compatibility)
    # =========================================================================

    async def _legacy_generate_story_structured(
        self,
        scenario: Scenario,
        child_name: str,
        child_age: int,
        child_gender: str | None,
        outcomes: list[LearningOutcome],
        visual_style: str = "children's book illustration, soft colors",
        visual_character_description: str = "",
    ) -> tuple[StoryResponse, list[FinalPageContent]]:
        """Legacy single-pass generation - kept for reference."""
        # Build outcome descriptions with AI prompts
        outcome_instructions = []
        for o in outcomes:
            if hasattr(o, "ai_prompt") and o.ai_prompt:
                outcome_instructions.append(o.ai_prompt)
            else:
                outcome_instructions.append(f"Hikayede {o.name} teması işlensin.")

        outcome_text = "\n".join([f"- {inst}" for inst in outcome_instructions])

        clothing_default = (
            "adventure clothes with a colorful jacket"
            if child_gender == "erkek"
            else "a pretty adventure outfit"
        )

        if visual_character_description:
            character_instruction = f'''⭐ DOUBLE LOCKING - KARAKTER AÇIKLAMASI:
"{visual_character_description}"
Bu açıklamayı HER visual_prompt'ta TAM OLARAK KULLAN!'''
        else:
            character_instruction = f"""KARAKTER: A {child_age}-year-old child named {child_name}"""

        system_prompt = f"""Sen bir UZMAN SANAT YÖNETMENİSİN.

{AI_DIRECTOR_SYSTEM}

{character_instruction}

📋 ÇIKTI: JSON formatında 17 sayfalık hikaye ve görsel promptlar.
GÖRSEL STİL: {visual_style}
EĞİTSEL HEDEFLER:
{outcome_text}"""

        user_prompt = f"""SENARYO: {scenario.name}
KARAKTER: {child_name}, {child_age} yaş
Şimdi 17 sayfalık hikaye üret."""

        try:
            api_url = get_gemini_api_url()

            logger.info(
                "Legacy: Generating story with single pass",
                model=self.model,
                scenario=scenario.name,
            )

            client = self._get_gemini_client()
            response = await client.post(
                f"{api_url}?key={self.api_key}",
                json={
                    "contents": [{"parts": [{"text": system_prompt + "\n\n" + user_prompt}]}],
                    "generationConfig": {
                        "temperature": self.story_temperature,
                        "topK": 64,
                        "topP": 0.95,
                        "maxOutputTokens": 16384,
                        "responseMimeType": "application/json",
                    },
                    "safetySettings": [
                        {
                            "category": "HARM_CATEGORY_HARASSMENT",
                            "threshold": "BLOCK_MEDIUM_AND_ABOVE",
                        },
                        {
                            "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                            "threshold": "BLOCK_MEDIUM_AND_ABOVE",
                        },
                        {
                            "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                            "threshold": "BLOCK_MEDIUM_AND_ABOVE",
                        },
                        {
                            "category": "HARM_CATEGORY_HATE_SPEECH",
                            "threshold": "BLOCK_MEDIUM_AND_ABOVE",
                        },
                    ],
                },
            )
            response.raise_for_status()

            data = response.json()
            parts = data["candidates"][0]["content"]["parts"]
            raw_text = _extract_text_from_parts(parts)

            # Parse JSON response
            try:
                story_data = json.loads(raw_text)
                story_response = StoryResponse(**story_data)
            except json.JSONDecodeError as e:
                logger.error(
                    "Failed to parse Gemini JSON response", error=str(e), raw=raw_text[:500]
                )
                raise AIServiceError("Gemini", "Hikaye formatı hatalı. Lütfen tekrar deneyin.")
            except Exception as e:
                logger.error("Failed to validate story structure", error=str(e))
                raise AIServiceError(
                    "Gemini", "Hikaye yapısı doğrulanamadı. Lütfen tekrar deneyin."
                )

            # Compose final visual prompts using scenario templates
            child_description = visual_character_description or self._build_child_description(
                child_name, child_age, child_gender
            )
            final_pages = self._compose_visual_prompts(
                story_response=story_response,
                scenario=scenario,
                child_name=child_name,
                child_description=child_description,
                visual_style=visual_style,
                fixed_outfit=clothing_default,
            )

            logger.info(
                "Structured story generated successfully",
                child_name=child_name,
                scenario=scenario.name,
                page_count=len(story_response.pages),
                title=story_response.title,
                cover_prompt_len=len(final_pages[0].visual_prompt) if final_pages else 0,
            )

            return story_response, final_pages

        except httpx.TimeoutException:
            logger.error("Gemini API timeout", scenario=scenario.name)
            raise AIServiceError(
                "Gemini",
                "AI yoğunluktan dolayı hikayeyi oluşturamadı. Lütfen tekrar deneyin.",
            )
        except httpx.HTTPStatusError as e:
            logger.error(
                "Gemini API error", status=e.response.status_code, body=e.response.text[:500]
            )
            raise AIServiceError("Gemini", "Hikaye oluşturulurken bir hata oluştu.")
        except AIServiceError:
            raise  # Re-raise our custom errors
        except Exception as e:
            logger.exception("Unexpected Gemini error", error=str(e))
            raise AIServiceError("Gemini", "Beklenmeyen bir hata oluştu.")

    # Legacy method for backward compatibility
    @rate_limit_retry(service="gemini", max_attempts=2, timeout_attempts=1)
    async def generate_story(
        self,
        scenario: Scenario,
        child_name: str,
        child_age: int,
        child_gender: str | None,
        outcomes: list[LearningOutcome],
    ) -> str:
        """
        Legacy method: Generate story as plain text.
        Use generate_story_structured() for new implementations.
        """
        story_response, _final_pages, _outfit, _bp = await self.generate_story_structured(
            scenario=scenario,
            child_name=child_name,
            child_age=child_age,
            child_gender=child_gender,
            outcomes=outcomes,
        )

        # Convert structured response to plain text
        full_text = f"# {story_response.title}\n\n"
        for page in story_response.pages:
            if page.page_number == 0:
                continue  # Skip cover for text version
            full_text += f"[SAYFA {page.page_number}]\n{page.text}\n\n"

        return full_text

    async def generate_story_with_prompts(
        self,
        scenario: Scenario,
        child_name: str,
        child_age: int,
        child_gender: str | None,
        outcomes: list[LearningOutcome],
        visual_style: str = "children's book illustration, soft colors",
    ) -> tuple[str, list[FinalPageContent]]:
        """
        Generate story and return both title and pages with composed visual prompts.

        This is the recommended method for new code.

        Returns:
            Tuple of (title, list[FinalPageContent])
        """
        story_response, final_pages, _outfit, _bp = await self.generate_story_structured(
            scenario=scenario,
            child_name=child_name,
            child_age=child_age,
            child_gender=child_gender,
            outcomes=outcomes,
            visual_style=visual_style,
        )
        return story_response.title, final_pages

    def parse_story_pages(self, story_text: str) -> list[str]:
        """
        Parse generated story into individual pages (legacy support).

        Args:
            story_text: Full story text with [SAYFA X] markers

        Returns:
            List of page texts
        """
        import re

        # Split by page markers
        pages = re.split(r"\[SAYFA \d+\]", story_text)

        # Clean up and filter empty pages
        pages = [p.strip() for p in pages if p.strip()]

        # Ensure we have at least 16 pages, pad if necessary
        while len(pages) < 16:
            pages.append("")

        return pages[:16]  # Return exactly 16 pages

    @rate_limit_retry(service="gemini", max_attempts=2, timeout_attempts=1)
    async def generate_json(self, prompt: str) -> dict:
        """
        Generate JSON response from a prompt using Gemini with Visual Director instructions.

        This method is used by StoryGenerationService for generating story text
        with clear, 2D-friendly scene descriptions (no cinematic/lens wording).

        Args:
            prompt: The full prompt text (includes system + user instructions)

        Returns:
            Parsed JSON response as dictionary

        Raises:
            AIServiceError: If generation fails
        """
        api_url = get_gemini_api_url()

        # Inject AI-Director instructions if not already present
        enhanced_prompt = prompt
        if "AI-DIRECTOR" not in prompt and "SANAT YÖNETMENİ" not in prompt:
            enhanced_prompt = f"{AI_DIRECTOR_SYSTEM}\n\n{prompt}"

        logger.info(
            "Generating JSON with Visual Director",
            model=self.model,
            temperature=self.story_temperature,
            prompt_length=len(enhanced_prompt),
        )

        try:
            client = self._get_gemini_client()
            response = await client.post(
                f"{api_url}?key={self.api_key}",
                json={
                    "contents": [{"parts": [{"text": enhanced_prompt}]}],
                    "generationConfig": {
                        "temperature": self.story_temperature,
                        "topK": 64,
                        "topP": 0.95,
                        "maxOutputTokens": 16384,
                        "responseMimeType": "application/json",
                    },
                    "safetySettings": [
                        {
                            "category": "HARM_CATEGORY_HARASSMENT",
                            "threshold": "BLOCK_MEDIUM_AND_ABOVE",
                        },
                        {
                            "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                            "threshold": "BLOCK_MEDIUM_AND_ABOVE",
                        },
                        {
                            "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                            "threshold": "BLOCK_MEDIUM_AND_ABOVE",
                        },
                        {
                            "category": "HARM_CATEGORY_HATE_SPEECH",
                            "threshold": "BLOCK_MEDIUM_AND_ABOVE",
                        },
                    ],
                },
            )
            response.raise_for_status()

            data = response.json()
            parts = data["candidates"][0]["content"]["parts"]
            raw_text = _extract_text_from_parts(parts)

            try:
                result = json.loads(raw_text)
                logger.info(
                    "JSON generation successful",
                    keys=list(result.keys()) if isinstance(result, dict) else "list",
                )
                return result
            except json.JSONDecodeError as e:
                logger.error("Failed to parse Gemini JSON", error=str(e), raw=raw_text[:500])
                raise AIServiceError("Gemini", "AI yanıtı işlenemedi. Lütfen tekrar deneyin.")

        except httpx.TimeoutException:
            logger.error("Gemini API timeout in generate_json")
            raise AIServiceError("Gemini", "AI yoğunluktan dolayı yanıt veremedi.")
        except httpx.HTTPStatusError as e:
            logger.error("Gemini API error", status=e.response.status_code)
            raise AIServiceError("Gemini", "AI servisinde hata oluştu.")
        except AIServiceError:
            raise
        except Exception as e:
            logger.exception("Unexpected error in generate_json", error=str(e))
            raise AIServiceError("Gemini", "Beklenmeyen bir hata oluştu.")

    async def enhance_pages_with_visual_prompts(
        self,
        story_pages: list[dict],
        blueprint: dict,
        character_bible,
        visual_style: str,
        location_key: str,
        value_visual_motif: str = "",
        likeness_hint: str = "",
        has_pulid: bool = False,
        leading_prefix_override: str | None = None,
        style_block_override: str | None = None,
    ) -> list[dict]:
        """Generate visual prompts for story pages that only have text.
        
        Used in two-phase generation: after story text is approved, generate visual prompts.
        
        Args:
            story_pages: Pages with text_tr but no image_prompt_en
            blueprint: Original blueprint from story generation
            character_bible: Character consistency data
            visual_style: Visual style modifier
            location_key: Location key for anchors
            value_visual_motif: Value-based visual motif
            likeness_hint: Face reference hint
            has_pulid: Whether PuLID is enabled
            leading_prefix_override: Style override
            style_block_override: Style block override
            
        Returns:
            Enhanced pages with visual prompts added
        """
        from app.prompt_engine.visual_prompt_builder import enhance_all_pages
        
        logger.info(
            "Enhancing pages with visual prompts",
            page_count=len(story_pages),
            has_character_bible=bool(character_bible),
        )
        
        try:
            enhancement_result = enhance_all_pages(
                pages=story_pages,
                blueprint=blueprint,
                character_bible=character_bible,
                visual_style=visual_style,
                location_key=location_key,
                value_visual_motif=value_visual_motif,
                likeness_hint=likeness_hint,
                has_pulid=has_pulid,
                leading_prefix_override=leading_prefix_override,
                style_block_override=style_block_override,
            )
            enhanced_pages = enhancement_result["pages"]
            
            logger.info(
                "Visual prompts enhanced successfully",
                original_count=len(story_pages),
                enhanced_count=len(enhanced_pages),
            )
            
            return enhanced_pages
        except Exception as e:
            logger.error(
                "Failed to enhance visual prompts",
                error=str(e),
                page_count=len(story_pages),
            )
            raise


_gemini_service: GeminiService | None = None


def get_gemini_service() -> GeminiService:
    """Get or create GeminiService singleton (single source for story/clothing)."""
    global _gemini_service
    if _gemini_service is None:
        _gemini_service = GeminiService()
    return _gemini_service


# Backward compatibility: trials.py imports gemini_service from this module
gemini_service = get_gemini_service()
