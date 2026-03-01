"""Deactivate old product formats, keeping only A4 Yatay Macera as the main story book.

Run: python -m scripts.cleanup_products

Products to DEACTIVATE:
  - Kare Masal (kare-masal)
  - A4 Dev Macera (a4-dev-macera)
  - Cep Boy Hikaye (cep-boy-hikaye)

Products to KEEP active:
  - A4 Yatay Macera (a4-yatay / a4-yatay-macera) — main story book
  - audio-addon-system-voice — Sesli okuma sistem sesi
  - audio-addon-cloned-voice — Sesli okuma klon ses
  - (coloring_book_products table) — Boyama kitabı

Also ensures all scenarios are linked to the A4 Yatay product.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select, update
from app.core.database import async_session_factory
from app.models.product import Product
from app.models.scenario import Scenario


SLUGS_TO_DEACTIVATE = ["kare-masal", "a4-dev-macera", "cep-boy-hikaye"]
MAIN_PRODUCT_SLUGS = ["a4-yatay", "a4-yatay-macera"]  # production may use either


async def main():
    async with async_session_factory() as db:
        # 1. Find the main A4 Yatay product
        for slug in MAIN_PRODUCT_SLUGS:
            result = await db.execute(
                select(Product).where(Product.slug == slug)
            )
            main_product = result.scalar_one_or_none()
            if main_product:
                break
        
        if not main_product:
            print("❌ A4 Yatay product not found with any known slug!")
            return

        print(f"✅ Main product found: {main_product.name} (slug={main_product.slug}, id={main_product.id})")
        
        # 2. Deactivate old products
        deactivated = 0
        for slug in SLUGS_TO_DEACTIVATE:
            result = await db.execute(
                select(Product).where(Product.slug == slug)
            )
            product = result.scalar_one_or_none()
            if product:
                product.is_active = False
                product.is_featured = False
                deactivated += 1
                print(f"  🗑️  Deactivated: {product.name} (slug={slug})")
            else:
                print(f"  ⚠️  Not found: {slug} (may already be removed)")
        
        # 3. Link all unlinked scenarios to A4 Yatay product
        result = await db.execute(
            select(Scenario).where(Scenario.linked_product_id.is_(None))
        )
        unlinked = result.scalars().all()
        for scenario in unlinked:
            scenario.linked_product_id = main_product.id
            print(f"  🔗 Linked scenario: {scenario.name} → {main_product.name}")
        
        # 4. Also re-link scenarios that were linked to deactivated products
        for slug in SLUGS_TO_DEACTIVATE:
            result = await db.execute(
                select(Product).where(Product.slug == slug)
            )
            old_product = result.scalar_one_or_none()
            if old_product:
                result = await db.execute(
                    select(Scenario).where(Scenario.linked_product_id == old_product.id)
                )
                orphaned = result.scalars().all()
                for scenario in orphaned:
                    scenario.linked_product_id = main_product.id
                    print(f"  🔄 Re-linked scenario: {scenario.name} (was linked to {old_product.name})")
        
        # 5. List remaining active products
        result = await db.execute(
            select(Product).where(Product.is_active == True).order_by(Product.display_order)
        )
        active_products = result.scalars().all()
        
        print(f"\n📦 Active products after cleanup ({len(active_products)}):")
        for p in active_products:
            print(f"  • {p.name} (slug={p.slug}, type={p.product_type}, price={p.base_price})")
        
        await db.commit()
        print(f"\n✅ Done! Deactivated {deactivated} products, linked {len(unlinked)} scenarios.")


if __name__ == "__main__":
    asyncio.run(main())
