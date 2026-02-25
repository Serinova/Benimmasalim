"""
Dinozorlar Macerası: Zaman Yolculuğu Senaryosu - Master Prompt Güncellemesi

Bu script, Dinozorlar Macerası senaryosunu profesyonel, tutarlı ve
paleontoloji odaklı prompt'larla ekler/günceller.

Çalıştırma:
    cd backend
    python -m scripts.update_dinosaur_scenario
"""

import asyncio
import json

from sqlalchemy import select, update
from app.core.database import async_session_factory
from app.models.scenario import Scenario


# =============================================================================
# DİNOZORLAR MACERASI - MASTER PROMPT TEMPLATES
# =============================================================================

# -----------------------------------------------------------------------------
# KAPAK PROMPT TEMPLATE (Modular - Pipeline-Friendly: ~380 char)
# -----------------------------------------------------------------------------

DINOSAUR_COVER_PROMPT = """Epic prehistoric scene: {scene_description}. 
MASSIVE T-Rex (12m) in background (majestic, not threatening). 
Triceratops herd (9m each) grazing. 
GIANT Brachiosaurus (25m) neck reaching clouds. 
Pteranodon flock flying (7m wingspan). 
Child TINY in vast prehistoric world. 
Giant tree ferns (15m), golden sunlight, volcanic mountains distant. 
Time portal glowing blue. Epic adventure atmosphere."""


# -----------------------------------------------------------------------------
# İÇ SAYFA PROMPT TEMPLATE (Modular - Pipeline-Friendly: ~470 char)
# -----------------------------------------------------------------------------

DINOSAUR_PAGE_PROMPT = """Prehistoric scene: {scene_description}. 
Dinosaurs: [T-Rex 12m: majestic, head lowering, ground shake / Triceratops 9m: 3 horns, riding between horns / Brachiosaurus 25m: climbing, 20m view / Velociraptor 2m: feathered pack, alliance / Pteranodon 7m wing: flying carrying child]. 
Giant ferns 15m, cycads, volcanic mountains. 
Golden sun, misty. 
Child TINY, dinosaurs GIGANTIC."""


# -----------------------------------------------------------------------------
# AI HİKAYE ÜRETİM PROMPTU (Gemini için - TR) - Dopamin Yönetimi Blueprint
# -----------------------------------------------------------------------------

