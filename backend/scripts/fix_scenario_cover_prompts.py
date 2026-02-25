"""Senaryo cover prompt'larını temizle — kırık cümleler ve 'no text' talimatı ekle.

Çalıştırma:
    python -m scripts.fix_scenario_cover_prompts
"""
import asyncio
import re
from sqlalchemy import select
from app.core.database import async_session_factory
from app.models.scenario import Scenario


async def main():
    async with async_session_factory() as s:
        result = await s.execute(select(Scenario))
        updated = 0
        for sc in result.scalars().all():
            cover = sc.cover_prompt_template
            if not cover:
                continue

            original = cover

            # "illustration for." → "illustration." (bozuk cümle düzelt)
            cover = re.sub(r'illustration\s+for\s*\.', 'illustration.', cover, flags=re.IGNORECASE)

            # "Story." tek başına satır başında ise temizle
            cover = re.sub(r'^Story\.\s*', '', cover, flags=re.MULTILINE)

            # Kalan {book_title} ve {story_title} referanslarını temizle
            cover = re.sub(r'\s*"?\{(?:book_title|story_title)\}"?\s*', ' ', cover)

            # Çift boşlukları temizle
            cover = re.sub(r'  +', ' ', cover).strip()
            cover = re.sub(r'\n{3,}', '\n\n', cover)

            # "no text in image" talimatı ekle (sonunda, yoksa)
            if 'no text' not in cover.lower() and 'no letters' not in cover.lower():
                cover += '\n\nNo text, no letters, no words in the image.'

            # Mevcut "no text" talimatını güçlendir
            if 'no text' in cover.lower() and 'no letters' not in cover.lower():
                cover = re.sub(
                    r'no text in image',
                    'no text in image, no letters, no words',
                    cover,
                    flags=re.IGNORECASE,
                )

            if cover != original:
                sc.cover_prompt_template = cover
                updated += 1
                print(f"  [UPDATED] {sc.name}")
            else:
                print(f"  [OK] {sc.name}")

        if updated > 0:
            await s.commit()
        print(f"\n{updated} senaryo güncellendi.")


if __name__ == "__main__":
    asyncio.run(main())
