import sys
sys.path.insert(0, '.')
from app.scenarios.galata import GALATA

prompt = GALATA.story_prompt_tr
words = prompt.split()
print(f"=== KELIME SAYISI: {len(words)} (hedef 700+) ===")
print()

# Placeholder check
placeholders = ['{animal_friend}', '{child_name}', '{clothing_description}', '{page_count}', '{child_age}', '{child_gender}']
print("=== PLACEHOLDER KONTROL ===")
for p in placeholders:
    count = prompt.count(p)
    if count > 0:
        print(f"  {p}: {count} kez")

# Hook words
hook_words = ["birden", "ansızın", "tam o sırada", "ama", "ancak", "fakat",
              "bir anda", "derken", "o an", "tam o anda", "baktığında",
              "dönünce", "merak", "acaba"]
found_hooks = [h for h in hook_words if h.lower() in prompt.lower()]
print(f"\n=== HOOK KELİMELERİ: {len(found_hooks)} ===")
print(f"  {found_hooks}")

# YANLIS/DOGRU
print(f"\n=== YANLIŞ/DOĞRU ===")
print(f"  YANLIŞ örnegi: {'YANLIŞ' in prompt}")
print(f"  DOĞRU örnegi: {'DOĞRU' in prompt}")

# Emotion keywords
emotions = {
    'merak': ['merak', 'acaba', 'sır', 'gizem'],
    'heyecan': ['heyecan', 'coşku', 'harika'],
    'korku/endişe': ['korku', 'ürper', 'karanlık', 'tehlike', 'tedirgin', 'endişe', 'titri'],
    'cesaret': ['cesaret', 'kararlı', 'yapabilirim'],
    'sevinç': ['sevinç', 'mutluluk', 'güldü', 'gülümse', 'parlıyor'],
    'gurur': ['gurur', 'başar'],
    'şaşkınlık': ['hayret', 'inanamadı', 'ağzı açık', 'şaşkın'],
}
print(f"\n=== DUYGU ANALİZİ ===")
emotion_count = 0
for emotion, keywords in emotions.items():
    found = [k for k in keywords if k.lower() in prompt.lower()]
    if found:
        emotion_count += 1
        print(f"  ✅ {emotion}: {found}")
    else:
        print(f"  ❌ {emotion}: YOK")
print(f"  Toplam: {emotion_count}/7 duygu kategorisi")

# Sensory
print(f"\n=== DUYUSAL DETAY ===")
visual = ["ışık", "parla", "renk", "altın", "kırmızı", "mor"]
auditory = ["ses", "çığlık", "zil", "gıcırd", "fısıl", "dalga", "yankıl", "ezan", "miyav"]
smell = ["koku", "baharat", "simit", "deniz koku", "nemli"]
touch = ["soğuk", "sıcak", "dokun", "pürüzlü", "ıslak", "kaygan", "kırılgan", "titr"]
taste = ["tat", "tuzlu"]

v = [w for w in visual if w.lower() in prompt.lower()]
a = [w for w in auditory if w.lower() in prompt.lower()]
s = [w for w in smell if w.lower() in prompt.lower()]
t = [w for w in touch if w.lower() in prompt.lower()]
ta = [w for w in taste if w.lower() in prompt.lower()]

print(f"  👁️ Görme ({len(v)}): {v}")
print(f"  👂 İşitme ({len(a)}): {a}")
print(f"  👃 Koklama ({len(s)}): {s}")
print(f"  ✋ Dokunma ({len(t)}): {t}")
print(f"  👅 Tat ({len(ta)}): {ta}")
senses_used = sum(1 for x in [v, a, s, t, ta] if x)
print(f"  Kullanılan duyu: {senses_used}/5")

# Active vs passive
active_verbs = ["koştu", "atladı", "tırmandı", "tırmanıyor", "kaydı", "bastı", "çekti",
                "fırlattı", "yakaladı", "kucakladı", "dokundu", "açtı", "koşuyor",
                "fısıldıyor", "gülümsüyor", "sokuyor", "tutuyor", "sıçrıyor",
                "iniyor", "dalıyor", "ilerliyor", "mırıldanıyor"]
passive_verbs = ["gördü", "baktı", "hissetti", "düşündü", "izledi", "anladı",
                 "görüyor", "fark ediyor", "biliyordu", "merak etti"]
active_found = [v for v in active_verbs if v.lower() in prompt.lower()]
passive_found = [v for v in passive_verbs if v.lower() in prompt.lower()]
total = len(active_found) + len(passive_found)
print(f"\n=== AKSİYON DENGESİ ===")
print(f"  Aktif: {len(active_found)} — {active_found}")
print(f"  Pasif: {len(passive_found)} — {passive_found}")
if total > 0:
    print(f"  Aktif oran: {len(active_found)/total*100:.0f}%")

# Micro-obstacles
print(f"\n=== MIKRO-ENGEL KONTROL ===")
obstacles = ["kırık", "ıslatacak", "kaygan", "karanlık", "uzaklaşıyor", "yetişemi", "az zaman"]
found_obs = [o for o in obstacles if o.lower() in prompt.lower()]
print(f"  {len(found_obs)} mikro-engel: {found_obs}")

# Location diversity
locations = ["Galata Kulesi", "Karaköy", "Beyoğlu", "İstiklal", "Tünel", "rıhtım", "avlu", "sokak", "merdiven"]
found_loc = [l for l in locations if l.lower() in prompt.lower()]
print(f"\n=== MEKAN ÇEŞİTLİLİĞİ: {len(found_loc)} ===")
print(f"  {found_loc}")

# Scenario bible
print(f"\n=== SCENARIO BIBLE ===")
print(f"  Boş mu: {GALATA.scenario_bible == {}}")
if GALATA.scenario_bible:
    print(f"  Anahtarlar: {list(GALATA.scenario_bible.keys())}")

# Dialog check
print(f"\n=== DİYALOG ===")
dialog_count = prompt.count('"') // 2
print(f"  Diyalog sayısı: ~{dialog_count}")

print(f"\n{'='*50}")
print(f"✅ TAMAMLANDI — Tüm kontroller bitti")
