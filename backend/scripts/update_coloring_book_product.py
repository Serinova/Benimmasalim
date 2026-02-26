"""Update coloring book product configuration."""

import asyncio
import sys
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_factory
from app.models.coloring_book import ColoringBookProduct


async def update_coloring_book_product():
    """Create or update coloring book product configuration."""
    async with async_session_factory() as db:
        try:
            # Check if already exists by slug
            stmt = select(ColoringBookProduct).where(
                ColoringBookProduct.slug == "boyama-kitabi"
            )
            result = await db.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                print("✓ Coloring book product exists - updating...")
                existing.active = True
                existing.discounted_price = Decimal("150.00")
                existing.base_price = Decimal("200.00")
                existing.line_art_method = "canny"
                existing.edge_threshold_low = 80
                existing.edge_threshold_high = 200
                await db.commit()
                await db.refresh(existing)
                print(f"  ID: {existing.id}")
                print(f"  Name: {existing.name}")
                print(f"  Base Price: {existing.base_price} TL")
                print(f"  Discounted Price: {existing.discounted_price} TL")
                print(f"  Active: {existing.active}")
                print(f"  Line-art: {existing.line_art_method} ({existing.edge_threshold_low}/{existing.edge_threshold_high})")
                return

            # Create new product
            print("✓ Creating new coloring book product...")
            config = ColoringBookProduct(
                name="Boyama Kitabı",
                slug="boyama-kitabi",
                description="Hikayenizdeki görsellerin boyama kitabı versiyonu.",
                base_price=Decimal("200.00"),
                discounted_price=Decimal("150.00"),
                line_art_method="canny",
                edge_threshold_low=80,
                edge_threshold_high=200,
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
            print(f"  Line-art: {config.line_art_method} ({config.edge_threshold_low}/{config.edge_threshold_high})")

        except Exception as e:
            print(f"❌ Error: {e}")
            await db.rollback()
            sys.exit(1)


if __name__ == "__main__":
    print("=" * 60)
    print("Updating Coloring Book Product Configuration")
    print("=" * 60)
    asyncio.run(update_coloring_book_product())
    print("=" * 60)
    print("Done!")
