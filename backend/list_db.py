import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from sqlalchemy import text

async def main():
    from app.core.database import async_session_factory as async_session_maker
    
    async with async_session_maker() as session:
        print(f"--- STORY PREVIEWS FOR URAS ---")
        try:
            result = await session.execute(text("SELECT id, child_name, child_gender FROM story_previews WHERE child_name ILIKE '%uras%' ORDER BY created_at DESC LIMIT 5"))
            for row in result.fetchall():
                print(f"ID: {row[0]}, Child: {row[1]}, Gender: {row[2]}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())