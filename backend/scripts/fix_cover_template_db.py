"""DB'deki COVER_TEMPLATE prompt kaydını güncelle - metin talimatını kaldır.

AI artık kapak resmine metin yazmayacak, başlık page_composer tarafından eklenir.
Hem content hem template_en sütunları güncellenir.

Çalıştırma:
    python -m scripts.fix_cover_template_db
"""
import asyncio
from sqlalchemy import text
from app.core.database import async_session_factory
from app.prompt_engine.constants import DEFAULT_COVER_TEMPLATE_EN


async def main():
    async with async_session_factory() as s:
        # Mevcut COVER_TEMPLATE kaydını oku (tüm sütunlar)
        result = await s.execute(text(
            "SELECT id, content, template_en FROM prompt_templates WHERE key = 'COVER_TEMPLATE'"
        ))
        row = result.fetchone()
        if row:
            old_content = row[1] or ""
            old_template_en = row[2] or ""
            print(f"[ESKI content] ({len(old_content)} chars): {old_content[:200]}")
            print(f"[ESKI template_en] ({len(old_template_en)} chars): {old_template_en[:200]}")

            new_en = DEFAULT_COVER_TEMPLATE_EN
            # TR versiyonu da metin yazdırmasın
            new_tr = (
                "Küçük bir çocuk {clothing_description} giyiyor. {scene_description}. "
                "Resmin üst kısmında temiz gökyüzü/arkaplan, resimde metin yok, harf yok, yazı yok."
            )
            print(f"\n[YENİ content] ({len(new_tr)} chars): {new_tr}")
            print(f"[YENİ template_en] ({len(new_en)} chars): {new_en}")

            await s.execute(text(
                "UPDATE prompt_templates "
                "SET content = :content, template_en = :template_en "
                "WHERE key = 'COVER_TEMPLATE'"
            ), {"content": new_tr, "template_en": new_en})
            await s.commit()
            print("\n[OK] COVER_TEMPLATE content + template_en güncellendi.")
        else:
            print("[SKIP] DB'de COVER_TEMPLATE kaydı bulunamadı (fallback kullanılır).")


if __name__ == "__main__":
    asyncio.run(main())
