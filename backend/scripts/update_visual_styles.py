"""
Visual Styles - Master Update for PuLID Face Preservation

Bu script, tum visual style'lari PuLID uyumlu ve yuz koruma odakli olarak gunceller.

KRITIK: PuLID Face Preservation
- id_weight: 0.8-0.95 arasi (dusuk = daha artistik, yuksek = daha gercekci yuz)
- Prompt'larda ASLA fiziksel ozellik yazilmaz
- "preserve facial features", "maintain face identity" gibi ifadeler eklenir

Calistirma:
    cd backend
    python -m scripts.update_visual_styles
"""

import asyncio
import uuid
from sqlalchemy import select, delete
from app.core.database import async_session_factory
from app.models.visual_style import VisualStyle


# =============================================================================
# MASTER VISUAL STYLES - PuLID OPTIMIZED
# =============================================================================

VISUAL_STYLES = [
    # =========================================================================
    # 1. 3D SUPER KAHRAMAN (Superhero Style) - YENi
    # =========================================================================
    # CRITICAL: Superhero = child wearing CAPE over regular clothes
    # NOT Incredibles costume! Child's face must be IDENTICAL to photo
    {
        "name": "3D Super Kahraman",
        "thumbnail_url": "/styles/superhero-3d.jpg",
        "prompt_modifier": """SUPERHERO STYLE for children's book illustration.

WHAT SUPERHERO MEANS (VERY IMPORTANT):
- The child wears a colorful flowing CAPE/CLOAK over their regular adventure clothes
- The cape is heroic red or child's favorite color, flowing dramatically
- DO NOT put the child in a superhero costume/suit (no Incredibles, no spandex)
- Child wears normal adventure outfit (t-shirt, pants) WITH a superhero cape added

FACE PRESERVATION (CRITICAL - HIGHEST PRIORITY):
- The child's face must be IDENTICAL to the reference photo
- Exact same eye shape, nose, mouth, and facial proportions
- The parent must INSTANTLY recognize: "This is definitely my child!"
- Apply artistic style to cape and environment ONLY, not to face
- Face should look like a beautiful portrait of the actual child

COMPOSITION (VERY IMPORTANT):
- WIDE SHOT composition - child is 30-40% of the frame, NOT filling entire image
- Background is CLEARLY VISIBLE and DETAILED - location must be recognizable
- DO NOT blur the background - show full scenic detail
- The scene/location (Istanbul, Cappadocia, etc.) must be clearly identifiable

ILLUSTRATION STYLE:
- Beautiful children's book illustration style
- Warm, vibrant colors with good contrast
- Professional quality similar to modern picture books
- Cape flows heroically with dynamic movement
- Warm lighting that flatters the child's face""",
    },
    
    # =========================================================================
    # 2. CIZGI FILM TARZI (Disney Pixar) - GUNCELLENDI
    # =========================================================================
    {
        "name": "Cizgi Film Tarzi",
        "thumbnail_url": "/styles/cartoon.jpg",
        "prompt_modifier": """The illustration style is Disney Pixar 3D animation with the warmth of "Coco" and charm of "Up".

STYLE CHARACTERISTICS:
- Soft 3D rendered look with rounded, friendly shapes
- Warm, vibrant color palette with magical lighting
- Cute character proportions with expressive features
- Gentle subsurface scattering on skin
- Dreamy, storybook atmosphere

FACE PRESERVATION RULES (CRITICAL):
- Child's facial features must remain recognizable from reference photo
- Apply cartoon stylization to expressions, NOT to core face structure
- Maintain the child's unique eye shape, nose, and smile
- Parent must instantly recognize their child

TECHNICAL DETAILS:
- Soft global illumination
- Gentle rim lighting
- Bokeh background blur
- Warm color temperature""",
    },
    
    # =========================================================================
    # 3. SULU BOYA (Watercolor) - GUNCELLENDI
    # =========================================================================
    {
        "name": "Sulu Boya",
        "thumbnail_url": "/styles/watercolor.jpg",
        "prompt_modifier": """The illustration style is professional watercolor painting with the elegance of classic children's book illustrations.

STYLE CHARACTERISTICS:
- Soft watercolor washes with visible brush strokes
- Dreamy, ethereal atmosphere with soft edges
- Gentle pastel color palette with subtle color bleeding
- Artistic paper texture visible
- Delicate, handcrafted artistic quality

FACE PRESERVATION RULES (CRITICAL):
- Child's face rendered with careful watercolor technique
- Facial features clearly defined despite soft style
- Maintain recognizable likeness - "This is my child as a watercolor painting"
- Soft artistic effect on edges, but face core preserved

TECHNICAL DETAILS:
- Visible watercolor paper grain
- Soft color gradients
- Gentle wet-on-wet effects
- Warm, nostalgic lighting""",
    },
    
    # =========================================================================
    # 4. VINTAGE RETRO - GUNCELLENDI
    # =========================================================================
    {
        "name": "Vintage Retro",
        "thumbnail_url": "/styles/vintage.jpg",
        "prompt_modifier": """The illustration style is vintage retro children's book art reminiscent of 1950s-60s Golden Books era.

STYLE CHARACTERISTICS:
- Muted, warm pastel color palette
- Nostalgic, timeless quality
- Soft textures with slight grain
- Classic storybook composition
- Warm, cozy atmosphere

FACE PRESERVATION RULES (CRITICAL):
- Child's face clearly recognizable with vintage artistic treatment
- Apply retro color grading, NOT face distortion
- Maintain child's unique facial features and expressions
- "This looks like a classic book illustration of my child"

TECHNICAL DETAILS:
- Subtle film grain texture
- Warm sepia undertones
- Soft vignette edges
- Classic golden hour lighting""",
    },
    
    # =========================================================================
    # 5. OYUN TARZI (Video Game Art) - GUNCELLENDI
    # =========================================================================
    {
        "name": "Oyun Tarzi",
        "thumbnail_url": "/styles/game.jpg",
        "prompt_modifier": """The illustration style is colorful adventure video game art similar to Nintendo and mobile game aesthetics.

STYLE CHARACTERISTICS:
- Bright, saturated color palette
- Playful, energetic compositions
- Clean, polished digital art style
- Dynamic lighting with game-like effects
- Fun, adventurous atmosphere

FACE PRESERVATION RULES (CRITICAL):
- Child's face must be recognizable with game art stylization
- Apply colorful game aesthetic to environment and style
- Maintain child's facial identity and features
- "This looks like my child as a video game character"

TECHNICAL DETAILS:
- Clean digital rendering
- Vibrant color saturation
- Soft cel-shading effects
- Playful rim lighting""",
    },
    
    # =========================================================================
    # 6. KALIGRAFIK (Elegant Storybook) - GUNCELLENDI
    # =========================================================================
    {
        "name": "Kaligrafik",
        "thumbnail_url": "/styles/calligraphy.jpg",
        "prompt_modifier": """The illustration style is elegant, ornate storybook illustration with fairy tale quality.

STYLE CHARACTERISTICS:
- Delicate, refined artistic style
- Ornate decorative elements and borders
- Elegant color palette with gold accents
- Fairy tale atmosphere with magical details
- Classic, timeless storybook quality

FACE PRESERVATION RULES (CRITICAL):
- Child's face rendered with elegant artistic care
- Facial features clearly defined and recognizable
- Apply decorative elegance to scene, preserve face identity
- "This is my child in a beautiful fairy tale book"

TECHNICAL DETAILS:
- Fine artistic detailing
- Subtle gold highlights
- Soft, diffused lighting
- Elegant composition""",
    },
    
    # =========================================================================
    # 7. ANIME TARZI (Japanese Animation) - YENi
    # =========================================================================
    {
        "name": "Anime Tarzi",
        "thumbnail_url": "/styles/anime.jpg",
        "prompt_modifier": """The illustration style is high-quality Japanese anime art similar to Studio Ghibli films.

STYLE CHARACTERISTICS:
- Beautiful anime art style with expressive eyes
- Soft, dreamy color palette
- Detailed backgrounds with magical atmosphere
- Studio Ghibli-inspired warmth and wonder
- Gentle, emotional storytelling quality

FACE PRESERVATION RULES (CRITICAL):
- Child's face adapted to anime style while KEEPING recognizable features
- Eye shape and facial structure must reference the child's real features
- Apply anime artistic style, NOT generic anime face
- "This anime version still looks like my child"

TECHNICAL DETAILS:
- Soft anime shading
- Beautiful sky and nature backgrounds
- Gentle lighting effects
- Expressive character poses""",
    },
    
    # =========================================================================
    # 8. GERCEKCI MASAL (Realistic Storybook) - YENi
    # =========================================================================
    {
        "name": "Gercekci Masal",
        "thumbnail_url": "/styles/realistic.jpg",
        "prompt_modifier": """The illustration style is realistic children's book illustration with photographic quality faces.

STYLE CHARACTERISTICS:
- High-quality realistic rendering
- Photorealistic face with artistic background
- Rich, detailed textures and lighting
- Professional portrait quality for the child
- Magical realism atmosphere

FACE PRESERVATION RULES (MOST CRITICAL):
- Child's face must be HIGHLY realistic and immediately recognizable
- Maximum face identity preservation - parent says "This IS my child!"
- Apply artistic style to environment and lighting only
- Face should look like a beautiful portrait of the actual child

TECHNICAL DETAILS:
- Professional portrait lighting on face
- Realistic skin tones and textures
- Artistic background with depth
- High detail rendering""",
    },
]


