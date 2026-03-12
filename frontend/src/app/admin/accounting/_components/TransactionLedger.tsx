"use client";

import { Search, ChevronLeft, ChevronRight, Headphones, Palette } from "lucide-react";
import type { TransactionsResponse } from "../_lib/accountingApi";

function fmt(n: number) {
  return n.toLocaleString("tr-TR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function fmtDate(iso: string | null) {
  if (!iso) return "-";
  return new Date(iso).toLocaleDateString("tr-TR", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function statusLabel(s: string) {
  const m: Record<string, string> = {
    COMPLETED: "Tamamlandı",
    COMPLETING: "İşleniyor",
    CONFIRMED: "Onaylandı",
    PAID: "Ödendi",
    PROCESSING: "İşlemde",
    READY_FOR_PRINT: "Baskıya Hazır",
    SHIPPED: "Kargoda",
    DELIVERED: "Teslim Edildi",
    REFUNDED: "İade",
    CANCELLED: "İptal",
  };
  return m[s] || s;
}

function statusColor(s: string) {
  if (["COMPLETED", "CONFIRMED", "PAID", "DELIVERED"].includes(s))
    return "bg-emerald-50 text-emerald-700";
  if (["REFUNDED", "CANCELLED"].includes(s)) return "bg-red-50 text-red-700";
  if (["PROCESSING", "COMPLETING", "READY_FOR_PRINT", "SHIPPED"].includes(s))
    return "bg-blue-50 text-blue-700";
  return "bg-slate-100 text-slate-600";
}

interface Props {
  data: TransactionsResponse | null;
  loading: boolean;
  search: string;
  onSearchChange: (v: string) => void;
  onPageChange: (p: number) => void;
}

export default function TransactionLedger({
  data,
  loading,
  search,
  onSearchChange,
  onPageChange,
}: Props) {
  const totalPages = data ? Math.ceil(data.total / data.limit) : 1;
  const currentPage = data?.page ?? 1;

  return (
    <div className="space-y-4">
      {/* Search bar */}
      <div className="flex items-center gap-3">
        <div className="flex flex-1 items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2">
          <Search className="h-4 w-4 text-slate-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder="E-posta, isim veya çocuk adı ara..."
            className="flex-1 bg-transparent text-sm text-slate-700 placeholder-slate-400 focus:outline-none"
          />
        </div>
        <span className="shrink-0 text-sm text-slate-500">
          Toplam: {data?.total ?? 0} işlem
        </span>
      </div>

      {/* Table */}
      <div className="overflow-x-auto rounded-xl border border-slate-100">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-100 bg-slate-50 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">
              <th className="px-4 py-3">Tarih</th>
              <th className="px-4 py-3">Müşteri</th>
              <th className="px-4 py-3">Çocuk</th>
              <th className="px-4 py-3">Ürün</th>
              <th className="px-4 py-3 text-right">Brüt</th>
              <th className="px-4 py-3 text-right">İndirim</th>
              <th className="px-4 py-3 text-right">Net</th>
              <th className="px-4 py-3 text-right">KDV</th>
              <th className="px-4 py-3">Kupon</th>
              <th className="px-4 py-3">Durum</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-50">
            {loading ? (
              Array.from({ length: 8 }).map((_, i) => (
                <tr key={i}>
                  {Array.from({ length: 10 }).map((_, j) => (
                    <td key={j} className="px-4 py-3">
                      <div className="h-4 animate-pulse rounded bg-slate-100" />
                    </td>
                  ))}
                </tr>
              ))
            ) : !data?.items.length ? (
              <tr>
                <td colSpan={10} className="px-4 py-12 text-center text-slate-400">
                  Bu dönemde işlem bulunamadı
                </td>
              </tr>
            ) : (
              data.items.map((txn) => (
                <tr key={txn.id} className="hover:bg-slate-50/80">
                  <td className="whitespace-nowrap px-4 py-3 text-xs text-slate-500">
                    {fmtDate(txn.paid_at)}
                  </td>
                  <td className="px-4 py-3">
                    <div className="max-w-[160px]">
                      <p className="truncate font-medium text-slate-800">{txn.customer_name}</p>
                      <p className="truncate text-xs text-slate-400">{txn.customer_email}</p>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-slate-700">{txn.child_name}</td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-1">
                      <span className="text-slate-700">{txn.product_name}</span>
                      {txn.has_audio && (
                        <span title="Sesli kitap"><Headphones className="h-3.5 w-3.5 text-blue-500" /></span>
                      )}
                      {txn.has_coloring && (
                        <span title="Boyama kitabı"><Palette className="h-3.5 w-3.5 text-orange-400" /></span>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-right text-slate-700">{fmt(txn.gross)} ₺</td>
                  <td className="px-4 py-3 text-right">
                    {txn.discount > 0 ? (
                      <span className="text-amber-600">-{fmt(txn.discount)} ₺</span>
                    ) : (
                      <span className="text-slate-400">-</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-right font-semibold text-slate-900">
                    {fmt(txn.net)} ₺
                  </td>
                  <td className="px-4 py-3 text-right text-xs text-violet-600">
                    {fmt(txn.vat)} ₺
                  </td>
                  <td className="px-4 py-3">
                    {txn.promo_code ? (
                      <span className="inline-flex items-center rounded-full bg-amber-50 px-2 py-0.5 text-xs font-mono font-medium text-amber-700">
                        {txn.promo_code}
                      </span>
                    ) : (
                      <span className="text-slate-300">-</span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${statusColor(txn.status)}`}
                    >
                      {statusLabel(txn.status)}
                    </span>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between text-sm">
          <span className="text-slate-500">
            Sayfa {currentPage} / {totalPages}
          </span>
          <div className="flex items-center gap-2">
            <button
              onClick={() => onPageChange(currentPage - 1)}
              disabled={currentPage <= 1}
              className="flex items-center gap-1 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-slate-700 hover:bg-slate-50 disabled:opacity-40"
            >
              <ChevronLeft className="h-4 w-4" />
              Önceki
            </button>
            <button
              onClick={() => onPageChange(currentPage + 1)}
              disabled={currentPage >= totalPages}
              className="flex items-center gap-1 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-slate-700 hover:bg-slate-50 disabled:opacity-40"
            >
              Sonraki
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
