"""Legacy 3-pass pipeline (V1/V2 compatibility).

Extracted from _story_writer.py.  Provides _LegacyPassesMixin which is
inherited by _StoryWriterMixin → GeminiService.

These passes are superseded by the V3 blueprint pipeline (generate_story_v3)
but kept for backward-compat with older order flows.
"""

from __future__ import annotations

import json

import httpx
import structlog

from app.core.exceptions import AIServiceError
from app.core.sanitizer import sanitize_for_prompt
from app.models.scenario import Scenario
from app.services.ai._helpers import (
    AI_DIRECTOR_SYSTEM,
    PURE_AUTHOR_SYSTEM,
    _extract_text_from_parts,
    get_gemini_story_url,
    get_gemini_technical_url,
)
from app.services.ai._models import PageContent, StoryResponse

logger = structlog.get_logger()


class _LegacyPassesMixin:
    """Mixin providing legacy PASS-1 (Pure Author) and PASS-2 (Technical Director)."""

    async def _pass1_write_story(
        self,
        scenario: Scenario,
        child_name: str,
        child_age: int,
        child_gender: str,
        page_count: int = 16,
        cultural_elements: dict | None = None,
        extra_instructions: str = "",
    ) -> str:
        """
        PASS 1: Pure Author - Generate beautiful story TEXT ONLY.

        Uses prompt_engine.story_prompt_composer for task prompt; PURE_AUTHOR_SYSTEM from DB.
        extra_instructions: appended to task (e.g. no_family retry strengthening).
        """
        child_name = sanitize_for_prompt(child_name, max_length=50, field_name="child_name")

        from app.prompt_engine import compose_story_prompt

        task_prompt = compose_story_prompt(
            scenario, child_name, child_age, child_gender, page_count
        )
        if extra_instructions:
            task_prompt = task_prompt + "\n\n" + extra_instructions.strip()

        cultural_prompt = ""
        if cultural_elements:
            primary = cultural_elements.get("primary", [])
            colors = cultural_elements.get("colors", "")
            cultural_prompt = f"""
ğŸ¨ KÜLTÜREL ELEMENTLER:
Atmosfer elementleri: {", ".join(primary) if primary else "Genel"}
Renk paleti: {colors if colors else "Doğal"}
Bu elementleri hikayeye doğal şekilde yedir.
"""
            logger.info("SCENARIO TEMPLATE: Using cultural_elements", elements=cultural_elements)

        system_prompt = await self._get_prompt("PURE_AUTHOR_SYSTEM", PURE_AUTHOR_SYSTEM)
        author_prompt = system_prompt + "\n\n" + task_prompt
        if cultural_prompt:
            author_prompt += "\n\n" + cultural_prompt

        import asyncio as _asyncio_p1

        story_url = get_gemini_story_url()
        _p1_max_retries = 3
        _p1_base_wait = 10  # seconds

        for _p1_attempt in range(_p1_max_retries):
            try:
                logger.info(
                    "PASS 1: Pure Author - Writing story",
                    model=self.story_model,
                    temperature=self.story_temperature,
                    child_name=child_name,
                    scenario=scenario.name if scenario else "?",
                    attempt=_p1_attempt + 1,
                )

                client = self._get_gemini_client()
                response = await client.post(
                    f"{story_url}?key={self.api_key}",
                    json={
                        "contents": [{"parts": [{"text": author_prompt}]}],
                        "generationConfig": {
                            "temperature": self.story_temperature,
                            "topK": 64,
                            "topP": 0.95,
                            "maxOutputTokens": 32000,
                        },
                        "safetySettings": [
                            {
                                "category": "HARM_CATEGORY_HARASSMENT",
                                "threshold": "BLOCK_MEDIUM_AND_ABOVE",
                            },
                            {
                                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                                "threshold": "BLOCK_MEDIUM_AND_ABOVE",
                            },
                            {
                                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                                "threshold": "BLOCK_MEDIUM_AND_ABOVE",
                            },
                            {
                                "category": "HARM_CATEGORY_HATE_SPEECH",
                                "threshold": "BLOCK_MEDIUM_AND_ABOVE",
                            },
                        ],
                    },
                )
                response.raise_for_status()

                data = response.json()
                parts = data["candidates"][0]["content"]["parts"]
                story_text = _extract_text_from_parts(parts)

                logger.info(
                    "PASS 1 Complete: Story written",
                    story_length=len(story_text),
                    preview=story_text[:200] + "...",
                )

                return story_text

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429 and _p1_attempt < _p1_max_retries - 1:
                    wait = _p1_base_wait * (2 ** _p1_attempt)
                    logger.warning(
                        "PASS 1 rate limited (429) — retrying",
                        attempt=_p1_attempt + 1,
                        wait_seconds=wait,
                    )
                    await _asyncio_p1.sleep(wait)
                    continue
                logger.error("PASS 1 Failed (HTTP)", error=str(e))
                raise AIServiceError("Gemini", f"Hikaye yazılamadı: {str(e)}")
            except Exception as e:
                logger.error("PASS 1 Failed", error=str(e))
                raise AIServiceError("Gemini", f"Hikaye yazılamadı: {str(e)}")

        raise AIServiceError("Gemini", "Hikaye yazma tüm denemelerde başarısız (rate limit).")

    # =========================================================================
    # PASS 2: TECHNICAL DIRECTOR - Format & Scene Descriptions
    # =========================================================================

    async def _pass2_format_story(
        self,
        story_text: str,
        child_name: str,
        child_age: int,
        child_gender: str,
        visual_character_description: str = "",
        scenario_name: str = "",
        location_constraints: str = "",
        fixed_outfit: str = "",
        expected_page_count: int = 0,
    ) -> StoryResponse:
        """
        PASS 2: Technical Director - Format story and generate SCENE DESCRIPTIONS.

        ⚠ï¸ IMPORTANT: This generates scene_description WITHOUT style!
        Style is added later in _compose_visual_prompts (SINGLE SOURCE OF TRUTH).

        Takes the beautiful story from Pass 1 and:
        - Splits into pages
        - Generates scene descriptions for each page (NO STYLE!)
        - Outputs structured JSON

        Args:
            story_text: Beautiful story from Pass 1
            visual_character_description: DOUBLE LOCKING character description
            scenario_name: Scenario name for location context
            location_constraints: Required location elements from scenario
            fixed_outfit: Consistent clothing for all pages (outfit lock)

        Returns:
            StoryResponse with pages and scene descriptions (NO STYLE!)
        """
        # ========== INPUT SANITIZATION (Security) ==========
        child_name = sanitize_for_prompt(child_name, max_length=50, field_name="child_name")

        # Use "child" instead of "boy/girl" to prevent diffusion model from
        # overriding PuLID face reference with a generic gendered archetype.
        clothing = (fixed_outfit or "").strip()

        # Character description for scene descriptions
        if visual_character_description:
            char_desc = sanitize_for_prompt(
                visual_character_description, max_length=300, field_name="char_desc"
            )
        else:
            char_desc = f"a {child_age}-year-old child named {child_name}"

        # ========== LOCATION CONSTRAINTS FROM SCENARIO ==========
        location_hint = ""
        if location_constraints:
            location_hint = f"""
ğŸ“ LOKASYON KISITLAMALARI (HER SAHNEDE KULLAN!):
{location_constraints}
ASLA bu lokasyon dışında mekan yazma!
"""

        # Scenario context
        scenario_hint = ""
        if scenario_name:
            scenario_hint = f"""
ğŸ—ºï¸ SENARYO: {scenario_name}
Tüm sahneler bu senaryoya uygun olmalı!
"""

        # ========== DYNAMIC PROMPT LOADING ==========
        # Fetch system prompt from database (with hardcoded fallback)
        director_system = await self._get_prompt("AI_DIRECTOR_SYSTEM", AI_DIRECTOR_SYSTEM)

        technical_prompt = f"""{director_system}
{scenario_hint}
{location_hint}

ğŸ¬ TEKNİK YÖNETMENLİK GÖREVİN:

Aşağıdaki güzel hikayeyi al ve TEKNİK FORMATA dönüştür.
HİKAYE METNİNİ DEÄİÅTİRME - sadece sayfalara böl ve SAHNE TANIMI ekle!

ğŸ“ SAYFA SAYISI KURALI (ÇOK ÖNEMLİ!):
Hikayeyi TAM {expected_page_count if expected_page_count > 0 else 'uygun sayıda'} sayfaya böl.
{'KAPAK (page_number: 0) + İÇ SAYFALAR (page_number: 1 ile ' + str(expected_page_count - 1) + ').' if expected_page_count > 0 else ''}
{'TOPLAM ' + str(expected_page_count) + ' adet page objesi döndür — ne eksik ne fazla!' if expected_page_count > 0 else ''}

⚠ï¸ ÖNEMLİ: scene_description içinde STYLE OLMAYACAK!
Style (Pixar, anime, watercolor vb.) ayrıca eklenecek - sen SADECE sahneyi tarif et!

ğŸ“– HİKAYE:
{story_text}

ğŸ“š KİTAP ADI KURALI (ÇOK ÖNEMLİ!):
title alanına KİÅİSELLEÅTİRİLMİÅ kitap adı yaz! Çocuğun adını İÇERMELİ!
✅ DOÄRU örnekler: "{child_name}'ın Kapadokya Macerası", "{child_name}'ın Büyülü Yolculuğu", "{child_name} ve Peri Bacaları"
âŒ YANLIÅ: "Hikaye", "Masal", "Macera", "Bir Hikaye" — bunlar YASAK!

ğŸ“‹ ÇIKTI FORMATI (JSON):
⛔ KAPAK KURALI (KESİNLİKLE UYULACAK):
- page_number=0 "text" alanına SADECE kitap başlığını yaz — "title" alanıyla AYNI olmalı!
- page_number=0 "text" alanına HİÇBİR HİKAYE CÜMLESİ YAZMA! Hikaye page_number=1'den başlar.
- page_number=1 = hikayenin GERÇEK 1. sayfası (ilk paragraf buraya gelir)
{{
  "title": "{child_name}'ın Büyülü Macerası",
  "pages": [
    {{
      "page_number": 0,
      "text": "{child_name}'ın Büyülü Macerası",
      "scene_description": "[LOCATION]. A {child_age}-year-old child named {child_name} [ACTION]. Warm light. Clear sky in upper third for title."
    }},
    {{
      "page_number": 1,
      "text": "Hikayenin İLK PARAGRAFI (giriş) — [SAYFA 1] ile başlayan metin. DEÄİÅTİRME!",
      "scene_description": "[LOCATION and setting]. A {child_age}-year-old child named {child_name} [ACTION]. [LIGHTING]."
    }},
    ... (page 2, 3, ... tüm iç sayfalar)
  ]
}}

â­ KARAKTER KİMLİÄİ (Referans — scene_description'a KOPYALAMA, sadece isim ve aksiyon yaz):
Çocuğun kimliği: "{char_desc}"
Bu bilgiyi scene_description'a YAZMA — sistem karakter bloğunu şablonla otomatik ekler.
scene_description'da sadece "{child_name}" ismini kullan, fiziksel tanım YAZMA.

ğŸ‘” KIYAFET: scene_description'a kıyafet YAZMA! Sistem "{clothing}" kıyafetini şablonla otomatik ekler.
Sadece aksesuar/ekipman yazabilirsin: sırt çantası, büyüteç, harita vb.
⛔ DÖNEM KIYAFETİ YASAK: Tarihsel mekanlarda bile çocuğu dönem kıyafeti ile TANIMLAMAYACAKSIN! "wearing tunic", "animal skin wrap", "toga", "loincloth" gibi dönem kıyafetleri YAZMA! Çocuk KENDİ günlük kıyafetlerini giyer — sistem bunu yönetir.

ğŸ’‡ SAÇ: scene_description'a saç tasviri YAZMA! Sistem saç bilgisini şablonla otomatik ekler. "long hair", "curly hair", "braids" gibi saç ifadeleri KULLANMA!

âŒ SCENE_DESCRIPTION İÇİNDE BUNLAR OLMAYACAK:
- Pixar, Disney, Ghibli, anime, cartoon, watercolor gibi STYLE kelimeleri
- "Children's book illustration", "storybook style" gibi ifadeler
- Art style referansları

✅ SCENE_DESCRIPTION (tekrarsız, 2–4 cümle — görselde hikaye detayı zengin olsun):
- Fiziksel mekan ve ortam detayları (lokasyon kısıtlamalarına uygun; ikonik öğeler: bacalar, balonlar, mağara girişi vb.)
- Karakter AKSİYONU ve POZ (en önemli)
- Hikayedeki nesneler/aksesuarlar/evcil hayvan (sincap, kedi, çanta, büyüteç vb.) sahneye dahil et
- Işık (sahneye uygun kısa ifade; sen seç)
- Kompozisyon/çerçeve YAZMA: "wide shot", "full body visible", "child 30%", "environment 70%", "natural proportions", "same clothing on every page" — sistem bunları TEK SEFER ekler. Sen yazma!
- Sinematik/lens YOK: wide-angle, f/8, cinematic, epic YOK

ğŸ¬ AKSİYON KURALI (ÇOK ÖNEMLİ!):
Çocuk HER SAHNEDE aktif olmalı — sadece durup bakmak YASAK!
Hikayedeki eylemleri sahne açıklamasına YANSIT:
- Hikayede kaplumbağa görüyorsa → "kneeling down to gently touch a small turtle"
- Hikayede balık izliyorsa → "leaning over the railing to watch the fish swimming below"
- Hikayede mağara keşfediyorsa → "stepping into a dark cave entrance holding a lantern"
- Hikayede balona biniyorsa → "leaning excitedly over the basket edge of a hot air balloon"
- Hikayede harita buluyorsa → "unrolling an old map on a stone surface, eyes wide"
Çocuğun yüz ifadesi hikayeyle uyumlu olmalı (merak, heyecan, şaşkınlık, korku vb.)

ğŸ¿ï¸ ÖNEMLİ GÖRSEL ÖÄELER (Hikaye–görsel uyumu):
Hikayedeki önemli öğeleri scene_description'a MUTLAKA dahil et: evcil hayvanlar (sincap, kedi, kaplumbağa vb.), çantalar, eşyalar, aksesuarlar.
Örn: Omuzda sincap varsa "with a small pet squirrel on her shoulder" ekle. Çantada büyüteç varsa "with a magnifying glass in her backpack" ekle.

ğŸ¾ HAYVAN TUTARLILIÄI (ÇOK KRİTİK!):
Hikayede bir hayvan arkadaş varsa, scene_description'da HER SAYFADA AYNI FİZİKSEL TANIMI kullan!
İlk göründüğü sayfadaki tanımı (renk, tür, boyut) birebir KOPYALA ve her sayfada tekrarla.
Örnek: İlk sayfa "a small white fluffy dog with brown ears" → TÜM sayfalarda aynısını yaz!
ASLA sayfalar arasında hayvanın rengini, boyutunu, türünü DEÄİÅTİRME!

⚠ï¸ ANATOMİK DOÄRULUK:
Hayvanlar insan gibi davranamaz. "holding hands with a dog" YASAKDIR — köpeğin eli yok!
Doğru: "running alongside the dog", "the dog trotting beside the child", "petting the dog"
Hayvanları GERÇEK hayvan davranışlarıyla tanımla!

⚠ï¸ KRİTİK KURALLAR:
1. HİKAYE METNİNİ DEÄİÅTİRME! Yazarın yazdığını koru!
2. scene_description zengin ama tekrarsız: mekan + ortam detayları + aksiyon + önemli nesneler/evcil hayvan + ışık (2–4 cümle). Görselde hikaye detayı net görünsün. Işığı sahneye göre sen seç. Aynı fikri iki kez yazma!
3. scene_description içinde STYLE ve KOMPOZİSYON YOK: "2D", "3D", "Pixar", "illustration", "watercolor", "storybook", "wide shot", "full body visible", "child 30%", "same clothing on every page", "natural proportions" YAZMA — sistem ekler!
4. Lokasyon MUTLAKA senaryo kısıtlamalarına uygun!
5. Kapak (page 0) için: scene_description iç sayfalarla AYNI TONDA olmalı — çocuk bir aksiyon/sahne içinde, lokasyon arka planda. "A breathtaking panoramic view" gibi EPIK/PANORAMIK ifadeler KULLANMA! İç sayfayla aynı format: mekan + çocuğun aksiyonu + ışık. Üst kısım açık gökyüzü/boşluk olsun.
6. scene_description SADECE İNGİLİZCE! Türkçe (Geniş çekim, Altta metin alanı vb.) KULLANMA!
7. ⛔ scene_description'a ASLA Türkçe hikaye metnini KOPYALAMA! "text" alanındaki Türkçe metin ile "scene_description" tamamen FARKLI olmalı. scene_description = İngilizce görsel sahne tasviri. text = Türkçe hikaye metni. ASLA birbirinin kopyası olmasın!
8. ⛔ Kapak (page 0) "text" alanına SADECE kişiselleştirilmiş Türkçe KİTAP BAÅLIÄI yaz ("{child_name}" + senaryo adı). ASLA "Hikaye", "Masal" gibi genel isimler koyma! Kapak sayfasına HİKAYE METNİ (paragraf, giriş, cümle) YAZMA — kapakta sadece başlık gösterilir, hikaye metni orada kullanılmaz.
9. ⛔ Hikaye metni MUTLAKA sayfa 1'den başlar. İlk paragrafı (giriş) page 1 "text" alanına koy. Böylece kitap açıldığında 1. sayfa hikayenin başlangıcı olur; kapakta yazdığın metin boşta kalmaz.

ÅİMDİ JSON DÖNDÜR:"""

        import asyncio as _asyncio

        technical_url = get_gemini_technical_url()
        _pass2_max_retries = 4
        _pass2_base_wait = 8  # saniye — free tier 15 RPM; kısa beklemeler yetmiyor

        raw_text = ""
        for _p2_attempt in range(_pass2_max_retries):
            try:
                logger.info(
                    "PASS 2: Technical Director - Formatting",
                    model=self.technical_model,
                    story_length=len(story_text),
                    attempt=_p2_attempt + 1,
                )

                client = self._get_gemini_client()
                response = await client.post(
                    f"{technical_url}?key={self.api_key}",
                    json={
                        "contents": [{"parts": [{"text": technical_prompt}]}],
                        "generationConfig": {
                            "temperature": 0.5,
                            "topK": 40,
                            "topP": 0.9,
                            "maxOutputTokens": 65536,
                            "responseMimeType": "application/json",
                        },
                        "safetySettings": [
                            {
                                "category": "HARM_CATEGORY_HARASSMENT",
                                "threshold": "BLOCK_MEDIUM_AND_ABOVE",
                            },
                            {
                                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                                "threshold": "BLOCK_MEDIUM_AND_ABOVE",
                            },
                            {
                                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                                "threshold": "BLOCK_MEDIUM_AND_ABOVE",
                            },
                            {
                                "category": "HARM_CATEGORY_HATE_SPEECH",
                                "threshold": "BLOCK_MEDIUM_AND_ABOVE",
                            },
                        ],
                    },
                )
                response.raise_for_status()

                data = response.json()
                parts = data["candidates"][0]["content"]["parts"]
                raw_text = _extract_text_from_parts(parts)

                story_data = self._extract_and_repair_json(raw_text)
                story_response = StoryResponse(**story_data)

                actual_count = len(story_response.pages)
                logger.info(
                    "PASS 2 Complete: Story formatted",
                    title=story_response.title,
                    page_count=actual_count,
                    expected_page_count=expected_page_count,
                )

                # Page count validation — retry if mismatch (tolerance ±1)
                if expected_page_count > 0:
                    diff = actual_count - expected_page_count
                    if abs(diff) > 1 and _p2_attempt < _pass2_max_retries - 1:
                        logger.warning(
                            "PASS 2 page count mismatch — retrying",
                            expected=expected_page_count,
                            actual=actual_count,
                            attempt=_p2_attempt + 1,
                        )
                        await _asyncio.sleep(2)
                        continue
                    if diff > 0:
                        logger.warning(
                            "PASS 2 trimming excess pages",
                            expected=expected_page_count,
                            actual=actual_count,
                            trimmed=diff,
                        )
                        story_response.pages = story_response.pages[:expected_page_count]
                    elif diff < 0:
                        logger.warning(
                            "PASS 2 page count shortage (accepted after retries)",
                            expected=expected_page_count,
                            actual=actual_count,
                            shortage=abs(diff),
                        )

                # ── Kapak sayfası metin düzeltmesi ──
                # AI bazen page_number=0'a hikaye metni koyuyor. Eğer kapak metni
                # başlıkla eşleşmiyorsa (hikaye paragrafı ise), o metni page_number=1
                # olarak öne ekle ve diğer sayfaları kaydır — böylece 1. sayfa metni kaybolmaz.
                _cover_page = next((p for p in story_response.pages if p.page_number == 0), None)
                if _cover_page and story_response.title:
                    _cover_text = (_cover_page.text or "").strip()
                    _title_text = story_response.title.strip()
                    # Kapak metni başlıkla eşleşmiyorsa ve 30 karakterden uzunsa hikaye metnidir
                    _is_story_text = (
                        _cover_text != _title_text
                        and len(_cover_text) > 30
                        and not _cover_text.lower().startswith(_title_text[:10].lower())
                    )
                    if _is_story_text:
                        logger.warning(
                            "COVER_TEXT_IS_STORY: page_number=0 contains story text, rescuing as page 1",
                            cover_text_preview=_cover_text[:80],
                            title=_title_text,
                        )
                        # Kapak metnini başlıkla düzelt
                        _cover_page.text = _title_text
                        # Kurtarılan metni page_number=1 olarak öne ekle.
                        # scene_description olarak mevcut page_number=1'inkini kullan (varsa),
                        # yoksa kapak sahnesini kullan (görsel üretimde yine de çalışır).
                        _existing_p1 = next((p for p in story_response.pages if p.page_number == 1), None)
                        _rescued_scene = (
                            _existing_p1.scene_description if _existing_p1 else _cover_page.scene_description
                        )
                        _rescued_page = PageContent(
                            page_number=1,
                            text=_cover_text,
                            scene_description=_rescued_scene,
                        )
                        _other_pages = [p for p in story_response.pages if p.page_number != 0]
                        # Kaydır: her sayfanın page_number'ını +1 artır
                        for _p in _other_pages:
                            _p.page_number += 1
                        # Yeni listeyi oluştur: kapak + kurtarılan sayfa + diğerleri
                        story_response.pages = (
                            [_cover_page, _rescued_page] + _other_pages
                        )
                        logger.info(
                            "COVER_TEXT_RESCUED: page count after rescue",
                            page_count=len(story_response.pages),
                        )

                return story_response

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429 and _p2_attempt < _pass2_max_retries - 1:
                    wait = _pass2_base_wait * (2 ** _p2_attempt)
                    logger.warning(
                        "PASS 2 rate limited (429) — retrying",
                        attempt=_p2_attempt + 1,
                        wait_seconds=wait,
                    )
                    await _asyncio.sleep(wait)
                    continue
                logger.error("PASS 2 Failed (HTTP)", error=str(e))
                raise AIServiceError("Gemini", f"Teknik formatlama başarısız: {str(e)}")

            except json.JSONDecodeError as e:
                logger.error(
                    "PASS 2 JSON Parse Error",
                    error=str(e),
                    raw_preview=raw_text[-500:] if raw_text else "N/A",
                )
                raise AIServiceError("Gemini", "Hikaye formatlanamadı.")
            except Exception as e:
                logger.error("PASS 2 Failed", error=str(e))
                raise AIServiceError("Gemini", f"Teknik formatlama başarısız: {str(e)}")

        raise AIServiceError("Gemini", "Teknik formatlama tüm denemelerde başarısız (rate limit).")
