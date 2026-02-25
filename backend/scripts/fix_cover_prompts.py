import asyncio
import os
import sys

# Ensure app is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import select
from app.core.database import async_session_factory
from app.models.scenario import Scenario

async def fix_cover_prompts():
    print("Fixing cover prompt templates in database...")
    async with async_session_factory() as db:
        result = await db.execute(select(Scenario))
        scenarios = result.scalars().all()
        
        updated_count = 0
        for scenario in scenarios:
            updated = False
            if scenario.cover_prompt_template:
                # Fix "must include" -> "include 2-3 key details"
                if "ICONIC BACKGROUND ELEMENTS (must include):" in scenario.cover_prompt_template:
                    scenario.cover_prompt_template = scenario.cover_prompt_template.replace(
                        "ICONIC BACKGROUND ELEMENTS (must include):", 
                        "ICONIC BACKGROUND ELEMENTS (include 2-3 key details):"
                    )
                    updated = True
                
                # Fix specific Yerebatan issue (entrance -> deep inside)
                if "yerebatan" in scenario.name.lower() and "standing at the entrance of the magnificent Yerebatan Cistern" in scenario.cover_prompt_template:
                    scenario.cover_prompt_template = scenario.cover_prompt_template.replace(
                        "standing at the entrance of the magnificent Yerebatan Cistern",
                        "exploring deep inside the magnificent underground Yerebatan Cistern"
                    )
                    updated = True
            
            if updated:
                updated_count += 1
                print(f"Updated cover template for: {scenario.name}")
        
        if updated_count > 0:
            await db.commit()
            print(f"Successfully updated {updated_count} scenarios.")
        else:
            print("No scenarios needed cover template updating.")

if __name__ == "__main__":
    asyncio.run(fix_cover_prompts())
