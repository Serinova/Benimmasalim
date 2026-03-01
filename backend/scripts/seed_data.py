"""Seed initial data for development and testing."""

import asyncio
import uuid
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_factory
from app.core.security import get_password_hash
from app.models.book_template import PageTemplate, PageType
from app.models.learning_outcome import LearningOutcome
from app.models.product import Product
from app.models.scenario import Scenario
from app.models.user import User, UserRole
from app.models.visual_style import VisualStyle


async def seed_users(db: AsyncSession) -> None:
    """Create default admin user."""
    admin = User(
        id=uuid.uuid4(),
        email="admin@benimmasalim.com",
        hashed_password=get_password_hash("admin123"),
        full_name="Admin User",
        role=UserRole.ADMIN,
        is_active=True,
    )
    db.add(admin)
    print("[OK] Admin user created: admin@benimmasalim.com / admin123")


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
    """Create categorized learning outcomes with AI prompts."""
    outcomes = [
        # ===== Öz Bakım (Self Care) =====
        LearningOutcome(
            name="Temizlik ve Düzen",
            description="Kendi çevresini temiz tutmak",
            category="SelfCare",
            category_label="Öz Bakım",
            ai_prompt="Hikayede karakter bulunduğu çevreyi ve kişisel eşyalarını temiz, düzenli tutmanın ona huzur ve başarı getirdiğini fark etsin.",
            display_order=1,
        ),
        LearningOutcome(
            name="Sağlıklı Beslenme",
            description="Sebze ve meyve yemenin faydaları",
            category="SelfCare",
            category_label="Öz Bakım",
            ai_prompt="Hikayede karakter sebze yemenin ona süper güç verdiğini keşfetsin ve sağlıklı beslenmeyi sevsin.",
            display_order=2,
        ),
        LearningOutcome(
            name="Düzenli Uyku",
            description="Vaktinde uyumanın önemi",
            category="SelfCare",
            category_label="Öz Bakım",
            ai_prompt="Hikayede karakter vaktinde uyumanın rüyalara açılan büyülü bir kapı olduğunu anlasın.",
            display_order=3,
        ),
        LearningOutcome(
            name="Sorumluluk Bilinci",
            description="Kendi görevlerini yerine getirmek",
            category="SelfCare",
            category_label="Öz Bakım",
            ai_prompt="Hikayede karakter kendi kararlarını alıp sonuçlarına sahip çıkmanın ve sorumluluk almanın onu nasıl büyüttüğünü görsün.",
            display_order=4,
        ),
        LearningOutcome(
            name="El Yıkama ve Hijyen",
            description="Temizlik alışkanlıkları",
            category="SelfCare",
            category_label="Öz Bakım",
            ai_prompt="Hikayede karakter mikroplardan korunmak için el yıkamanın önemini öğrensin ve bunu alışkanlık haline getirsin.",
            display_order=5,
        ),

        # ===== Kişisel Gelişim & Duygusal (Personal Growth) =====
        LearningOutcome(
            name="Cesaret ve Özgüven",
            description="Korkuları yenmek ve kendine güvenmek",
            category="PersonalGrowth",
            category_label="Kişisel Gelişim",
            ai_prompt="Hikayede karakter korktuğu bir şeyin üstüne gitsin ve cesaretinin onu başarıya götürdüğünü görsün.",
            display_order=1,
        ),
        LearningOutcome(
            name="Sabırlı Olmak",
            description="Beklemenin güzelliğini öğrenmek",
            category="PersonalGrowth",
            category_label="Kişisel Gelişim",
            ai_prompt="Hikayede karakter istediği bir şey için beklemenin güzelliğini öğrensin ve sabrın ödüllendirildiğini görsün.",
            display_order=2,
        ),
        LearningOutcome(
            name="Hata Yapmaktan Korkmamak",
            description="Hatalardan öğrenmek",
            category="PersonalGrowth",
            category_label="Kişisel Gelişim",
            ai_prompt="Hikayede karakter hata yapmanın öğrenmenin doğal bir parçası olduğunu anlasın ve hatalarından ders çıkarsın.",
            display_order=3,
        ),
        LearningOutcome(
            name="Liderlik",
            description="Sorumluluk almak ve yol göstermek",
            category="PersonalGrowth",
            category_label="Kişisel Gelişim",
            ai_prompt="Hikayede karakter arkadaşlarına yol gösterip sorumluluk alsın ve lider olmanın güzelliğini keşfetsin.",
            display_order=4,
        ),
        LearningOutcome(
            name="Duygularını İfade Etme",
            description="Duygularını sağlıklı şekilde anlatmak",
            category="PersonalGrowth",
            category_label="Kişisel Gelişim",
            ai_prompt="Hikayede karakter üzüldüğünde veya kızdığında duygularını doğru şekilde ifade etmeyi öğrensin.",
            display_order=5,
        ),

        # ===== Sosyal Beceriler (Social Skills) =====
        LearningOutcome(
            name="Paylaşmak Güzeldir",
            description="Paylaşmanın mutluluğu",
            category="SocialSkills",
            category_label="Sosyal Beceriler",
            ai_prompt="Hikayede karakter oyuncağını veya yiyeceğini paylaşmanın mutluluğunu yaşasın ve paylaşınca daha çok sevdiğini görsün.",
            display_order=1,
        ),
        LearningOutcome(
            name="Özür Dilemek",
            description="Hata yapınca özür dilemenin önemi",
            category="SocialSkills",
            category_label="Sosyal Beceriler",
            ai_prompt="Hikayede karakter bir hata yaptığında özür dilemenin erdem olduğunu öğrensin ve ilişkilerini düzeltsin.",
            display_order=2,
        ),
        LearningOutcome(
            name="İş Birliği ve Takım Çalışması",
            description="Başkalarıyla uyum içinde çalışmak",
            category="SocialSkills",
            category_label="Sosyal Beceriler",
            ai_prompt="Hikayede karakter karşılaştığı zorlukları yalnız başına değil, oradaki bilge rehberle veya hayvan dostuyla iş birliği yaparak aşsın ve takım çalışmasının gücünü anlasın.",
            display_order=3,
        ),
        LearningOutcome(
            name="Yardımseverlik",
            description="Başkalarına yardım etmek",
            category="SocialSkills",
            category_label="Sosyal Beceriler",
            ai_prompt="Hikayede karakter zor durumdaki birine yardım etsin ve yardım etmenin verdiği mutluluğu yaşasın.",
            display_order=4,
        ),
        LearningOutcome(
            name="Arkadaşlık Kurmak",
            description="Yeni arkadaşlar edinmek",
            category="SocialSkills",
            category_label="Sosyal Beceriler",
            ai_prompt="Hikayede karakter yeni bir arkadaş edinsin ve arkadaşlığın nasıl kurulup büyütüldüğünü öğrensin.",
            display_order=5,
        ),

        # ===== Eğitim & Çevre (Education & Nature) =====
        LearningOutcome(
            name="Doğa ve Hayvan Sevgisi",
            description="Doğayı ve hayvanları korumak",
            category="EducationNature",
            category_label="Eğitim & Çevre",
            ai_prompt="Hikayede karakter doğayı korumayı ve hayvanlara nazik davranmayı öğrensin.",
            display_order=1,
        ),
        LearningOutcome(
            name="Kitap Okuma Sevgisi",
            description="Kitapların büyülü dünyası",
            category="EducationNature",
            category_label="Eğitim & Çevre",
            ai_prompt="Hikayede karakter kitapların içindeki büyülü dünyayı keşfetsin ve okumayı sevsin.",
            display_order=2,
        ),
        LearningOutcome(
            name="Ekran Süresi Dengesi",
            description="Tablet/TV dışında aktiviteler",
            category="EducationNature",
            category_label="Eğitim & Çevre",
            ai_prompt="Hikayede karakter tablet ve TV dışında oyun oynamanın daha eğlenceli olduğunu fark etsin.",
            display_order=3,
        ),
        LearningOutcome(
            name="Merak ve Keşfetmek",
            description="Soru sorma ve öğrenme isteği",
            category="EducationNature",
            category_label="Eğitim & Çevre",
            ai_prompt="Hikayede karakter meraklı sorular sorsun ve yeni şeyler keşfetmenin heyecanını yaşasın.",
            display_order=4,
        ),
        LearningOutcome(
            name="Çevre Temizliği",
            description="Çöpleri doğru yere atmak",
            category="EducationNature",
            category_label="Eğitim & Çevre",
            ai_prompt="Hikayede karakter çevreyi temiz tutmanın önemini öğrensin ve çöpleri doğru yere atmayı alışkanlık haline getirsin.",
            display_order=5,
        ),
    ]

    for outcome in outcomes:
        db.add(outcome)
    print(f"[OK] {len(outcomes)} learning outcomes created (4 categories)")


