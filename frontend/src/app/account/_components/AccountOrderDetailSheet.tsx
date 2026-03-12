"use client";

import React, { useEffect, useCallback } from "react";
import Link from "next/link";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import {
  getOrderDetail,
  API_BASE_URL,
  type OrderDetail,
  type InvoiceSummary,
} from "@/lib/api";
import {
  Truck,
  CheckCircle,
  Download,
  Headphones,
  QrCode,
  ExternalLink,
  FileText,
  Loader2,
  ArrowRight,
} from "lucide-react";

const CARRIER_URLS: Record<string, (tn: string) => string> = {
  yurtici: (tn) =>
    `https://www.yurticikargo.com/tr/online-servisler/gonderi-sorgula?code=${tn}`,
  aras: (tn) =>
    `https://www.araskargo.com.tr/taki.aspx?p_kargo_takip_no=${tn}`,
  mng: (tn) =>
    `https://www.mngkargo.com.tr/gonderi-takip/?gonderino=${tn}`,
  ptt: (tn) =>
    `https://gonderitakip.ptt.gov.tr/Track/Verify?q=${tn}`,
};

const STATUS_ORDER = [
  "DRAFT", "TEXT_APPROVED", "COVER_APPROVED", "PAYMENT_PENDING", "PAID",
  "PROCESSING", "READY_FOR_PRINT", "SHIPPED", "DELIVERED",
];

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("tr-TR", {
    day: "numeric",
    month: "long",
    year: "numeric",
  });
}

async function downloadInvoice(orderId: string, invoiceNumber: string): Promise<void> {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  const res = await fetch(`${API_BASE_URL}/orders/${orderId}/invoice/download`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!res.ok) throw new Error("İndirme başarısız");
  const blob = await res.blob();
  const href = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = href;
  a.download = `fatura_${invoiceNumber}.pdf`;
  a.click();
  URL.revokeObjectURL(href);
}

function InvoiceBlock({
  orderId,
  invoice,
  formatDate,
}: {
  orderId: string;
  invoice: InvoiceSummary;
  formatDate: (iso: string) => string;
}) {
  const [downloading, setDownloading] = React.useState(false);
  const handleDownload = async () => {
    setDownloading(true);
    try {
      await downloadInvoice(orderId, invoice.invoice_number);
    } finally {
      setDownloading(false);
    }
  };
  return (
    <div className="rounded-xl border bg-white p-4">
      <h3 className="mb-2 flex items-center gap-2 text-sm font-semibold text-slate-700">
        <FileText className="h-4 w-4" />
        Fatura
      </h3>
      <p className="text-xs text-slate-600">
        {invoice.invoice_number}
        {invoice.issued_at && ` · ${formatDate(invoice.issued_at)}`}
      </p>
      {invoice.pdf_ready && (
        <Button
          size="sm"
          variant="outline"
          className="mt-2 text-xs"
          onClick={handleDownload}
          disabled={downloading}
        >
          {downloading ? (
            <Loader2 className="mr-1 h-3 w-3 animate-spin" />
          ) : (
            <Download className="mr-1 h-3 w-3" />
          )}
          {downloading ? "İndiriliyor..." : "PDF İndir"}
        </Button>
      )}
    </div>
  );
}

