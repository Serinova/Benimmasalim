"""Test Turkish character rendering with Pillow."""
import sys
from PIL import Image, ImageDraw, ImageFont

# Ensure proper encoding
text = "Birdenbire, ta\u015flar\u0131n aras\u0131ndan par\u0131ldayan bir \u0131\u015f\u0131k huzmesi belirdi."
print(f"Test text: {text}")
print(f"Encoding check: {text.encode('utf-8')}")

fonts = [
    ("Schoolbell", "/usr/share/fonts/truetype/google/Schoolbell-Regular.ttf"),
    ("ComicNeue", "/usr/share/fonts/truetype/google/ComicNeue-Regular.ttf"),
    ("Nunito", "/usr/share/fonts/truetype/google/Nunito.ttf"),
    ("IndieFlower", "/usr/share/fonts/truetype/google/IndieFlower-Regular.ttf"),
]

for name, path in fonts:
    try:
        font = ImageFont.truetype(path, 30)
        img = Image.new("RGB", (900, 60), "white")
        draw = ImageDraw.Draw(img)
        draw.text((10, 10), text, fill="black", font=font)
        out = f"/tmp/test_{name}.png"
        img.save(out)
        
        # Check for missing glyphs by checking if character width is 0
        missing = []
        for ch in "\u015f\u011f\u0131\u00e7\u00f6\u00fc\u015e\u011e\u0130\u00c7\u00d6\u00dc":
            bbox = font.getbbox(ch)
            w = bbox[2] - bbox[0] if bbox else 0
            if w < 1:
                missing.append(ch)
        
        status = "OK" if not missing else f"MISSING: {''.join(missing)}"
        print(f"  {name}: {status}")
    except Exception as e:
        print(f"  {name}: ERROR {e}")

print("\nDone. Check /tmp/test_*.png files.")
