"use client";

import React from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import type { OrderDetail } from "../_lib/types";
import { LazyImage } from "./LazyImage";

interface ImageGalleryDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  detail: OrderDetail;
  onDownloadSingle: (url: string, filename: string) => void;
  onDownloadAll: () => void;
  zipDownloading: boolean;
}

export function ImageGalleryDialog({
  open,
  onOpenChange,
  detail,
  onDownloadSingle,
  onDownloadAll,
  zipDownloading,
}: ImageGalleryDialogProps) {
  const pageImages = detail.page_images ?? {};
  const entries = Object.entries(pageImages).sort(([a], [b]) => {
    const order = (k: string) => {
      if (k === "dedication") return -2;
      if (k === "intro") return -1;
      return parseInt(k) || 0;
    };
    return order(a) - order(b);
  });

  const isLandscape = detail.product_name?.includes("Yatay");
  const aspectRatio = isLandscape ? "aspect-[297/210]" : detail.product_name?.includes("Kare") ? "aspect-square" : "aspect-[210/297]";

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[90vh] max-w-5xl overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center justify-between">
            <span>Görsel Galeri — {detail.child_name}</span>
            <Button
              size="sm"
              variant="outline"
              disabled={zipDownloading}
              onClick={onDownloadAll}
              className="text-xs"
            >
              {zipDownloading ? "İndiriliyor..." : "Tümünü ZIP İndir"}
            </Button>
          </DialogTitle>
        </DialogHeader>

        <div className="grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-4">
          {entries.map(([pageKey, url]) => {
            const isDedication = pageKey === "dedication";
            const isIntro = pageKey === "intro";
            const label = isDedication ? "Karşılama 1" :
              isIntro ? "Karşılama 2" :
              `Sayfa ${parseInt(pageKey) + 1}`;
            const filename = isDedication ? "karsilama_1" :
              isIntro ? "karsilama_2" :
              `sayfa_${parseInt(pageKey) + 1}`;

            return (
              <div key={pageKey} className="overflow-hidden rounded-lg border">
                <div className="flex items-center justify-between bg-slate-50 px-2 py-1">
                  <span className="text-[10px] font-medium text-slate-600">{label}</span>
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => onDownloadSingle(url, `${detail.child_name || "kitap"}_${filename}.jpg`)}
                      className="rounded bg-violet-600 px-1 py-0.5 text-[9px] font-medium text-white hover:bg-violet-700"
                    >
                      İndir
                    </button>
                    <a href={url} target="_blank" rel="noopener noreferrer" className="text-[9px] text-blue-600 hover:underline">
                      Tam
                    </a>
                  </div>
                </div>
                <LazyImage src={url} alt={label} className={`w-full ${aspectRatio}`} />
              </div>
            );
          })}

          {/* Back cover */}
          {detail.back_cover_image_url && (
            <div className="overflow-hidden rounded-lg border border-violet-300">
              <div className="flex items-center justify-between bg-violet-50 px-2 py-1">
                <span className="text-[10px] font-medium text-violet-700">Arka Kapak</span>
                <button
                  onClick={() => onDownloadSingle(detail.back_cover_image_url!, `${detail.child_name || "kitap"}_arka_kapak.jpg`)}
                  className="rounded bg-violet-600 px-1 py-0.5 text-[9px] font-medium text-white hover:bg-violet-700"
                >
                  İndir
                </button>
              </div>
              <LazyImage src={detail.back_cover_image_url} alt="Arka Kapak" className="w-full aspect-[297/210]" />
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
