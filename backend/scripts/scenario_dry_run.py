"""
Scenario Dry-Run Tester — Görsel üretmeden hikaye pipeline'ını çalıştırır.

Bu script, production V3 pipeline'ını (PASS-0 Blueprint + PASS-1 Story Writer)
gerçek Gemini API üzerinden çalıştırır ama HİÇBİR GÖRSEL ÜRETMEZ.

Çıktılar:
- Blueprint JSON (sayfa rolleri, sahne hedefleri, duygusal yay)
- Her sayfa için: text_tr + image_prompt_en + negative_prompt_en
- Companion (G2) ve lokasyon (G3) tutarlılık analizi

Kullanım:
    python scripts/scenario_dry_run.py --theme_key dinosaur
    python scripts/scenario_dry_run.py --theme_key dinosaur --child_name "Ali" --child_age 8
    python scripts/scenario_dry_run.py --theme_key cappadocia --child_gender kiz
"""

import argparse
import asyncio
import re
import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.database import async_session_factory
from app.models import Scenario
from sqlalchemy import select


# ============================================================================
# G2 DENETİM FONKSİYONLARI
# ============================================================================

def check_g2_companion(pages: list[dict], scenario) -> dict:
    """G2-a: Yardımcı karakter tutarlılığını denetle."""
    bible = getattr(scenario, "scenario_bible", None) or {}
    side_char = bible.get("side_character", {})
    if not side_char:
        return {"status": "SKIP", "message": "scenario_bible.side_character tanımlı değil", "issues": []}

    companion_name = side_char.get("name", "")
    companion_anchor = side_char.get("appearance", "")
    companion_type = side_char.get("type", "")

    if not companion_name:
        return {"status": "SKIP", "message": "Companion adı boş", "issues": []}

    issues = []
    pages_with_companion = 0
    pages_missing_anchor = 0
    pages_wrong_type = 0

    for page in pages:
        text = (page.get("text") or "").lower()
        prompt_raw = (page.get("visual_prompt") or "").lower()

        # CAST RULES bölümünü çıkar — bu bölüm companion'ın hayvan olduğunu söyler,
        # ama "human child" ifadesi Yusuf için kullanılıyor ve false positive'e yol açar
        prompt = re.sub(r'cast on this page:.*?(?=\n\n|a \d+-year-old)', '', prompt_raw, flags=re.DOTALL)

        # Companion hikayede mi?
        if companion_name.lower() in text:
            pages_with_companion += 1

            # Anchor cümlesi prompt'ta mı?
            anchor_lower = companion_anchor.lower()
            if anchor_lower and anchor_lower not in prompt:
                # Kısmi kontrol: en az tür ve renk geçiyor mu?
                has_type = companion_type.lower() in prompt if companion_type else True
                has_name = companion_name.lower() in prompt
                if not has_type and not has_name:
                    # Ne tür ne isim var — ciddi sorun
                    issues.append({
                        "page": page.get("page_number"),
                        "severity": "HIGH",
                        "issue": f"{companion_name} metinde var ama prompt'ta ne tür ({companion_type}) ne isim geçiyor",
                        "prompt_preview": prompt[:200],
                    })
                    pages_missing_anchor += 1
                elif not has_type and has_name:
                    # İsim var ama tür keyword yok — hafif uyarı
                    # (pipeline companion'ı adıyla tanımlıyor, tür belirtmemiş)
                    pass  # Companion adıyla referans verilmiş, kabul edilebilir
                elif companion_anchor.lower()[:30] not in prompt:
                    issues.append({
                        "page": page.get("page_number"),
                        "severity": "MEDIUM",
                        "issue": f"{companion_name} prompt'ta var ama tam anchor cümlesi eksik",
                        "prompt_preview": prompt[:200],
                    })

            # İnsan olarak mı çizilmiş? (CAST RULES bölümü hariç)
            human_markers = ["second child", "another child", "a boy named", "a girl named"]
            # "human child" marker'ını companion'ın adıyla AYNI CÜMLEDE ara
            for marker in human_markers:
                if marker in prompt and companion_name.lower() in prompt:
                    issues.append({
                        "page": page.get("page_number"),
                        "severity": "CRITICAL",
                        "issue": f"{companion_name} İNSAN olarak tanımlanmış! marker='{marker}'",
                        "prompt_preview": prompt[:200],
                    })
                    pages_wrong_type += 1

    status = "PASS" if not issues else ("FAIL" if pages_wrong_type > 0 else "WARN")
    return {
        "status": status,
        "companion_name": companion_name,
        "companion_type": companion_type,
        "pages_with_companion": pages_with_companion,
        "pages_missing_anchor": pages_missing_anchor,
        "pages_wrong_type": pages_wrong_type,
        "issues": issues,
    }


def check_outfit_lock(pages: list[dict], outfit: str) -> dict:
    """Kıyafet kilidini denetle — her sayfada aynı kıyafet mi?"""
    if not outfit:
        return {"status": "SKIP", "message": "Kıyafet tanımı boş", "issues": []}

    issues = []
    outfit_lower = outfit.lower()[:60]  # İlk 60 karakter yeterli

    for page in pages:
        if page.get("page_type") not in ("inner",):
            continue
        prompt = (page.get("visual_prompt") or "").lower()
        if outfit_lower[:30] not in prompt:
            issues.append({
                "page": page.get("page_number"),
                "severity": "LOW",
                "issue": "Kıyafet tanımı prompt'ta bulunamadı",
            })

    return {
        "status": "PASS" if not issues else "WARN",
        "outfit_preview": outfit[:100],
        "issues": issues,
    }


