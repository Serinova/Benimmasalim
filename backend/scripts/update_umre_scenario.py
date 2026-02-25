"""
Umre Yolculuğu Senaryosu - Master Prompt Güncellemesi

Bu script, Umre Yolculuğu senaryosunu profesyonel, saygılı ve
manevi odaklı prompt'larla ekler/günceller.

HASSAS İÇERİK: Dini danışman onayı önerilir.

Çalıştırma:
    cd backend
    python -m scripts.update_umre_scenario
"""

import asyncio
import json

from sqlalchemy import select, update
from app.core.database import async_session_factory
from app.models.scenario import Scenario


# =============================================================================
# UMRE YOLCULUĞU - MASTER PROMPT TEMPLATES
# =============================================================================

# -----------------------------------------------------------------------------
# KAPAK PROMPT TEMPLATE (Style-Agnostic)
# -----------------------------------------------------------------------------

UMRE_COVER_PROMPT = """Sacred pilgrimage scene: {scene_description}. 
Child in foreground, Masjid al-Haram and black Kaaba with golden Kiswah in distance. 
White marble courtyard, golden minarets, grand domes. 
Peaceful pilgrims in white ihram (distant, no faces). 
Golden sunlight, spiritual atmosphere. 
Child looking toward Kaaba with reverence (NOT camera). 
Wide shot: child 20%, architecture 80%. 
RESPECTFUL distance. NO Prophet/angel depictions."""


# -----------------------------------------------------------------------------
# İÇ SAYFA PROMPT TEMPLATE (Style-Agnostic)
# -----------------------------------------------------------------------------

UMRE_PAGE_PROMPT = """Umrah pilgrimage scene: {scene_description}. 
Locations: [Kaaba: black with golden Kiswah embroidery, white marble courtyard, golden minarets, pilgrims in white ihram (distant) / Masjid al-Nabawi: green dome (Gunbad al-Khadra), white marble, date palms, peaceful / Safa-Marwa: long marble corridor, 7 walks ritual, green-lit middle zone / Hira Cave: rocky mountain, cave entrance, Mecca panoramic view / Arafat: white monument, open plain, humility / Zemzem: marble interior, blessed water dispensing]. 
Islamic architecture: geometric patterns, calligraphy (decorative, not readable). 
Golden sunlight, reverent atmosphere. 
NO Prophet/angel depictions, NO worship close-ups, NO detailed pilgrim faces. 
Child observes respectfully."""


# -----------------------------------------------------------------------------
# AI HİKAYE ÜRETİM PROMPTU (Gemini için - TR)
# -----------------------------------------------------------------------------

