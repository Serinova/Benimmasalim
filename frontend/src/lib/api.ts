/**
 * API client for backend communication — Prompt System V2.
 *
 * All AI prompt composition happens on the backend.
 * Frontend sends IDs only (scenario_id, learning_outcome_ids, visual_style_id)
 * plus child meta and clothing_description.
 */

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "/api/v1";

// ─── Error handling ──────────────────────────────────────────────

interface FetchOptions extends RequestInit {
  token?: string;
}

interface APIErrorData {
  detail?: string | Array<{ msg?: string; loc?: string[] }>;
  message?: string;
  errors?: Record<string, string[]>;
}

function extractErrorMessage(data: APIErrorData | null, statusText: string): string {
  if (!data) return statusText;
  if (typeof data.detail === "string") return data.detail;
  if (data.message) return data.message;
  if (Array.isArray(data.detail) && data.detail.length > 0) {
    const first = data.detail[0];
    const msg = first?.msg ?? "";
    const loc = Array.isArray(first?.loc) ? first.loc.filter((x) => x !== "body").join(".") : "";
    return loc ? `${loc}: ${msg}` : String(msg);
  }
  return statusText;
}

export class APIError extends Error {
  constructor(
    public status: number,
    public statusText: string,
    public data: APIErrorData | null
  ) {
    super(extractErrorMessage(data, statusText));
    this.name = "APIError";
  }
}

let _isRefreshing = false;
let _refreshPromise: Promise<string | null> | null = null;

/**
 * Attempt to refresh the access token using the stored refresh token.
 * Returns the new access token or null on failure.
 */