def check_content_safety(pages: list[dict]) -> dict:
    """İçerik güvenliği denetimi — kelime sınırı (word boundary) ile kontrol."""
    # Türkçe: tam kelime eşleşmesi için regex pattern'ler
    BANNED_PATTERNS_TR = [
        (r"\böldür", "öldür"), (r"\bsaldır", "saldır"),
        (r"\byıkım\b", "yıkım"), (r"\bvahşet\b", "vahşet"),
        (r"\bşiddet\b", "şiddet"),  # "şiddetlendi" yakalamaz
        (r"\bkan\b", "kan"),  # "kanyon" yakalamaz
        (r"\bnamaz\b", "namaz"), (r"\bibadet\b", "ibadet"),
        (r"\bdua et", "dua et"), (r"\bsecde\b", "secde"),
        (r"\boruç\b", "oruç"),
        (r"\bsiyaset\b", "siyaset"), (r"\bparti\b", "parti"),
        (r"\bseçim\b", "seçim"), (r"\bbaşkan\b", "başkan"),
    ]
    BANNED_WORDS_EN = [
        "blood", "kill", "attack", "destroy", "violent",
        "sexy", "nude", "naked", "bikini",
        "skin color", "skin tone", "hair color", "eye color",
    ]

    issues = []
    for page in pages:
        text = (page.get("text") or "").lower()
        prompt = (page.get("visual_prompt") or "").lower()
        # Negative prompt'u HARIÇ tut — orda "violence" vs. zaten yasaklama amaçlı
        # Sadece visual_prompt'u kontrol et

        for pattern, label in BANNED_PATTERNS_TR:
            if re.search(pattern, text):
                issues.append({
                    "page": page.get("page_number"),
                    "severity": "HIGH",
                    "issue": f"Yasaklı kelime text_tr'de: '{label}'",
                })

        for word in BANNED_WORDS_EN:
            # Kelime sınırı ile kontrol — substring false-positive önleme
            # (ör: "skillfully" → "kill", "violence" → "violent" yakalanmasın)
            if ' ' in word:
                # Çok kelimeli terimler (skin color vb.) düz arama
                found = word in prompt
            else:
                found = bool(re.search(r'\b' + re.escape(word) + r'\b', prompt))
            if found:
                # "violent" bağlam analizi — doğa olayları ve olumsuzlama hariç
                if word == "violent":
                    safe_contexts = [
                        "non-violent", "non violent", "not violent", "no violent",
                        "violently sway", "sway violently", "violently shak",
                        "shaking violently", "violently shaking",
                        "wind violently", "violently blow", "waves violently",
                        "rain violently", "storm violently", "violently crash",
                        "violently toss", "tossing violently",
                        "violently rocking", "rocking violently",
                        "violent shake", "violent storm", "violent turbulence",
                    ]
                    if any(ctx in prompt for ctx in safe_contexts):
                        continue
                issues.append({
                    "page": page.get("page_number"),
                    "severity": "CRITICAL" if word in ("skin color", "hair color") else "HIGH",
                    "issue": f"Yasaklı kelime prompt'ta: '{word}'",
                })

    return {"status": "PASS" if not issues else "FAIL", "issues": issues}


def check_page_completeness(pages: list[dict], expected_page_count: int) -> dict:
    """Sayfa sayısı ve boş sayfa denetimi."""
    issues = []

    inner_pages = [p for p in pages if p.get("page_type") == "inner"]
    if len(inner_pages) != expected_page_count:
        issues.append({
            "severity": "HIGH",
            "issue": f"Beklenen {expected_page_count} iç sayfa, üretilen {len(inner_pages)}",
        })

    short_pages = [p for p in inner_pages if len((p.get("text") or "").strip()) < 30]
    if short_pages:
        for p in short_pages:
            issues.append({
                "page": p.get("page_number"),
                "severity": "HIGH",
                "issue": f"Kısa metin ({len((p.get('text') or '').strip())} karakter)",
            })

    empty_prompts = [p for p in inner_pages if len((p.get("visual_prompt") or "").strip()) < 20]
    if empty_prompts:
        for p in empty_prompts:
            issues.append({
                "page": p.get("page_number"),
                "severity": "HIGH",
                "issue": "Görsel prompt boş veya çok kısa",
            })

    return {"status": "PASS" if not issues else "FAIL", "issues": issues}


def check_text_visual_alignment(pages: list[dict]) -> dict:
    """Metin-görsel uyumu: text_tr'deki anahtar öğeler prompt'ta var mı?
    
    Eş anlamlı kelimeler de kabul edilir (ör: orman → forest/jungle/woodland).
    """
    TR_TO_EN = {
        "kelebek": ["butterfly"],
        "kartal": ["eagle"],
        "aslan": ["lion", "roar", "mane"],
        "dinozor": ["dinosaur", "dino", "parasaurolophus", "brachiosaurus", "t-rex", "triceratops", "pteranodon"],
        "pusula": ["compass"],
        "madalyon": ["medallion"],
        "nehir": ["river", "stream", "water", "creek"],
        "fırtına": ["storm", "thunder", "wind", "tempest", "rain", "downpour", "shelter", "turbulence", "turbulent"],
        "şimşek": ["lightning", "thunder"],
        "mağara": ["cave", "cavern", "grotto"],
        "orman": ["forest", "jungle", "woodland", "woods"],
        "ağaç": ["tree", "trunk", "log", "fern", "branch", "plant", "leaf", "vegetation", "foliage"],
        "gemi": ["ship", "boat", "vessel", "spaceship", "spacecraft", "shuttle"],
        "balon": ["balloon"],
        "köprü": ["bridge", "wooden bridge", "footbridge", "path", "crossing", "walkway", "arch", "overpass"],
        "kanyon": ["canyon", "gorge", "ravine", "cliff", "path", "edge", "narrow", "precipice"],
        "bataklık": ["swamp", "marsh", "bog", "mud"],
    }

    issues = []
    for page in pages:
        if page.get("page_type") != "inner":
            continue
        text = (page.get("text") or "").lower()
        prompt = (page.get("visual_prompt") or "").lower()

        for tr_word, en_words in TR_TO_EN.items():
            # Kelime sınırı ile kontrol — substring false positive önleme
            if re.search(r'\b' + re.escape(tr_word) + r'', text):
                # En az bir eş anlamlı kelime prompt'ta varsa OK
                if not any(en in prompt for en in en_words):
                    issues.append({
                        "page": page.get("page_number"),
                        "severity": "MEDIUM",
                        "issue": f"'{tr_word}' metinde var ama {en_words} prompt'ta yok",
                    })

    return {
        "status": "PASS" if not issues else "WARN",
        "issues": issues,
    }


