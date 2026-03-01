export const PAGE_SIZE = 30;

export const STATUS_OPTIONS = [
  "", "PENDING", "PROCESSING", "CONFIRMED", "FAILED", "QUEUE_FAILED", "EXPIRED", "CANCELLED",
] as const;

export const STATUS_COLORS: Record<string, string> = {
  PENDING: "bg-amber-50 text-amber-700 border-amber-200",
  CONFIRMED: "bg-emerald-50 text-emerald-700 border-emerald-200",
  EXPIRED: "bg-slate-100 text-slate-500 border-slate-200",
  CANCELLED: "bg-red-50 text-red-700 border-red-200",
  PROCESSING: "bg-blue-50 text-blue-700 border-blue-200",
  FAILED: "bg-red-50 text-red-700 border-red-200",
  QUEUE_FAILED: "bg-orange-50 text-orange-700 border-orange-200",
};

export const STATUS_LABELS: Record<string, string> = {
  PENDING: "Beklemede",
  CONFIRMED: "Onaylandı",
  EXPIRED: "Süresi Doldu",
  CANCELLED: "İptal",
  PROCESSING: "İşleniyor",
  FAILED: "Başarısız",
  QUEUE_FAILED: "Kuyruk Hatası",
};

export function getStatusColor(status: string): string {
  return STATUS_COLORS[status] ?? "bg-slate-100 text-slate-600 border-slate-200";
}

export function getStatusLabel(status: string): string {
  return STATUS_LABELS[status] ?? status;
}

export function getCoverThumb(item: { page_images?: Record<string, string> | null; cover_thumb?: string | null }): string | null {
  if (item.cover_thumb) return item.cover_thumb;
  if (item.page_images) {
    return item.page_images["0"] ?? item.page_images["page_0"] ?? null;
  }
  return null;
}
