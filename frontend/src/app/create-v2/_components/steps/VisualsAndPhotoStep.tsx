"use client";

import { useState, useCallback, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import Image from "next/image";
import {
  Camera,
  Upload,
  X,
  CheckCircle2,
  ShieldCheck,
  Sparkles,
  ImageIcon,
} from "lucide-react";
import StickyCTA from "../StickyCTA";
import type { VisualStyle } from "@/lib/api";
import { MAX_PHOTO_SIZE_BYTES, ACCEPTED_IMAGE_TYPES } from "../../_lib/constants";

/* ── Props ── */
interface VisualsAndPhotoStepProps {
  childName: string;
  photoPreview: string;
  faceDetected: boolean;
  isAnalyzing: boolean;
  onPhotoSelect: (file: File) => void;
  onClear: () => void;
  onAnalyze: () => void;
  visualStyles: VisualStyle[];
  selectedStyle: string;
  onStyleSelect: (id: string) => void;
  onBack: () => void;
  onSubmit: () => void;
  isSubmitting: boolean;
}

/* ── Main Component ── */
export default function VisualsAndPhotoStep({
  childName,
  photoPreview,
  faceDetected,
  isAnalyzing,
  onPhotoSelect,
  onClear,
  onAnalyze,
  visualStyles,
  selectedStyle,
  onStyleSelect,
  onBack,
  onSubmit,
  isSubmitting,
}: VisualsAndPhotoStepProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [dragActive, setDragActive] = useState(false);

  // Photo must be uploaded AND analyzed (face detected) before continuing
  const canContinue = !!selectedStyle && !isSubmitting && faceDetected;

  const handleFileChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (!file) return;
      if (!ACCEPTED_IMAGE_TYPES.includes(file.type)) return;
      if (file.size > MAX_PHOTO_SIZE_BYTES) return;
      onPhotoSelect(file);
    },
    [onPhotoSelect],
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragActive(false);
      const file = e.dataTransfer.files[0];
      if (!file || !ACCEPTED_IMAGE_TYPES.includes(file.type)) return;
      if (file.size > MAX_PHOTO_SIZE_BYTES) return;
      onPhotoSelect(file);
    },
    [onPhotoSelect],
  );

  return (
    <div className="pb-24 space-y-5">
      {/* ── Header ── */}
      <header>
        <p className="text-[10px] sm:text-xs font-bold text-violet-500 uppercase tracking-wider mb-0.5">
          Adım 2
        </p>
        <h2 className="text-lg sm:text-xl font-bold text-slate-800">
          Fotoğraf & İllüstrasyon Stili
        </h2>
        <p className="text-xs sm:text-sm text-slate-500 mt-1">
          {childName
            ? `${childName}'ın fotoğrafını yükleyin ve kitabın illüstrasyon stilini seçin.`
            : "Çocuğunuzun fotoğrafını yükleyin ve illüstrasyon stilini seçin."}
        </p>
      </header>

      {/* ── Section A: Photo Upload ── */}
      <section className="rounded-2xl border border-slate-100 bg-white shadow-sm overflow-hidden">
        <div className="px-4 pt-3.5 pb-2.5 border-b border-slate-50 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Camera className="h-4 w-4 text-violet-500" />
            <span className="text-sm font-semibold text-slate-700">Çocuğun Fotoğrafı</span>
          </div>
          <span className="text-[10px] text-red-500 bg-red-50 px-2 py-0.5 rounded-full font-medium">
            Zorunlu
          </span>
        </div>

        <div className="p-4">
          {photoPreview ? (
            /* Photo uploaded state */
            <div className="space-y-3">
              <div className="relative mx-auto w-48 sm:w-56">
                {/* Polaroid frame */}
                <div className="relative rounded-xl bg-white shadow-lg p-2 pb-3 border border-slate-100">
                  <div className="relative aspect-square rounded-lg overflow-hidden bg-slate-100">
                    <Image
                      src={photoPreview}
                      alt={`${childName || "Çocuk"} fotoğrafı`}
                      fill
                      className="object-cover"
                      sizes="224px"
                    />
                    {/* Face detection overlay */}
                    <AnimatePresence>
                      {faceDetected && (
                        <motion.div
                          initial={{ opacity: 0, scale: 0.8 }}
                          animate={{ opacity: 1, scale: 1 }}
                          className="absolute inset-0 flex items-center justify-center"
                        >
                          <div className="absolute inset-4 rounded-lg border-2 border-emerald-400/60" />
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                  {/* Name label under photo */}
                  <p className="text-center text-xs text-slate-500 mt-2 font-medium">
                    {childName || "Küçük Kahraman"}
                  </p>
                </div>

                {/* Remove button */}
                <button
                  type="button"
                  onClick={onClear}
                  className="absolute -top-2 -right-2 flex h-7 w-7 items-center justify-center rounded-full bg-red-500 text-white shadow-md transition-transform hover:scale-110"
                  aria-label="Fotoğrafı kaldır"
                >
                  <X className="h-3.5 w-3.5" />
                </button>
              </div>

              {/* Analysis status */}
              <div className="text-center">
                {faceDetected ? (
                  <motion.div
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="inline-flex items-center gap-1.5 rounded-full bg-emerald-50 px-3 py-1.5 text-xs font-semibold text-emerald-700"
                  >
                    <CheckCircle2 className="h-3.5 w-3.5" />
                    Yüz başarıyla tespit edildi
                  </motion.div>
                ) : isAnalyzing ? (
                  <div className="inline-flex items-center gap-2 text-xs text-violet-600">
                    <div className="h-4 w-4 animate-spin rounded-full border-2 border-violet-600 border-t-transparent" />
                    Fotoğraf analiz ediliyor...
                  </div>
                ) : (
                  <motion.button
                    type="button"
                    whileTap={{ scale: 0.97 }}
                    onClick={onAnalyze}
                    className="inline-flex items-center gap-1.5 rounded-xl bg-violet-600 px-4 py-2 text-xs font-bold text-white shadow-md shadow-violet-200 transition-all hover:bg-violet-700"
                  >
                    <Sparkles className="h-3.5 w-3.5" />
                    Fotoğrafı Analiz Et
                  </motion.button>
                )}
              </div>
            </div>
          ) : (
            /* Upload area */
            <div
              onDragOver={(e) => {
                e.preventDefault();
                setDragActive(true);
              }}
              onDragLeave={() => setDragActive(false)}
              onDrop={handleDrop}
              className={`
                relative flex flex-col items-center justify-center rounded-2xl border-2 border-dashed p-6 sm:p-8 transition-all cursor-pointer
                ${dragActive
                  ? "border-violet-400 bg-violet-50"
                  : "border-slate-200 bg-slate-50/50 hover:border-violet-300 hover:bg-violet-50/30"
                }
              `}
              onClick={() => fileInputRef.current?.click()}
              role="button"
              tabIndex={0}
              aria-label="Fotoğraf yükle"
            >
              <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-violet-100 text-violet-500 mb-3">
                <Upload className="h-6 w-6" />
              </div>
              <p className="text-sm font-semibold text-slate-700 mb-1">
                Fotoğraf yükleyin
              </p>
              <p className="text-xs text-slate-400 text-center">
                Sürükleyip bırakın veya tıklayın · JPG, PNG, WEBP · Max 10 MB
              </p>

              {/* Hidden file input */}
              <input
                ref={fileInputRef}
                type="file"
                accept="image/jpeg,image/png,image/webp"
                capture="environment"
                onChange={handleFileChange}
                className="hidden"
              />
            </div>
          )}

          {/* KVKK notice */}
          <div className="mt-3 flex items-start gap-2 rounded-xl bg-blue-50/50 p-2.5 text-[11px] text-blue-600">
            <ShieldCheck className="h-3.5 w-3.5 flex-shrink-0 mt-0.5" />
            <span>
              Fotoğraflar yalnızca illüstrasyon için kullanılır.
              Teslimat sonrası 30 gün içinde otomatik silinir (KVKK).
            </span>
          </div>
        </div>
      </section>



      {/* ── Section B: Style Selection ── */}
      <section className="rounded-2xl border border-slate-100 bg-white shadow-sm overflow-hidden">
        <div className="px-4 pt-3.5 pb-2.5 border-b border-slate-50 flex items-center gap-2">
          <ImageIcon className="h-4 w-4 text-violet-500" />
          <span className="text-sm font-semibold text-slate-700">İllüstrasyon Stili</span>
        </div>

        <div className="p-4">
          {visualStyles.length === 0 ? (
            /* Skeleton loading */
            <div className="grid grid-cols-2 gap-3">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="animate-pulse rounded-xl bg-slate-100 aspect-[4/5]" />
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-2 gap-3">
              {visualStyles.map((style, idx) => {
                const isSelected = selectedStyle === style.id;
                return (
                  <motion.button
                    key={style.id}
                    type="button"
                    initial={{ opacity: 0, y: 12 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: idx * 0.05 }}
                    whileTap={{ scale: 0.97 }}
                    onClick={() => onStyleSelect(style.id)}
                    className={`
                      relative flex flex-col overflow-hidden rounded-xl border-2 transition-all text-left
                      ${isSelected
                        ? "border-violet-500 bg-violet-50/30 shadow-md shadow-violet-100 ring-1 ring-violet-300"
                        : "border-slate-100 bg-white hover:border-slate-200 hover:shadow-sm"
                      }
                    `}
                  >
                    {/* Style preview image */}
                    <div className="relative aspect-[4/3] w-full overflow-hidden bg-slate-100">
                      {style.thumbnail_url ? (
                        <Image
                          src={style.thumbnail_url}
                          alt={style.display_name || style.name}
                          fill
                          className="object-cover"
                          sizes="(max-width: 640px) 50vw, 250px"
                        />
                      ) : (
                        <div className="flex h-full items-center justify-center text-slate-300">
                          <ImageIcon className="h-8 w-8" />
                        </div>
                      )}

                      {/* Selected checkmark */}
                      {isSelected && (
                        <motion.div
                          initial={{ scale: 0 }}
                          animate={{ scale: 1 }}
                          className="absolute top-2 right-2 flex h-6 w-6 items-center justify-center rounded-full bg-violet-600 text-white shadow-md"
                        >
                          <CheckCircle2 className="h-4 w-4" />
                        </motion.div>
                      )}
                    </div>

                    {/* Style name */}
                    <div className="p-2.5">
                      <p className={`text-xs font-semibold ${isSelected ? "text-violet-700" : "text-slate-700"}`}>
                        {style.display_name || style.name}
                      </p>
                    </div>
                  </motion.button>
                );
              })}
            </div>
          )}
        </div>
      </section>

      {/* ── StickyCTA ── */}
      <StickyCTA
        primaryLabel={isSubmitting ? "Kitap Üretiliyor..." : "Kitabı Oluştur ✨"}
        onPrimary={onSubmit}
        primaryDisabled={!canContinue}
        primaryLoading={isSubmitting}
        secondaryLabel="← Geri"
        onSecondary={onBack}
      />
    </div>
  );
}