DINOSAUR_STORY_PROMPT_TR = """Sen {child_name} isimli {child_age} yaşında bir çocuğun ZAMAN MAKİNESİ ile 65 milyon yıl öncesine, DİNOZORLAR ÇAĞINA yaptığı EPİK MACERA yazıyorsun.

🧠 DOPAMİN YÖNETİMİ - HEYECAN MERDİVENİ:

**BÖLÜM 1 - ANTİSİPASYON** (Sayfa 1-4) [role: opening]:
- Sayfa 1: Zaman makinesi aktif → "Ne göreceğim?" (merak)
- Sayfa 2: İlk dinozor görünüşü → ŞOK! ("DEVASA Brachio!")
  → Dopamin #1: ⭐⭐⭐ (ilk hayranlık)
- Sayfa 3-4: Prehistorik dünya, Ptero uçuyor
  → Emotion: Merak→Şok→Hayranlık

**BÖLÜM 2 - İLK ÖDÜL** (Sayfa 5-7) [role: exploration]:
- Sayfa 5: Trike sürüsü → Endişe ("Üç boynuz! Tehlikeli mi?")
- Sayfa 6: Yavru Trike tanışma → Rahatlama
- Sayfa 7: Lider Trike boynuzlarına binme → BAŞARI!
  → Dopamin #2: ⭐⭐⭐⭐ (ilk binme başarısı)
  → Emotion: Endişe→Rahatlama→Sevinç

**BÖLÜM 3 - YENİ ZORLUK** (Sayfa 8-10) [role: exploration→crisis]:
- Sayfa 8: Sürü panik (uzaktan T-Rex kükremesi) → Endişe
- Sayfa 9: Velociraptor sürüsü çıkıyor → KORKU ARTIYOR
- Sayfa 10: Raptorlar yaklaşıyor → "Avcılar!"
  → Dopamin: Düşüş (yeni tehdit)
  → Emotion: Rahatlık→Endişe→Korku

**BÖLÜM 4 - ORTA ÖDÜLLER** (Sayfa 11-13) [role: resolution]:
- Sayfa 11: Raptor lideri göz göze → İletişim, zeka
  → Dopamin #3: ⭐⭐⭐ (alliance)
- Sayfa 12: Raptor sürüsü kabul ediyor → İTTİFAK!
- Sayfa 13: Brachio'ya tırmanma → 20m yükseklik!
  → Dopamin #4: ⭐⭐⭐⭐⭐ (yüksek heyecan)
  → Emotion: İletişim→İttifak→Epic heyecan

**BÖLÜM 5 - BÜYÜK KRİZ** (Sayfa 14-16) [role: crisis→climax]:
- Sayfa 14: T-Rex yaralı, tuzakta → "12 METRE! Kral!"
  → Endişe MAX: "Kurtarmalı mıyım? Tehlikeli değil mi?"
- Sayfa 15: Yaklaşma cesareti → KRİTİK AN
  → "Kalbim çok hızlı atıyor ama... yardıma ihtiyacı var"
- Sayfa 16: T-Rex'e dokunma, kurtarma → EYLEM
  → Dopamin: En düşük→yükselmeye başlıyor

**BÖLÜM 6 - EPİK DORUK** (Sayfa 17-19) [role: climax]:
- Sayfa 17: Kurtarma başarılı → T-Rex ayağa kalkıyor!
  → Dopamin #5: ⭐⭐⭐⭐⭐ (epic başarı)
- Sayfa 18: T-Rex başını eğiyor → SAYGININ DORUĞI
  → Dopamin #6: ⭐⭐⭐⭐⭐⭐ (MAX! Dinozor kralı saygısı!)
  → "Kral bana teşekkür ediyor!"
- Sayfa 19: Ptero ile victory flight → ZİRVE!
  → Dopamin #7: ⭐⭐⭐⭐⭐ (zafer turu)
  → Emotion: Başarı→Saygı→Zafer→Tatmin

**BÖLÜM 7 - TATMIN** (Sayfa 20-22) [role: conclusion]:
- Sayfa 20: Tüm dinozorlar toplanıyor → HERO
- Sayfa 21: Veda töreni (Brachio, Trike, Raptor, Ptero, T-Rex kükreyerek)
- Sayfa 22: Zaman makinesine dönüş → "Asla unutmayacağım"
  → Dopamin: Sürdürülebilir mutluluk
  → Emotion: Gurur→Duygusallık→Tatmin

⚡ ENDİŞE→BAŞARI DÖNGÜLERİ (4 Kritik):

**Döngü 1 - Trike (Sayfa 5-7):**
- Endişe: "Üç boynuz! Saldırır mı?" 
- Çözüm: Yavru oyuncu, sürü nazik
- Başarı: Lidere binme → Dopamin ⭐⭐⭐⭐

**Döngü 2 - Raptor (Sayfa 9-12):**
- Endişe MAX: "Hızlı avcılar! Tüyleri diken diken!"
- Çözüm: Göz teması, zeka, respect
- Başarı: Alliance → Dopamin ⭐⭐⭐⭐

**Döngü 3 - Brachio (Sayfa 13):**
- Endişe: "25 metre! Çok yüksek, düşer miyim?"
- Eylem: Dikkatli tırmanma
- Başarı: Bulutlara değme → Dopamin ⭐⭐⭐⭐⭐

**Döngü 4 - T-Rex KRAL (Sayfa 14-18) - EN UZUN, EN YÜKSEK:**
- Endişe MAX: "Kral! 12m! Yaralı ama... en güçlüsü!"
- Cesaret: "Yardım etmeliyim" (sayfa 15-16)
- Kurtarma: Tuzaktan çıkarma (sayfa 17)
- Epic ödül: Baş eğme (sayfa 18)
- Dopamin: ⭐⭐⭐⭐⭐⭐ (MAX!)

🦖 HİKAYE YAPISI (Devasa Dinozorlarla Epik Macera):

AÇILIŞ - Zaman Yolculuğu:
- Zaman makinesi ile geçmişe yolculuk, dinozor dünyasına ilk varış
- İlk karşılaşma: DEVASA bir Brachiosaurus gökyüzüne uzanıyor, çocuk karşılaştırma yapıyor
- Pteranodon sürüsü başın üstünde uçuyor, kanat sesleri duyuluyor

OLAY TETİKLEYİCİ - Büyük Tehlike:
- Triceratops sürüsü panik halinde koşuyor - büyük tehlike yaklaşıyor!
- Sürünün liderinin boynuzunda yaralanma var, yardıma ihtiyacı var
- VEYA: Dev bir T-Rex yaralı ve tuzağa düşmüş, kurtarılması gerekiyor
- VEYA: Brachiosaurus sürüsü bataklıkta mahsur kalmış, köprü yapılması lazım

GELİŞME - Devasa Dinozorlarla Bağ Kurma:

**1. BRACHIOSAURUS'A BINME SAHNESİ:**
- Çocuk dev Brachiosaurus'un bacağına tırmanır
- 20 metre yüksekte, sırtında yolculuk yapar
- Gökyüzü manzarası, ağaç tepelerini elleriyle dokunur
- Brachiosaurus nazik devdir, çocuğu güvenle taşır
- Bu yüksekten tehlikeyi görür: T-Rex yaklaşıyor!

**2. PTERANODON İLE UÇUŞ SAHNESİ:**
- Dev Pteranodon (7 metre kanat açıklığı) çocuğu omuzlarından tutar
- Gökyüzünde süzülme, dağların üzerinde uçuş
- Kuşbakışı dinozor sürülerini görür
- Rüzgar yüzünde, bulutlara dokunur
- Heyecan verici iniş: kayalıklara güvenli landing

**3. TRICERATOPS SÜRÜSÜYLE YOLCULUK:**
- Çocuk lider Triceratops'un boynuzları arasına oturur
- Sürü lideri olarak ilerler, 50 Triceratops etrafında
- Güçlü, heybetli yürüyüş - yer sallanıyor
- Sürü çocuğu koruyucu sarıyor

**4. VELOCIRAPTOR SÜRÜSÜYLE İTTİFAK:**
- Tüylü, zeki Velociraptor lideri ile göz göze gelir
- Çocuk onlara saygı gösterir, yardım ister
- Velociraptor sürüsü iz takip eder, çocuğa yol gösterir
- Hızlı koşu sahnesi: Velociraptor sürüsünün arkasında

**5. T-REX KRAL KARŞILAŞMASI (EPİK DORUK):**
- 12 metre uzunluğunda, devasa T-Rex ortaya çıkar
- İLK: Korkutucu, heybetli, yer sallanıyor
- SONRA: Yaralı veya tuzakta, yardıma ihtiyacı var
- Çocuk cesaretle yaklaşır, onu kurtarmayı başarır
- T-Rex minnetle başını eğer - çocuğu dinozor kralı olarak tanır
- T-Rex güvenli mesafeden kükreyerek selamlar - dostluk göstergesi

KAPANIŞ - Kahramanlık ve Vedalaşma:
- Tüm dinozor türleri çocuğu çevreler: Kahraman olarak tanınır
- Brachiosaurus, Triceratops sürüsü, Pteranodon'lar, hatta uzaktan T-Rex
- Epik veda sahnesi: Her dinozor türü kendi dilinde vedalaşır
- Zaman makinesine dönüş, "Asla unutmayacağım" anı
- Gelecekte bu dostluğu her zaman hatırlayacak

⚡ HEYECracker VERICI AKSIYON SAHNELERI (MUTLAŞim):

1. **Yüksek Tempolu Koşu**: Velociraptor sürüsüyle orman içinde hızlı koşma
2. **Binme Macerası**: Brachiosaurus sırtında yüksek yolculuk
3. **Uçuş Deneyimi**: Pteranodon ile gökyüzünde süzülme
4. **Epik Karşılaşma**: T-Rex ile yüz yüze gelme (saygılı, heyecanlı)
5. **Sürü Lideriği**: Triceratops sürüsüyle toplu yürüyüş
6. **Kurtarma Operasyonu**: Yaralı dev dinozoru kurtarma
7. **Güven Anı**: T-Rex'in başını çocuğa doğru eğmesi (nazik, güven)

🦕 DİNOZOR BOYUT ve KORKUTUCULUK YÖNETİMİ:

**DEVASA Ama GÜVENLİ:**
- Dinozorlar GERÇEKÇİ boyutlarda: Brachiosaurus 25m, T-Rex 12m
- İLK karşılaşma: Heybetli, büyük, çocuk ufacık kalır
- SONRA: Dinozorlar nazik, dostane, koruyucu
- Boyut farkı SÜREKLİ vurgulanır: "T-Rex'in tek dişi senin boyundan büyüktü!"
- Ama aksiyon VAR: Binme, uçma, kurtarma, liderlik

**T-REX KRAL SAHNESI:**
- Uzaktan görünüş: Korkutucu, heybetli, güçlü
- Yerdeki sarsıntı hissedilir
- Derin kükreme sesi
- Ama: Çocuğa ZARARA VERMİYOR
- Kurtarıldıktan/yardım edildikten sonra: Başını eğer, minnetle bakar
- Final: Kükreyerek selam verir (dostluk, saygı)

📚 DİNOZOR BİLGİLERİ (Hikayeye Doğal Entegre):

- T-Rex: Kretase'nin en büyük yırtıcısı, 12m uzunluk, 6 ton ağırlık, kısa ön kollar ama güçlü bacaklar
- Triceratops: 3 boynuz (savunma için), sürü halinde yaşar, 9m uzunluk, otobur
- Brachiosaurus: En uzun boyunlu (25m), ön bacaklar arka bacaklardan uzun, ağaç tepesi yiyicisi
- Velociraptor: Tüylü vücut, zeki avcı, 2m uzunluk, sürü halinde avlanır, sıcakkanlı
- Pteranodon: Uçan sürüngen (dinozor değil!), 7m kanat açıklığı, kemikler hafif ve içi boş

💎 ANA DEĞER: CESARET ve SAYGI
- Büyük ve bilinmeyen karşısında cesaretli olmak
- Dev yaratıklara saygı göstermek
- Yardım elini uzatma cesareti
- Farklı olana korku değil merak
- Dostluk her boyutta mümkün

🎬 TON ve ATMOSFER:
- **EPİK MACERA** ağırlıklı
- Sinematik, geniş açılar, dramatik anlar
- Tempo YÜKSEK: Aksiyon → Keşif → Aksiyon
- Duygusal doruk noktaları: T-Rex'in başını eğmesi, veda sahnesi
- Yaşa uygun dil ({child_age} yaş), ama HEYECAN dolu

⛔ YASAKLAR (Çocuk Güvenliği):
- Dinozor saldırısı YOK (T-Rex bile saldırmaz)
- Kan, yara detayı, şiddet sahnesi YOK
- Avlanma detayları YOK (sadece bahsedilebilir)
- Ölüm, fosil oluşumu travmatik anlatım YOK
- Terkedilme, kaybolma travması YOK
- Korku maksimum 10 saniye (hemen geçer, güven gelir)

📖 SAYFA DAĞILIMI:
Hikayeyi {page_count} sayfaya yaz. Her sayfa 3-5 cümle (60-100 kelime).
İlk 2 sayfa: Zaman yolculuğu + ilk karşılaşma
Orta sayfalar: Her dinozor türüyle aksiyon sahnesi (binme, uçma, liderlik)
Son 3 sayfa: T-Rex epik sahne + Veda + Dönüş

🎯 CUSTOM INPUT KULLANIMI:
- {favorite_dinosaur}: Bu dinozora EN FAZLA zaman ayır, en özel bağ
- {time_machine_type}: Hikaye başında ve sonunda bahset
- {discovery_goal}: Ana görev olarak entegre et (ama aksiyon odaklı)

✨ ÖZEL TALİMATLAR:
- Her sayfada EN AZ 1 dinozor GÖRÜNÜR olmalı
- Binme/uçma/liderlik sahneleri MUTLAKa olmalı
- T-Rex sahnesi EPİK, unutulmaz, duygusal (korku değil saygı)
- Veda sahnesi TÜM dinozor türlerini içermeli
- Çocuk HER ZAMAN AKTİF rol alır (izlemez, YAPAR)"""


