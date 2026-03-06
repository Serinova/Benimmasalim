"use client";

import React from "react";
import type { OrderDetail } from "../../_lib/types";

const PAID_STATUSES = new Set([
  // Order statuses
  "PAID", "PROCESSING", "READY_FOR_PRINT", "SHIPPED", "DELIVERED",
  // StoryPreview statuses (admin panel uses these)
  "CONFIRMED", "COMPLETING", "COMPLETED",
]);

interface PaymentTabProps {
  detail: OrderDetail;
  onInvoiceAction: (orderId: string, action: string, method?: string, successMsg?: string) => void;
  onDownloadInvoicePdf: (orderId: string, invoiceNumber: string) => void;
  onCreateInvoice?: (orderId: string) => void;
}

export function PaymentTab({ detail, onInvoiceAction, onDownloadInvoicePdf, onCreateInvoice }: PaymentTabProps) {
  const canCreateInvoice = !detail.invoice && PAID_STATUSES.has(detail.status?.toUpperCase() ?? "");
  return (
    <div className="space-y-4">
      {/* Billing info */}
      {detail.billing?.billing_type && (
        <div className="rounded-lg border bg-amber-50 p-3">
          <p className="mb-2 text-xs font-semibold text-slate-700">Fatura Bilgileri</p>
          <div className="grid grid-cols-2 gap-1 text-xs">
            <span className="text-slate-500">Tip:</span>
            <span className="font-medium">{detail.billing.billing_type === "corporate" ? "Kurumsal" : "Bireysel"}</span>
            {detail.billing.billing_full_name && (
              <><span className="text-slate-500">Ad Soyad:</span><span className="font-medium">{detail.billing.billing_full_name}</span></>
            )}
            {detail.billing.billing_tc_no && (
              <><span className="text-slate-500">TC Kimlik No:</span><span className="font-medium">{detail.billing.billing_tc_no}</span></>
            )}
            {detail.billing.billing_company_name && (
              <><span className="text-slate-500">Şirket:</span><span className="font-medium">{detail.billing.billing_company_name}</span></>
            )}
            {detail.billing.billing_tax_id && (
              <><span className="text-slate-500">Vergi No:</span><span className="font-medium">{detail.billing.billing_tax_id}</span></>
            )}
            {detail.billing.billing_tax_office && (
              <><span className="text-slate-500">Vergi Dairesi:</span><span className="font-medium">{detail.billing.billing_tax_office}</span></>
            )}
            {detail.billing.billing_email && (
              <><span className="text-slate-500">Email:</span><span className="font-medium">{detail.billing.billing_email}</span></>
            )}
            {detail.billing.billing_phone && (
              <><span className="text-slate-500">Telefon:</span><span className="font-medium">{detail.billing.billing_phone}</span></>
            )}
            {detail.billing.billing_address && (
              <>
                <span className="text-slate-500">Adres:</span>
                <span className="font-medium">
                  {typeof detail.billing.billing_address === "object"
                    ? [
                      (detail.billing.billing_address as Record<string, string>).address_line ||
                      (detail.billing.billing_address as Record<string, string>).address || "",
                      (detail.billing.billing_address as Record<string, string>).district || "",
                      (detail.billing.billing_address as Record<string, string>).city || "",
                      (detail.billing.billing_address as Record<string, string>).postalCode || "",
                    ].filter(Boolean).join(", ")
                    : String(detail.billing.billing_address)}
                </span>
              </>
            )}
          </div>
        </div>
      )}

      {/* Create invoice button — when no invoice yet and order is paid */}
      {canCreateInvoice && onCreateInvoice && (
        <div className="rounded-lg border border-dashed border-amber-400 bg-amber-50 p-3">
          <p className="mb-2 text-xs text-slate-600">Bu sipariş için henüz fatura oluşturulmamış.</p>
          <button
            onClick={() => onCreateInvoice(detail.id)}
            className="w-full rounded bg-amber-600 px-3 py-2 text-xs font-semibold text-white hover:bg-amber-700"
          >
            Fatura Oluştur
          </button>
        </div>
      )}

      {/* Invoice info */}
      {detail.invoice && <InvoiceSection detail={detail} onInvoiceAction={onInvoiceAction} onDownloadInvoicePdf={onDownloadInvoicePdf} />}

      {!detail.billing?.billing_type && !detail.invoice && !canCreateInvoice && (
        <div className="py-8 text-center text-sm text-slate-400">Ödeme/fatura bilgisi bulunamadı</div>
      )}
    </div>
  );
}

