/**
 * TypeScript type definitions — Prompt System V2.
 */

// User types
export interface User {
  id: string;
  email: string | null;
  full_name: string | null;
  phone: string | null;
  role: "user" | "editor" | "admin";
  is_guest: boolean;
}

// Product types
export interface Product {
  id: string;
  name: string;
  description: string | null;
  width_mm: number;
  height_mm: number;
  bleed_mm: number;
  default_page_count: number;
  min_page_count: number;
  max_page_count: number;
  paper_type: string;
  paper_finish: string;
  cover_type: string;
  base_price: number;
  thumbnail_url: string;
  has_overlay: boolean;
  overlay_preview_url: string | null;
  is_featured: boolean;
  stock_status: string;
}

// Scenario types (V2) — story-world prompt only, no visual templates
export interface Scenario {
  id: string;
  name: string;
  description: string | null;
  thumbnail_url: string;
  story_prompt_tr: string | null;
  location_en: string | null;
  default_page_count: number | null;
  flags: Record<string, boolean> | null;
  custom_inputs_schema?: CustomInputField[];
}

export interface CustomInputField {
  key: string;
  label: string;
  type: "text" | "number" | "select" | "textarea";
  default?: string;
  options?: string[];
  required?: boolean;
  placeholder?: string;
  help_text?: string;
}

// Learning outcome types (V2)
export interface LearningOutcome {
  id: string;
  name: string;
  description: string | null;
  category: string;
  age_group: string;
  ai_prompt_instruction: string | null;
  banned_words_tr: string | null;
}

// Visual style types (V2) — injected only on backend at compose stage
export interface VisualStyle {
  id: string;
  name: string;
  display_name?: string | null;
  thumbnail_url: string;
  prompt_modifier: string;
  style_negative_en: string | null;
  id_weight: number;
}

// Order types
export type OrderStatus =
  | "DRAFT"
  | "TEXT_APPROVED"
  | "COVER_APPROVED"
  | "PAYMENT_PENDING"
  | "PAID"
  | "PROCESSING"
  | "READY_FOR_PRINT"
  | "SHIPPED"
  | "DELIVERED"
  | "REFUNDED"
  | "CANCELLED";

export interface Order {
  id: string;
  status: OrderStatus;
  child_name: string;
  child_age: number;
  child_gender: string | null;
  product_id: string;
  scenario_id: string;
  visual_style_id: string;
  selected_outcomes: string[];
  payment_amount: number | null;
  tracking_number: string | null;
  cover_regenerate_count: number;
  max_cover_regenerate: number;
  created_at: string;
  back_cover_image_url?: string | null;
  cover_spread_image_url?: string | null;
}

// Shipping address
export interface ShippingAddress {
  full_name: string;
  phone: string;
  address_line1: string;
  address_line2?: string;
  city: string;
  district: string;
  postal_code: string;
}

// API Response types
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

// Error types
export interface APIError {
  detail: string;
  status_code: number;
}

// Story page types
export interface StoryPage {
  page_number: number;
  text: string;
  visual_prompt: string;
}

export interface StoryStructure {
  title: string;
  pages: StoryPage[];
}

// Child info types (V2: includes clothing_description)
export interface ChildInfo {
  name: string;
  age: string;
  gender: "erkek" | "kiz";
  clothingDescription: string;
}

// Parent info types
export interface ParentInfo {
  fullName: string;
  email: string;
  phone: string;
}

// Audio types
export type AudioOption = "none" | "system" | "cloned";
export type SystemVoiceType = "female" | "male";
