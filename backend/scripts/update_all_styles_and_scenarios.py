"""
Master Update Script - Tum Stiller ve Senaryolar
Background-First Prompt Sistemi

Bu script tum visual style ve senaryolari yeni sisteme gore gunceller:
- Arka plan ONCE ve DETAYLI
- Cocuk KUCUK (%30-40)
- Kompozisyon kurallari NET
- Kulturel elementler ZORUNLU

Calistirma:
    cd backend
    python -m scripts.update_all_styles_and_scenarios
"""

import asyncio
import uuid

from sqlalchemy import select

from app.core.database import async_session_factory
from app.models.scenario import Scenario

# =============================================================================
# VISUAL STYLES - BACKGROUND-FIRST OPTIMIZED
# =============================================================================

# =============================================================================
# VISUAL STYLES - SHORT PROMPTS (Flux optimized - max 80 chars each)
# =============================================================================
# CRITICAL: Flux ignores long prompts. Keep style modifiers VERY SHORT.
# Location comes from scenario template, style is just a modifier.
# =============================================================================

VISUAL_STYLES = [
    # =========================================================================
    # 1. 3D SUPER KAHRAMAN
    # =========================================================================
    {
        "name": "3D Super Kahraman",
        "thumbnail_url": "/styles/superhero-3d.jpg",
        "prompt_modifier": "3D superhero style, child with flowing cape, vibrant colors, wide shot.",
    },
    
    # =========================================================================
    # 2. CIZGI FILM TARZI (Disney/Pixar Style)
    # =========================================================================
    {
        "name": "Cizgi Film Tarzi",
        "thumbnail_url": "/styles/cartoon.jpg",
        "prompt_modifier": "Disney Pixar 3D animation style, warm colors, magical lighting, wide shot.",
    },
    
    # =========================================================================
    # 3. SULU BOYA (Watercolor)
    # =========================================================================
    {
        "name": "Sulu Boya",
        "thumbnail_url": "/styles/watercolor.jpg",
        "prompt_modifier": "Watercolor painting style, soft brush strokes, dreamy atmosphere, wide shot.",
    },
    
    # =========================================================================
    # 4. VINTAGE RETRO
    # =========================================================================
    {
        "name": "Vintage Retro",
        "thumbnail_url": "/styles/vintage.jpg",
        "prompt_modifier": "Vintage 1950s Golden Books style, warm pastels, nostalgic, wide shot.",
    },
    
    # =========================================================================
    # 5. OYUN TARZI (Video Game Art)
    # =========================================================================
    {
        "name": "Oyun Tarzi",
        "thumbnail_url": "/styles/game.jpg",
        "prompt_modifier": "Video game art style, bright saturated colors, adventure aesthetic, wide shot.",
    },
    
    # =========================================================================
    # 6. KALIGRAFIK (Elegant Storybook)
    # =========================================================================
    {
        "name": "Kaligrafik",
        "thumbnail_url": "/styles/calligraphy.jpg",
        "prompt_modifier": "Elegant fairy tale storybook style, ornate details, magical atmosphere, wide shot.",
    },
    
    # =========================================================================
    # 7. ANIME TARZI (Studio Ghibli Style)
    # =========================================================================
    {
        "name": "Anime Tarzi",
        "thumbnail_url": "/styles/anime.jpg",
        "prompt_modifier": "Studio Ghibli anime style, detailed backgrounds, soft dreamy colors, wide shot.",
    },
    
    # =========================================================================
    # 8. GERCEKCI MASAL (Realistic Storybook)
    # =========================================================================
    {
        "name": "Gercekci Masal",
        "thumbnail_url": "/styles/realistic.jpg",
        "prompt_modifier": "Realistic storybook illustration, detailed scenic background, warm lighting, wide shot.",
    },
]




# =============================================================================
# SCENARIOS - BACKGROUND-FIRST TEMPLATES
# =============================================================================

