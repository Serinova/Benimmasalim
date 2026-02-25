import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from sqlalchemy.future import select


async def main():
    try:

        from app.core.database import async_session_factory as async_session_maker
        from app.models.order import Order
        from app.models.story_preview import StoryPreview
        
        async with async_session_maker() as session:
            # Look for order or preview with the given ID
            target_id = "680a55ea-8e86-49f9-8654-fc64ec998cb5"
            print(f"Checking Order for {target_id}...")
            result = await session.execute(select(Order).where(Order.id == target_id))
            order = result.scalar_one_or_none()
            
            if order:
                print(f"Found Order: {order.child_name}, {order.story_title}")
                print(f"Clothing Description: {order.clothing_description}")
                print("Prompt Debug JSON:")
                if order.prompt_debug_json:
                    for page, data in list(order.prompt_debug_json.items())[:3]:
                        print(f"Page {page}:")
                        print(f"  Prompt: {data.get('final_prompt')}")
                        print(f"  Negative: {data.get('negative_prompt')}")
            else:
                print("Checking StoryPreview...")
                result = await session.execute(select(StoryPreview).where(StoryPreview.id == target_id))
                preview = result.scalar_one_or_none()
                if preview:
                    print(f"Found StoryPreview: {preview.child_name}, {preview.story_title}")
                    print(f"Clothing Description: {preview.clothing_description}")
                    print("Prompt Debug JSON:")
                    if preview.prompt_debug_json:
                        for page, data in list(preview.prompt_debug_json.items())[:3]:
                            print(f"Page {page}:")
                            print(f"  Prompt: {data.get('final_prompt')}")
                            print(f"  Negative: {data.get('negative_prompt')}")
                else:
                    print("Not found by ID. Searching by name Ahsen...")
                    result = await session.execute(select(StoryPreview).where(StoryPreview.child_name == 'Ahsen').order_by(StoryPreview.created_at.desc()).limit(1))
                    preview = result.scalar_one_or_none()
                    if preview:
                        print(f"Found latest for Ahsen: {preview.story_title}")
                        print(f"Clothing Description: {preview.clothing_description}")
                        print("Prompt Debug JSON:")
                        if preview.prompt_debug_json:
                            for page, data in list(preview.prompt_debug_json.items())[:3]:
                                print(f"Page {page}:")
                                print(f"  Prompt: {data.get('final_prompt')}")
                                print(f"  Negative: {data.get('negative_prompt')}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
