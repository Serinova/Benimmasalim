"""DB'deki cover prompt template kaydını kontrol et."""
import asyncio
from sqlalchemy import text
from app.core.database import async_session_factory


async def main():
    async with async_session_factory() as s:
        # prompt_templates tablosu
        result = await s.execute(text(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema='public' AND table_name LIKE '%prompt%'"
        ))
        tables = [r[0] for r in result.fetchall()]
        print("Prompt tables:", tables)

        for t in tables:
            result2 = await s.execute(text(f"SELECT * FROM {t} LIMIT 10"))
            rows = result2.fetchall()
            print(f"\n--- {t} ({len(rows)} rows) ---")
            for r in rows:
                print(r)

        # Ayrıca Scenario tablosundan cover prompt'ları kontrol et
        result3 = await s.execute(text(
            "SELECT name, LEFT(cover_prompt_template, 300) FROM scenarios"
        ))
        print("\n=== Scenario cover prompts ===")
        for r in result3.fetchall():
            print(f"  {r[0]}: {r[1]}")

        # generate_consistent_image'ın template_en parametresini kontrol için
        # prompt_template_service'in ne döndüğünü test et
        from app.services.prompt_template_service import get_prompt_service
        from app.prompt_engine.constants import DEFAULT_COVER_TEMPLATE_EN
        svc = get_prompt_service()
        tpl = await svc.get_template_en(s, "COVER_TEMPLATE", DEFAULT_COVER_TEMPLATE_EN)
        print(f"\n=== prompt_template_service COVER_TEMPLATE ===")
        print(f"  Result ({len(tpl)} chars): {tpl}")

if __name__ == "__main__":
    asyncio.run(main())
