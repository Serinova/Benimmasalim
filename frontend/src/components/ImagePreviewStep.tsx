"use client";

import { useState, useRef, useEffect, forwardRef, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ChevronLeft,
  ChevronRight,
  AlertCircle,
  X,
  Sparkles,
  BookOpen,
} from "lucide-react";
import type { GenerationProgress } from "@/lib/api";

interface ImagePreviewStepProps {
  childName: string;
  previewImages: { [key: number | string]: string };
  onApprove: () => void;
  onBack: () => void;
  onReportIssue?: (issue: string) => void;
  isLoading?: boolean;
  generationProgress?: GenerationProgress | null;
  backCoverImageUrl?: string | null;
}

// Cover Page component with glossy effect
const CoverPage = forwardRef<HTMLDivElement, { imageUrl: string; isFront?: boolean }>(
  ({ imageUrl, isFront = true }, ref) => {
    return (
      <div ref={ref} className="page-content cover-page">
        <div className="relative h-full w-full overflow-hidden">
          {imageUrl ? (
            <>
              <img
                src={imageUrl}
                alt="Kapak"
                className="h-full w-full object-cover"
                draggable={false}
              />
              {/* Glossy overlay effect */}
              <div
                className="pointer-events-none absolute inset-0"
                style={{
                  background: `
                    linear-gradient(
                      135deg, 
                      rgba(255,255,255,0.3) 0%, 
                      rgba(255,255,255,0.1) 30%,
                      transparent 50%,
                      rgba(0,0,0,0.1) 80%,
                      rgba(0,0,0,0.2) 100%
                    )
                  `,
                }}
              />
              {/* Light reflection stripe */}
              <div
                className="pointer-events-none absolute inset-0"
                style={{
                  background: `
                    linear-gradient(
                      105deg,
                      transparent 40%,
                      rgba(255,255,255,0.15) 45%,
                      rgba(255,255,255,0.3) 50%,
                      rgba(255,255,255,0.15) 55%,
                      transparent 60%
                    )
                  `,
                }}
              />
              {/* Edge highlight for 3D effect */}
              {isFront && (
                <div className="pointer-events-none absolute bottom-0 right-0 top-0 w-4 bg-gradient-to-l from-black/20 to-transparent" />
              )}
            </>
          ) : (
            <div className="flex h-full w-full items-center justify-center bg-gradient-to-br from-amber-800 to-amber-950">
              <div className="text-center text-amber-200/60">
                <BookOpen className="mx-auto mb-3 h-16 w-16 opacity-50" />
                <p>Kapak yükleniyor...</p>
              </div>
            </div>
          )}
        </div>
      </div>
    );
  }
);
CoverPage.displayName = "CoverPage";

// Dedication page component — pastel background with centred text
const DedicationPage = forwardRef<HTMLDivElement, { childName: string; imageUrl?: string }>(
  ({ childName, imageUrl }, ref) => {
    // If backend provided a composed dedication image, show it directly
    if (imageUrl) {
      return (
        <div ref={ref} className="page-content inner-page">
          <div className="relative h-full w-full overflow-hidden">
            <img
              src={imageUrl}
              alt="Karşılama Sayfası"
              className="h-full w-full object-cover"
              draggable={false}
            />
          </div>
        </div>
      );
    }
    // Otherwise, render a CSS-based fallback
    return (
      <div ref={ref} className="page-content inner-page">
        <div
          className="relative flex h-full w-full flex-col items-center justify-center overflow-hidden"
          style={{ backgroundColor: "#FFF5E6" }}
        >
          {/* Decorative border */}
          <div
            className="absolute inset-4 rounded-xl border-2"
            style={{ borderColor: "#5B463640" }}
          />
          <p
            className="z-10 px-8 text-center leading-relaxed"
            style={{
              fontFamily: "'Nunito', sans-serif",
              fontSize: "clamp(14px, 2.5vw, 22px)",
              color: "#5B4636",
            }}
          >
            Bu kitap{" "}
            <span className="font-bold" style={{ color: "#8B5E3C" }}>
              {childName}
            </span>{" "}
            için özel hazırlanmıştır
          </p>
          <p className="mt-2 text-lg" style={{ color: "#5B463680" }}>
            ✨
          </p>
        </div>
      </div>
    );
  }
);
DedicationPage.displayName = "DedicationPage";

