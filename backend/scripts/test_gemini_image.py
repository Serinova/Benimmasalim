#!/usr/bin/env python3
"""
Gemini Image Generator Test Script.

Bu script, modüler image generator yapısını test eder.

Kullanım:
    cd backend
    python scripts/test_gemini_image.py
    
    # Belirli provider ile test:
    python scripts/test_gemini_image.py --provider gemini
    python scripts/test_gemini_image.py --provider gemini_flash

Çıktı:
    - generated_images/ klasörüne PNG dosyaları kaydedilir
    - Console'da üretim süreleri ve detaylar gösterilir
"""

import argparse
import asyncio
import os
import sys
import time
from pathlib import Path

# Backend'i import edebilmek için path'e ekle
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv()

from app.services.ai.image_generator import (
    BaseImageGenerator,
    ImageProvider,
    ImageSize,
    get_image_generator,
)

# Test prompt'ları
TEST_PROMPTS = [
    {
        "name": "cover",
        "prompt": "A brave little boy named Uras exploring a magical forest with glowing mushrooms and friendly forest creatures",
        "style": "pixar style, 3D animation, warm lighting",
        "aspect": ImageSize.PORTRAIT,
    },
    {
        "name": "page1",
        "prompt": "A cute child finding a treasure chest in a colorful underwater world with friendly fish",
        "style": "watercolor illustration, soft colors, dreamy atmosphere",
        "aspect": ImageSize.SQUARE,
    },
    {
        "name": "page2",
        "prompt": "A happy child flying on a friendly dragon over a rainbow landscape with floating islands",
        "style": "disney animation style, vibrant colors, magical sparkles",
        "aspect": ImageSize.LANDSCAPE,
    },
]


async def test_single_generation(
    generator: BaseImageGenerator,
    prompt: str,
    style: str,
    aspect: ImageSize,
    output_path: Path,
) -> dict:
    """Tek bir görsel üret ve kaydet."""

    print(f"\n{'='*60}")
    print(f"Provider: {generator.provider_name}")
    print(f"Prompt: {prompt[:80]}...")
    print(f"Style: {style}")
    print(f"Aspect: {aspect.value}")
    print(f"{'='*60}")

    start_time = time.time()

    try:
        image_bytes = await generator.generate_with_aspect_ratio(
            prompt=prompt,
            aspect_ratio=aspect,
            style_prompt=style,
        )

        elapsed = time.time() - start_time

        # Kaydet
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(image_bytes)

        file_size_kb = len(image_bytes) / 1024

        print("\n✅ BAŞARILI!")
        print(f"   Süre: {elapsed:.2f} saniye")
        print(f"   Boyut: {file_size_kb:.1f} KB")
        print(f"   Dosya: {output_path}")

        return {
            "success": True,
            "elapsed": elapsed,
            "size_kb": file_size_kb,
            "path": str(output_path),
        }

    except Exception as e:
        elapsed = time.time() - start_time
        print("\n❌ HATA!")
        print(f"   Süre: {elapsed:.2f} saniye")
        print(f"   Hata: {str(e)}")

        return {
            "success": False,
            "elapsed": elapsed,
            "error": str(e),
        }


async def run_tests(provider: ImageProvider):
    """Tüm test prompt'larını çalıştır."""

    print("\n" + "="*70)
    print("   GEMINI IMAGE GENERATOR TEST")
    print(f"   Provider: {provider.value}")
    print("="*70)

    # Generator oluştur
    try:
        generator = get_image_generator(provider)
        print(f"\n✓ Generator oluşturuldu: {generator.provider_name}")
    except Exception as e:
        print(f"\n✗ Generator oluşturulamadı: {e}")
        return

    # Çıktı klasörü
    output_dir = Path(__file__).parent.parent / "generated_images" / provider.value
    output_dir.mkdir(parents=True, exist_ok=True)

    # Testleri çalıştır
    results = []
    for i, test in enumerate(TEST_PROMPTS):
        output_path = output_dir / f"{test['name']}_{int(time.time())}.png"

        result = await test_single_generation(
            generator=generator,
            prompt=test["prompt"],
            style=test["style"],
            aspect=test["aspect"],
            output_path=output_path,
        )
        result["name"] = test["name"]
        results.append(result)

    # Özet
    print("\n" + "="*70)
    print("   ÖZET")
    print("="*70)

    successful = [r for r in results if r.get("success")]
    failed = [r for r in results if not r.get("success")]

    print(f"\n✓ Başarılı: {len(successful)}/{len(results)}")
    print(f"✗ Başarısız: {len(failed)}/{len(results)}")

    if successful:
        avg_time = sum(r["elapsed"] for r in successful) / len(successful)
        total_size = sum(r.get("size_kb", 0) for r in successful)
        print(f"\n⏱  Ortalama süre: {avg_time:.2f} saniye")
        print(f"📦 Toplam boyut: {total_size:.1f} KB")

        print(f"\n📁 Görseller kaydedildi: {output_dir}")

    if failed:
        print("\n❌ Hatalar:")
        for r in failed:
            print(f"   - {r['name']}: {r.get('error', 'Bilinmeyen hata')}")

    return results


async def quick_test(provider: ImageProvider):
    """Hızlı tek görsel testi."""

    print("\n🚀 Hızlı Test Başlatılıyor...")

    generator = get_image_generator(provider)

    output_dir = Path(__file__).parent.parent / "generated_images"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"quick_test_{provider.value}_{int(time.time())}.png"

    result = await test_single_generation(
        generator=generator,
        prompt="A cute cartoon child riding a friendly unicorn through a rainbow sky",
        style="pixar style, colorful, magical",
        aspect=ImageSize.SQUARE,
        output_path=output_path,
    )

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Gemini Image Generator Test Script"
    )
    parser.add_argument(
        "--provider",
        type=str,
        choices=["gemini", "gemini_flash", "fal"],
        default="gemini_flash",
        help="Görsel üretim servisi (varsayılan: gemini_flash)",
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Sadece tek bir hızlı test yap",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Tüm test senaryolarını çalıştır",
    )

    args = parser.parse_args()

    # Provider seç
    provider_map = {
        "gemini": ImageProvider.GEMINI,
        "gemini_flash": ImageProvider.GEMINI_FLASH,
        "fal": ImageProvider.FAL,
    }
    provider = provider_map[args.provider]

    # Environment check
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ HATA: GEMINI_API_KEY environment variable'ı bulunamadı!")
        print("   .env dosyasını kontrol edin veya:")
        print("   export GEMINI_API_KEY='your-api-key'")
        sys.exit(1)

    print(f"✓ API Key bulundu: {api_key[:20]}...")

    # Test seç ve çalıştır
    if args.quick:
        asyncio.run(quick_test(provider))
    elif args.full:
        asyncio.run(run_tests(provider))
    else:
        # Varsayılan: quick test
        asyncio.run(quick_test(provider))


if __name__ == "__main__":
    main()