async function tryRefreshToken(): Promise<string | null> {
  const refreshToken = typeof window !== "undefined" ? localStorage.getItem("refreshToken") : null;
  if (!refreshToken) return null;

  try {
    const res = await fetch(`${API_BASE_URL}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
    if (!res.ok) return null;
    const data = await res.json();
    if (data?.access_token) {
      localStorage.setItem("token", data.access_token);
      if (data.refresh_token) {
        localStorage.setItem("refreshToken", data.refresh_token);
      }
      return data.access_token as string;
    }
  } catch {
    // refresh failed
  }
  return null;
}

async function fetchAPI<T>(endpoint: string, options: FetchOptions = {}): Promise<T> {
  const { token, ...fetchOptions } = options;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(fetchOptions.headers as Record<string, string>),
  };

  // Auto-attach stored token if none provided
  const effectiveToken =
    token || (typeof window !== "undefined" ? localStorage.getItem("token") : null);
  if (effectiveToken) {
    headers["Authorization"] = `Bearer ${effectiveToken}`;
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...fetchOptions,
    headers,
  });

  // Auto-refresh on 401 (token expired)
  if (response.status === 401 && effectiveToken && !endpoint.includes("/auth/")) {
    if (!_isRefreshing) {
      _isRefreshing = true;
      _refreshPromise = tryRefreshToken().finally(() => {
        _isRefreshing = false;
        _refreshPromise = null;
      });
    }
    const newToken = await (_refreshPromise ?? tryRefreshToken());
    if (newToken) {
      headers["Authorization"] = `Bearer ${newToken}`;
      const retryResponse = await fetch(`${API_BASE_URL}${endpoint}`, {
        ...fetchOptions,
        headers,
      });
      const retryData = await retryResponse.json().catch(() => null);
      if (!retryResponse.ok) {
        throw new APIError(retryResponse.status, retryResponse.statusText, retryData);
      }
      return retryData as T;
    }
  }

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    throw new APIError(response.status, response.statusText, data);
  }

  return data as T;
}

// ─── Data types ──────────────────────────────────────────────────

export interface Product {
  id: string;
  name: string;
  description: string | null;
  width_mm: number;
  height_mm: number;
  base_price: number;
  thumbnail_url: string;
  has_overlay: boolean;
  is_featured: boolean;
  default_page_count?: number;
}

/** V2: Scenario stores only story-world prompt (TR). No visual templates. */
export interface Scenario {
  id: string;
  name: string;
  description: string | null;
  thumbnail_url: string;
  /** Kitaptan kareler — backend gallery_images (liste URL) */
  gallery_images?: string[];
  story_prompt_tr: string | null;
  location_en: string | null;
  default_page_count: number | null;
  linked_product_page_count?: number | null;
  outfit_girl?: string | null;
  outfit_boy?: string | null;
  flags: Record<string, boolean> | null;
  custom_inputs_schema?: CustomInputField[];
  // Marketing fields
  marketing_video_url?: string | null;
  marketing_gallery?: string[];
  marketing_price_label?: string | null;
  marketing_features?: string[];
  marketing_badge?: string | null;
  age_range?: string | null;
  estimated_duration?: string | null;
  tagline?: string | null;
  rating?: number | null;
  review_count?: number | null;
  // Product link & override settings
  linked_product_id?: string | null;
  linked_product_name?: string | null;
  price_override_base?: number | null;
  price_override_extra_page?: number | null;
  // Book structure (for marketing display)
  story_page_count?: number | null;
  cover_count?: number | null;
  greeting_page_count?: number | null;
  back_info_page_count?: number | null;
  total_page_count?: number | null;
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

/** V2: Learning outcome with optional banned words for no_family. */
export interface LearningOutcome {
  id: string;
  name: string;
  description: string | null;
  category: string;
  ai_prompt_instruction: string | null;
  banned_words_tr: string | null;
}

export interface LearningOutcomeCategory {
  category: string;
  category_label: string;
  items: LearningOutcome[];
}

/** V2: Visual style — style injection happens only on backend. */
export interface VisualStyle {
  id: string;
  name: string;
  /** Kullanıcıya gösterilen isim (boşsa name kullanılır). */
  display_name?: string | null;
  thumbnail_url: string;
  prompt_modifier: string;
  style_negative_en: string | null;
  id_weight: number;
  // PuLID overrides (null = style_config.py fallback)
  true_cfg?: number | null;
  start_step?: number | null;
  // FLUX generation overrides (null = GenerationConfig defaults)
  num_inference_steps?: number | null;
  guidance_scale?: number | null;
}

// ─── Story types ─────────────────────────────────────────────────

export interface StoryPage {
  page_number: number;
  text: string;
  visual_prompt: string;
  image_base64?: string | null;
  v3_composed?: boolean;
  negative_prompt?: string | null;
  page_type?: string; // "cover" | "front_matter" | "inner"
  composer_version?: string; // "v3" when V3 pipeline
  pipeline_version?: string; // "v3" when V3 pipeline; admin shows this
}

export interface StoryStructure {
  title: string;
  pages: StoryPage[];
}

// ─── V2 request/response types ───────────────────────────────────

/**
 * PASS-1 + PASS-2 request: IDs + child meta. No prompt text from frontend.
 *
 * Backend model (TestStructuredStoryRequest) accepted fields:
 *   child_name, child_age, child_gender, child_photo_url,
 *   scenario_id, learning_outcomes, visual_style, visual_style_id,
 *   page_count, clothing_description, custom_variables.
 */
export interface GenerateStoryV2Request {
  child_name: string;
  child_age: number;
  child_gender: string;
  child_photo_url?: string;
  scenario_id: string;
  learning_outcomes: string[]; // outcome names (backend still expects names)
  visual_style: string; // style prompt_modifier text (fallback if no visual_style_id)
  visual_style_id?: string; // UUID — backend looks up VisualStyle from DB
  page_count: number;
  clothing_description?: string; // outfit lock: consistent across all pages (max 300 chars)
  custom_variables?: Record<string, string>;
}

export interface GenerateStoryV2Response {
  success: boolean;
  story?: StoryStructure;
  error?: string;
  generation_method?: string;
  pipeline_version?: string;
  v3_enhancement_skipped?: boolean;
  page_count?: number;
  used_page_count?: number;
  metadata?: {
    scenario_name?: string;
    visual_style?: string;
    clothing_description?: string;
    child_visual_description?: string;
  };
}

/**
 * Submit preview order — backend generates images in background.
 *
 * Backend model (AsyncPreviewRequest) accepted fields are listed below.
 * Fields NOT in backend model will be silently ignored by Pydantic.
 */
export interface SubmitPreviewV2Request {
  user_id?: string | null;
  parent_name: string;
  parent_email: string;
  parent_phone?: string;
  child_name: string;
  child_age: number;
  child_gender?: string;
  child_photo_url?: string | null;
  clothing_description?: string; // outfit lock for FAL image generation
  story_title: string;
  story_pages: StoryPage[];
  product_id?: string;
  product_name?: string;
  product_price?: number;
  scenario_name?: string | null;
  visual_style_name?: string | null;
  visual_style?: string;
  id_weight?: number;
  learning_outcomes?: string[] | null;
  has_audio_book: boolean;
  audio_type?: string | null;
  audio_voice_id?: string | null;
  voice_sample_url?: string | null;
  dedication_note?: string | null;
  promo_code?: string | null;
}

export interface SubmitPreviewV2Response {
  success: boolean;
  preview_id?: string;
  message?: string;
  estimated_time?: string;
  can_close_page?: boolean;
  error?: string;
}

export interface UploadTempImageResponse {
  success: boolean;
  url?: string;
  error?: string;
}

// ─── API functions ───────────────────────────────────────────────

// Products
export async function getProducts(): Promise<Product[]> {
  return fetchAPI("/products");
}

export async function getProduct(id: string): Promise<Product> {
  return fetchAPI(`/products/${id}`);
}

// Scenarios (V2)
export async function getScenarios(): Promise<Scenario[]> {
  return fetchAPI("/scenarios");
}

// Admin: rate limit sıfırlama (admin token gerekir)
export interface AdminResetRateLimitsResponse {
  ok: boolean;
  message: string;
  deleted_keys?: number;
}

export async function adminResetRateLimits(): Promise<AdminResetRateLimitsResponse> {
  return fetchAPI("/admin/rate-limit/reset-all", { method: "POST" });
}

// Admin: kullanıcı listesi
export interface AdminUserItem {
  id: string;
  email: string | null;
  full_name: string | null;
  role: string;
  is_active: boolean;
  is_guest: boolean;
  created_at: string;
}

export interface AdminUserListResponse {
  items: AdminUserItem[];
  total: number;
  page: number;
  page_size: number;
}

export async function adminListUsers(params: {
  page?: number;
  page_size?: number;
  search?: string;
}): Promise<AdminUserListResponse> {
  const sp = new URLSearchParams();
  if (params.page != null) sp.set("page", String(params.page));
  if (params.page_size != null) sp.set("page_size", String(params.page_size));
  if (params.search) sp.set("search", params.search);
  const q = sp.toString();
  return fetchAPI(`/admin/users${q ? `?${q}` : ""}`);
}

// Learning Outcomes (V2)
export async function getLearningOutcomes(): Promise<LearningOutcomeCategory[]> {
  return fetchAPI("/scenarios/learning-outcomes");
}

// Visual Styles (V2)
export async function getVisualStyles(): Promise<VisualStyle[]> {
  return fetchAPI("/scenarios/visual-styles");
}

// ─── Outfit Suggestion ──────────────────────────────────────────

export interface SuggestOutfitsRequest {
  child_name: string;
  child_age: number;
  child_gender: string;
  scenario_id?: string;
  visual_style_id?: string;
}

export interface SuggestOutfitsResponse {
  success: boolean;
  outfits: string[];
  error?: string;
}

/**
 * Get 6 AI-generated outfit suggestions based on child + scenario + style.
 * Falls back to gender-based defaults if AI fails.
 */
export async function suggestOutfits(req: SuggestOutfitsRequest): Promise<SuggestOutfitsResponse> {
  return fetchAPI("/ai/suggest-outfits", {
    method: "POST",
    body: JSON.stringify(req),
  });
}

// ─── V2 AI pipeline ─────────────────────────────────────────────

const STORY_GENERATION_TIMEOUT_MS = 120_000; // 2 dakika

/**
 * PASS-1 + PASS-2: Generate structured story with composed visual prompts.
 * Backend handles all prompt composition — frontend sends IDs only.
 * Timeout: 2 dakika; aşımda net hata gösterilir.
 */
export async function generateStoryV2(
  req: GenerateStoryV2Request
): Promise<GenerateStoryV2Response> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), STORY_GENERATION_TIMEOUT_MS);
  try {
    return await fetchAPI("/ai/test-story-structured", {
      method: "POST",
      body: JSON.stringify(req),
      signal: controller.signal,
    });
  } catch (err) {
    if (err instanceof Error && err.name === "AbortError") {
      throw new Error(
        "Hikaye oluşturma zaman aşımına uğradı (2 dk). Lütfen tekrar deneyin veya sayfa sayısını azaltın."
      );
    }
    throw err;
  } finally {
    clearTimeout(timeoutId);
  }
}

/**
 * Upload a base64 image to get a public URL (GCS) for PuLID.
 */
export async function uploadTempImage(imageBase64: string): Promise<UploadTempImageResponse> {
  return fetchAPI("/ai/upload/temp-image", {
    method: "POST",
    body: JSON.stringify({ image_base64: imageBase64 }),
  });
}

/**
 * Submit preview order — images are generated in background by backend.
 * Returns immediately. User can close the page.
 */
export async function submitPreviewV2(
  req: SubmitPreviewV2Request
): Promise<SubmitPreviewV2Response> {
  return fetchAPI("/orders/submit-preview-async", {
    method: "POST",
    body: JSON.stringify(req),
  });
}

// ─── Trial Preview ───────────────────────────────────────────────

export interface GeneratePreviewRequest {
  user_id?: string | null;
  parent_name: string;
  parent_email: string;
  parent_phone?: string | null;
  child_name: string;
  child_age: number;
  child_gender?: string | null;
  child_photo_url?: string | null;
  product_id?: string | null;
  product_name?: string | null;
  product_price?: number | null;
  story_title: string;
  story_pages: { page_number: number; text: string; visual_prompt: string }[];
  scenario_id?: string | null;
  scenario_name?: string | null;
  visual_style?: string | null;
  visual_style_name?: string | null;
  learning_outcomes?: string[] | null;
  clothing_description?: string | null;
  id_weight?: number | null;
}

export interface GeneratePreviewResponse {
  success: boolean;
  trial_id: string;
  status: string;
  message: string;
  preview_url?: string | null;
  trial_token?: string | null;
}

export interface GenerationProgress {
  current_page: number;
  total_pages: number;
  stage: string; // "generating_images" | "composing" | "uploading" | "failed"
  message?: string;
  error?: string;
}

export interface TrialStatusResponse {
  trial_id: string;
  status: string;
  is_preview_ready: boolean;
  is_story_ready: boolean;
  is_failed: boolean;
  preview_images_count: number;
  story_title: string;
  generation_progress?: GenerationProgress | null;
}

export interface TrialPreviewResponse {
  success: boolean;
  trial_id: string;
  status: string;
  story_title: string;
  story_pages: { page_number: number; text: string; visual_prompt: string }[];
  preview_images: Record<string, string>;
  child_name: string;
  product_name?: string | null;
  product_price?: number | null;
}

/**
 * Generate 3 composed preview images from an existing story.
 * Returns a trial_id to poll for status.
 */
export async function generatePreviewImages(
  req: GeneratePreviewRequest
): Promise<GeneratePreviewResponse> {
  return fetchAPI("/trials/generate-preview", {
    method: "POST",
    body: JSON.stringify(req),
  });
}

/**
 * Poll trial status until preview images are ready.
 * @param trialToken - X-Trial-Token for ownership verification
 */
export async function getTrialStatus(trialId: string, trialToken?: string): Promise<TrialStatusResponse> {
  const headers: Record<string, string> = {};
  if (trialToken) headers["X-Trial-Token"] = trialToken;
  return fetchAPI(`/trials/${trialId}/status`, { headers });
}

/**
 * Get trial preview data including composed images.
 * @param trialToken - X-Trial-Token for ownership verification
 */
export async function getTrialPreview(trialId: string, trialToken?: string): Promise<TrialPreviewResponse> {
  const headers: Record<string, string> = {};
  if (trialToken) headers["X-Trial-Token"] = trialToken;
  return fetchAPI(`/trials/${trialId}/preview`, { headers });
}

// ─── Trial Complete (after payment) ──────────────────────────────

export interface CompleteTrialRequest {
  trial_id: string;
  payment_reference: string;
  parent_name?: string | null;
  parent_email?: string | null;
  parent_phone?: string | null;
  dedication_note?: string | null;
  promo_code?: string | null;
  has_audio_book?: boolean;
  audio_type?: string | null;
  audio_voice_id?: string | null;
  voice_sample_url?: string | null;
}

export interface CompleteTrialResponse {
  success: boolean;
  trial_id: string;
  status: string;
  message: string;
}

/**
 * Complete a trial after payment — triggers remaining page generation.
 * @param trialToken - X-Trial-Token for ownership verification
 */
export async function completeTrial(
  req: CompleteTrialRequest,
  trialToken?: string,
): Promise<CompleteTrialResponse> {
  const headers: Record<string, string> = {};
  if (trialToken) headers["X-Trial-Token"] = trialToken;
  return fetchAPI("/trials/complete", {
    method: "POST",
    headers,
    body: JSON.stringify(req),
  });
}

// ─── Trial Payment (Iyzico) ──────────────────────────────────────

export interface CreateTrialPaymentResponse {
  success: boolean;
  payment_url: string;
  trial_id: string;
}

export interface VerifyTrialPaymentResponse {
  success: boolean;
  trial_id?: string;
  payment_reference?: string;
  error?: string;
}

/**
 * Create an Iyzico checkout session for a trial (paid orders).
 * Returns a payment_url to redirect the user to Iyzico.
 */
export async function createTrialPayment(
  trialId: string,
  trialToken?: string,
): Promise<CreateTrialPaymentResponse> {
  const headers: Record<string, string> = {};
  if (trialToken) headers["X-Trial-Token"] = trialToken;
  return fetchAPI(`/trials/${trialId}/create-payment`, {
    method: "POST",
    headers,
  });
}

/**
 * Verify Iyzico payment result for a trial after returning from Iyzico page.
 */
export async function verifyTrialPayment(
  trialId: string,
  token: string,
  trialToken?: string,
): Promise<VerifyTrialPaymentResponse> {
  const headers: Record<string, string> = {};
  if (trialToken) headers["X-Trial-Token"] = trialToken;
  return fetchAPI(`/trials/${trialId}/verify-payment`, {
    method: "POST",
    headers,
    body: JSON.stringify({ token }),
  });
}

// ─── Auth ────────────────────────────────────────────────────────

export async function login(email: string, password: string) {
  return fetchAPI<{ access_token: string; refresh_token: string }>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export async function register(email: string, password: string, fullName: string) {
  return fetchAPI<{ access_token: string; refresh_token: string }>("/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, password, full_name: fullName }),
  });
}

// ─── V2 Payload builder (testable) ──────────────────────────────

/**
 * Build V2 PASS-1 request payload. Ensures no prompt text leaks from frontend.
 */
export function buildStoryPayload(params: {
  childName: string;
  childAge: number;
  childGender: string;
  childPhotoUrl?: string;
  scenarioId: string;
  learningOutcomeNames: string[];
  visualStylePromptModifier: string;
  visualStyleId?: string;
  pageCount: number;
  clothingDescription?: string;
  customVariables?: Record<string, string>;
}): GenerateStoryV2Request {
  const rawName = (params.childName || "").trim().slice(0, 50);
  const child_name = rawName.length >= 2 ? rawName : "Cocuk";
  return {
    child_name,
    child_age: Math.min(12, Math.max(2, params.childAge)),
    child_gender: params.childGender || "erkek",
    child_photo_url: params.childPhotoUrl || undefined,
    scenario_id: params.scenarioId,
    learning_outcomes:
      params.learningOutcomeNames.length > 0
        ? params.learningOutcomeNames
        : ["Genel macera ve eglence"],
    visual_style: params.visualStylePromptModifier,
    visual_style_id: params.visualStyleId || undefined,
    page_count: params.pageCount,
    clothing_description: params.clothingDescription?.trim() || undefined,
    custom_variables:
      params.customVariables && Object.keys(params.customVariables).length > 0
        ? params.customVariables
        : undefined,
  };
}
