"""Admin API module."""

from fastapi import APIRouter

from app.api.v1.admin import (
    abandoned_trials,
    accounting,
    back_cover,
    book_config,
    coloring_books,
    homepage,
    kvkk,
    orders,
    products,
    promo_codes,
    prompts,
    rate_limit,
    scenarios,
    seed_coloring,
    settings,
    users,
    visual_styles,
)

router = APIRouter()

router.include_router(orders.router, prefix="/orders", tags=["Admin - Orders"])
router.include_router(products.router, prefix="/products", tags=["Admin - Products"])
router.include_router(users.router, prefix="/users", tags=["Admin - Users"])
router.include_router(book_config.router, prefix="/book-config", tags=["Admin - Book Config"])
router.include_router(scenarios.router, prefix="/scenarios", tags=["Admin - Scenarios"])
router.include_router(back_cover.router, prefix="/back-cover", tags=["Admin - Back Cover"])
router.include_router(visual_styles.router, prefix="/visual-styles", tags=["Admin - Visual Styles"])
router.include_router(coloring_books.router, tags=["Admin - Coloring Books"])
router.include_router(kvkk.router, prefix="/kvkk", tags=["Admin - KVKK"])
router.include_router(prompts.router, prefix="/prompts", tags=["Admin - Prompts"])
router.include_router(abandoned_trials.router, prefix="/trials", tags=["Admin - Trials"])
router.include_router(
    promo_codes.router, prefix="/promo-codes", tags=["Admin - Promo Codes"]
)
router.include_router(homepage.router, prefix="/homepage", tags=["Admin - Homepage"])
router.include_router(rate_limit.router, prefix="/rate-limit", tags=["Admin - Rate Limit"])
router.include_router(seed_coloring.router, tags=["Admin - Seed"])
router.include_router(settings.router, prefix="/settings", tags=["Admin - Settings"])
router.include_router(accounting.router, prefix="/accounting", tags=["Admin - Accounting"])
