#!/usr/bin/env python3
"""
One-time migration script: move any base64 image data stored in
story_previews.page_images JSONB to GCS and replace with URLs.

Usage (inside backend container):
    python -m scripts.migrate_base64_to_gcs [--dry-run]

How it works:
  1. Scans every row in story_previews where page_images IS NOT NULL.
  2. For each key/value pair, checks if the value looks like a URL
     (starts with "http") — those are already fine.
  3. If the value is NOT a URL, it is assumed to be raw base64 image data.
     The script uploads it to GCS and replaces the JSONB value with the URL.
  4. Commits in batches to avoid long-running transactions.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

# Ensure project root is on sys.path
_here = Path(__file__).resolve().parent
sys.path.insert(0, str(_here.parent))

import structlog
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.database import async_session_factory
from app.services.storage_service import storage_service

logger = structlog.get_logger()

BATCH_SIZE = 50


def _is_url(value: str) -> bool:
    """Check if a value looks like a URL rather than base64 data."""
    if not isinstance(value, str):
        return False
    return value.startswith("http://") or value.startswith("https://")


async def migrate(dry_run: bool = False) -> None:
    """Scan story_previews.page_images and migrate base64 values to GCS."""

    total_rows = 0
    total_migrated = 0
    total_b64_fields = 0

    async with async_session_factory() as db:
        # Count first
        count_result = await db.execute(
            text("SELECT count(*) FROM story_previews WHERE page_images IS NOT NULL")
        )
        total_rows = count_result.scalar_one()
        logger.info("Migration scan starting", total_rows=total_rows, dry_run=dry_run)

        if total_rows == 0:
            logger.info("No rows with page_images found — nothing to migrate.")
            return

        # Process in batches
        offset = 0
        while offset < total_rows:
            result = await db.execute(
                text(
                    "SELECT id, page_images FROM story_previews "
                    "WHERE page_images IS NOT NULL "
                    "ORDER BY id "
                    f"LIMIT {BATCH_SIZE} OFFSET {offset}"
                )
            )
            rows = result.fetchall()
            if not rows:
                break

            for row in rows:
                row_id = row[0]
                page_images: dict = row[1]

                if not isinstance(page_images, dict):
                    continue

                updated = False
                new_images = dict(page_images)

                for key, value in page_images.items():
                    if not isinstance(value, str):
                        continue
                    if _is_url(value):
                        continue

                    # This is base64 data
                    total_b64_fields += 1
                    b64_size_kb = len(value) / 1024
                    logger.info(
                        "Found base64 in DB",
                        row_id=str(row_id),
                        page_key=key,
                        size_kb=round(b64_size_kb, 1),
                        dry_run=dry_run,
                    )

                    if not dry_run:
                        try:
                            url = storage_service.upload_base64_image(
                                base64_data=value,
                                folder=f"migrated/{row_id}",
                                filename=f"page_{key}.png",
                            )
                            new_images[key] = url
                            updated = True
                            logger.info(
                                "Migrated to GCS",
                                row_id=str(row_id),
                                page_key=key,
                                url=url[:80],
                            )
                        except Exception as e:
                            logger.error(
                                "Migration upload failed — skipping",
                                row_id=str(row_id),
                                page_key=key,
                                error=str(e),
                            )

                if updated:
                    await db.execute(
                        text(
                            "UPDATE story_previews SET page_images = :data WHERE id = :id"
                        ),
                        {"data": new_images, "id": row_id},
                    )
                    total_migrated += 1

            if not dry_run:
                await db.commit()

            offset += BATCH_SIZE
            logger.info(
                "Migration progress",
                processed=min(offset, total_rows),
                total=total_rows,
                migrated_rows=total_migrated,
                base64_fields_found=total_b64_fields,
            )

    logger.info(
        "Migration complete",
        total_rows_scanned=total_rows,
        rows_with_base64=total_migrated,
        total_base64_fields=total_b64_fields,
        dry_run=dry_run,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate base64 images in DB to GCS")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only scan and report — don't upload or modify DB",
    )
    args = parser.parse_args()
    asyncio.run(migrate(dry_run=args.dry_run))


if __name__ == "__main__":
    main()