UMRE_STORY_PROMPT_TR = """Ailesiyle birlikte Mekke ve Medine'ye Umre yolculuğuna giden {child_name} adlı {child_age} yaşında bir çocuğun manevi ve eğitici hikayesini yaz.

HİKAYE YAPISI:
- Giriş: Havaalanında heyecan, ailesiyle birlikte kutsal topraklara gidiş hazırlığı
- Kabe İlk Görüş: Masjid al-Haram'a ilk adım, Kabe'yi görme anı, gözyaşları ve huşu
- Tavaf: Kabe etrafında dönme ritüeli, insan birliği hissi, dua
- Safa-Marwa Sa'y: Hz. Hacer'in hikayesi (annesi anlatır), iki tepe arası yürüyüş, sebat
- Zemzem: Bereketli su içme, kutsallık hissi
- Medine Yolculuğu: Yeşil kubbeyi görme, Mescid-i Nebevi'nin huzuru, palmiye ağaçları
- Nur Dağı (Hira): Hz. Muhammed'in ilk vahyi aldığı yer (hikaye olarak anlatılır), bilgi arayışı
- Arafat: Dua tepesi, tevazu, tüm insanlık için dua
- Dönüş: Manevi dönüşüm, minnet, evde ailesine anlatma

MANEVI TEMALAR (hikayeye doğal entegre):
- İlk Kabe görüşünde gözyaşları (duygusal, manevi bağ)
- Tavaf sırasında dua etme, ailesiyle el ele
- Hz. Hacer'in sabrı ve sebatı (Safa-Marwa'da)
- Zemzem suyunun bereketi ve tarihi
- Mescid-i Nebevi'nin huzuru ve yeşil kubbenin anlamı
- Hira Mağarası'nda bilgi ve vahiy teması
- Arafat'ta tüm insanlık için dua, kardeşlik

EĞİTSEL BİLGİLER (hikayeye organik yerleştir):
- Kabe: İlk mabet, Kıble, İbrahim ve İsmail
- Tavaf: 7 tur, saat yönü tersine
- Safa-Marwa: Hz. Hacer'in su arayışı, 7 gidiş-dönüş
- Zemzem: Hz. İsmail için fışkıran su, binlerce yıldır akar
- Mescid-i Nebevi: Hz. Muhammed'in mescidi, yeşil kubbe
- Hira Mağarası: İlk vahiy yeri
- Arafat: Veda Hutbesi'nin verildiği yer

HER LOKASYONDA 1 MİNİ BİLGİ (ansiklopedik değil, hikayenin içinde):
- Örnek: "{child_name}, Kabe'nin etrafında yavaşça yürürken, annesinin elini sıkıca tuttu. 'Bu, Hz. İbrahim ve oğlu İsmail'in Allah için inşa ettiği ilk mabet,' dedi annesi. {child_name}'in kalbi huzurla doldu."

ANA DEĞER: SAYGI ve TEVAZU
- Kutsal mekanlara derin saygı
- Büyüklere (anne-baba, din büyükleri) saygı
- Farklı milletlerden Müslümanlara saygı ve kardeşlik
- Tevazu ile dua etme, kibir göstermeme

TON:
- Saygılı, huzurlu, öğretici
- Duygusal anlar (gözyaşı pozitif bağlamda - huşu, sevgi)
- Meditatif, sakin tempo
- Aile bağı ve birlik vurgusu
- Vaaz edici DEĞİL, keşif ve deneyim odaklı
- Yaşa uygun dil ({child_age} yaş - detaylı açıklamalar)

YASAKLAR (dini hassasiyet):
- Hz. Muhammed, diğer peygamberler, melekler GÖRSELLEŞTİRİLMEZ (sadece hikaye anlatımı)
- Namaz kılan insanların yüzleri detaylı gösterilmez
- Hacerü'l Esved (kara taş) sadece bahsedilir, close-up yok
- Mezhep/sekt ayrımcılığı yok
- Abartılı mucize veya fantastik unsurlar yok
- Korku, baskı, travma unsurları yok
- İbadet hatası gösterimi yok

SAYFA DAĞILIMI:
Hikayeyi {page_count} sayfaya uygun olarak yaz. Her sayfa 2-4 cümle (50-90 kelime). 7-10 yaş için detaylı ve öğretici dil kullan.

CUSTOM INPUT KULLANIMI (eğer sağlanmışsa):
- {favorite_location}: Çocuğun en sevdiği yeri hikayede öne çıkar
- {travel_with}: Kimle gittiğini hikayede belirt
- {special_dua}: Özel duasını hikayede vurgula"""


# -----------------------------------------------------------------------------
# KIYAFET TASARIMLARI (Scenario-Specific - İhram Benzeri)
# -----------------------------------------------------------------------------

OUTFIT_GIRL = """white cotton modest dress with long sleeves reaching wrists, floor-length covering ankles, white hijab headscarf covering hair completely with simple edges, comfortable beige sandals, small white backpack, simple and clean appearance inspired by ihram purity, no jewelry or decorations, serene and humble look"""

OUTFIT_BOY = """white cotton tunic (knee-length kurta style), white taqiyah prayer cap on head, light beige loose-fitting pants, comfortable tan sandals, small white backpack, simple and clean appearance inspired by ihram purity, no patterns or decorations, humble and respectful look"""


# -----------------------------------------------------------------------------
# KÜLTÜREL ELEMENTLER (JSON)
# -----------------------------------------------------------------------------

