"""Seed initial data for development and testing."""

import asyncio
import uuid
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_factory
from app.core.security import get_password_hash
from app.models.book_template import PageTemplate, PageType
from app.models.product import Product
from app.models.scenario import Scenario
from app.models.user import User, UserRole


async def seed_users(db: AsyncSession) -> None:
    """Create default admin user."""
    admin = User(
        id=uuid.uuid4(),
        email="admin@benimmasalim.com",
        hashed_password=get_password_hash("***REDACTED_ADMIN_PASSWORD***"),
        full_name="Admin User",
        role=UserRole.ADMIN,
        is_active=True,
    )
    db.add(admin)
    print("[OK] Admin user created: admin@benimmasalim.com / ***REDACTED_ADMIN_PASSWORD***")


async def seed_page_templates(db: AsyncSession) -> dict:
    """Create default page templates and return them for product linking."""
    templates = {}

    # Kare Masal - Cover Template
    kare_cover = PageTemplate(
        id=uuid.uuid4(),
        name="Kare Masal Kapak",
        page_type=PageType.COVER.value,
        page_width_mm=210.0,
        page_height_mm=210.0,
        bleed_mm=3.0,
        image_width_percent=100.0,
        image_height_percent=100.0,
    )
    db.add(kare_cover)
    templates["kare_cover"] = kare_cover

    # Kare Masal - Inner Template
    kare_inner = PageTemplate(
        id=uuid.uuid4(),
        name="Kare Masal Ic Sayfa",
        page_type=PageType.INNER.value,
        page_width_mm=210.0,
        page_height_mm=210.0,
        bleed_mm=3.0,
        image_width_percent=100.0,
        image_height_percent=70.0,
        text_height_percent=25.0,
    )
    db.add(kare_inner)
    templates["kare_inner"] = kare_inner

    # A4 - Cover Template
    a4_cover = PageTemplate(
        id=uuid.uuid4(),
        name="A4 Kapak",
        page_type=PageType.COVER.value,
        page_width_mm=210.0,
        page_height_mm=297.0,
        bleed_mm=3.0,
        image_width_percent=100.0,
        image_height_percent=100.0,
    )
    db.add(a4_cover)
    templates["a4_cover"] = a4_cover

    # A4 - Inner Template
    a4_inner = PageTemplate(
        id=uuid.uuid4(),
        name="A4 Ic Sayfa",
        page_type=PageType.INNER.value,
        page_width_mm=210.0,
        page_height_mm=297.0,
        bleed_mm=3.0,
        image_width_percent=100.0,
        image_height_percent=65.0,
        text_height_percent=30.0,
    )
    db.add(a4_inner)
    templates["a4_inner"] = a4_inner

    # Cep Boy - Cover Template
    cep_cover = PageTemplate(
        id=uuid.uuid4(),
        name="Cep Boy Kapak",
        page_type=PageType.COVER.value,
        page_width_mm=148.0,
        page_height_mm=210.0,
        bleed_mm=3.0,
        image_width_percent=100.0,
        image_height_percent=100.0,
    )
    db.add(cep_cover)
    templates["cep_cover"] = cep_cover

    # Cep Boy - Inner Template
    cep_inner = PageTemplate(
        id=uuid.uuid4(),
        name="Cep Boy Ic Sayfa",
        page_type=PageType.INNER.value,
        page_width_mm=148.0,
        page_height_mm=210.0,
        bleed_mm=3.0,
        image_width_percent=100.0,
        image_height_percent=70.0,
        text_height_percent=25.0,
    )
    db.add(cep_inner)
    templates["cep_inner"] = cep_inner

    # A4 Yatay (Landscape) - Cover Template
    a4_yatay_cover = PageTemplate(
        id=uuid.uuid4(),
        name="A4 Yatay Kapak",
        page_type=PageType.COVER.value,
        page_width_mm=297.0,  # Yatay: genişlik > yükseklik
        page_height_mm=210.0,
        bleed_mm=3.0,
        image_width_percent=100.0,
        image_height_percent=100.0,
        image_x_percent=0.0,
        image_y_percent=0.0,
    )
    db.add(a4_yatay_cover)
    templates["a4_yatay_cover"] = a4_yatay_cover

    # A4 Yatay (Landscape) - Inner Template
    a4_yatay_inner = PageTemplate(
        id=uuid.uuid4(),
        name="A4 Yatay Ic Sayfa",
        page_type=PageType.INNER.value,
        page_width_mm=297.0,  # Yatay: genişlik > yükseklik
        page_height_mm=210.0,
        bleed_mm=3.0,
        image_width_percent=100.0,
        image_height_percent=70.0,  # Resim üstte %70
        image_x_percent=0.0,
        image_y_percent=0.0,
        text_x_percent=5.0,
        text_y_percent=72.0,  # Metin altta
        text_width_percent=90.0,
        text_height_percent=25.0,
        text_position="bottom",
        text_align="center",
        font_size_pt=16,
        font_family="Arial",
        font_color="#333333",
    )
    db.add(a4_yatay_inner)
    templates["a4_yatay_inner"] = a4_yatay_inner

    await db.flush()
    print(f"[OK] {len(templates)} page templates created")
    return templates


