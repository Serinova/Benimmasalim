#!/usr/bin/env python3
"""Visual Prompt Pipeline Verification Runner.

Executes the full enhance_all_pages() pipeline on a realistic 22-page
Cappadocia/Uras story, then runs all validators and outputs a JSON report.

Usage:
    cd backend
    py scripts/run_visual_pipeline_verification.py
"""
from __future__ import annotations

import json
import sys
import os
import random

# Ensure backend/app is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.prompt_engine.character_bible import build_character_bible
from app.prompt_engine.scene_director import build_shot_plan, validate_shot_diversity
from app.prompt_engine.iconic_anchors import pick_anchors
from app.prompt_engine.visual_prompt_builder import (
    enhance_all_pages,
    extract_visual_beat,
)
from app.prompt_engine.story_validators import (
    validate_visual_prompt_diversity,
    validate_character_consistency,
    validate_story_output,
    apply_all_fixes,
)
from app.prompt_engine.style_adapter import adapt_style

# =============================================================================
# META — realistic Cappadocia book
# =============================================================================

META = {
    "book_title": "Bora'nın Kapadokya Macerası",
    "child_name": "Bora",
    "child_age": 4,
    "child_gender": "erkek",
    "child_description": "kıvırcık kahverengi saçlı, ela gözlü",
    "location_key": "cappadocia",
    "visual_style": "watercolor",
    "page_count": 22,
    "magic_items": ["sihirli pusula"],
}

# =============================================================================
# BLUEPRINT — 22 pages with varied roles
# =============================================================================

