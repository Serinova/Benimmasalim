"""
Amazon Ormanları Keşfediyorum Senaryosu - Master Prompt Güncellemesi

Bu script, Amazon Ormanları Keşfediyorum senaryosunu profesyonel, tutarlı ve
biyolojik çeşitlilik odaklı prompt'larla günceller.

Çalıştırma:
    cd backend
    python -m scripts.update_amazon_scenario
"""

import asyncio
import json

from sqlalchemy import select, update
from app.core.database import async_session_factory
from app.models.scenario import Scenario


# =============================================================================
# AMAZON ORMANLARI KEŞFEDİYORUM - MASTER PROMPT TEMPLATES
# =============================================================================

# -----------------------------------------------------------------------------
# KAPAK PROMPT TEMPLATE (Style-Agnostic)
# -----------------------------------------------------------------------------

AMAZON_COVER_PROMPT = """Amazon rainforest scene: {scene_description}. 
Child on massive tree root at river, gazing into dense jungle. 
Towering kapok trees with buttress roots, emerald canopy. 
Scarlet and blue-gold macaws flying, toucans perched. 
Winding brown river, golden sunlight shafts (god rays). 
Hanging lianas, vibrant orchids, misty atmosphere. 
Rich colors: emerald, scarlet, electric blue, amber. 
Wide shot: child 25%, rainforest 75%. 
Epic scale, biodiversity."""


# -----------------------------------------------------------------------------
# İÇ SAYFA PROMPT TEMPLATE (Style-Agnostic)
# -----------------------------------------------------------------------------

AMAZON_PAGE_PROMPT = """Amazon rainforest scene: {scene_description}. 
Elements: [Giant kapok trees with buttress roots, multi-layer canopy (40m+), winding tributary / Birds: scarlet macaws (pairs), blue-gold macaws, toucans, harpy eagles (distant) / River fauna: pink dolphins (boto), capybaras, caimans (small, non-threatening), river turtles / Forest: three-toed sloths, howler monkeys, poison dart frogs (blue/red/yellow), morpho butterflies (iridescent blue), leafcutter ants / Jaguar: distant, majestic, respectful, NOT threatening]. 
Vegetation: lianas, bromeliads, orchids, moss, ferns, dense undergrowth. 
Dappled sunlight filtering through canopy, misty humid air. 
Rich colors: emerald, jade, scarlet, electric blue, golden amber. 
At least 2-3 species visible per scene. 
Layered depth: emergent layer, canopy, understory, forest floor."""


# -----------------------------------------------------------------------------
# AI HİKAYE ÜRETİM PROMPTU (Gemini için - TR)
# -----------------------------------------------------------------------------