// Inner page component with matte paper texture
const InnerPage = forwardRef<
  HTMLDivElement,
  { imageUrl: string; pageNumber: number; side: "left" | "right" }
>(({ imageUrl, pageNumber, side }, ref) => {
  return (
    <div ref={ref} className="page-content inner-page">
      <div className="relative h-full w-full overflow-hidden bg-amber-50">
        {/* Paper texture base */}
        <div
          className="absolute inset-0 opacity-40"
          style={{
            backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%' height='100%' filter='url(%23noise)'/%3E%3C/svg%3E")`,
          }}
        />

        {imageUrl ? (
          <>
            <img
              src={imageUrl}
              alt={`Sayfa ${pageNumber}`}
              className="relative z-10 h-full w-full object-cover"
              draggable={false}
            />
            {/* Matte finish overlay - subtle */}
            <div
              className="pointer-events-none absolute inset-0 z-20"
              style={{
                background:
                  side === "left"
                    ? "linear-gradient(to right, rgba(0,0,0,0.08) 0%, transparent 15%)"
                    : "linear-gradient(to left, rgba(0,0,0,0.08) 0%, transparent 15%)",
              }}
            />
          </>
        ) : (
          <div className="relative z-10 flex h-full w-full items-center justify-center">
            <div className="text-center text-amber-400/60">
              <BookOpen className="mx-auto mb-2 h-12 w-12 opacity-50" />
              <p className="text-sm">Sayfa {pageNumber}</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
});
InnerPage.displayName = "InnerPage";

// Back cover (blank/decorative)
const BackCover = forwardRef<HTMLDivElement, object>((_, ref) => {
  return (
    <div ref={ref} className="page-content back-cover">
      <div
        className="relative h-full w-full overflow-hidden"
        style={{
          background: "linear-gradient(135deg, #92400e 0%, #78350f 50%, #451a03 100%)",
        }}
      >
        {/* Leather texture pattern */}
        <div
          className="absolute inset-0 opacity-30"
          style={{
            backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23000' fill-opacity='0.2'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`,
          }}
        />
        {/* Embossed logo area */}
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-center text-amber-200/20">
            <BookOpen className="mx-auto mb-4 h-20 w-20" />
            <p className="font-serif text-lg">Benim Masalım</p>
          </div>
        </div>
        {/* Edge shadow for depth */}
        <div className="absolute bottom-0 left-0 top-0 w-4 bg-gradient-to-r from-black/30 to-transparent" />
      </div>
    </div>
  );
});
BackCover.displayName = "BackCover";

// Issue Report Modal
function IssueModal({
  isOpen,
  onClose,
  onSubmit,
}: {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (issue: string) => void;
}) {
  const issues = [
    { id: "face", label: "Çocuğun yüzü benzememiş", icon: "😕" },
    { id: "quality", label: "Görsel kalitesi düşük", icon: "📷" },
    { id: "style", label: "Stil beklediğim gibi değil", icon: "🎨" },
    { id: "content", label: "İçerik hikayeyle uyuşmuyor", icon: "📖" },
    { id: "other", label: "Diğer", icon: "💬" },
  ];

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-[100] flex items-center justify-center p-4"
          onClick={onClose}
        >
          <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" />

          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.9, opacity: 0 }}
            onClick={(e) => e.stopPropagation()}
            className="relative w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl"
          >
            <button
              onClick={onClose}
              className="absolute right-4 top-4 rounded-full p-2 transition-colors hover:bg-gray-100"
            >
              <X className="h-5 w-5 text-gray-400" />
            </button>

            <div className="mb-6 text-center">
              <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-amber-100">
                <AlertCircle className="h-7 w-7 text-amber-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900">Bir Sorun mu Var?</h3>
              <p className="mt-1 text-sm text-gray-500">Sorunu seçin, size yardımcı olalım</p>
            </div>

            <div className="space-y-3">
              {issues.map((issue) => (
                <button
                  key={issue.id}
                  onClick={() => {
                    onSubmit(issue.id);
                    onClose();
                  }}
                  className="group flex w-full items-center gap-4 rounded-xl border-2 border-gray-100 p-4 text-left transition-all hover:border-purple-300 hover:bg-purple-50/50"
                >
                  <span className="text-2xl">{issue.icon}</span>
                  <span className="font-medium text-gray-700 group-hover:text-purple-700">
                    {issue.label}
                  </span>
                </button>
              ))}
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

// Loading animation component with progress tracking
function MagicalLoadingAnimation({
  progress,
}: {
  progress?: GenerationProgress | null;
}) {
  // Calculate progress percentage
  const getProgressPercent = (): number => {
    if (!progress) return 5; // Indeterminate — small amount to show "started"
    const { current_page, total_pages, stage } = progress;
    if (stage === "queued") return 2;
    if (stage === "uploading") return 90;
    if (stage === "composing") return 75;
    // generating_images: scale 5%–70% based on pages
    if (total_pages <= 0) return 10;
    return Math.min(5 + (current_page / total_pages) * 65, 70);
  };

  const getStageMessage = (): string => {
    if (!progress) return "Sihirli sayfalar hazırlanıyor...";
    const { current_page, total_pages, stage } = progress;
    switch (stage) {
      case "queued":
        return "Sıranız bekleniyor...";
      case "generating_images":
        return current_page > 0
          ? `Sayfa ${current_page}/${total_pages} oluşturuldu`
          : `Görseller oluşturuluyor (0/${total_pages})...`;
      case "composing":
        return "Sayfalar tasarlanıyor...";
      case "uploading":
        return "Son dokunuşlar yapılıyor...";
      default:
        return "Sihirli sayfalar hazırlanıyor...";
    }
  };

  const percent = getProgressPercent();
  const message = getStageMessage();

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 flex items-center justify-center"
      style={{
        background: "linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)",
      }}
    >
      <div className="relative flex flex-col items-center">
        {/* Animated book */}
        <motion.div
          animate={{
            rotateY: [0, 10, 0, -10, 0],
            scale: [1, 1.02, 1, 1.02, 1],
          }}
          transition={{
            duration: 3,
            repeat: Infinity,
            ease: "easeInOut",
          }}
          className="relative"
        >
          <div className="relative h-48 w-72">
            <motion.div
              animate={{ rotateY: [-5, 5, -5] }}
              transition={{ duration: 2, repeat: Infinity }}
              className="absolute left-0 top-0 h-48 w-36 origin-right rounded-l-lg bg-gradient-to-r from-amber-100 to-amber-50"
              style={{
                boxShadow: "inset -10px 0 20px rgba(0,0,0,0.1)",
              }}
            />
            <motion.div
              animate={{ rotateY: [5, -5, 5] }}
              transition={{ duration: 2, repeat: Infinity }}
              className="absolute right-0 top-0 h-48 w-36 origin-left rounded-r-lg bg-gradient-to-l from-amber-100 to-amber-50"
              style={{
                boxShadow: "inset 10px 0 20px rgba(0,0,0,0.1)",
              }}
            />
            <div className="absolute left-1/2 top-0 h-48 w-2 -translate-x-1/2 rounded-sm bg-amber-800" />
          </div>

          <motion.div
            animate={{
              opacity: [0.3, 0.7, 0.3],
              scale: [1, 1.2, 1],
            }}
            transition={{
              duration: 2,
              repeat: Infinity,
              ease: "easeInOut",
            }}
            className="absolute inset-0 -m-8"
            style={{
              background: "radial-gradient(circle, rgba(255,215,0,0.4) 0%, transparent 70%)",
              filter: "blur(20px)",
            }}
          />
        </motion.div>

        {/* Sparkle particles */}
        {[...Array(8)].map((_, i) => (
          <motion.div
            key={i}
            animate={{
              y: [-20, -60, -20],
              x: [0, i % 2 === 0 ? 20 : -20, 0],
              opacity: [0, 1, 0],
              scale: [0.5, 1, 0.5],
            }}
            transition={{
              duration: 2 + i * 0.3,
              repeat: Infinity,
              delay: i * 0.2,
            }}
            className="absolute"
            style={{
              left: `${20 + i * 10}%`,
              top: "10%",
            }}
          >
            <Sparkles className="h-4 w-4 text-yellow-300" />
          </motion.div>
        ))}

        {/* Progress bar */}
        <div className="mt-10 w-72">
          <div className="h-2 w-full overflow-hidden rounded-full bg-white/10">
            <motion.div
              className="h-full rounded-full"
              style={{
                background: "linear-gradient(90deg, #f59e0b, #fbbf24, #f59e0b)",
                backgroundSize: "200% 100%",
              }}
              initial={{ width: "0%" }}
              animate={{
                width: `${percent}%`,
                backgroundPosition: ["0% 0%", "100% 0%", "0% 0%"],
              }}
              transition={{
                width: { duration: 0.8, ease: "easeOut" },
                backgroundPosition: { duration: 2, repeat: Infinity, ease: "linear" },
              }}
            />
          </div>

          {/* Percentage text */}
          <motion.p
            key={percent}
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-2 text-right text-xs text-amber-300/60"
          >
            %{Math.round(percent)}
          </motion.p>
        </div>

        {/* Stage message */}
        <AnimatePresence mode="wait">
          <motion.p
            key={message}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.4 }}
            className="mt-4 text-center font-medium text-amber-200"
          >
            {message}
          </motion.p>
        </AnimatePresence>

        {/* Subtle hint */}
        <motion.p
          animate={{ opacity: [0.3, 0.6, 0.3] }}
          transition={{ duration: 3, repeat: Infinity }}
          className="mt-3 text-center text-xs text-amber-200/40"
        >
          Bu işlem 1-3 dakika sürebilir
        </motion.p>
      </div>
    </motion.div>
  );
}

