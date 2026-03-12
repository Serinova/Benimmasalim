export interface StoryPageContent {
  text?: string;
  image_prompt?: string;
  visual_prompt?: string;
  is_back_cover?: boolean;
  page_number?: number;
  page_type?: string;
}

export interface GenerationManifestEntry {
  provider?: string;
  model?: string;
  num_inference_steps?: number;
  guidance_scale?: number;
  width?: number;
  height?: number;
  is_cover?: boolean;
  prompt_hash?: string;
  negative_hash?: string;
  reference_image_used?: boolean;
  final_prompt?: string;
  negative_prompt?: string;
}

export interface PromptByPage {
  final_prompt: string;
  negative_prompt: string;
  pipeline_version?: string;
  composer_version?: string;
  page_type?: string;
  page_index?: number;
  story_page_number?: number | null;
}

export interface BillingInfo {
  billing_type: string | null;
  billing_tc_no?: string | null;
  billing_full_name: string | null;
  billing_email: string | null;
  billing_phone: string | null;
  billing_company_name: string | null;
  billing_tax_id: string | null;
  billing_tax_office: string | null;
  billing_address: Record<string, string> | string | null;
}

export interface InvoiceInfo {
  invoice_number: string;
  invoice_status: string;
  pdf_ready: boolean;
  pdf_version: number;
  issued_at: string | null;
  last_error: string | null;
  retry_count: number;
  needs_credit_note: boolean;
  email_sent: boolean;
  email_status: string;
  email_sent_at: string | null;
  email_error: string | null;
  email_retry_count: number;
  email_resent_count: number;
  email_last_resent_at: string | null;
}

/** Lightweight item for the list view — no page_images */
export interface OrderListItem {
  id: string;
  status: string;
  parent_name: string;
  parent_email: string;
  parent_phone: string | null;
  child_name: string;
  child_age: number;
  child_gender: string | null;
  story_title: string;
  product_name: string | null;
  product_price: number | null;
  scenario_name: string | null;
  visual_style_name: string | null;
  page_count: number;
  page_images: Record<string, string> | null;
  confirmed_at: string | null;
  created_at: string;
  admin_notes?: string | null;
  has_coloring_book?: boolean;
  has_audio_book?: boolean;
  // Slim fields (PR-2 will add cover_thumb, image_count, has_pdf, has_invoice)
  cover_thumb?: string | null;
  image_count?: number;
  has_pdf?: boolean;
  has_invoice?: boolean;
}

/** Full detail for the drawer */
export interface OrderDetail extends OrderListItem {
  confirmation_token?: string;
  product_id?: string | null;
  story_pages: StoryPageContent[] | null;
  dedication_note?: string | null;
  audio_type?: string | null;
  audio_voice_id?: string | null;
  voice_sample_url?: string | null;
  pdf_url?: string | null;
  coloring_pdf_url?: string | null;
  back_cover_image_url?: string | null;
  cover_spread_image_url?: string | null;
  generation_manifest_json?: Record<string, GenerationManifestEntry> | null;
  prompt_debug_json?: Record<string, { final_prompt?: string; negative_prompt?: string }> | null;
  prompts_by_page?: Record<string, PromptByPage> | null;
  pipeline_version?: string | null;
  pipeline_label?: string | null;
  billing?: BillingInfo | null;
  invoice?: InvoiceInfo | null;
  updated_at?: string | null;
  expires_at?: string | null;
}

export interface OrderStats {
  total: number;
  pending: number;
  confirmed: number;
  expired: number;
  total_revenue: number;
}

export interface InvoiceDashboard {
  pdf_issues_count: number;
  email_issues_count: number;
  token_abuse_count: number;
  invoice_status_counts: Record<string, number>;
  total_invoices: number;
}

export interface BackCoverConfig {
  id: string;
  name: string;
  company_name: string;
  company_website: string;
  company_email: string;
  tagline: string;
  tips_title: string;
  tips_content: string;
  copyright_text: string;
  background_color: string;
  primary_color: string;
  text_color: string;
  border_color: string;
  qr_enabled: boolean;
  qr_label: string;
  show_border: boolean;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}
