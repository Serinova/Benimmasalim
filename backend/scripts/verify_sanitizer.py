"""Verify scene_description sanitizer catches Turkish text."""
import sys
sys.path.insert(0, "/app")

from app.services.ai.gemini_service import GeminiService

svc = GeminiService.__new__(GeminiService)

tests = [
    # (input, should_be_fallback)
    (
        "Enes, gizemli Yerebatan Sarnıcı'nın serin koridorlarında dolaşırken, su damlalarının sesiyle yankılanan antik sütunlara hayranlıkla baktı.",
        True,
        "Full Turkish story text"
    ),
    (
        "Cover text placeholder",
        True,
        "English placeholder"
    ),
    (
        "A breathtaking view of Cappadocia with fairy chimneys and hot air balloons.",
        False,
        "Correct English scene"
    ),
    (
        "Birdenbire, taşların arasından parıldayan bir ışık huzmesi belirdi.",
        True,
        "Turkish inner page text leaked"
    ),
    (
        "The interior of Basilica Cistern with ancient marble columns. A child looking up in wonder.",
        False,
        "Correct English scene (Yerebatan)"
    ),
]

FALLBACK = "A child in an adventure scene."

print("Sanitizer Tests:")
for text, should_fallback, desc in tests:
    result = svc._sanitize_scene_description(text)
    is_fallback = result == FALLBACK
    match = is_fallback == should_fallback
    status = "PASS" if match else "FAIL"
    print(f"  [{status}] {desc}")
    if not match:
        print(f"    Input: {text[:80]}")
        print(f"    Got: {result[:80]}")
        print(f"    Expected fallback: {should_fallback}")