def analyze_companion_visual_consistency(pages: list[dict], scenario) -> dict:
    """Companion'ın görsel tanımının sayfalar arası tutarlılığını analiz et.
    
    CAST BLOCK ve companion suffix'teki appearance bilgisini her sayfada
    karşılaştırarak tutarlılığı ölçer.
    """
    bible = getattr(scenario, "scenario_bible", None) or {}
    side_char = bible.get("side_character", {})
    if not side_char:
        return {"status": "SKIP", "score": 10, "message": "scenario_bible.side_character yok", 
                "pages_analyzed": 0, "consistency_ratio": 0}
    
    comp_name = side_char.get("name", "")
    comp_appearance = side_char.get("appearance", "")
    comp_type = side_char.get("type", "")
    
    if not comp_name:
        return {"status": "SKIP", "score": 10, "message": "Companion adı boş",
                "pages_analyzed": 0, "consistency_ratio": 0}
    
    inner = [p for p in pages if p.get("page_type") == "inner"]
    
    # Her sayfadaki companion tanımını çıkar
    page_descriptions = []
    pages_with_appearance = 0
    pages_without = []
    
    for p in inner:
        vp = p.get("visual_prompt", "")
        
        # Appearance metnini prompt'ta ara
        has_appearance = comp_appearance.lower() in vp.lower() if comp_appearance else False
        
        # CAST BLOCK'taki tanımı çıkar
        cast_pattern = re.escape(comp_name) + r'\s+is\s+a\s+' + re.escape(comp_type) + r'\s*\((.*?)\)'
        cast_match = re.search(cast_pattern, vp, re.IGNORECASE)
        cast_desc = cast_match.group(1).strip() if cast_match else ""
        
        # Companion suffix'teki tanım
        suffix_pattern = re.escape(comp_name) + r'\s+the\s+' + re.escape(comp_type) + r',?\s*(.*?)(?:is present|IMPORTANT)'
        suffix_match = re.search(suffix_pattern, vp, re.IGNORECASE)
        suffix_desc = suffix_match.group(1).strip() if suffix_match else ""
        
        desc = cast_desc or suffix_desc or ""
        
        if has_appearance or desc:
            pages_with_appearance += 1
            page_descriptions.append({
                "page": p["page_number"],
                "has_full_appearance": has_appearance,
                "extracted_desc": desc[:150],
            })
        else:
            pages_without.append(p["page_number"])
    
    consistency_ratio = pages_with_appearance / max(len(inner), 1)
    
    # Tanım tutarlılığı — çıkarılan tanımlar aynı mı?
    unique_descs = set(pd["extracted_desc"] for pd in page_descriptions if pd["extracted_desc"])
    desc_consistent = len(unique_descs) <= 1
    
    score = 10
    if consistency_ratio < 0.5:
        score -= 4
    elif consistency_ratio < 0.8:
        score -= 2
    elif consistency_ratio < 1.0:
        score -= 1
    
    if not desc_consistent:
        score -= 2  # Farklı tanımlar var
    
    issues = []
    if pages_without:
        issues.append({
            "severity": "MEDIUM" if len(pages_without) <= 3 else "HIGH",
            "issue": f"{comp_name} appearance {len(pages_without)} sayfada eksik: {pages_without}",
        })
    if not desc_consistent:
        issues.append({
            "severity": "HIGH",
            "issue": f"{comp_name} tanımı tutarsız! {len(unique_descs)} farklı tanım bulundu",
        })
    
    return {
        "status": "PASS" if not issues else ("WARN" if score >= 7 else "FAIL"),
        "score": max(1, round(score, 1)),
        "companion_name": comp_name,
        "companion_type": comp_type,
        "pages_with_appearance": pages_with_appearance,
        "pages_without_appearance": pages_without,
        "total_pages": len(inner),
        "consistency_ratio": round(consistency_ratio * 100),
        "description_consistent": desc_consistent,
        "unique_descriptions": len(unique_descs),
        "issues": issues,
    }


