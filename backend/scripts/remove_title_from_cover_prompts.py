"""
Kapak prompt'larından başlık talimatlarını kaldır.

AI artık kapak resmine metin yazmayacak — başlık page_composer tarafından
WordArt tarzında eklenir. Bu script:
  1. Tüm senaryo cover_prompt_template'lerinden "Book title..." satırını kaldırır
  2. Her prompt'a "no text in image" talimatı ekler

Çalıştırma:
    cd backend
    python -m scripts.remove_title_from_cover_prompts
"""

import asyncio
import re

from sqlalchemy import select
from app.core.database import async_session_factory
from app.models.scenario import Scenario


# Kaldırılacak / değiştirilecek kalıplar
_TITLE_PATTERNS = [
    # "Book title at top in large bold golden embossed letters: "{story_title}"."
    r'Book title at top[^.]*\.\s*',
    # "Book title ... "{book_title}" ..."
    r'[^.]*book.title[^.]*"?\{(?:book_title|story_title)\}"?[^.]*\.\s*',
    # "Title text ..." tarzı satırlar
    r'(?:TITLE|BOOK TITLE)[:\s]+[^\n]*\n?',
    # "{book_title}" veya "{story_title}" placeholder'ları (tek başına)
    r'\s*"?\{book_title\}"?\s*',
    r'\s*"?\{story_title\}"?\s*',
]

# "No text" talimatı eklenecek (zaten yoksa)
_NO_TEXT_INSTRUCTION = "No text, no letters, no words in the image."


async def main() -> None:
    async with async_session_factory() as session:
        result = await session.execute(select(Scenario))
        scenarios = result.scalars().all()

        updated = 0
        for scenario in scenarios:
            cover = scenario.cover_prompt_template
            if not cover:
                continue

            original = cover

            # Title kalıplarını temizle
            for pattern in _TITLE_PATTERNS:
                cover = re.sub(pattern, "", cover, flags=re.IGNORECASE)

            # Çift boşlukları temizle
            cover = re.sub(r'\n{3,}', '\n\n', cover)
            cover = re.sub(r'  +', ' ', cover)
            cover = cover.strip()

            # "no text" talimatı ekle (yoksa)
            if "no text" not in cover.lower() and "no letters" not in cover.lower():
                cover += f"\n\n{_NO_TEXT_INSTRUCTION}"

            if cover != original:
                scenario.cover_prompt_template = cover
                updated += 1
                print(f"  [UPDATED] {scenario.name}: {len(original)} → {len(cover)} chars")
            else:
                print(f"  [OK] {scenario.name}: no changes needed")

        if updated > 0:
            await session.commit()
            print(f"\n{updated} senaryo güncellendi.")
        else:
            print("\nHiçbir senaryo güncellenmedi (zaten temiz).")


if __name__ == "__main__":
    asyncio.run(main())
