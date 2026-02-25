import json
import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import text
import asyncio

async def main():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("NO DATABASE_URL")
        return
        
    engine = create_async_engine(db_url)
    SessionLocal = async_sessionmaker(bind=engine)
    
    async with SessionLocal() as session:
        res = await session.execute(text("SELECT prompt_debug_json, clothing_description FROM story_previews WHERE child_name = 'Ahse' ORDER BY created_at DESC LIMIT 1"))
        row = res.fetchone()
        if row:
            print("CLOTHING DESC IN DB:", row[1])
            print(json.dumps(row[0], indent=2))
        else:
            print("Not found")

if __name__ == "__main__":
    asyncio.run(main())