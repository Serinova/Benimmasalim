"""
Sync learning_outcomes with prompt_templates.

This script:
1. Removes duplicate/fallback EDUCATIONAL prompts (English ones)
2. Creates EDUCATIONAL_xxx prompt for each learning_outcome that doesn't have one
3. Ensures 1:1 mapping between learning_outcomes and educational prompts

Run with: python -m scripts.sync_outcomes_prompts
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.models.learning_outcome import LearningOutcome
from app.models.prompt_template import PromptTemplate


def normalize_key(name: str) -> str:
    """Normalize a name to a key for prompt templates."""
    tr_map = {
        "ş": "s", "Ş": "S",
        "ı": "i", "İ": "I",
        "ö": "o", "Ö": "O",
        "ü": "u", "Ü": "U",
        "ğ": "g", "Ğ": "G",
        "ç": "c", "Ç": "C",
    }
    key = name.lower()
    for tr, en in tr_map.items():
        key = key.replace(tr, en.lower())
    key = "".join(c if c.isalnum() or c == "_" else "_" for c in key)
    while "__" in key:
        key = key.replace("__", "_")
    return key.strip("_")


async def analyze_current_state(db: AsyncSession) -> dict:
    """Analyze current state of learning_outcomes and prompt_templates."""
    
    # Get all learning outcomes
    result = await db.execute(select(LearningOutcome).order_by(LearningOutcome.category, LearningOutcome.name))
    outcomes = result.scalars().all()
    
    # Get all educational prompts
    result = await db.execute(
        select(PromptTemplate)
        .where(PromptTemplate.category == "educational")
        .order_by(PromptTemplate.key)
    )
    prompts = result.scalars().all()
    
    print("\n" + "="*60)
    print("CURRENT STATE ANALYSIS")
    print("="*60)
    
    print(f"\n📋 Learning Outcomes: {len(outcomes)}")
    for o in outcomes:
        expected_key = f"EDUCATIONAL_{normalize_key(o.name)}"
        print(f"  - {o.name} ({o.category}) → {expected_key}")
    
    print(f"\n📝 Educational Prompts: {len(prompts)}")
    for p in prompts:
        print(f"  - {p.key}: {p.name} (active={p.is_active})")
    
    # Find duplicates and mismatches
    outcome_keys = {f"EDUCATIONAL_{normalize_key(o.name)}": o for o in outcomes}
    prompt_keys = {p.key: p for p in prompts}
    
    # Prompts without matching outcome
    orphan_prompts = []
    for key, prompt in prompt_keys.items():
        if key not in outcome_keys:
            orphan_prompts.append(prompt)
    
    # Outcomes without matching prompt
    missing_prompts = []
    for key, outcome in outcome_keys.items():
        if key not in prompt_keys:
            missing_prompts.append((key, outcome))
    
    print(f"\n⚠️  Orphan Prompts (no matching outcome): {len(orphan_prompts)}")
    for p in orphan_prompts:
        print(f"  - {p.key}: {p.name}")
    
    print(f"\n⚠️  Missing Prompts (outcomes without prompt): {len(missing_prompts)}")
    for key, o in missing_prompts:
        print(f"  - {o.name} → needs {key}")
    
    return {
        "outcomes": outcomes,
        "prompts": prompts,
        "outcome_keys": outcome_keys,
        "prompt_keys": prompt_keys,
        "orphan_prompts": orphan_prompts,
        "missing_prompts": missing_prompts,
    }


async def cleanup_and_sync(db: AsyncSession, dry_run: bool = True) -> None:
    """
    Clean up orphan prompts and create missing ones.
    
    Args:
        dry_run: If True, only print what would be done without making changes
    """
    state = await analyze_current_state(db)
    
    print("\n" + "="*60)
    print("CLEANUP PLAN" + (" (DRY RUN)" if dry_run else " (EXECUTING)"))
    print("="*60)
    
    # 1. Delete orphan prompts (those without matching learning outcome)
    if state["orphan_prompts"]:
        print(f"\n🗑️  Will DELETE {len(state['orphan_prompts'])} orphan prompts:")
        for p in state["orphan_prompts"]:
            print(f"  - {p.key}")
            if not dry_run:
                await db.delete(p)
    
    # 2. Create missing prompts
    if state["missing_prompts"]:
        print(f"\n➕ Will CREATE {len(state['missing_prompts'])} new prompts:")
        for key, outcome in state["missing_prompts"]:
            # Build prompt content from outcome's ai_prompt field
            theme = outcome.name.upper()
            instruction = outcome.ai_prompt_instruction or outcome.ai_prompt or f"Hikayede çocuk '{outcome.name}' konusunu deneyimlesin."
            
            content = f"""⭐ {theme}

{instruction}"""
            
            print(f"  - {key}: {outcome.name}")
            
            if not dry_run:
                prompt = PromptTemplate(
                    key=key,
                    name=outcome.name,
                    category="educational",
                    description=f"Eğitsel değer promptu: {outcome.name}",
                    content=content,
                    language="tr",
                    version=1,
                    is_active=outcome.is_active,
                    modified_by="sync_script",
                )
                db.add(prompt)
    
    if not dry_run:
        await db.commit()
        print("\n✅ Changes committed!")
    else:
        print("\n⚠️  DRY RUN - No changes made. Run with --execute to apply changes.")


async def main():
    """Main entry point."""
    # Parse args
    dry_run = "--execute" not in sys.argv
    
    if dry_run:
        print("Running in DRY RUN mode. Use --execute to apply changes.")
    
    # Create engine
    engine = create_async_engine(settings.database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        await cleanup_and_sync(db, dry_run=dry_run)
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
