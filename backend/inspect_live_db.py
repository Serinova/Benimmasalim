import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

DATABASE_URL = "postgresql+asyncpg://postgres:BnmMsl2026ProdDB%21@127.0.0.1:5433/benimmasalim"

async def inspect_db():
    print("Baglaniliyor...")
    engine = create_async_engine(DATABASE_URL)
    try:
        async with engine.connect() as conn:
            print("Baglandi! Tablolar getiriliyor...")
            result = await conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
            tables = [row[0] for row in result]
            print(f"Buldunan tablolar ({len(tables)}):")
            for t in tables:
                print(f" - {t}")
                
            # Tablo verilerinden biraz istatistik
            if "orders" in tables:
                count = await conn.execute(text("SELECT count(*) FROM orders"))
                print(f"\nToplam Siparis (orders) sayisi: {count.scalar()}")
                
            if "users" in tables:
                count = await conn.execute(text("SELECT count(*) FROM users"))
                print(f"Toplam Kullanici (users) sayisi: {count.scalar()}")
                
            if "scenarios" in tables:
                count = await conn.execute(text("SELECT count(*) FROM scenarios"))
                print(f"Toplam Senaryo (scenarios) sayisi: {count.scalar()}")
                
    except Exception as e:
        print(f"Hata: {e}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(inspect_db())
