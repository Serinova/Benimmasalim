import { API_BASE_URL, getAdminHeaders, getAdminHeadersNoContent } from "@/lib/adminFetch";

function qs(params: Record<string, string | number | undefined | null>): string {
  const p = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v != null && v !== "") p.set(k, String(v));
  }
  const s = p.toString();
  return s ? `?${s}` : "";
}

async function apiFetch<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE_URL}/admin/accounting${path}`, {
    headers: getAdminHeaders(),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(typeof err.detail === "string" ? err.detail : "İstek başarısız");
  }
  return res.json() as Promise<T>;
}

// ── Types ──────────────────────────────────────────────────────────────────

export interface AccountingSummary {
  gross_revenue: number;
  total_discount: number;
  net_revenue: number;
  vat_amount: number;
  revenue_ex_vat: number;
  refund_total: number;
  promo_savings: number;
  order_count: number;
  promo_used_count: number;
  audio_book_count: number;
  coloring_book_count: number;
  from_date: string | null;
  to_date: string | null;
}

export interface RevenuePoint {
  period: string;
  gross: number;
  discount: number;
  net: number;
  count: number;
}

export interface ProductRevenue {
  product_name: string;
  count: number;
  gross: number;
  discount: number;
  net: number;
}

export interface PromoStat {
  code: string;
  uses: number;
  total_discount: number;
  gross_before_discount: number;
  discount_pct: number;
  discount_type: string | null;
  discount_value: number | null;
  is_active: boolean | null;
}

export interface Transaction {
  id: string;
  customer_name: string;
  customer_email: string;
  child_name: string;
  product_name: string;
  gross: number;
  discount: number;
  net: number;
  vat: number;
  promo_code: string | null;
  paid_at: string | null;
  payment_ref: string | null;
  status: string;
  source: "preview" | "order";
  has_audio: boolean;
  has_coloring: boolean;
}

export interface TransactionsResponse {
  items: Transaction[];
  total: number;
  page: number;
  limit: number;
}

// ── API calls ──────────────────────────────────────────────────────────────

export async function fetchSummary(from_date?: string, to_date?: string): Promise<AccountingSummary> {
  return apiFetch(`/summary${qs({ from_date, to_date })}`);
}

export async function fetchRevenueOverTime(
  period: "daily" | "weekly" | "monthly",
  from_date?: string,
  to_date?: string,
): Promise<RevenuePoint[]> {
  return apiFetch(`/revenue-over-time${qs({ period, from_date, to_date })}`);
}

export async function fetchByProduct(from_date?: string, to_date?: string): Promise<ProductRevenue[]> {
  return apiFetch(`/by-product${qs({ from_date, to_date })}`);
}

export async function fetchPromoAnalysis(from_date?: string, to_date?: string): Promise<PromoStat[]> {
  return apiFetch(`/promo-analysis${qs({ from_date, to_date })}`);
}

export async function fetchTransactions(params: {
  from_date?: string;
  to_date?: string;
  page?: number;
  limit?: number;
  search?: string;
}): Promise<TransactionsResponse> {
  return apiFetch(`/transactions${qs(params)}`);
}

export async function downloadTransactionsCsv(from_date?: string, to_date?: string): Promise<void> {
  const res = await fetch(
    `${API_BASE_URL}/admin/accounting/export-csv${qs({ from_date, to_date })}`,
    { headers: getAdminHeadersNoContent() },
  );
  if (!res.ok) throw new Error("CSV indirilemedi");
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  const cd = res.headers.get("Content-Disposition") || "";
  const match = cd.match(/filename="([^"]+)"/);
  a.download = match ? match[1] : "islem_defteri.csv";
  a.href = url;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