export default function ImagePreviewStep({
  childName,
  previewImages,
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  onApprove,
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  onBack,
  onReportIssue,
  isLoading = false,
  generationProgress,
  backCoverImageUrl,
}: ImagePreviewStepProps) {
  const [currentSlide, setCurrentSlide] = useState(0);
  const [showIssueModal, setShowIssueModal] = useState(false);
  const [imagesLoaded, setImagesLoaded] = useState(false);
  const touchStartX = useRef(0);

  // Image mapping:
  //   cover        → key 0
  //   dedication   → key "dedication"  (karşılama 1)
  //   intro        → key "intro"       (karşılama 2, optional)
  //   story pages  → numeric keys > 0, sorted ascending
  const coverImage = previewImages[0] || "";
  const dedicationImage = previewImages["dedication"] || "";
  const introImage = (previewImages as Record<string, string>)["intro"] || "";
  const hasIntro = Boolean(previewImages["intro"]);

  // Dynamically find ALL story page keys (any numeric key > 0, sorted ascending)
  const storyPageKeys = Object.keys(previewImages)
    .filter((k) => k !== "0" && k !== "dedication" && k !== "intro" && !k.includes("back"))
    .map(Number)
    .filter((n) => !Number.isNaN(n) && n > 0)
    .sort((a, b) => a - b);

  // Slide layout:
  //   0: cover
  //   1: dedication
  //   2 (if hasIntro): intro
  //   2 or 3 ... N: story pages (all of them)
  //   last: back cover (if available)
  // cover=0, dedication=1, [intro=2 if hasIntro], story pages start at (hasIntro?3:2)
  const pagesStartIdx = hasIntro ? 3 : 2;
  const TOTAL_SLIDES = 2 + (hasIntro ? 1 : 0) + storyPageKeys.length + (backCoverImageUrl ? 1 : 0);
  // back cover is always at the last slide index if available
  const backCoverSlideIdx = backCoverImageUrl ? TOTAL_SLIDES - 1 : -1;


  useEffect(() => {
    // Show preview as soon as loading is done and at least the cover image exists.
    // Dedication / intro pages may be absent (partial generation) — handled gracefully below.
    if (!isLoading && Object.keys(previewImages).length >= 1) {
      const timer = setTimeout(() => setImagesLoaded(true), 1500);
      return () => clearTimeout(timer);
    }
  }, [isLoading, previewImages]);

  const goNext = useCallback(() => {
    setCurrentSlide((s) => (s < TOTAL_SLIDES - 1 ? s + 1 : s));
  }, [TOTAL_SLIDES]);

  const goPrev = useCallback(() => {
    setCurrentSlide((s) => (s > 0 ? s - 1 : s));
  }, []);

  const goToSlide = useCallback((index: number) => {
    setCurrentSlide(Math.max(0, Math.min(index, TOTAL_SLIDES - 1)));
  }, [TOTAL_SLIDES]);

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

  const handleIssueSubmit = (issue: string) => {
    onReportIssue?.(issue);
  };

  // Helper: get slide index for a story page (0-based in storyPageKeys)
  const getStorySlideIdx = (pageIdx: number) => pagesStartIdx + pageIdx;

  if (isLoading || !imagesLoaded) {
    return <MagicalLoadingAnimation progress={generationProgress} />;
  }

  return (
    <>
      <div className="relative overflow-hidden pb-4">
        {/* Premium Textured Background */}
        <div
          className="absolute inset-0 z-0"
          style={{
            background: `linear-gradient(135deg, #2d1f14 0%, #3d2b1f 50%, #4a3728 100%)`,
          }}
        >
          <div
            className="absolute inset-0 opacity-20"
            style={{
              backgroundImage: `url("data:image/svg+xml,%3Csvg width='100' height='100' viewBox='0 0 100 100' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='%23000' fill-opacity='0.3'%3E%3Cpath d='M0 0h100v2H0zM0 10h100v1H0zM0 23h100v1H0zM0 35h100v2H0zM0 48h100v1H0zM0 60h100v1H0zM0 73h100v2H0zM0 85h100v1H0zM0 98h100v2H0z'/%3E%3C/g%3E%3C/svg%3E")`,
            }}
          />
          <div
            className="absolute inset-0"
            style={{
              background:
                "radial-gradient(ellipse at 50% -20%, rgba(255,200,100,0.15) 0%, transparent 60%)",
            }}
          />
          <div
            className="absolute inset-0"
            style={{
              background:
                "radial-gradient(ellipse at center, transparent 30%, rgba(0,0,0,0.4) 100%)",
            }}
          />
        </div>

        {/* Content Container */}
        <div className="relative z-10">
          {/* Header */}
          <motion.div
            initial={{ opacity: 0, y: -30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="px-4 pb-2 pt-4 text-center"
          >
            <div className="mb-2 flex items-center justify-center gap-3">
              <motion.div
                animate={{ rotate: [0, 10, -10, 0] }}
                transition={{ duration: 4, repeat: Infinity }}
              >
                <Sparkles className="h-6 w-6 text-yellow-400" />
              </motion.div>
              <h1 className="font-serif text-xl text-amber-100 md:text-2xl">
                {childName}&apos;{childName.slice(-1).match(/[aıouAIOU]/) ? "nın" : "ın"} Kitabı
                Hazır!
              </h1>
              <motion.div
                animate={{ rotate: [0, -10, 10, 0] }}
                transition={{ duration: 4, repeat: Infinity }}
              >
                <Sparkles className="h-6 w-6 text-yellow-400" />
              </motion.div>
            </div>
            <p className="text-sm text-amber-200/70">
              Kaydırarak veya oklarla sayfaları inceleyin
            </p>
          </motion.div>

          {/* Tek sayfa gösterim (ana sayfa hero ile aynı tarz — mobil uyumlu) */}
          <motion.div
            initial={{ opacity: 0, scale: 0.98 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.3, duration: 0.4 }}
            className="relative flex min-h-[360px] items-center justify-center px-2 py-4 sm:min-h-[420px] md:min-h-[480px]"
            onTouchStart={handleTouchStart}
            onTouchEnd={handleTouchEnd}
          >
            {/* Sol ok */}
            <button
              type="button"
              onClick={goPrev}
              disabled={currentSlide <= 0}
              className="absolute left-1 z-20 flex h-10 w-10 shrink-0 items-center justify-center rounded-full border border-white/20 bg-white/10 text-amber-200 backdrop-blur-sm transition-all hover:scale-105 hover:bg-white/20 hover:text-white disabled:opacity-30 sm:left-2 sm:h-12 sm:w-12 md:left-4 md:h-14 md:w-14"
              aria-label="Önceki sayfa"
            >
              <ChevronLeft className="h-5 w-5 sm:h-6 sm:w-6 md:h-8 md:w-8" />
            </button>

            {/* Tek sayfa alanı — tam genişlikte tek resim */}
            <div
              className="relative mx-auto w-full max-w-lg overflow-hidden rounded-xl shadow-2xl"
              style={{ aspectRatio: "297 / 210" }}
            >
              <AnimatePresence mode="wait">
                {/* Kapak */}
                {currentSlide === 0 && (
                  <motion.div
                    key="cover"
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -20 }}
                    transition={{ duration: 0.25 }}
                    className="absolute inset-0"
                  >
                    <CoverPage imageUrl={coverImage} isFront={true} ref={() => { }} />
                  </motion.div>
                )}
                {/* Karşılama 1 - İthaf sayfası */}
                {currentSlide === 1 && (
                  <motion.div
                    key="dedication"
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -20 }}
                    transition={{ duration: 0.25 }}
                    className="absolute inset-0"
                  >
                    <DedicationPage childName={childName} imageUrl={dedicationImage} ref={() => { }} />
                  </motion.div>
                )}
                {/* Karşılama 2 - isteğe bağlı intro sayfası */}
                {hasIntro && currentSlide === 2 && (
                  <motion.div
                    key="intro"
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -20 }}
                    transition={{ duration: 0.25 }}
                    className="absolute inset-0"
                  >
                    <DedicationPage childName={childName} imageUrl={introImage} ref={() => { }} />
                  </motion.div>
                )}
                {/* TÜM hikaye sayfaları — döngüyle */}
                {storyPageKeys.map((pageKey, pageIdx) => {
                  const slideIdx = getStorySlideIdx(pageIdx);
                  return currentSlide === slideIdx ? (
                    <motion.div
                      key={`story-page-${pageKey}`}
                      initial={{ opacity: 0, x: 20 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: -20 }}
                      transition={{ duration: 0.25 }}
                      className="absolute inset-0"
                    >
                      <InnerPage
                        imageUrl={previewImages[pageKey] || ""}
                        pageNumber={pageIdx + 1}
                        side={pageIdx % 2 === 0 ? "left" : "right"}
                        ref={() => { }}
                      />
                    </motion.div>
                  ) : null;
                })}
                {/* Arka kapak */}
                {backCoverImageUrl && currentSlide === backCoverSlideIdx && (
                  <motion.div
                    key="back"
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -20 }}
                    transition={{ duration: 0.25 }}
                    className="absolute inset-0"
                  >
                    <CoverPage imageUrl={backCoverImageUrl} isFront={false} ref={() => { }} />
                  </motion.div>
                )}
                {/* Arka kapak (resim yoksa dekoratif) */}
                {!backCoverImageUrl && currentSlide === TOTAL_SLIDES - 1 && storyPageKeys.length > 0 && (
                  <motion.div
                    key="back-default"
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -20 }}
                    transition={{ duration: 0.25 }}
                    className="absolute inset-0"
                  >
                    <BackCover ref={() => { }} />
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            {/* Sağ ok */}
            <button
              type="button"
              onClick={goNext}
              disabled={currentSlide >= TOTAL_SLIDES - 1}
              className="absolute right-1 z-20 flex h-10 w-10 shrink-0 items-center justify-center rounded-full border border-white/20 bg-white/10 text-amber-200 backdrop-blur-sm transition-all hover:scale-105 hover:bg-white/20 hover:text-white disabled:opacity-30 sm:right-2 sm:h-12 sm:w-12 md:right-4 md:h-14 md:w-14"
              aria-label="Sonraki sayfa"
            >
              <ChevronRight className="h-5 w-5 sm:h-6 sm:w-6 md:h-8 md:w-8" />
            </button>
          </motion.div>

          {/* Sayfa göstergesi (noktalar + etiketler) — tüm sayfalar */}
          <div className="mt-4 flex flex-wrap items-center justify-center gap-2 px-2">
            {[
              { label: "Kapak", idx: 0 },
              { label: "İthaf", idx: 1 },
              ...(hasIntro ? [{ label: "Giriş", idx: 2 }] : []),
              ...storyPageKeys.map((_, pageIdx) => ({
                label: `Sayfa ${pageIdx + 1}`,
                idx: getStorySlideIdx(pageIdx),
              })),
              ...(backCoverImageUrl ? [{ label: "Arka Kapak", idx: backCoverSlideIdx }] : []),
            ].map(({ label, idx }) => (
              <button
                key={`nav-${idx}`}
                type="button"
                onClick={() => goToSlide(idx)}
                className={`rounded-full px-3 py-1.5 text-xs font-medium transition-all touch-manipulation ${currentSlide === idx
                  ? "bg-amber-500 text-white shadow-lg"
                  : "bg-amber-200/20 text-amber-200/80 hover:bg-amber-200/30"
                  }`}
              >
                {label}
              </button>
            ))}
          </div>
          {/* Sayfa konumu bilgisi */}
          <p className="mt-2 text-center text-xs text-amber-300/50">
            {currentSlide + 1} / {TOTAL_SLIDES}
          </p>
        </div>

        {/* Issue report link (non-sticky) */}
        <div className="mt-3 flex justify-center">
          <button
            onClick={() => setShowIssueModal(true)}
            className="flex items-center gap-2 text-xs text-amber-300/60 transition-colors hover:text-amber-200"
          >
            <AlertCircle className="h-3.5 w-3.5" />
            Bir sorun mu var?
          </button>
        </div>
      </div>

      {/* Issue Report Modal */}
      <IssueModal
        isOpen={showIssueModal}
        onClose={() => setShowIssueModal(false)}
        onSubmit={handleIssueSubmit}
      />

      {/* Tek sayfa önizleme stilleri (hero ile aynı tarz) */}
      <style jsx global>{`
        .page-content {
          width: 100%;
          height: 100%;
          overflow: hidden;
          padding: 0;
          border-radius: inherit;
        }

        .page-content img {
          width: 100%;
          height: 100%;
          object-fit: cover;
          object-position: center;
          display: block;
        }

        .cover-page {
          background: linear-gradient(135deg, #92400e 0%, #78350f 100%);
        }

        .inner-page {
          background: #fef3c7;
        }

        .back-cover {
          background: linear-gradient(135deg, #78350f 0%, #451a03 100%);
        }
      `}</style>
    </>
  );
}
