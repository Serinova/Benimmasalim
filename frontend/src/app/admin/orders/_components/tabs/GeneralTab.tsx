"use client";

import React from "react";
import { Button } from "@/components/ui/button";
import { Loader2 } from "lucide-react";
import type { OrderDetail } from "../../_lib/types";

interface GeneralTabProps {
  detail: OrderDetail;
  onUpdateStatus: (id: string, status: string) => void;
  onGenerateBook: (id: string) => void;
  onDownloadPdf: () => void;
  onColoringBook: (id: string, url?: string | null) => void;
  pdfDownloading: boolean;
  bookGenerating: boolean;
  coloringGenerating: boolean;
}

export function GeneralTab({
  detail,
  onUpdateStatus,
  onGenerateBook,
  onDownloadPdf,
  onColoringBook,
  pdfDownloading,
  bookGenerating,
  coloringGenerating,
}: GeneralTabProps) {
  return (
    <div className="space-y-4">
      {/* FAILED error banner */}
      {detail.status === "FAILED" && (
        <div className="rounded-lg border-2 border-red-300 bg-red-50 p-3">
          <p className="text-sm font-semibold text-red-800">Arka plan işlemi başarısız</p>
          <p className="mt-1 whitespace-pre-wrap font-mono text-xs text-red-700">
            {detail.admin_notes || "Hata mesajı kaydedilmemiş."}
          </p>
        </div>
      )}

      {/* PROCESSING info */}
      {detail.status === "PROCESSING" && (
        <div className="rounded-lg border border-blue-200 bg-blue-50 p-3">
          <p className="text-sm text-blue-800">
            Görseller arka planda üretiliyor. Birkaç dakika sonra sayfayı yenileyin.
          </p>
        </div>
      )}

      {/* Quick info grid */}
      <div className="grid grid-cols-2 gap-3">
        <InfoCard label="Ebeveyn" primary={detail.parent_name} secondary={detail.parent_email} extra={detail.parent_phone} bg="bg-white" />
        <InfoCard
          label="Çocuk"
          primary={`${detail.child_name} (${detail.child_age} yaş)`}
          secondary={detail.child_gender === "erkek" ? "Erkek" : detail.child_gender === "kiz" ? "Kız" : undefined}
          bg="bg-blue-50"
        />
        <InfoCard
          label="Ürün"
          primary={detail.product_name || "—"}
          secondary={detail.product_price ? `${detail.product_price} TL` : undefined}
          bg="bg-violet-50"
          secondaryClass="text-sm font-bold text-violet-600"
        />
        <InfoCard
          label="Senaryo & Stil"
          primary={detail.scenario_name || "—"}
          secondary={detail.visual_style_name || undefined}
          bg="bg-emerald-50"
        />
      </div>

      {/* Actions */}
      <div className="flex flex-wrap gap-2 border-t border-b py-3">
        {detail.status === "PENDING" && (
          <>
            <Button size="sm" className="bg-emerald-600 hover:bg-emerald-700" onClick={() => onUpdateStatus(detail.id, "CONFIRMED")}>
              Onayla
            </Button>
            <Button size="sm" variant="destructive" onClick={() => onUpdateStatus(detail.id, "CANCELLED")}>
              İptal Et
            </Button>
          </>
        )}
        {detail.status === "CONFIRMED" && (
          <>
            <Button size="sm" className="bg-emerald-600 hover:bg-emerald-700" disabled={bookGenerating} onClick={() => onGenerateBook(detail.id)}>
              {bookGenerating && <Loader2 className="mr-1.5 h-3.5 w-3.5 animate-spin" />}
              {bookGenerating
                ? "Üretiliyor..."
                : detail.has_audio_book ? "Kitap + Ses Üret" : "Kitap Üret"}
            </Button>
            <Button size="sm" className="bg-blue-600 hover:bg-blue-700" disabled={pdfDownloading} onClick={onDownloadPdf}>
              {pdfDownloading ? "PDF Hazırlanıyor..." : "PDF İndir"}
            </Button>
            <Button size="sm" variant="outline" onClick={() => window.print()}>
              Yazdır
            </Button>
          </>
        )}
        {detail.has_coloring_book && (
          <Button
            size="sm"
            className="bg-pink-600 hover:bg-pink-700"
            disabled={coloringGenerating}
            onClick={() => onColoringBook(detail.id, detail.coloring_pdf_url)}
          >
            {coloringGenerating && <Loader2 className="mr-1.5 h-3.5 w-3.5 animate-spin" />}
            {coloringGenerating
              ? "Üretiliyor..."
              : `Boyama PDF ${detail.coloring_pdf_url ? "İndir" : "Üret"}`}
          </Button>
        )}
      </div>

      {/* Audio */}
      {detail.has_audio_book && (
        <div className="flex gap-3">
          <div className="w-40 flex-shrink-0 rounded-lg bg-indigo-50 p-3">
            <p className="text-[10px] font-medium text-slate-500">Sesli Kitap</p>
            <p className="text-xs font-medium text-indigo-700">
              {detail.audio_type === "cloned" ? "Klonlanmış" : "Sistem"}
            </p>
          </div>
        </div>
      )}

      {/* Timestamps */}
      <div className="space-y-1 border-t pt-3 text-xs text-slate-500">
        <p>Oluşturulma: {new Date(detail.created_at).toLocaleString("tr-TR")}</p>
        {detail.confirmed_at && (
          <p className="text-emerald-600">Onaylanma: {new Date(detail.confirmed_at).toLocaleString("tr-TR")}</p>
        )}
      </div>
    </div>
  );
}

function InfoCard({ label, primary, secondary, extra, bg, secondaryClass }: {
  label: string;
  primary: string;
  secondary?: string;
  extra?: string | null;
  bg: string;
  secondaryClass?: string;
}) {
  return (
    <div className={`rounded-lg ${bg} border p-3`}>
      <p className="text-[10px] font-medium text-slate-500">{label}</p>
      <p className="truncate text-xs font-medium text-slate-800">{primary}</p>
      {secondary && <p className={`truncate text-[10px] ${secondaryClass ?? "text-slate-500"}`}>{secondary}</p>}
      {extra && <p className="truncate text-[10px] text-slate-400">{extra}</p>}
    </div>
  );
}
