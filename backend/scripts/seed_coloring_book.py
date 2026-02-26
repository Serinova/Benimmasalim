"""Seed default coloring book product configuration."""

import asyncio
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_async_session
from app.models.coloring_book import ColoringBookProduct


async def seed_coloring_book_product():
    """Create or update default coloring book product configuration."""
    async for db in get_async_session():
        # Check if already exists by slug
        stmt = select(ColoringBookProduct).where(ColoringBookProduct.slug == "boyama-kitabi")
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            print("✓ Coloring book product already exists - updating...")
            existing.active = True
            existing.discounted_price = Decimal("150.00")
            await db.commit()
            await db.refresh(existing)
            print(f"  ID: {existing.id}")
            print(f"  Name: {existing.name}")
            print(f"  Base Price: {existing.base_price} TL")
            print(f"  Discounted Price: {existing.discounted_price} TL")
            print(f"  Active: {existing.active}")
            return

        # Create default configuration (optimized for simple, kid-friendly coloring)
        config = ColoringBookProduct(
            name="Boyama Kitabı",
            slug="boyama-kitabi",
            description="Hikayenizdeki görsellerin boyama kitabı versiyonu. Metin içermez, sadece boyama için optimize edilmiş basit çizgiler.",
            base_price=Decimal("200.00"),
            discounted_price=Decimal("150.00"),
            line_art_method="canny",
            edge_threshold_low=80,  # Higher = fewer fine details, easier coloring
            edge_threshold_high=200,  # Higher = simpler shapes, bolder lines
            active=True,
        )

        db.add(config)
        await db.commit()
        await db.refresh(config)

        print("✓ Coloring book product created successfully!")
        print(f"  ID: {config.id}")
        print(f"  Name: {config.name}")
        print(f"  Base Price: {config.base_price} TL")
        print(f"  Discounted Price: {config.discounted_price} TL")
        print(f"  Line-art Method: {config.line_art_method}")
        print(f"  Edge Thresholds: {config.edge_threshold_low}/{config.edge_threshold_high}")


if __name__ == "__main__":
    print("=" * 60)
    print("Seeding Coloring Book Product Configuration")
    print("=" * 60)
    asyncio.run(seed_coloring_book_product())
    print("=" * 60)
    print("Done!")
