"use client";

import { useState, useCallback, useRef } from "react";
import { useDropzone } from "react-dropzone";
import { motion, AnimatePresence } from "framer-motion";
import {
    Camera,
    Upload,
    Trash2,
    Sparkles,
    CheckCircle2,
    Shield,
    ChevronRight,
    ChevronLeft,
    Settings2,
    Loader2,
} from "lucide-react";
import type { VisualStyle } from "@/lib/api";

interface VisualsStepProps {
    childName: string;
    photoPreview: string;
    faceDetected: boolean;
    isAnalyzing: boolean;
    onPhotoSelect: (file: File) => void;
    onClear: () => void;
    onAnalyze: () => Promise<void>;
    visualStyles: VisualStyle[];
    selectedStyle: string;
    customIdWeight: number | null;
    onStyleSelect: (id: string) => void;
    onIdWeightChange: (v: number | null) => void;
    onBack: () => void;
    onSubmit: () => void;
    isSubmitting: boolean;
}

export default function VisualsStep({
    childName,
    photoPreview,
    faceDetected,
    isAnalyzing,
    onPhotoSelect,
    onClear,
    onAnalyze,
    visualStyles,
    selectedStyle,
    customIdWeight,
    onStyleSelect,
    onIdWeightChange,
    onBack,
    onSubmit,
    isSubmitting,
}: VisualsStepProps) {
    const [showAdvanced, setShowAdvanced] = useState(false);
    const [kvkkConsent, setKvkkConsent] = useState(false);
    const scrollRef = useRef<HTMLDivElement>(null);

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop: useCallback((files: File[]) => {
            if (files[0]) onPhotoSelect(files[0]);
        }, [onPhotoSelect]),
        accept: { "image/jpeg": [".jpg", ".jpeg"], "image/png": [".png"], "image/webp": [".webp"] },
        maxSize: 10 * 1024 * 1024,
        multiple: false,
    });

    const selectedStyleObj = visualStyles.find(s => s.id === selectedStyle);
    const canSubmit = !!(selectedStyle && photoPreview && faceDetected && kvkkConsent);
    const hasPhoto = !!photoPreview;

    const scrollStyles = (dir: "left" | "right") => {
        scrollRef.current?.scrollBy({ left: dir === "left" ? -200 : 200, behavior: "smooth" });
    };

    const ctaLabel = !photoPreview
        ? "Önce Fotoğraf Yükle"
        : !faceDetected
            ? "Fotoğrafı Analiz Et"
            : !kvkkConsent
                ? "KVKK Onayı Gerekli"
                : !selectedStyle
                    ? "Görsel Stil Seçin"
                    : "Kitabımı Oluştur";

    return (
        <div className="space-y-5 sm:space-y-6">

            {/* ── Photo Upload Card ── */}
            <section
                aria-label="Fotoğraf yükleme"
                className="rounded-2xl border border-gray-100 bg-white shadow-sm overflow-hidden"
            >
                <div className="px-4 pt-3.5 pb-2.5 border-b border-gray-50 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <Camera className="h-4 w-4 text-purple-500" />
                        <span className="text-sm font-semibold text-gray-700">Fotoğraf Yükle</span>
                    </div>
                    <span className="text-[10px] font-medium text-red-500 bg-red-50 rounded-full px-2 py-0.5">Zorunlu</span>
                </div>

                <div className="p-3.5 sm:p-4">
                    {!hasPhoto ? (
                        <div
                            {...getRootProps()}
                            className={`
                                relative flex flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed cursor-pointer transition-all
                                py-8 sm:py-10
                                ${isDragActive
                                    ? "border-purple-400 bg-purple-50"
                                    : "border-gray-200 bg-gray-50/80 hover:border-purple-300 hover:bg-purple-50/50 active:bg-purple-50"}
                            `}
                        >
                            <input {...getInputProps()} />
                            <div className={`w-14 h-14 sm:w-16 sm:h-16 rounded-2xl flex items-center justify-center transition-colors ${isDragActive ? "bg-purple-500 text-white" : "bg-purple-100 text-purple-600"}`}>
                                <Upload className="h-6 w-6 sm:h-7 sm:w-7" />
                            </div>
                            <div className="text-center px-4">
                                <p className="text-sm sm:text-base font-semibold text-gray-700">
                                    {isDragActive ? "Bırakın!" : "Fotoğraf Yükle"}
                                </p>
                                <p className="text-xs text-gray-400 mt-1">JPG, PNG, WebP · Maks 10MB</p>
                            </div>
                            <div className="flex items-center gap-4 mt-1 text-xs text-gray-400">
                                <span>☀️ Aydınlık</span>
                                <span>👁️ Tam yüz</span>
                                <span>🔍 Net</span>
                            </div>
                        </div>
                    ) : (
                        <div className="flex items-start gap-3 sm:gap-4">
                            <div className="relative w-20 h-20 sm:w-24 sm:h-24 flex-shrink-0 rounded-xl overflow-hidden border-2 border-purple-200 shadow-sm">
                                <img src={photoPreview} alt="Yüklenen fotoğraf" className="w-full h-full object-cover" />
                                {isAnalyzing && (
                                    <div className="absolute inset-0 bg-black/40 flex items-center justify-center">
                                        <Loader2 className="h-6 w-6 text-white animate-spin" />
                                    </div>
                                )}
                                {faceDetected && !isAnalyzing && (
                                    <div className="absolute bottom-1 right-1">
                                        <CheckCircle2 className="h-5 w-5 text-green-500 drop-shadow" />
                                    </div>
                                )}
                            </div>

                            <div className="flex-1 min-w-0 space-y-2">
                                {faceDetected ? (
                                    <div className="flex items-center gap-2 rounded-xl bg-green-50 border border-green-200 px-3 py-2.5">
                                        <CheckCircle2 className="h-4 w-4 text-green-600 flex-shrink-0" />
                                        <p className="text-xs sm:text-sm font-semibold text-green-700">Yüz başarıyla tespit edildi!</p>
                                    </div>
                                ) : isAnalyzing ? (
                                    <div className="flex items-center gap-2 rounded-xl bg-purple-50 border border-purple-200 px-3 py-2.5">
                                        <Loader2 className="h-4 w-4 text-purple-600 animate-spin flex-shrink-0" />
                                        <p className="text-xs sm:text-sm font-semibold text-purple-700">Yüz analiz ediliyor...</p>
                                    </div>
                                ) : (
                                    <button
                                        type="button"
                                        onClick={onAnalyze}
                                        className="w-full flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-purple-600 to-pink-500 text-white text-sm font-semibold py-2.5 active:scale-[0.98] transition-transform"
                                    >
                                        <Sparkles className="h-4 w-4" />
                                        Fotoğrafı Analiz Et
                                    </button>
                                )}

                                <button
                                    type="button"
                                    onClick={onClear}
                                    className="w-full flex items-center justify-center gap-2 rounded-xl border border-gray-200 text-gray-500 text-xs font-medium py-2 hover:bg-gray-50 active:bg-gray-100 transition-colors"
                                >
                                    <Trash2 className="h-3.5 w-3.5" />
                                    Değiştir
                                </button>
                            </div>
                        </div>
                    )}

                    {/* KVKK Consent */}
                    <AnimatePresence>
                        {hasPhoto && (
                            <motion.div
                                initial={{ opacity: 0, height: 0 }}
                                animate={{ opacity: 1, height: "auto" }}
                                exit={{ opacity: 0, height: 0 }}
                                className="overflow-hidden"
                            >
                                <div className="mt-3 rounded-xl bg-gray-50 border border-gray-100 p-3">
                                    <label className="flex items-start gap-2.5 cursor-pointer">
                                        <input
                                            type="checkbox"
                                            checked={kvkkConsent}
                                            onChange={e => setKvkkConsent(e.target.checked)}
                                            className="mt-0.5 h-4 w-4 rounded accent-purple-600 flex-shrink-0"
                                        />
                                        <span className="text-xs text-gray-600 leading-relaxed">
                                            Fotoğrafın <strong>sadece hikaye oluşturmak</strong> için kullanılacağını,
                                            işlem sonrası silineceğini kabul ediyorum.{" "}
                                            <a href="/kvkk" target="_blank" className="text-purple-600 underline">KVKK</a>
                                        </span>
                                    </label>
                                    <div className="mt-2 flex items-center gap-3 text-[10px] text-gray-400">
                                        <span className="flex items-center gap-1"><Shield className="h-3 w-3" /> KVKK Uyumlu</span>
                                        <span>· SSL Şifreli</span>
                                        <span>· 30 Gün Sonra Silme</span>
                                    </div>
                                </div>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>
            </section>

            {/* ── Style Selector Card ── */}
            <section
                aria-label="Görsel stil seçimi"
                className="rounded-2xl border border-gray-100 bg-white shadow-sm overflow-hidden"
            >
                <div className="px-4 pt-3.5 pb-2.5 border-b border-gray-50 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <span className="text-sm">🎨</span>
                        <span className="text-sm font-semibold text-gray-700">Görsel Stil</span>
                        <span className="text-[10px] font-medium text-red-500 bg-red-50 rounded-full px-2 py-0.5">Zorunlu</span>
                    </div>
                    {selectedStyleObj && (
                        <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-xs font-semibold text-purple-600 truncate max-w-[120px]">
                            ✓ {selectedStyleObj.display_name || selectedStyleObj.name}
                        </motion.p>
                    )}
                </div>

                <div className="p-3.5 sm:p-4 space-y-3">
                    {/* Style Grid — mobile: 2-col grid, desktop: scrollable row */}
                    <div className="relative">
                        <button
                            type="button"
                            onClick={() => scrollStyles("left")}
                            className="absolute left-0 top-1/2 -translate-y-1/2 z-10 w-8 h-8 rounded-full bg-white/90 shadow-md border border-gray-100 items-center justify-center hidden lg:flex hover:bg-white"
                        >
                            <ChevronLeft className="h-4 w-4 text-gray-600" />
                        </button>

                        {/* Mobile: 2-col grid */}
                        <div className="grid grid-cols-2 gap-2.5 sm:hidden">
                            {visualStyles.map((style) => {
                                const isSelected = selectedStyle === style.id;
                                const displayName = style.display_name || style.name;
                                return (
                                    <motion.button
                                        key={style.id}
                                        type="button"
                                        whileTap={{ scale: 0.97 }}
                                        onClick={() => onStyleSelect(style.id)}
                                        className={`
                                            rounded-xl overflow-hidden text-left transition-all
                                            ${isSelected ? "ring-2 ring-purple-500 shadow-lg shadow-purple-100" : "border border-gray-100 shadow-sm"}
                                        `}
                                    >
                                        <div className="relative aspect-[4/3] bg-gradient-to-br from-purple-100 to-pink-100">
                                            {style.thumbnail_url ? (
                                                <img src={style.thumbnail_url} alt={displayName} loading="lazy" className="h-full w-full object-cover" />
                                            ) : (
                                                <div className="h-full w-full flex items-center justify-center text-3xl">🎨</div>
                                            )}
                                            {isSelected && (
                                                <div className="absolute inset-0 bg-purple-600/20 flex items-center justify-center">
                                                    <div className="w-7 h-7 rounded-full bg-purple-600 flex items-center justify-center shadow">
                                                        <CheckCircle2 className="h-4 w-4 text-white" />
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                        <div className={`px-2.5 py-2 ${isSelected ? "bg-purple-50" : "bg-white"}`}>
                                            <p className={`text-xs font-semibold leading-tight truncate ${isSelected ? "text-purple-700" : "text-gray-700"}`}>
                                                {displayName}
                                            </p>
                                        </div>
                                    </motion.button>
                                );
                            })}
                        </div>

                        {/* Desktop: horizontal scroll */}
                        <div
                            ref={scrollRef}
                            className="hidden sm:flex gap-3 overflow-x-auto pb-2 px-0.5 scrollbar-hide"
                            style={{ scrollSnapType: "x mandatory", WebkitOverflowScrolling: "touch" }}
                        >
                            {visualStyles.map((style, i) => {
                                const isSelected = selectedStyle === style.id;
                                const displayName = style.display_name || style.name;
                                return (
                                    <motion.button
                                        key={style.id}
                                        type="button"
                                        initial={{ opacity: 0, x: 16 }}
                                        animate={{ opacity: 1, x: 0 }}
                                        transition={{ delay: i * 0.03 }}
                                        whileTap={{ scale: 0.97 }}
                                        onClick={() => onStyleSelect(style.id)}
                                        className={`
                                            flex-shrink-0 w-[140px] rounded-xl overflow-hidden text-left transition-all
                                            ${isSelected ? "ring-2 ring-purple-500 shadow-lg shadow-purple-100" : "border border-gray-100 shadow-sm"}
                                        `}
                                        style={{ scrollSnapAlign: "start" }}
                                    >
                                        <div className="relative h-28 bg-gradient-to-br from-purple-100 to-pink-100">
                                            {style.thumbnail_url ? (
                                                <img src={style.thumbnail_url} alt={displayName} loading="lazy" className="h-full w-full object-cover" />
                                            ) : (
                                                <div className="h-full w-full flex items-center justify-center text-3xl">🎨</div>
                                            )}
                                            {isSelected && (
                                                <div className="absolute inset-0 bg-purple-600/20 flex items-center justify-center">
                                                    <div className="w-8 h-8 rounded-full bg-purple-600 flex items-center justify-center shadow">
                                                        <CheckCircle2 className="h-5 w-5 text-white" />
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                        <div className={`px-2.5 py-2 ${isSelected ? "bg-purple-50" : "bg-white"}`}>
                                            <p className={`text-xs font-semibold leading-tight truncate ${isSelected ? "text-purple-700" : "text-gray-700"}`}>
                                                {displayName}
                                            </p>
                                        </div>
                                    </motion.button>
                                );
                            })}
                        </div>

                        <button
                            type="button"
                            onClick={() => scrollStyles("right")}
                            className="absolute right-0 top-1/2 -translate-y-1/2 z-10 w-8 h-8 rounded-full bg-white/90 shadow-md border border-gray-100 items-center justify-center hidden lg:flex hover:bg-white"
                        >
                            <ChevronRight className="h-4 w-4 text-gray-600" />
                        </button>
                    </div>

                    <p className="text-center text-[11px] text-gray-400 hidden sm:block">← Kaydırarak daha fazla stil gör →</p>

                    {/* Advanced settings */}
                    <div>
                        <button
                            type="button"
                            onClick={() => setShowAdvanced(!showAdvanced)}
                            className="flex items-center gap-1.5 text-xs text-gray-400 hover:text-purple-600 transition-colors font-medium"
                        >
                            <Settings2 className="h-3.5 w-3.5" />
                            Gelişmiş Ayarlar
                            <span className={`transition-transform text-[10px] ${showAdvanced ? "rotate-180" : ""}`}>▾</span>
                        </button>
                        <AnimatePresence>
                            {showAdvanced && (
                                <motion.div
                                    initial={{ height: 0, opacity: 0 }}
                                    animate={{ height: "auto", opacity: 1 }}
                                    exit={{ height: 0, opacity: 0 }}
                                    className="overflow-hidden"
                                >
                                    <div className="mt-2 rounded-xl border border-gray-100 bg-gray-50 px-3 py-3 space-y-2">
                                        <div className="flex justify-between text-xs">
                                            <span className="font-semibold text-gray-600">Yüz Benzerliği</span>
                                            <span className="text-purple-600 font-bold">
                                                {customIdWeight !== null ? `${Math.round(customIdWeight * 100)}%` : "Varsayılan"}
                                            </span>
                                        </div>
                                        <input
                                            type="range" min={0} max={1} step={0.05}
                                            value={customIdWeight ?? (selectedStyleObj?.id_weight ?? 0.7)}
                                            onChange={e => onIdWeightChange(parseFloat(e.target.value))}
                                            className="w-full accent-purple-600"
                                        />
                                        <div className="flex justify-between text-[10px] text-gray-400">
                                            <span>Çizgisel</span><span>Gerçekçi</span>
                                        </div>
                                    </div>
                                </motion.div>
                            )}
                        </AnimatePresence>
                    </div>
                </div>
            </section>

            {/* ── Sticky Bottom CTA ── */}
            <motion.div
                initial={{ opacity: 0, y: 40 }}
                animate={{ opacity: 1, y: 0 }}
                className="fixed bottom-0 left-0 right-0 z-50 bg-white/95 backdrop-blur-md border-t border-gray-100 px-3 sm:px-4 py-2.5 sm:py-3"
                style={{ paddingBottom: "max(0.625rem, env(safe-area-inset-bottom))" }}
            >
                <div className="mx-auto flex max-w-lg gap-2 sm:gap-3">
                    <button
                        type="button"
                        onClick={onBack}
                        className="h-11 sm:h-12 px-3 sm:px-5 rounded-xl border-2 border-gray-200 text-gray-600 font-semibold text-sm flex items-center transition-colors hover:bg-gray-50 active:bg-gray-100"
                    >
                        ← Geri
                    </button>
                    <motion.button
                        type="button"
                        whileTap={canSubmit && !isSubmitting ? { scale: 0.97 } : undefined}
                        onClick={() => canSubmit && onSubmit()}
                        disabled={!canSubmit || isSubmitting}
                        className={`
                            h-11 sm:h-12 flex-1 rounded-xl font-bold text-sm sm:text-base transition-all flex items-center justify-center gap-2
                            ${canSubmit && !isSubmitting
                                ? "bg-gradient-to-r from-purple-600 to-pink-500 text-white shadow-lg shadow-purple-200"
                                : "bg-gray-200 text-gray-400 cursor-not-allowed shadow-none"}
                        `}
                    >
                        {isSubmitting ? (
                            <>
                                <Loader2 className="h-5 w-5 animate-spin" />
                                <span>Hazırlanıyor...</span>
                            </>
                        ) : (
                            <span>{ctaLabel}</span>
                        )}
                    </motion.button>
                </div>
            </motion.div>
        </div>
    );
}
