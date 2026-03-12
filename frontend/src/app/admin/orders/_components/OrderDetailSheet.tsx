"use client";

import React from "react";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from "@/components/ui/sheet";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import type { OrderDetail, BackCoverConfig } from "../_lib/types";
import { StatusBadge } from "./StatusBadge";
import { GeneralTab } from "./tabs/GeneralTab";
import { PaymentTab } from "./tabs/PaymentTab";
import { ProductionTab } from "./tabs/ProductionTab";
import { ShippingTab } from "./tabs/ShippingTab";
import { NotesTab } from "./tabs/NotesTab";

interface OrderDetailSheetProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  detail: OrderDetail | null;
  loading: boolean;
  backCoverConfig: BackCoverConfig | null;
  // Actions
  onUpdateStatus: (id: string, status: string) => void;
  onGenerateBook: (id: string) => void;
  onDownloadPdf: () => void;
  onColoringBook: (id: string, url?: string | null) => void;
  onInvoiceAction: (orderId: string, action: string, method?: string, successMsg?: string) => void;
  onDownloadInvoicePdf: (orderId: string, invoiceNumber: string) => void;
  onCreateInvoice?: (orderId: string) => void;
  onGenerateRemaining: (id: string, count: number) => void;
  onRecompose: (id: string) => void;
  onDownloadSingleImage: (url: string, filename: string) => void;
  onDownloadAllImages: () => void;
  pdfDownloading: boolean;
  zipDownloading: boolean;
  bookGenerating: boolean;
  coloringGenerating: boolean;
}

export function OrderDetailSheet({
  open,
  onOpenChange,
  detail,
  loading,
  backCoverConfig,
  onUpdateStatus,
  onGenerateBook,
  onDownloadPdf,
  onColoringBook,
  onInvoiceAction,
  onDownloadInvoicePdf,
  onCreateInvoice,
  onGenerateRemaining,
  onRecompose,
  onDownloadSingleImage,
  onDownloadAllImages,
  pdfDownloading,
  zipDownloading,
  bookGenerating,
  coloringGenerating,
}: OrderDetailSheetProps) {
  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-full overflow-y-auto sm:max-w-2xl p-0">
        {loading && !detail ? (
          <div className="flex h-full items-center justify-center">
            <div className="flex items-center gap-3">
              <div className="h-5 w-5 animate-spin rounded-full border-2 border-slate-300 border-t-violet-500" />
              <span className="text-sm text-slate-500">Yükleniyor...</span>
            </div>
          </div>
        ) : detail ? (
          <div className="flex h-full flex-col">
            {/* Header */}
            <SheetHeader className="border-b px-6 py-4">
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0 flex-1">
                  <SheetTitle className="truncate text-lg">
                    {detail.story_title}
                  </SheetTitle>
                  <SheetDescription className="mt-0.5">
                    {detail.child_name} — {detail.story_pages?.length || 0} sayfa
                    <span className="ml-2 font-mono text-[10px] text-slate-400">{detail.id.slice(0, 8)}</span>
                  </SheetDescription>
                </div>
                <div className="flex flex-shrink-0 items-center gap-2">
                  {detail.has_coloring_book && (
                    <span className="rounded bg-pink-100 px-2 py-0.5 text-[10px] font-semibold text-pink-700">Boyama</span>
                  )}
                  {(() => {
                    const manifest = detail.generation_manifest_json;
                    const anyMissingRef = manifest && Object.values(manifest).some((m) => m?.reference_image_used === false);
                    return anyMissingRef ? (
                      <span className="rounded-full bg-amber-100 px-2 py-0.5 text-[10px] font-medium text-amber-800" title="Referans (PuLID) kullanılmadı">
                        Ref yok
                      </span>
                    ) : null;
                  })()}
                  <StatusBadge status={detail.status} size="md" />
                </div>
              </div>

              {/* "What's happening now?" box */}
              <StatusExplainer status={detail.status} />
            </SheetHeader>

            {/* Tabs */}
            <div className="flex-1 overflow-y-auto px-6 py-4">
              <Tabs defaultValue="general" className="w-full">
                <TabsList className="mb-4 w-full">
                  <TabsTrigger value="general" className="flex-1 text-xs">Genel</TabsTrigger>
                  <TabsTrigger value="payment" className="flex-1 text-xs">Ödeme</TabsTrigger>
                  <TabsTrigger value="production" className="flex-1 text-xs">Üretim</TabsTrigger>
                  <TabsTrigger value="shipping" className="flex-1 text-xs">Kargo</TabsTrigger>
                  <TabsTrigger value="notes" className="flex-1 text-xs">Notlar</TabsTrigger>
                </TabsList>

                <TabsContent value="general">
                  <GeneralTab
                    detail={detail}
                    onUpdateStatus={onUpdateStatus}
                    onGenerateBook={onGenerateBook}
                    onDownloadPdf={onDownloadPdf}
                    onColoringBook={onColoringBook}
                    pdfDownloading={pdfDownloading}
                    bookGenerating={bookGenerating}
                    coloringGenerating={coloringGenerating}
                  />
                </TabsContent>

                <TabsContent value="payment">
                  <PaymentTab
                    detail={detail}
                    onInvoiceAction={onInvoiceAction}
                    onDownloadInvoicePdf={onDownloadInvoicePdf}
                    onCreateInvoice={onCreateInvoice}
                  />
                </TabsContent>

                <TabsContent value="production">
                  <ProductionTab
                    detail={detail}
                    onGenerateRemaining={onGenerateRemaining}
                    onRecompose={onRecompose}
                    onDownloadSingleImage={onDownloadSingleImage}
                    onDownloadAllImages={onDownloadAllImages}
                    zipDownloading={zipDownloading}
                    backCoverConfig={backCoverConfig}
                  />
                </TabsContent>

                <TabsContent value="shipping">
                  <ShippingTab
                    detail={detail}
                    onDownloadPdf={onDownloadPdf}
                    pdfDownloading={pdfDownloading}
                  />
                </TabsContent>

                <TabsContent value="notes">
                  <NotesTab detail={detail} />
                </TabsContent>
              </Tabs>
            </div>
          </div>
        ) : null}
      </SheetContent>
    </Sheet>
  );
}

