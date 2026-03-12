/**
 * API client for backend communication — Prompt System V2.
 *
 * All AI prompt composition happens on the backend.
 * Frontend sends IDs only (scenario_id, visual_style_id)
 * plus child meta and clothing_description.
 */

// Runtime detection: production uses backend Cloud Run URL directly,
// localhost uses Next.js proxy rewrite (/api/v1 → backend).
function resolveApiBaseUrl(): string {
  // Build-time env var (if set during docker build)
  if (process.env.NEXT_PUBLIC_API_URL) return process.env.NEXT_PUBLIC_API_URL;

  // Client-side runtime detection
  if (typeof window !== "undefined") {
    const host = window.location.hostname;
    if (
      host.includes("benimmasalim") ||
      host.includes("run.app") ||
      host.includes("vercel.app")
    ) {
      return "https://benimmasalim-backend-554846094227.europe-west1.run.app/api/v1";
    }
  }

  // Local dev fallback (proxied via next.config.js rewrites)
  return "/api/v1";
}

export const API_BASE_URL = resolveApiBaseUrl();

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

    // Refresh failed — clear stale tokens and redirect to login
    if (typeof window !== "undefined") {
      localStorage.removeItem("token");
      localStorage.removeItem("refreshToken");
      localStorage.removeItem("user");
      window.dispatchEvent(new Event("auth-change"));
      const currentPath = window.location.pathname;
      if (currentPath.startsWith("/account")) {
        window.location.href = `/auth/login?returnUrl=${encodeURIComponent(currentPath)}`;
      }
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


/** V2: Visual style — style injection happens via style_config.py on the backend. */
export interface VisualStyle {
  id: string;
  name: string;
  /** Kullanıcıya gösterilen isim (boşsa name kullanılır). */
  display_name?: string | null;
  thumbnail_url: string;
  is_active: boolean;
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
 *   scenario_id, visual_style, visual_style_id,
 *   page_count, clothing_description, custom_variables.
 */
export interface GenerateStoryV2Request {
  child_name: string;
  child_age: number;
  child_gender: string;
  child_photo_url?: string;
  scenario_id: string;
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
  clothing_description?: string; // outfit lock for image generation
  story_title: string;
  story_pages: StoryPage[];
  product_id?: string;
  product_name?: string;
  product_price?: number;
  scenario_name?: string | null;
  visual_style_name?: string | null;
  visual_style?: string;
  id_weight?: number;
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
  id_weight?: number | null;
  clothing_description?: string | null;
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

export interface BillingDataPayload {
  billing_type: "individual" | "corporate";
  billing_tc_no?: string | null;
  billing_full_name?: string | null;
  billing_email?: string | null;
  billing_phone?: string | null;
  billing_company_name?: string | null;
  billing_tax_id?: string | null;
  billing_tax_office?: string | null;
  billing_address?: Record<string, string> | null;
  use_shipping_address?: boolean;
}

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
  has_coloring_book?: boolean;
  billing?: BillingDataPayload | null;
}

export interface CompleteTrialResponse {
  success: boolean;
  trial_id: string;
  status: string;
  message: string;
  order_id?: string | null; // Main story order or coloring order (if created)
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
  promoCode?: string | null,
  billing?: BillingDataPayload | null,
): Promise<CreateTrialPaymentResponse> {
  const headers: Record<string, string> = {};
  if (trialToken) headers["X-Trial-Token"] = trialToken;
  return fetchAPI(`/trials/${trialId}/create-payment`, {
    method: "POST",
    headers,
    body: JSON.stringify({
      promo_code: promoCode || null,
      billing: billing || null,
    }),
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

// ─── Coloring Book Order ────────────────────────────────────────

export interface AddColoringBookResponse {
  coloring_order_id: string;
  payment_url: string;
  amount: number;
}

/**
 * Add coloring book to an existing completed story order.
 * Creates a new order and returns payment URL for checkout.
 */
export async function addColoringBookToOrder(
  orderId: string,
): Promise<AddColoringBookResponse> {
  return fetchAPI(`/orders/${orderId}/add-coloring-book`, {
    method: "POST",
    body: JSON.stringify({}),
  });
}

/**
 * Add coloring book to an existing completed TRIAL.
 * Creates an Iyzico payment form specifically for the coloring book.
 * @param trialId - The StoryPreview ID
 * @param trialToken - X-Trial-Token for ownership verification
 */
export async function addColoringBookToTrial(
  trialId: string,
  trialToken?: string,
): Promise<CreateTrialPaymentResponse> {
  const headers: Record<string, string> = {};
  if (trialToken) headers["X-Trial-Token"] = trialToken;
  return fetchAPI(`/trials/${trialId}/add-coloring-book`, {
    method: "POST",
    headers,
    body: JSON.stringify({}),
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

// ─── User Account ────────────────────────────────────────────────

export interface UserOrder {
  id: string;
  status: string;
  child_name: string;
  created_at: string;
  payment_amount: number | null;
  tracking_number: string | null;
  carrier: string | null;
  has_audio_book: boolean;
  total_pages: number;
  completed_pages: number;
}

export interface UserProfile {
  id: string;
  email: string | null;
  full_name: string | null;
  phone: string | null;
  role: string;
  is_guest: boolean;
}

/**
 * Fetch authenticated user's orders (returns paginated response, extracts items for backward compat).
 */
export async function getUserOrders(): Promise<UserOrder[]> {
  const res = await fetchAPI<PaginatedOrders | UserOrder[]>("/orders");
  if (Array.isArray(res)) return res;
  return (res as PaginatedOrders).items ?? [];
}

/**
 * Fetch authenticated user's profile.
 */
export async function getUserProfile(): Promise<UserProfile> {
  return fetchAPI("/auth/me");
}

// ─── Order Detail & Account Management ───────────────────────────

export interface OrderPageStatus {
  page_number: number;
  status: string;
  is_cover?: boolean;
  preview_image_url?: string | null;
  image_url?: string | null;
}

export interface TimelineEvent {
  action: string;
  status: string;
  timestamp: string;
}

export interface OrderDetail {
  id: string;
  status: string;
  status_description: string;
  status_hint: string | null;
  child_name: string;
  child_age: number;
  child_gender: string | null;
  created_at: string;
  updated_at: string | null;
  payment_amount: number | null;
  payment_status: string | null;
  shipping_address: {
    full_name?: string;
    phone?: string;
    address_line1?: string;
    address_line2?: string;
    city?: string;
    district?: string;
    postal_code?: string;
  } | null;
  tracking_number: string | null;
  carrier: string | null;
  final_pdf_url: string | null;
  has_audio_book: boolean;
  audio_type: string | null;
  audio_file_url: string | null;
  qr_code_url: string | null;
  total_pages: number;
  completed_pages: number;
  cover_regenerate_count: number;
  max_cover_regenerate: number;
  delivered_at: string | null;
  is_guest_order: boolean;
  billing: BillingSummary | null;
  invoice: InvoiceSummary | null;
  pages: OrderPageStatus[];
  timeline_events: TimelineEvent[];
}

export interface InvoiceSummary {
  invoice_number: string;
  invoice_status: string;
  pdf_ready: boolean;
  issued_at: string | null;
  needs_credit_note: boolean;
  email_sent: boolean;
  email_status: string | null;
  // Admin-only fields (present in admin detail response)
  email_sent_at?: string | null;
  email_error?: string | null;
  email_retry_count?: number;
  email_resent_count?: number;
  email_last_resent_at?: string | null;
}

export interface BillingSummary {
  billing_type: string | null;
  billing_tc_no?: string | null;
  billing_full_name: string | null;
  billing_email: string | null;
  billing_phone: string | null;
  billing_company_name: string | null;
  billing_tax_id: string | null;
  billing_tax_office: string | null;
  billing_address: Record<string, string> | null;
}

export interface UserTrial {
  id: string;
  status: string;
  child_name: string;
  story_title: string;
  created_at: string;
  product_name: string | null;
  product_price: number | null;
  has_audio_book: boolean;
  has_coloring_book: boolean;
  preview_images: Record<string, string> | null;
  confirmation_token: string;
}

/**
 * Fetch a single order's details.
 * @param include - comma-separated sections to include: "pages", "timeline"
 */
export async function getOrderDetail(
  orderId: string,
  include?: string,
): Promise<OrderDetail> {
  const qs = include ? `?include=${encodeURIComponent(include)}` : "";
  return fetchAPI(`/orders/${orderId}${qs}`);
}

export interface BillingUpdatePayload {
  billing_type: "individual" | "corporate";
  billing_tc_no?: string | null;
  billing_full_name?: string | null;
  billing_email?: string | null;
  billing_phone?: string | null;
  billing_company_name?: string | null;
  billing_tax_id?: string | null;
  billing_tax_office?: string | null;
  billing_address?: Record<string, string> | null;
  use_shipping_address?: boolean;
}

export async function updateOrderBilling(
  orderId: string,
  billing: BillingUpdatePayload,
): Promise<{ ok: boolean; billing: BillingSummary }> {
  return fetchAPI(`/orders/${orderId}/billing`, {
    method: "PATCH",
    body: JSON.stringify(billing),
  });
}

/**
 * Fetch user's active trials (in-progress story previews).
 */
export async function getUserTrials(): Promise<UserTrial[]> {
  return fetchAPI("/trials/me");
}

/**
 * Fetch user's paid/completed trials (shown as "Siparişlerim").
 */
export async function getUserPaidTrials(): Promise<UserTrial[]> {
  return fetchAPI("/trials/me?include_paid=true");
}

/**
 * Update user profile (name, phone).
 */
export async function updateProfile(data: { full_name?: string; phone?: string }): Promise<UserProfile> {
  return fetchAPI("/auth/me", {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

// ─── Auth Extensions ─────────────────────────────────────────────

export async function forgotPassword(email: string): Promise<{ message: string }> {
  return fetchAPI("/auth/forgot-password", {
    method: "POST",
    body: JSON.stringify({ email }),
  });
}

export async function resetPassword(token: string, email: string, newPassword: string): Promise<{ message: string }> {
  return fetchAPI("/auth/reset-password", {
    method: "POST",
    body: JSON.stringify({ token, email, new_password: newPassword }),
  });
}

export async function changePassword(currentPassword: string, newPassword: string): Promise<{ message: string }> {
  return fetchAPI("/auth/change-password", {
    method: "POST",
    body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
  });
}

export async function convertGuest(email: string, password: string, fullName: string) {
  return fetchAPI<{ access_token: string; refresh_token: string; user: { id: string; email: string; full_name: string; role: string } }>(
    "/auth/convert-guest",
    { method: "POST", body: JSON.stringify({ email, password, full_name: fullName }) },
  );
}

// ─── Profile: Addresses ──────────────────────────────────────────

export interface UserAddress {
  id: string;
  label: string;
  full_name: string;
  phone: string | null;
  address_line: string;
  city: string;
  district: string | null;
  postal_code: string | null;
  is_default: boolean;
}

export async function getAddresses(): Promise<UserAddress[]> {
  return fetchAPI("/profile/addresses");
}

export async function createAddress(data: Omit<UserAddress, "id">): Promise<UserAddress> {
  return fetchAPI("/profile/addresses", { method: "POST", body: JSON.stringify(data) });
}

export async function updateAddress(id: string, data: Partial<UserAddress>): Promise<UserAddress> {
  return fetchAPI(`/profile/addresses/${id}`, { method: "PATCH", body: JSON.stringify(data) });
}

export async function deleteAddress(id: string): Promise<void> {
  return fetchAPI(`/profile/addresses/${id}`, { method: "DELETE" });
}

export async function setDefaultAddress(id: string): Promise<UserAddress> {
  return fetchAPI(`/profile/addresses/${id}/set-default`, { method: "PATCH" });
}

// ─── Profile: Notification Preferences ───────────────────────────

export interface NotificationPrefs {
  email_order_updates: boolean;
  email_marketing: boolean;
  sms_order_updates: boolean;
}

export async function getNotificationPrefs(): Promise<NotificationPrefs> {
  return fetchAPI("/profile/notification-preferences");
}

export async function updateNotificationPrefs(data: Partial<NotificationPrefs>): Promise<NotificationPrefs> {
  return fetchAPI("/profile/notification-preferences", { method: "PATCH", body: JSON.stringify(data) });
}

// ─── Profile: Children ───────────────────────────────────────────

export interface ChildProfile {
  id: string;
  name: string;
  age: number;
  gender: string | null;
  photo_url: string | null;
  order_count: number;
}

export async function getChildren(): Promise<ChildProfile[]> {
  return fetchAPI("/profile/children");
}

export async function createChild(data: { name: string; age: number; gender?: string }): Promise<ChildProfile> {
  return fetchAPI("/profile/children", { method: "POST", body: JSON.stringify(data) });
}

export async function deleteChild(id: string): Promise<void> {
  return fetchAPI(`/profile/children/${id}`, { method: "DELETE" });
}

// ─── Privacy / KVKK ─────────────────────────────────────────────

export async function deletePhotoNow(orderId: string): Promise<{ message: string }> {
  return fetchAPI("/privacy/delete-photo-now", { method: "POST", body: JSON.stringify({ order_id: orderId }) });
}

export async function deleteAccount(password: string, reason?: string): Promise<{ message: string }> {
  return fetchAPI("/privacy/account", { method: "DELETE", body: JSON.stringify({ password, reason }) });
}

export async function exportData(): Promise<Record<string, unknown>> {
  return fetchAPI("/privacy/export-data");
}

// ─── Enhanced Orders (paginated) ─────────────────────────────────

export interface PaginatedOrders {
  items: UserOrder[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

export async function getUserOrdersPaginated(params?: {
  status_filter?: string;
  search?: string;
  page?: number;
  per_page?: number;
}): Promise<PaginatedOrders> {
  const qs = new URLSearchParams();
  if (params?.status_filter) qs.set("status_filter", params.status_filter);
  if (params?.search) qs.set("search", params.search);
  if (params?.page) qs.set("page", String(params.page));
  if (params?.per_page) qs.set("per_page", String(params.per_page));
  const query = qs.toString();
  return fetchAPI(`/orders${query ? `?${query}` : ""}`);
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
