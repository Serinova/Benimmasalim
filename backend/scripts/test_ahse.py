import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import text
import json

engine = create_async_engine('postgresql+asyncpg://postgres:123456@localhost:5432/benimmasalim')
SessionLocal = async_sessionmaker(bind=engine)

async def get_preview():
    async with SessionLocal() as session:
        res = await session.execute(text("SELECT prompt_debug_json, clothing_description FROM story_previews WHERE child_name = 'Ahse' ORDER BY created_at DESC LIMIT 1"))
        row = res.fetchone()
        if row:
            print("CLOTHING DESC IN DB:", row[1])
            print(json.dumps(row[0], indent=2))
        else:
            print("Not found")

asyncio.run(get_preview())