import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import text

async def get_templates():
    engine = create_async_engine("postgresql+asyncpg://postgres:123456@host.docker.internal:5432/benimmasalim")
    SessionLocal = async_sessionmaker(bind=engine)
    async with SessionLocal() as session:
        res = await session.execute(text("SELECT id, name, cover_prompt_template, page_prompt_template FROM scenarios WHERE name LIKE '%Efes%'"))
        for row in res.fetchall():
            print("ID:", row[0])
            print("NAME:", row[1])
            print("COVER TEMPLATE:", row[2])
            print("PAGE TEMPLATE:", row[3])

asyncio.run(get_templates())