AMAZON_STORY_PROMPT_TR = """Amazon yağmur ormanlarında geçen, {child_name} adlı {child_age} yaşında bir çocuğun keşif macerası hikayesi yaz.

🌳 KEŞİF DOPAMİNİ - BİYOÇEŞİTLİLİK MERDİVENİ:

**BÖLÜM 1 - İLK KEŞİF** (Sayfa 1-4) [role: opening]:
- Sayfa 1-2: Amazon'a varış, ilk izlenimler
  Epic #1: Dev kapok ağacı kökler (devasa scale)
  Emotion: Merak, heyecan
- Sayfa 3-4: İlk hayvan karşılaşması
  Dopamin ⭐⭐⭐ (başlangıç)

**BÖLÜM 2 - MACAW AİLESİ** (Sayfa 5-8) [role: exploration]:
- Sayfa 5-6: Scarlet macaw ailesi
  → Endişe: "Kayıp yavru macaw!"
- Sayfa 7-8: Yuva bulma yardımı
  → Epic #2: Renkli macaw uçuşu (sürü halinde)
  → Başarı: Aile birliği → Dopamin ⭐⭐⭐⭐
  → DEĞER: Yardımlaşma

**BÖLÜM 3 - NEHİR KEŞFİ** (Sayfa 9-12) [role: exploration]:
- Sayfa 9-10: Nehirde yön kaybı
  → Endişe: "Hangi yöne gitsem?"
- Sayfa 11-12: Pembe yunus (boto) rehberlik
  → Epic #3: Yunus dansı, nehir surfing
  → Başarı: İletişim, güven → Dopamin ⭐⭐⭐⭐
  → DEĞER: İletişim, dostluk

**BÖLÜM 4 - TEMBEL ANI** (Sayfa 13-15) [role: climax]:
- Sayfa 13-14: Üç parmaklı tembel ile tanışma
  → Soru: "Neden bu kadar yavaş?"
  → Epic #4: Tembelin dünyası - sabır, gözlem
- Sayfa 15: Öğrenme anı
  → Başarı: Herkesin kendi temposu var → Dopamin ⭐⭐⭐⭐⭐
  → DEĞER: Sabır, farklılıklara saygı

**BÖLÜM 5 - KARINCA EKİBİ** (Sayfa 16-18) [role: resolution]:
- Sayfa 16-17: Yaprak kesici karıncalar
  → Epic #5: Organize çalışma hattı
  → Gözlem: Minicik ama organize!
- Sayfa 18: İşbirliği anlaşılıyor
  → Başarı: Birlikte güçlüyüz → Dopamin ⭐⭐⭐⭐
  → DEĞER: İşbirliği, ekip çalışması

**BÖLÜM 6 - JAGUAR CAMEO** (Sayfa 19-20) [role: resolution]:
- Sayfa 19: Uzaktan jaguar görünüşü
  → Epic #6: Ormanın kralı (saygılı mesafe)
  → Endişe: "Tehlikeli mi?" → Hayır, ormanın koruyucusu!
- Sayfa 20: Saygı anlaşılıyor
  → Dopamin ⭐⭐⭐
  → DEĞER: Her canlının rolü var

**BÖLÜM 7 - DÖNÜŞ VE KORUMA BİLİNCİ** (Sayfa 21-22) [role: conclusion]:
- Sayfa 21: Günbatımı canopy görünümü
  → Tüm orman panoramik
- Sayfa 22: Dönüş ve söz
  → "Bu ormanı koruyacağım"
  → Dopamin: Sürdürülebilir tatmin
  → DEĞER: Doğayı koruma sorumluluğu

⚡ KEŞİF→ÖĞRENME DÖNGÜLERİ (4 Kritik):

**Döngü 1 - Macaw ailesi** (5-8):
- Endişe: "Kayıp yavru! Ailesini bulamaz"
- Eylem: Yuva arama, yardım
- Başarı: Aile birliği → Dopamin ⭐⭐⭐⭐

**Döngü 2 - Pembe yunus** (10-12):
- Endişe: "Nehirde kayboldum"
- Eylem: Yunus ile iletişim
- Başarı: Rehberlik, güven → Dopamin ⭐⭐⭐⭐

**Döngü 3 - Tembel** (14-15):
- Soru: "Neden bu kadar yavaş?"
- Gözlem: Sabır, herkesin temposu farklı
- Öğrenme: Farklılıklara saygı → Dopamin ⭐⭐⭐⭐⭐

**Döngü 4 - Karıncalar** (17-18):
- Gözlem: "Minicikler ama organize!"
- Keşif: İşbirliği gücü
- Başarı: Ekip çalışması → Dopamin ⭐⭐⭐⭐

HİKAYE YAPISI (Biyoçeşitlilik Keşfi):

HAYVANLAR VE ÖĞRETİLER:
1. **Scarlet macaw ailesi** → Yardımlaşma, aile bağları
2. **Pembe nehir yunusu (boto)** → İletişim, rehberlik
3. **Üç parmaklı tembel** → Sabır, herkesin kendi hızı
4. **Yaprak kesici karıncalar** → İşbirliği, organize çalışma
5. **Jaguar (uzaktan)** → Saygı, ormanın dengesi

EK HAYVANLAR (sahne zenginliği):
- Toucan, kapybara, morfo kelebek, zehirli ok kurbağası (renkli)
- Morpho butterfly cloud (mavi patlama) - görsel şölen

MİNİ BİLGİLER (hikayeye doğal yerleştir):
- Her hayvan karşılaşmasında 1 kısa bilgi
- Örnek: "{child_name} nehir yunusunun sıçradığını görünce mutlu oldu. Annesi demişti: Pembe yunuslar dünyanın tek tatlı su yunusuydu!"

DEĞERLER:
- Yardımlaşma ve empati (macaw)
- İletişim ve dostluk (yunus)
- Sabır ve farklılıklara saygı (tembel)
- İşbirliği (karıncalar)
- Biyolojik çeşitlilik
- Ormanı koruma sorumluluğu

TON:
- Merak uyandırıcı, keşif odaklı
- Eğitici ama didaktik değil
- Şiddetsiz, güvenli, pozitif

YASAKLAR:
- Korku, şiddet, gore yok
- Yılan saldırısı yok
- Kaybolma travması yok
- Jaguar tehlikeli DEĞİL (uzak, saygılı)
- Hayvan zararı yok

Hikayeyi {page_count} sayfaya yaz. Her sayfa 2-4 cümle (40-80 kelime). 
Vurgulanmak istenen değer: {value_name}. Dopamini yönet, keşif heyecanı yarat."""


