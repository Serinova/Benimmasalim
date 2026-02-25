# Clothing Selector — V2 Outfit Lock UX

## Overview

The ClothingSelector replaces the old manual-only clothing input with a 3-mode UX:

1. **AI Suggest** — Generates 6 outfit options via Gemini based on scenario + child + style context.
2. **Quick Pick Cards** — User selects one of the 6 suggestions with a single tap.
3. **Manual Edit** — Optional textarea to customize the selected outfit or write from scratch.

## Architecture

```
Backend:  POST /api/v1/ai/suggest-outfits
          Request:  { child_name, child_age, child_gender, scenario_id?, visual_style_id? }
          Response: { success, outfits: string[6], error? }
          Fallback: gender-based defaults if Gemini fails

Frontend: ClothingSelector.tsx
          ├── suggestOutfits() → api.ts
          ├── normalizeClothingDescription() → compliance.ts
          ├── validateClothingDescription() → compliance.ts
          └── orderStore (Zustand persist)
              ├── clothingDescription: string
              ├── selectedOutfitIndex: number | null
              └── outfitSuggestions: string[]
```

## UX Flow (Wizard Step 5)

1. User fills name, age, gender in ChildInfoForm.
2. Below the form, ClothingSelector section appears:
   - "AI Öner (6 seçenek)" button calls backend.
   - 6 cards appear as a 2-column grid.
   - User taps a card → sets `clothingDescription` in store.
   - "Düzenle" toggle reveals textarea for manual edits.
3. Clothing is **optional** — user can skip.
4. If provided, must pass validation:
   - Minimum 8 characters.
   - No banned words (bikini, lingerie, underwear, etc.).
   - Common typos auto-normalized (tishort→t-shirt, jean→kot pantolon, etc.).

## Normalization Table

| Input     | Output               |
|-----------|----------------------|
| tishort   | t-shirt              |
| tişört    | t-shirt              |
| tshirt    | t-shirt              |
| jean      | kot pantolon         |
| jeans     | kot pantolon         |
| sneaker   | spor ayakkabı        |
| sneakers  | spor ayakkabı        |
| hoodie    | kapüşonlu sweatshirt |

## Banned Words

`bikini`, `lingerie`, `underwear`, `bra`, `thong`, `iç çamaşırı`, `mayo`, `sütyen`, `string`, `tanga`

## Files Changed

| File | Change |
|------|--------|
| `backend/app/api/v1/ai.py` | Added `POST /ai/suggest-outfits` endpoint |
| `frontend/src/lib/api.ts` | Added `suggestOutfits()` function + types |
| `frontend/src/lib/compliance.ts` | Added `normalizeClothingDescription()` + `validateClothingDescription()` |
| `frontend/src/stores/orderStore.ts` | Added `selectedOutfitIndex`, `outfitSuggestions`, `selectOutfit()`, `setOutfitSuggestions()` |
| `frontend/src/components/ClothingSelector.tsx` | New component (AI suggest + cards + edit) |
| `frontend/src/components/ChildInfoForm.tsx` | Added `hideClothing` prop, made clothing optional |
| `frontend/src/app/create/page.tsx` | Wired ClothingSelector, normalize before send |
| `frontend/src/__tests__/v2-compliance.test.ts` | Added normalization + validation + payload tests |

## Test Results

- **Jest**: 23 passed, 0 failed
- **tsc --noEmit**: 0 errors
- **Backend pytest**: 164 passed, 2 skipped
