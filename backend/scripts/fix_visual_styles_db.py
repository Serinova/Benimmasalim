import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from sqlalchemy import select
from app.core.database import async_session_factory
from app.models.visual_style import VisualStyle

async def fix_styles():
    async with async_session_factory() as session:
        result = await session.execute(select(VisualStyle))
        styles = result.scalars().all()
        
        for style in styles:
            if 'Watercolor' in style.name:
                print(f"Eski Watercolor: {style.prompt_modifier}")
                style.prompt_modifier = "beautiful watercolor painting, 2D children's storybook illustration, soft brush strokes, vibrant cheerful colors, hand-painted warmth, dreamy atmosphere"
                print(f"Yeni Watercolor: {style.prompt_modifier}")
            
            if 'Adventure' in style.name and style.style_negative_en:
                if style.style_negative_en.startswith('“'):
                    print(f"Eski Adventure Negatif Başlangıcı: {style.style_negative_en[:20]}")
                    style.style_negative_en = style.style_negative_en.lstrip('“')
                    print(f"Yeni Adventure Negatif Başlangıcı: {style.style_negative_en[:20]}")
        
        await session.commit()
        print("Visual Styles başarıyla düzeltildi!")

if __name__ == "__main__":
    asyncio.run(fix_styles())