# -----------------------------------------------------------------------------
# KIYAFET TASARIMLARI (Scenario-Specific)
# -----------------------------------------------------------------------------

OUTFIT_GIRL = """khaki explorer vest over light green breathable shirt, cargo shorts with multiple pockets, sturdy brown hiking boots, small binoculars around neck, fabric hat with mosquito net"""

OUTFIT_BOY = """olive green explorer shirt with rolled-up sleeves, khaki cargo pants with zippered pockets, brown leather hiking boots, canvas backpack with water bottle, wide-brim explorer hat"""


# -----------------------------------------------------------------------------
# KÜLTÜREL ELEMENTLER (JSON)
# -----------------------------------------------------------------------------

AMAZON_CULTURAL_ELEMENTS = {
    "primary_landmarks": [
        "giant kapok trees with buttress roots",
        "winding tributary rivers",
        "multi-layered rainforest canopy",
        "flooded forest (igapó)",
        "massive strangler figs"
    ],
    "fauna_diversity": [
        "scarlet macaws (pairs)",
        "pink river dolphins",
        "three-toed sloths",
        "toucans",
        "leafcutter ants",
        "poison dart frogs",
        "morpho butterflies",
        "capybaras"
    ],
    "flora_diversity": [
        "kapok/ceiba trees",
        "bromeliads and orchids",
        "hanging lianas",
        "strangler figs",
        "dense ferns",
        "moss-covered bark"
    ],
    "color_palette": "deep emerald green, vibrant scarlet, electric blue, golden amber, jade, warm brown",
    "atmosphere": "lush, humid, biodiverse, ancient, mystical",
    "time_periods": ["filtered morning light", "dappled midday", "golden afternoon", "misty dawn"],
    "educational_themes": ["biodiversity", "ecosystem layers", "animal behavior", "conservation"]
}


# -----------------------------------------------------------------------------
# ÖZEL GİRİŞ ALANLARI (Custom Inputs)
# -----------------------------------------------------------------------------

AMAZON_CUSTOM_INPUTS = [
    {
        "key": "favorite_animal",
        "label": "En Sevdiği Hayvan",
        "type": "select",
        "options": [
            "Renkli Papağan (Macaw)",
            "Pembe Nehir Yunusu",
            "Ağaç Tembeli",
            "Toucan (Gagalı Kuş)",
            "Mavi Kelebek"
        ],
        "default": "Renkli Papağan (Macaw)",
        "required": False,
        "help_text": "Hikayede çocuğun en çok vakit geçireceği hayvan arkadaş"
    },
    {
        "key": "helper_tool",
        "label": "Yardım Aracı",
        "type": "select",
        "options": [
            "Harita ve Pusula",
            "Dürbün ve Not Defteri",
            "Su Matarası",
            "Sihirli Fener"
        ],
        "default": "Dürbün ve Not Defteri",
        "required": False,
        "help_text": "Ormanda keşif yaparken kullanacağı özel araç"
    },
    {
        "key": "jungle_mission",
        "label": "Orman Görevi",
        "type": "select",
        "options": [
            "Kayıp Yavruyu Ailesine Ulaştır",
            "Gizli Su Kaynağını Keşfet",
            "Dev Ağacın Sırrını Çöz",
            "Orman Haritasını Tamamla"
        ],
        "default": "Kayıp Yavruyu Ailesine Ulaştır",
        "required": False,
        "help_text": "Hikayenin ana macera görevi"
    }
]


