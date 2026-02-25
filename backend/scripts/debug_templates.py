"""Debug: Show FULL scenario templates from database."""
import asyncio
import sys
sys.path.insert(0, ".")

from sqlalchemy import select
from app.core.database import async_session_factory
from app.models.scenario import Scenario


async def show_templates():
    async with async_session_factory() as db:
        result = await db.execute(select(Scenario))
        scenarios = result.scalars().all()
        
        print(f"\n{'='*80}")
        print(f"DATABASE SCENARIO TEMPLATES")
        print(f"Found {len(scenarios)} scenarios")
        print(f"{'='*80}\n")
        
        for s in scenarios:
            print(f"\n{'='*80}")
            print(f"SCENARIO: {s.name}")
            print(f"ID: {s.id}")
            print(f"{'='*80}")
            
            print(f"\n--- COVER PROMPT TEMPLATE ({len(s.cover_prompt_template)} chars) ---")
            print(s.cover_prompt_template)
            print(f"--- END COVER ---\n")
            
            print(f"\n--- PAGE PROMPT TEMPLATE ({len(s.page_prompt_template)} chars) ---")
            print(s.page_prompt_template)
            print(f"--- END PAGE ---\n")
            
            # Check for key terms
            cover_lower = s.cover_prompt_template.lower()
            print(f"Cover contains 'cappadocia': {'cappadocia' in cover_lower}")
            print(f"Cover contains 'kapadokya': {'kapadokya' in cover_lower}")
            print(f"Cover contains 'fairy chimney': {'fairy chimney' in cover_lower}")
            print(f"Cover contains 'cone-shaped': {'cone-shaped' in cover_lower}")
            print(f"Cover contains 'balloon': {'balloon' in cover_lower}")


if __name__ == "__main__":
    asyncio.run(show_templates())