def analyze_object_consistency(pages: list[dict], scenario) -> dict:
    """Sihirli eşya ve anahtar objelerin prompt'lardaki tutarlılığını analiz et.
    
    scenario_bible'daki magic_item ve hikayedeki tekrar eden objeleri tespit edip
    prompt'larda tutarlı şekilde tanımlanıp tanımlanmadığını kontrol eder.
    """
    bible = getattr(scenario, "scenario_bible", None) or {}
    inner = [p for p in pages if p.get("page_type") == "inner"]
    
    # Bible'dan sihirli eşyayı al
    magic_item_tr = bible.get("magic_item", "")
    
    # Hikayede sık geçen objeleri tespit et (Türkçe metinde)
    COMMON_OBJECTS_TR_EN = {
        "pusula": ["compass", "navigation"],
        "anahtar": ["key", "golden key"],
        "harita": ["map"],
        "madalyon": ["medallion", "amulet"],
        "kalkan": ["shield"],
        "taç": ["crown", "tiara"],
        "kristal": ["crystal"],
        "kitap": ["book", "tome"],
        "fener": ["lantern", "lamp"],
        "kapsül": ["capsule", "pod", "submarine"],
        "dürbün": ["telescope", "binocular"],
        "bileklik": ["bracelet"],
        "yüzük": ["ring"],
        "kolye": ["necklace", "pendant"],
        "kılıç": ["sword"],
    }
    
    # Hangi objeler hikayede tekrar geçiyor
    object_tracking = {}
    for obj_tr, obj_en_list in COMMON_OBJECTS_TR_EN.items():
        pages_in_text = []
        pages_in_prompt = []
        
        for p in inner:
            text = (p.get("text") or "").lower()
            vp = (p.get("visual_prompt") or "").lower()
            
            if re.search(r'\b' + re.escape(obj_tr) + r'', text):
                pages_in_text.append(p["page_number"])
            if any(en in vp for en in obj_en_list):
                pages_in_prompt.append(p["page_number"])
        
        if len(pages_in_text) >= 3:  # En az 3 sayfada geçen objeler
            object_tracking[obj_tr] = {
                "en_equivalents": obj_en_list,
                "in_text_pages": pages_in_text,
                "in_prompt_pages": pages_in_prompt,
                "text_count": len(pages_in_text),
                "prompt_count": len(pages_in_prompt),
                "missing_in_prompt": [p for p in pages_in_text if p not in pages_in_prompt],
            }
    
    # Puan hesapla
    score = 10
    issues = []
    
    for obj_tr, info in object_tracking.items():
        missing = info["missing_in_prompt"]
        if len(missing) > info["text_count"] * 0.5:
            score -= 1.5
            issues.append({
                "severity": "MEDIUM",
                "issue": f"'{obj_tr}' {info['text_count']} sayfada geçiyor ama prompt'ta sadece {info['prompt_count']} sayfada var. Eksik: {missing}",
            })
        elif len(missing) > 0 and len(missing) <= 2:
            # 1-2 sayfada eksik, küçük uyarı
            pass
    
    return {
        "status": "PASS" if not issues else "WARN",
        "score": max(1, round(score, 1)),
        "tracked_objects": object_tracking,
        "magic_item": magic_item_tr,
        "issues": issues,
    }


# ============================================================================
# HİKAYE KALİTESİ ANALİZ FONKSİYONLARI
# ============================================================================

def analyze_repetition(pages: list[dict]) -> dict:
    """Tekrar eden kalıp/cümle tespiti."""
    inner = [p for p in pages if p.get("page_type") == "inner"]
    
    # Son cümle kalıpları (her sayfanın son cümlesi)
    endings = []
    # Başlangıç kalıpları (ilk 5 kelime)
    openings = []
    # Cümle kalıpları
    pattern_counts: dict[str, int] = {}
    
    for p in inner:
        text = (p.get("text") or "").strip()
        sentences = [s.strip() for s in re.split(r'[.!?]', text) if s.strip()]
        
        if sentences:
            endings.append(sentences[-1][:50])
            openings.append(" ".join(text.split()[:5]).lower())
        
        # 4+ kelimelik n-gram kalıplarını say
        words = text.lower().split()
        for n in range(4, 7):
            for i in range(len(words) - n):
                ngram = " ".join(words[i:i+n])
                pattern_counts[ngram] = pattern_counts.get(ngram, 0) + 1
    
    # Tekrar eden kalıplar (2+ sayfada)
    repeated = {k: v for k, v in pattern_counts.items() if v >= 3}
    top_repeated = sorted(repeated.items(), key=lambda x: -x[1])[:10]
    
    # Benzer açılışlar
    from collections import Counter
    opening_counts = Counter(openings)
    similar_openings = {k: v for k, v in opening_counts.items() if v >= 3}
    
    score = 10
    if len(top_repeated) > 5:
        score -= 3
    elif len(top_repeated) > 2:
        score -= 1.5
    if similar_openings:
        score -= 1
    
    return {
        "score": max(1, round(score, 1)),
        "repeated_patterns": top_repeated,
        "similar_openings": list(similar_openings.items()),
        "unique_endings_ratio": len(set(endings)) / max(len(endings), 1),
    }


def analyze_dialogue(pages: list[dict]) -> dict:
    """Diyalog miktarı ve kalitesi analizi."""
    inner = [p for p in pages if p.get("page_type") == "inner"]
    
    total_dialogues = 0
    pages_with_dialogue = 0
    dialogue_chars = set()  # Kimler konuşuyor
    dialogue_examples = []
    
    for p in inner:
        text = p.get("text", "")
        # Türkçe tırnak/guillemet veya "" içindeki konuşmalar
        dialogues = re.findall(r'[""«»\'](.*?)[""«»\']', text)
        if dialogues:
            pages_with_dialogue += 1
            total_dialogues += len(dialogues)
            for d in dialogues[:2]:
                dialogue_examples.append({"page": p["page_number"], "text": d[:100]})
    
    dialogue_ratio = pages_with_dialogue / max(len(inner), 1)
    
    # Puan: ideal %30-50 sayfada diyalog
    score = 10
    if dialogue_ratio < 0.15:
        score -= 3  # Çok az diyalog
    elif dialogue_ratio < 0.25:
        score -= 1.5
    elif dialogue_ratio > 0.7:
        score -= 1  # Çok fazla diyalog
    
    return {
        "score": max(1, round(score, 1)),
        "total_dialogues": total_dialogues,
        "pages_with_dialogue": pages_with_dialogue,
        "dialogue_ratio": round(dialogue_ratio * 100),
        "examples": dialogue_examples[:6],
    }


