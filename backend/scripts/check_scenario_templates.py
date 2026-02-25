"""Check scenario templates for {child_name} usage."""
import asyncio
import sys
sys.path.insert(0, ".")

from sqlalchemy import select
from app.core.database import async_session_factory
from app.models.scenario import Scenario


async def check_templates():
    async with async_session_factory() as db:
        result = await db.execute(select(Scenario))
        scenarios = result.scalars().all()
        
        print(f"\n{'='*60}")
        print(f"Found {len(scenarios)} scenarios")
        print(f"{'='*60}\n")
        
        for s in scenarios:
            print(f"Scenario: {s.name}")
            print(f"  ID: {s.id}")
            
            # Check cover template
            if s.cover_prompt_template:
                has_child_name = "{child_name}" in s.cover_prompt_template
                print(f"  Cover template has child_name: {has_child_name}")
                if has_child_name:
                    print(f"    Template preview: {s.cover_prompt_template[:200]}...")
            
            # Check page template
            if s.page_prompt_template:
                has_child_name = "{child_name}" in s.page_prompt_template
                print(f"  Page template has child_name: {has_child_name}")
            
            print()


if __name__ == "__main__":
    asyncio.run(check_templates())
