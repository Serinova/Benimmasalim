"""Check story previews in database."""
import asyncio

import asyncpg


async def main():
    conn = await asyncpg.connect(
        host='localhost',
        database='benimmasalim',
        user='benimmasalim',
        password='Benim.376132212'
    )

    rows = await conn.fetch('''
        SELECT id, status, parent_email, child_name, 
               substring(story_title, 1, 30) as title,
               confirmed_at, created_at 
        FROM story_previews 
        ORDER BY created_at DESC 
        LIMIT 5
    ''')

    print("\n=== Story Previews ===")
    for row in rows:
        print(f"Status: {row['status']:<12} | Email: {row['parent_email']:<30} | Child: {row['child_name']:<10} | Confirmed: {row['confirmed_at']}")

    # Count by status
    counts = await conn.fetch('''
        SELECT status, count(*) as cnt FROM story_previews GROUP BY status
    ''')
    print("\n=== Counts by Status ===")
    for row in counts:
        print(f"{row['status']}: {row['cnt']}")

    await conn.close()

asyncio.run(main())
