import json

data = json.load(open('tmp/all_scenarios_dump.json', 'r', encoding='utf-8'))

with open('tmp/scenario_summary.txt', 'w', encoding='utf-8') as f:
    for d in data:
        tk = d.get('theme_key') or 'NONE'
        nm = d.get('name') or 'NONE'
        active = 'ACTIVE' if d.get('is_active') else 'PASSIVE'
        prompt_len = len(d.get('story_prompt_tr') or '')
        outfit_g = len(d.get('outfit_girl') or '')
        bible = 'YES' if d.get('scenario_bible') else 'NO'
        cis = d.get('custom_inputs_schema')
        has_companion = 'YES' if cis and len(cis) > 0 else 'NO'
        flags = d.get('flags') or {}
        no_fam = flags.get('no_family', False)
        loc = d.get('location_en') or ''
        page_count = d.get('default_page_count') or 6
        
        f.write(f"{'='*80}\n")
        f.write(f"theme_key: {tk}\n")
        f.write(f"name: {nm}\n")
        f.write(f"status: {active}\n")
        f.write(f"location_en: {loc}\n")
        f.write(f"default_page_count: {page_count}\n")
        f.write(f"story_prompt_tr length: {prompt_len} chars\n")
        f.write(f"outfit_girl length: {outfit_g} chars\n")
        f.write(f"scenario_bible: {bible}\n")
        f.write(f"has_companion: {has_companion}\n")
        f.write(f"no_family: {no_fam}\n")
        if cis:
            for c in cis:
                if isinstance(c, dict):
                    f.write(f"  custom_input: key={c.get('key')}, type={c.get('type')}, options={c.get('options')}\n")
        f.write(f"\n")

print("Wrote scenario_summary.txt")
