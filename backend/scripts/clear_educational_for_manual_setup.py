"""Eğitsel prompt şablonlarını ve kazanımları siler. Manuel ekleyecekseniz bu script'i bir kez çalıştırın.

- prompt_templates: category='educational' olan tüm kayıtlar silinir.
- learning_outcomes: Tüm kazanımlar silinir.

Manuel eklediğiniz kazanımlar ve eğitsel şablonlar hikaye üretiminde kullanılır (gemini_service zaten DB'den okuyor).

Çalıştırma:
  Bilgisayardan (localhost DB):  py -m scripts.clear_educational_for_manual_setup
  Docker (container DB):         docker exec benimmasalim-backend python -m scripts.clear_educational_for_manual_setup
                                (önce bir kez: docker compose build backend)
"""

import asyncio

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_factory
from app.models.learning_outcome import LearningOutcome
from app.models.prompt_template import PromptTemplate


async def clear_educational() -> None:
    async with async_session_factory() as db:
        # 1. Eğitsel prompt şablonları sayısı ve sil
        r = await db.execute(select(PromptTemplate).where(PromptTemplate.category == "educational"))
        prompt_list = r.scalars().all()
        prompt_count = len(prompt_list)
        for p in prompt_list:
            await db.delete(p)

        # 2. Kazanımlar sayısı ve sil
        r2 = await db.execute(select(LearningOutcome))
        outcome_list = r2.scalars().all()
        outcome_count = len(outcome_list)
        for o in outcome_list:
            await db.delete(o)

        await db.commit()
        print(f"[OK] Silindi: {prompt_count} eğitsel prompt şablonu, {outcome_count} kazanım.")
        print("    Admin panelden manuel eklediğiniz kazanımlar ve şablonlar hikayede kullanılacak.")


if __name__ == "__main__":
    asyncio.run(clear_educational())
