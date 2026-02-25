import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import select
from app.core.database import async_session_factory
from app.models.scenario import Scenario

async def fix_constraints():
    async with async_session_factory() as db:
        result = await db.execute(select(Scenario))
        scenarios = result.scalars().all()
        updated_count = 0
        
        for scenario in scenarios:
            if scenario.location_constraints and "required in every scene:" in scenario.location_constraints:
                scenario.location_constraints = scenario.location_constraints.replace(
                    "required in every scene:", 
                    "iconic elements (include 1-2 relevant details depending on the scene):"
                )
                updated_count += 1
                print(f"Updated {scenario.name}")
            elif scenario.location_constraints and "her sahnede zorunlu" in scenario.location_constraints.lower():
                 scenario.location_constraints = scenario.location_constraints.replace(
                    "her sahnede zorunlu", 
                    "sahneye uygun olanları seç"
                )
                 updated_count += 1
                 print(f"Updated {scenario.name} (TR)")

        if updated_count > 0:
            await db.commit()
            print(f"Total scenarios updated: {updated_count}")
        else:
            print("No scenarios needed updating.")

if __name__ == "__main__":
    asyncio.run(fix_constraints())
