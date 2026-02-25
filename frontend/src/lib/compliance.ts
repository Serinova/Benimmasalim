/**
 * Frontend compliance checks for Prompt System V2.
 *
 * These are UI-only sanity checks — backend already enforces everything.
 * If any check fails, the UI shows a warning banner to the user.
 */

import type { StoryPage } from "@/lib/api";

// ─── Clothing validation ─────────────────────────────────────────

/** Words banned in clothing descriptions (inappropriate for children's books). */
const BANNED_CLOTHING_WORDS = [
  "bikini",
  "lingerie",
  "underwear",
  "bra",
  "thong",
  "iç çamaşırı",
  "mayo",
  "sütyen",
  "string",
  "tanga",
];

/**
 * TR→EN clothing normalizations. Longer phrases first (applied in order).
 * Backend also normalizes, so this is a complementary client-side pass.
 */
const CLOTHING_NORMALIZATIONS: [string, string][] = [
  // Multi-word phrases first (longest match)
  ["spor ayakkabısı", "sneakers"],
  ["spor ayakkabisi", "sneakers"],
  ["spor ayakkabı", "sneakers"],
  ["spor ayakkabi", "sneakers"],
  ["kot pantolon", "jeans"],
  ["lastik çizme", "rain boots"],
  ["lastik cizme", "rain boots"],
  ["trekking ayakkabısı", "hiking shoes"],
  ["trekking ayakkabisi", "hiking shoes"],
  ["eşofman altı", "sweatpants"],
  ["esofman alti", "sweatpants"],
  ["kargo pantolon", "cargo pants"],
  ["sırt çantası", "backpack"],
  ["sirt cantasi", "backpack"],
  ["iç çamaşırı", "underwear"],
  ["t shirt", "t-shirt"],
  ["sweat shirt", "sweatshirt"],
  // Typos
  ["tishort", "t-shirt"],
  ["tişört", "t-shirt"],
  ["tisort", "t-shirt"],
  ["tisört", "t-shirt"],
  ["tshirt", "t-shirt"],
  // Colors TR→EN
  ["kırmızı", "red"],
  ["kirmizi", "red"],
  ["mavi", "blue"],
  ["yeşil", "green"],
  ["yesil", "green"],
  ["sarı", "yellow"],
  ["sari", "yellow"],
  ["beyaz", "white"],
  ["siyah", "black"],
  ["pembe", "pink"],
  ["mor", "purple"],
  ["turuncu", "orange"],
  ["lacivert", "navy blue"],
  ["kahverengi", "brown"],
  ["bordo", "burgundy"],
  ["turkuaz", "turquoise"],
  ["lila", "lilac"],
  ["haki", "khaki"],
  ["koyu", "dark"],
  ["gri", "gray"],
  ["renkli", "colorful"],
  ["çiçekli", "floral"],
  ["cicekli", "floral"],
  // Garments TR→EN
  ["mont", "jacket"],
  ["ceket", "jacket"],
  ["pantolon", "pants"],
  ["şort", "shorts"],
  ["sort", "shorts"],
  ["etek", "skirt"],
  ["tayt", "leggings"],
  ["gömlek", "shirt"],
  ["gomlek", "shirt"],
  ["kazak", "sweater"],
  ["yelek", "vest"],
  ["polar", "fleece"],
  ["rüzgarlık", "windbreaker"],
  ["ruzgarlik", "windbreaker"],
  ["yağmurluk", "raincoat"],
  ["yagmurluk", "raincoat"],
  ["kapüşonlu", "hooded"],
  ["kapusonlu", "hooded"],
  ["elbise", "dress"],
  ["ayakkabısı", "shoes"],
  ["ayakkabisi", "shoes"],
  ["ayakkabı", "shoes"],
  ["ayakkabi", "shoes"],
  ["bot", "boots"],
  ["çizme", "boots"],
  ["cizme", "boots"],
  ["sneaker", "sneakers"],
  ["sneakers", "sneakers"],
  ["jean", "jeans"],
  ["jeans", "jeans"],
  ["hoodie", "hooded sweatshirt"],
];

