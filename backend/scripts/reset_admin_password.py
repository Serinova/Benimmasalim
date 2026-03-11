"""Admin kullanıcısının şifresini sıfırlar.

Kullanım:
    python scripts/reset_admin_password.py
    (Yeni parola interactive olarak sorulur)
"""

import asyncio
import getpass
import os
import sys

# Ensure /app is in the Python path (required when running from /app/scripts/)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import select, update

from app.core.security import get_password_hash
from app.db.session import async_session_factory
from app.models.user import User

ADMIN_EMAIL = "admin@benimmasalim.com"


async def reset_password() -> None:
    # Interactive parola girişi
    new_password = getpass.getpass(f"Yeni admin parolası girin ({ADMIN_EMAIL}): ")
    if len(new_password) < 8:
        print("[ERROR] Parola en az 8 karakter olmalıdır.", file=sys.stderr)
        sys.exit(1)

    confirm = getpass.getpass("Parolayı tekrar girin: ")
    if new_password != confirm:
        print("[ERROR] Parolalar eşleşmiyor.", file=sys.stderr)
        sys.exit(1)

    async with async_session_factory() as db:
        result = await db.execute(select(User).where(User.email == ADMIN_EMAIL))
        user = result.scalar_one_or_none()

        if not user:
            print(f"[ERROR] Admin kullanıcısı bulunamadı: {ADMIN_EMAIL}", file=sys.stderr)
            sys.exit(1)

        new_hash = get_password_hash(new_password)
        await db.execute(
            update(User).where(User.email == ADMIN_EMAIL).values(hashed_password=new_hash)
        )
        await db.commit()
        print(f"[OK] Admin şifresi başarıyla sıfırlandı: {ADMIN_EMAIL}")


if __name__ == "__main__":
    asyncio.run(reset_password())
