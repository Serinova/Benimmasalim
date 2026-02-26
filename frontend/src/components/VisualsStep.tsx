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
} from "lucide-react";
import type { VisualStyle } from "@/lib/api";

interface VisualsStepProps {
    childName: string;
    // Photo
    photoPreview: string;
    faceDetected: boolean;
    isAnalyzing: boolean;
    onPhotoSelect: (file: File) => void;
    onClear: () => void;
    onAnalyze: () => Promise<void>;
    // Style
    visualStyles: VisualStyle[];
    selectedStyle: string;
    customIdWeight: number | null;
    onStyleSelect: (id: string) => void;
    onIdWeightChange: (v: number | null) => void;
    // Nav
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
    const canSubmit = selectedStyle && (!photoPreview || (photoPreview && kvkkConsent) || !photoPreview);
    const hasPhoto = !!photoPreview;

    const scrollStyles = (dir: "left" | "right") => {
        scrollRef.current?.scrollBy({ left: dir === "left" ? -200 : 200, behavior: "smooth" });
    };

    return (
        <div className="space-y-4 px-1 pt-2 pb-4">

            {/* ── Header ── */}
            <div>
                <p className="text-xs font-semibold text-purple-500 uppercase tracking-wider mb-1">📸 Fotoğraf & Stil</p>
                <h2 className="text-xl font-bold text-gray-800 leading-tight">
                    {childName
                        ? <><span className="text-purple-600">{childName}</span>&apos;ı Kitabın İçine Alalım</>
                        : "Görsel Ayarlar"}
                </h2>
                <p className="text-sm text-gray-400 mt-0.5">Fotoğraf isteğe bağlı — stil zorunlu</p>
            </div>

            {/* ── Photo Upload Card ── */}
            <div className="rounded-2xl border-2 border-gray-100 bg-white shadow-sm overflow-hidden">
                <div className="px-4 pt-4 pb-3 border-b border-gray-50">
                    <p className="text-sm font-semibold text-gray-700 flex items-center gap-2">
                        <Camera className="h-4 w-4 text-purple-500" />
                        Fotoğraf Yükle
                        <span className="ml-auto text-xs font-normal text-gray-400 bg-gray-100 rounded-full px-2 py-0.5">İsteğe bağlı</span>
                    </p>
                </div>

                <div className="p-4">
                    {!hasPhoto ? (
                        /* Drop zone */
                        <div
                            {...getRootProps()}
                            className={`
                relative flex flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed cursor-pointer transition-all p-6
                ${isDragActive
                                    ? "border-purple-400 bg-purple-50"
                                    : "border-gray-200 bg-gray-50 hover:border-purple-300 hover:bg-purple-50/50"
                                }
              `}
                        >
                            <input {...getInputProps()} />
                            <div className={`w-12 h-12 rounded-full flex items-center justify-center ${isDragActive ? "bg-purple-500 text-white" : "bg-purple-100 text-purple-600"}`}>
                                <Upload className="h-6 w-6" />
                            </div>
                            <div className="text-center">
                                <p className="text-sm font-semibold text-gray-700">
                                    {isDragActive ? "Bırakın!" : "Fotoğraf Yükle"}
                                </p>
                                <p className="text-xs text-gray-400 mt-0.5">JPG, PNG, WebP · Maks 10MB</p>
                            </div>
                            <div className="flex items-center gap-3 mt-1 text-xs text-gray-400">
                                <span className="flex items-center gap-1">☀️ Aydınlık</span>
                                <span className="flex items-center gap-1">👁️ Tam yüz</span>
                                <span className="flex items-center gap-1">🔍 Net</span>
                            </div>
                        </div>
                    ) : (
                        /* Photo preview */
                        <div className="flex items-start gap-4">
                            <div className="relative w-24 h-24 flex-shrink-0 rounded-xl overflow-hidden border-2 border-purple-200 shadow-sm">
                                <img src={photoPreview} alt="Yüklenen fotoğraf" className="w-full h-full object-cover" />
                                {isAnalyzing && (
                                    <div className="absolute inset-0 bg-black/40 flex items-center justify-center">
                                        <motion.div animate={{ rotate: 360 }} transition={{ duration: 1, repeat: Infinity, ease: "linear" }}>
                                            <Sparkles className="h-6 w-6 text-white" />
                                        </motion.div>
                                    </div>
                                )}
                                {faceDetected && !isAnalyzing && (
                                    <div className="absolute inset-0 bg-green-500/20 flex items-end justify-center pb-1">
                                        <CheckCircle2 className="h-5 w-5 text-green-600" />
                                    </div>
                                )}
                            </div>

                            <div className="flex-1 space-y-2">
                                {faceDetected ? (
                                    <div className="flex items-center gap-2 rounded-xl bg-green-50 border border-green-200 px-3 py-2">
                                        <CheckCircle2 className="h-4 w-4 text-green-600 flex-shrink-0" />
                                        <p className="text-xs font-semibold text-green-700">Yüz başarıyla tespit edildi!</p>
                                    </div>
                                ) : isAnalyzing ? (
                                    <div className="flex items-center gap-2 rounded-xl bg-purple-50 border border-purple-200 px-3 py-2">
                                        <motion.div animate={{ rotate: 360 }} transition={{ duration: 1, repeat: Infinity, ease: "linear" }}>
                                            <Sparkles className="h-4 w-4 text-purple-600" />
                                        </motion.div>
                                        <p className="text-xs font-semibold text-purple-700">Analiz ediliyor...</p>
                                    </div>
                                ) : (
                                    <button
                                        onClick={onAnalyze}
                                        className="w-full flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-purple-600 to-pink-500 text-white text-sm font-semibold py-2.5"
                                    >
                                        <Sparkles className="h-4 w-4" />
                                        Fotoğrafı Analiz Et
                                    </button>
                                )}

                                <button
                                    onClick={onClear}
                                    className="w-full flex items-center justify-center gap-2 rounded-xl border border-gray-200 text-gray-500 text-xs font-medium py-2"
                                >
                                    <Trash2 className="h-3.5 w-3.5" />
                                    Değiştir
                                </button>
                            </div>
                        </div>
                    )}

                    {/* KVKK Consent — shows only after photo is uploaded */}
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
            </div>

            {/* ── Style Selector Card ── */}
            <div className="rounded-2xl border-2 border-gray-100 bg-white shadow-sm overflow-hidden">
                <div className="px-4 pt-4 pb-3 border-b border-gray-50 flex items-center justify-between">
                    <p className="text-sm font-semibold text-gray-700 flex items-center gap-2">
                        🎨 Görsel Stil
                        <span className="text-xs font-normal text-red-400 bg-red-50 rounded-full px-2 py-0.5">Zorunlu</span>
                    </p>
                    {selectedStyleObj && (
                        <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-xs font-semibold text-purple-600">
                            ✓ {selectedStyleObj.display_name || selectedStyleObj.name}
                        </motion.p>
                    )}
                </div>

                <div className="p-4 space-y-3">
                    {/* Style Carousel */}
                    <div className="relative">
                        <button onClick={() => scrollStyles("left")} className="absolute left-0 top-1/2 -translate-y-1/2 z-10 w-7 h-7 rounded-full bg-white shadow border border-gray-100 items-center justify-center hidden md:flex">
                            <ChevronLeft className="h-3.5 w-3.5 text-gray-600" />
                        </button>
                        <div
                            ref={scrollRef}
                            className="flex gap-2.5 overflow-x-auto pb-2 px-0.5"
                            style={{ scrollSnapType: "x mandatory", WebkitOverflowScrolling: "touch", scrollbarWidth: "none" }}
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
                                        transition={{ delay: i * 0.04 }}
                                        whileTap={{ scale: 0.97 }}
                                        onClick={() => onStyleSelect(style.id)}
                                        className={`
                      flex-shrink-0 rounded-xl overflow-hidden text-left transition-all
                      ${isSelected ? "ring-2 ring-purple-500 shadow-lg shadow-purple-100" : "shadow-sm"}
                    `}
                                        style={{ width: "120px", scrollSnapAlign: "start" }}
                                    >
                                        <div className="relative h-28 bg-gradient-to-br from-purple-200 to-pink-200">
                                            {style.thumbnail_url
                                                ? <img src={style.thumbnail_url} alt={displayName} className="h-full w-full object-cover" />
                                                : <div className="h-full w-full flex items-center justify-center text-3xl">🎨</div>
                                            }
                                            {isSelected && (
                                                <div className="absolute inset-0 bg-purple-600/20 flex items-center justify-center">
                                                    <div className="w-8 h-8 rounded-full bg-purple-600 flex items-center justify-center shadow">
                                                        <CheckCircle2 className="h-5 w-5 text-white" />
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                        <div className={`px-2 py-2 ${isSelected ? "bg-purple-50" : "bg-white"}`}>
                                            <p className={`text-xs font-semibold leading-tight truncate ${isSelected ? "text-purple-700" : "text-gray-700"}`}>
                                                {displayName}
                                            </p>
                                        </div>
                                    </motion.button>
                                );
                            })}
                        </div>
                        <button onClick={() => scrollStyles("right")} className="absolute right-0 top-1/2 -translate-y-1/2 z-10 w-7 h-7 rounded-full bg-white shadow border border-gray-100 items-center justify-center hidden md:flex">
                            <ChevronRight className="h-3.5 w-3.5 text-gray-600" />
                        </button>
                    </div>
                    <p className="text-center text-[11px] text-gray-400">← Kaydırarak daha fazla stil gör →</p>

                    {/* Advanced */}
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
                                            <span className="font-semibold text-gray-600">🪪 Yüz Benzerliği</span>
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
                        onClick={() => canSubmit && onSubmit()}
                        disabled={!canSubmit || isSubmitting}
                        className={`
              h-14 flex-1 rounded-2xl font-bold text-base transition-all duration-200 flex items-center justify-center gap-2
              ${canSubmit && !isSubmitting
                                ? "bg-gradient-to-r from-purple-600 to-pink-500 text-white shadow-lg shadow-purple-200"
                                : "bg-gray-100 text-gray-400 cursor-not-allowed"
                            }
            `}
                    >
                        {isSubmitting ? (
                            <>
                                <motion.div animate={{ rotate: 360 }} transition={{ duration: 1, repeat: Infinity, ease: "linear" }}>
                                    <Sparkles className="h-5 w-5" />
                                </motion.div>
                                <span>Hazırlanıyor...</span>
                            </>
                        ) : (
                            <>
                                <span>Kitabı Oluştur 🪄</span>
                            </>
                        )}
                    </motion.button>
                </div>
            </div>
        </div>
    );
}
