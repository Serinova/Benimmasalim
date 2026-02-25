import asyncio
import os
import json
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import text

async def main():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("NO DATABASE_URL")
        return
        
    engine = create_async_engine(db_url)
    SessionLocal = async_sessionmaker(bind=engine)
    
    async with SessionLocal() as session:
        res = await session.execute(text("SELECT id, name, cover_prompt_template, page_prompt_template FROM scenarios WHERE name LIKE '%Efes%'"))
        for r in res.fetchall():
            print(dict(r._mapping))

if __name__ == "__main__":
    asyncio.run(main())