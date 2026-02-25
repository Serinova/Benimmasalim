import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from sqlalchemy.future import select


async def main():
    try:
        from app.core.database import async_session_factory as async_session_maker
        from app.models.scenario import Scenario
        
        async with async_session_maker() as session:
            result = await session.execute(select(Scenario).where(Scenario.name.ilike('%Kapadokya%')))
            scenario = result.scalar_one_or_none()
            
            if scenario:
                print("SCENARIO FOUND:")
                print(f"Name: {scenario.name}")
                print(f"Theme Key: {scenario.theme_key}")
                print(f"Location Constraints: {scenario.location_constraints}")
                print("\n=== STORY PROMPT TR ===")
                print(scenario.story_prompt_tr)
                print("\n=== SCENARIO BIBLE ===")
                print(json.dumps(scenario.scenario_bible, ensure_ascii=False, indent=2))
                print("\n=== CULTURAL ELEMENTS ===")
                print(json.dumps(scenario.cultural_elements, ensure_ascii=False, indent=2))
            else:
                print("Scenario not found.")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