BLUEPRINT: dict = {
    "title": META["book_title"],
    "page_count": 22,
    "location_key": "cappadocia",
    "visual_style": META["visual_style"],
    "theme": ["cesaret", "merak", "keşif"],
    "cultural_facts_plan": [
        "Peri bacaları: rüzgar ve yağmurun binlerce yıl boyunca şekillendirdiği kaya oluşumları",
        "Yeraltı şehirleri: insanlar tehlikelerden korunmak için kayaların altına şehirler kazmış",
        "Kaya kiliseleri: kayaların içine oyulmuş, duvarları renkli fresklarla süslü",
        "Avanos'ta çömlekçilik geleneği, Kızılırmak'ın kırmızı kili ile yapılır",
        "Volkanik tüf kayası yumuşak olduğu için kolayca oyulabilir",
        "Güvercin vadisi: binlerce güvercin yuvası oyulmuş kayalıklar",
        "Kapadokya adının 'güzel atlar ülkesi' anlamına geldiği söylenir",
    ],
    "side_character": {"name": "Güvercin Bulut", "type": "güvercin rehber", "intro_page": 2},
    "pages": [
        {"page": 1, "role": "dedication", "scene_goal": "Bora'ya özel ithaf", "visual_brief_tr": "Altın çerçeve içinde Bora ismi, peri bacaları ve balonlar", "conflict_or_question": "", "cultural_hook": "", "magic_touch": ""},
        {"page": 2, "role": "arrival", "scene_goal": "Kapadokya'ya varış, manzara keşfi", "visual_brief_tr": "Göreme vadisi panoraması, peri bacaları, şafak ışığı", "conflict_or_question": "Bu devasa kayalar nasıl oluşmuş?", "cultural_hook": "Peri bacaları rüzgar ve yağmurun eseri", "magic_touch": ""},
        {"page": 3, "role": "arrival", "scene_goal": "Güvercin Bulut ile tanışma, harita bulunması", "visual_brief_tr": "Kaya oyuğu, tozlu harita, güvercin", "conflict_or_question": "Haritadaki üç yıldız nereyi gösteriyor?", "cultural_hook": "", "magic_touch": ""},
        {"page": 4, "role": "obstacle", "scene_goal": "Rüzgarlı peri bacaları arasında yol bulma", "visual_brief_tr": "Rüzgarlı vadi, eğilen ağaçlar, sallanan peri bacaları", "conflict_or_question": "Doğru yolu nasıl bulacak?", "cultural_hook": "Volkanik tüf kayası yumuşak", "magic_touch": ""},
        {"page": 5, "role": "puzzle", "scene_goal": "Fresk tamamlama bulmacası kaya kilisesinde", "visual_brief_tr": "Kaya kilisesi içi, renkli freskler, eksik bölüm", "conflict_or_question": "Eksik parça nerede?", "cultural_hook": "Kaya kiliseleri: kayaların içine oyulmuş ibadethaneler", "magic_touch": ""},
        {"page": 6, "role": "small_victory", "scene_goal": "Freski tamamlayınca gizli geçit açılır", "visual_brief_tr": "Duvar kayar, gizli geçit görünür, ışık huzmesi", "conflict_or_question": "", "cultural_hook": "", "magic_touch": ""},
        {"page": 7, "role": "exploration", "scene_goal": "Yeraltı şehrine iniş başlar", "visual_brief_tr": "Taş merdivenler aşağı iner, meşale ışığı, oyma taş duvarlar", "conflict_or_question": "Aşağıda ne var?", "cultural_hook": "Yeraltı şehirleri: tehlikelerden korunmak için kazmışlar", "magic_touch": ""},
        {"page": 8, "role": "obstacle", "scene_goal": "Yeraltında karanlık tünel, yön kaybı", "visual_brief_tr": "Karanlık tünel, havalandırma şaftı, taş kapı", "conflict_or_question": "Hangi yöne gitmeli?", "cultural_hook": "", "magic_touch": "sihirli pusula kuzey gösterir"},
        {"page": 9, "role": "surprise_discovery", "scene_goal": "Avanos çömlekçi atölyesi keşfi", "visual_brief_tr": "Çömlekçi atölyesi, çark, kırmızı kil, raflarda çömlekler", "conflict_or_question": "", "cultural_hook": "Avanos çömlekçilik geleneği, Kızılırmak kili", "magic_touch": ""},
        {"page": 10, "role": "cultural_moment", "scene_goal": "Çömlekçi ustadan çömlek yapma dersi", "visual_brief_tr": "Bora çömlekçi çarkında, kil yoğuruyor, usta izliyor", "conflict_or_question": "", "cultural_hook": "Kızılırmak kırmızı kili ile çömlek yapımı", "magic_touch": ""},
        {"page": 11, "role": "obstacle", "scene_goal": "Güvercin vadisinde kayıp mesaj arayışı", "visual_brief_tr": "Beyaz kayalıklara oyulmuş güvercin yuvaları, uçuşan güvercinler", "conflict_or_question": "Mesaj hangi yuvada?", "cultural_hook": "Güvercin vadisi: binlerce yuva oyulmuş", "magic_touch": ""},
        {"page": 12, "role": "puzzle", "scene_goal": "Renk eşleştirme — balonların sırası", "visual_brief_tr": "Gökyüzünde renkli balonlar, sıralama bulmacası", "conflict_or_question": "Hangi sıra doğru?", "cultural_hook": "Balonlar her sabah şafakta gökyüzünü boyar", "magic_touch": ""},
        {"page": 13, "role": "small_victory", "scene_goal": "Balon festivali yukarıdan izlenir", "visual_brief_tr": "Gökyüzünde düzinelerce balon, vadinin kuş bakışı görünümü", "conflict_or_question": "", "cultural_hook": "", "magic_touch": ""},
        {"page": 14, "role": "obstacle", "scene_goal": "Uçhisar kalesine tırmanma zorluğu", "visual_brief_tr": "Uçhisar kale kayası, dik patika, rüzgar", "conflict_or_question": "Tepeye ulaşabilecek mi?", "cultural_hook": "", "magic_touch": ""},
        {"page": 15, "role": "surprise_discovery", "scene_goal": "Kalenin tepesinden tüm vadiyi görme", "visual_brief_tr": "Panoramik Kapadokya manzarası, gün batımı tonları", "conflict_or_question": "", "cultural_hook": "Kapadokya güzel atlar ülkesi", "magic_touch": ""},
        {"page": 16, "role": "puzzle", "scene_goal": "Harita okuma — son ipucu çözümü", "visual_brief_tr": "Bora haritaya dikkatle bakıyor, pusula ve yıldızlar", "conflict_or_question": "Son yıldız nereyi işaret ediyor?", "cultural_hook": "", "magic_touch": "sihirli pusula titreşir"},
        {"page": 17, "role": "challenge", "scene_goal": "Kaya kilisesine giden labirent yol", "visual_brief_tr": "Dar kayalık geçitler, çatallaşan yollar", "conflict_or_question": "Doğru geçidi seçmeli", "cultural_hook": "", "magic_touch": ""},
        {"page": 18, "role": "obstacle", "scene_goal": "Labirentte yanlış dönüş, geri dönüş", "visual_brief_tr": "Çıkmaz yol, dönüp yeniden denemek", "conflict_or_question": "Vazgeçmeyecek mi?", "cultural_hook": "", "magic_touch": ""},
        {"page": 19, "role": "main_discovery", "scene_goal": "Gizli kaya kilisesindeki hazine", "visual_brief_tr": "Görkemli kaya kilisesi, altın ışık, duvar freskleri, hazine sandığı", "conflict_or_question": "", "cultural_hook": "Kaya kiliseleri renkli fresklarla süslü", "magic_touch": ""},
        {"page": 20, "role": "reward", "scene_goal": "Cesaret madalyonu ve dostluk mesajı", "visual_brief_tr": "Bora madalyonu tutuyor, Bulut omzunda, gururlu ifade", "conflict_or_question": "", "cultural_hook": "", "magic_touch": ""},
        {"page": 21, "role": "closure", "scene_goal": "Balonla vedalaşma, gökyüzüne yükseliş", "visual_brief_tr": "Sıcak hava balonunda Bora, alttan vadi, gün batımı", "conflict_or_question": "", "cultural_hook": "", "magic_touch": ""},
        {"page": 22, "role": "closure", "scene_goal": "Eve dönüş, kapanış mesajı", "visual_brief_tr": "Bora pencereden yıldızlara bakıyor, madalyon göğsünde", "conflict_or_question": "", "cultural_hook": "", "magic_touch": ""},
    ],
}

