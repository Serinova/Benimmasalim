// Shared types for scenarios module

/** Proper {label, value} dict format for select options. */
export interface SelectOption {
  label: string;
  value: string;
}

export interface CustomInputField {
  key: string; // Variable key used in templates, e.g., "spaceship_name"
  label: string; // Display label for users, e.g., "Uzay Gemisi Adı"
  type: "text" | "number" | "select" | "textarea";
  default?: string;
  /** For "select" type — always stored as {label, value}[] dicts.
   *  Legacy string[] is also accepted for backward compat. */
  options?: SelectOption[] | string[];
  required?: boolean;
  placeholder?: string;
  help_text?: string;
}

export interface Scenario {
  id: string;
  name: string;
  description: string | null;
  thumbnail_url: string;
  theme_key?: string | null;
  // V2: Story-only fields
  story_prompt_tr: string | null;
  location_en: string | null;
  default_page_count: number | null;
  /** Gösterim için: linked product varsa ürünün sayfa sayısı (tutarlı 22 vb.) */
  effective_default_page_count?: number;
  effective_story_page_count?: number | null;
  flags: Record<string, boolean> | null;
  // Legacy (kept for compat, hidden from UI)
  cover_prompt_template: string;
  page_prompt_template: string;
  ai_prompt_template?: string | null;
  // Dynamic Variables / Custom Inputs
  custom_inputs_schema?: CustomInputField[];
  available_variables?: string[];
  // Registry companion + object anchors (read-only display)
  companions?: { name_tr: string; name_en: string; species: string; appearance: string; short_name: string }[];
  objects?: { name_tr: string; appearance_en: string; prompt_suffix: string }[];
  // Media
  gallery_images: string[];
  // Marketing Fields
  marketing_video_url?: string | null;
  marketing_gallery?: string[];
  marketing_price_label?: string | null;
  marketing_features?: string[];
  marketing_badge?: string | null;
  age_range?: string | null;
  estimated_duration?: string | null;
  tagline?: string | null;
  rating?: number | null;
  review_count?: number;
  // Book Structure (marketing display)
  story_page_count?: number | null;
  cover_count?: number | null;
  greeting_page_count?: number | null;
  back_info_page_count?: number | null;
  total_page_count?: number | null;
  // Outfit Design (scenario-specific, gender-specific)
  outfit_girl?: string | null;
  outfit_boy?: string | null;
  // Product Link & Override Settings
  linked_product_id?: string | null;
  linked_product_name?: string | null;
  price_override_base?: number | null;
  price_override_extra_page?: number | null;
  cover_template_id_override?: string | null;
  inner_template_id_override?: string | null;
  back_template_id_override?: string | null;
  ai_config_id_override?: string | null;
  paper_type_override?: string | null;
  paper_finish_override?: string | null;
  cover_type_override?: string | null;
  lamination_override?: string | null;
  orientation_override?: string | null;
  min_page_count_override?: number | null;
  max_page_count_override?: number | null;
  // Display
  is_active: boolean;
  display_order: number;
  created_at: string | null;
  // Registry metadata — tells the frontend which fields are read-only
  is_code_managed?: boolean;
  code_managed_fields?: string[];
}