# -----------------------------------------------------------------------------
# KIYAFET TASARIMLARI (Scenario-Specific)
# -----------------------------------------------------------------------------

OUTFIT_GIRL = """silver-gray explorer jumpsuit with futuristic blue trim lines, protective knee pads with holographic display, high-tech hiking boots with LED lights on sides, tablet device strapped to left arm showing time readings, transparent time-traveler goggles on forehead, utility belt with glowing time machine remote control, small backpack with antenna"""

OUTFIT_BOY = """dark blue time-traveler jacket with metallic silver shoulder pads, cargo pants with zippered tech pockets and knee guards, sturdy brown boots with ankle support and grip soles, digital compass watch on wrist with holographic display, small gray backpack with glowing blue time crystal visible, explorer cap with built-in camera lens on side"""


# -----------------------------------------------------------------------------
# KÜLTÜREL ELEMENTLER (JSON)
# -----------------------------------------------------------------------------

DINOSAUR_CULTURAL_ELEMENTS = {
    "dinosaur_species": [
        "T-Rex (Tyrannosaurus Rex) - distant observation only",
        "Triceratops - friendly herbivore",
        "Brachiosaurus - gentle giant",
        "Velociraptor - curious pack",
        "Pteranodon - flying reptile",
        "Ankylosaurus (background)",
        "Stegosaurus (background)"
    ],
    "prehistoric_environment": [
        "giant tree fern forests (10+ meters)",
        "cycad palm groves",
        "ginkgo trees with fan-shaped leaves",
        "wide river deltas with muddy banks",
        "open plains with dinosaur herds",
        "volcanic mountains (distant, safe)",
        "prehistoric moss and ground ferns"
    ],
    "time_period": "Late Cretaceous (65 million years ago)",
    "color_palette": "earthy brown, mossy green, volcanic gray, amber orange, rust red, prehistoric blue-green",
    "atmosphere": "prehistoric, ancient, mysterious, adventurous, epic scale, time-travel wonder",
    "lighting_options": [
        "bright tropical sun with sharp shadows",
        "golden hour glow across plains",
        "misty morning filtered light",
        "dramatic side-lighting for scale"
    ],
    "educational_themes": [
        "dinosaur anatomy and behavior",
        "prehistoric ecosystems",
        "paleontology basics",
        "time periods and extinction",
        "natural history"
    ],
    "time_travel_elements": [
        "glowing portal with blue energy",
        "sleek time capsule",
        "holographic displays",
        "futuristic technology mixed with prehistoric setting"
    ]
}


