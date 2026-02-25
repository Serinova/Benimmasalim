# -*- coding: utf-8 -*-
"""Tüm senaryoları backend script'lerinden analiz et."""

import os
import re
import json

print("="*80)
print("   SISTEMDEKI TUM SENARYOLAR - KAPSAMLI ANALIZ")
print("="*80)

script_dir = "backend/scripts"
scenario_scripts = [f for f in os.listdir(script_dir) if 'scenario' in f.lower() and f.endswith('.py') and not f.startswith('check_') and not f.startswith('fix_')]
scenario_scripts.sort()

print(f"\n[SCRIPT DOSYALARI] {len(scenario_scripts)} senaryo script bulundu\n")

scenarios_info = []

for script in scenario_scripts:
    script_path = os.path.join(script_dir, script)
    
    try:
        with open(script_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        theme_match = re.search(r'theme_key\s*=\s*["\']([^"\']+)["\']', content)
        theme_key = theme_match.group(1) if theme_match else "?"
        
        name_match = re.search(r'scenario\.name\s*=\s*["\']([^"\']+)["\']', content)
        if not name_match:
            name_match = re.search(r'name\s*=\s*["\']([^"\']+)["\']', content)
        scenario_name = name_match.group(1) if name_match else script.replace('_', ' ').replace('.py', '')
        
        cover_prompt_match = re.search(r'(COVER_PROMPT|cover_prompt_template)\s*=\s*"""([^"]{100,})', content, re.DOTALL)
        page_prompt_match = re.search(r'(PAGE_PROMPT|page_prompt_template)\s*=\s*"""([^"]{100,})', content, re.DOTALL)
        
        cover_len = len(cover_prompt_match.group(2)) if cover_prompt_match else 0
        page_len = len(page_prompt_match.group(2)) if page_prompt_match else 0
        
        has_outfit_girl = 'outfit_girl' in content or 'OUTFIT_GIRL' in content
        has_outfit_boy = 'outfit_boy' in content or 'OUTFIT_BOY' in content
        has_marketing = 'marketing_badge' in content
        
        info = {
            'script': script,
            'name': scenario_name,
            'theme_key': theme_key,
            'cover_len': cover_len,
            'page_len': page_len,
            'has_outfits': has_outfit_girl and has_outfit_boy,
            'has_marketing': has_marketing,
        }
        scenarios_info.append(info)
        
        status = "KULLANILMAZ" if (cover_len > 500 or page_len > 500) else ("KULLANILIR" if (cover_len > 0 or page_len > 0) else "DEFAULT")
        print(f"{len(scenarios_info):2d}. {scenario_name[:40]:40s} [{status}]")
        print(f"    theme: {theme_key:30s} cover: {cover_len:4d} page: {page_len:4d}")
        print(f"    outfit: {'OK' if has_outfit_girl and has_outfit_boy else 'NO':3s}  marketing: {'OK' if has_marketing else 'NO':3s}")
        
    except Exception as e:
        print(f"  [HATA] {script}: {e}")

print("\n" + "="*80)
print("KRITIK SONUC:")
print("="*80)

uzun = [s for s in scenarios_info if s['page_len'] > 500 or s['cover_len'] > 500]
kisa = [s for s in scenarios_info if 0 < s['page_len'] <= 500 or 0 < s['cover_len'] <= 500]
yok = [s for s in scenarios_info if s['page_len'] == 0 and s['cover_len'] == 0]

print(f"\n[UZUN PROMPT - KULLANILMIYOR!] {len(uzun)}/{len(scenarios_info)} senaryo")
print(f"[KISA PROMPT - KULLANILIYOR] {len(kisa)}/{len(scenarios_info)} senaryo")
print(f"[PROMPT YOK - DEFAULT] {len(yok)}/{len(scenarios_info)} senaryo")

print(f"\n[KRITIK!] {len(uzun)} senaryonun ozel prompt'lari PIPELINE TARAFINDAN KULLANILMIYOR!")
print("Sebebi: 500 karakter limiti asimi")
print("\nBunlar:")
for s in uzun[:5]:
    print(f"  - {s['name']}")
print(f"  ... ve {len(uzun)-5} tane daha")

print("\n[EYLEM GEREKLI] Tum senaryolar icin:")
print("  1. Prompt'lari KISALT (300-400 char, sadece scene/action)")
print("  2. Clothing/composition/style bloklarini KALDIR (pipeline ekler)")
print("  3. VEYA pipeline'daki 500 char limitini KALDIR")

# JSON rapor
with open('scenario_analysis_report.json', 'w', encoding='utf-8') as f:
    json.dump(scenarios_info, f, ensure_ascii=False, indent=2)

print("\n[RAPOR KAYDEDILDI] scenario_analysis_report.json")
