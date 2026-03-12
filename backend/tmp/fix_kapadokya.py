"""Fix Kapadokya scenario: custom_inputs_schema + scenario_bible"""
import asyncio, json, os
from dotenv import load_dotenv
load_dotenv(override=True)
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

engine = create_async_engine(os.getenv('DATABASE_URL'))

# Correct custom_inputs_schema with proper {label, value} dicts
CORRECT_CUSTOM_INPUTS = json.dumps([
    {
        "key": "animal_friend",
        "type": "select",
        "label": "Yol Arkadaşı",
        "default": "Cesur Yılkı Atı",
        "options": [
            {"label": "Cesur Yılkı Atı", "value": "Cesur Yılkı Atı"},
            {"label": "Sevimli Kapadokya Tilkisi", "value": "Sevimli Kapadokya Tilkisi"}
        ]
    }
], ensure_ascii=False)

# Scenario bible for better companion/object consistency
SCENARIO_BIBLE = json.dumps({
    "companions": [
        {
            "name_tr": "Cesur Yılkı Atı",
            "name_en": "brave wild Cappadocian horse",
            "species": "wild horse",
            "appearance": "small brown wild Cappadocian horse with flowing dark mane"
        },
        {
            "name_tr": "Sevimli Kapadokya Tilkisi",
            "name_en": "small reddish-orange Cappadocian fox",
            "species": "fox",
            "appearance": "small reddish-orange Cappadocian fox with fluffy tail and bright green eyes"
        }
    ],
    "key_objects": [
        {
            "name_tr": "Göktürk Madalyonu",
            "appearance_en": "ancient golden Gokturk medallion with carved sun symbol and small holes, palm-sized, hanging on a leather cord",
            "first_page": 11,
            "last_page": 21,
            "prompt_suffix": "holding ancient golden medallion with sun symbol — SAME appearance on every page"
        }
    ],
    "locations": [
        "Goreme Valley fairy chimneys at sunrise",
        "Derinkuyu Underground City dark tunnels with stone walls",
        "Ancient carved stone door with horse, bird, sun symbols",
        "Hidden fresco room with colorful ancient wall paintings",
        "Hot air balloon basket high above Cappadocia valleys",
        "Goreme landing field at sunset"
    ],
    "no_family": True,
    "no_magic": True,
    "child_solo": True,
    "guide_character": False
}, ensure_ascii=False)


async def fix():
    async with engine.begin() as conn:
        # Verify current state
        r = await conn.execute(text(
            "SELECT custom_inputs_schema::text, scenario_bible::text FROM scenarios WHERE theme_key = 'cappadocia'"
        ))
        row = r.fetchone()
        if not row:
            print("ERROR: Kapadokya scenario not found!")
            return

        print("BEFORE:")
        print(f"  custom_inputs_schema: {row[0][:200]}")
        print(f"  scenario_bible: {row[1]}")
        print()

        # Update
        await conn.execute(text(
            "UPDATE scenarios SET custom_inputs_schema = :cis, scenario_bible = :sb WHERE theme_key = 'cappadocia'"
        ), {"cis": CORRECT_CUSTOM_INPUTS, "sb": SCENARIO_BIBLE})

        # Verify
        r2 = await conn.execute(text(
            "SELECT custom_inputs_schema::text, scenario_bible::text FROM scenarios WHERE theme_key = 'cappadocia'"
        ))
        row2 = r2.fetchone()
        print("AFTER:")
        print(f"  custom_inputs_schema: {row2[0][:200]}")
        print(f"  scenario_bible: {row2[1][:200]}")
        print()
        print("✅ Kapadokya scenario fixed!")

    await engine.dispose()

asyncio.run(fix())