async def seed_products(db: AsyncSession, templates: dict) -> None:
    """Create default products linked to page templates.
    
    Only A4 Yatay Macera is created as the main story book product.
    Audio addons and coloring book are seeded separately.
    """
    products = [
        Product(
            name="A4 Yatay Macera",
            slug="a4-yatay-macera",
            description="Yatay A4 format (297x210mm), 16 sayfa baskiya hazir",
            default_page_count=16,
            min_page_count=8,
            max_page_count=24,
            base_price=Decimal("550.00"),
            thumbnail_url="",
            is_featured=True,
            display_order=1,
            cover_template_id=templates["a4_yatay_cover"].id,
            inner_template_id=templates["a4_yatay_inner"].id,
        ),
    ]

    for product in products:
        db.add(product)
    print(f"[OK] {len(products)} products created")


async def seed_scenarios(db: AsyncSession) -> None:
    """Create default scenarios (only active ones)."""
    scenarios = [
        Scenario(
            name="Kapadokya Macerası",
            description="Peri bacaları, sıcak hava balonları ve yeraltı şehirleri arasında unutulmaz bir Kapadokya macerası!",
            thumbnail_url="",
            theme_key="cappadocia",
            display_order=1,
        ),
        Scenario(
            name="Yerebatan Sarnıcı",
            description="İstanbul'un gizemli yeraltı sarayında, antik sütunlar ve Medusa başları arasında büyülü bir macera!",
            thumbnail_url="",
            theme_key="yerebatan",
            display_order=2,
        ),
        Scenario(
            name="Göbeklitepe Macerası",
            description="Dünyanın en eski tapınağı Göbeklitepe'de 12.000 yıllık bir gizemi çöz! Dev dikilitaşların hayvan kabartmaları canlanıyor.",
            thumbnail_url="",
            theme_key="gobeklitepe",
            display_order=3,
        ),
        Scenario(
            name="Efes Antik Kent Macerası",
            description="Antik dünyanın en görkemli şehri Efes'te 2.000 yıllık bir maceraya atıl! Celsus Kütüphanesi'nin bilgelik heykelleri canlanıyor.",
            thumbnail_url="",
            theme_key="ephesus",
            display_order=4,
        ),
        Scenario(
            name="Çatalhöyük Neolitik Kenti Macerası",
            description="İnsanlığın ilk şehrinde 9.000 yıllık bir maceraya atıl! Çatıdan girilen evler, canlanan duvar resimleri ve Ana Tanrıça'nın sırları.",
            thumbnail_url="",
            theme_key="catalhoyuk",
            display_order=5,
        ),
        Scenario(
            name="Sümela Manastırı Macerası",
            description="Karadeniz'in sisli ormanlarında, 1.200 metre yükseklikte kayalara oyulmuş gizemli manastırı keşfet!",
            thumbnail_url="",
            theme_key="sumela",
            display_order=6,
        ),
        Scenario(
            name="Sultanahmet Camii Macerası",
            description="İstanbul'un kalbinde 20.000 mavi İznik çinisiyle süslü Mavi Camii'de büyülü bir macera!",
            thumbnail_url="",
            theme_key="sultanahmet",
            display_order=7,
        ),
        Scenario(
            name="Galata Kulesi Macerası",
            description="İstanbul'un 700 yıllık gözetleme kulesinde 67 metre yükseklikte büyülü bir macera! Spiral merdivende zaman yolculuğu ve 360° İstanbul panoraması.",
            thumbnail_url="",
            theme_key="galata",
            display_order=8,
        ),
        Scenario(
            name="Kudüs Eski Şehir Macerası",
            description="UNESCO Dünya Mirası surlarla çevrili antik şehirde büyülü bir macera! 5.000 yıllık taş sokaklarda zaman yolculuğu ve kültürlerin mozaiği.",
            thumbnail_url="",
            theme_key="kudus",
            display_order=9,
        ),
        Scenario(
            name="Abu Simbel Tapınakları Macerası",
            description="Antik Mısır'ın en görkemli tapınağında 3.000 yıllık bir macera! 20 metrelik dev firavun heykelleri ve güneş ışığının sırrı.",
            thumbnail_url="",
            theme_key="abusimbel",
            display_order=10,
        ),
        Scenario(
            name="Tac Mahal Macerası",
            description="Dünyanın en güzel anıtında beyaz mermer ve yarı değerli taşlarla süslü büyülü bir macera! Simetrinin, sabrın ve sevginin sırrı.",
            thumbnail_url="",
            theme_key="tacmahal",
            display_order=11,
        ),
    ]

    for scenario in scenarios:
        db.add(scenario)
    print(f"[OK] {len(scenarios)} scenarios created")


async def seed_learning_outcomes(db: AsyncSession) -> None:
    """Learning outcomes are removed."""
    print("[SKIP] Learning outcomes removed")


async def seed_visual_styles(db: AsyncSession) -> None:
    """Visual styles are managed via admin panel (/admin/visual-styles).

    This seed function is intentionally a no-op. Styles are configured
    through the admin UI where prompt_modifier, id_weight, true_cfg,
    and other parameters can be fine-tuned per style.

    If you need initial styles, use:
        python -m scripts.update_visual_styles
    """
    print("[SKIP] Visual styles managed via admin panel — use /admin/visual-styles")



async def seed_all() -> None:
    """Run all seed functions."""
    print("\n[SEED] Starting database seeding...\n")

    async with async_session_factory() as db:
        await seed_users(db)
        templates = await seed_page_templates(db)
        await seed_products(db, templates)
        await seed_scenarios(db)
        await seed_learning_outcomes(db)
        await seed_visual_styles(db)

        await db.commit()

    print("\n[DONE] Database seeding completed!\n")


if __name__ == "__main__":
    asyncio.run(seed_all())
