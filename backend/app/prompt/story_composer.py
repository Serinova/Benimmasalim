"""PASS-1 hikaye yazım prompt'u: Senaryo + Çocuk Bilgisi → TR system prompt.

Gemini'ye gönderilecek hikaye yazım prompt'unu oluşturur.
Senaryo metni ve çocuk bilgileri burada birleştirilir.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

import structlog

from app.prompt.templates import STORY_NO_FIRST_DEGREE_FAMILY_TR

if TYPE_CHECKING:
    from app.models.scenario import Scenario

logger = structlog.get_logger()


def compose_story_prompt(
    scenario: Scenario,
    child_name: str,
    child_age: int,
    child_gender: str,
    page_count: int = 6,
) -> str:
    """Gemini PASS-1 için Türkçe system prompt oluşturur."""
    story_prompt = (
        getattr(scenario, "story_prompt_tr", None)
        or getattr(scenario, "ai_prompt_template", None)
        or ""
    )

    location_en = getattr(scenario, "location_en", None) or ""
    flags: dict = getattr(scenario, "flags", None) or {}
    no_family = flags.get("no_family", False)
    gender_tr = "erkek çocuk" if child_gender == "erkek" else "kız çocuk"

    pg_intro = max(1, math.floor(page_count * 0.15))
    pg_problem = max(2, math.floor(page_count * 0.20))
    pg_crisis = max(1, math.floor(page_count * 0.15))
    pg_learning = max(2, math.floor(page_count * 0.25))
    pg_apply = max(1, math.floor(page_count * 0.15))
    subtotal = pg_intro + pg_problem + pg_crisis + pg_learning + pg_apply
    pg_ending = max(1, page_count - subtotal)

    while (pg_intro + pg_problem + pg_crisis + pg_learning + pg_apply + pg_ending) > page_count:
        if pg_learning > 2:
            pg_learning -= 1
        elif pg_problem > 2:
            pg_problem -= 1
        elif pg_apply > 1:
            pg_apply -= 1
        elif pg_intro > 1:
            pg_intro -= 1
        else:
            break

    sections: list[str] = []

    sections.append(
        f"Sen ödüllü bir çocuk kitabı yazarısın.\n"
        f"Görevin: {child_name} adlı {child_age} yaşındaki {gender_tr} için "
        f"{page_count} sayfalık, BAŞTAN SONA TUTARLI BİR KURGUSU olan hikaye yazmak.\n\n"
        f"⚡ KRİTİK: Her sayfa bir öncekinin DEVAMI olmalı. Kopuk sahneler YASAK!\n"
        f"Hikaye bir ROMAN gibi akmalı — her sayfa neden-sonuç zinciriyle bağlı."
    )

    if story_prompt:
        sections.append(f"🎭 SENARYO TALİMATLARI:\n{story_prompt}")

    if location_en:
        sections.append(
            f"📍 LOKASYON: Tüm sahneler {location_en} bölgesinde geçmeli. "
            f"Lokasyonu ARKA PLAN olarak kullan, turistik bilgi verme!"
        )

    sections.append(
        f"📐 DRAMATİK YAY — SAYFA DAĞILIMI ({page_count} sayfa):\n\n"
        f"BÖLÜM 1 — GİRİŞ (Sayfa 1-{pg_intro}):\n"
        f"  → {child_name}'ın kişiliğini ve ZAYIF YANINI tanıt.\n"
        f"  → Sorunun tohumunu ek: uyarıyı dinlemeyen, inatçı, korkak vb.\n\n"
        f"BÖLÜM 2 — SORUN BÜYÜYOR (Sayfa {pg_intro + 1}-{pg_intro + pg_problem}):\n"
        f"  → Zayıf yandan dolayı işler kötüye gidiyor.\n"
        f"  → İnatçılığın / yanlış davranışın SONUÇLARI ortaya çıkıyor.\n"
        f"  → Gerilim artıyor, her sayfa durumu biraz daha kötüleştiriyor.\n\n"
        f"BÖLÜM 3 — KRİZ + MENTOR (Sayfa {pg_intro + pg_problem + 1}-{pg_intro + pg_problem + pg_crisis}):\n"
        f"  → En kötü an: düşme, utanma, kaybolma, başarısızlık.\n"
        f"  → Bir MENTOR belirir (yaşlı usta, konuşan hayvan, peri, bilge figür).\n"
        f"  → Mentor yargılamaz, çocuğu ANLAR ve ona bir GÖREV verir.\n\n"
        f"BÖLÜM 4 — ÖĞRENME + METAFOR (Sayfa {pg_intro + pg_problem + pg_crisis + 1}-{pg_intro + pg_problem + pg_crisis + pg_learning}):\n"
        f"  → Mentor bir METAFOR / ARAÇ / OYUN ile dersi öğretir.\n"
        f"  → Çocuk önce BAŞARISIZ olur (acelecilik, dikkatsizlik).\n"
        f"  → Durur, düşünür, tekrar dener → BAŞARIR!\n"
        f"  → Ders söylenmiyor, çocuk yaşayarak buluyor.\n\n"
        f"BÖLÜM 5 — UYGULAMA (Sayfa {pg_intro + pg_problem + pg_crisis + pg_learning + 1}-{pg_intro + pg_problem + pg_crisis + pg_learning + pg_apply}):\n"
        f"  → Öğrendiğini gerçek durumda uygular.\n"
        f"  → Eski alışkanlık aklına gelir ama DOĞRU SEÇİMİ yapar.\n"
        f"  → 'Eskiden olsa koşardı ama şimdi durdu, düşündü.'\n\n"
        f"BÖLÜM 6 — KAPANIŞ (Sayfa {page_count - pg_ending + 1}-{page_count}):\n"
        f"  → {child_name} değişmiş, büyümüş.\n"
        f"  → Güçlü kapanış: 'Ben artık Akıllı {child_name}!'ım!'\n"
        f"  → Başlangıçtaki zayıf {child_name} ile sondaki güçlü {child_name} KONTRASTI."
    )

    sections.append(f"🚫 {STORY_NO_FIRST_DEGREE_FAMILY_TR}")

    if no_family:
        sections.append(
            "🚫🚫🚫 AİLE KISITLAMASI (senaryo kuralı — İHLAL EDİLEMEZ!) 🚫🚫🚫\n"
            "Bu hikayede ASLA şunlar GEÇMEYECEK: anne, baba, kardeş, abla, abi, dede, nine,\n"
            "babaanne, anneanne, aile, ebeveyn — ve bunların ekleri (annesi, babası, annem, babam vb.).\n"
            "Çocuk macerayı TEK BAŞINA veya hayvan/hayali arkadaşlarıyla yaşamalı.\n"
            "'Annesi söyledi', 'babası götürdü', 'ailesiyle geldi' gibi ifadeler KESİNLİKLE YASAK!\n"
            "Hikayenin başında çocuk ZATEN orada — nasıl geldiği anlatılmaz.\n"
            "Yardımcı karakter: hayvan arkadaş veya bilge mentor (usta, peri, yaşlı adam vb.)."
        )

    sections.append(
        f"Her sayfa 2-4 cümle olmalı (diyaloglar dahil).\n"
        f"Sayfa sayısı: TAM {page_count} sayfa.\n"
        f"Dil: Türkçe.\n"
        f"Çocuğun adı: {child_name}, Yaş: {child_age}, Cinsiyet: {gender_tr}.\n\n"
        f"⚡ SON HATIRLATMA: Sayfalar arası NEDEN-SONUÇ bağlantısı KESİNLİKLE olmalı!\n"
        f"Her sayfa bir öncekini referans almalı. Kopuk sahneler = BAŞARISIZ hikaye.\n\n"
        f"🐾 HAYVAN TUTARLILIĞI: Hikayede bir hayvan arkadaş varsa (köpek, kedi, sincap vb.),\n"
        f"o hayvanın rengi, türü ve boyutu TÜM SAYFALARDA AYNI kalmalı!\n"
        f"İlk tanımladığın hayvanı SON SAYFAYA KADAR değiştirme!\n\n"
        f"❌ ANATOMİK KURAL: Hayvanlar insan gibi davranamaz!\n"
        f"'El ele tutuştular' (köpeğin eli yok!), 'kucaklaştılar' gibi imkansız sahneler YASAK!\n"
        f"Doğru: 'Köpek yanında koşuyordu', 'Sincap omzuna atladı', 'Kedi bacağına sürtündü'"
    )

    prompt = "\n\n".join(sections)

    logger.info(
        "story_prompt_composed",
        scenario=getattr(scenario, "name", "?"),
        has_location=bool(location_en),
        no_family=no_family,
        prompt_length=len(prompt),
    )

    return prompt