async def update_amazon_scenario():
    """Amazon Ormanları Keşfediyorum senaryosunu master prompt'larla güncelle veya oluştur."""
    
    print("\n" + "="*60)
    print("AMAZON ORMANLARI KEŞFEDİYORUM SENARYO GÜNCELLEMESİ")
    print("="*60 + "\n")
    
    async with async_session_factory() as db:
        # Mevcut senaryoyu bul
        result = await db.execute(
            select(Scenario).where(Scenario.name.ilike("%Amazon%Ormanlar%"))
        )
        scenario = result.scalar_one_or_none()
        
        if not scenario:
            print("[INFO] 'Amazon Ormanları Keşfediyorum' senaryosu bulunamadı. Yeni oluşturuluyor...")
            scenario = Scenario(
                name="Amazon Ormanları Keşfediyorum",
                is_active=True
            )
            db.add(scenario)
        else:
            print(f"[OK] Senaryo bulundu: {scenario.name} (ID: {scenario.id})")
        
        # Güncelleme yap
        scenario.description = "Dünyanın en zengin ekosistemi Amazon yağmur ormanlarında büyülü bir keşif! Renkli papağanlar, pembe nehir yunusları, ağaç tembelleri ve dev kapok ağaçları arasında biyolojik çeşitliliği keşfet. Yardımlaşma ve doğayı koruma değerlerini öğren."
        scenario.cover_prompt_template = AMAZON_COVER_PROMPT
        scenario.page_prompt_template = AMAZON_PAGE_PROMPT
        scenario.story_prompt_tr = AMAZON_STORY_PROMPT_TR
        scenario.ai_prompt_template = None  # V2 story_prompt_tr kullanıyor
        scenario.location_en = "Amazon Rainforest"
        scenario.theme_key = "amazon_rainforest"
        scenario.cultural_elements = AMAZON_CULTURAL_ELEMENTS
        scenario.custom_inputs_schema = AMAZON_CUSTOM_INPUTS
        scenario.outfit_girl = OUTFIT_GIRL
        scenario.outfit_boy = OUTFIT_BOY
        scenario.default_page_count = 22
        scenario.display_order = 12
        
        await db.commit()
        await db.refresh(scenario)
        
        print("\n[OK] GÜNCELLEME TAMAMLANDI!\n")
        print("-"*60)
        print("Güncellenen alanlar:")
        print(f"   - ID: {scenario.id}")
        print(f"   - name: {scenario.name}")
        print(f"   - description: {len(scenario.description)} karakter")
        print(f"   - cover_prompt_template: {len(AMAZON_COVER_PROMPT)} karakter")
        print(f"   - page_prompt_template: {len(AMAZON_PAGE_PROMPT)} karakter")
        print(f"   - story_prompt_tr: {len(AMAZON_STORY_PROMPT_TR)} karakter")
        print("   - location_en: Amazon Rainforest")
        print("   - theme_key: amazon_rainforest")
        print(f"   - cultural_elements: {len(json.dumps(AMAZON_CULTURAL_ELEMENTS))} karakter (JSON)")
        print(f"   - custom_inputs_schema: {len(AMAZON_CUSTOM_INPUTS)} özel alan")
        print(f"   - outfit_girl: {len(OUTFIT_GIRL)} karakter")
        print(f"   - outfit_boy: {len(OUTFIT_BOY)} karakter")
        print(f"   - default_page_count: {scenario.default_page_count}")
        print(f"   - display_order: {scenario.display_order}")
        print("-"*60)
        
        # Preview
        print("\nKAPAK PROMPT ÖNİZLEME (ilk 500 karakter):")
        print("-"*60)
        print(AMAZON_COVER_PROMPT[:500] + "...")
        
        print("\nSAYFA PROMPT ÖNİZLEME (ilk 500 karakter):")
        print("-"*60)
        print(AMAZON_PAGE_PROMPT[:500] + "...")
        
        print("\nSTORY_PROMPT_TR ÖNİZLEME (ilk 400 karakter):")
        print("-"*60)
        print(AMAZON_STORY_PROMPT_TR[:400] + "...")
        
        print("\n" + "="*60)
        print("Amazon Ormanları Keşfediyorum artık master-level prompt'lara sahip!")
        print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(update_amazon_scenario())
