"use client";

import { useState, useCallback, useEffect, useRef } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { ChevronLeft, ChevronRight, X, Maximize2 } from "lucide-react";

interface ShowcaseBookProps {
  /** Array of image URLs for book pages (first = cover) */
  pages: string[];
}

/* ═══════════════════════════════════════════════════════════════════════
   MINI PREVIEW — Horizontal landscape book shown in the hero section.
   Clicking opens the fullscreen flipbook.
   ═══════════════════════════════════════════════════════════════════════ */

export default function ShowcaseBook({ pages }: ShowcaseBookProps) {
  const [isOpen, setIsOpen] = useState(false);

  if (!pages || pages.length === 0) return null;

  return (
    <>
      {/* Mini Preview — clickable landscape book */}
      <div
        className="group relative cursor-pointer"
        onClick={() => setIsOpen(true)}
        role="button"
        tabIndex={0}
        aria-label="Vitrin kitabını incele"
        onKeyDown={(e) => e.key === "Enter" && setIsOpen(true)}
      >
        <div className="relative mx-auto w-[300px] sm:w-[360px] md:w-[420px]">
          {/* Back pages (depth effect) */}
          {pages.length > 2 && (
            <div className="absolute -bottom-2 left-1 right-1 h-full rounded-xl bg-purple-200/60 shadow-sm" />
          )}
          {pages.length > 1 && (
            <div className="absolute -bottom-1 left-0.5 right-0.5 h-full rounded-xl bg-purple-100/80 shadow-sm" />
          )}

          {/* Cover page — landscape A4 ratio */}
          <div className="relative aspect-[297/210] overflow-hidden rounded-xl border-2 border-white/50 shadow-2xl transition-transform duration-300 group-hover:scale-[1.02] group-hover:shadow-purple-300/40">
            <img
              src={pages[0]}
              alt="Kitap kapağı"
              className="h-full w-full object-cover"
              loading="eager"
            />

            {/* Hover overlay */}
            <div className="absolute inset-0 flex items-center justify-center bg-black/0 transition-colors duration-300 group-hover:bg-black/20">
              <div className="flex items-center gap-2 rounded-full bg-white/90 px-4 py-2 text-sm font-semibold text-gray-800 opacity-0 shadow-lg backdrop-blur-sm transition-all duration-300 group-hover:opacity-100">
                <Maximize2 className="h-4 w-4" />
                Kitabı İncele
              </div>
            </div>

            {/* Top spine shadow (for landscape book) */}
            <div className="absolute inset-x-0 top-0 h-2 bg-gradient-to-b from-black/10 to-transparent" />
          </div>

          {/* Page count badge */}
          <div className="absolute -bottom-3 -right-2 rounded-full bg-purple-600 px-2.5 py-1 text-[10px] font-bold text-white shadow-lg">
            {pages.length} sayfa
          </div>
        </div>
      </div>

      {/* Fullscreen Flipbook Modal */}
      <AnimatePresence>
        {isOpen && (
          <FlipbookModal pages={pages} onClose={() => setIsOpen(false)} />
        )}
      </AnimatePresence>
    </>
  );
}

/* ═══════════════════════════════════════════════════════════════════════
   FULLSCREEN FLIPBOOK — Landscape page turning animation
   ═══════════════════════════════════════════════════════════════════════ */

