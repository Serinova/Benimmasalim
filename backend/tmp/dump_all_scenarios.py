"""Dump ALL scenario data from DB to a single file for migration planning."""
import asyncio, json, os
from dotenv import load_dotenv
load_dotenv(override=True)
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

engine = create_async_engine(os.getenv('DATABASE_URL'))

FIELDS = [
    "id", "name", "theme_key", "description", "is_active", "display_order",
    "story_prompt_tr", "cover_prompt_template", "page_prompt_template",
    "outfit_girl", "outfit_boy",
    "scenario_bible::text as scenario_bible",
    "cultural_elements::text as cultural_elements",
    "custom_inputs_schema::text as custom_inputs_schema",
    "location_constraints", "location_en",
    "flags::text as flags",
    "default_page_count",
    "ai_prompt_template",
    # Marketing
    "thumbnail_url", "tagline", "marketing_badge", "age_range",
    "estimated_duration", "rating", "review_count",
    "marketing_price_label",
    "linked_product_id::text as linked_product_id",
    # Book structure
    "story_page_count", "cover_count", "greeting_page_count", "back_info_page_count",
]

async def dump():
    async with engine.connect() as conn:
        r = await conn.execute(text(f"SELECT {', '.join(FIELDS)} FROM scenarios ORDER BY display_order"))
        rows = r.fetchall()
        keys = r.keys()
        
        data = []
        for row in rows:
            d = dict(zip(keys, row))
            # Parse JSON fields
            for jf in ['scenario_bible', 'cultural_elements', 'custom_inputs_schema', 'flags']:
                if d.get(jf) and isinstance(d[jf], str):
                    try:
                        d[jf] = json.loads(d[jf])
                    except:
                        pass
            data.append(d)
        
        with open('tmp/all_scenarios_dump.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"Dumped {len(data)} scenarios")
        for d in data:
            active = "Y" if d['is_active'] else "N"
            prompt_len = len(d.get('story_prompt_tr') or '')
            tk = str(d.get('theme_key') or 'NONE')
            nm = str(d.get('name') or 'NONE')
            print(f"  {active} {tk:20s} | {nm:40s} | prompt={prompt_len} chars")
    
    await engine.dispose()

asyncio.run(dump())
