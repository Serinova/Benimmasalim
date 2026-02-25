"""Test Turkish character rendering in page_composer."""
import asyncio
import base64
import io
import sys
sys.path.insert(0, "/app")

from PIL import Image, ImageDraw, ImageFont

# Simulate page_composer text drawing
FONT_PATH = "/usr/share/fonts/truetype/google/Schoolbell-Regular.ttf"
TURKISH_TEXT = (
    "Birdenbire, ta\u015flar\u0131n aras\u0131ndan par\u0131ldayan "
    "bir \u0131\u015f\u0131k h\u00fczmesi belirdi. Enes merakla "
    "\u0131\u015f\u0131\u011fa do\u011fru ilerledi."
)

print(f"Test text: {TURKISH_TEXT}")
print(f"Contains \u015f: {chr(0x015f) in TURKISH_TEXT}")
print(f"Contains \u011f: {chr(0x011f) in TURKISH_TEXT}")
print(f"Contains \u0131: {chr(0x0131) in TURKISH_TEXT}")

# Load font
font = ImageFont.truetype(FONT_PATH, 40)

# Create test image
img = Image.new("RGB", (1200, 200), "white")
draw = ImageDraw.Draw(img)

# Draw text
draw.text((20, 50), TURKISH_TEXT, fill="black", font=font)

# Save
img.save("/tmp/compose_turkish_test.png")

# Verify: check if Turkish chars have non-zero width
chars_to_check = {
    "\u015f": "s-cedilla",
    "\u011f": "g-breve",
    "\u0131": "dotless-i",
    "\u00e7": "c-cedilla",
    "\u00f6": "o-umlaut",
    "\u00fc": "u-umlaut",
    "\u015e": "S-cedilla",
    "\u011e": "G-breve",
    "\u0130": "I-dot",
}

print("\nGlyph width check:")
for ch, name in chars_to_check.items():
    bbox = font.getbbox(ch)
    w = bbox[2] - bbox[0] if bbox else 0
    h = bbox[3] - bbox[1] if bbox else 0
    mask = font.getmask(ch)
    mask_size = mask.size if mask else (0, 0)
    print(f"  {name} ({repr(ch)}): bbox_w={w} bbox_h={h} mask_size={mask_size}")

# Now test with actual page_composer
print("\n--- Testing via PageComposer ---")
try:
    from app.services.page_composer import PageComposer

    composer = PageComposer()
    
    # Create a dummy base64 image
    test_img = Image.new("RGB", (1024, 724), (200, 220, 240))
    buf = io.BytesIO()
    test_img.save(buf, format="PNG")
    test_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    
    template_config = {
        "text_position": "bottom",
        "text_x_percent": 5.0,
        "text_y_percent": 72.0,
        "text_width_percent": 90.0,
        "text_height_percent": 25.0,
        "font_family": "Schoolbell",
        "font_size_pt": 20,
        "font_color": "#000000",
        "text_align": "center",
        "background_color": "#FFFFFF",
        "text_enabled": True,
        "text_stroke_enabled": False,
        "text_bg_enabled": True,
        "text_bg_color": "#000000",
        "text_bg_opacity": 180,
        "text_bg_shape": "soft_vignette",
        "text_bg_blur": 30,
        "page_type": "inner",
    }

    result_b64 = composer.compose_page(
        image_base64=test_b64,
        text=TURKISH_TEXT,
        template_config=template_config,
        page_width_mm=297,
        page_height_mm=210,
        dpi=150,  # Lower DPI for faster test
    )

    # Decode result
    if "," in result_b64:
        img_data = base64.b64decode(result_b64.split(",")[1])
    else:
        img_data = base64.b64decode(result_b64)
    
    result_img = Image.open(io.BytesIO(img_data))
    result_img.save("/tmp/compose_result.png")
    print(f"Composed image saved: {result_img.size}")
    print("Check /tmp/compose_result.png for Turkish text rendering")
    
except Exception as e:
    print(f"PageComposer test failed: {e}")
    import traceback
    traceback.print_exc()
