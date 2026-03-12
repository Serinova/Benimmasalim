import sys
sys.path.insert(0, '.')
from app.scenarios.cappadocia import CAPPADOCIA

words = CAPPADOCIA.story_prompt_tr.split()
print(f"Cappadocia kelime sayisi: {len(words)}")
print(f"Companion: {len(CAPPADOCIA.companions)}")
print(f"Scenario bible bos: {CAPPADOCIA.scenario_bible == {}}")
print(f"Bible keys: {list(CAPPADOCIA.scenario_bible.keys()) if CAPPADOCIA.scenario_bible else 'NONE'}")
