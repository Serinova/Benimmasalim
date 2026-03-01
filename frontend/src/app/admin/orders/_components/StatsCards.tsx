"use client";

import React from "react";
import type { OrderStats, InvoiceDashboard } from "../_lib/types";

interface StatsCardsProps {
  stats: OrderStats | null;
  invoiceDashboard: InvoiceDashboard | null;
  showInvoiceReports: boolean;
  onToggleInvoiceReports: () => void;
  invoiceReportType: string;
  invoiceReportData: Record<string, unknown>[] | null;
  invoiceReportLoading: boolean;
  onLoadInvoiceReport: (type: string) => void;
  onCloseReport: () => void;
}

export const StatsCards = React.memo(function StatsCards({
  stats,
  invoiceDashboard,
  showInvoiceReports,
  onToggleInvoiceReports,
  invoiceReportType,
  invoiceReportData,
  invoiceReportLoading,
  onLoadInvoiceReport,
  onCloseReport,
}: StatsCardsProps) {
  if (!stats) return null;

  return (
    <div className="space-y-4">
      {/* Stats row */}
      <div className="grid grid-cols-5 gap-3">
        <StatCard label="Toplam" value={stats.total} />
        <StatCard label="Beklemede" value={stats.pending} color="text-amber-600" borderColor="border-amber-200" />
        <StatCard label="Onaylanan" value={stats.confirmed} color="text-emerald-600" borderColor="border-emerald-200" />
        <StatCard label="Süresi Dolan" value={stats.expired} color="text-slate-500" />
        <StatCard
          label="Toplam Gelir"
          value={`${stats.total_revenue.toLocaleString("tr-TR")} TL`}
          color="text-violet-600"
          borderColor="border-violet-200"
        />
      </div>

      {/* Invoice reports */}
      {invoiceDashboard && (
        <div>
          <button
            onClick={onToggleInvoiceReports}
            className="mb-2 flex items-center gap-2 text-sm font-semibold text-slate-700 hover:text-violet-700 transition-colors"
          >
            <span className="text-xs">{showInvoiceReports ? "▼" : "▶"}</span>
            Fatura Raporları
            {(invoiceDashboard.pdf_issues_count > 0 || invoiceDashboard.email_issues_count > 0 || invoiceDashboard.token_abuse_count > 0) && (
              <span className="rounded-full bg-red-100 px-2 py-0.5 text-[10px] font-bold text-red-700">
                {invoiceDashboard.pdf_issues_count + invoiceDashboard.email_issues_count + invoiceDashboard.token_abuse_count}
              </span>
            )}
          </button>

          {showInvoiceReports && (
            <div className="space-y-3">
              <div className="grid grid-cols-4 gap-3">
                <InvoiceStatCard
                  label="PDF Sorunlu"
                  value={invoiceDashboard.pdf_issues_count}
                  active={invoiceReportType === "pdf"}
                  hasIssue={invoiceDashboard.pdf_issues_count > 0}
                  onClick={() => onLoadInvoiceReport("pdf")}
                />
                <InvoiceStatCard
                  label="Email Sorunlu"
                  value={invoiceDashboard.email_issues_count}
                  active={invoiceReportType === "email"}
                  hasIssue={invoiceDashboard.email_issues_count > 0}
                  onClick={() => onLoadInvoiceReport("email")}
                />
                <InvoiceStatCard
                  label="Token Şüpheli"
                  value={invoiceDashboard.token_abuse_count}
                  active={invoiceReportType === "token"}
                  hasIssue={invoiceDashboard.token_abuse_count > 0}
                  onClick={() => onLoadInvoiceReport("token")}
                />
                <div className="rounded-lg border bg-white px-3 py-2">
                  <p className="text-[10px] text-slate-500">Toplam Fatura</p>
                  <p className="text-xl font-bold text-violet-600">{invoiceDashboard.total_invoices}</p>
                </div>
              </div>

              {invoiceReportLoading && (
                <div className="flex items-center justify-center py-4">
                  <div className="h-5 w-5 animate-spin rounded-full border-2 border-slate-300 border-t-violet-500" />
                </div>
              )}

              {invoiceReportData && !invoiceReportLoading && (
                <InvoiceReportTable
                  type={invoiceReportType}
                  data={invoiceReportData}
                  onClose={onCloseReport}
                />
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
});

function StatCard({ label, value, color, borderColor }: {
  label: string;
  value: string | number;
  color?: string;
  borderColor?: string;
}) {
  return (
    <div className={`rounded-lg border bg-white px-3 py-2 ${borderColor ?? ""}`}>
      <p className="text-[10px] font-medium text-slate-500">{label}</p>
      <p className={`text-xl font-bold ${color ?? "text-slate-900"}`}>{value}</p>
    </div>
  );
}

function InvoiceStatCard({ label, value, active, hasIssue, onClick }: {
  label: string;
  value: number;
  active: boolean;
  hasIssue: boolean;
  onClick: () => void;
}) {
  return (
    <div
      className={`cursor-pointer rounded-lg border bg-white px-3 py-2 transition-all hover:ring-2 hover:ring-violet-300 ${active ? "ring-2 ring-violet-500" : ""}`}
      onClick={onClick}
    >
      <p className="text-[10px] text-slate-500">{label}</p>
      <p className={`text-xl font-bold ${hasIssue ? "text-red-600" : "text-emerald-600"}`}>{value}</p>
    </div>
  );
}

function InvoiceReportTable({ type, data, onClose }: {
  type: string;
  data: Record<string, unknown>[];
  onClose: () => void;
}) {
  const title =
    type === "pdf" ? "PDF Sorunlu Siparişler" :
    type === "email" ? "Email Sorunlu Faturalar" :
    "Şüpheli Token Kullanımları";

  return (
    <div className="rounded-lg border bg-white">
      <div className="flex items-center justify-between border-b px-3 py-2">
        <p className="text-xs font-semibold text-slate-700">
          {title} <span className="ml-2 text-slate-400">({data.length})</span>
        </p>
        <button onClick={onClose} className="text-xs text-slate-400 hover:text-slate-600">Kapat</button>
      </div>
      {data.length === 0 ? (
        <p className="px-3 py-4 text-center text-xs text-slate-400">Sorun bulunamadı</p>
      ) : (
        <div className="max-h-64 overflow-y-auto">
          <table className="w-full text-xs">
            <thead className="sticky top-0 bg-slate-50">
              <tr>
                {type === "pdf" && (
                  <>
                    <th className="px-2 py-1.5 text-left text-slate-500">Sipariş</th>
                    <th className="px-2 py-1.5 text-left text-slate-500">Çocuk</th>
                    <th className="px-2 py-1.5 text-left text-slate-500">Fatura Durum</th>
                    <th className="px-2 py-1.5 text-left text-slate-500">Hata</th>
                    <th className="px-2 py-1.5 text-left text-slate-500">Retry</th>
                  </>
                )}
                {type === "email" && (
                  <>
                    <th className="px-2 py-1.5 text-left text-slate-500">Fatura No</th>
                    <th className="px-2 py-1.5 text-left text-slate-500">Çocuk</th>
                    <th className="px-2 py-1.5 text-left text-slate-500">Email</th>
                    <th className="px-2 py-1.5 text-left text-slate-500">Durum</th>
                    <th className="px-2 py-1.5 text-left text-slate-500">Hata</th>
                  </>
                )}
                {type === "token" && (
                  <>
                    <th className="px-2 py-1.5 text-left text-slate-500">Token</th>
                    <th className="px-2 py-1.5 text-left text-slate-500">Çocuk</th>
                    <th className="px-2 py-1.5 text-left text-slate-500">Kullanım</th>
                    <th className="px-2 py-1.5 text-left text-slate-500">Durum</th>
                    <th className="px-2 py-1.5 text-left text-slate-500">Son Kullanım</th>
                  </>
                )}
              </tr>
            </thead>
            <tbody className="divide-y">
              {data.map((row, i) => (
                <tr key={i} className="hover:bg-slate-50">
                  {type === "pdf" && (
                    <>
                      <td className="px-2 py-1.5 font-mono">{String(row.order_id || "").slice(0, 8)}</td>
                      <td className="px-2 py-1.5">{String(row.child_name || "")}</td>
                      <td className="px-2 py-1.5">
                        <span className={`rounded px-1 py-0.5 text-[10px] font-medium ${
                          row.invoice_status === "FAILED" ? "bg-red-100 text-red-700" :
                          row.invoice_status === "MISSING" ? "bg-slate-100 text-slate-700" :
                          "bg-amber-100 text-amber-700"
                        }`}>{String(row.invoice_status || "MISSING")}</span>
                      </td>
                      <td className="max-w-[120px] truncate px-2 py-1.5 text-red-500" title={String(row.last_error || "")}>{String(row.last_error || "-")}</td>
                      <td className="px-2 py-1.5">{String(row.retry_count ?? 0)}</td>
                    </>
                  )}
                  {type === "email" && (
                    <>
                      <td className="px-2 py-1.5 font-mono">{String(row.invoice_number || "")}</td>
                      <td className="px-2 py-1.5">{String(row.child_name || "")}</td>
                      <td className="max-w-[120px] truncate px-2 py-1.5">{String(row.billing_email || "yok")}</td>
                      <td className="px-2 py-1.5">
                        <span className={`rounded px-1 py-0.5 text-[10px] font-medium ${
                          row.email_status === "FAILED" ? "bg-red-100 text-red-700" : "bg-slate-100 text-slate-700"
                        }`}>{String(row.email_status || "NOT_SENT")}</span>
                      </td>
                      <td className="max-w-[120px] truncate px-2 py-1.5 text-red-500" title={String(row.email_error || "")}>{String(row.email_error || "-")}</td>
                    </>
                  )}
                  {type === "token" && (
                    <>
                      <td className="px-2 py-1.5 font-mono">{String(row.token_hash_prefix || "")}</td>
                      <td className="px-2 py-1.5">{String(row.child_name || "")}</td>
                      <td className="px-2 py-1.5 font-medium">{String(row.used_count ?? 0)}/{String(row.max_uses ?? 1)}</td>
                      <td className="px-2 py-1.5">
                        {row.is_revoked ? <span className="rounded bg-red-100 px-1 py-0.5 text-[10px] text-red-700">İptal</span> :
                         row.is_expired ? <span className="rounded bg-slate-100 px-1 py-0.5 text-[10px] text-slate-700">Süresi Dolmuş</span> :
                         <span className="rounded bg-emerald-100 px-1 py-0.5 text-[10px] text-emerald-700">Aktif</span>}
                      </td>
                      <td className="px-2 py-1.5">{row.last_used_at ? new Date(String(row.last_used_at)).toLocaleString("tr-TR") : "-"}</td>
                    </>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