# =============================================================================
# PULID AYARLARI - STIL BAZLI
# =============================================================================

STYLE_PULID_SETTINGS = {
    "3D Super Kahraman": {"id_weight": 0.92, "guidance": 3.2},  # HIGH - face must be identical
    "Cizgi Film Tarzi": {"id_weight": 0.85, "guidance": 3.5},
    "Sulu Boya": {"id_weight": 0.82, "guidance": 3.5},
    "Vintage Retro": {"id_weight": 0.85, "guidance": 3.5},
    "Oyun Tarzi": {"id_weight": 0.82, "guidance": 3.5},
    "Kaligrafik": {"id_weight": 0.85, "guidance": 3.5},
    "Anime Tarzi": {"id_weight": 0.78, "guidance": 4.0},  # Anime needs more stylization freedom
    "Gercekci Masal": {"id_weight": 0.95, "guidance": 3.0},  # Maximum face preservation
}


async def update_visual_styles():
    """Tum visual style'lari PuLID uyumlu olarak guncelle."""
    
    print("\n" + "="*60)
    print("VISUAL STYLES - MASTER UPDATE")
    print("PuLID Face Preservation Optimized")
    print("="*60 + "\n")
    
    async with async_session_factory() as db:
        # Mevcut stilleri sil (clean update)
        await db.execute(delete(VisualStyle))
        print("[INFO] Mevcut stiller silindi")
        
        # Yeni stilleri ekle
        for style_data in VISUAL_STYLES:
            style = VisualStyle(
                id=uuid.uuid4(),
                name=style_data["name"],
                thumbnail_url=style_data["thumbnail_url"],
                prompt_modifier=style_data["prompt_modifier"],
                is_active=True,
            )
            db.add(style)
            
            pulid_settings = STYLE_PULID_SETTINGS.get(style_data["name"], {})
            print(f"[OK] {style_data['name']}")
            print(f"     - id_weight: {pulid_settings.get('id_weight', 0.80)}")
            print(f"     - prompt length: {len(style_data['prompt_modifier'])} chars")
        
        await db.commit()
        
        print("\n" + "-"*60)
        print(f"[DONE] {len(VISUAL_STYLES)} visual style olusturuldu")
        print("-"*60)
        
        # 3D Super Kahraman detayli onizleme
        print("\n3D SUPER KAHRAMAN STIL ONIZLEME:")
        print("-"*60)
        superhero_style = next(s for s in VISUAL_STYLES if s["name"] == "3D Super Kahraman")
        print(superhero_style["prompt_modifier"][:800] + "...")
        
        print("\n" + "="*60)
        print("Visual styles PuLID uyumlu olarak guncellendi!")
        print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(update_visual_styles())
