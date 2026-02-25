import asyncio
import os
import json
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import text

async def fetch_prompts():
    engine = create_async_engine('postgresql+asyncpg://postgres:123456@host.docker.internal:5432/benimmasalim')
    SessionLocal = async_sessionmaker(bind=engine)
    async with SessionLocal() as session:
        res = await session.execute(text("SELECT id, prompt_debug_json FROM story_previews WHERE child_name ILIKE '%ahsen%' ORDER BY created_at DESC LIMIT 1"))
        row = res.fetchone()
        if row:
            print("ID:", row[0])
            print("PROMPTS:")
            if row[1]:
                # Keys might be strings "0", "1", ...
                for key, val in sorted(row[1].items(), key=lambda x: int(x[0])):
                    print(f"\n--- PAGE {key} ---")
                    print(val.get('final_prompt_after', 'N/A'))
            else:
                print("No prompt_debug_json found.")
        else:
            print("Not found")

if __name__ == "__main__":
    asyncio.run(fetch_prompts())