interface AccountOrderDetailSheetProps {
  orderId: string | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function AccountOrderDetailSheet({
  orderId,
  open,
  onOpenChange,
}: AccountOrderDetailSheetProps) {
  const [order, setOrder] = React.useState<OrderDetail | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  const [loading, setLoading] = React.useState(false);

  const loadDetail = useCallback(async () => {
    if (!orderId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await getOrderDetail(orderId, "pages,timeline");
      setOrder(data);
    } catch {
      setOrder(null);
      setError("Sipariş detayları yüklenemedi.");
    } finally {
      setLoading(false);
    }
  }, [orderId]);

  useEffect(() => {
    if (open && orderId) loadDetail();
    else if (!open) { setOrder(null); setError(null); }
  }, [open, orderId, loadDetail]);

  if (!orderId) return null;

  const currentIdx = order ? STATUS_ORDER.indexOf(order.status) : -1;
  const isTerminal = order?.status === "CANCELLED" || order?.status === "REFUNDED";

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-full overflow-y-auto sm:max-w-2xl p-0">
        {loading && !order ? (
          <div className="flex h-full items-center justify-center">
            <div className="flex items-center gap-3">
              <Loader2 className="h-5 w-5 animate-spin text-slate-400" />
              <span className="text-sm text-slate-500">Yükleniyor...</span>
            </div>
          </div>
        ) : error ? (
          <div className="flex h-full flex-col items-center justify-center gap-3 px-6 text-center">
            <p className="text-sm text-slate-600">{error}</p>
            <Button size="sm" variant="outline" onClick={loadDetail}>
              Tekrar Dene
            </Button>
          </div>
        ) : order ? (
          <div className="flex h-full flex-col">
            <SheetHeader className="border-b px-6 py-4">
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0 flex-1">
                  <SheetTitle className="truncate text-lg text-slate-800">
                    {order.child_name}
                  </SheetTitle>
                  <SheetDescription className="mt-0.5 text-slate-500">
                    Sipariş #{order.id.slice(0, 8).toUpperCase()}
                    {" · "}
                    {formatDate(order.created_at)}
                    {order.payment_amount != null && order.payment_amount > 0 && (
                      <span className="ml-2 font-medium text-slate-700">
                        {order.payment_amount.toFixed(2)} TL
                      </span>
                    )}
                  </SheetDescription>
                </div>
              </div>

              {/* Status banner */}
              {!isTerminal && (
                <div className="mt-3 rounded-xl border border-purple-100 bg-purple-50/50 p-3">
                  <p className="text-sm font-semibold text-purple-900">
                    {order.status_description}
                  </p>
                  {order.status_hint && (
                    <p className="mt-0.5 text-xs text-purple-700">
                      {order.status_hint}
                    </p>
                  )}
                </div>
              )}
            </SheetHeader>

            <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
              {/* Timeline stepper */}
              {!isTerminal && currentIdx >= STATUS_ORDER.indexOf("PAID") && (
                <div className="rounded-xl border bg-white p-4">
                  <h3 className="mb-3 text-sm font-semibold text-slate-700">Sipariş Durumu</h3>
                  <div className="flex items-center justify-between">
                    {["Ödendi", "Üretiliyor", "Baskıya Hazır", "Kargoda", "Teslim Edildi"].map((label, i) => {
                      const stepIdx = STATUS_ORDER.indexOf(["PAID", "PROCESSING", "READY_FOR_PRINT", "SHIPPED", "DELIVERED"][i]);
                      const done = currentIdx >= stepIdx;
                      const active = order.status === (["PAID", "PROCESSING", "READY_FOR_PRINT", "SHIPPED", "DELIVERED"][i]);
                      return (
                        <div key={label} className="flex flex-1 flex-col items-center">
                          <div
                            className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-xs font-bold ${
                              done ? "bg-purple-600 text-white" : "bg-slate-200 text-slate-400"
                            } ${active ? "ring-2 ring-purple-200" : ""}`}
                          >
                            {done ? <CheckCircle className="h-4 w-4" /> : i + 1}
                          </div>
                          <span className={`mt-1.5 text-center text-[10px] ${done ? "text-purple-600" : "text-slate-400"}`}>
                            {label}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Page images preview */}
              {order.pages && order.pages.length > 0 && (
                <div className="rounded-xl border bg-white p-4">
                  <h3 className="mb-3 text-sm font-semibold text-slate-700">Kitap Önizleme</h3>
                  <div className="flex gap-2 overflow-x-auto pb-2">
                    {order.pages.map((p) => {
                      const url = p.image_url || p.preview_image_url;
                      if (!url) return null;
                      return (
                        <div key={p.page_number} className="flex shrink-0 flex-col items-center">
                          <img
                            src={url}
                            alt={`Sayfa ${p.page_number}`}
                            className="h-20 w-auto rounded-lg border object-cover"
                          />
                          <span className="mt-1 text-[10px] text-slate-500">
                            {p.is_cover ? "Kapak" : p.page_number}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Production progress */}
              {order.status === "PROCESSING" && (
                <div className="rounded-xl border bg-white p-4">
                  <h3 className="mb-2 flex items-center gap-2 text-sm font-semibold text-slate-700">
                    <Loader2 className="h-4 w-4" />
                    Üretim İlerlemesi
                  </h3>
                  <div className="flex justify-between text-xs text-slate-600">
                    <span>{order.completed_pages} / {order.total_pages} sayfa</span>
                    <span className="font-semibold text-purple-600">
                      {order.total_pages > 0 ? Math.round((order.completed_pages / order.total_pages) * 100) : 0}%
                    </span>
                  </div>
                  <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-slate-100">
                    <div
                      className="h-full rounded-full bg-purple-500 transition-all"
                      style={{
                        width: `${order.total_pages > 0 ? (order.completed_pages / order.total_pages) * 100 : 0}%`,
                      }}
                    />
                  </div>
                </div>
              )}

              {/* Cargo tracking */}
              {order.tracking_number && (
                <div className="rounded-xl border bg-white p-4">
                  <h3 className="mb-2 flex items-center gap-2 text-sm font-semibold text-slate-700">
                    <Truck className="h-4 w-4" />
                    Kargo Takibi
                  </h3>
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <p className="text-sm font-medium text-slate-800">{order.carrier || "Kargo"}</p>
                      <p className="text-xs text-slate-500">{order.tracking_number}</p>
                    </div>
                    {order.carrier && CARRIER_URLS[(order.carrier || "").toLowerCase()] && (
                      <a
                        href={CARRIER_URLS[(order.carrier || "").toLowerCase()]!(order.tracking_number!)}
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        <Button size="sm" variant="outline" className="text-xs">
                          Takip Et
                          <ExternalLink className="ml-1 h-3 w-3" />
                        </Button>
                      </a>
                    )}
                  </div>
                </div>
              )}

              {/* Digital downloads */}
              {(order.final_pdf_url || order.audio_file_url || order.qr_code_url) && (
                <div className="rounded-xl border bg-white p-4">
                  <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-slate-700">
                    <Download className="h-4 w-4" />
                    Dijital İçerikler
                  </h3>
                  <div className="grid gap-2 sm:grid-cols-3">
                    {order.final_pdf_url && (
                      <a
                        href={order.final_pdf_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-2 rounded-lg border p-3 text-sm font-medium text-slate-700 hover:bg-slate-50"
                      >
                        <Download className="h-4 w-4 text-green-600" />
                        PDF İndir
                      </a>
                    )}
                    {order.audio_file_url && (
                      <a
                        href={order.audio_file_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-2 rounded-lg border p-3 text-sm font-medium text-slate-700 hover:bg-slate-50"
                      >
                        <Headphones className="h-4 w-4 text-blue-600" />
                        Sesli Kitap
                      </a>
                    )}
                    {order.qr_code_url && (
                      <a
                        href={order.qr_code_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-2 rounded-lg border p-3 text-sm font-medium text-slate-700 hover:bg-slate-50"
                      >
                        <QrCode className="h-4 w-4 text-purple-600" />
                        QR Kod
                      </a>
                    )}
                  </div>
                </div>
              )}

              {/* Invoice */}
              {order.invoice && (
                <InvoiceBlock orderId={order.id} invoice={order.invoice} formatDate={formatDate} />
              )}

              {/* Shipping address */}
              {order.shipping_address && (
                <div className="rounded-xl border bg-white p-4">
                  <h3 className="mb-2 flex items-center gap-2 text-sm font-semibold text-slate-700">
                    <Truck className="h-4 w-4" />
                    Teslimat Adresi
                  </h3>
                  <p className="text-sm text-slate-600">
                    {order.shipping_address.full_name}
                    <br />
                    {order.shipping_address.address_line1}
                    {order.shipping_address.address_line2 && (
                      <><br />{order.shipping_address.address_line2}</>
                    )}
                    <br />
                    {order.shipping_address.district && `${order.shipping_address.district}, `}
                    {order.shipping_address.city}
                    {order.shipping_address.postal_code && ` ${order.shipping_address.postal_code}`}
                  </p>
                </div>
              )}

              {/* Link to full detail page */}
              <Link href={`/account/orders/${order.id}`}>
                <Button variant="outline" className="w-full rounded-xl">
                  Tam Detay Görüntüle
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              </Link>
            </div>
          </div>
        ) : null}
      </SheetContent>
    </Sheet>
  );
}
