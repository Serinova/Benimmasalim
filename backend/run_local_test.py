import asyncio
import uuid
import structlog
from app.core.database import async_session_factory
from app.tasks.generate_coloring_book_for_trial import generate_coloring_book_for_trial
from app.models.story_preview import StoryPreview
from sqlalchemy import select

structlog.configure(
    processors=[structlog.processors.TimeStamper(fmt="iso"), structlog.processors.JSONRenderer()]
)

async def test_run():
    # Use one of the trial IDs from the trigger script
    trial_id_str = "0f63841a-0cd9-4a55-9548-fc8a99adfb31"
    trial_id = uuid.UUID(trial_id_str)
    
    async with async_session_factory() as db:
        print("Checking trial in DB...")
        res = await db.execute(select(StoryPreview).where(StoryPreview.id == trial_id))
        trial = res.scalar_one_or_none()
        if not trial:
            print("Trial not found!")
            return
            
        print(f"Trial found: has_coloring_book={trial.has_coloring_book}")
        
        try:
            print("Running generate_coloring_book_for_trial...")
            await generate_coloring_book_for_trial(trial_id, db)
            print("Completed successfully!")
        except Exception as e:
            print(f"ERROR OCCURRED: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_run())
