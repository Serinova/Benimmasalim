"use client";

import React from "react";
import type { OrderDetail } from "../../_lib/types";

interface ShippingTabProps {
  detail: OrderDetail;
  onDownloadPdf: () => void;
  pdfDownloading: boolean;
}

export function ShippingTab({ detail, onDownloadPdf, pdfDownloading }: ShippingTabProps) {
  return (
    <div className="space-y-4">
      {/* PDF section */}
      <div className="rounded-lg border bg-white p-3">
        <p className="mb-2 text-xs font-semibold text-slate-700">Kitap PDF</p>
        {detail.pdf_url ? (
          <div className="flex items-center gap-3">
            <span className="rounded bg-emerald-100 px-2 py-0.5 text-xs font-medium text-emerald-700">Hazır</span>
            <button
              onClick={onDownloadPdf}
              disabled={pdfDownloading}
              className="rounded bg-blue-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {pdfDownloading ? "İndiriliyor..." : "PDF İndir"}
            </button>
            <a href={detail.pdf_url} target="_blank" rel="noopener noreferrer" className="text-xs text-blue-600 hover:underline">
              Yeni sekmede aç
            </a>
          </div>
        ) : (
          <p className="text-xs text-slate-400">PDF henüz oluşturulmadı</p>
        )}
      </div>

      {/* Coloring book PDF */}
      {detail.has_coloring_book && (
        <div className="rounded-lg border bg-white p-3">
          <p className="mb-2 text-xs font-semibold text-slate-700">Boyama Kitabı PDF</p>
          {detail.coloring_pdf_url ? (
            <div className="flex items-center gap-3">
              <span className="rounded bg-pink-100 px-2 py-0.5 text-xs font-medium text-pink-700">Hazır</span>
              <a href={detail.coloring_pdf_url} target="_blank" rel="noopener noreferrer" className="rounded bg-pink-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-pink-700">
                PDF İndir
              </a>
            </div>
          ) : (
            <p className="text-xs text-slate-400">Boyama kitabı henüz oluşturulmadı</p>
          )}
        </div>
      )}

      {/* Shipping placeholder */}
      <div className="rounded-lg border bg-white p-3">
        <p className="mb-2 text-xs font-semibold text-slate-700">Kargo Bilgileri</p>
        <p className="text-xs text-slate-400">Kargo bilgisi henüz eklenmedi</p>
      </div>
    </div>
  );
}
