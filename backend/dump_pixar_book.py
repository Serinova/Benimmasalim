import asyncio

from sqlalchemy import select

from app.core.database import async_session_factory as async_session_maker
from app.models.book import Book, Page


async def main():
    book_id = "f176a48c-e2de-497a-977f-f51873719818"
    async with async_session_maker() as session:
        result = await session.execute(select(Book).where(Book.id == book_id))
        book = result.scalar_one_or_none()
        if not book:
            print("Book not found")
            return
            
        print(f"Book Status: {book.status}")
        print(f"Value: {book.value}")
        print(f"Style: {book.style}")
        print(f"Scenario ID: {book.scenario_id}")
        
        pages_result = await session.execute(
            select(Page).where(Page.book_id == book_id).order_by(Page.page_number)
        )
        pages = pages_result.scalars().all()
        for p in pages:
            print(f"\n--- Page {p.page_number} ---")
            print(f"Story Text: {p.story_text_tr}")
            print(f"Image Prompt: {p.image_prompt_en}")

if __name__ == "__main__":
    asyncio.run(main())
