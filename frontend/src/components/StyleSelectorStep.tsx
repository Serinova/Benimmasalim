"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Check,
  Sparkles,
  Palette,
  Wand2,
  ChevronRight,
  Trophy,
  Sliders,
  User,
  Image,
} from "lucide-react";
// NOT: styleExtensions ve defaultStyles kaldırıldı — stiller artık sadece API/DB'den gelir.
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";

// Types
interface VisualStyle {
  id: string;
  name: string;
  /** Kullanıcıya gösterilen isim (boşsa name kullanılır). */
  display_name?: string | null;
  thumbnail_url: string;
  prompt_modifier: string;
  id_weight?: number; // PuLID face weight (0.2-0.7)
  // Extended fields
  description?: string;
  badge?: string;
  badgeIcon?: string;
  bestFor?: string;
  colorAccent?: string;
}

interface StyleSelectorStepProps {
  visualStyles: VisualStyle[];
  selectedStyle: string;
  onSelect: (styleId: string) => void;
  onContinue: () => void;
  onBack: () => void;
  childName?: string;
  customIdWeight?: number | null; // Custom PuLID weight override
  onIdWeightChange?: (weight: number | null) => void; // Callback for weight change
  isLoading?: boolean; // Hikaye üretilirken butonu devre dışı bırak
}

// Varsayılan renk gradyanı — DB stili thumbnail yoksa kullanılır.
const DEFAULT_COLOR_ACCENT = "from-purple-400 to-pink-500";

// Style Card Component — larger images, mobile-friendly
function StyleCard({
  style,
  isSelected,
  onSelect,
}: {
  style: VisualStyle;
  isSelected: boolean;
  onSelect: () => void;
}) {
  const [imageError, setImageError] = useState(false);

  const displayLabel = style.display_name ?? style.name;
  const colorAccent = style.colorAccent || DEFAULT_COLOR_ACCENT;
  const showFallback = !style.thumbnail_url || imageError;

  return (
    <motion.div
      layoutId={`style-card-${style.id}`}
      onClick={onSelect}
      whileTap={{ scale: 0.97 }}
      className={`relative cursor-pointer overflow-hidden rounded-2xl border-2 transition-all duration-200 ${
        isSelected
          ? "border-purple-500 shadow-xl shadow-purple-200/50 ring-2 ring-purple-400 ring-offset-2"
          : "border-transparent shadow-md hover:shadow-lg hover:border-gray-200"
      }`}
    >
      {/* Image Container — taller aspect ratio for better visuals */}
      <div className="relative aspect-[3/4] overflow-hidden bg-gradient-to-br from-gray-100 to-gray-200">
        {style.thumbnail_url && !imageError ? (
          <img
            src={style.thumbnail_url}
            alt={displayLabel}
            className="h-full w-full object-cover transition-transform duration-300 hover:scale-105"
            onError={() => setImageError(true)}
            loading="lazy"
          />
        ) : showFallback ? (
          <div className={`flex h-full w-full items-center justify-center bg-gradient-to-br ${colorAccent}`}>
            <Palette className="h-12 w-12 text-white/40" />
          </div>
        ) : null}

        {/* Bottom gradient for text readability */}
        {!showFallback && (
          <div className="absolute inset-x-0 bottom-0 h-20 bg-gradient-to-t from-black/60 via-black/20 to-transparent" />
        )}

        {/* Selected checkmark */}
        <AnimatePresence>
          {isSelected && (
            <motion.div
              initial={{ scale: 0, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0, opacity: 0 }}
              className="absolute right-2 top-2 flex h-8 w-8 items-center justify-center rounded-full bg-purple-600 shadow-lg sm:h-9 sm:w-9"
            >
              <Check className="h-4 w-4 text-white sm:h-5 sm:w-5" strokeWidth={3} />
            </motion.div>
          )}
        </AnimatePresence>

        {/* Badge */}
        {style.badge && (
          <div className="absolute left-2 top-2 rounded-full bg-white/90 px-2 py-1 text-[10px] font-bold text-gray-800 shadow backdrop-blur-sm sm:text-xs">
            {style.badge}
          </div>
        )}

        {/* Name overlay on image */}
        {!showFallback && (
          <div className="absolute inset-x-0 bottom-0 p-2.5 sm:p-3">
            <h3 className="text-sm font-bold leading-tight text-white drop-shadow-md sm:text-base">
              {displayLabel}
            </h3>
          </div>
        )}
      </div>

      {/* Fallback text below (only when no image) */}
      {showFallback && (
        <div className={`p-2.5 sm:p-3 ${isSelected ? `bg-gradient-to-r ${colorAccent} text-white` : "bg-white"}`}>
          <h3 className={`text-sm font-bold sm:text-base ${isSelected ? "text-white" : "text-gray-800"}`}>
            {displayLabel}
          </h3>
        </div>
      )}
    </motion.div>
  );
}

