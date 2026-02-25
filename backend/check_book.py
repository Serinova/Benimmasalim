import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from sqlalchemy import text

async def main():
    target_id = "04307a93-6a37-4234-bc5c-a033b2e8fb63"
    
    from app.core.database import async_session_factory as async_session_maker
    
    async with async_session_maker() as session:
        print(f"Checking story_previews for {target_id}...")
        try:
            result = await session.execute(text("SELECT id, child_name, story_title, clothing_description, story_pages, prompt_debug_json FROM story_previews WHERE id = :id"), {"id": target_id})
            preview = result.fetchone()
            if preview:
                print("FOUND AS PREVIEW")
                print(f"Child: {preview[1]}, Title: {preview[2]}")
                print(f"Clothing: {preview[3]}")
                print("\n--- STORY TEXT ---")
                print(preview[4])
                if preview[5]:
                    print("\n--- PROMPTS ---")
                    import json
                    prompts = preview[5]
                    if isinstance(prompts, str):
                        prompts = json.loads(prompts)
                    for k, v in prompts.items():
                        print(f"Page {k}:")
                        print(f"  Prompt: {v.get('final_prompt')}")
                        print(f"  Negative: {v.get('negative_prompt')}")
                else:
                    print("No prompt debug json")
                return
        except Exception as e:
            print(f"Error querying story_previews: {e}")
            
        print("Not found.")

if __name__ == "__main__":
    asyncio.run(main())