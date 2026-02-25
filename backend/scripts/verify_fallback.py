"""Verify Turkish font fallback mechanism."""
import sys
sys.path.insert(0, "/app")

from app.services.page_composer import (
    _font_supports_turkish,
    _resolve_font_path,
    _text_needs_turkish,
)

print("Font Turkish Support Check:")
for name in ["Schoolbell", "IndieFlower", "ComicNeue", "Nunito", "Lobster", "Chewy", "Gaegu"]:
    path = _resolve_font_path(name)
    ok = _font_supports_turkish(path)
    status = "OK" if ok else "FAIL"
    print(f"  {name}: {status} ({path})")

print("\nText needs Turkish check:")
texts = [
    ("Hello world", False),
    ("Birdenbire ta\u015flar\u0131n", True),
    ("Enes merakla \u0131\u015f\u0131\u011fa", True),
]
for txt, expected in texts:
    result = _text_needs_turkish(txt)
    match = "OK" if result == expected else "WRONG"
    print(f"  '{txt[:30]}': needs_turkish={result} (expected={expected}) [{match}]")
