"""Test story text overlay: scrim + stroke + drop shadow + padding.
Run from backend: python scripts/test_story_text_overlay.py
Saves composed pages to scripts/output/story_overlay_*.png for visual check.
On Windows, use UTF-8 for logs: $env:PYTHONIOENCODING='utf-8'; python scripts/test_story_text_overlay.py
"""
import base64
import io
import os
import sys

# Add backend to path when run from repo root or backend
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image

from app.services.page_composer import PageComposer

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Caption-style config: white text, dark stroke, scrim (drawn by compose_page for inner)
INNER_TEMPLATE = {
    "page_type": "inner",
    "text_enabled": True,
    "text_position": "bottom",
    "text_x_percent": 3.0,
    "text_y_percent": 72.0,
    "text_width_percent": 94.0,
    "text_height_percent": 25.0,
    "text_vertical_align": "bottom",
    "font_family": "Nunito",
    "font_size_pt": 18,
    "font_color": "#FFFFFF",
    "text_align": "center",
    "line_height": 1.35,
    "text_stroke_enabled": True,
    "text_stroke_color": "#000000",
    "text_stroke_width": 1.2,
    "background_color": "#FFFFFF",
}

SAMPLES = [
    ("açık arka plan", (240, 248, 255), "Güneşli bir günde ormanda yürüyordum. Birdenbire önümde sihirli bir kapı belirdi."),
    ("detaylı sahne", (255, 250, 240), "Taşların arasından parıldayan bir ışık hüzmesi belirdi. Enes merakla ışığa doğru ilerledi."),
    ("çok satır", (230, 240, 255), "İlk satır burada. İkinci satır da geliyor. Üçüncü satır ile metin uzayacak ve scrim üzerinde okunurluk test edilecek."),
]


def make_dummy_image(width: int, height: int, rgb: tuple[int, int, int]) -> str:
    img = Image.new("RGB", (width, height), rgb)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def main() -> None:
    composer = PageComposer()
    for name, rgb, text in SAMPLES:
        b64 = make_dummy_image(1200, 848, rgb)
        result = composer.compose_page(
            image_base64=b64,
            text=text,
            template_config=INNER_TEMPLATE,
            page_width_mm=297,
            page_height_mm=210,
            dpi=150,
        )
        if "," in result:
            data = base64.b64decode(result.split(",")[1])
        else:
            data = base64.b64decode(result)
        out_path = os.path.join(OUTPUT_DIR, f"story_overlay_{name.replace(' ', '_')}.png")
        with open(out_path, "wb") as f:
            f.write(data)
        print(f"Saved: {out_path}")
    print(f"Done. Check {OUTPUT_DIR} for composed pages (scrim + stroke + drop shadow).")


if __name__ == "__main__":
    main()
