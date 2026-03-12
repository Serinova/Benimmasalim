import asyncio, json, os
from dotenv import load_dotenv
load_dotenv(override=True)
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

engine = create_async_engine(os.getenv('DATABASE_URL'))

async def verify():
    async with engine.connect() as conn:
        r = await conn.execute(text(
            "SELECT custom_inputs_schema::text, scenario_bible::text FROM scenarios WHERE theme_key = 'cappadocia'"
        ))
        row = r.fetchone()
        
        with open('tmp/verify_fix.txt', 'w', encoding='utf-8') as f:
            cis = json.loads(row[0]) if row[0] else None
            sb = json.loads(row[1]) if row[1] else None
            f.write("=== custom_inputs_schema ===\n")
            f.write(json.dumps(cis, ensure_ascii=False, indent=2))
            f.write("\n\n=== scenario_bible ===\n")
            f.write(json.dumps(sb, ensure_ascii=False, indent=2))
        print("Wrote verify_fix.txt")
    await engine.dispose()

asyncio.run(verify())