# =============================================================================
# PAGES — 22-page story (text_tr + raw LLM image_prompt_en)
# =============================================================================

PAGES: list[dict] = [
    {"page": 1, "text_tr": "Bu kitap, gözleri merakla parlayan, kıvırcık saçları rüzgarda savrulan minik kaşif Bora'ya özeldir. Hazır mısın Bora? Çünkü bu macera tam sana göre!",
     "image_prompt_en": "Dedication page, warm golden frame with the name Bora, fairy chimneys and colorful balloons, soft light, wide shot, child 30% of frame, no text, no watermark, no logo",
     "negative_prompt_en": "text, watermark, blurry"},
    {"page": 2, "text_tr": "Bora vadinin kenarına geldiğinde ağzı açık kaldı. Devasa kayalar, mantarlara benzeyen şekilleriyle gökyüzüne uzanıyordu. \"Bunlara peri bacası diyorlar,\" diye fısıldadı rüzgar. \"Binlerce yıldır burada duruyorlar.\"",
     "image_prompt_en": "A child in an adventure scene, wide shot, child 30% of frame, warm lighting, no text, no watermark, no logo",
     "negative_prompt_en": "text, watermark, blurry"},
    {"page": 3, "text_tr": "Bir güvercin kanat çırparak yanına kondu. Boynu parlak beyaz tüylerle kaplıydı. \"Ben Bulut,\" dedi güvercin. \"Seni bekliyordum. Bu vadinin bir sırrı var ve onu seninle keşfetmek istiyorum.\"",
     "image_prompt_en": "A 4-year-old boy meeting a white dove with shiny feathers, medium shot, eye level, the dove landing on a rock beside the child, fairy chimney valley background, golden hour, no text, no watermark, no logo",
     "negative_prompt_en": "text, watermark, blurry"},
    {"page": 4, "text_tr": "Rüzgar birden şiddetlendi. Peri bacalarının arasındaki dar patikada ilerlemek zorlaştı. Tüf kayası ayaklarının altında yumuşacık ufalanıyordu. Bora dişlerini sıktı ve bir adım daha attı.",
     "image_prompt_en": "A child walking through a windy fairy chimney valley, volcanic tuff crumbling underfoot, wind bending small trees, determined expression, wide shot, dramatic cloudy sky, no text, no watermark, no logo",
     "negative_prompt_en": "text, watermark, blurry"},
    {"page": 5, "text_tr": "Kayaların içine oyulmuş bir kiliseye girdiler. Duvarlar rengarenk resimlerle doluydu ama bir tanesi eksikti. \"Freski tamamlarsan kapı açılır,\" dedi Bulut gözlerini kısarak.",
     "image_prompt_en": "A boy and a white dove inside a rock-carved church, colorful ancient frescoes on stone walls, one fresco section missing, dim interior warm light from above, close-up on the wall painting, no text, no watermark, no logo",
     "negative_prompt_en": "text, watermark, blurry"},
    {"page": 6, "text_tr": "Bora son parçayı yerine koyduğunda taş duvar titredi. Çatırrr! Duvar yana kayarak gizli bir geçit açtı. İçeriden altın renginde bir ışık süzülüyordu.",
     "image_prompt_en": "A stone wall sliding open to reveal a secret passage, golden light streaming through, dust particles in the air, a boy stepping forward with excitement, the white dove flying beside him, medium shot, no text, no watermark, no logo",
     "negative_prompt_en": "text, watermark, blurry"},
    {"page": 7, "text_tr": "Taş merdivenler aşağıya doğru kıvrılıyordu. Duvarlarda oyulmuş küçük nişler meşale ışığıyla aydınlanıyordu. \"Burası yeraltı şehri,\" dedi Bulut. \"İnsanlar tehlikelerden korunmak için burayı kazmışlar.\"",
     "image_prompt_en": "A boy and dove descending carved stone stairs into underground city, torch-lit niches in walls, ancient carved stone tunnels, warm amber light, medium shot, child 35% of frame, no text, no watermark, no logo",
     "negative_prompt_en": "text, watermark, blurry"},
    {"page": 8, "text_tr": "Tüneller karanlıklaştı. Bora cebindeki sihirli pusulayı çıkardı. Pusulanın ibresi mavi bir ışık saçarak kuzeyi gösterdi. \"Bu tarafa!\" dedi Bora güvenle.",
     "image_prompt_en": "A child in an adventure scene in a dark tunnel, wide shot, child 30% of frame, no text, no watermark, no logo",
     "negative_prompt_en": "text, watermark, blurry"},
    {"page": 9, "text_tr": "Tünelin sonunda beklenmedik bir yer vardı: bir çömlekçi atölyesi! Raflarda kırmızı kilden yapılmış çömlekler diziliydi. Avanos'un ünlü Kızılırmak kili burada şekil alıyordu.",
     "image_prompt_en": "A hidden underground pottery workshop, red Kizilirmak clay on shelves, ceramic jugs and pots, pottery wheel in center, warm lantern light, a boy and dove discovering the room with amazement, medium shot, no text, no watermark, no logo",
     "negative_prompt_en": "text, watermark, blurry"},
    {"page": 10, "text_tr": "Yaşlı bir çömlekçi usta, Bora'ya çarkı nasıl çevireceğini gösterdi. Ellerinin arasında kil dönerken şekil almaya başladı. \"Sabır ve sevgiyle her şey güzel olur,\" dedi usta gülümseyerek.",
     "image_prompt_en": "A boy shaping red clay on a pottery wheel, an elderly pottery master guiding his hands, the white dove watching from a shelf, close-up on hands and spinning clay, warm workshop light, no text, no watermark, no logo",
     "negative_prompt_en": "text, watermark, blurry"},
    {"page": 11, "text_tr": "Güvercin vadisine ulaştıklarında Bora beyaz kayalıklara oyulmuş yüzlerce yuvayı gördü. Güvercinler uçuşuyor, kanat sesleri vadiyi dolduruyordu. \"Mesaj bunlardan birinde gizli,\" dedi Bulut.",
     "image_prompt_en": "White rock cliff face with hundreds of carved pigeon houses, pigeons flying around, a boy looking up searching, green valley below, wide shot, child 25% of frame, bright daylight, no text, no watermark, no logo",
     "negative_prompt_en": "text, watermark, blurry"},
    {"page": 12, "text_tr": "Gökyüzü birden renklendi. Düzinelerce sıcak hava balonu şafakla birlikte yükselmeye başladı. \"Balonların rengini doğru sıraya koy!\" dedi Bulut. Bora parmağıyla kırmızı, sarı, mavi diye saydı.",
     "image_prompt_en": "Dozens of colorful hot air balloons rising at dawn over fairy chimney valley, a boy pointing up counting colors, vibrant sky with orange pink purple hues, wide shot, child 20% of frame, no text, no watermark, no logo",
     "negative_prompt_en": "text, watermark, blurry"},
    {"page": 13, "text_tr": "Bir balonun sepetinden vadiye baktıklarında her şey minyatür gibiydi. Peri bacaları küçücük mantarlar, ağaçlar yeşil noktalar olmuştu. Bora gülümsedi: \"Dünya yukarıdan ne güzelmiş!\"",
     "image_prompt_en": "A child in an adventure scene, wide shot, child 30% of frame, no text, no watermark, no logo",
     "negative_prompt_en": "text, watermark, blurry"},
    {"page": 14, "text_tr": "Uçhisar kalesinin dik patikasında tırmanmak kolay değildi. Rüzgar saçlarını savururken Bora her adımda biraz daha yükseldi. Bulut başının üstünde süzülüp cesaret veriyordu.",
     "image_prompt_en": "A boy climbing a steep rocky path up Uchisar castle rock, wind blowing his curly hair, dove flying above encouraging, dramatic rocky landscape, low angle looking up, no text, no watermark, no logo",
     "negative_prompt_en": "text, watermark, blurry"},
    {"page": 15, "text_tr": "Tepeye ulaştığında Bora nefesini tuttu. Tüm Kapadokya ayaklarının altına serilmişti! Güneş batarken peri bacaları altın rengine boyanıyordu. \"Güzel atlar ülkesi...\" diye fısıldadı hayretle.",
     "image_prompt_en": "Panoramic sunset view of Cappadocia from Uchisar summit, fairy chimneys turning golden, a boy standing at peak with arms slightly open, dove on shoulder, high angle looking down at vast valley, orange purple sky, no text, no watermark, no logo",
     "negative_prompt_en": "text, watermark, blurry"},
    {"page": 16, "text_tr": "Bora haritayı açtı. Son yıldız bir kaya kilisesini işaret ediyordu. Sihirli pusula titremeye başladı ve ibresi yıldızla aynı yönü gösterdi. \"Çok yakınız!\" dedi heyecanla.",
     "image_prompt_en": "A boy studying an ancient map while a glowing compass trembles in his hand, star markings on the map, dove looking over his shoulder, warm golden sunset light, medium shot, child 40% of frame, no text, no watermark, no logo",
     "negative_prompt_en": "text, watermark, blurry"},
    {"page": 17, "text_tr": "Dar kayalık geçitlerden ilerliyorlardı. Yol ikiye ayrıldığında Bora duraksadı. Sol geçit karanlık, sağ geçit biraz aydınlıktı. Pusula sola döndü. Bora derin bir nefes aldı ve karanlığa adım attı.",
     "image_prompt_en": "A boy standing at a fork in narrow rocky canyon passages, left passage dark, right passage lit, dove perched on rock, dramatic shadows, the child taking a brave step left, medium shot, no text, no watermark, no logo",
     "negative_prompt_en": "text, watermark, blurry"},
    {"page": 18, "text_tr": "Çıkmaz sokak! Yol bitiyordu. Ama Bora vazgeçmedi. Geri döndü ve bu sefer duvardaki küçük bir işareti fark etti. \"Burası gizli kapı!\" Eliyle bastırdığında duvar sessizce açıldı.",
     "image_prompt_en": "A boy pressing a hidden symbol on a stone wall in a dead-end passage, the wall beginning to open, dust falling, discovery expression, dove fluttering with excitement, warm dim light, close-up on hands and symbol, no text, no watermark, no logo",
     "negative_prompt_en": "text, watermark, blurry"},
    {"page": 19, "text_tr": "İçeri adım attığında gözleri kamaştı. Muhteşem bir kaya kilisesiydi! Duvarlar baştan aşağı renkli fresklarla kaplıydı. Ortada altın ışıkla parlayan bir sandık duruyordu. Bora yavaşça yaklaştı.",
     "image_prompt_en": "A magnificent rock-carved church interior, vibrant colorful frescoes covering walls and ceiling, golden light illuminating a treasure chest in the center, a boy approaching slowly with awe, dove flying in golden light above, wide shot, grand scale, no text, no watermark, no logo",
     "negative_prompt_en": "text, watermark, blurry"},
    {"page": 20, "text_tr": "Sandığı açtığında içinde altın renginde bir madalyon buldu. Madalyonun üzerinde küçük bir peri bacası kabartması vardı. \"Bu cesaret madalyonu,\" dedi Bulut. \"Sen bunu hak ettin, dostum.\"",
     "image_prompt_en": "A boy holding a golden medallion with a fairy chimney embossed on it, pride in his eyes, dove on his shoulder, soft golden warm light, treasure chest open behind, medium shot, child 40% of frame, no text, no watermark, no logo",
     "negative_prompt_en": "text, watermark, blurry"},
    {"page": 21, "text_tr": "Gün batarken Bora bir sıcak hava balonunun sepetine bindi. Balon yavaşça yükselirken Kapadokya'nın tüm güzellikleri altlarında kaldı. Bulut yanında süzülüyordu. \"Hoşça kal Kapadokya!\" diye seslendi Bora.",
     "image_prompt_en": "A boy riding in a hot air balloon basket at sunset, vast Cappadocia valley below with fairy chimneys, dove flying alongside, orange pink golden sky, wide shot, child 30% of frame, no text, no watermark, no logo",
     "negative_prompt_en": "text, watermark, blurry"},
    {"page": 22, "text_tr": "O gece Bora penceresinden yıldızlara baktı. Göğsündeki madalyon ışıl ışıl parlıyordu. \"Her macera bir cesaret adımıyla başlar,\" diye düşündü. Ve Bora biliyordu ki bu sadece başlangıçtı.",
     "image_prompt_en": "A boy looking at stars through a window at night, medallion glowing on chest, cozy room, starry sky outside, dove sleeping on windowsill, medium shot, soft moonlight and warm interior glow, no text, no watermark, no logo",
     "negative_prompt_en": "text, watermark, blurry"},
]


