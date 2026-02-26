import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def main():
    engine = create_async_engine('postgresql+asyncpg://postgres:BnmMsl2026ProdDB!@localhost:5433/benimmasalim')
    async with engine.begin() as conn:
        await conn.execute(text("UPDATE story_previews SET coloring_pdf_url = NULL WHERE id IN ('0f63841a-0cd9-4a55-9548-fc8a99adfb31', '7136ee83-4c2c-4c0d-ab3a-5641d8f68c63', 'eefa582c-ef96-4b43-b4b4-3c82f95cebb9')"))
        print('Updated database.')
    await engine.dispose()
asyncio.run(main())
