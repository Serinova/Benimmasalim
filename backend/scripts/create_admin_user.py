"""Sadece admin kullanıcısı oluşturur. Veritabanı boşken veya yeni kurulumda kullanın."""

import asyncio
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_factory
from app.core.security import get_password_hash
from app.models.user import User, UserRole

ADMIN_EMAIL = "admin@benimmasalim.com"
ADMIN_PASSWORD = "admin123"


async def create_admin() -> None:
    async with async_session_factory() as db:
        result = await db.execute(select(User).where(User.email == ADMIN_EMAIL))
        existing = result.scalar_one_or_none()
        if existing:
            print(f"[OK] Admin zaten mevcut: {ADMIN_EMAIL}")
            return
        admin = User(
            id=uuid.uuid4(),
            email=ADMIN_EMAIL,
            hashed_password=get_password_hash(ADMIN_PASSWORD),
            full_name="Admin User",
            role=UserRole.ADMIN,
            is_active=True,
        )
        db.add(admin)
        await db.commit()
        print(f"[OK] Admin oluşturuldu: {ADMIN_EMAIL} / {ADMIN_PASSWORD}")


if __name__ == "__main__":
    asyncio.run(create_admin())
