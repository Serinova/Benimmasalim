import sys
sys.path.insert(0, '.')
from app.scenarios.galata import GALATA

# Word count
words = GALATA.story_prompt_tr.split()
print(f"story_prompt_tr kelime sayisi: {len(words)}")
print(f"Companion sayisi: {len(GALATA.companions)}")
print(f"Object sayisi: {len(GALATA.objects)}")
for obj in GALATA.objects:
    print(f"  - {obj.name_tr}: {obj.appearance_en}")
    print(f"    prompt_suffix: {obj.prompt_suffix}")
print(f"Has companion: {GALATA.has_companion}")
print(f"Flags: {GALATA.flags}")
print(f"Location constraints length: {len(GALATA.location_constraints)}")
print(f"Cultural elements: {GALATA.cultural_elements}")
print(f"Scenario bible: {GALATA.scenario_bible}")
print(f"Custom inputs schema: {GALATA.custom_inputs_schema}")
print(f"Outfit girl: {GALATA.outfit_girl}")
print(f"Outfit boy: {GALATA.outfit_boy}")
print(f"Cover prompt: {GALATA.cover_prompt_template}")
print(f"Page prompt: {GALATA.page_prompt_template}")
print(f"Location constraints: {GALATA.location_constraints}")

# Placeholder check
prompt = GALATA.story_prompt_tr
placeholders = ['{animal_friend}', '{animal_friend_en}', '{companion}', '{guide}', '{rehber}', '{child_name}', '{clothing_description}', '{page_count}']
print("\n=== PLACEHOLDER KONTROL ===")
for p in placeholders:
    count = prompt.count(p)
    if count > 0:
        print(f"  {p}: {count} kez bulundu")
    
# Story prompt analysis
print(f"\n=== STORY PROMPT ANALIZ ===")
lines = [l.strip() for l in prompt.strip().split('\n') if l.strip()]
print(f"Satir sayisi: {len(lines)}")

# Check for YANLIS/DOGRU examples
print(f"YANLIS ornegi var mi: {'YANLIŞ' in prompt or '❌' in prompt}")
print(f"DOGRU ornegi var mi: {'DOĞRU' in prompt or '✅' in prompt}")

# Check for yasakli kelimeler
for word in ['anne', 'baba', 'kardeş', 'aile']:
    if word.lower() in prompt.lower():
        print(f"UYARI: '{word}' kelimesi bulundu!")

# Duygu keywords check
emotions = {
    'merak': ['merak', 'acaba', 'sır', 'gizem'],
    'heyecan': ['heyecan', 'coşku', 'harika'],
    'korku': ['korku', 'ürper', 'karanlık', 'tehlike'],
    'cesaret': ['cesaret', 'kararlı'],
    'sevinç': ['sevinç', 'mutluluk', 'güldü', 'gülümsü'],
    'gurur': ['gurur', 'başar'],
    'şaşkınlık': ['hayret', 'inanamadı'],
}
print("\n=== DUYGU ANALIZI ===")
for emotion, keywords in emotions.items():
    found = [k for k in keywords if k.lower() in prompt.lower()]
    if found:
        print(f"  {emotion}: {found}")
    else:
        print(f"  {emotion}: BULUNAMADI")