export default function StyleSelectorStep({
  visualStyles,
  selectedStyle,
  onSelect,
  onContinue,
  onBack,
  childName,
  customIdWeight,
  onIdWeightChange,
  isLoading = false,
}: StyleSelectorStepProps) {
  const [showAdvanced, setShowAdvanced] = useState(false);

  // Stiller API'den gelir
  const styles = visualStyles;

  // Seçili stil bilgisi
  const selectedExtended = selectedStyle
    ? styles.find((s) => s.id === selectedStyle) ?? null
    : null;

  // Get effective id_weight (custom > style default > 0.40)
  const selectedStyleData = styles.find((s) => s.id === selectedStyle);
  const effectiveIdWeight = customIdWeight ?? selectedStyleData?.id_weight ?? 0.4;

  return (
    <div className="space-y-4 pb-20 text-base touch-manipulation min-h-0">
      {/* Header — 16px base on mobile to prevent iOS zoom on focus */}
      <div className="text-center">
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-4 inline-flex items-center gap-2 rounded-full bg-gradient-to-r from-purple-100 via-pink-100 to-orange-100 px-4 py-2 text-sm sm:text-base"
        >
          <Palette className="h-4 w-4 text-purple-600" />
          <span className="font-medium text-purple-700">Sanat Stüdyosu</span>
        </motion.div>

        <motion.h1
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="text-xl font-bold text-gray-800 sm:text-2xl md:text-3xl"
        >
          Hikayeniz Hangi Dünyada Geçsin?
        </motion.h1>

        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
          className="mx-auto mt-3 max-w-lg text-sm text-gray-600 sm:text-base"
        >
          {childName ? (
            <>
              <span className="font-medium text-purple-600">{childName}</span>&apos;ın fotoğrafını
              yapay zeka ile bu sanat stillerinden birine dönüştüreceğiz.
            </>
          ) : (
            "Çocuğunuzun fotoğrafını yapay zeka ile bu sanat stillerinden birine dönüştüreceğiz."
          )}
        </motion.p>
      </div>

      {/* Selected Style Preview */}
      <AnimatePresence>
        {selectedExtended && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="space-y-3 overflow-hidden"
          >
            <div
              className={`bg-gradient-to-r ${selectedExtended.colorAccent || DEFAULT_COLOR_ACCENT} rounded-2xl p-4 text-white`}
            >
              <div className="flex items-center gap-4">
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-white/20">
                  <Wand2 className="h-6 w-6" />
                </div>
                <div className="flex-1">
                  <p className="text-sm text-white/80">Seçilen Stil</p>
                  <p className="text-lg font-bold">{selectedExtended?.display_name ?? selectedExtended?.name ?? ""}</p>
                </div>
                <button
                  type="button"
                  onClick={() => setShowAdvanced(!showAdvanced)}
                  className="flex items-center gap-1.5 rounded-full bg-white/20 px-3 py-1.5 text-base transition-colors hover:bg-white/30"
                >
                  <Sliders className="h-4 w-4" />
                  Gelişmiş
                </button>
              </div>
            </div>

            {/* Advanced Settings - ID Weight Slider */}
            <AnimatePresence>
              {showAdvanced && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  exit={{ opacity: 0, height: 0 }}
                  className="overflow-hidden"
                >
                  <div className="space-y-4 rounded-xl border border-gray-200 bg-gray-50 p-4">
                    <div className="flex items-center gap-2 text-gray-700">
                      <Sliders className="h-5 w-5" />
                      <span className="font-semibold">Yüz Benzerliği Ayarı</span>
                    </div>

                    <div className="space-y-3">
                      <div className="flex items-center justify-between text-sm">
                        <div className="flex items-center gap-2">
                          {/* eslint-disable-next-line jsx-a11y/alt-text -- Lucide icon, decorative */}
                          <Image className="h-4 w-4 text-purple-500" aria-hidden />
                          <span className="text-gray-600">Daha Stilize</span>
                        </div>
                        <span className="rounded bg-gray-200 px-2 py-1 font-mono text-sm">
                          {(effectiveIdWeight * 100).toFixed(0)}%
                        </span>
                        <div className="flex items-center gap-2">
                          <span className="text-gray-600">Daha Gerçekçi</span>
                          <User className="h-4 w-4 text-blue-500" />
                        </div>
                      </div>

                      <Slider
                        value={[effectiveIdWeight]}
                        min={0.15}
                        max={0.7}
                        step={0.05}
                        onValueChange={(value) => onIdWeightChange?.(value[0])}
                        className="w-full"
                      />

                      <div className="flex justify-between text-xs text-gray-500">
                        <span>15% - Anime/Sanatsal</span>
                        <span>40% - Dengeli</span>
                        <span>70% - Fotoğraf Gibi</span>
                      </div>

                      {customIdWeight !== null &&
                        customIdWeight !== selectedStyleData?.id_weight && (
                          <button
                            onClick={() => onIdWeightChange?.(null)}
                            className="text-xs text-purple-600 underline hover:text-purple-800"
                          >
                            Varsayılana Sıfırla (
                            {((selectedStyleData?.id_weight ?? 0.4) * 100).toFixed(0)}%)
                          </button>
                        )}
                    </div>

                    <p className="text-xs text-gray-500">
                      💡 <strong>İpucu:</strong> Anime/sulu boya gibi stilize tarzlar için düşük
                      değer (20-30%), gerçekçi stiller için yüksek değer (50-70%) önerilir.
                    </p>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Style Grid — 2 cols mobile, 3 tablet, 4 desktop for larger images */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.3 }}
        className="grid grid-cols-2 gap-3 sm:gap-4 md:grid-cols-3 lg:grid-cols-4"
      >
        {styles.map((style, index) => (
          <motion.div
            key={style.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.05 * index + 0.3 }}
          >
            <StyleCard
              style={style}
              isSelected={selectedStyle === style.id}
              onSelect={() => onSelect(style.id)}
            />
          </motion.div>
        ))}
      </motion.div>

      {/* Recommendation Note */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.6 }}
        className="flex items-center justify-center gap-2 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2"
      >
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-amber-100">
          <Trophy className="h-4 w-4 text-amber-600" />
        </div>
        <div>
          <p className="text-sm text-amber-800">
            <span className="font-bold">Öneri:</span> &quot;Sihirli Animasyon&quot; stilimiz
            ailelerin %78&apos;i tarafından tercih ediliyor!
          </p>
        </div>
      </motion.div>

      {/* Sticky Bottom Bar */}
      <motion.div
        initial={{ opacity: 0, y: 50 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
        className="fixed bottom-0 left-0 right-0 z-50 border-t border-gray-200 bg-white/95 px-4 py-2.5 backdrop-blur-md"
      >
        <div className="mx-auto flex max-w-4xl flex-col items-center gap-3 md:flex-row">
          {/* Selection Status */}
          <div className="flex flex-1 items-center gap-3">
            {selectedStyle ? (
              <>
                <div
                  className={`h-10 w-10 rounded-xl bg-gradient-to-r ${selectedExtended?.colorAccent || DEFAULT_COLOR_ACCENT} flex items-center justify-center`}
                >
                  <Check className="h-5 w-5 text-white" />
                </div>
                <div>
                  <p className="text-sm text-gray-500">Seçili Stil</p>
                  <p className="font-bold text-gray-800">{selectedExtended?.display_name ?? selectedExtended?.name ?? ""}</p>
                </div>
              </>
            ) : (
              <>
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gray-100">
                  <Palette className="h-5 w-5 text-gray-400" />
                </div>
                <div>
                  <p className="text-gray-500">Henüz seçim yapılmadı</p>
                </div>
              </>
            )}
          </div>

          {/* Action Buttons */}
          <div className="flex w-full gap-3 md:w-auto">
            <Button variant="outline" onClick={onBack} className="flex-1 md:flex-none">
              Geri
            </Button>
            <Button
              onClick={onContinue}
              disabled={!selectedStyle || isLoading}
              className={`flex-1 px-6 py-3 text-sm font-bold transition-all md:flex-none ${
                selectedStyle && !isLoading
                  ? "bg-gradient-to-r from-purple-600 via-pink-500 to-orange-400 shadow-lg shadow-purple-200 hover:from-purple-700 hover:via-pink-600 hover:to-orange-500"
                  : "cursor-not-allowed bg-gray-200 text-gray-500"
              }`}
            >
              {isLoading ? (
                <span className="flex items-center gap-2">
                  <svg className="h-5 w-5 animate-spin" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  Hikaye Oluşturuluyor...
                </span>
              ) : selectedStyle ? (
                <span className="flex items-center gap-2">
                  <Sparkles className="h-5 w-5" />
                  Hikayeyi Oluştur
                  <ChevronRight className="h-5 w-5" />
                </span>
              ) : (
                "Bir Stil Seçin"
              )}
            </Button>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
