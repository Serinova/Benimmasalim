import asyncio, os
from dotenv import load_dotenv
load_dotenv(override=True)
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

engine = create_async_engine(os.getenv('DATABASE_URL'))

async def check():
    async with engine.connect() as conn:
        r = await conn.execute(text("SELECT version(), current_database(), inet_server_addr(), inet_server_port()"))
        row = r.fetchone()
        
        r2 = await conn.execute(text("SELECT datname FROM pg_database WHERE datistemplate = false ORDER BY datname"))
        dbs = r2.fetchall()

        r3 = await conn.execute(text("SELECT COUNT(*) FROM scenarios"))
        count = r3.scalar()

        r4 = await conn.execute(text("SELECT theme_key, name, LENGTH(story_prompt_tr), custom_inputs_schema::text, scenario_bible::text FROM scenarios WHERE theme_key = 'cappadocia'"))
        row4 = r4.fetchone()

        with open('tmp/db_info.txt', 'w', encoding='utf-8') as f:
            f.write(f"DB Version: {row[0]}\n")
            f.write(f"Database: {row[1]}\n")
            f.write(f"Server Addr: {row[2]}\n")
            f.write(f"Server Port: {row[3]}\n\n")
            f.write("All databases on this server:\n")
            for db in dbs:
                f.write(f"  - {db[0]}\n")
            f.write(f"\nTotal scenarios: {count}\n")
            if row4:
                f.write(f"\nKapadokya: theme_key={row4[0]}, name={row4[1]}, prompt_len={row4[2]}\n")
                f.write(f"custom_inputs_schema: {row4[3]}\n")
                f.write(f"scenario_bible: {row4[4]}\n")
        print("Wrote tmp/db_info.txt")
    await engine.dispose()

asyncio.run(check())