/**
 * Normalize common clothing typos and return cleaned string.
 * Always trims and lowercases for comparison, but preserves case in output
 * except where replacements are applied.
 */
/** Turkish-aware word boundary (JS \b doesn't support çğıöşüİ) */
const TR_WORD_CHARS = "a-zA-ZçğıöşüÇĞİÖŞÜâîû0-9";
const LEFT_BOUNDARY = `(?<![${TR_WORD_CHARS}])`;
const RIGHT_BOUNDARY = `(?![${TR_WORD_CHARS}])`;

export function normalizeClothingDescription(raw: string): string {
  let text = raw.trim();
  if (!text) return "";

  // Apply normalizations — longer phrases first (array is pre-sorted)
  for (const [tr, en] of CLOTHING_NORMALIZATIONS) {
    const escaped = tr.replace(/[.*+?^${}()|[\]\\]/g, String.raw`\$&`);
    const regex = new RegExp(LEFT_BOUNDARY + escaped + RIGHT_BOUNDARY, "gi");
    text = text.replaceAll(regex, en);
  }

  // Normalize comma spacing
  text = text.replace(/\s*,\s*/g, ", ");

  return text.trim();
}

/**
 * Validate clothing description for banned words.
 * Returns null if valid, or an error message string if invalid.
 */
export function validateClothingDescription(desc: string): string | null {
  const lower = desc.toLowerCase();
  for (const banned of BANNED_CLOTHING_WORDS) {
    if (lower.includes(banned)) {
      return `Kıyafet açıklamasında uygunsuz kelime: "${banned}"`;
    }
  }
  const trimmed = desc.trim();
  if (trimmed.length > 0 && trimmed.length < 8) {
    return `Kıyafet açıklaması en az 8 karakter olmalı (${trimmed.length}/8)`;
  }
  return null;
}

// ─── Family words ─────────────────────────────────────────────────

/** Turkish family words banned when scenario.no_family = true */
const BANNED_FAMILY_WORDS_TR = [
  "anne",
  "baba",
  "abla",
  "abi",
  "kardes",
  "kardeş",
  "aile",
  "annecik",
  "babacık",
  "babacik",
  "dede",
  "nine",
  "babaanne",
  "anneanne",
  "teyze",
  "dayı",
  "dayi",
  "amca",
  "hala",
];

/**
 * Check story pages + visual prompts for obvious V2 compliance issues.
 * Returns an array of warning strings (empty = all good).
 */
export function checkPromptCompliance(pages: StoryPage[], noFamily?: boolean): string[] {
  const warnings: string[] = [];

  for (const page of pages) {
    const vp = page.visual_prompt || "";

    // Check for "Kapadokya" in visual prompt (should be "Cappadocia" only)
    if (/kapadokya/i.test(vp)) {
      warnings.push(
        `Sayfa ${page.page_number}: Visual prompt icinde "Kapadokya" bulundu (sadece "Cappadocia" olmali).`
      );
    }

    // Check for double STYLE block
    if (/STYLE:\s*STYLE:/i.test(vp)) {
      warnings.push(`Sayfa ${page.page_number}: "STYLE: STYLE:" duplikasyonu bulundu.`);
    }

    // Check for empty clothing placeholder
    if (/wearing\s*\./i.test(vp) || /A young child wearing\s*\./i.test(vp)) {
      warnings.push(`Sayfa ${page.page_number}: Bos kiyafet yer tutucusu ("wearing .") bulundu.`);
    }

    // Check no_family enforcement on story text
    if (noFamily && page.text) {
      const lowerText = page.text.toLowerCase();
      for (const word of BANNED_FAMILY_WORDS_TR) {
        if (lowerText.includes(word)) {
          warnings.push(
            `Sayfa ${page.page_number}: Hikaye metninde yasakli aile kelimesi "${word}" bulundu (no_family aktif).`
          );
          break;
        }
      }
    }
  }

  return warnings;
}
