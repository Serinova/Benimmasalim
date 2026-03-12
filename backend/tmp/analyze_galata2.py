import sys
sys.path.insert(0, '.')
from app.scenarios.galata import GALATA

prompt = GALATA.story_prompt_tr
words = prompt.split()
print(f"KELIME SAYISI: {len(words)}")
print()

# Hook analysis - check for hook trigger words
hook_words = ["birden", "ansızın", "tam o sırada", "ama", "ancak", "fakat",
              "bir anda", "derken", "o an", "tam o anda", "baktığında",
              "dönünce", "merak", "acaba", "nasıl olur da", "kim",
              "ne olacak", "bu kez", "henüz", "hâlâ"]
found_hooks = [h for h in hook_words if h.lower() in prompt.lower()]
print(f"Hook trigger kelimeleri: {found_hooks}")

# Active vs passive verbs
active_verbs = ["koştu", "atladı", "tırmandı", "kaydı", "bastı", "çekti", "döndürdü",
                "fırlattı", "yakaladı", "uzandı", "kucakladı", "salladı", "eğildi",
                "dokundu", "açtı", "kırdı", "bağırdı", "fısıldadı", "gülümsedi",
                "kaçtı", "uçtu", "yürüdü", "adım attı", "tutundu", "sıçradı",
                "yuvarlandı", "tırmanıyor", "iniyor", "ulaşıyor", "saklıyor", "tutuyor"]
passive_verbs = ["gördü", "baktı", "hissetti", "düşündü", "izledi", "anladı",
                 "biliyordu", "merak etti", "fark etti", "hatırladı", "durdu",
                 "bekledi", "oturdu", "görüyor", "fark ediyor"]

active_found = [v for v in active_verbs if v.lower() in prompt.lower()]
passive_found = [v for v in passive_verbs if v.lower() in prompt.lower()]
print(f"\nAktif fiiller: {active_found}")
print(f"Pasif fiiller: {passive_found}")
total = len(active_found) + len(passive_found)
if total > 0:
    print(f"Aktif oran: {len(active_found)/total*100:.0f}%")

# Gezi rehberi check
gezi_patterns = ["gördü. Sonra", "gitti. Sonra", "geldi. Sonra", "yapılmıştır", "kullanılıyordu"]
for p in gezi_patterns:
    if p.lower() in prompt.lower():
        print(f"\n⚠️ GEZİ REHBERİ PATTERN: '{p}'")

# Direct preaching check
preaching = ["öğrendi", "anlamıştı", "anladı", "kavradı", "önemli olduğunu", 
             "öğretmişti", "güzelliğini öğrendi", "gerektiğini biliyordu"]
for p in preaching:
    if p.lower() in prompt.lower():
        print(f"\n⚠️ DOĞRUDAN ÖĞÜT: '{p}'")

# Content - check sections
print("\n=== BÖLÜM YAPISI ===")
sections = prompt.split("### Bölüm")
print(f"Bölüm sayisi: {len(sections) - 1}")

# Scene/location diversity
locations = ["Galata Kulesi", "Karaköy", "Beyoğlu", "İstiklal", "Tünel", "rıhtım", "avlu", "sokak"]
found_locations = [l for l in locations if l.lower() in prompt.lower()]
print(f"\nMekan çeşitliliği: {len(found_locations)} — {found_locations}")

# Sensory details
print("\n=== DUYUSAL DETAY ===")
visual = ["ışık", "parla", "renk", "altın", "kırmızı", "mor", "parlıyor"]
auditory = ["ses", "gıcırdı", "fısıl"]
smell = ["koku", "baharat"]
touch = ["soğuk", "sıcak", "dokundu", "hissetti"]
taste = ["tat", "tuzlu"]

v = [w for w in visual if w.lower() in prompt.lower()]
a = [w for w in auditory if w.lower() in prompt.lower()]
s = [w for w in smell if w.lower() in prompt.lower()]
t = [w for w in touch if w.lower() in prompt.lower()]
ta = [w for w in taste if w.lower() in prompt.lower()]

print(f"  Görme: {v}")
print(f"  İşitme: {a}")
print(f"  Koklama: {s}")
print(f"  Dokunma: {t}")
print(f"  Tat: {ta}")
senses_used = sum(1 for x in [v, a, s, t, ta] if x)
print(f"  Kullanılan duyu: {senses_used}/5")

# Outfit check
print("\n=== KIYAFET KONTROL ===")
print(f"outfit_girl contains 'EXACTLY': {'EXACTLY' in GALATA.outfit_girl}")
print(f"outfit_boy contains 'EXACTLY': {'EXACTLY' in GALATA.outfit_boy}")
print(f"outfit_girl İngilizce: {all(ord(c) < 256 or c in ',' for c in GALATA.outfit_girl)}")
print(f"outfit_boy İngilizce: {all(ord(c) < 256 or c in ',' for c in GALATA.outfit_boy)}")

# scenario_bible check
print(f"\nScenario bible boş mu: {GALATA.scenario_bible == {} or not GALATA.scenario_bible}")
