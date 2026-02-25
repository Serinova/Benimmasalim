import asyncio
import os
import sys

# Ensure backend path is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from app.prompt.book_context import BookContext
from app.prompt.composer import PromptComposer
from app.services.ai.face_analyzer_service import get_face_analyzer
from app.services.ai.gemini_consistent_image import GeminiConsistentImageService


async def main():
    image_path = r"C:\Users\yusuf\OneDrive\Belgeler\BenimMasalim\WhatsApp Image 2026-02-11 at 18.33.33 (1).jpeg"
    with open(image_path, "rb") as f:
        image_bytes = f.read()

    print("Analyzing face...")
    analyzer = get_face_analyzer()
    description = await analyzer.get_enhanced_child_description(
        image_source=image_bytes,
        child_name="Eren",
        child_age=6,
        child_gender="erkek",
    )
    
    print("\n--- FACE DESCRIPTION ---")
    print(description)
    
    print("\n--- BUILDING BOOK CONTEXT ---")
    ctx = BookContext.build(
        child_name="Eren",
        child_age=6,
        child_gender="erkek",
        style_modifier="default",
        character_description=description,
        clothing_description="a red t-shirt and blue jeans",
        hair_description="",
        face_reference_url="test_url",
        story_title="Eren in the Magical Forest"
    )
    
    print("\n--- COMPOSING PAGE PROMPT ---")
    composer = PromptComposer(ctx)
    scene_description = "Eren is running through a glowing magical forest, looking amazed."
    result = composer.compose_page(scene_description, 1)
    
    print("Page Prompt (Base):")
    print(result.prompt)
    print("\nPage Negative Prompt:")
    print(result.negative_prompt)

    print("\n--- GEMINI CONSISTENT IMAGE GENERATION PAYLOAD SIMULATION ---")
    # Emulate the final text instruction generation in GeminiConsistentImageService
    _gemini_svc = GeminiConsistentImageService(api_key="mock")
    # Need to access private/internal variables to show what is sent to the model?
    # We can just run a mocked version of the final instruction logic
    
    _hair_note = ""
    _clean_char_desc = description.split("|")[0].strip().lower()
    if any(kw in _clean_char_desc for kw in ("curly", "curl", "coil", "kinky", "ringlet")):
        _hair_note = "HAIR: The child has CURLY hair — draw spiral curls, NOT straight, NOT wavy. "
    elif any(kw in _clean_char_desc for kw in ("wavy", "wave")):
        _hair_note = "HAIR: The child has WAVY hair — draw visible waves, NOT straight. "

    _age_note = ""
    if 6 <= 7:
        _age_note = (
            "AGE: Only 6 years old — draw a VERY YOUNG child face: "
            "round chubby cheeks, soft small nose, baby-face proportions. NOT older than 6. "
        )

    _outfit_note = "OUTFIT: a red t-shirt and blue jeans. "
    _secondary_note = (
        "Other characters in the scene must look CLEARLY DIFFERENT from the main child — "
        "different age, different hair, different face. Adults must look visibly adult (taller, older face). "
    )

    base_instruction = (
        "Generate a full-bleed 4:3 landscape children's book illustration. "
        "Fill the entire frame edge-to-edge. "
        "Do NOT include any text, letters, words, logos, or watermarks. "
    )

    _gemini_style = ctx.style.style_block

    text_instruction = (
        base_instruction
        + f"TASK: Look at the attached photo. This is the main character. "
        f"Redraw this EXACT face and head as a {_gemini_style} children's book illustration. "
        f"CRITICAL FOR LIKENESS: You MUST perfectly copy the hair (length, parting, bangs), face shape, skin tone, and eye color from the photo. "
        + _hair_note
        + _age_note
        + f"STYLE: {_gemini_style}. "
        "2D painted illustration — NOT photorealistic, NOT 3D CGI, NOT Pixar 3D. "
        + "COMPOSITION: Wide angle shot. The child's FULL BODY (head to shoes) MUST be visible, "
        "occupying 20-30% of the frame. The detailed environment fills the rest. "
        "NO close-ups, NO cropped bodies, NO portraits. "
        + _outfit_note
        + "HEAD: The child's hair MUST BE UNCOVERED AND VISIBLE — NO headscarf, NO hijab, NO veil, NO hood. "
        "This applies even inside a mosque or religious site. "
        + _secondary_note
        + "NO text, words, letters, watermarks in the image. "
        + "SCENE: " + result.prompt
    )

    print("\n--- FINAL GEMINI PROMPT (text_instruction) ---")
    print(text_instruction)


if __name__ == "__main__":
    asyncio.run(main())