def analyze_action_passivity(pages: list[dict]) -> dict:
    """Kahramanın aktif mi pasif mi olduğunu analiz et."""
    inner = [p for p in pages if p.get("page_type") == "inner"]
    
    ACTIVE_VERBS = [
        "koştu", "atladı", "tırmandı", "yüzdü", "tuttu", "çekti", "itti",
        "açtı", "kapattı", "kesti", "bağırdı", "fısıldadı", "döndü",
        "uzandı", "bastı", "kavradı", "fırlattı", "yakaladı", "taşıdı",
        "sürdü", "yuvarladı", "salladı", "karıştırdı", "topladı",
        "derin bir nefes aldı", "adım attı", "hamle yaptı",
    ]
    PASSIVE_VERBS = [
        "izledi", "baktı", "gördü", "fark etti", "hissetti", "düşündü",
        "merak etti", "hayret etti", "şaşırdı", "endişelendi", "korktu",
        "anladı", "dinledi", "duydu", "uyandı", "hayranlıkla",
    ]
    
    active_count = 0
    passive_count = 0
    active_pages = []
    passive_pages = []
    
    child_name = ""
    # İlk sayfadan çocuk adını bul
    for p in inner[:3]:
        text = p.get("text", "")
        names = re.findall(r'\b([A-ZÇĞİÖŞÜ][a-zçğıöşü]+)\b', text)
        for n in names:
            if n not in ("Bir", "Bu", "Tam", "Ama", "Her", "Ne", "Sonra"):
                child_name = n
                break
        if child_name:
            break
    
    for p in inner:
        text = (p.get("text") or "").lower()
        page_active = sum(1 for v in ACTIVE_VERBS if v in text)
        page_passive = sum(1 for v in PASSIVE_VERBS if v in text)
        active_count += page_active
        passive_count += page_passive
        
        if page_active > page_passive:
            active_pages.append(p["page_number"])
        elif page_passive > page_active:
            passive_pages.append(p["page_number"])
    
    total = active_count + passive_count
    active_ratio = active_count / max(total, 1)
    
    score = 10
    if active_ratio < 0.3:
        score -= 3  # Çok pasif
    elif active_ratio < 0.4:
        score -= 1.5
    elif active_ratio > 0.8:
        score -= 1  # Biraz fazla aksiyon, düşünme yok
    
    return {
        "score": max(1, round(score, 1)),
        "active_verbs": active_count,
        "passive_verbs": passive_count,
        "active_ratio": round(active_ratio * 100),
        "active_pages": active_pages,
        "passive_pages": passive_pages,
    }


def analyze_emotional_arc(pages: list[dict]) -> dict:
    """Sayfa sayfa duygusal yay haritalama."""
    inner = [p for p in pages if p.get("page_type") == "inner"]
    
    EMOTION_KEYWORDS = {
        "merak": ["merak", "acaba", "gizemli", "sır", "ne olacak"],
        "heyecan": ["heyecan", "hızla", "koştu", "atladı", "macera", "wow"],
        "korku": ["kork", "endişe", "tehlike", "titred", "ürpertici", "karanlık"],
        "üzüntü": ["üzül", "hüzün", "kalbini burktu", "gözyaş", "acı"],
        "sevinç": ["sevinç", "mutlu", "güldü", "neşe", "harika", "coşku", "muhteşem"],
        "cesaret": ["cesaret", "cesur", "kararlı", "yapabilirim", "derin bir nefes"],
        "şaşkınlık": ["şaşır", "hayret", "inanamad", "büyülen", "büyülen", "gözlerine inanamad"],
        "gurur": ["gurur", "başard", "kahraman", "zafer", "tamamlandı"],
    }
    
    arc = []
    for p in inner:
        text = (p.get("text") or "").lower()
        page_emotions = {}
        for emotion, keywords in EMOTION_KEYWORDS.items():
            count = sum(1 for kw in keywords if kw in text)
            if count:
                page_emotions[emotion] = count
        
        dominant = max(page_emotions, key=page_emotions.get) if page_emotions else "nötr"
        arc.append({
            "page": p["page_number"],
            "dominant": dominant,
            "emotions": page_emotions,
        })
    
    # Duygusal çeşitlilik — kaç farklı duygu var?
    all_emotions = set()
    for a in arc:
        all_emotions.update(a["emotions"].keys())
    
    # İdeal: En az 4 farklı duygu
    score = 10
    if len(all_emotions) < 3:
        score -= 3
    elif len(all_emotions) < 4:
        score -= 1
    
    # Korku-cesaret geçişi var mı? (önemli dramatik yay)
    has_fear_courage = False
    for i in range(len(arc) - 1):
        if "korku" in arc[i]["emotions"] and "cesaret" in arc[i+1].get("emotions", {}):
            has_fear_courage = True
    if not has_fear_courage:
        score -= 1
    
    return {
        "score": max(1, round(score, 1)),
        "arc": arc,
        "emotion_variety": len(all_emotions),
        "emotions_found": list(all_emotions),
        "has_fear_courage_transition": has_fear_courage,
    }


def analyze_page_rhythm(pages: list[dict]) -> dict:
    """Sayfa uzunluk dengesi ve ritim analizi."""
    inner = [p for p in pages if p.get("page_type") == "inner"]
    
    word_counts = []
    for p in inner:
        text = p.get("text", "")
        wc = len(text.split())
        word_counts.append({"page": p["page_number"], "words": wc})
    
    counts = [w["words"] for w in word_counts]
    avg = sum(counts) / max(len(counts), 1)
    min_wc = min(counts) if counts else 0
    max_wc = max(counts) if counts else 0
    
    # Standart sapma
    variance = sum((c - avg) ** 2 for c in counts) / max(len(counts), 1)
    std_dev = variance ** 0.5
    
    # Çok kısa veya çok uzun sayfalar
    too_short = [w for w in word_counts if w["words"] < 25]
    too_long = [w for w in word_counts if w["words"] > 100]
    
    score = 10
    if std_dev > 25:
        score -= 2  # Çok dengesiz
    elif std_dev > 15:
        score -= 1
    if too_short:
        score -= len(too_short) * 0.5
    if too_long:
        score -= len(too_long) * 0.5
    
    return {
        "score": max(1, round(score, 1)),
        "avg_words": round(avg, 1),
        "min_words": min_wc,
        "max_words": max_wc,
        "std_dev": round(std_dev, 1),
        "too_short_pages": [w["page"] for w in too_short],
        "too_long_pages": [w["page"] for w in too_long],
        "word_counts": word_counts,
    }


