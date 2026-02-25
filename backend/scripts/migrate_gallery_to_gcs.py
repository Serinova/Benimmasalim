"""One-time script: migrate base64 gallery images in scenarios to GCS URLs.

Usage (inside the backend container):
    python -m scripts.migrate_gallery_to_gcs
"""

import asyncio
import sys
from pathlib import Path

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import structlog

from app.config import settings  # noqa: E402
from app.core.database import async_session_factory  # noqa: E402
from app.models.scenario import Scenario  # noqa: E402
from app.services.storage_service import StorageService  # noqa: E402
from sqlalchemy import select  # noqa: E402

logger = structlog.get_logger()
storage = StorageService()

_URL_PREFIXES = ("http://", "https://", "/")


def _is_base64(s: str) -> bool:
    return s.startswith("data:") or (len(s) > 500 and not s.startswith(_URL_PREFIXES))


def _upload_gallery_images(images: list[str], scenario_name: str = "") -> list[str]:
    if not images:
        return []
    result: list[str] = []
    for idx, img in enumerate(images):
        if not img:
            continue
        if _is_base64(img):
            try:
                url = storage.upload_base64_image(base64_data=img, folder="scenarios")
                if url:
                    result.append(url)
                    logger.info("Uploaded gallery image", scenario=scenario_name, idx=idx)
                    continue
            except Exception as e:
                logger.error("Gallery upload failed", scenario=scenario_name, idx=idx, error=str(e))
                continue
        elif img.startswith(_URL_PREFIXES):
            result.append(img)
    return result


async def main() -> None:
    print(f"Connecting to DB: {str(settings.database_url)[:50]}...")

    async with async_session_factory() as db:
        result = await db.execute(select(Scenario))
        scenarios = result.scalars().all()
        print(f"Found {len(scenarios)} scenarios")

        migrated = 0
        total_images = 0

        for scenario in scenarios:
            changed = False

            if scenario.thumbnail_url and _is_base64(scenario.thumbnail_url):
                try:
                    url = storage.upload_base64_image(
                        base64_data=scenario.thumbnail_url, folder="scenarios"
                    )
                    if url:
                        scenario.thumbnail_url = url
                        changed = True
                        print(f"  Thumbnail migrated: {scenario.name}")
                except Exception as e:
                    print(f"  Thumbnail migration failed: {scenario.name} - {e}")

            raw = scenario.gallery_images or []
            has_base64 = any(_is_base64(img) for img in raw if isinstance(img, str))

            if has_base64:
                new_gallery = _upload_gallery_images(raw, scenario.name)
                scenario.gallery_images = new_gallery
                total_images += len(new_gallery)
                changed = True
                print(f"  Gallery migrated: {scenario.name} ({len(raw)} -> {len(new_gallery)})")

            if changed:
                migrated += 1

        if migrated:
            await db.commit()
            print(f"\nDone! {migrated} scenarios migrated, {total_images} images uploaded to GCS")
        else:
            print("\nNo base64 images found — nothing to migrate")


if __name__ == "__main__":
    asyncio.run(main())