UMRE_CULTURAL_ELEMENTS = {
    "holy_locations": [
        "Kaaba (House of Allah) - center of Islamic world",
        "Masjid al-Haram (Grand Mosque, Mecca)",
        "Masjid al-Nabawi (Prophet's Mosque, Medina)",
        "Safa and Marwa Hills - Sa'y ritual path",
        "Jabal al-Noor (Mountain of Light) - Hira Cave",
        "Jabal Rahmah (Mount Arafat) - Plain of Arafat",
        "Zemzem Well - blessed water source"
    ],
    "umrah_rituals": [
        "Tawaf - 7 circuits around Kaaba (counterclockwise)",
        "Sa'y - 7 walks between Safa and Marwa hills",
        "Prayer at sacred sites",
        "Drinking Zemzem water",
        "Dua (supplication and prayer)",
        "Visiting Prophet's Mosque in Medina"
    ],
    "architecture": [
        "Black Kaaba with golden embroidered Kiswah covering",
        "Green Dome (Gunbad al-Khadra) of Prophet's Mosque",
        "White marble minarets with golden crescents",
        "Grand golden domes and ornate decorations",
        "White marble courtyards with geometric patterns",
        "Modern umbrella shade structures",
        "Islamic geometric patterns on walls and floors",
        "Calligraphic decorations (ornamental, not readable text)"
    ],
    "historical_elements": [
        "Prophet Ibrahim and Ismail built the Kaaba",
        "Hajar's search for water (Safa-Marwa origin)",
        "Zemzem spring miracle for baby Ismail",
        "Prophet Muhammad received first revelation at Hira Cave",
        "Farewell Sermon at Mount Arafat",
        "Prophet's Mosque built by Prophet Muhammad in Medina"
    ],
    "atmosphere": "peaceful, reverent, spiritual, humble, educational, devotional, serene",
    "color_palette": "white (purity), gold (sacred), green (Medina), black (Kaaba), marble white, warm sunset amber",
    "lighting_options": [
        "golden hour sunlight with spiritual glow",
        "soft morning light with gentle shadows",
        "clear bright daylight on white marble",
        "sunset amber tones with dramatic sacred sky"
    ],
    "educational_themes": [
        "Islamic pilgrimage history and significance",
        "Prophet Muhammad's life (narrated, not depicted)",
        "Respect for sacred places",
        "Unity of Muslims worldwide",
        "Gratitude, humility, and patience",
        "Knowledge seeking and spiritual reflection"
    ],
    "values": [
        "Respect (Saygı) - for sacred places, elders, diversity",
        "Humility (Tevazu) - before Allah, no arrogance",
        "Gratitude (Şükür) - for blessings and opportunity",
        "Unity (Birlik) - brotherhood/sisterhood of faith",
        "Patience (Sabır) - learning from Hajar's story"
    ]
}


# -----------------------------------------------------------------------------
# ÖZEL GİRİŞ ALANLARI (Custom Inputs)
# -----------------------------------------------------------------------------

UMRE_CUSTOM_INPUTS = [
    {
        "key": "favorite_location",
        "label": "En Sevdiği Yer",
        "type": "select",
        "options": [
            "Kabe ve Mescid-i Haram",
            "Mescid-i Nebevi (Medine)",
            "Safa-Marwa Tepeleri",
            "Nur Dağı (Hira Mağarası)",
            "Arafat Dağı"
        ],
        "default": "Kabe ve Mescid-i Haram",
        "required": False,
        "help_text": "Hikayede çocuğun en çok vakit geçireceği lokasyon"
    },
    {
        "key": "travel_with",
        "label": "Kimle Gidiyor",
        "type": "select",
        "options": [
            "Anne ve Baba ile",
            "Aile ile (büyük grup)",
            "Dede/Nine ile"
        ],
        "default": "Anne ve Baba ile",
        "required": False,
        "help_text": "Umre yolculuğuna kiminle gittiği"
    },
    {
        "key": "special_dua",
        "label": "Özel Dua Konusu",
        "type": "select",
        "options": [
            "Aile sağlığı için",
            "Bilgi ve başarı için",
            "Dünya barışı için",
            "Tüm insanlık için"
        ],
        "default": "Aile sağlığı için",
        "required": False,
        "help_text": "Çocuğun özel olarak ettiği dua"
    }
]


