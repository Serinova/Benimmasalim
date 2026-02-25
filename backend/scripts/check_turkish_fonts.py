"""Check which installed fonts support Turkish characters."""
import os
from PIL import ImageFont

fonts_dir = "/usr/share/fonts/truetype/google"
test_chars = "şğıçöüŞĞİÇÖÜ"

for f in sorted(os.listdir(fonts_dir)):
    path = os.path.join(fonts_dir, f)
    try:
        font = ImageFont.truetype(path, 20)
        missing = []
        for ch in test_chars:
            bbox = font.getbbox(ch)
            if not bbox or (bbox[2] - bbox[0]) < 1:
                missing.append(ch)
        missing_str = "".join(missing)
        if not missing:
            print(f"  OK  {f}")
        else:
            print(f"  BAD {f}  missing: {missing_str}")
    except Exception as e:
        print(f"  ERR {f}  {e}")
