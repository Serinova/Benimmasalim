"use client";

import { useState, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronLeft, ChevronRight, CheckCircle2, Settings2 } from "lucide-react";
import type { VisualStyle } from "@/lib/api";

interface StyleSelectorStepProps {
  // New API
  styles?: VisualStyle[];
  // Old API (backward compat)
  visualStyles?: VisualStyle[];
  selectedStyle: string;
  onSelect: (id: string) => void;
  customIdWeight: number | null;
  onIdWeightChange: (v: number | null) => void;
  onContinue?: () => void;
  onBack?: () => void;
  // Old API extras (ignored gracefully)
  childName?: string;
  isLoading?: boolean;
  hideNavButtons?: boolean;
}

export default function StyleSelectorStep({
  styles: stylesProp,
  visualStyles,
  selectedStyle,
  onSelect,
  customIdWeight,
  onIdWeightChange,
  onContinue,
  onBack,
  hideNavButtons: _hideNavButtons,
}: StyleSelectorStepProps) {
  const [showAdvanced, setShowAdvanced] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Support both old and new prop names
  const styles = stylesProp ?? visualStyles ?? [];

  const selectedObj = styles.find((s) => s.id === selectedStyle);

  const scroll = (dir: "left" | "right") => {
    if (!scrollRef.current) return;
    scrollRef.current.scrollBy({ left: dir === "left" ? -220 : 220, behavior: "smooth" });
  };

  return (
    <div className="space-y-5 px-1 pt-2 pb-4">

      {/* ── Header ── */}
      <div>
        <p className="text-xs font-semibold text-purple-500 uppercase tracking-wider mb-1">🎨 Görsel Stil</p>
        <h2 className="text-xl font-bold text-gray-800 leading-tight">Kitabın Tarzını Seç</h2>
        <p className="text-sm text-gray-400 mt-0.5">Her kitap bu stilde çizilecek</p>
      </div>

      {/* ── Selected style banner ── */}
      <AnimatePresence>
        {selectedObj && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="overflow-hidden"
          >
            <div className="rounded-2xl bg-gradient-to-r from-purple-50 to-pink-50 border border-purple-100 px-4 py-3 flex items-center gap-3">
              {selectedObj.thumbnail_url ? (
                <img
                  src={selectedObj.thumbnail_url}
                  alt={selectedObj.display_name || selectedObj.name}
                  className="w-12 h-12 rounded-xl object-cover flex-shrink-0"
                />
              ) : (
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-purple-300 to-pink-400 flex-shrink-0" />
              )}
              <div className="flex-1 min-w-0">
                <p className="text-xs text-purple-500 font-semibold">Seçilen Stil</p>
                <p className="text-sm font-bold text-gray-800 truncate">
                  {selectedObj.display_name || selectedObj.name}
                </p>
              </div>
              <CheckCircle2 className="h-5 w-5 text-purple-500 flex-shrink-0" />
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── Horizontal Carousel ── */}
      <div className="relative">
        {/* Desktop scroll arrows */}
        <button
          onClick={() => scroll("left")}
          className="absolute left-0 top-1/2 -translate-y-1/2 z-10 w-8 h-8 rounded-full bg-white shadow-md border border-gray-100 items-center justify-center hidden md:flex"
        >
          <ChevronLeft className="h-4 w-4 text-gray-600" />
        </button>

        <div
          ref={scrollRef}
          className="flex gap-3 overflow-x-auto scroll-snap-x-mandatory scrollbar-none px-1 pb-2"
          style={{ scrollSnapType: "x mandatory", WebkitOverflowScrolling: "touch" }}
        >
          {styles.map((style, i) => {
            const isSelected = selectedStyle === style.id;
            const displayName = style.display_name || style.name;

            return (
              <motion.button
                key={style.id}
                type="button"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.05 }}
                whileTap={{ scale: 0.97 }}
                onClick={() => onSelect(style.id)}
                className={`
                  flex-shrink-0 rounded-2xl overflow-hidden text-left transition-all duration-200
                  ${isSelected
                    ? "ring-3 ring-purple-500 shadow-xl shadow-purple-200 scale-[1.02]"
                    : "shadow-sm hover:shadow-md"
                  }
                `}
                style={{
                  width: "160px",
                  scrollSnapAlign: "start",
                }}
              >
                {/* Style image */}
                <div className="relative h-40 bg-gradient-to-br from-purple-200 to-pink-200">
                  {style.thumbnail_url ? (
                    <img
                      src={style.thumbnail_url}
                      alt={displayName}
                      className="h-full w-full object-cover"
                    />
                  ) : (
                    <div className="h-full w-full flex items-center justify-center text-4xl">🎨</div>
                  )}
                  {isSelected && (
                    <motion.div
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="absolute inset-0 bg-purple-600/20 flex items-center justify-center"
                    >
                      <div className="w-9 h-9 rounded-full bg-purple-600 flex items-center justify-center shadow-lg">
                        <CheckCircle2 className="h-5 w-5 text-white" />
                      </div>
                    </motion.div>
                  )}
                </div>

                {/* Card body */}
                <div className={`p-3 ${isSelected ? "bg-purple-50" : "bg-white"}`}>
                  <p className={`text-sm font-bold leading-tight ${isSelected ? "text-purple-700" : "text-gray-800"}`}>
                    {displayName}
                  </p>
                  {isSelected && (
                    <p className="text-xs text-purple-500 mt-0.5 font-medium">✓ Seçili</p>
                  )}
                </div>
              </motion.button>
            );
          })}
        </div>

        <button
          onClick={() => scroll("right")}
          className="absolute right-0 top-1/2 -translate-y-1/2 z-10 w-8 h-8 rounded-full bg-white shadow-md border border-gray-100 items-center justify-center hidden md:flex"
        >
          <ChevronRight className="h-4 w-4 text-gray-600" />
        </button>
      </div>

      {/* Scroll hint */}
      <p className="text-center text-xs text-gray-400">← Kaydırarak daha fazla stil gör →</p>

      {/* ── Advanced Settings (collapsible) ── */}
      <div>
        <button
          type="button"
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="flex items-center gap-2 text-sm text-gray-500 font-medium hover:text-purple-600 transition-colors"
        >
          <Settings2 className="h-4 w-4" />
          Gelişmiş Ayarlar
          <span className={`transition-transform ${showAdvanced ? "rotate-180" : ""}`}>▾</span>
        </button>

        <AnimatePresence>
          {showAdvanced && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="overflow-hidden"
            >
              <div className="mt-3 rounded-2xl border border-gray-200 bg-gray-50 p-4 space-y-3">
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <label className="text-sm font-semibold text-gray-700">
                      🪪 Yüz Benzerliği
                    </label>
                    <span className="text-sm font-bold text-purple-600">
                      {customIdWeight !== null
                        ? `${Math.round(customIdWeight * 100)}%`
                        : "Varsayılan"
                      }
                    </span>
                  </div>
                  <input
                    type="range"
                    min={0}
                    max={1}
                    step={0.05}
                    value={customIdWeight ?? (selectedObj?.id_weight ?? 0.7)}
                    onChange={(e) => onIdWeightChange(parseFloat(e.target.value))}
                    className="w-full accent-purple-600"
                  />
                  <div className="flex justify-between text-xs text-gray-400 mt-1">
                    <span>Daha Çizgisel</span>
                    <span>Daha Gerçekçi</span>
                  </div>
                </div>
                {customIdWeight !== null && (
                  <button
                    type="button"
                    onClick={() => onIdWeightChange(null)}
                    className="text-xs text-purple-600 font-medium hover:underline"
                  >
                    Varsayılana sıfırla
                  </button>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* ── Sticky Bottom CTA ── */}
      <div className="fixed bottom-0 left-0 right-0 z-50 bg-white/95 backdrop-blur-md border-t border-gray-100 px-4 pt-3 pb-safe-4">
        <div className="mx-auto flex max-w-lg gap-3 pb-2">
          <button
            type="button"
            onClick={onBack}
            className="h-14 px-5 rounded-2xl border-2 border-gray-200 text-gray-600 font-semibold text-sm"
          >
            ← Geri
          </button>
          <motion.button
            type="button"
            whileTap={{ scale: 0.98 }}
            onClick={() => selectedStyle && onContinue?.()}
            disabled={!selectedStyle}
            className={`
              h-14 flex-1 rounded-2xl font-bold text-base transition-all duration-200
              ${selectedStyle
                ? "bg-gradient-to-r from-purple-600 to-pink-500 text-white shadow-lg shadow-purple-200"
                : "bg-gray-100 text-gray-400 cursor-not-allowed"
              }
            `}
          >
            {selectedStyle ? "Kitabı Oluştur 🪄" : "Bir Stil Seç"}
          </motion.button>
        </div>
      </div>
    </div>
  );
}
