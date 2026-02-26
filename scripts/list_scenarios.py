# -*- coding: utf-8 -*-
"""Tüm aktif senaryoları listele ve detaylarını göster."""

import requests

API_URL = "https://benimmasalim-backend-1059478049554.europe-west1.run.app/api/v1/scenarios"

print("="*80)
print("   MEVCUT SENARYOLAR - DETAYLI ANALIZ")
print("="*80)

try:
    r = requests.get(API_URL, timeout=10)
    r.raise_for_status()
    scenarios = r.json()
    
    print(f"\n[TOPLAM] {len(scenarios)} aktif senaryo bulundu\n")
    
    for i, s in enumerate(scenarios, 1):
        print(f"\n{'='*80}")
        print(f"{i}. {s['name']}")
        print('='*80)
        print(f"  theme_key: {s.get('theme_key', 'N/A')}")
        print(f"  location: {s.get('location_en', 'N/A')}")
        print(f"  age_range: {s.get('age_range', 'N/A')}")
        print(f"  marketing_badge: {s.get('marketing_badge', 'N/A')}")
        print(f"  tagline: {s.get('tagline', 'N/A')[:60]}..." if s.get('tagline') and len(s.get('tagline', '')) > 60 else f"  tagline: {s.get('tagline', 'N/A')}")
        
        # Prompt'lar var mı kontrol (public API'de görünmez genelde)
        has_cover = s.get('cover_prompt_template') is not None
        has_page = s.get('page_prompt_template') is not None
        has_story = s.get('story_prompt_tr') is not None
        
        print(f"  Prompts: cover={has_cover}, page={has_page}, story={has_story}")
        
        # Custom inputs
        custom_inputs = s.get('custom_inputs_schema')
        if custom_inputs:
            print(f"  custom_inputs: {len(custom_inputs)} alan")
        else:
            print("  custom_inputs: Yok/None")
        
        # Outfit
        has_outfit_girl = s.get('outfit_girl') is not None
        has_outfit_boy = s.get('outfit_boy') is not None
        print(f"  outfits: girl={has_outfit_girl}, boy={has_outfit_boy}")
        
        # Default sayfa sayisi
        print(f"  default_page_count: {s.get('default_page_count', 'N/A')}")
        
        # Display order
        print(f"  display_order: {s.get('display_order', 'N/A')}")

    print("\n" + "="*80)
    print("SCRIPT DOSYALARI:")
    print("="*80)
    
    import os
    script_dir = "backend/scripts"
    scenario_scripts = [f for f in os.listdir(script_dir) if 'scenario' in f.lower() and f.endswith('.py')]
    scenario_scripts.sort()
    
    print(f"\n{len(scenario_scripts)} senaryo script dosyasi bulundu:\n")
    for script in scenario_scripts:
        print(f"  - {script}")

except Exception as e:
    print(f"\n[HATA] API cagrisi basarisiz: {e}")
