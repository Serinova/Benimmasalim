-- Ocean Modular Prompts Migration (Manual SQL)
-- Run in Cloud SQL console or via gcloud sql connect

BEGIN;

-- Check current ocean scenario
SELECT 
    id, 
    name, 
    theme_key,
    LENGTH(cover_prompt_template) as cover_len,
    LENGTH(page_prompt_template) as page_len,
    LENGTH(story_prompt_tr) as story_len
FROM scenarios
WHERE theme_key = 'ocean_depths';

-- Update Ocean scenario with modular prompts
UPDATE scenarios SET
    cover_prompt_template = 'Epic underwater scene: {scene_description}. 
Dolphin companion beside child (playful, friendly guide). 
MASSIVE blue whale in background (30m, emphasize scale - child tiny). 
Bioluminescent jellyfish glowing. Vibrant coral reefs. 
Deep ocean gradient (turquoise to indigo). Sunlight rays from above. 
Peaceful, wondrous atmosphere.',

    page_prompt_template = 'Underwater scene: {scene_description}. 
Dolphin companion in shallow-mid depths (playful guide). 
Zone: [Epipelagic 0-200m: coral, tropical fish, turtle, turquoise, sun / Mesopelagic 200-1000m: blue-purple, glowing jellyfish, lanternfish / Bathypelagic 1000-4000m: dark, anglerfish, bioluminescence / Whale: MASSIVE (30m, 200 tons), child TINY, gentle, singing, riding / Abyssopelagic 4000m+: darkness, hydrothermal vents, phosphorescent stars]. 
Match zone to depth.',

    -- Story prompt too long for inline SQL, will be updated via script
    updated_at = NOW()
WHERE theme_key = 'ocean_depths';

-- Verify update
SELECT 
    name,
    theme_key,
    LENGTH(cover_prompt_template) as new_cover_len,
    LENGTH(page_prompt_template) as new_page_len,
    updated_at
FROM scenarios
WHERE theme_key = 'ocean_depths';

COMMIT;

-- Expected results:
-- new_cover_len: 326
-- new_page_len: 464
