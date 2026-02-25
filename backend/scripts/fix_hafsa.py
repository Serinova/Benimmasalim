"""Fix Hafsa possessive suffix."""
import asyncio
import sys
sys.path.insert(0, "/app")
import asyncpg

async def main():
    conn = await asyncpg.connect("postgresql://postgres:postgres@postgres:5432/benimmasalim")
    # Fix Hafsa'ın -> Hafsa'nın
    result = await conn.execute(
        "UPDATE story_previews SET story_title = $1 WHERE child_name ILIKE $2 AND story_title LIKE $3",
        "Hafsa\u2019n\u0131n Kapadokya maceras\u0131".replace("\u2019", "'"),
        "hafsa",
        "Hafsa%\u0131n Kapadokya%"
    )
    print(f"Updated Hafsa titles: {result}")
    
    # Also fix Efe'in -> Efe'nin  
    result2 = await conn.execute(
        "UPDATE story_previews SET story_title = $1 WHERE child_name ILIKE $2 AND story_title LIKE $3",
        "Efe'nin Kapadokya maceras\u0131",
        "efe",
        "Efe%in Kapadokya%"
    )
    print(f"Updated Efe titles: {result2}")
    
    await conn.close()

asyncio.run(main())
