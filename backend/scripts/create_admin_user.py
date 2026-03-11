"""Sadece admin kullanıcısı oluşturur. Veritabanı boşken veya yeni kurulumda kullanın.

Kullanım:
    python scripts/create_admin_user.py
    (Parola interactive olarak sorulur)
"""

import asyncio
import getpass
import sys
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_factory
from app.core.security import get_password_hash
from app.models.user import User, UserRole

ADMIN_EMAIL = "admin@benimmasalim.com"


async def create_admin() -> None:
    # Interactive parola girişi
    password = getpass.getpass(f"Admin parolası girin ({ADMIN_EMAIL}): ")
    if len(password) < 8:
        print("[ERROR] Parola en az 8 karakter olmalıdır.", file=sys.stderr)
        sys.exit(1)

    password_confirm = getpass.getpass("Parolayı tekrar girin: ")
    if password != password_confirm:
        print("[ERROR] Parolalar eşleşmiyor.", file=sys.stderr)
        sys.exit(1)

    async with async_session_factory() as db:
        result = await db.execute(select(User).where(User.email == ADMIN_EMAIL))
        existing = result.scalar_one_or_none()
        if existing:
            print(f"[OK] Admin zaten mevcut: {ADMIN_EMAIL}")
            return
        admin = User(
            id=uuid.uuid4(),
            email=ADMIN_EMAIL,
            hashed_password=get_password_hash(password),
            full_name="Admin User",
            role=UserRole.ADMIN,
            is_active=True,
        )
        db.add(admin)
        await db.commit()
        print(f"[OK] Admin oluşturuldu: {ADMIN_EMAIL}")


if __name__ == "__main__":
    asyncio.run(create_admin())
