"""Check which fonts ACTUALLY render Turkish glyphs (using mask_size, not bbox)."""
import os
from PIL import ImageFont

fonts_dir = "/usr/share/fonts/truetype/google"
# These are the problematic chars
critical_chars = "\u015f\u011f\u015e\u011e\u0130"  # ş ğ Ş Ğ İ
all_turkish = "\u015f\u011f\u0131\u00e7\u00f6\u00fc\u015e\u011e\u0130\u00c7\u00d6\u00dc"

print("Font Turkish Glyph Support (mask-based check)")
print("=" * 60)

for f in sorted(os.listdir(fonts_dir)):
    path = os.path.join(fonts_dir, f)
    try:
        font = ImageFont.truetype(path, 30)
        missing = []
        for ch in all_turkish:
            mask = font.getmask(ch)
            if mask.size[0] == 0 or mask.size[1] == 0:
                missing.append(ch)
        
        critical_missing = [ch for ch in critical_chars if ch in missing]
        
        if not missing:
            print(f"  \u2705 {f}")
        elif critical_missing:
            print(f"  \u274c {f}  missing: {''.join(missing)}")
        else:
            print(f"  \u26a0\ufe0f  {f}  partial: {''.join(missing)}")
    except Exception as e:
        print(f"  ERR {f}  {e}")
