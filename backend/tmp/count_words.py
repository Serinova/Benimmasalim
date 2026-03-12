import re

with open("app/scenarios/amazon.py", encoding="utf-8") as f:
    text = f.read()

m = re.search(r'story_prompt_tr="""(.*?)"""', text, re.DOTALL)
if m:
    prompt = m.group(1)
    words = prompt.split()
    print(f"Kelime sayisi: {len(words)}")
    
    # Hook analizi
    hook_words = ["birden", "ansızın", "tam o sırada", "ama", "ancak", "fakat",
                  "bir anda", "derken", "o an", "tam o anda", "baktığında",
                  "dönünce", "merak", "acaba", "nasıl olur da", "kim",
                  "ne olacak", "bu kez", "henüz", "hâlâ"]
    
    for hw in hook_words:
        if hw in prompt.lower():
            print(f"Hook kelime bulundu: {hw}")
    
    # Duygu analizi
    emotions = {
        "merak": ["merak", "acaba", "ne olacak", "ilginç", "tuhaf", "sır", "gizem", "gizemli"],
        "heyecan": ["heyecan", "harika", "muhteşem"],
        "korku": ["korku", "ürperdi", "karanlık", "tehlike", "endişe", "endişeli"],
        "sevinç": ["sevinç", "mutluluk", "güldü", "neşe"],
        "cesaret": ["cesaret", "kararlı"],
        "şaşkınlık": ["hayret", "inanamadı", "beklenmedik"],
        "gurur": ["gurur", "başardı"],
    }
    
    found_emotions = []
    for emo, keywords in emotions.items():
        for kw in keywords:
            if kw in prompt.lower():
                found_emotions.append(f"{emo} ({kw})")
                break
    
    print(f"\nBulunan duygular: {found_emotions}")
    print(f"Duygu cesitliligi: {len(found_emotions)}")
    
    # Placeholder analizi
    placeholders = ["{animal_friend}", "{child_name}", "{clothing_description}", "{page_count}"]
    for ph in placeholders:
        count = prompt.count(ph)
        print(f"Placeholder {ph}: {count} kez")
    
    # Yasak kelime kontrolu
    forbidden = ["anne", "baba", "kardeş", "aile"]
    for fw in forbidden:
        if fw in prompt.lower():
            print(f"YASAK kelime bulundu: {fw}")
    
    # Dogrudan ogut kontrolu
    ogut_patterns = ["olduğunu anladı", "olduğunu öğrendi", "olduğunu kavradı", 
                     "ne kadar önemli", "gösterdi"]
    for op in ogut_patterns:
        if op in prompt.lower():
            print(f"Dogrudan ogut kalıbı: '{op}'")
