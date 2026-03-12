import asyncio, json, os
from dotenv import load_dotenv
load_dotenv(override=True)
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

engine = create_async_engine(os.getenv('DATABASE_URL'))

async def check():
    async with engine.connect() as conn:
        r = await conn.execute(text(
            "SELECT theme_key, name, is_active FROM scenarios ORDER BY name"
        ))
        rows = r.fetchall()
        with open('tmp/scenario_list.txt', 'w', encoding='utf-8') as f:
            for row in rows:
                f.write(f"theme_key={row[0]}  |  name={row[1]}  |  active={row[2]}\n")
        print(f"Wrote {len(rows)} scenarios to tmp/scenario_list.txt")
    await engine.dispose()

asyncio.run(check())