# -----------------------------------------------------------------------------
# KAPADOKYA MACERASI - AI-DIRECTOR MODE (Context-Aware Prompts)
# -----------------------------------------------------------------------------
# IMPORTANT: Do NOT hardcode outdoor landscapes!
# Gemini AI-Director generates page-specific scenes:
# - Indoor (cave/tunnel): "Inside dimly lit underground tunnel..."
# - Outdoor (valley): "Wide view of Cappadocia valley with balloons..."
# - Bedroom: "Cozy bedroom with child at bedside table..."
# 
# {scene_description} contains the FULL context from AI-Director!
# -----------------------------------------------------------------------------

# Scene-only: no {visual_style} or style tokens. Style applied at image API.
KAPADOKYA_COVER_PROMPT = """{scene_description}. A young child wearing {clothing_description}. Wide shot, child 30% of frame, environment 70%. Child NOT looking at camera. Title space at top."""

KAPADOKYA_PAGE_PROMPT = """{scene_description}. A young child wearing {clothing_description}. Wide shot, child naturally interacting with the environment, NOT facing camera. Text space at bottom."""

KAPADOKYA_AI_PROMPT = """Sen profesyonel bir cocuk hikayesi yazari ve Kapadokya uzmanisin.

GOREV: {child_name} adli {child_age} yasindaki cocuk icin Kapadokya'da gecen buyulu bir macera hikayesi yaz.

KAPADOKYA MEKANLARI (HER SAHNEDE SPESIFIK KULLAN):
1. Goreme Vadisi - kayalara oyulmus antik magara evler, renkli duvar resimleri
2. Uchisar Kalesi - Kapadokya'nin en yuksek peri bacasi
3. Derinkuyu Yeralti Sehri - gizemli tuneller, gizli odalar
4. Guvercin Vadisi - binlerce guvercin evi oyulmus kayalar
5. Pasabag (Mantar Kayalar) - sapkali peri bacalari
6. Zelve Vadisi - terk edilmis kaya koyu
7. Kizilcukur (Rose Valley) - pembe kayalar

KULTUREL ELEMENTLER:
- Sicak hava balonlari ve balon festivalleri
- Geleneksel comlek yapimi (Avanos)
- El dokuma halilar ve kilimler
- Nazar boncugu gelenegi
- Turk kahvesi ve misafirperverlik

SAHNE ACIKLAMASI KURALLARI (Ingilizce scene):
Her sahne icin MUTLAKA:
1. Spesifik Kapadokya lokasyonu (orn: "among the mushroom-shaped fairy chimneys of Pasabag")
2. Arka plan detaylari (orn: "with dozens of colorful hot air balloons floating in the golden sky")
3. Kulturel elementler (orn: "traditional pottery visible, evil eye beads hanging")
4. Isik ve atmosfer (orn: "warm sunset light casting long shadows")

YASAK: Genel ifadeler ("in Cappadocia", "near rocks")
DOGRU: Detayli, sinematik, lokasyon-spesifik tasvirler

EGITSEL KAZANIMLAR: {outcomes}

KARAKTER: {child_name}, {child_age} yas, {child_gender}"""



# (Eski senaryolar kaldırıldı - Sadece Kapadokya ve Yerebatan Sarnıcı aktif)


# =============================================================================
# SCENARIO CONFIGURATIONS
# =============================================================================

