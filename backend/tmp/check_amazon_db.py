import asyncio, os
from dotenv import load_dotenv
load_dotenv(override=True)
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

engine = create_async_engine(os.getenv("DATABASE_URL"))

async def check():
    async with engine.connect() as conn:
        r = await conn.execute(text(
            "SELECT theme_key, name, description, tagline, is_active, "
            "display_order, image_url, badge, age_range "
            "FROM scenarios WHERE theme_key = 'amazon'"
        ))
        row = r.fetchone()
        if row:
            for i, col in enumerate(r.keys()):
                val = row[i]
                if isinstance(val, str) and len(val) > 300:
                    val = val[:300] + "..."
                print(f"{col}: {val}")
        else:
            print("Amazon senaryosu DB'de bulunamadi!")
    await engine.dispose()

asyncio.run(check())
