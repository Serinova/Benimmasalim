"""
Update Prompt Templates for Fal.ai Flux + PuLID Pipeline

This script updates all existing scenarios and visual styles in the database
to be compatible with the new Fal.ai image generation pipeline.

CHANGES:
1. Remove {child_description} variable (PuLID handles face from photo)
2. Add {clothing_description} variable (for outfit consistency)
3. Convert comma-separated tags to natural sentences (Flux preference)
4. Remove physical trait descriptions (hair, eyes, skin)

Run: python -m scripts.update_prompts_for_fal
"""

import asyncio

from sqlalchemy import select, update

from app.core.database import async_session_factory
from app.models.scenario import Scenario
from app.models.visual_style import VisualStyle

# =============================================================================
# NEW FLUX-OPTIMIZED TEMPLATES
# =============================================================================

# Template for cover images
NEW_COVER_TEMPLATE = """A beautiful children's book cover illustration for a story called "{book_title}".
The scene shows a young child {scene_description}.
The child is wearing {clothing_description}.
{visual_style}.
The composition is designed as a professional book cover with space for the title at the top."""

# Template for inner page images
NEW_PAGE_TEMPLATE = """A children's book illustration showing a young child {scene_description}.
The child is wearing {clothing_description}.
{visual_style}.
The scene has a clear focal point with soft background, suitable for text overlay at the bottom."""

# Updated visual style modifiers (natural sentences instead of tags)
# Includes variations for different naming conventions in database
NEW_VISUAL_STYLES = {
    # Original names
    "Çizgi Film Tarzı": "The illustration style is Disney Pixar 3D animation with vibrant colors and cute character design",
    "Vintage Retro": "The illustration style is vintage retro with muted pastel colors and nostalgic warm tones reminiscent of classic children's books",
    "Sulu Boya": "The illustration style is soft watercolor painting with dreamy atmosphere, gentle colors and artistic soft edges",
    "Oyun Tarzı": "The illustration style is colorful video game art with bright saturated colors and playful adventure game aesthetic",
    "Kaligrafik": "The illustration style is elegant storybook illustration with calligraphy elements and ornate decorative details",
    # Alternative names found in database
    "Japon Anime": "The illustration style is Japanese anime with big expressive eyes, soft pastel colors and whimsical kawaii aesthetic",
    "3D Süper Kahraman": "The illustration style is 3D superhero animation with dynamic poses, bright colors and heroic comic book aesthetic",
    "Sulu Boya Rüyası": "The illustration style is dreamy watercolor painting with soft flowing colors, gentle gradients and magical atmosphere",
    "Yaratıcı Pastel Boya": "The illustration style is creative pastel artwork with soft chalky textures, warm colors and cozy storybook feeling",
    "Kağıt Katman Sanatı": "The illustration style is paper cut layered art with depth, shadows and handcrafted paper texture aesthetic",
    "Sihirli Animasyon": "The illustration style is magical animation with sparkles, glowing effects and enchanting fairy tale atmosphere",
}


async def update_scenarios() -> int:
    """Update all scenarios with new Flux-compatible templates."""
    print("\n[UPDATE] Updating scenario prompt templates...")
    
    async with async_session_factory() as db:
        # Get all scenarios
        result = await db.execute(select(Scenario))
        scenarios = result.scalars().all()
        
        updated = 0
        for scenario in scenarios:
            old_cover = scenario.cover_prompt_template
            old_page = scenario.page_prompt_template
            
            # Check if already updated (contains {clothing_description})
            if "{clothing_description}" in old_cover and "{clothing_description}" in old_page:
                print(f"  [SKIP] {scenario.name} - already updated")
                continue
            
            # Update templates
            scenario.cover_prompt_template = NEW_COVER_TEMPLATE
            scenario.page_prompt_template = NEW_PAGE_TEMPLATE
            
            updated += 1
            print(f"  [OK] Updated: {scenario.name}")
            print(f"       Old cover had: {'{child_description}' in old_cover}")
            print(f"       New cover has: {{clothing_description}}, {{scene_description}}")
        
        await db.commit()
        
    return updated


