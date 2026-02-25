"""
Kapadokya Macerası ile kayıtlı tüm stillerin görsel prompt'larını üretir ve
karşılaştırma raporu yazar. Proje .env'deki DATABASE_URL kullanılır.

Kullanım (backend klasöründen):
  python scripts/compare_prompts_kapadokya.py

Çıktı: backend/tests/output/prompt_comparison_kapadokya_<timestamp>.md
"""

from __future__ import annotations

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

# Backend root'u path'e ekle
BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

os.chdir(BACKEND_ROOT)

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models.visual_style import VisualStyle
from app.prompt_engine.constants import (
    DEFAULT_COVER_TEMPLATE_EN,
    DEFAULT_INNER_TEMPLATE_EN,
)
from app.prompt_engine.visual_prompt_composer import compose_visual_prompt
from app.services.prompt_template_service import PromptTemplateService

# Kapadokya sahneleri. Işık gerçek akışta Gemini tarafından eklenir.
KAPADOKYA_INNER_SCENE = "exploring fairy chimneys with hot air balloons in the sky."
KAPADOKYA_COVER_SCENE = (
    "standing on a hill overlooking Cappadocia with fairy chimneys and hot air balloons in the sky."
)
CLOTHING = "turquoise t-shirt, denim shorts, brown hiking boots"
CHILD_AGE = 9


def _write_md(results: list[dict], out_path: Path) -> None:
    lines = [
        "# Kapadokya Macerası — Stil Bazlı Görsel Prompt Karşılaştırması",
        "",
        f"Üretim tarihi: {datetime.now().isoformat()}",
        f"Stil sayısı: {len(results)}",
        "",
        "---",
        "",
    ]
    for i, r in enumerate(results, 1):
        name = r["style_name"]
        lines.append(f"## {i}. {name}")
        lines.append("")
        lines.append("### İç sayfa (inner) — final_prompt")
        lines.append("```")
        lines.append(r["inner_final_prompt"])
        lines.append("```")
        lines.append("")
        lines.append("### İç sayfa — negative_prompt (ilk 1200 karakter)")
        lines.append("```")
        neg = r["inner_negative_prompt"]
        lines.append(neg[:1200] + ("..." if len(neg) > 1200 else ""))
        lines.append("```")
        lines.append("")
        lines.append("### Kapak (cover) — final_prompt")
        lines.append("```")
        lines.append(r["cover_final_prompt"])
        lines.append("```")
        lines.append("")
        lines.append("### Kapak — negative_prompt (ilk 800 karakter)")
        lines.append("```")
        neg_c = r["cover_negative_prompt"]
        lines.append(neg_c[:800] + ("..." if len(neg_c) > 800 else ""))
        lines.append("```")
        lines.append("")
        lines.append("---")
        lines.append("")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Rapor yazıldı: {out_path}")


async def main() -> None:
    from app.config import settings

    database_url = str(settings.database_url)
    if "test" in database_url:
        print("Uyarı: test DB kullanılıyor. Gerçek stiller için .env'de DATABASE_URL'ü proje DB'ye ayarlayın.")

    engine = create_async_engine(database_url, pool_pre_ping=True)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Stiller
        result = await session.execute(
            select(VisualStyle).where(VisualStyle.is_active == True).order_by(VisualStyle.name)
        )
        styles = result.scalars().all()
        if not styles:
            print("DB'de aktif VisualStyle bulunamadı. Çıkılıyor.")
            return

        # Şablonlar
        tpl_svc = PromptTemplateService()
        inner_tpl = await tpl_svc.get_template_en(
            session, "INNER_TEMPLATE", DEFAULT_INNER_TEMPLATE_EN
        )
        cover_tpl = await tpl_svc.get_template_en(
            session, "COVER_TEMPLATE", DEFAULT_COVER_TEMPLATE_EN
        )

        results = []
        for s in styles:
            name = s.name
            style_prompt_en = s.prompt_modifier or name
            style_negative_en = (s.style_negative_en or "").strip()

            inner_final, inner_neg = compose_visual_prompt(
                scene_description=KAPADOKYA_INNER_SCENE,
                is_cover=False,
                template_en=inner_tpl,
                clothing_description=CLOTHING,
                child_age=CHILD_AGE,
                style_prompt_en=style_prompt_en,
                style_negative_en=style_negative_en,
            )
            cover_final, cover_neg = compose_visual_prompt(
                scene_description=KAPADOKYA_COVER_SCENE,
                is_cover=True,
                template_en=cover_tpl,
                clothing_description=CLOTHING,
                child_age=CHILD_AGE,
                style_prompt_en=style_prompt_en,
                style_negative_en=style_negative_en,
            )
            results.append({
                "style_name": name,
                "inner_final_prompt": inner_final,
                "inner_negative_prompt": inner_neg,
                "cover_final_prompt": cover_final,
                "cover_negative_prompt": cover_neg,
            })

    out_dir = BACKEND_ROOT / "tests" / "output"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = out_dir / f"prompt_comparison_kapadokya_{timestamp}.md"
    _write_md(results, out_path)
    print(f"Toplam {len(results)} stil karşılaştırıldı.")


if __name__ == "__main__":
    asyncio.run(main())