def analyze_vocabulary(pages: list[dict]) -> dict:
    """Kelime çeşitliliği ve zenginlik analizi."""
    inner = [p for p in pages if p.get("page_type") == "inner"]
    
    all_words = []
    for p in inner:
        text = (p.get("text") or "").lower()
        # Noktalama temizle
        text = re.sub(r'[^\w\s]', '', text)
        words = [w for w in text.split() if len(w) > 2]
        all_words.extend(words)
    
    total = len(all_words)
    unique = len(set(all_words))
    ttr = unique / max(total, 1)  # Type-Token Ratio
    
    # Çocuk kitabı için ideal TTR: 0.35-0.55
    score = 10
    if ttr < 0.25:
        score -= 3  # Çok tekrarlı
    elif ttr < 0.30:
        score -= 1.5
    elif ttr > 0.65:
        score -= 1  # Belki çok karmaşık
    
    # Sıfat çeşitliliği (renk, boyut, duygu sıfatları)
    color_adj = ["kırmızı", "mavi", "yeşil", "sarı", "turuncu", "pembe", "mor",
                 "beyaz", "siyah", "gri", "altın", "gümüş", "rengarenk", "parlak"]
    size_adj = ["küçük", "büyük", "kocaman", "minik", "devasa", "dev", "ufak"]
    
    colors_used = [c for c in color_adj if c in " ".join(all_words)]
    sizes_used = [s for s in size_adj if s in " ".join(all_words)]
    
    return {
        "score": max(1, round(score, 1)),
        "total_words": total,
        "unique_words": unique,
        "ttr": round(ttr, 3),
        "colors_used": colors_used,
        "sizes_used": sizes_used,
    }


def analyze_hooks(pages: list[dict]) -> dict:
    """Sayfa sonu hook/merak uyandırma analizi."""
    inner = [p for p in pages if p.get("page_type") == "inner"]
    
    HOOK_INDICATORS = [
        "acaba", "ne olacak", "merak", "birden", "tam o sırada",
        "?", "!", "ama", "ancak", "fakat", "beklenmedik",
        "ansızın", "birdenbire", "o anda", "derken",
    ]
    
    pages_with_hook = 0
    hook_details = []
    
    for p in inner[:-1]:  # Son sayfa hariç (sonuç sayfası)
        text = (p.get("text") or "").strip()
        # Son cümle
        sentences = [s.strip() for s in re.split(r'[.!?]', text) if s.strip()]
        last_sentence = sentences[-1].lower() if sentences else ""
        last_two = " ".join(sentences[-2:]).lower() if len(sentences) >= 2 else last_sentence
        
        has_hook = any(h in last_two for h in HOOK_INDICATORS)
        if has_hook:
            pages_with_hook += 1
        hook_details.append({
            "page": p["page_number"],
            "has_hook": has_hook,
            "ending": sentences[-1][:80] if sentences else "",
        })
    
    hook_ratio = pages_with_hook / max(len(inner) - 1, 1)
    
    score = 10
    if hook_ratio < 0.3:
        score -= 3
    elif hook_ratio < 0.5:
        score -= 1.5
    
    return {
        "score": max(1, round(score, 1)),
        "pages_with_hook": pages_with_hook,
        "total_checked": len(inner) - 1,
        "hook_ratio": round(hook_ratio * 100),
        "details": hook_details,
    }


def calculate_fun_score(analyses: dict) -> dict:
    """Tüm analizlerden genel eğlence puanı hesapla."""
    weights = {
        "repetition": 0.15,
        "dialogue": 0.15,
        "action": 0.15,
        "emotional_arc": 0.20,
        "rhythm": 0.10,
        "vocabulary": 0.10,
        "hooks": 0.15,
    }
    
    weighted_sum = 0
    breakdown = {}
    for key, weight in weights.items():
        s = analyses.get(key, {}).get("score", 5)
        weighted_sum += s * weight
        breakdown[key] = {"score": s, "weight": f"{int(weight*100)}%"}
    
    final = round(weighted_sum, 1)
    
    # Emoji rating
    if final >= 9:
        emoji = "🌟🌟🌟🌟🌟"
        label = "OLAĞANÜSTÜ"
    elif final >= 8:
        emoji = "🌟🌟🌟🌟"
        label = "ÇOK İYİ"
    elif final >= 6.5:
        emoji = "🌟🌟🌟"
        label = "İYİ"
    elif final >= 5:
        emoji = "🌟🌟"
        label = "ORTA"
    else:
        emoji = "🌟"
        label = "GELİŞTİRİLMELİ"
    
    return {
        "final_score": final,
        "emoji": emoji,
        "label": label,
        "breakdown": breakdown,
    }


# ============================================================================
# ANA DRY-RUN FONKSİYONU
# ============================================================================