SCENARIOS = [
    {
        "name": "Kapadokya Macerasi",
        "description": "Peri bacalari, sicak hava balonlari ve yeralti sehirleri arasinda unutulmaz bir Kapadokya macerasi! Turkiye'nin en buyulu bolgesinde gizemli magaralari, antik yeralti sehirlerini ve renkli balonlari kesfet.",
        "thumbnail_url": "/scenarios/kapadokya.jpg",
        "cover_prompt_template": KAPADOKYA_COVER_PROMPT,
        "page_prompt_template": KAPADOKYA_PAGE_PROMPT,
        "ai_prompt_template": KAPADOKYA_AI_PROMPT,
        "theme_key": "cappadocia",
        "display_order": 1,
        "location_constraints": "Cappadocia landmarks required: fairy chimneys, hot air balloons, cave dwellings, rock formations",
        "cultural_elements": {
            "primary": ["fairy chimneys", "hot air balloons", "cave dwellings", "Uchisar Castle"],
            "secondary": ["pottery", "carpets", "underground cities", "pigeon houses"],
            "colors": "warm earth tones, terracotta, sandy beige, sunset oranges"
        },
        "custom_inputs": [
            {"key": "favorite_balloon_color", "label": "En Sevdigi Balon Rengi", "type": "select", "options": ["Kirmizi", "Turuncu", "Mavi", "Gokkusagi"], "default": "Gokkusagi"},
            {"key": "travel_companion", "label": "Yol Arkadasi", "type": "select", "options": ["Sevimli Guvercin", "Bilge Baykus", "Cesur Karinca"], "default": "Sevimli Guvercin"}
        ]
    },
]


# =============================================================================
# UPDATE FUNCTIONS
# =============================================================================

async def update_visual_styles(db):
    """Visual styles artık style_config.py'den yönetiliyor.

    Admin panelden (/admin/visual-styles) thumbnail ve display_name ayarlanır.
    Bu fonksiyon no-op olarak bırakılmıştır.
    """
    print("\n" + "="*60)
    print("VISUAL STYLES → style_config.py'den yönetiliyor")
    print("Admin panelden düzenleyin: /admin/visual-styles")
    print("="*60)


async def update_scenarios(db):
    """Update all scenarios."""
    print("\n" + "="*60)
    print("SENARYOLAR GUNCELLENIYOR")
    print("="*60)
    
    for scenario_data in SCENARIOS:
        # Mevcut senaryoyu bul veya olustur
        result = await db.execute(
            select(Scenario).where(Scenario.name == scenario_data["name"])
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            scenario = existing
            print(f"  [UPDATE] {scenario_data['name']}")
        else:
            scenario = Scenario(id=uuid.uuid4())
            db.add(scenario)
            print(f"  [CREATE] {scenario_data['name']}")
        
        # Tum alanlari guncelle
        scenario.name = scenario_data["name"]
        scenario.description = scenario_data["description"]
        scenario.thumbnail_url = scenario_data["thumbnail_url"]
        scenario.cover_prompt_template = scenario_data["cover_prompt_template"]
        scenario.page_prompt_template = scenario_data["page_prompt_template"]
        scenario.ai_prompt_template = scenario_data["ai_prompt_template"]
        scenario.theme_key = scenario_data["theme_key"]
        scenario.display_order = scenario_data["display_order"]
        scenario.location_constraints = scenario_data.get("location_constraints", "")
        scenario.cultural_elements = scenario_data.get("cultural_elements")
        scenario.custom_inputs_schema = scenario_data.get("custom_inputs", [])
        scenario.is_active = True
    
    print(f"\n  TOPLAM: {len(SCENARIOS)} senaryo guncellendi")


async def main():
    """Main update function."""
    print("\n" + "="*70)
    print("MASTER UPDATE - TUM STILLER VE SENARYOLAR")
    print("Background-First Prompt Sistemi")
    print("="*70)
    
    async with async_session_factory() as db:
        await update_visual_styles(db)
        await update_scenarios(db)
        await db.commit()
    
    print("\n" + "="*70)
    print("GUNCELLEME TAMAMLANDI!")
    print("="*70)
    print("\nYeni sistem ozellikleri:")
    print("  - Arka plan ONCE ve DETAYLI (%60-70)")
    print("  - Cocuk KUCUK (%30-40)")
    print("  - Kulturel elementler ZORUNLU")
    print("  - Lokasyon aninda tanidir")
    print("="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
