"""
Backfill: Strip style tokens from existing story_previews.story_pages[].visual_prompt.

Run after deploying style-independence (scene-only prompts). Keeps generation_manifest_json
and prompt_debug_json unchanged. Updates only the visual_prompt text in story_pages.

Usage:
    cd backend && python -m scripts.backfill_visual_prompt_strip_style [--dry-run]
"""

import argparse
import asyncio
import re
import sys

# Add project root
sys.path.insert(0, "")

# Style token patterns to strip from stored visual_prompt (scene-only contract)
STYLE_STRIP_PATTERNS = [
    r"\s*Children's book cover illustration\.?",
    r"\s*Children's book illustration\.?",
    r"\s*children's book cover illustration\.?",
    r"\s*children's book illustration\.?",
    r"\s*Book cover illustration,?\s*title space at top\.?",
    r"\s*,\s*warm colors,?\s*text space at bottom\.?",
    r"\s*\.\s*Pixar[^.]*\.?",
    r"\s*\.\s*Studio Ghibli[^.]*\.?",
    r"\s*\.\s*watercolor[^.]*\.?",
    r"\s*\.\s*2D children's book[^.]*\.?",
    r"\s*\.\s*3D animated[^.]*\.?",
    r"\s*,\s*soft colors\.?",
    r"\s*,\s*pixar style[^.]*\.?",
    r"\s*,\s*ghibli[^.]*\.?",
    r"\s*,\s*magical atmosphere\.?",
]
STYLE_STRIP_RE = re.compile("|".join(f"({p})" for p in STYLE_STRIP_PATTERNS), re.IGNORECASE)


def strip_style_tokens_from_prompt(text: str) -> str:
    """Remove style token phrases; keep scene + composition."""
    if not text or not text.strip():
        return text
    s = STYLE_STRIP_RE.sub(" ", text)
    s = re.sub(r"\s+", " ", s).strip().strip(".,")
    return s


async def main(dry_run: bool) -> None:
    from sqlalchemy import select, update
    from app.core.database import async_session_factory
    from app.models.story_preview import StoryPreview

    session_factory = async_session_factory
    updated_count = 0
    preview_count = 0

    async with session_factory() as db:
        result = await db.execute(select(StoryPreview).where(StoryPreview.story_pages.isnot(None)))
        previews = result.scalars().all()

        for preview in previews:
            pages = preview.story_pages
            if not isinstance(pages, list):
                continue
            preview_count += 1
            changed = False
            new_pages = []
            for p in pages:
                if not isinstance(p, dict):
                    new_pages.append(p)
                    continue
                vp = p.get("visual_prompt") or ""
                new_vp = strip_style_tokens_from_prompt(vp)
                if new_vp != vp:
                    changed = True
                new_pages.append({**p, "visual_prompt": new_vp})

            if changed and not dry_run:
                await db.execute(
                    update(StoryPreview).where(StoryPreview.id == preview.id).values(story_pages=new_pages)
                )
                updated_count += 1
            elif changed:
                updated_count += 1

        if not dry_run and updated_count > 0:
            await db.commit()

    print(f"Previews with story_pages: {preview_count}")
    print(f"Previews with style-stripped visual_prompt: {updated_count}")
    if dry_run:
        print("(dry run - no changes committed)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Do not commit changes")
    args = parser.parse_args()
    asyncio.run(main(dry_run=args.dry_run))