async def update_umre_scenario():
    """Umre Yolculuğu senaryosunu master prompt'larla güncelle veya oluştur."""
    
    print("\n" + "="*60)
    print("UMRE YOLCULUĞU SENARYO GÜNCELLEMESİ")
    print("="*60 + "\n")
    
    async with async_session_factory() as db:
        # Mevcut senaryoyu bul
        result = await db.execute(
            select(Scenario).where(Scenario.name.ilike("%Umre%"))
        )
        scenario = result.scalar_one_or_none()
        
        if not scenario:
            print("[INFO] 'Umre Yolculuğu' senaryosu bulunamadı. Yeni oluşturuluyor...")
            scenario = Scenario(
                name="Umre Yolculuğu: Kutsal Topraklarda",
                is_active=True
            )
            db.add(scenario)
        else:
            print(f"[OK] Senaryo bulundu: {scenario.name} (ID: {scenario.id})")
        
        # Güncelleme yap
        scenario.description = "Ailesiyle birlikte Mekke ve Medine'ye manevi bir yolculuk! Kabe'yi görme, tavaf, Safa-Marwa, Zemzem, yeşil kubbe ve Nur Dağı. Saygı, tevazu ve şükür dolu bir deneyim."
        scenario.cover_prompt_template = UMRE_COVER_PROMPT
        scenario.page_prompt_template = UMRE_PAGE_PROMPT
        scenario.story_prompt_tr = UMRE_STORY_PROMPT_TR
        scenario.ai_prompt_template = None  # V3 story_prompt_tr kullanıyor
        scenario.location_en = "Mecca and Medina"
        scenario.theme_key = "umre_pilgrimage"
        scenario.cultural_elements = UMRE_CULTURAL_ELEMENTS
        scenario.custom_inputs_schema = UMRE_CUSTOM_INPUTS
        scenario.outfit_girl = OUTFIT_GIRL
        scenario.outfit_boy = OUTFIT_BOY
        scenario.default_page_count = 22
        scenario.display_order = 14
        
        # Marketing alanları
        scenario.marketing_badge = "Manevi Yolculuk"
        scenario.age_range = "7-10 yaş"
        scenario.tagline = "Kutsal topraklarda unutulmaz bir manevi deneyim"
        scenario.marketing_features = [
            "Kabe ve Mescid-i Haram ziyareti",
            "Safa-Marwa ve Zemzem suyu",
            "Medine ve yeşil kubbe",
            "Nur Dağı ve Arafat",
            "Saygı ve tevazu değerleri",
            "Ailece manevi bağ"
        ]
        scenario.estimated_duration = "20-25 dakika okuma"
        scenario.marketing_price_label = "299 TL'den başlayan fiyatlarla"
        scenario.rating = 5.0
        
        await db.commit()
        await db.refresh(scenario)
        
        print("\n[OK] GÜNCELLEME TAMAMLANDI!\n")
        print("-"*60)
        print("Güncellenen alanlar:")
        print(f"   - ID: {scenario.id}")
        print(f"   - name: {scenario.name}")
        print(f"   - description: {len(scenario.description)} karakter")
        print(f"   - cover_prompt_template: {len(UMRE_COVER_PROMPT)} karakter")
        print(f"   - page_prompt_template: {len(UMRE_PAGE_PROMPT)} karakter")
        print(f"   - story_prompt_tr: {len(UMRE_STORY_PROMPT_TR)} karakter")
        print("   - location_en: Mecca and Medina")
        print("   - theme_key: umre_pilgrimage")
        print(f"   - cultural_elements: {len(json.dumps(UMRE_CULTURAL_ELEMENTS))} karakter (JSON)")
        print(f"   - custom_inputs_schema: {len(UMRE_CUSTOM_INPUTS)} özel alan")
        print(f"   - outfit_girl: {len(OUTFIT_GIRL)} karakter")
        print(f"   - outfit_boy: {len(OUTFIT_BOY)} karakter")
        print(f"   - default_page_count: {scenario.default_page_count}")
        print(f"   - display_order: {scenario.display_order}")
        print("-"*60)
        
        # Preview
        print("\nKAPAK PROMPT ÖNİZLEME (ilk 500 karakter):")
        print("-"*60)
        print(UMRE_COVER_PROMPT[:500] + "...")
        
        print("\nSAYFA PROMPT ÖNİZLEME (ilk 500 karakter):")
        print("-"*60)
        print(UMRE_PAGE_PROMPT[:500] + "...")
        
        print("\nSTORY_PROMPT_TR ÖNİZLEME (ilk 400 karakter):")
        print("-"*60)
        print(UMRE_STORY_PROMPT_TR[:400] + "...")
        
        print("\n" + "="*60)
        print("⚠️  DİNİ DANIŞ MAN ONAYI GEREKLİ!")
        print("Prod'a çıkmadan önce içeriği inceletin.")
        print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(update_umre_scenario())
