"use client";

import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import type { OrderDetail, StoryPageContent } from "../../_lib/types";
import { LazyImage } from "../LazyImage";
import { ImageGalleryDialog } from "../ImageGalleryDialog";

interface ProductionTabProps {
  detail: OrderDetail;
  onGenerateRemaining: (id: string, count: number) => void;
  onRecompose: (id: string) => void;
  onDownloadSingleImage: (url: string, filename: string) => void;
  onDownloadAllImages: () => void;
  zipDownloading: boolean;
  backCoverConfig: {
    company_name: string;
    tagline: string;
    tips_title: string;
    tips_content: string;
    copyright_text: string;
    background_color: string;
    primary_color: string;
    text_color: string;
    border_color: string;
    qr_enabled: boolean;
    qr_label: string;
    show_border: boolean;
    company_website: string;
    company_email: string;
  } | null;
}

export function ProductionTab({
  detail,
  onGenerateRemaining,
  onRecompose,
  onDownloadSingleImage,
  onDownloadAllImages,
  zipDownloading,
  backCoverConfig,
}: ProductionTabProps) {
  const [galleryOpen, setGalleryOpen] = useState(false);

  const pageImages = detail.page_images ?? {};
  const imageCount = Object.keys(pageImages).length;
  const numericKeys = Object.keys(pageImages).filter((k) => /^\d+$/.test(k));
  const totalPages = detail.story_pages?.length || 0;
  const missingCount = totalPages - numericKeys.length;

  const pageImageUrl = (pageKey: string): string => {
    return pageImages[pageKey] || pageImages[String(pageKey)] || "";
  };

  return (
    <div className="space-y-4">
      {/* Summary bar */}
      <div className="flex items-center justify-between rounded-lg border bg-slate-50 p-3">
        <div>
          <p className="text-xs font-medium text-slate-700">
            {imageCount} / {totalPages} görsel hazır
          </p>
          {missingCount > 0 && (
            <p className="text-[10px] text-red-500">{missingCount} eksik sayfa</p>
          )}
        </div>
        <div className="flex gap-2">
          {missingCount > 0 && (
            <Button
              size="sm"
              variant="destructive"
              className="h-7 text-xs"
              onClick={() => onGenerateRemaining(detail.id, missingCount)}
            >
              {missingCount} Eksik Sayfa Oluştur
            </Button>
          )}
          <Button
            size="sm"
            variant="outline"
            className="h-7 text-xs"
            onClick={() => onRecompose(detail.id)}
          >
            Yeniden Compose Et
          </Button>
          {imageCount > 0 && (
            <Button
              size="sm"
              variant="outline"
              className="h-7 text-xs"
              disabled={zipDownloading}
              onClick={onDownloadAllImages}
            >
              {zipDownloading ? "İndiriliyor..." : "ZIP İndir"}
            </Button>
          )}
        </div>
      </div>

      {/* Print info */}
      <div className="rounded-lg border border-blue-200 bg-blue-50 p-2.5">
        <div className="flex items-center justify-between text-xs">
          <span className="font-medium text-blue-800">
            Baskı: {detail.product_name?.includes("Yatay") ? "Yatay A4" :
              detail.product_name?.includes("Kare") ? "Kare 210×210" :
              detail.product_name?.includes("Cep") ? "Cep Boy" : "A4"}
          </span>
          <span className="text-blue-500">Bleed: 3mm</span>
        </div>
      </div>

      {/* Page grid — shows images inline */}
      {totalPages > 0 || imageCount > 0 ? (
        <>
          <div className="grid grid-cols-3 gap-2">
            {/* Dedication */}
            {pageImages["dedication"] && (
              <PageThumb
                pageKey="dedication"
                label="Karşılama 1"
                url={pageImages["dedication"]}
                detail={detail}
                onDownload={onDownloadSingleImage}
              />
            )}
            {/* Intro */}
            {pageImages["intro"] && (
              <PageThumb
                pageKey="intro"
                label="Karşılama 2"
                url={pageImages["intro"]}
                detail={detail}
                onDownload={onDownloadSingleImage}
              />
            )}
            {/* Story pages */}
            {detail.story_pages?.map((page: StoryPageContent, idx: number) => {
              const url = pageImageUrl(idx.toString());
              return (
                <PageThumb
                  key={idx}
                  pageKey={String(idx)}
                  label={idx === 0 ? "0 (Kapak)" : `${idx}`}
                  url={url}
                  detail={detail}
                  text={page.text}
                  onDownload={onDownloadSingleImage}
                />
              );
            })}
          </div>

          {/* Back cover */}
          {(detail.back_cover_image_url || backCoverConfig) && (
            <div className="rounded-lg border bg-white">
              <div className="flex items-center justify-between bg-violet-50 px-3 py-2">
                <span className="text-xs font-medium text-violet-800">Arka Kapak</span>
                {detail.back_cover_image_url && (
                  <button
                    onClick={() => onDownloadSingleImage(detail.back_cover_image_url!, `${detail.child_name || "kitap"}_arka_kapak.jpg`)}
                    className="rounded bg-violet-600 px-1.5 py-0.5 text-[10px] font-medium text-white hover:bg-violet-700"
                  >
                    İndir
                  </button>
                )}
              </div>
              {detail.back_cover_image_url ? (
                <div className="p-2">
                  <LazyImage src={detail.back_cover_image_url} alt="Arka Kapak" className="w-full rounded border aspect-[297/210]" />
                </div>
              ) : backCoverConfig && (
                <div className="p-3" style={{ backgroundColor: backCoverConfig.background_color }}>
                  <div className="rounded-lg p-3" style={{ border: backCoverConfig.show_border ? `2px solid ${backCoverConfig.border_color}` : "none" }}>
                    <div className="mb-2 text-center">
                      <h3 className="text-sm font-bold" style={{ color: backCoverConfig.primary_color }}>{backCoverConfig.company_name}</h3>
                      <p className="text-xs italic" style={{ color: backCoverConfig.text_color }}>{backCoverConfig.tagline}</p>
                    </div>
                    <p className="text-center text-xs italic" style={{ color: backCoverConfig.primary_color }}>
                      Bu kitap {detail.child_name} için özel olarak hazırlandı
                    </p>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Full gallery button */}
          {imageCount > 0 && (
            <Button variant="outline" className="w-full" onClick={() => setGalleryOpen(true)}>
              Tam Ekran Galeri ({imageCount} görsel)
            </Button>
          )}

          <ImageGalleryDialog
            open={galleryOpen}
            onOpenChange={setGalleryOpen}
            detail={detail}
            onDownloadSingle={onDownloadSingleImage}
            onDownloadAll={onDownloadAllImages}
            zipDownloading={zipDownloading}
          />
        </>
      ) : (
        <div className="py-8 text-center text-sm text-slate-400">Henüz sayfa görseli yok</div>
      )}
    </div>
  );
}

function PageThumb({ pageKey, label, url, detail, text, onDownload }: {
  pageKey: string;
  label: string;
  url: string;
  detail: OrderDetail;
  text?: string;
  onDownload: (url: string, filename: string) => void;
}) {
  const isLandscape = detail.product_name?.includes("Yatay");
  const aspectRatio = isLandscape ? "aspect-[297/210]" : detail.product_name?.includes("Kare") ? "aspect-square" : "aspect-[210/297]";

  return (
    <div className="overflow-hidden rounded-lg border bg-white">
      <div className="flex items-center justify-between bg-slate-50 px-2 py-1">
        <span className="text-[10px] font-medium text-slate-600">{label}</span>
        <div className="flex items-center gap-1">
          {url && (
            <>
              <button
                onClick={(e) => { e.stopPropagation(); onDownload(url, `${detail.child_name || "kitap"}_${pageKey}.jpg`); }}
                className="rounded bg-violet-600 px-1 py-0.5 text-[9px] font-medium text-white hover:bg-violet-700"
              >
                İndir
              </button>
              <a href={url} target="_blank" rel="noopener noreferrer" className="text-[9px] text-blue-600 hover:underline" onClick={(e) => e.stopPropagation()}>
                Tam
              </a>
            </>
          )}
        </div>
      </div>
      <div className="p-1">
        {url ? (
          <LazyImage src={url} alt={label} className={`w-full rounded ${aspectRatio}`} />
        ) : (
          <div className={`flex items-center justify-center rounded bg-slate-100 ${aspectRatio}`}>
            <span className="text-[10px] text-slate-400">Görsel yok</span>
          </div>
        )}
        {text && (
          <p className="mt-1 line-clamp-2 px-1 text-[10px] text-slate-500">{text}</p>
        )}
      </div>
    </div>
  );
}
