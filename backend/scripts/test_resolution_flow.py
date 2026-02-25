"""Test script to verify the resolution calculation flow.

Tests the complete flow:
1. PageTemplate → mm dimensions
2. mm_to_px() → target pixel dimensions
3. calculate_generation_params() → AI generation + upscale strategy
4. resize_to_target() → final exact dimensions

Run with: python -m scripts.test_resolution_flow
"""

import sys

sys.path.insert(0, ".")

from app.utils.resolution_calc import (
    DEFAULT_AI_MAX_SIZE,
    DEFAULT_DPI,
    calculate_generation_params_from_mm,
    calculate_target_resolution_from_mm,
    mm_to_px,
)


def test_mm_to_px():
    """Test mm to pixel conversion."""
    print("\n=== Test: mm_to_px ===")

    # Test cases: (mm, bleed_mm, expected_px)
    test_cases = [
        (210, 0, 2480),    # A4 width without bleed
        (210, 3, 2551),    # A4 width with 3mm bleed (each side)
        (297, 0, 3508),    # A4 height without bleed
        (297, 3, 3579),    # A4 height with 3mm bleed
    ]

    for mm_val, bleed, expected in test_cases:
        result = mm_to_px(mm_val, bleed_mm=bleed, dpi=300)
        status = "OK" if result == expected else f"FAIL (got {result})"
        print(f"  {mm_val}mm + {bleed}mm bleed = {expected}px ... {status}")

    print()


def test_square_book():
    """Test Kare Masal Kitabı (210x210mm)."""
    print("\n=== Test: Kare Masal Kitabı (210x210mm + 3mm bleed) ===")

    width_mm = 210.0
    height_mm = 210.0
    bleed_mm = 3.0

    # Step 1: Calculate target resolution
    target_w, target_h = calculate_target_resolution_from_mm(
        width_mm, height_mm, bleed_mm
    )
    print(f"  1. Hedef cozunurluk: {target_w}x{target_h}px")

    # Step 2: Calculate generation params
    params = calculate_generation_params_from_mm(width_mm, height_mm, bleed_mm)

    print(f"  2. AI uretim boyutu: {params['generation_width']}x{params['generation_height']}px")
    print(f"     Aspect ratio: {params['aspect_ratio']}")
    print(f"     Upscale gerekli mi: {params['needs_upscale']}")
    print(f"     Upscale faktörü: {params['upscale_factor']}x")

    # Step 3: Simulate upscale
    upscaled_w = params['generation_width'] * params['upscale_factor']
    upscaled_h = params['generation_height'] * params['upscale_factor']
    print(f"  3. Upscale sonrasi: {upscaled_w}x{upscaled_h}px")

    # Step 4: Final resize
    print(f"  4. Final resize: {params['target_width']}x{params['target_height']}px")

    # Verify
    assert target_w == params['target_width'], "Target width mismatch!"
    assert target_h == params['target_height'], "Target height mismatch!"
    assert upscaled_w >= params['target_width'], f"Upscaled too small: {upscaled_w} < {params['target_width']}"
    assert upscaled_h >= params['target_height'], f"Upscaled too small: {upscaled_h} < {params['target_height']}"

    print("  [OK] Tum boyutlar dogru!")


def test_a4_portrait():
    """Test A4 Portrait (210x297mm)."""
    print("\n=== Test: A4 Portrait (210x297mm + 3mm bleed) ===")

    width_mm = 210.0
    height_mm = 297.0
    bleed_mm = 3.0

    params = calculate_generation_params_from_mm(width_mm, height_mm, bleed_mm)

    print(f"  Hedef: {params['target_width']}x{params['target_height']}px")
    print(f"  AI üretim: {params['generation_width']}x{params['generation_height']}px")
    print(f"  Aspect ratio: {params['aspect_ratio']}")
    print(f"  Upscale: {params['upscale_factor']}x")

    # Verify aspect ratio is preserved
    target_aspect = params['target_width'] / params['target_height']
    gen_aspect = params['generation_width'] / params['generation_height']
    aspect_diff = abs(target_aspect - gen_aspect)

    print(f"  Aspect ratio farki: {aspect_diff:.4f}")
    assert aspect_diff < 0.05, f"Aspect ratio too different: {aspect_diff}"

    print("  [OK] Portrait boyutlar dogru!")


def test_landscape_wide():
    """Test Landscape Wide (297x148mm - 2:1 ratio)."""
    print("\n=== Test: Landscape Wide (297x148mm + 3mm bleed) ===")

    width_mm = 297.0
    height_mm = 148.0
    bleed_mm = 3.0

    params = calculate_generation_params_from_mm(width_mm, height_mm, bleed_mm)

    print(f"  Hedef: {params['target_width']}x{params['target_height']}px")
    print(f"  AI üretim: {params['generation_width']}x{params['generation_height']}px")
    print(f"  Aspect ratio: {params['aspect_ratio']}")
    print(f"  Upscale: {params['upscale_factor']}x")

    upscaled_w = params['generation_width'] * params['upscale_factor']
    upscaled_h = params['generation_height'] * params['upscale_factor']

    assert upscaled_w >= params['target_width'], "Upscaled width too small"
    assert upscaled_h >= params['target_height'], "Upscaled height too small"

    print("  [OK] Landscape boyutlar dogru!")


def print_summary():
    """Print a summary of the resolution system."""
    print("\n" + "=" * 60)
    print("OZET: Dinamik Cozunurluk Hesaplama Sistemi")
    print("=" * 60)

    print(f"""
Formul: (mm + 2 x bleed_mm) / 25.4 x {DEFAULT_DPI} DPI

Akis:
1. PageTemplate'ten mm boyutlari alinir
2. mm_to_px() ile hedef piksel hesaplanir
3. AI icin {DEFAULT_AI_MAX_SIZE}px limit dahilinde uretim boyutu belirlenir
4. Real-ESRGAN ile 2x veya 4x upscale yapilir
5. LANCZOS ile tam hedef boyuta resize edilir

Ornek: Kare 210x210mm + 3mm bleed
  -> Hedef: 2551x2551px (baski kalitesi)
  -> AI uretir: 1024x1024px
  -> Upscale 4x: 4096x4096px
  -> Final resize: 2551x2551px
""")


if __name__ == "__main__":
    print("=" * 60)
    print("Dinamik Cozunurluk Hesaplama Test Script'i")
    print("=" * 60)

    test_mm_to_px()
    test_square_book()
    test_a4_portrait()
    test_landscape_wide()
    print_summary()

    print("\n[OK] Tum testler basarili!")
