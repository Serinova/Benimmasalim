"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { BookOpen, Mail, RefreshCw, Package, Palette, ChevronLeft, ChevronRight } from "lucide-react";
import type { GenerationProgress } from "@/lib/api";

interface GenerationWaitingModalProps {
    progress?: GenerationProgress | null;
    isVisible: boolean;
}

/* Info slides shown during book generation */
const INFO_SLIDES = [
    {
        icon: Mail,
        title: "E-posta Onayı",
        description: "Siparişiniz tamamlandığında onay e-postası gönderilecek. E-postanızdaki butona tıklayarak siparişinizi kontrol edebilirsiniz.",
        color: "bg-blue-50 text-blue-600",
    },
    {
        icon: RefreshCw,
        title: "Yeniden Yazdırma Hakkı",
        description: "Görsellerden memnun kalmazsanız 4 kez ücretsiz yeniden yazdırma hakkınız var. Her seferinde farklı sonuçlar alabilirsiniz.",
        color: "bg-emerald-50 text-emerald-600",
    },
    {
        icon: Package,
        title: "Hızlı Teslimat",
        description: "Kitabınız özenle basılıp 3-5 iş gününde adresinize teslim edilecek. Kargo takip numarası e-posta ile paylaşılacak.",
        color: "bg-amber-50 text-amber-600",
    },
    {
        icon: Palette,
        title: "Her Sayfa Özel",
        description: "Kitabınızdaki her sayfa, yapay zeka tarafından çocuğunuzun yüz özelliklerine uygun olarak özel olarak tasarlanıyor.",
        color: "bg-indigo-50 text-indigo-600",
    },
];

const SLIDE_INTERVAL = 5000; // 5 seconds per slide