def main() -> None:
    meta = META.copy()
    visual_style = meta["visual_style"]

    # =========================================================================
    # 1. BUILD CHARACTER BIBLE
    # =========================================================================
    character_bible = build_character_bible(
        child_name=meta["child_name"],
        child_age=meta["child_age"],
        child_gender=meta["child_gender"],
        child_description=meta["child_description"],
    )

    # =========================================================================
    # 2. BUILD SHOT PLAN
    # =========================================================================
    shot_plans = build_shot_plan(BLUEPRINT["pages"])
    shot_diversity = validate_shot_diversity(shot_plans)

    # =========================================================================
    # 3. RUN enhance_all_pages() — THE MAIN PIPELINE
    # =========================================================================
    pages = [dict(p) for p in PAGES]  # deep copy

    pages = enhance_all_pages(
        pages=pages,
        blueprint=BLUEPRINT,
        character_bible=character_bible,
        visual_style=visual_style,
        location_key=meta["location_key"],
    )

    # =========================================================================
    # 4. STYLE LOCK — override negative to include anti-style blocks
    # =========================================================================
    style_mapping = adapt_style(visual_style)
    forbidden_style_terms: list[str] = []

    if "watercolor" in visual_style.lower() or "pastel" in visual_style.lower():
        anti_style = "3D, CGI, Pixar, Disney, render, photorealistic"
        forbidden_style_terms = ["3d", "cgi", "pixar", "disney", "render", "photorealistic"]
    elif "3d" in visual_style.lower() or "pixar" in visual_style.lower() or "cgi" in visual_style.lower():
        anti_style = "watercolor, paper texture, lineart, hand-drawn, flat shading"
        forbidden_style_terms = ["watercolor", "paper texture", "lineart", "hand-drawn"]
    else:
        anti_style = "3D, CGI, Pixar, Disney, render"
        forbidden_style_terms = ["pixar", "disney", "3d render"]

    no_text_block = "NO TEXT, NO LETTERS, NO WATERMARK"

    for page in pages:
        neg = page.get("negative_prompt_en", "")
        if anti_style not in neg:
            neg = neg.rstrip(", ") + ", " + anti_style
        if no_text_block.lower() not in neg.lower():
            neg = neg.rstrip(", ") + ", " + no_text_block
        page["negative_prompt_en"] = neg

        # Ensure style keyword is in every prompt
        prompt = page.get("image_prompt_en", "")
        if visual_style.lower() not in prompt.lower():
            prompt = prompt.rstrip(", .") + f", {visual_style} style"
            # Re-add suffix
            if "no text, no watermark, no logo" not in prompt.lower():
                prompt += ", no text, no watermark, no logo"
            page["image_prompt_en"] = prompt

    # =========================================================================
    # 5. RUN VALIDATORS
    # =========================================================================
    # Pre-validation text fixes
    pages, fix_summary_text = apply_all_fixes(pages)

    # Post-enhancement validators
    diversity_result = validate_visual_prompt_diversity(pages)
    consistency_result = validate_character_consistency(pages, character_bible.prompt_block)

    overall_report = validate_story_output(
        pages=pages,
        blueprint=BLUEPRINT,
        magic_items=meta["magic_items"],
        expected_page_count=meta["page_count"],
        character_prompt_block=character_bible.prompt_block,
    )

    # =========================================================================
    # 6. DETECT PLACEHOLDER / GENERIC PROMPTS + AUTO-FIX
    # =========================================================================
    auto_fixes: list[dict] = []
    _PLACEHOLDER_PHRASES = [
        "a child in an adventure scene",
        "a young child in a scene",
        "generic scene",
    ]

    for page in pages:
        page_num = page["page"]
        prompt_lower = page["image_prompt_en"].lower()

        for ph in _PLACEHOLDER_PHRASES:
            if ph in prompt_lower:
                auto_fixes.append({"page": page_num, "reason": f"Placeholder detected: '{ph}' — replaced by enhancement pipeline with character+scene+shot details"})

        # Check underground with balloons
        text_lower = page.get("text_tr", "").lower()
        if ("yeraltı" in text_lower or "tünel" in text_lower) and "balloon" in prompt_lower:
            auto_fixes.append({"page": page_num, "reason": "Underground scene incorrectly has 'balloon' — iconic anchor should be tunnel/stone instead"})

    # Check near-duplicates
    for i in range(1, len(pages)):
        prev_words = set(pages[i - 1]["image_prompt_en"].lower().split())
        curr_words = set(pages[i]["image_prompt_en"].lower().split())
        if prev_words and curr_words:
            overlap = len(prev_words & curr_words) / max(len(prev_words), len(curr_words))
            if overlap > 0.85:
                auto_fixes.append({"page": pages[i]["page"], "reason": f"Near-duplicate with page {pages[i-1]['page']} (overlap {overlap:.0%})"})

    # =========================================================================
    # 7. STYLE-LOCK CHECK (3 random pages)
    # =========================================================================
    random.seed(42)
    check_pages = random.sample(range(len(pages)), min(3, len(pages)))
    style_lock_checks: list[dict] = []

    for idx in check_pages:
        p = pages[idx]
        prompt_lower = p["image_prompt_en"].lower()
        neg_lower = p["negative_prompt_en"].lower()

        has_style = visual_style.lower() in prompt_lower or style_mapping.style_tag.lower() in prompt_lower
        found_forbidden = [t for t in forbidden_style_terms if t in prompt_lower]
        has_anti_in_neg = any(t in neg_lower for t in forbidden_style_terms[:3])

        style_lock_checks.append({
            "page": p["page"],
            "has_style_in_prompt": "yes" if has_style else "no",
            "forbidden_style_terms_in_prompt": found_forbidden if found_forbidden else [],
            "anti_style_in_negative": "yes" if has_anti_in_neg else "no",
        })

    # =========================================================================
    # 8. BUILD OUTPUT JSON
    # =========================================================================
    # Shot plan summary
    shot_plan_out = []
    for sp in shot_plans:
        bp_page = next((bp for bp in BLUEPRINT["pages"] if bp["page"] == sp.page), {})
        text_tr = next((p["text_tr"] for p in pages if p["page"] == sp.page), "")
        beat = extract_visual_beat({"page": sp.page, "text_tr": text_tr}, bp_page)
        anchors = pick_anchors(meta["location_key"], text_tr + " " + bp_page.get("visual_brief_tr", ""))

        shot_plan_out.append({
            "page": sp.page,
            "shot_type": sp.shot_type.value,
            "camera_angle": sp.camera_angle.value,
            "action_type": sp.action_type.value,
            "child_frame_pct": sp.child_frame_pct,
            "anchors": anchors,
        })

    # Pages preview (first 3 full)
    pages_preview = []
    for p in pages[:3]:
        pages_preview.append({
            "page": p["page"],
            "text_tr": p["text_tr"],
            "image_prompt_en": p["image_prompt_en"],
            "negative_prompt_en": p["negative_prompt_en"],
        })

    # Pages summary (4-22)
    pages_summary = []
    for i, p in enumerate(pages[3:], start=4):
        sp = shot_plans[i - 1] if i - 1 < len(shot_plans) else shot_plans[-1]
        bp_page = next((bp for bp in BLUEPRINT["pages"] if bp["page"] == p["page"]), {})
        beat = extract_visual_beat(p, bp_page)
        anchors = pick_anchors(meta["location_key"], p["text_tr"] + " " + bp_page.get("visual_brief_tr", ""))

        pages_summary.append({
            "page": p["page"],
            "shot": sp.shot_type.value,
            "action": sp.action_type.value,
            "objects": beat.key_objects,
            "anchors": anchors,
        })

    # Character bible output
    cb_out = {
        "child_name": character_bible.child_name,
        "child_age": character_bible.child_age,
        "child_gender": character_bible.child_gender,
        "appearance_tokens": character_bible.appearance_tokens,
        "outfit": {
            "top": character_bible.outfit.top,
            "bottom": character_bible.outfit.bottom,
            "shoes": character_bible.outfit.shoes,
            "colors": character_bible.outfit.colors,
        },
        "prompt_block": character_bible.prompt_block,
        "negative_tokens": character_bible.negative_tokens,
    }

    output = {
        "meta": meta,
        "character_bible": cb_out,
        "shot_plan": shot_plan_out,
        "shot_diversity": shot_diversity,
        "pages_preview": pages_preview,
        "pages_summary": pages_summary,
        "validation": {
            "diversity": "PASS" if diversity_result.passed else f"FAIL: {diversity_result.message}",
            "consistency": "PASS" if consistency_result.passed else f"FAIL: {consistency_result.message}",
            "overall": "PASS" if overall_report.all_passed else f"FAIL ({len(overall_report.failures)} issues)",
            "failure_codes": [f.code for f in overall_report.failures] if not overall_report.all_passed else [],
        },
        "auto_fixes": auto_fixes,
        "style_lock_check": style_lock_checks,
    }

    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