# -----------------------------------------------------------------------------
# ÖZEL GİRİŞ ALANLARI (Custom Inputs)
# -----------------------------------------------------------------------------

DINOSAUR_CUSTOM_INPUTS = [
    {
        "key": "favorite_dinosaur",
        "label": "En Sevdiği Dinozor",
        "type": "select",
        "options": [
            "T-Rex (Kral Dinozor)",
            "Triceratops (Üç Boynuzlu)",
            "Brachiosaurus (Uzun Boyunlu)",
            "Velociraptor (Hızlı ve Zeki)",
            "Pteranodon (Uçan Sürüngen)"
        ],
        "default": "Triceratops (Üç Boynuzlu)",
        "required": False,
        "help_text": "Hikayede çocuğun en çok vakit geçireceği dinozor türü"
    },
    {
        "key": "time_machine_type",
        "label": "Zaman Makinesi Türü",
        "type": "select",
        "options": [
            "Işıldayan Kapsül",
            "Mavi Portal",
            "Işınlanma Cihazı",
            "Uçan Zaman Aracı"
        ],
        "default": "Işıldayan Kapsül",
        "required": False,
        "help_text": "Çocuğun geçmişe gidiş yöntemi"
    },
    {
        "key": "discovery_goal",
        "label": "Keşif Amacı",
        "type": "select",
        "options": [
            "Kayıp Yavruyu Ailesine Ulaştır",
            "Dinozor Fotoğrafları Çek",
            "Prehistorik Bitki Örnekleri Topla",
            "Dinozor İzlerini Takip Et"
        ],
        "default": "Kayıp Yavruyu Ailesine Ulaştır",
        "required": False,
        "help_text": "Hikayenin ana macera görevi"
    }
]