export default function GenerationWaitingModal({ progress, isVisible }: GenerationWaitingModalProps) {
    const [currentSlide, setCurrentSlide] = useState(0);
    const [simulatedPercent, setSimulatedPercent] = useState(3);
    const lastRealPercent = useRef(0);

    // Auto-advance slides
    useEffect(() => {
        if (!isVisible) return;
        const timer = setInterval(() => {
            setCurrentSlide((prev) => (prev + 1) % INFO_SLIDES.length);
        }, SLIDE_INTERVAL);
        return () => clearInterval(timer);
    }, [isVisible]);

    /* Compute the real progress from backend */
    const getRealPercent = useCallback((): number => {
        if (!progress) return 3;
        const { current_page, total_pages, stage } = progress;
        switch (stage) {
            case "queued":
                return 3;
            case "generating_story":
                return 8;
            case "story_ready":
                return 18;
            case "generating_images":
                if (total_pages <= 0) return 20;
                return Math.min(20 + (current_page / total_pages) * 55, 75);
            case "composing":
                return 80;
            case "uploading":
                return 92;
            default:
                return 5;
        }
    }, [progress]);

    /* Simulated progress: creep forward slowly even when backend hasn't responded */
    useEffect(() => {
        if (!isVisible) return;
        const realPercent = getRealPercent();

        // If real percent jumped ahead, catch up immediately
        if (realPercent > simulatedPercent) {
            setSimulatedPercent(realPercent);
            lastRealPercent.current = realPercent;
            return;
        }
        lastRealPercent.current = realPercent;

        // Slow drift: add ~0.3% every 800ms, but never exceed the next stage threshold
        const maxDrift = realPercent + 8; // don't exceed 8% past last known real
        const interval = setInterval(() => {
            setSimulatedPercent((prev) => {
                if (prev >= maxDrift) return prev;
                if (prev >= 95) return prev; // never exceed 95
                return prev + 0.3;
            });
        }, 800);
        return () => clearInterval(interval);
    }, [isVisible, progress, getRealPercent, simulatedPercent]);

    // Reset simulated progress when visibility changes
    useEffect(() => {
        if (isVisible) {
            setSimulatedPercent(3);
        }
    }, [isVisible]);

    const getStageMessage = (): string => {
        if (!progress) return "Sihirli sayfalar hazırlanıyor...";
        const { current_page, total_pages, stage } = progress;
        switch (stage) {
            case "queued":
                return "Sıranız bekleniyor...";
            case "generating_story":
                return "Hikaye oluşturuluyor... 📝";
            case "story_ready":
                return "Hikaye hazır, görseller başlıyor... 🎨";
            case "generating_images":
                return current_page > 0
                    ? `Sayfa ${current_page}/${total_pages} çiziliyor ✨`
                    : `Görseller oluşturuluyor (0/${total_pages})...`;
            case "composing":
                return "Sayfalar tasarlanıyor... 🖌️";
            case "uploading":
                return "Son dokunuşlar yapılıyor... ✅";
            default:
                return "Sihirli sayfalar hazırlanıyor...";
        }
    };

    const goToSlide = useCallback((index: number) => {
        setCurrentSlide(Math.max(0, Math.min(index, INFO_SLIDES.length - 1)));
    }, []);

    const goNext = useCallback(() => {
        setCurrentSlide((prev) => (prev + 1) % INFO_SLIDES.length);
    }, []);

    const goPrev = useCallback(() => {
        setCurrentSlide((prev) => (prev - 1 + INFO_SLIDES.length) % INFO_SLIDES.length);
    }, []);

    const percent = Math.round(simulatedPercent);
    const message = getStageMessage();
    const slide = INFO_SLIDES[currentSlide];
    const SlideIcon = slide.icon;

    if (!isVisible) return null;

    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-[70] flex flex-col items-center justify-center bg-[#fafaf9] px-4"
        >
            {/* Top section — Book animation + Progress */}
            <div className="flex w-full max-w-md flex-col items-center">
                {/* Animated book icon */}
                <motion.div
                    animate={{ rotateZ: [0, 2, -2, 0], y: [0, -4, 0] }}
                    transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
                    className="mb-6 flex h-20 w-20 items-center justify-center rounded-3xl bg-indigo-50"
                    style={{ boxShadow: "0 8px 32px rgba(99,102,241,0.12)" }}
                >
                    <BookOpen className="h-9 w-9 text-indigo-600" />
                </motion.div>

                {/* Title */}
                <h2 className="mb-1.5 text-center text-xl font-bold tracking-tight text-stone-800 sm:text-2xl">
                    Kitabınız Hazırlanıyor
                </h2>
                <AnimatePresence mode="wait">
                    <motion.p
                        key={message}
                        initial={{ opacity: 0, y: 4 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -4 }}
                        transition={{ duration: 0.3 }}
                        className="text-center text-sm text-stone-500"
                    >
                        {message}
                    </motion.p>
                </AnimatePresence>

                {/* Progress bar */}
                <div className="mt-5 w-full max-w-sm">
                    <div className="h-2.5 w-full overflow-hidden rounded-full bg-stone-100">
                        <motion.div
                            className="h-full rounded-full bg-indigo-600"
                            initial={{ width: "0%" }}
                            animate={{ width: `${percent}%` }}
                            transition={{ duration: 0.8, ease: "easeOut" }}
                        />
                    </div>
                    <div className="mt-1.5 flex items-center justify-between">
                        <motion.p
                            key={percent}
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            className="text-xs font-semibold text-indigo-600"
                        >
                            %{percent}
                        </motion.p>
                        <p className="text-[10px] text-stone-400">Bu işlem 1-3 dk sürebilir</p>
                    </div>
                </div>
            </div>

            {/* Info carousel card */}
            <div
                className="mx-auto mt-8 w-full max-w-md overflow-hidden rounded-2xl bg-white sm:mt-10"
                style={{ boxShadow: "0 4px 24px rgba(0,0,0,0.08)" }}
            >
                <AnimatePresence mode="wait">
                    <motion.div
                        key={currentSlide}
                        initial={{ opacity: 0, x: 30 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: -30 }}
                        transition={{ duration: 0.3, ease: [0.25, 0.1, 0.25, 1] }}
                        className="p-6 sm:p-8"
                    >
                        <div className={`mb-4 inline-flex h-12 w-12 items-center justify-center rounded-2xl ${slide.color}`}>
                            <SlideIcon className="h-6 w-6" />
                        </div>
                        <h3 className="mb-2 text-lg font-bold text-stone-800">{slide.title}</h3>
                        <p className="leading-relaxed text-sm text-stone-500">
                            {slide.description}
                        </p>
                    </motion.div>
                </AnimatePresence>

                {/* Carousel navigation */}
                <div className="flex items-center justify-between border-t border-stone-100 px-5 py-3">
                    <button
                        type="button"
                        onClick={goPrev}
                        className="flex h-8 w-8 items-center justify-center rounded-full text-stone-400 transition-colors hover:bg-stone-50 hover:text-stone-600"
                    >
                        <ChevronLeft className="h-4 w-4" />
                    </button>

                    {/* Dots */}
                    <div className="flex gap-2">
                        {INFO_SLIDES.map((_, i) => (
                            <button
                                key={i}
                                type="button"
                                onClick={() => goToSlide(i)}
                                className={`h-2 rounded-full transition-all duration-300 ${i === currentSlide
                                    ? "w-6 bg-indigo-600"
                                    : "w-2 bg-stone-200 hover:bg-stone-300"
                                    }`}
                                aria-label={`Slayt ${i + 1}`}
                            />
                        ))}
                    </div>

                    <button
                        type="button"
                        onClick={goNext}
                        className="flex h-8 w-8 items-center justify-center rounded-full text-stone-400 transition-colors hover:bg-stone-50 hover:text-stone-600"
                    >
                        <ChevronRight className="h-4 w-4" />
                    </button>
                </div>
            </div>

            {/* Bottom hint */}
            <motion.p
                animate={{ opacity: [0.4, 0.7, 0.4] }}
                transition={{ duration: 3, repeat: Infinity }}
                className="mt-6 text-center text-xs text-stone-400"
            >
                Lütfen sayfayı kapatmayın ·{" "}
                <span className="font-medium text-stone-500">Kitabınız emin ellerde</span> 📖
            </motion.p>
        </motion.div>
    );
}
