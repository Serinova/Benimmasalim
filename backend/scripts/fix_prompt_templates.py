import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import text

async def fix_templates():
    db_url = os.getenv("DATABASE_URL")
    engine = create_async_engine(db_url)
    SessionLocal = async_sessionmaker(bind=engine)
    
    async with SessionLocal() as session:
        # Check current templates
        res = await session.execute(text("SELECT key, content_en FROM prompt_templates WHERE key IN ('COVER_TEMPLATE', 'INNER_TEMPLATE')"))
        print("BEFORE:")
        for r in res.fetchall():
            print(f"{r[0]}: {r[1]}")
            
        # Update COVER
        await session.execute(text("""
            UPDATE prompt_templates 
            SET content_en = 'A young child wearing {clothing_description}. {scene_description}. CRITICAL COVER LAYOUT: Leave massive empty negative space / clear sky at the top 30% of the image for the book title. Do not draw important elements or the child''s head at the very top. CRITICAL: Do NOT include ANY text, titles, letters, words, or typography anywhere in the image.' 
            WHERE key = 'COVER_TEMPLATE'
        """))
        
        # Update INNER
        await session.execute(text("""
            UPDATE prompt_templates 
            SET content_en = 'A young child wearing {clothing_description}. {scene_description}. Ensure clear areas in the environment where text can be placed without obscuring the main action. Do NOT include ANY text, letters, words, or watermarks.' 
            WHERE key = 'INNER_TEMPLATE'
        """))
        
        await session.commit()
        
        # Check new templates
        res = await session.execute(text("SELECT key, content_en FROM prompt_templates WHERE key IN ('COVER_TEMPLATE', 'INNER_TEMPLATE')"))
        print("\nAFTER:")
        for r in res.fetchall():
            print(f"{r[0]}: {r[1]}")

if __name__ == "__main__":
    asyncio.run(fix_templates())