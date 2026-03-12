import {
  API_BASE_URL,
  getAdminHeaders as getAuthHeaders,
  getAdminHeadersNoContent as getAuthHeadersNoContent,
} from "@/lib/adminFetch";
import type {
  OrderListItem,
  OrderDetail,
  OrderStats,
  InvoiceDashboard,
  BackCoverConfig,
} from "./types";

// ── List ──────────────────────────────────────────────────────────────

export async function fetchOrdersList(params: {
  status?: string;
  page: number;
  pageSize: number;
  search?: string;
  dateFrom?: string;
  dateTo?: string;
}): Promise<{ items: OrderListItem[]; total: number }> {
  const qs = new URLSearchParams();
  if (params.status) qs.set("status", params.status);
  qs.set("limit", String(params.pageSize));
  qs.set("offset", String(params.page * params.pageSize));
  if (params.search) qs.set("search", params.search);
  if (params.dateFrom) qs.set("date_from", params.dateFrom);
  if (params.dateTo) qs.set("date_to", params.dateTo);

  const res = await fetch(`${API_BASE_URL}/admin/orders/previews?${qs.toString()}`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(typeof err.detail === "string" ? err.detail : "Siparişler yüklenemedi");
  }
  const data = await res.json();
  if (data.items) {
    return { items: data.items, total: data.total ?? data.items.length };
  }
  if (Array.isArray(data)) {
    return { items: data as OrderListItem[], total: data.length };
  }
  return { items: [], total: 0 };
}

// ── Detail ────────────────────────────────────────────────────────────

export async function fetchOrderDetail(
  id: string,
  signal?: AbortSignal,
): Promise<OrderDetail> {
  const res = await fetch(`${API_BASE_URL}/admin/orders/previews/${id}`, {
    headers: getAuthHeaders(),
    signal,
  });
  if (!res.ok) throw new Error("Sipariş detayı yüklenemedi");
  return res.json();
}

// ── Stats ─────────────────────────────────────────────────────────────

export async function fetchOrderStats(): Promise<OrderStats> {
  const res = await fetch(`${API_BASE_URL}/admin/orders/stats/previews`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error("İstatistikler yüklenemedi");
  const data = await res.json();
  return {
    total: data.total ?? 0,
    pending: data.pending ?? 0,
    confirmed: data.confirmed ?? 0,
    expired: data.expired ?? 0,
    total_revenue: data.total_revenue ?? 0,
  };
}

// ── Invoice Dashboard ─────────────────────────────────────────────────

export async function fetchInvoiceDashboard(): Promise<InvoiceDashboard | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/admin/orders/invoices/dashboard`, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

export async function fetchInvoiceReport(type: string): Promise<Record<string, unknown>[]> {
  const endpoint =
    type === "pdf" ? "invoices/issues" :
    type === "email" ? "invoices/email-issues" :
    "invoices/token-abuse";
  const res = await fetch(`${API_BASE_URL}/admin/orders/${endpoint}`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error("Rapor yüklenemedi");
  return res.json();
}

// ── Back Cover Config ─────────────────────────────────────────────────

export async function fetchBackCoverConfig(): Promise<BackCoverConfig | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/admin/back-cover/default`, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

// ── Actions ───────────────────────────────────────────────────────────

export async function updateOrderStatus(id: string, newStatus: string): Promise<void> {
  const res = await fetch(
    `${API_BASE_URL}/admin/orders/previews/${id}/status?status=${newStatus}`,
    { method: "PATCH", headers: getAuthHeaders() },
  );
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Güncelleme başarısız");
  }
}

export async function generateBook(previewId: string): Promise<{ success: boolean; pdf_url?: string; pdf_error?: string; audio_url?: string; detail?: string }> {
  const res = await fetch(
    `${API_BASE_URL}/admin/orders/previews/${previewId}/generate-book`,
    { method: "POST", headers: getAuthHeaders() },
  );
  if (res.status === 401) throw new Error("AUTH_EXPIRED");
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Kitap oluşturma başarısız");
  return data;
}

export async function downloadPdfUrl(previewId: string): Promise<string> {
  const res = await fetch(
    `${API_BASE_URL}/admin/orders/previews/${previewId}/download-pdf`,
    { headers: getAuthHeaders() },
  );
  if (res.status === 401) throw new Error("AUTH_EXPIRED");
  if (res.status === 404) throw new Error("PDF bulunamadı. Önce 'Kitap Üret' butonuna basın.");
  const data = await res.json().catch(() => { throw new Error(`Sunucu hatası (HTTP ${res.status})`); });
  if (!res.ok) throw new Error(typeof data.detail === "string" ? data.detail : "PDF alınamadı");
  return data.pdf_url as string;
}

export async function generateRemainingPages(previewId: string): Promise<{ message?: string }> {
  const res = await fetch(
    `${API_BASE_URL}/admin/orders/previews/${previewId}/generate-remaining`,
    { method: "POST", headers: getAuthHeaders() },
  );
  if (!res.ok) throw new Error("İşlem başarısız");
  return res.json();
}

export async function recomposeImages(previewId: string): Promise<OrderDetail> {
  const res = await fetch(
    `${API_BASE_URL}/admin/orders/previews/${previewId}/composed-images?force_recompose=true`,
    { headers: getAuthHeaders() },
  );
  if (!res.ok) throw new Error("Recompose başarısız");
  const detailRes = await fetch(`${API_BASE_URL}/admin/orders/previews/${previewId}`, {
    headers: getAuthHeaders(),
  });
  if (!detailRes.ok) throw new Error("Detay yüklenemedi");
  return detailRes.json();
}

export async function generateColoringBook(previewId: string): Promise<{ success: boolean; coloring_pdf_url?: string; message?: string; detail?: string }> {
  const res = await fetch(
    `${API_BASE_URL}/admin/orders/previews/${previewId}/generate-coloring-book`,
    { method: "POST", headers: getAuthHeaders() },
  );
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "İşlem başarısız");
  return data;
}

// ── Invoice Actions ───────────────────────────────────────────────────

export async function invoiceAction(
  orderId: string,
  action: string,
  method: string = "POST",
): Promise<Record<string, unknown>> {
  const res = await fetch(
    `${API_BASE_URL}/admin/orders/${orderId}/invoice/${action}`,
    { method, headers: getAuthHeadersNoContent() },
  );
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "İşlem başarısız");
  return data;
}

export async function createInvoice(orderId: string): Promise<Record<string, unknown>> {
  const res = await fetch(
    `${API_BASE_URL}/admin/orders/${orderId}/invoice/create`,
    { method: "POST", headers: getAuthHeadersNoContent() },
  );
  const data = await res.json();
  if (!res.ok) throw new Error(typeof data.detail === "string" ? data.detail : "Fatura oluşturulamadı");
  return data;
}

export async function downloadInvoicePdf(orderId: string, invoiceNumber: string): Promise<void> {
  const res = await fetch(
    `${API_BASE_URL}/admin/orders/${orderId}/invoice/download`,
    { headers: getAuthHeadersNoContent() },
  );
  if (!res.ok) throw new Error("İndirme başarısız");
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `fatura_${invoiceNumber}.pdf`;
  a.click();
  URL.revokeObjectURL(url);
}