function StatusExplainer({ status }: { status: string }) {
  const explanations: Record<string, { text: string; next: string; color: string }> = {
    PENDING: { text: "Sipariş onay bekliyor.", next: "Onayla veya iptal et.", color: "bg-amber-50 border-amber-200 text-amber-800" },
    CONFIRMED: { text: "Sipariş onaylandı, üretim bekliyor.", next: "Kitap üretimini başlat.", color: "bg-emerald-50 border-emerald-200 text-emerald-800" },
    PROCESSING: { text: "Görseller arka planda üretiliyor.", next: "Otomatik tamamlanacak.", color: "bg-blue-50 border-blue-200 text-blue-800" },
    FAILED: { text: "Üretim sırasında hata oluştu.", next: "Hata detayını incele ve tekrar dene.", color: "bg-red-50 border-red-200 text-red-800" },
    QUEUE_FAILED: { text: "Kuyruk hatası oluştu.", next: "Tekrar kuyruğa ekle.", color: "bg-orange-50 border-orange-200 text-orange-800" },
    EXPIRED: { text: "Sipariş süresi doldu.", next: "İşlem yapılamaz.", color: "bg-slate-50 border-slate-200 text-slate-600" },
    CANCELLED: { text: "Sipariş iptal edildi.", next: "İşlem yapılamaz.", color: "bg-slate-50 border-slate-200 text-slate-600" },
  };

  const info = explanations[status];
  if (!info) return null;

  return (
    <div className={`mt-3 rounded-lg border p-2.5 ${info.color}`}>
      <p className="text-xs font-medium">{info.text}</p>
      <p className="text-[10px] opacity-80">Sonraki adım: {info.next}</p>
    </div>
  );
}
