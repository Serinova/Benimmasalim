"""Extract key data for each remaining scenario."""
import json

data = json.load(open('tmp/all_scenarios_dump.json', 'r', encoding='utf-8'))
done = {'cappadocia', 'umre_pilgrimage'}

for d in data:
    tk = d.get('theme_key') or 'NONE'
    if tk in done:
        continue
    fname = f'tmp/sc_{tk}.txt'
    with open(fname, 'w', encoding='utf-8') as f:
        f.write(f"theme_key: {tk}\n")
        f.write(f"name: {d['name']}\n")
        f.write(f"location_en: {d.get('location_en', '')}\n")
        f.write(f"active: {d['is_active']}\n")
        flags = d.get('flags') or {}
        f.write(f"no_family: {flags.get('no_family', False)}\n")
        f.write(f"page_count: {d.get('default_page_count', 22)}\n\n")
        f.write(f"--- OUTFIT GIRL ---\n{d.get('outfit_girl', '')}\n\n")
        f.write(f"--- OUTFIT BOY ---\n{d.get('outfit_boy', '')}\n\n")
        cis = d.get('custom_inputs_schema') or []
        f.write(f"--- CUSTOM INPUTS ---\n{json.dumps(cis, ensure_ascii=False, indent=2)}\n\n")
        ce = d.get('cultural_elements') or {}
        f.write(f"--- CULTURAL ELEMENTS ---\n{json.dumps(ce, ensure_ascii=False, indent=2)}\n\n")
        f.write(f"--- LOCATION CONSTRAINTS ---\n{d.get('location_constraints', '')}\n\n")
        sb = d.get('scenario_bible') or {}
        f.write(f"--- SCENARIO BIBLE ---\n{json.dumps(sb, ensure_ascii=False, indent=2)}\n\n")
        spt = d.get('story_prompt_tr') or ''
        f.write(f"--- COVER PROMPT ---\n{d.get('cover_prompt_template', '')}\n\n")
        f.write(f"--- PAGE PROMPT ---\n{d.get('page_prompt_template', '')}\n\n")
        f.write(f"--- STORY PROMPT TR ---\n{spt}\n")
    print(f"Wrote {fname} ({len(spt)} chars prompt)")

print("Done")
