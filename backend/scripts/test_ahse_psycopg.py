import json
import os
import psycopg2
from psycopg2.extras import RealDictCursor

db_url = os.getenv('DATABASE_URL')
# handle sqlalchemy format to psycopg2 format
if db_url.startswith('postgresql+asyncpg://'):
    db_url = db_url.replace('postgresql+asyncpg://', 'postgresql://')

conn = psycopg2.connect(db_url)
cur = conn.cursor(cursor_factory=RealDictCursor)
cur.execute("SELECT prompt_debug_json, clothing_description FROM story_previews WHERE child_name = 'Ahse' ORDER BY created_at DESC LIMIT 1")
row = cur.fetchone()
if row:
    print("CLOTHING DESC IN DB:", row['clothing_description'])
    print(json.dumps(row['prompt_debug_json'], indent=2))
else:
    print("Not found")
conn.close()