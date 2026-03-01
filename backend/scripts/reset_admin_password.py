"""Admin kullanıcısının şifresini sıfırlar. Production'da sadece bir kez kullanılır."""

import asyncio
import sys
import os

# Ensure /app is in the Python path (required when running from /app/scripts/)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import select, update

from app.core.security import get_password_hash
from app.db.session import async_session_factory
from app.models.user import User

ADMIN_EMAIL = "admin@benimmasalim.com"
NEW_PASSWORD = "Admin123!"


async def reset_password() -> None:
    async with async_session_factory() as db:
        result = await db.execute(select(User).where(User.email == ADMIN_EMAIL))
        user = result.scalar_one_or_none()

        if not user:
            print(f"[ERROR] Admin kullanıcısı bulunamadı: {ADMIN_EMAIL}", file=sys.stderr)
            sys.exit(1)

        new_hash = get_password_hash(NEW_PASSWORD)
        await db.execute(
            update(User).where(User.email == ADMIN_EMAIL).values(hashed_password=new_hash)
        )
        await db.commit()
        print(f"[OK] Admin şifresi sıfırlandı: {ADMIN_EMAIL} → {NEW_PASSWORD}")


if __name__ == "__main__":
    asyncio.run(reset_password())
