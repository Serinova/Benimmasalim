"""Database configuration and session management."""

import ssl
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


def _build_connect_args() -> dict:
    """Build connection arguments — adds SSL in production."""
    args: dict = {
        "command_timeout": 30,  # 30s statement timeout — prevents runaway queries
    }
    # Cloud SQL Proxy handles TLS termination, so direct SSL is only needed
    # when connecting to a remote DB without the proxy.
    if settings.is_production and "cloudsql" not in str(settings.database_url):
        ssl_ctx = ssl.create_default_context()  # noqa: S501
        # Cloud SQL server certs are Google-signed; for external DBs, keep defaults.
        args["ssl"] = ssl_ctx
    return args


# Create async engine
engine = create_async_engine(
    str(settings.database_url),
    echo=settings.db_echo,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_pre_ping=True,
    pool_timeout=10,    # Fail fast instead of waiting 30s (default) when pool exhausted
    pool_recycle=1800,  # Recycle connections every 30 min to avoid stale connections
    connect_args=_build_connect_args(),
)

# Session factory
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency that provides a database session.

    Usage in routes:
        @router.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