function FlipbookModal({
  pages,
  onClose,
}: {
  pages: string[];
  onClose: () => void;
}) {
  const [currentPage, setCurrentPage] = useState(0);
  const [flipDirection, setFlipDirection] = useState<"next" | "prev" | null>(null);
  const [isFlipping, setIsFlipping] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const totalPages = pages.length;

  const goNext = useCallback(() => {
    if (currentPage >= totalPages - 1 || isFlipping) return;
    setFlipDirection("next");
    setIsFlipping(true);
    setTimeout(() => {
      setCurrentPage((p) => p + 1);
      setIsFlipping(false);
      setFlipDirection(null);
    }, 500);
  }, [currentPage, totalPages, isFlipping]);

  const goPrev = useCallback(() => {
    if (currentPage <= 0 || isFlipping) return;
    setFlipDirection("prev");
    setIsFlipping(true);
    setTimeout(() => {
      setCurrentPage((p) => p - 1);
      setIsFlipping(false);
      setFlipDirection(null);
    }, 500);
  }, [currentPage, isFlipping]);

  // Keyboard navigation
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
      if (e.key === "ArrowRight" || e.key === " ") goNext();
      if (e.key === "ArrowLeft") goPrev();
    };
    globalThis.addEventListener("keydown", handler);
    return () => globalThis.removeEventListener("keydown", handler);
  }, [onClose, goNext, goPrev]);

  // Swipe support
  const touchStartX = useRef(0);
  const handleTouchStart = (e: React.TouchEvent) => {
    touchStartX.current = e.touches[0].clientX;
  };
  const handleTouchEnd = (e: React.TouchEvent) => {
    const diff = touchStartX.current - e.changedTouches[0].clientX;
    if (Math.abs(diff) > 50) {
      if (diff > 0) goNext();
      else goPrev();
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/90 backdrop-blur-sm"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      {/* Close button */}
      <button
        onClick={onClose}
        className="absolute right-4 top-4 z-10 rounded-full bg-white/10 p-2.5 text-white transition-colors hover:bg-white/20"
        aria-label="Kapat"
      >
        <X className="h-6 w-6" />
      </button>

      {/* Page counter */}
      <div className="absolute left-1/2 top-4 z-10 -translate-x-1/2 rounded-full bg-white/10 px-4 py-1.5 text-sm font-medium text-white backdrop-blur-sm">
        {currentPage === 0 ? "Kapak" : `Sayfa ${currentPage}`} / {totalPages - 1}
      </div>

      {/* Navigation arrows */}
      <button
        onClick={goPrev}
        disabled={currentPage <= 0 || isFlipping}
        className="absolute left-2 top-1/2 z-10 -translate-y-1/2 rounded-full bg-white/10 p-3 text-white transition-all hover:bg-white/20 disabled:opacity-20 sm:left-4"
        aria-label="Önceki sayfa"
      >
        <ChevronLeft className="h-6 w-6 sm:h-8 sm:w-8" />
      </button>
      <button
        onClick={goNext}
        disabled={currentPage >= totalPages - 1 || isFlipping}
        className="absolute right-2 top-1/2 z-10 -translate-y-1/2 rounded-full bg-white/10 p-3 text-white transition-all hover:bg-white/20 disabled:opacity-20 sm:right-4"
        aria-label="Sonraki sayfa"
      >
        <ChevronRight className="h-6 w-6 sm:h-8 sm:w-8" />
      </button>

      {/* Book container */}
      <div
        ref={containerRef}
        className="relative mx-auto flex items-center justify-center px-14 sm:px-20"
        style={{ perspective: "1500px" }}
        onTouchStart={handleTouchStart}
        onTouchEnd={handleTouchEnd}
      >
        {/* The book — landscape A4 */}
        <div className="relative" style={{ transformStyle: "preserve-3d" }}>
          {/* Current page (static base) */}
          <motion.div
            key={`page-${currentPage}`}
            initial={false}
            className="relative overflow-hidden rounded-lg shadow-2xl"
            style={{
              width: "min(85vw, 800px)",
              aspectRatio: "297 / 210",
            }}
          >
            <img
              src={pages[currentPage]}
              alt={currentPage === 0 ? "Kapak" : `Sayfa ${currentPage}`}
              className="h-full w-full object-cover"
              draggable={false}
            />
            {/* Top spine shadow for landscape */}
            <div className="absolute inset-x-0 top-0 h-3 bg-gradient-to-b from-black/15 to-transparent" />
            <div className="absolute inset-x-0 bottom-0 h-1 bg-gradient-to-t from-black/10 to-transparent" />
          </motion.div>

          {/* Flipping page overlay */}
          <AnimatePresence>
            {isFlipping && flipDirection === "next" && (
              <motion.div
                key="flip-next"
                className="absolute inset-0 overflow-hidden rounded-lg shadow-2xl"
                style={{
                  transformOrigin: "top center",
                  backfaceVisibility: "hidden",
                }}
                initial={{ rotateX: 0 }}
                animate={{ rotateX: -180 }}
                exit={{ rotateX: -180 }}
                transition={{ duration: 0.5, ease: [0.4, 0, 0.2, 1] }}
              >
                <img
                  src={pages[currentPage]}
                  alt=""
                  className="h-full w-full object-cover"
                  draggable={false}
                />
                <div className="absolute inset-x-0 top-0 h-3 bg-gradient-to-b from-black/15 to-transparent" />
              </motion.div>
            )}
            {isFlipping && flipDirection === "prev" && (
              <motion.div
                key="flip-prev"
                className="absolute inset-0 overflow-hidden rounded-lg shadow-2xl"
                style={{
                  transformOrigin: "bottom center",
                  backfaceVisibility: "hidden",
                }}
                initial={{ rotateX: 0 }}
                animate={{ rotateX: 180 }}
                exit={{ rotateX: 180 }}
                transition={{ duration: 0.5, ease: [0.4, 0, 0.2, 1] }}
              >
                <img
                  src={pages[currentPage]}
                  alt=""
                  className="h-full w-full object-cover"
                  draggable={false}
                />
                <div className="absolute inset-x-0 bottom-0 h-1 bg-gradient-to-t from-black/10 to-transparent" />
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* Thumbnail strip — landscape thumbnails */}
      <div className="absolute bottom-4 left-1/2 z-10 flex max-w-[90vw] -translate-x-1/2 gap-2 overflow-x-auto rounded-xl bg-white/10 p-2 backdrop-blur-sm">
        {pages.map((url, idx) => (
          <button
            key={idx}
            onClick={() => {
              if (!isFlipping && idx !== currentPage) {
                setCurrentPage(idx);
              }
            }}
            className={`flex-shrink-0 overflow-hidden rounded-md border-2 transition-all ${
              idx === currentPage
                ? "border-white shadow-lg scale-110"
                : "border-transparent opacity-60 hover:opacity-90"
            }`}
          >
            <img
              src={url}
              alt={idx === 0 ? "Kapak" : `Sayfa ${idx}`}
              className="h-10 w-14 object-cover sm:h-12 sm:w-[68px]"
              loading="lazy"
            />
          </button>
        ))}
      </div>
    </motion.div>
  );
}
