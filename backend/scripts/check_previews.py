"""Check story previews in database.

Uses DATABASE_URL from .env (via app config) or direct env var.
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import asyncpg


async def main():
    # DATABASE_URL from environment (.env or Cloud Run)
    db_url = os.environ.get("DATABASE_URL", "")
    if not db_url:
        print("[ERROR] DATABASE_URL environment variable is not set.", file=sys.stderr)
        print("  Set it in .env or export it before running this script.", file=sys.stderr)
        sys.exit(1)

    # asyncpg expects postgresql:// (not postgresql+asyncpg://)
    db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")

    conn = await asyncpg.connect(db_url)

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