function InvoiceSection({ detail, onInvoiceAction, onDownloadInvoicePdf }: PaymentTabProps) {
  const inv = detail.invoice!;
  const statusColor =
    inv.invoice_status === "PDF_READY" ? "text-emerald-700" :
      inv.invoice_status === "FAILED" ? "text-red-600" :
        inv.invoice_status === "CANCELLED" ? "text-slate-500" :
          "text-amber-600";
  const emailColor =
    inv.email_status === "SENT" ? "text-emerald-700" :
      inv.email_status === "FAILED" ? "text-red-600" :
        inv.email_status === "SKIPPED" ? "text-amber-600" :
          "text-slate-500";

  return (
    <div className="space-y-3 rounded-lg border bg-emerald-50 p-3">
      <p className="text-xs font-semibold text-slate-700">Fatura Durumu</p>

      <div className="grid grid-cols-2 gap-1 text-xs">
        <span className="text-slate-500">Fatura No:</span>
        <span className="font-medium">{inv.invoice_number}</span>
        <span className="text-slate-500">Durum:</span>
        <span className={`font-medium ${statusColor}`}>{inv.invoice_status}</span>
        {inv.issued_at && (
          <>
            <span className="text-slate-500">Tarih:</span>
            <span className="font-medium">{new Date(inv.issued_at).toLocaleDateString("tr-TR")}</span>
          </>
        )}
        {inv.last_error && (
          <>
            <span className="text-slate-500">Hata:</span>
            <span className="max-w-[200px] truncate font-medium text-red-500" title={inv.last_error}>{inv.last_error.slice(0, 60)}</span>
          </>
        )}
        <span className="text-slate-500">PDF v:</span>
        <span className="font-medium">{inv.pdf_version} (retry: {inv.retry_count})</span>
      </div>

      {/* PDF actions */}
      <div className="flex gap-1.5">
        {inv.pdf_ready && (
          <button onClick={() => onDownloadInvoicePdf(detail.id, inv.invoice_number)} className="flex-1 rounded bg-emerald-600 px-2 py-1.5 text-xs font-medium text-white hover:bg-emerald-700">
            PDF İndir
          </button>
        )}
        <button onClick={() => onInvoiceAction(detail.id, "regenerate", "POST", "Fatura yeniden oluşturuluyor...")} className="flex-1 rounded bg-blue-600 px-2 py-1.5 text-xs font-medium text-white hover:bg-blue-700">
          Yeniden Oluştur
        </button>
        {inv.invoice_status === "FAILED" && (
          <button onClick={() => onInvoiceAction(detail.id, "retry", "POST", "Fatura tekrar deneniyor...")} className="flex-1 rounded bg-orange-600 px-2 py-1.5 text-xs font-medium text-white hover:bg-orange-700">
            Tekrar Dene
          </button>
        )}
      </div>

      {/* Email status */}
      <div className="border-t pt-2">
        <p className="mb-1.5 text-xs font-semibold text-slate-700">Email Durumu</p>
        <div className="grid grid-cols-2 gap-1 text-xs">
          <span className="text-slate-500">Email:</span>
          <span className={`font-medium ${emailColor}`}>{inv.email_status || "Gönderilmedi"}</span>
          {inv.email_sent_at && (
            <>
              <span className="text-slate-500">Gönderim:</span>
              <span className="font-medium">{new Date(inv.email_sent_at).toLocaleString("tr-TR")}</span>
            </>
          )}
          {inv.email_error && (
            <>
              <span className="text-slate-500">Hata:</span>
              <span className="max-w-[200px] truncate font-medium text-red-500" title={inv.email_error}>{inv.email_error.slice(0, 60)}</span>
            </>
          )}
          {inv.email_resent_count > 0 && (
            <>
              <span className="text-slate-500">Tekrar:</span>
              <span className="font-medium">{inv.email_resent_count}x (retry: {inv.email_retry_count})</span>
            </>
          )}
        </div>
        <div className="mt-2 flex gap-1.5">
          {inv.pdf_ready && (
            <button onClick={() => onInvoiceAction(detail.id, "resend-email", "POST", "Fatura emaili gönderildi")} className="flex-1 rounded bg-violet-600 px-2 py-1.5 text-xs font-medium text-white hover:bg-violet-700">
              Email Gönder
            </button>
          )}
          {inv.pdf_ready && (
            <button onClick={() => onInvoiceAction(detail.id, "revoke-tokens", "POST", "Tokenlar iptal edildi, yeni token oluşturuldu")} className="flex-1 rounded bg-red-600 px-2 py-1.5 text-xs font-medium text-white hover:bg-red-700">
              Token İptal & Yenile
            </button>
          )}
        </div>
      </div>

      {inv.needs_credit_note && (
        <p className="text-xs font-medium text-red-500">İade notu gerekli</p>
      )}
    </div>
  );
}
