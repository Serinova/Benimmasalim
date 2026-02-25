import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import text

async def fetch_templates():
    engine = create_async_engine('postgresql+asyncpg://postgres:123456@host.docker.internal:5432/benimmasalim')
    SessionLocal = async_sessionmaker(bind=engine)
    async with SessionLocal() as session:
        res = await session.execute(text("SELECT key, content_en FROM prompt_templates WHERE key IN ('COVER_TEMPLATE', 'INNER_TEMPLATE')"))
        for row in res.fetchall():
            print(f"{row[0]} : {row[1]}")

if __name__ == "__main__":
    asyncio.run(fetch_templates())