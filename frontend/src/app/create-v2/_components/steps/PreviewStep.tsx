"use client";

import { useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import Image from "next/image";
import {
  BookOpen,
  ChevronLeft,
  ChevronRight,
  RefreshCw,
  AlertTriangle,
} from "lucide-react";
import GenerationWaitingModal from "../ui/GenerationWaitingModal";
import StickyCTA from "../StickyCTA";
import type { GenerationProgress } from "@/lib/api";

/* ── Props ── */
interface PreviewStepProps {
  childName: string;
  previewImages: Record<string, string>;
  backCoverImageUrl?: string | null;
  isLoading: boolean;
  generationProgress?: GenerationProgress | null;
  errorMessage?: string | null;
  onApprove: () => void;
  onBack: () => void;
  onRetry?: () => void;
}

/* ── Main Component ── */
export default function PreviewStep({
  childName,
  previewImages,
  isLoading,
  generationProgress,
  errorMessage,
  onApprove,
  onBack,
  onRetry,
}: PreviewStepProps) {
  const [currentIdx, setCurrentIdx] = useState(0);

  /* Prepare sorted pages */
  const imageEntries = Object.entries(previewImages)
    .filter(([, url]) => !!url)
    .sort(([a], [b]) => {
      // Priority: cover(0) → page0(1) → dedication(2) → intro(3) → numbered pages(100+n) → backcover(999)
      const priority = (key: string): number => {
        if (key === "cover") return 0;
        if (key === "0" || key === "page_0" || key === "page0") return 1;
        if (key === "dedication") return 2;
        if (key === "intro") return 3;
        if (key === "backcover") return 999;
        const num = parseInt(key.replace(/\D/g, ""), 10);
        return isNaN(num) ? 500 : 100 + num;
      };
      return priority(a) - priority(b);
    });

  const hasImages = imageEntries.length > 0;
  const totalPages = imageEntries.length;
  const safeIdx = Math.min(currentIdx, totalPages - 1);

  /* Navigation */
  const goNext = useCallback(() => {
    setCurrentIdx(prev => Math.min(prev + 1, totalPages - 1));
  }, [totalPages]);

  const goPrev = useCallback(() => {
    setCurrentIdx(prev => Math.max(prev - 1, 0));
  }, []);

  /* Page label */
  const getPageLabel = (key: string) => {
    if (key === "cover") return "Kapak";
    if (key === "0" || key === "page_0" || key === "page0") return "Kapak";
    if (key === "dedication") return "Karşılama Sayfası";
    if (key === "backcover") return "Arka Kapak";
    if (key === "intro") return "Giriş Sayfası";
    const num = key.replace(/\D/g, "");
    return num ? `Sayfa ${num}` : key;
  };

  /* ── LOADING STATE ── */
  if (isLoading) {
    return (
      <GenerationWaitingModal
        progress={generationProgress}
        isVisible={true}
      />
    );
  }

  /* ── ERROR STATE ── */
  if (errorMessage && !hasImages) {
    return (
      <div className="pb-24 space-y-5">
        <div className="flex flex-col items-center justify-center py-16 px-4">
          <div className="mb-5 flex h-16 w-16 items-center justify-center rounded-2xl bg-red-50 text-red-500">
            <AlertTriangle className="h-8 w-8" />
          </div>
          <h2 className="text-lg font-bold text-slate-800 mb-2 text-center">
            Bir Sorun Oluştu
          </h2>
          <p className="text-sm text-slate-500 text-center max-w-sm mb-6">
            {errorMessage}
          </p>
          {onRetry && (
            <motion.button
              type="button"
              whileTap={{ scale: 0.97 }}
              onClick={onRetry}
              className="inline-flex items-center gap-2 rounded-xl bg-violet-600 px-6 py-3 text-sm font-bold text-white shadow-md shadow-violet-200"
            >
              <RefreshCw className="h-4 w-4" />
              Tekrar Dene
            </motion.button>
          )}
        </div>
        <StickyCTA
          primaryLabel="Tekrar Dene"
          onPrimary={onRetry || onBack}
          secondaryLabel="← Geri"
          onSecondary={onBack}
          hideTrust
        />
      </div>
    );
  }

  /* ── PREVIEW READY — BOOK-STYLE FULL-PAGE VIEW ── */
  const currentEntry = imageEntries[safeIdx];

  return (
    <div className="pb-24 space-y-4">
      {/* ── Header ── */}
      <header>
        <p className="text-[10px] sm:text-xs font-bold text-violet-500 uppercase tracking-wider mb-0.5">
          Adım 3
        </p>
        <h2 className="text-lg sm:text-xl font-bold text-slate-800">
          {childName} İçin Kitabınız 📖
        </h2>
        <p className="text-xs sm:text-sm text-slate-500 mt-1">
          Sayfaları inceleyin, beğenmezseniz tekrar oluşturabilirsiniz.
        </p>
      </header>

      {/* ── Full-page Book Viewer ── */}
      {hasImages && currentEntry && (
        <section className="rounded-2xl border border-slate-100 bg-white shadow-sm overflow-hidden">
          {/* Page indicator header */}
          <div className="px-4 pt-3 pb-2 border-b border-slate-50 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <BookOpen className="h-4 w-4 text-violet-500" />
              <span className="text-sm font-semibold text-slate-700">
                {getPageLabel(currentEntry[0])}
              </span>
            </div>
            <span className="text-xs font-medium text-slate-400 tabular-nums bg-slate-50 px-2 py-0.5 rounded-full">
              {safeIdx + 1} / {totalPages}
            </span>
          </div>

          {/* Image display area */}
          <div className="relative bg-gradient-to-b from-slate-50 to-slate-100/50 px-3 py-4 sm:px-6 sm:py-6">
            {/* Page image with animation */}
            <AnimatePresence mode="wait">
              <motion.div
                key={currentEntry[0]}
                initial={{ opacity: 0, x: 30 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -30 }}
                transition={{ duration: 0.2 }}
                className="relative mx-auto"
                style={{ maxWidth: "500px" }}
              >
                {/* Book page shadow */}
                <div className="relative rounded-lg overflow-hidden shadow-xl ring-1 ring-black/5">
                  <Image
                    src={currentEntry[1]}
                    alt={getPageLabel(currentEntry[0])}
                    width={800}
                    height={560}
                    className="w-full h-auto object-contain"
                    sizes="(max-width: 640px) 100vw, 500px"
                    priority
                  />
                </div>
              </motion.div>
            </AnimatePresence>

            {/* Navigation arrows */}
            <button
              type="button"
              onClick={goPrev}
              disabled={safeIdx === 0}
              className={`
                absolute left-1 top-1/2 -translate-y-1/2 flex h-10 w-10 items-center justify-center rounded-full bg-white/90 shadow-lg backdrop-blur-sm transition-all
                sm:left-2 sm:h-11 sm:w-11
                ${safeIdx === 0 ? "opacity-30 cursor-not-allowed" : "hover:bg-white hover:scale-110 active:scale-95"}
              `}
              aria-label="Önceki sayfa"
            >
              <ChevronLeft className="h-5 w-5 text-slate-700" />
            </button>

            <button
              type="button"
              onClick={goNext}
              disabled={safeIdx === totalPages - 1}
              className={`
                absolute right-1 top-1/2 -translate-y-1/2 flex h-10 w-10 items-center justify-center rounded-full bg-white/90 shadow-lg backdrop-blur-sm transition-all
                sm:right-2 sm:h-11 sm:w-11
                ${safeIdx === totalPages - 1 ? "opacity-30 cursor-not-allowed" : "hover:bg-white hover:scale-110 active:scale-95"}
              `}
              aria-label="Sonraki sayfa"
            >
              <ChevronRight className="h-5 w-5 text-slate-700" />
            </button>
          </div>

          {/* Page dots navigation */}
          <div className="px-4 py-2.5 flex items-center justify-center gap-1.5 border-t border-slate-50">
            {imageEntries.map(([key], idx) => (
              <button
                key={key}
                type="button"
                onClick={() => setCurrentIdx(idx)}
                className={`
                  rounded-full transition-all
                  ${idx === safeIdx
                    ? "h-2.5 w-6 bg-violet-500"
                    : "h-2 w-2 bg-slate-200 hover:bg-slate-300"
                  }
                `}
                aria-label={`${getPageLabel(key)} sayfasına git`}
              />
            ))}
          </div>
        </section>
      )}

      {/* ── Retry link ── */}
      {onRetry && (
        <div className="text-center">
          <button
            type="button"
            onClick={onRetry}
            className="inline-flex items-center gap-1.5 text-xs font-medium text-slate-400 hover:text-violet-600 transition-colors"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            Beğenmedim, tekrar oluştur
          </button>
        </div>
      )}

      {/* ── CTA ── */}
      {hasImages && (
        <StickyCTA
          primaryLabel="Kitabın Devamı İçin Süreci Tamamlayın 👉"
          onPrimary={onApprove}
          secondaryLabel="← Geri"
          onSecondary={onBack}
        />
      )}
    </div>
  );
}
