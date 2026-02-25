"""Fix all story_previews with story_title='Hikaye' by setting deterministic title."""
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

DB_URL = "postgresql+asyncpg://postgres:postgres@postgres:5432/benimmasalim"

FIXES = [
    ("282765a7-f50a-4c3b-8986-90bcd231f5cf", "Uras", "Yerebatan Sarnıcı"),
    ("b795e28f-0a89-4960-80f9-648b95d9c96d", "Uras", "Kapadokya macerası"),
    ("8391d8a3-3739-4b00-830c-82b05762f520", "Uras", "Yerebatan Sarnıcı"),
    ("7c459ee7-421e-4d7d-bd53-a91b37d33be8", "Uras", "Kapadokya macerası"),
]


async def main():
    from app.services.ai.gemini_service import _get_possessive_suffix, _normalize_title_turkish

    engine = create_async_engine(DB_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        for tid, child, scenario in FIXES:
            child_cap = child[0].upper() + child[1:].lower() if len(child) > 1 else child.upper()
            suffix = _get_possessive_suffix(child_cap)
            title = _normalize_title_turkish(f"{child_cap}'{suffix} {scenario}")
            await db.execute(
                text("UPDATE story_previews SET story_title = :title WHERE id = :id"),
                {"title": title, "id": tid},
            )
            print(f"  {tid}: {title}")
        await db.commit()
        print("Done!")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
