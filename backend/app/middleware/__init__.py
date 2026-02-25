"""Middleware module for FastAPI application."""

from app.middleware.rate_limiter import RateLimitMiddleware

__all__ = ["RateLimitMiddleware"]
