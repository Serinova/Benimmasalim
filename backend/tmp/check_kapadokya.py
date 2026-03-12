import asyncio, json, os
from dotenv import load_dotenv
load_dotenv(override=True)
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

engine = create_async_engine(os.getenv('DATABASE_URL'))

async def check():
    async with engine.connect() as conn:
        r = await conn.execute(text(
            """SELECT theme_key, name, story_prompt_tr, scenario_bible,
                      custom_inputs_schema, outfit_girl, outfit_boy,
                      cover_prompt_template, page_prompt_template,
                      location_constraints, cultural_elements, flags
               FROM scenarios WHERE theme_key = 'cappadocia'"""
        ))
        row = r.fetchone()
        if row:
            with open('tmp/kapadokya_data.txt', 'w', encoding='utf-8') as f:
                for i, col in enumerate(r.keys()):
                    val = row[i]
                    if isinstance(val, (dict, list)):
                        val = json.dumps(val, ensure_ascii=False, indent=2)
                    f.write(f'=== {col} ===\n')
                    f.write(str(val) + '\n\n')
            print("Wrote kapadokya_data.txt")
        else:
            print('Kapadokya senaryo bulunamadi!')
    await engine.dispose()

asyncio.run(check())