async def seed_visual_styles(db: AsyncSession) -> None:
    """
    Create default visual styles.
    
    OPTIMIZED FOR FAL.AI FLUX:
    - Natural sentence format (not comma-separated tags)
    - Describes illustration STYLE only (not content)
    - PuLID handles face from photo, clothing added separately
    """
    # Yalnızca aktif 7 stil — DB ile birebir eşleşir.
    styles = [
        VisualStyle(
            name="2D CHILDREN'S BOOK STYLE (Likeness-first, NOT big eyes) + NEGATIVE (copy/paste)",
            thumbnail_url="",
            prompt_modifier="Warm cheerful 2D hand-painted storybook illustration, vibrant yet soft color palette with cheerful hues, smooth soft shading",
            cover_aspect_ratio="3:2",
            page_aspect_ratio="3:2",
        ),
        VisualStyle(
            name="3D Pixar-ish (daha 3D, ama hâlâ çocuk kitabı)",
            thumbnail_url="",
            prompt_modifier="cinematic 3D animation style, Disney Pixar quality, warm lighting, vibrant colors",
            cover_aspect_ratio="3:2",
            page_aspect_ratio="3:2",
        ),
        VisualStyle(
            name="Adventure Digital (Macera Dijital Boyama)",
            thumbnail_url="",
            prompt_modifier="adventure digital painting style, vibrant warm colors, painterly rendering, bright natural lighting, rich saturated colors",
            cover_aspect_ratio="3:2",
            page_aspect_ratio="3:2",
        ),
        VisualStyle(
            name="Default Storybook (örneğe en yakın)",
            thumbnail_url="",
            prompt_modifier="2D children's storybook illustration, classic picture-book style, vibrant cheerful colors",
            cover_aspect_ratio="3:2",
            page_aspect_ratio="3:2",
        ),
        VisualStyle(
            name="Ghibli-ish (anime dokusu, çok yumuşak)",
            thumbnail_url="",
            prompt_modifier="Studio Ghibli anime style, cel-shaded, peaceful nature, magical atmosphere, soft colors",
            cover_aspect_ratio="3:2",
            page_aspect_ratio="3:2",
        ),
        VisualStyle(
            name="Watercolor Storybook",
            thumbnail_url="",
            prompt_modifier="watercolor illustration style, soft edges, pastel colors, dreamy children's book atmosphere",
            cover_aspect_ratio="3:2",
            page_aspect_ratio="3:2",
        ),
        VisualStyle(
            name="Yumuşak Pastel",
            thumbnail_url="",
            prompt_modifier="soft pastel storybook illustration, gentle hand-drawn lines, warm muted colors (beige, cream, soft coral), warm magical atmosphere, dreamy softness",
            cover_aspect_ratio="3:2",
            page_aspect_ratio="3:2",
        ),
    ]

    # Duplicate koruması: aynı isimle zaten varsa ekleme (idempotent)
    from sqlalchemy import select as _sel
    existing_names_q = await db.execute(_sel(VisualStyle.name))
    existing_names = {row[0] for row in existing_names_q.all()}

    added = 0
    for style in styles:
        if style.name not in existing_names:
            db.add(style)
            added += 1
        else:
            print(f"  [SKIP] Visual style '{style.name}' already exists")
    print(f"[OK] {added}/{len(styles)} visual styles created (Flux-optimized, {len(styles) - added} skipped)")


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
