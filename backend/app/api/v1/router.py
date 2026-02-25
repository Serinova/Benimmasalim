"""API v1 main router."""

from fastapi import APIRouter

from app.api.v1 import (
    ai,
    audio,
    auth,
    consent,
    data_request,
    homepage,
    leads,
    orders,
    payments,
    products,
    scenarios,
    trials,
    webhooks,
)
from app.api.v1.admin import router as admin_router

api_router = APIRouter()

# Public endpoints
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(consent.router, prefix="/consent", tags=["Consent (KVKK)"])
api_router.include_router(data_request.router, prefix="/data-request", tags=["Data Request (KVKK)"])
api_router.include_router(leads.router, prefix="/leads", tags=["Lead Capture"])
api_router.include_router(trials.router, prefix="/trials", tags=["Try Before You Buy"])
api_router.include_router(products.router, prefix="/products", tags=["Products"])
api_router.include_router(scenarios.router, prefix="/scenarios", tags=["Scenarios"])
api_router.include_router(orders.router, prefix="/orders", tags=["Orders"])
api_router.include_router(ai.router, prefix="/ai", tags=["AI Services"])
api_router.include_router(payments.router, prefix="/payments", tags=["Payments"])
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["Webhooks"])
api_router.include_router(audio.router, prefix="/audio", tags=["Audio"])
api_router.include_router(homepage.router, prefix="/homepage", tags=["Homepage"])

# Admin endpoints
api_router.include_router(admin_router, prefix="/admin", tags=["Admin"])