async def run_dry_test(theme_key: str, child_name: str, child_age: int, child_gender: str):
    """Pipeline'ı çalıştır, çıktıları analiz et, rapor sun."""
    from app.services.ai.gemini_service import GeminiService

    # 1. Senaryoyu DB'den çek
    async with async_session_factory() as db:
        result = await db.execute(
            select(Scenario).where(
                (Scenario.theme_key == theme_key) | (Scenario.name.ilike(f"%{theme_key}%"))
            )
        )
        scenario = result.scalar_one_or_none()
        if not scenario:
            print(f"❌ HATA: '{theme_key}' senaryosu bulunamadı!")
            return None

    print("=" * 80)
    print(f"🧪 SCENARIO DRY-RUN TESTER")
    print("=" * 80)
    print(f"  Senaryo: {scenario.name}")
    print(f"  Theme Key: {scenario.theme_key}")
    print(f"  story_page_count: {scenario.story_page_count}")
    print(f"  scenario_bible: {'VAR' if scenario.scenario_bible else 'YOK'}")
    print(f"  custom_inputs: {len(scenario.custom_inputs_schema or [])}")
    print(f"  outfit_boy: {'VAR' if scenario.outfit_boy else 'YOK'}")
    print(f"  outfit_girl: {'VAR' if scenario.outfit_girl else 'YOK'}")
    print()

    page_count = scenario.story_page_count or 21

    # Kıyafet belirle
    if child_gender in ("kiz", "girl", "female"):
        fixed_outfit = scenario.outfit_girl or ""
    else:
        fixed_outfit = scenario.outfit_boy or ""

    # 2. Pipeline çalıştır
    print(f"🚀 Pipeline başlatılıyor...")
    print(f"   Çocuk: {child_name}, {child_age} yaş, {child_gender}")
    print(f"   Sayfa: {page_count}")
    print()

    start_time = time.monotonic()

    gemini = GeminiService()

    # Retry mekanizması — Gemini API geçici 400/503 hatası verebilir
    max_retries = 3
    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            print(f"   Deneme {attempt}/{max_retries}...")
            story_response, final_pages, outfit, blueprint = await gemini.generate_story_v3(
                scenario=scenario,
                child_name=child_name,
                child_age=child_age,
                child_gender=child_gender,
                outcomes=[],
                visual_style="children's book illustration, soft colors",
                page_count=page_count,
                fixed_outfit=fixed_outfit,
                generate_visual_prompts=True,
            )
            break  # Başarılı
        except Exception as e:
            last_error = e
            print(f"   ⚠️ Deneme {attempt} başarısız: {type(e).__name__}: {str(e)[:200]}")
            if attempt < max_retries:
                wait = 15 * attempt
                print(f"   ⏳ {wait} saniye bekleniyor...")
                await asyncio.sleep(wait)
            else:
                print(f"\n❌ Pipeline {max_retries} denemede de başarısız oldu!")
                print(f"   Son hata: {last_error}")
                return None

    elapsed = time.monotonic() - start_time
    print(f"✅ Pipeline tamamlandı ({elapsed:.1f} saniye)")
    print()

    # 3. Çıktıları yapılandır
    pages_data = []
    for fp in final_pages:
        pages_data.append({
            "page_number": fp.page_number,
            "page_type": fp.page_type,
            "text": fp.text,
            "visual_prompt": fp.visual_prompt,
            "negative_prompt": getattr(fp, "negative_prompt", ""),
            "scene_description": fp.scene_description,
        })

    # 4. Tüm sayfaları yazdır
    print("=" * 80)
    print(f"📖 BAŞLIK: {story_response.title}")
    print("=" * 80)

    for p in pages_data:
        if p["page_type"] == "cover":
            print(f"\n🎨 KAPAK:")
            print(f"   Metin: {p['text']}")
            print(f"   Prompt: {p['visual_prompt'][:300]}...")
        elif p["page_type"] == "backcover":
            print(f"\n🔚 ARKA KAPAK:")
            print(f"   Prompt: {p['visual_prompt'][:300]}...")
        else:
            print(f"\n📄 SAYFA {p['page_number']}:")
            print(f"   Metin: {p['text'][:200]}")
            print(f"   Prompt: {p['visual_prompt'][:300]}")

    # 5. DENETİM çalıştır
    print()
    print("=" * 80)
    print(f"🔍 DENETİM SONUÇLARI")
    print("=" * 80)

    g2_result = check_g2_companion(pages_data, scenario)
    outfit_result = check_outfit_lock(pages_data, outfit)
    safety_result = check_content_safety(pages_data)
    completeness_result = check_page_completeness(pages_data, page_count)
    alignment_result = check_text_visual_alignment(pages_data)
    companion_visual = analyze_companion_visual_consistency(pages_data, scenario)
    object_result = analyze_object_consistency(pages_data, scenario)

    checks = {
        "G2-a Companion Tutarlılığı": g2_result,
        "G2-b Companion Görsel Kilidi": companion_visual,
        "Kıyafet Kilidi": outfit_result,
        "İçerik Güvenliği": safety_result,
        "Sayfa Tamamlılığı": completeness_result,
        "Metin-Görsel Uyumu": alignment_result,
        "Obje/Eşya Tutarlılığı": object_result,
    }

    total_issues = 0
    for name, result in checks.items():
        status = result["status"]
        icon = {"PASS": "✅", "WARN": "⚠️", "FAIL": "❌", "SKIP": "⏭️"}.get(status, "❓")
        issue_count = len(result.get("issues", []))
        total_issues += issue_count
        
        # Ek bilgi göster
        extra = ""
        if name == "G2-b Companion Görsel Kilidi" and status != "SKIP":
            cr = result.get("consistency_ratio", 0)
            cn = result.get("companion_name", "")
            dc = "tutarlı" if result.get("description_consistent") else "TUTARSIZ"
            extra = f" — {cn} tanımı %{cr} sayfada mevcut, {dc}"
        elif name == "Obje/Eşya Tutarlılığı":
            tracked = result.get("tracked_objects", {})
            if tracked:
                obj_list = ", ".join(f"{k}({v['text_count']}s)" for k, v in tracked.items())
                extra = f" — Takip edilen: {obj_list}"
        
        print(f"  {icon} {name}: {status} ({issue_count} sorun){extra}")

        for issue in result.get("issues", []):
            severity = issue.get("severity", "")
            page_num = issue.get("page", "?")
            msg = issue.get("issue", "")
            if page_num != "?":
                print(f"      [{severity}] Sayfa {page_num}: {msg}")
            else:
                print(f"      [{severity}] {msg}")

    print()

    print(f"📊 TOPLAM: {total_issues} sorun bulundu")

    # 6. HİKAYE KALİTESİ ANALİZİ
    print()
    print("=" * 80)
    print(f"📚 HİKAYE KALİTESİ ANALİZİ")
    print("=" * 80)

    story_analyses = {
        "repetition": analyze_repetition(pages_data),
        "dialogue": analyze_dialogue(pages_data),
        "action": analyze_action_passivity(pages_data),
        "emotional_arc": analyze_emotional_arc(pages_data),
        "rhythm": analyze_page_rhythm(pages_data),
        "vocabulary": analyze_vocabulary(pages_data),
        "hooks": analyze_hooks(pages_data),
    }
    fun = calculate_fun_score(story_analyses)

    labels = {
        "repetition": "🔁 Tekrar Analizi",
        "dialogue": "💬 Diyalog Analizi",
        "action": "🏃 Aksiyon/Pasiflik",
        "emotional_arc": "📈 Duygusal Yay",
        "rhythm": "📏 Sayfa Ritmi",
        "vocabulary": "🔤 Kelime Çeşitliliği",
        "hooks": "🪝 Sayfa Sonu Hook'ları",
    }

    for key, label in labels.items():
        a = story_analyses[key]
        score = a["score"]
        bar = "█" * int(score) + "░" * (10 - int(score))
        print(f"  {label}: {score}/10 [{bar}]")

        # Detay bilgiler
        if key == "repetition":
            rp = a.get("repeated_patterns", [])
            if rp:
                print(f"      Tekrar eden kalıplar: {len(rp)} adet")
                for pattern, count in rp[:3]:
                    print(f"        '{pattern}' → {count}x")
        elif key == "dialogue":
            print(f"      Diyalog oranı: %{a['dialogue_ratio']} ({a['pages_with_dialogue']}/{len([p for p in pages_data if p.get('page_type')=='inner'])} sayfa)")
            for ex in a.get("examples", [])[:2]:
                print(f"        S.{ex['page']}: \"{ex['text'][:60]}...\"")
        elif key == "action":
            print(f"      Aktif/Pasif oranı: %{a['active_ratio']} aktif ({a['active_verbs']} aktif, {a['passive_verbs']} pasif fiil)")
        elif key == "emotional_arc":
            print(f"      Duygu çeşitliliği: {a['emotion_variety']} farklı duygu ({', '.join(a['emotions_found'])})")
            print(f"      Korku→Cesaret geçişi: {'✅ VAR' if a['has_fear_courage_transition'] else '❌ YOK'}")
            arc_str = " → ".join(f"S.{x['page']}:{x['dominant']}" for x in a["arc"] if x["dominant"] != "nötr")
            if arc_str:
                print(f"      Yay: {arc_str[:200]}")
        elif key == "rhythm":
            print(f"      Ort: {a['avg_words']} kelime | Min: {a['min_words']} | Max: {a['max_words']} | StdDev: {a['std_dev']}")
            if a["too_short_pages"]:
                print(f"      ⚠️ Çok kısa sayfalar: {a['too_short_pages']}")
            if a["too_long_pages"]:
                print(f"      ⚠️ Çok uzun sayfalar: {a['too_long_pages']}")
        elif key == "vocabulary":
            print(f"      Toplam: {a['total_words']} kelime | Benzersiz: {a['unique_words']} | TTR: {a['ttr']}")
            if a["colors_used"]:
                print(f"      🎨 Renkler: {', '.join(a['colors_used'])}")
            if a["sizes_used"]:
                print(f"      📐 Boyutlar: {', '.join(a['sizes_used'])}")
        elif key == "hooks":
            print(f"      Hook oranı: %{a['hook_ratio']} ({a['pages_with_hook']}/{a['total_checked']} sayfa)")

    print()
    print(f"  {'='*50}")
    print(f"  🎯 GENEL EĞLENCE PUANI: {fun['final_score']}/10 {fun['emoji']}")
    print(f"     Değerlendirme: {fun['label']}")
    print(f"  {'='*50}")

    # 7. JSON'a kaydet
    output_dir = os.path.join(os.path.dirname(__file__), "..", "tmp", "dry_run")
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"{theme_key}_dry_run.json")

    output = {
        "scenario_name": scenario.name,
        "theme_key": theme_key,
        "child": {"name": child_name, "age": child_age, "gender": child_gender},
        "outfit": outfit,
        "blueprint": blueprint,
        "pages": pages_data,
        "audit": {name: {k: v for k, v in r.items() if k != "issues"} | {"issue_count": len(r.get("issues", []))}
                  for name, r in checks.items()},
        "audit_details": checks,
        "story_quality": {
            "fun_score": fun,
            "analyses": {k: {kk: vv for kk, vv in v.items() if kk != "details"} 
                        for k, v in story_analyses.items()},
        },
        "elapsed_seconds": round(elapsed, 1),
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n💾 Çıktı kaydedildi: {output_file}")
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="🧪 Scenario Dry-Run Tester")
    parser.add_argument("--theme_key", required=True, help="Senaryo theme_key (örn: dinosaur)")
    parser.add_argument("--child_name", default="Yusuf", help="Test çocuğu adı")
    parser.add_argument("--child_age", type=int, default=7, help="Test çocuğu yaşı")
    parser.add_argument("--child_gender", default="erkek", help="Test cinsiyeti (erkek/kiz)")
    args = parser.parse_args()

    asyncio.run(run_dry_test(args.theme_key, args.child_name, args.child_age, args.child_gender))
