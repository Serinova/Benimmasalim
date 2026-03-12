#!/usr/bin/env python3
"""Toplu Senaryo Kalite Denetim Scripti — audit_all_scenarios.py

Tüm kayıtlı senaryoları otomatik tarayıp kalite raporu üretir.
Kapadokya sipariş analizinden öğrenilen kontrolleri uygular.

Kullanım:
    cd backend
    python scripts/audit_all_scenarios.py

Sonuç: Markdown raporu stdout'a yazılır.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

# Proje kökünü ekle
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.scenarios._base import ScenarioContent
from app.scenarios._registry import _load_all_scenarios, get_all_scenarios


# ═══════════════════════════════════════════════════════════════
# KONFİGÜRASYON
# ═══════════════════════════════════════════════════════════════

# Sihir/büyü kelime listesi (hikaye prompt'unda yasaklanması gereken)
MAGIC_KEYWORDS_TR = {
    "büyü", "sihir", "sihirli", "büyülü", "peri", "melek", "cin",
    "levitasyon", "ışınlanma", "uçma", "uçuyor",
    "parlayan küre", "enerji yayan", "havada asılı",
    "sihirli ağaç", "kristal mağara", "büyülü dünya",
}

# Yasaklanması gereken mekan kelimeleri (Kapadokya dışına sapma)
FORBIDDEN_LOCATION_WORDS_EN = {
    "forest", "tropical island", "floating island", "crystal cave",
    "magical tree", "enchanted garden", "underwater world",
    "fairy kingdom", "magical realm",
}

# Tek çocuk zorlama kelimeleri
SINGLE_CHILD_MARKERS = {"EXACTLY ONE", "only ONE child", "no duplicate", "no twin", "no second child"}


# ═══════════════════════════════════════════════════════════════
# KONTROL FONKSİYONLARI
# ═══════════════════════════════════════════════════════════════

@dataclass
class Issue:
    """Tek bir sorun kaydı."""
    severity: str  # 🔴 KRİTİK, 🟡 UYARI, 🟢 ÖNERİ
    code: str
    message: str


@dataclass
class ScenarioReport:
    """Tek senaryo için denetim sonucu."""
    theme_key: str
    name: str
    score: int = 0
    max_score: int = 0
    issues: list[Issue] = field(default_factory=list)

    @property
    def grade(self) -> str:
        pct = (self.score / self.max_score * 100) if self.max_score else 0
        if pct >= 90:
            return "🏆 A"
        if pct >= 75:
            return "✅ B"
        if pct >= 60:
            return "🟡 C"
        if pct >= 40:
            return "🟠 D"
        return "🔴 F"

    def add(self, points: int, max_pts: int, severity: str, code: str, msg: str):
        self.score += points
        self.max_score += max_pts
        if points < max_pts:
            self.issues.append(Issue(severity=severity, code=code, message=msg))


def audit_scenario(sc: ScenarioContent) -> ScenarioReport:
    """15+ kontrol ile tek senaryoyu denetle."""
    r = ScenarioReport(theme_key=sc.theme_key, name=sc.name)

    # ── 1. story_prompt_tr Uzunluğu ──
    prompt = sc.story_prompt_tr or ""
    wc = len(prompt.split())
    if wc >= 700:
        r.add(10, 10, "🟢", "PROMPT_LEN", f"Prompt uzunluğu: {wc} kelime ✅")
    elif wc >= 500:
        r.add(7, 10, "🟡", "PROMPT_LEN", f"Prompt {wc} kelime — 700+ önerilir")
    elif wc >= 300:
        r.add(4, 10, "🟡", "PROMPT_LEN", f"Prompt {wc} kelime — kısa, 500+ olmalı")
    else:
        r.add(0, 10, "🔴", "PROMPT_LEN", f"Prompt {wc} kelime — ÇOK KISA")

    # ── 2. No-magic Kuralı (MUTLAK YASAKLAR) ──
    prompt_lower = prompt.lower()
    has_no_magic_rule = any(kw in prompt_lower for kw in [
        "sihir yok", "büyü yok", "sihir yasak", "büyü yasak",
        "sihirli değil", "no magic", "no_magic",
        "mutlak yasak", "kesinlikle yok",
    ])
    no_magic_flag = sc.flags.get("no_family", False)  # no_magic ayrı flag değil

    bible_no_magic = sc.scenario_bible.get("no_magic", False)

    if has_no_magic_rule and bible_no_magic:
        r.add(5, 5, "🟢", "NO_MAGIC", "No-magic kuralı hem prompt'ta hem bible'da var ✅")
    elif has_no_magic_rule or bible_no_magic:
        r.add(3, 5, "🟡", "NO_MAGIC", "No-magic kuralı sadece bir yerde var — ikisinde de olmalı")
    else:
        r.add(0, 5, "🔴", "NO_MAGIC", "No-magic kuralı YOK — AI sihir üretebilir!")

    # ── 3. Companion Tanımı ──
    if sc.companions:
        r.add(3, 3, "🟢", "COMPANION_DEF", f"{len(sc.companions)} companion tanımlı ✅")
    else:
        r.add(0, 3, "🔴", "COMPANION_DEF", "Companion tanımlı değil")

    # ── 4. Companion Tür Kilidi (kelebek gibi yanlış türlerin yasaklanması) ──
    has_companion_type_lock = any(kw in prompt_lower for kw in [
        "hayvan", "asla kelebek", "kelebek yasak", "peri yasak",
        "sihirli yaratık yasak", "melek yasak",
        "at, tilki, kartal", "gerçek hayvan",
    ])
    if has_companion_type_lock:
        r.add(5, 5, "🟢", "COMPANION_LOCK", "Companion tür kilidi var ✅")
    elif sc.companions:
        r.add(1, 5, "🟡", "COMPANION_LOCK",
               "Companion tanımlı ama prompt'ta tür kilidi yok — AI yanlış tür üretebilir")
    else:
        r.add(0, 5, "🟡", "COMPANION_LOCK", "Companion yok, tür kilidi N/A")

    # ── 5. Obje Tanımı ──
    if sc.objects:
        r.add(3, 3, "🟢", "OBJECT_DEF", f"{len(sc.objects)} obje anchor tanımlı ✅")
        # Obje adı kilidi kontrolü
        obj_name = sc.objects[0].name_tr.lower()
        has_obj_lock = obj_name in prompt_lower and any(
            kw in prompt_lower for kw in ["küre değil", "kristal değil", "asla", "dönüştürme"]
        )
        if has_obj_lock:
            r.add(3, 3, "🟢", "OBJECT_LOCK", f"Obje adı kilidi var: '{sc.objects[0].name_tr}' ✅")
        else:
            r.add(1, 3, "🟡", "OBJECT_LOCK",
                   f"Obje '{sc.objects[0].name_tr}' tanımlı ama prompt'ta ad kilidi yok")
    else:
        r.add(0, 3, "🟡", "OBJECT_DEF", "Obje anchor tanımlı değil (opsiyonel)")
        r.add(0, 3, "🟡", "OBJECT_LOCK", "Obje yok, ad kilidi N/A")

    # ── 6. location_constraints Varlığı ──
    lc = sc.location_constraints or ""
    if len(lc) > 100:
        r.add(5, 5, "🟢", "LOC_CONSTRAINTS", f"location_constraints tanımlı ({len(lc)} karakter) ✅")
    elif len(lc) > 0:
        r.add(2, 5, "🟡", "LOC_CONSTRAINTS", "location_constraints kısa — daha detaylı olmalı")
    else:
        r.add(0, 5, "🔴", "LOC_CONSTRAINTS", "location_constraints TANIMSIZ — görsel drift riski!")

    # ── 7. FORBIDDEN Lokasyon Listesi ──
    has_forbidden = "FORBIDDEN" in (lc.upper()) or "yasak" in prompt_lower
    bible_forbidden = "FORBIDDEN_locations" in sc.scenario_bible
    if has_forbidden or bible_forbidden:
        r.add(3, 3, "🟢", "FORBIDDEN_LOC", "Yasaklı lokasyon listesi var ✅")
    else:
        r.add(0, 3, "🟡", "FORBIDDEN_LOC", "Yasaklı lokasyon listesi yok — mekan sapması riski")

    # ── 8. Per-Bölüm MEKAN Etiketleri ──
    mekan_count = prompt.count("MEKAN:") + prompt.count("🌍")
    section_count = prompt.count("BÖLÜM") or prompt.count("###")
    if section_count > 0 and mekan_count >= section_count * 0.5:
        r.add(5, 5, "🟢", "MEKAN_TAGS", f"{mekan_count} MEKAN etiketi / {section_count} bölüm ✅")
    elif mekan_count > 0:
        r.add(2, 5, "🟡", "MEKAN_TAGS",
               f"Sadece {mekan_count} MEKAN etiketi — her bölümde olmalı")
    else:
        r.add(0, 5, "🟡", "MEKAN_TAGS", "MEKAN etiketleri yok — AI lokasyonu değiştirebilir")

    # ── 9. page_prompt_template Tek Çocuk Kilidi ──
    ppt = sc.page_prompt_template or ""
    ppt_upper = ppt.upper()
    has_single_child = any(m.upper() in ppt_upper for m in SINGLE_CHILD_MARKERS)
    if has_single_child:
        r.add(5, 5, "🟢", "SINGLE_CHILD", "page_prompt_template'de tek çocuk kilidi var ✅")
    else:
        r.add(0, 5, "🔴", "SINGLE_CHILD",
               "page_prompt_template'de tek çocuk kilidi YOK — iki çocuk çizimi riski!")

    # ── 10. Kıyafet Tanımları ──
    has_girl = len(sc.outfit_girl or "") > 30
    has_boy = len(sc.outfit_boy or "") > 30
    if has_girl and has_boy:
        r.add(5, 5, "🟢", "OUTFIT", "Kız ve erkek kıyafetleri tanımlı ✅")
    elif has_girl or has_boy:
        r.add(3, 5, "🟡", "OUTFIT", "Sadece bir cinsiyet kıyafeti tanımlı")
    else:
        r.add(0, 5, "🔴", "OUTFIT", "Kıyafet tanımları YOK")

    # ── 11. custom_inputs_schema Companion Bağlantısı ──
    animal_input = next((i for i in sc.custom_inputs_schema if i.get("key") == "animal_friend"), None)
    if animal_input:
        inp_type = animal_input.get("type", "")
        if inp_type == "hidden":
            r.add(3, 3, "🟢", "INPUT_SCHEMA", f"Companion sabit (hidden) ✅ — '{animal_input.get('default', '?')}'")
        elif inp_type == "select":
            r.add(3, 3, "🟢", "INPUT_SCHEMA", "Companion seçimli (select) ✅")
        else:
            r.add(1, 3, "🟡", "INPUT_SCHEMA", f"animal_friend type='{inp_type}' — hidden veya select olmalı")
    elif sc.companions:
        r.add(0, 3, "🔴", "INPUT_SCHEMA",
               "Companion var ama custom_inputs_schema'da animal_friend yok!")
    else:
        r.add(2, 3, "🟡", "INPUT_SCHEMA", "Companion yok, input schema N/A")

    # ── 12. scenario_bible Tutarlılık Kuralları ──
    bible_rules = sc.scenario_bible.get("consistency_rules", [])
    if len(bible_rules) >= 5:
        r.add(5, 5, "🟢", "BIBLE_RULES", f"{len(bible_rules)} tutarlılık kuralı var ✅")
    elif len(bible_rules) >= 2:
        r.add(3, 5, "🟡", "BIBLE_RULES", f"Sadece {len(bible_rules)} tutarlılık kuralı — 5+ önerilir")
    elif sc.scenario_bible:
        r.add(1, 5, "🟡", "BIBLE_RULES", "Scenario bible var ama consistency_rules eksik")
    else:
        r.add(0, 5, "🔴", "BIBLE_RULES", "Scenario bible TANIMSIZ — tutarlılık riski yüksek!")

    # ── 13. cultural_elements Zenginliği ──
    ce = sc.cultural_elements
    primary = ce.get("primary", [])
    if len(primary) >= 4:
        r.add(3, 3, "🟢", "CULTURAL", f"{len(primary)} birincil kültürel element ✅")
    elif len(primary) >= 2:
        r.add(2, 3, "🟡", "CULTURAL", f"Sadece {len(primary)} birincil element — 4+ önerilir")
    elif ce:
        r.add(1, 3, "🟡", "CULTURAL", "cultural_elements var ama az")
    else:
        r.add(0, 3, "🟡", "CULTURAL", "cultural_elements tanımlı değil")

    # ── 14. DOĞRU/YANLIŞ Örnekleri (AI yönlendirmesi) ──
    has_examples = "YANLIŞ" in prompt and "DOĞRU" in prompt
    if has_examples:
        r.add(3, 3, "🟢", "EXAMPLES", "DOĞRU/YANLIŞ örnekleri var ✅")
    else:
        r.add(0, 3, "🟡", "EXAMPLES", "DOĞRU/YANLIŞ örnekleri yok — AI gezi rehberi gibi yazabilir")

    # ── 15. Diyalog Kuralı ──
    has_dialog = any(kw in prompt_lower for kw in ["diyalog", "💬", "konuşma"])
    if has_dialog:
        r.add(2, 2, "🟢", "DIALOG", "Diyalog kuralı var ✅")
    else:
        r.add(0, 2, "🟡", "DIALOG", "Diyalog kuralı yok — monoton hikaye riski")

    # ── 16. cover_prompt_template ──
    cpt = sc.cover_prompt_template or ""
    if len(cpt) > 50:
        r.add(2, 2, "🟢", "COVER_TPL", "Kapak prompt şablonu tanımlı ✅")
    else:
        r.add(0, 2, "🔴", "COVER_TPL", "Kapak prompt şablonu EKSİK!")

    return r


# ═══════════════════════════════════════════════════════════════
# RAPOR ÇIKTISI
# ═══════════════════════════════════════════════════════════════

def generate_report(reports: list[ScenarioReport]) -> str:
    """Tüm raporları Markdown formatında üret."""
    lines = [
        "# 📊 Senaryo Kalite Denetim Raporu",
        "",
        f"**Taranan senaryo sayısı:** {len(reports)}",
        "",
        "## Özet Tablo",
        "",
        "| # | Senaryo | Puan | Not | Kritik Sorun |",
        "|---|---------|------|-----|-------------|",
    ]

    # Puan sırasına göre sırala (en düşük üstte)
    sorted_reports = sorted(reports, key=lambda r: r.score / r.max_score if r.max_score else 0)

    for i, r in enumerate(sorted_reports, 1):
        pct = int(r.score / r.max_score * 100) if r.max_score else 0
        critical = sum(1 for iss in r.issues if iss.severity == "🔴")
        warnings = sum(1 for iss in r.issues if iss.severity == "🟡")
        lines.append(
            f"| {i} | {r.name} | {r.score}/{r.max_score} ({pct}%) | {r.grade} | "
            f"🔴 {critical} 🟡 {warnings} |"
        )

    lines.extend(["", "---", ""])

    # Detaylı raporlar (en düşük puanlılar önce)
    for r in sorted_reports:
        pct = int(r.score / r.max_score * 100) if r.max_score else 0
        lines.extend([
            f"## {r.grade} {r.name} ({r.theme_key}) — {r.score}/{r.max_score} ({pct}%)",
            "",
        ])

        if r.issues:
            for iss in r.issues:
                lines.append(f"- {iss.severity} **{iss.code}**: {iss.message}")
            lines.append("")
        else:
            lines.append("- ✅ Tüm kontroller geçti!")
            lines.append("")

    # İstatistikler
    total_critical = sum(1 for r in reports for iss in r.issues if iss.severity == "🔴")
    total_warning = sum(1 for r in reports for iss in r.issues if iss.severity == "🟡")
    avg_pct = int(sum(r.score / r.max_score * 100 if r.max_score else 0 for r in reports) / len(reports)) if reports else 0

    lines.extend([
        "---",
        "",
        "## 📈 Genel İstatistikler",
        "",
        f"- **Ortalama puan:** {avg_pct}%",
        f"- **Toplam kritik sorun (🔴):** {total_critical}",
        f"- **Toplam uyarı (🟡):** {total_warning}",
        f"- **A notu alan:** {sum(1 for r in reports if r.grade.startswith('🏆'))}",
        f"- **F notu alan:** {sum(1 for r in reports if r.grade.startswith('🔴'))}",
    ])

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

def main():
    # Tüm senaryoları yükle
    _load_all_scenarios()
    all_scenarios = get_all_scenarios()

    print(f"\\n🔍 {len(all_scenarios)} senaryo taranıyor...\\n", file=sys.stderr)

    reports: list[ScenarioReport] = []
    for theme_key, sc in sorted(all_scenarios.items()):
        report = audit_scenario(sc)
        reports.append(report)
        pct = int(report.score / report.max_score * 100) if report.max_score else 0
        critical = sum(1 for iss in report.issues if iss.severity == "🔴")
        print(f"  {report.grade} {sc.name}: {report.score}/{report.max_score} ({pct}%) — 🔴 {critical}", file=sys.stderr)

    # Markdown rapor
    markdown = generate_report(reports)
    print(markdown)

    # Exit kodu: kritik sorun varsa 1
    total_critical = sum(1 for r in reports for iss in r.issues if iss.severity == "🔴")
    if total_critical > 0:
        print(f"\\n⚠️  {total_critical} kritik sorun bulundu!", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
