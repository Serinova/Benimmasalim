"""Fix all story_preview titles: Hikaye -> personalized, broken encoding -> correct Turkish."""
import asyncio
import sys
sys.path.insert(0, "/app")

import asyncpg

DB_URL = "postgresql://postgres:postgres@postgres:5432/benimmasalim"

# Turkish possessive suffix
def get_possessive(name: str) -> str:
    """Get Turkish possessive suffix for a name."""
    name = name.strip()
    if not name:
        return "'in"
    last_vowel = ""
    for ch in reversed(name.lower()):
        if ch in "aeıioöuü":
            last_vowel = ch
            break
    # Turkish vowel harmony
    if last_vowel in ("a", "ı"):
        suffix = "ın"
    elif last_vowel in ("e", "i"):
        suffix = "in"
    elif last_vowel in ("o", "u"):
        suffix = "un"
    elif last_vowel in ("ö", "ü"):
        suffix = "ün"
    else:
        suffix = "in"
    
    # Apostrophe type based on last char
    last_char = name[-1].lower()
    if last_char in "aeıioöuü":
        # Ends with vowel: use 'n' connector
        return f"'{suffix[0]}n"  # e.g., Uras'ın, Ahsen'in
    return f"'{suffix}"

def capitalize_name(name: str) -> str:
    """Properly capitalize a Turkish name."""
    if not name:
        return name
    # Handle Turkish İ/I properly
    return name[0].upper() + name[1:].lower() if len(name) > 1 else name.upper()

async def main():
    conn = await asyncpg.connect(DB_URL)
    
    # Get all previews with bad titles
    rows = await conn.fetch("""
        SELECT id, child_name, scenario_name, story_title 
        FROM story_previews 
        WHERE story_title = 'Hikaye' 
           OR story_title LIKE '%Ä%'
           OR story_title LIKE '%ı%n %acera%'
        ORDER BY created_at DESC
    """)
    
    print(f"Found {len(rows)} previews with bad titles")
    
    fixed = 0
    for row in rows:
        child = capitalize_name(row["child_name"] or "")
        scenario = row["scenario_name"] or "Büyülü Macera"
        suffix = get_possessive(child)
        
        new_title = f"{child}{suffix} {scenario}"
        
        if row["story_title"] != new_title:
            await conn.execute(
                "UPDATE story_previews SET story_title = $1 WHERE id = $2",
                new_title, row["id"]
            )
            print(f"  Fixed: '{row['story_title'][:40]}' -> '{new_title}'")
            fixed += 1
    
    print(f"\nFixed {fixed} titles")
    await conn.close()

asyncio.run(main())