async def update_visual_styles() -> int:
    """Update visual style prompt modifiers to natural sentences."""
    print("\n[UPDATE] Updating visual style prompt modifiers...")
    
    async with async_session_factory() as db:
        # Get all visual styles
        result = await db.execute(select(VisualStyle))
        styles = result.scalars().all()
        
        updated = 0
        for style in styles:
            if style.name in NEW_VISUAL_STYLES:
                old_modifier = style.prompt_modifier
                new_modifier = NEW_VISUAL_STYLES[style.name]
                
                # Check if already updated
                if style.prompt_modifier == new_modifier:
                    print(f"  [SKIP] {style.name} - already updated")
                    continue
                
                style.prompt_modifier = new_modifier
                updated += 1
                print(f"  [OK] Updated: {style.name}")
                print(f"       Old: {old_modifier[:50]}...")
                print(f"       New: {new_modifier[:50]}...")
            else:
                print(f"  [WARN] {style.name} - no predefined update (custom style)")
        
        await db.commit()
        
    return updated


async def validate_templates() -> dict:
    """Validate that all templates follow Fal.ai rules."""
    print("\n[VALIDATE] Checking template compliance...")
    
    issues = {
        "physical_traits": [],
        "missing_clothing": [],
        "comma_tags": [],
    }
    
    # Forbidden physical trait patterns
    forbidden_patterns = [
        "{child_description}",
        "{child_eyes}",
        "{child_hair}",
        "{child_skin}",
        "blue eyes",
        "brown hair",
        "blonde hair",
    ]
    
    async with async_session_factory() as db:
        # Check scenarios
        result = await db.execute(select(Scenario))
        scenarios = result.scalars().all()
        
        for scenario in scenarios:
            templates = [
                ("cover", scenario.cover_prompt_template),
                ("page", scenario.page_prompt_template),
            ]
            
            for template_type, template in templates:
                # Rule 1: Check for physical traits
                for pattern in forbidden_patterns:
                    if pattern.lower() in template.lower():
                        issues["physical_traits"].append(
                            f"{scenario.name} ({template_type}): contains '{pattern}'"
                        )
                
                # Rule 2: Check for clothing variable
                if "{clothing_description}" not in template:
                    issues["missing_clothing"].append(
                        f"{scenario.name} ({template_type}): missing {{clothing_description}}"
                    )
        
        # Check visual styles
        result = await db.execute(select(VisualStyle))
        styles = result.scalars().all()
        
        for style in styles:
            # Rule 3: Check for comma-separated tags (more than 3 commas in short text)
            comma_count = style.prompt_modifier.count(",")
            if comma_count > 3 and len(style.prompt_modifier) < 150:
                issues["comma_tags"].append(
                    f"{style.name}: {comma_count} commas (likely tag-style)"
                )
    
    return issues


async def main():
    """Run the update script."""
    print("=" * 60)
    print("FAL.AI PROMPT TEMPLATE UPDATE SCRIPT")
    print("=" * 60)
    
    # Update scenarios
    scenarios_updated = await update_scenarios()
    print(f"\n[RESULT] {scenarios_updated} scenarios updated")
    
    # Update visual styles
    styles_updated = await update_visual_styles()
    print(f"[RESULT] {styles_updated} visual styles updated")
    
    # Validate
    issues = await validate_templates()
    
    print("\n" + "=" * 60)
    print("VALIDATION RESULTS")
    print("=" * 60)
    
    total_issues = sum(len(v) for v in issues.values())
    
    if total_issues == 0:
        print("\n[PASS] ALL TEMPLATES PASS FAL.AI COMPATIBILITY CHECK!")
    else:
        print(f"\n[FAIL] Found {total_issues} issues:\n")
        
        if issues["physical_traits"]:
            print("Rule 1 (No Physical Traits) FAILURES:")
            for issue in issues["physical_traits"]:
                print(f"  - {issue}")
        
        if issues["missing_clothing"]:
            print("\nRule 2 (Clothing Variable) FAILURES:")
            for issue in issues["missing_clothing"]:
                print(f"  - {issue}")
        
        if issues["comma_tags"]:
            print("\nRule 3 (Natural Sentences) WARNINGS:")
            for issue in issues["comma_tags"]:
                print(f"  - {issue}")
    
    print("\n" + "=" * 60)
    print("UPDATE COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
