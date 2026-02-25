"""Add id_weight column to visual_styles table."""
import os
from urllib.parse import urlparse

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import psycopg2


def _get_db_params():
    url = os.environ.get("DATABASE_URL", "").replace("postgresql+asyncpg://", "postgresql://")
    if url:
        parsed = urlparse(url)
        return {
            "host": parsed.hostname or "localhost",
            "port": parsed.port or 5432,
            "database": (parsed.path or "/benimmasalim").lstrip("/"),
            "user": parsed.username or "postgres",
            "password": parsed.password or "postgres",
        }
    return {
        "host": "localhost",
        "port": 5432,
        "database": "benimmasalim",
        "user": "postgres",
        "password": "postgres",
    }


def add_column():
    """Add id_weight column if not exists using psycopg2 directly."""
    params = _get_db_params()
    conn = psycopg2.connect(**params)
    conn.autocommit = True
    cur = conn.cursor()
    
    try:
        # Check if column exists
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'visual_styles' AND column_name = 'id_weight'
        """)
        exists = cur.fetchone()
        
        if not exists:
            cur.execute("ALTER TABLE visual_styles ADD COLUMN id_weight FLOAT DEFAULT 0.35")
            print("id_weight column added to visual_styles!")
        else:
            print("id_weight column already exists")
            
        # Update existing styles with recommended values
        updates = [
            ("Anime Tarzi", 0.18),
            ("Sulu Boya", 0.22),
            ("Cizgi Film Tarzi", 0.25),
            ("Oyun Tarzi", 0.30),
            ("Vintage Retro", 0.30),
            ("Kaligrafik", 0.32),
            ("3D Super Kahraman", 0.38),
            ("Gercekci Masal", 0.48),
        ]
        
        for name, weight in updates:
            cur.execute(
                "UPDATE visual_styles SET id_weight = %s WHERE name = %s",
                (weight, name)
            )
            if cur.rowcount > 0:
                print(f"  Updated {name} -> {weight}")
        
        print("Updated id_weight values for existing styles")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    add_column()