async def update_dinosaur_scenario():
    """Dinozorlar Macerası senaryosunu master prompt'larla güncelle veya oluştur."""
    
    print("\n" + "="*60)
    print("DİNOZORLAR MACERASI: ZAMAN YOLCULUĞU SENARYO GÜNCELLEMESİ")
    print("="*60 + "\n")
    
    async with async_session_factory() as db:
        # Mevcut senaryoyu bul
        result = await db.execute(
            select(Scenario).where(Scenario.name.ilike("%Dinozor%"))
        )
        scenario = result.scalar_one_or_none()
        
        if not scenario:
            print("[INFO] 'Dinozorlar Macerası' senaryosu bulunamadı. Yeni oluşturuluyor...")
            scenario = Scenario(
                name="Dinozorlar Macerası: Zaman Yolculuğu",
                is_active=True
            )
            db.add(scenario)
        else:
            print(f"[OK] Senaryo bulundu: {scenario.name} (ID: {scenario.id})")
        
        # Güncelleme yap
        scenario.description = "Zaman makinesi ile 65 milyon yıl öncesine gidip T-Rex, Triceratops, Brachiosaurus ve daha fazlasıyla tanış! Kayıp yavru dinozorun ailesini bul ve prehistorik dünyanın sırlarını keşfet. Aksiyon dolu bir macera!"
        scenario.cover_prompt_template = DINOSAUR_COVER_PROMPT
        scenario.page_prompt_template = DINOSAUR_PAGE_PROMPT
        scenario.story_prompt_tr = DINOSAUR_STORY_PROMPT_TR
        scenario.ai_prompt_template = None  # V3 story_prompt_tr kullanıyor
        scenario.location_en = "Cretaceous Period"
        scenario.theme_key = "dinosaur_time_travel"
        scenario.cultural_elements = DINOSAUR_CULTURAL_ELEMENTS
        scenario.custom_inputs_schema = DINOSAUR_CUSTOM_INPUTS
        scenario.outfit_girl = OUTFIT_GIRL
        scenario.outfit_boy = OUTFIT_BOY
        scenario.default_page_count = 22
        scenario.display_order = 13
        
        await db.commit()
        await db.refresh(scenario)
        
        print("\n[OK] GÜNCELLEME TAMAMLANDI!\n")
        print("-"*60)
        print("Güncellenen alanlar:")
        print(f"   - ID: {scenario.id}")
        print(f"   - name: {scenario.name}")
        print(f"   - description: {len(scenario.description)} karakter")
        print(f"   - cover_prompt_template: {len(DINOSAUR_COVER_PROMPT)} karakter")
        print(f"   - page_prompt_template: {len(DINOSAUR_PAGE_PROMPT)} karakter")
        print(f"   - story_prompt_tr: {len(DINOSAUR_STORY_PROMPT_TR)} karakter")
        print("   - location_en: Cretaceous Period")
        print("   - theme_key: dinosaur_time_travel")
        print(f"   - cultural_elements: {len(json.dumps(DINOSAUR_CULTURAL_ELEMENTS))} karakter (JSON)")
        print(f"   - custom_inputs_schema: {len(DINOSAUR_CUSTOM_INPUTS)} özel alan")
        print(f"   - outfit_girl: {len(OUTFIT_GIRL)} karakter")
        print(f"   - outfit_boy: {len(OUTFIT_BOY)} karakter")
        print(f"   - default_page_count: {scenario.default_page_count}")
        print(f"   - display_order: {scenario.display_order}")
        print("-"*60)
        
        # Preview
        print("\nKAPAK PROMPT ÖNİZLEME (ilk 500 karakter):")
        print("-"*60)
        print(DINOSAUR_COVER_PROMPT[:500] + "...")
        
        print("\nSAYFA PROMPT ÖNİZLEME (ilk 500 karakter):")
        print("-"*60)
        print(DINOSAUR_PAGE_PROMPT[:500] + "...")
        
        print("\nSTORY_PROMPT_TR ÖNİZLEME (ilk 400 karakter):")
        print("-"*60)
        print(DINOSAUR_STORY_PROMPT_TR[:400] + "...")
        
        print("\n" + "="*60)
        print("Dinozorlar Macerası artık master-level prompt'lara sahip!")
        print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(update_dinosaur_scenario())
