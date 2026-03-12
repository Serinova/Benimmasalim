import asyncio, json
from dotenv import load_dotenv
load_dotenv(override=True)
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import os

engine = create_async_engine(os.getenv('DATABASE_URL'))

async def check():
    async with engine.connect() as conn:
        r = await conn.execute(text(
            "SELECT theme_key, name, story_prompt_tr, scenario_bible, "
            "custom_inputs_schema, outfit_girl, outfit_boy, "
            "cover_prompt_template, page_prompt_template, "
            "location_constraints, cultural_elements, flags "
            "FROM scenarios WHERE theme_key = 'sultanahmet'"
        ))
        row = r.fetchone()
        if row:
            for i, col in enumerate(r.keys()):
                val = row[i]
                if isinstance(val, str) and len(val) > 500:
                    val = val[:500] + '...'
                elif isinstance(val, dict):
                    val = json.dumps(val, ensure_ascii=False)[:500]
                elif isinstance(val, list):
                    val = json.dumps(val, ensure_ascii=False)[:500]
                print(f'{col}: {val}')
        else:
            print('SENARYO DB-DE BULUNAMADI')
    await engine.dispose()

asyncio.run(check())
