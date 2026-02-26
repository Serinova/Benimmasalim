"use client";

import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Mic,
  Headphones,
  BookX,
  Play,
  Pause,
  Volume2,
  Sparkles,
  Star,
  ChevronLeft,
  ChevronRight,
  QrCode,
  Check,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import VoiceRecorderStep from "@/components/VoiceRecorderStep";

type AudioOption = "none" | "system" | "cloned";
type SystemVoiceType = "female" | "male";

interface AudioSelectionStepProps {
  hideNavButtons?: boolean;
  childName: string;
  basePrice: number;
  selectedOption: AudioOption;
  systemVoice: SystemVoiceType;
  clonedVoiceId: string | null;
  isCloningVoice?: boolean;
  onOptionChange: (option: AudioOption) => void;
  onSystemVoiceChange: (voice: SystemVoiceType) => void;
  onVoiceRecorded: (audioBase64: string) => void;
  onContinue: () => void;
  onBack: () => void;
  // Test mode - bypass checkout
  isTestMode?: boolean;
  onTestSubmit?: (email: string) => void;
  isSubmitting?: boolean;
}

// Animated Waveform Visualizer
function WaveformVisualizer({ isPlaying }: { isPlaying: boolean }) {
  const bars = 20;

  return (
    <div className="flex h-12 items-center justify-center gap-[3px] px-4">
      {[...Array(bars)].map((_, i) => (
        <motion.div
          key={i}
          className="w-1 rounded-full bg-gradient-to-t from-purple-500 to-pink-400"
          animate={
            isPlaying
              ? {
                  height: [Math.random() * 20 + 8, Math.random() * 40 + 12, Math.random() * 20 + 8],
                }
              : { height: 8 }
          }
          transition={{
            duration: 0.4 + Math.random() * 0.3,
            repeat: isPlaying ? Infinity : 0,
            ease: "easeInOut",
            delay: i * 0.05,
          }}
          style={{ height: 8 }}
        />
      ))}
    </div>
  );
}

// Audio Player Component
function AudioPlayer({
  label,
  isActive,
  onToggle,
}: {
  label: string;
  isActive: boolean;
  onToggle: () => void;
}) {
  return (
    <button
      onClick={onToggle}
      className={`
        flex w-full items-center gap-3 rounded-xl px-4 py-3 transition-all
        ${
          isActive
            ? "bg-purple-100 text-purple-700 shadow-inner"
            : "bg-gray-100 text-gray-600 hover:bg-gray-200"
        }
      `}
    >
      <motion.div
        animate={{ scale: isActive ? [1, 1.2, 1] : 1 }}
        transition={{ duration: 0.5, repeat: isActive ? Infinity : 0 }}
        className={`flex h-10 w-10 items-center justify-center rounded-full ${
          isActive ? "bg-purple-600 text-white" : "bg-white shadow"
        }`}
      >
        {isActive ? <Pause className="h-5 w-5" /> : <Play className="ml-0.5 h-5 w-5" />}
      </motion.div>
      <span className="text-sm font-medium">{label}</span>
      {isActive && (
        <div className="ml-auto">
          <Volume2 className="h-4 w-4 animate-pulse" />
        </div>
      )}
    </button>
  );
}

// Option Card Component
function OptionCard({
  id,
  icon: Icon,
  title,
  description,
  price,
  isSelected,
  isRecommended,
  isPremium,
  onSelect,
  children,
}: {
  id: AudioOption;
  icon: React.ElementType;
  title: string;
  description: string;
  price: number;
  isSelected: boolean;
  isRecommended?: boolean;
  isPremium?: boolean;
  onSelect: () => void;
  children?: React.ReactNode;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -4 }}
      transition={{ duration: 0.3 }}
      onClick={onSelect}
      className={`
        relative cursor-pointer overflow-hidden rounded-2xl transition-all
        ${isPremium ? "z-10 md:-my-2 md:scale-105" : ""}
        ${
          isSelected
            ? isPremium
              ? "shadow-2xl shadow-purple-500/30 ring-4 ring-purple-500 ring-offset-2"
              : "shadow-lg ring-2 ring-purple-400 ring-offset-2"
            : "shadow-md hover:shadow-xl"
        }
      `}
    >
      {/* Recommended Badge */}
      {isRecommended && (
        <div className="absolute right-0 top-0 z-20">
          <div className="flex items-center gap-1.5 rounded-bl-xl bg-gradient-to-r from-amber-400 to-orange-500 px-4 py-1.5 text-xs font-bold text-white">
            <Star className="h-3 w-3 fill-current" />
            ÖNERİLEN
          </div>
        </div>
      )}

      {/* Background */}
      <div
        className={`
          absolute inset-0 
          ${
            isPremium
              ? "bg-gradient-to-br from-purple-900 via-purple-800 to-indigo-900"
              : id === "none"
                ? "bg-gradient-to-br from-gray-100 to-gray-200"
                : "bg-gradient-to-br from-white to-purple-50"
          }
        `}
      />

      {/* Glow effect for premium */}
      {isPremium && (
        <div className="absolute inset-0 overflow-hidden">
          <motion.div
            animate={{
              x: ["-100%", "100%"],
              opacity: [0, 0.3, 0],
            }}
            transition={{
              duration: 3,
              repeat: Infinity,
              ease: "linear",
            }}
            className="absolute inset-0 bg-gradient-to-r from-transparent via-purple-400 to-transparent"
          />
        </div>
      )}

      {/* Content */}
      <div className={`relative p-4 ${isPremium ? "text-white" : ""}`}>
        {/* Icon */}
        <div
          className={`
          mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-xl
          ${
            isPremium
              ? "bg-gradient-to-br from-amber-400 to-orange-500 shadow-lg shadow-amber-500/30"
              : id === "none"
                ? "bg-gray-200"
                : "bg-purple-100"
          }
        `}
        >
          <Icon
            className={`h-8 w-8 ${isPremium ? "text-white" : id === "none" ? "text-gray-500" : "text-purple-600"}`}
          />
        </div>

        {/* Title & Description */}
        <h3
          className={`mb-2 text-center text-xl font-bold ${isPremium ? "text-white" : id === "none" ? "text-gray-600" : "text-gray-800"}`}
        >
          {title}
        </h3>
        <p
          className={`mb-4 text-center text-sm ${isPremium ? "text-purple-200" : "text-gray-500"}`}
        >
          {description}
        </p>

        {/* Price Tag */}
        <div
          className={`
          mb-4 text-center 
          ${
            isPremium
              ? "rounded-xl bg-white/10 py-3 backdrop-blur"
              : id === "none"
                ? "rounded-xl bg-gray-100 py-3"
                : "rounded-xl bg-purple-100 py-3"
          }
        `}
        >
          {price === 0 ? (
            <span className={`text-lg font-semibold ${id === "none" ? "text-gray-500" : ""}`}>
              Ücretsiz
            </span>
          ) : (
            <div className="flex items-baseline justify-center gap-1">
              <span
                className={`text-3xl font-bold ${isPremium ? "text-amber-400" : "text-purple-600"}`}
              >
                +{price}
              </span>
              <span className={`text-sm ${isPremium ? "text-purple-200" : "text-gray-500"}`}>
                TL
              </span>
            </div>
          )}
        </div>

        {/* Selection Indicator */}
        <div
          className={`
          flex items-center justify-center gap-2 rounded-lg py-2 transition-all
          ${
            isSelected
              ? isPremium
                ? "bg-white/20 text-white"
                : "bg-purple-600 text-white"
              : isPremium
                ? "bg-white/10 text-purple-200"
                : "bg-gray-100 text-gray-500"
          }
        `}
        >
          {isSelected ? (
            <>
              <Check className="h-4 w-4" />
              <span className="text-sm font-medium">Seçildi</span>
            </>
          ) : (
            <span className="text-sm">Seçmek için tıklayın</span>
          )}
        </div>

        {/* Extra Content (Audio Players) */}
        {children && <div className="mt-4 border-t border-white/10 pt-4">{children}</div>}
      </div>
    </motion.div>
  );
}

// Voice Recording Full-Screen Overlay
function VoiceRecordOverlay({
  isOpen,
  childName,
  onClose,
  onRecordingComplete,
  isProcessing,
}: {
  isOpen: boolean;
  childName: string;
  onClose: () => void;
  onRecordingComplete: (audioBase64: string) => void;
  isProcessing: boolean;
}) {
  // Processing overlay
  if (isProcessing) {
    return (
      <AnimatePresence>
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-[100] flex items-center justify-center"
          style={{
            background: "linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%)",
          }}
        >
          <div className="text-center">
            <div className="relative mx-auto mb-6 h-20 w-20">
              <div className="absolute inset-0 rounded-full border-4 border-purple-400/30" />
              <div className="absolute inset-0 animate-spin rounded-full border-4 border-purple-500 border-t-transparent" />
              <div className="absolute inset-2 rounded-full border-4 border-pink-400/30" />
              <div
                className="absolute inset-2 animate-spin rounded-full border-4 border-pink-500 border-t-transparent"
                style={{ animationDirection: "reverse" }}
              />
            </div>
            <h4 className="mb-3 text-2xl font-bold text-white">Sesiniz Klonlanıyor...</h4>
            <p className="mx-auto max-w-sm text-purple-200">
              Yapay zeka sesinizi öğreniyor. Bu işlem 30-60 saniye sürebilir.
            </p>

            {/* Progress dots */}
            <div className="mt-6 flex items-center justify-center gap-2">
              {[0, 1, 2].map((i) => (
                <motion.div
                  key={i}
                  animate={{ opacity: [0.3, 1, 0.3] }}
                  transition={{ duration: 1.5, repeat: Infinity, delay: i * 0.3 }}
                  className="h-2 w-2 rounded-full bg-purple-400"
                />
              ))}
            </div>
          </div>
        </motion.div>
      </AnimatePresence>
    );
  }

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-[100] overflow-auto"
        >
          <VoiceRecorderStep
            childName={childName}
            onRecordingComplete={onRecordingComplete}
            onBack={onClose}
            minDurationSeconds={30}
            maxDurationSeconds={90}
          />
        </motion.div>
      )}
    </AnimatePresence>
  );
}

export default function AudioSelectionStep({
  childName,
  basePrice,
  selectedOption,
  systemVoice,
  clonedVoiceId,
  isCloningVoice = false,
  onOptionChange,
  onSystemVoiceChange,
  onVoiceRecorded,
  onContinue,
  onBack,
  isTestMode = false,
  onTestSubmit,
  isSubmitting = false,
}: AudioSelectionStepProps) {
  const [playingAudio, setPlayingAudio] = useState<string | null>(null);
  const [showRecordModal, setShowRecordModal] = useState(false);
  const [testEmail, setTestEmail] = useState("");
  const audioRef = useRef<HTMLAudioElement>(null);

  // Calculate total price
  const getAddonPrice = () => {
    switch (selectedOption) {
      case "system":
        return 150;
      case "cloned":
        return 300;
      default:
        return 0;
    }
  };
  const totalPrice = basePrice + getAddonPrice();

  // Handle audio playback
  const handlePlayAudio = (audioId: string) => {
    if (playingAudio === audioId) {
      setPlayingAudio(null);
      // Stop audio
    } else {
      setPlayingAudio(audioId);
      // Play audio (mock)
    }
  };

  // Auto-stop audio after 5 seconds (demo)
  useEffect(() => {
    if (playingAudio) {
      const timer = setTimeout(() => setPlayingAudio(null), 5000);
      return () => clearTimeout(timer);
    }
  }, [playingAudio]);

  return (
    <div className="relative min-h-[80vh] pb-28">
      {/* Background */}
      <div
        className="fixed inset-0 z-0"
        style={{
          background: "linear-gradient(135deg, #1e1b4b 0%, #312e81 50%, #3730a3 100%)",
        }}
      >
        {/* Sound wave pattern overlay */}
        <div className="absolute inset-0 opacity-5">
          <svg className="h-full w-full" viewBox="0 0 1440 800" preserveAspectRatio="none">
            <path
              d="M0,400 Q360,300 720,400 T1440,400 V800 H0 Z"
              fill="currentColor"
              className="text-white"
            />
          </svg>
        </div>

        {/* Floating particles */}
        {[...Array(20)].map((_, i) => (
          <motion.div
            key={i}
            className="absolute h-1 w-1 rounded-full bg-purple-400 opacity-30"
            animate={{
              y: [0, -100, 0],
              x: [0, Math.sin(i) * 20, 0],
              opacity: [0.2, 0.5, 0.2],
            }}
            transition={{
              duration: 5 + i * 0.5,
              repeat: Infinity,
              delay: i * 0.3,
            }}
            style={{
              left: `${(i / 20) * 100}%`,
              top: `${50 + Math.sin(i * 2) * 30}%`,
            }}
          />
        ))}
      </div>

      {/* Content */}
      <div className="relative z-10 px-4 py-4">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-6 text-center"
        >
          <div className="mb-2 flex items-center justify-center gap-3">
            <motion.div
              animate={{ rotate: [0, 10, -10, 0] }}
              transition={{ duration: 2, repeat: Infinity }}
            >
              <Volume2 className="h-6 w-6 text-purple-400" />
            </motion.div>
          </div>

          <h1 className="mb-2 text-2xl font-bold text-white md:text-3xl">Masalı Kim Anlatsın?</h1>
          <p className="mx-auto max-w-lg text-sm text-purple-200/80">
            Kitabın arkasındaki QR kodu okutunca masal başlar
          </p>

          {/* QR Code illustration */}
          <motion.div
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: 0.3 }}
            className="mt-3 inline-flex items-center gap-2 rounded-xl bg-white/10 px-4 py-2 backdrop-blur"
          >
            <QrCode className="h-6 w-6 text-white" />
            <div className="text-left">
              <p className="text-sm font-medium text-white">QR Kod ile Dinle</p>
              <p className="text-xs text-purple-300">Telefon kamerasıyla taratın</p>
            </div>
          </motion.div>
        </motion.div>

        {/* Options Grid */}
        <div className="mx-auto grid max-w-4xl grid-cols-1 gap-4 md:grid-cols-3 md:items-start md:gap-3">
          {/* Option 1: No Audio */}
          <OptionCard
            id="none"
            icon={BookX}
            title="Sadece Kitap"
            description="Sesli kitap özelliği olmadan basılı kitap"
            price={0}
            isSelected={selectedOption === "none"}
            onSelect={() => onOptionChange("none")}
          />

          {/* Option 2: System Voice */}
          <OptionCard
            id="system"
            icon={Headphones}
            title="Profesyonel Masalcı"
            description="Pedagojik eğitimli seslendirmenler"
            price={150}
            isSelected={selectedOption === "system"}
            onSelect={() => onOptionChange("system")}
          >
            {selectedOption === "system" && (
              <div className="space-y-3">
                {/* Voice Selection */}
                <div className="grid grid-cols-2 gap-2">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onSystemVoiceChange("female");
                    }}
                    className={`rounded-xl p-3 text-center transition-all ${
                      systemVoice === "female"
                        ? "bg-purple-600 text-white shadow-lg"
                        : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                    }`}
                  >
                    <span className="mb-1 block text-2xl">👩</span>
                    <span className="text-xs font-medium">Ayşe Teyze</span>
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onSystemVoiceChange("male");
                    }}
                    className={`rounded-xl p-3 text-center transition-all ${
                      systemVoice === "male"
                        ? "bg-purple-600 text-white shadow-lg"
                        : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                    }`}
                  >
                    <span className="mb-1 block text-2xl">👨</span>
                    <span className="text-xs font-medium">Mert Amca</span>
                  </button>
                </div>

                {/* Audio Player */}
                <div onClick={(e) => e.stopPropagation()}>
                  <AudioPlayer
                    label={systemVoice === "female" ? "Ayşe Teyze'yi Dinle" : "Mert Amca'yı Dinle"}
                    isActive={playingAudio === "system"}
                    onToggle={() => handlePlayAudio("system")}
                  />
                </div>

                {/* Waveform */}
                <AnimatePresence>
                  {playingAudio === "system" && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: "auto" }}
                      exit={{ opacity: 0, height: 0 }}
                      className="overflow-hidden rounded-xl bg-purple-50"
                    >
                      <WaveformVisualizer isPlaying={true} />
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            )}
          </OptionCard>

          {/* Option 3: Cloned Voice (Premium) */}
          <OptionCard
            id="cloned"
            icon={Mic}
            title="Sizin Sesinizle Sonsuza Kadar"
            description="Yapay zeka sesinizi kopyalar. Siz evde yokken bile çocuğunuz masalı sizin sesinizden dinler."
            price={300}
            isSelected={selectedOption === "cloned"}
            isRecommended={true}
            isPremium={true}
            onSelect={() => onOptionChange("cloned")}
          >
            {selectedOption === "cloned" && (
              <div className="space-y-3">
                {/* Voice Status */}
                {clonedVoiceId ? (
                  <motion.div
                    initial={{ scale: 0.9 }}
                    animate={{ scale: 1 }}
                    className="rounded-xl border border-green-400/30 bg-green-500/20 p-4 text-center"
                  >
                    <div className="mb-2 flex items-center justify-center gap-2 text-green-400">
                      <Check className="h-5 w-5" />
                      <span className="font-bold">Sesiniz Hazır!</span>
                    </div>
                    <p className="text-xs text-green-300/80">Masallar sizin sesinizle okunacak</p>
                  </motion.div>
                ) : (
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={(e) => {
                      e.stopPropagation();
                      setShowRecordModal(true);
                    }}
                    className="flex w-full items-center justify-center gap-3 rounded-xl bg-gradient-to-r from-amber-500 to-orange-500 px-6 py-4 font-semibold text-white shadow-lg shadow-amber-500/30"
                  >
                    <Mic className="h-5 w-5" />
                    <span>Sesimi Kaydet</span>
                  </motion.button>
                )}

                {/* Demo Player */}
                <div onClick={(e) => e.stopPropagation()}>
                  <AudioPlayer
                    label="Örnek Klonlanmış Ses"
                    isActive={playingAudio === "cloned"}
                    onToggle={() => handlePlayAudio("cloned")}
                  />
                </div>

                {/* Waveform */}
                <AnimatePresence>
                  {playingAudio === "cloned" && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: "auto" }}
                      exit={{ opacity: 0, height: 0 }}
                      className="overflow-hidden rounded-xl bg-white/10"
                    >
                      <WaveformVisualizer isPlaying={true} />
                    </motion.div>
                  )}
                </AnimatePresence>

                {/* Features */}
                <div className="grid grid-cols-2 gap-2 pt-2">
                  {[
                    { icon: "🎯", text: "AI Ses Klonlama" },
                    { icon: "♾️", text: "Sınırsız Dinleme" },
                    { icon: "❤️", text: "Ebedi Hatıra" },
                    { icon: "📱", text: "QR ile Kolay" },
                  ].map((feature, i) => (
                    <div key={i} className="flex items-center gap-2 text-xs text-purple-200/80">
                      <span>{feature.icon}</span>
                      <span>{feature.text}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </OptionCard>
        </div>

        {/* Emotional Appeal Banner */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="mx-auto mt-10 max-w-2xl"
        >
          <div className="rounded-2xl border border-amber-400/30 bg-gradient-to-r from-amber-500/20 to-orange-500/20 p-6 text-center backdrop-blur">
            <Sparkles className="mx-auto mb-3 h-8 w-8 text-amber-400" />
            <p className="mb-2 font-medium text-white">
              &ldquo;{childName} büyüdüğünde bile sesinizi duyabilecek&rdquo;
            </p>
            <p className="text-sm text-purple-200/70">
              Yapay zeka teknolojisi ile sesiniz sonsuza kadar korunur
            </p>
          </div>
        </motion.div>
      </div>

      {/* Sticky Footer */}
      <div className="fixed bottom-0 left-0 right-0 z-50">
        <div
          className="px-4 pb-6 pt-6"
          style={{
            background:
              "linear-gradient(to top, rgba(30,27,75,0.98) 0%, rgba(30,27,75,0.95) 70%, transparent 100%)",
          }}
        >
          <div className="mx-auto max-w-xl">
            {/* Price Summary */}
            <div className="mb-4 rounded-2xl bg-white/10 p-4 backdrop-blur">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-purple-200/70">Toplam Tutar</p>
                  <div className="flex items-baseline gap-2">
                    <span className="text-3xl font-bold text-white">{totalPrice}</span>
                    <span className="text-purple-200">TL</span>
                  </div>
                </div>
                <div className="text-right text-sm">
                  <p className="text-purple-200/70">Kitap: {basePrice} TL</p>
                  {getAddonPrice() > 0 && (
                    <p className="text-amber-400">Sesli Kitap: +{getAddonPrice()} TL</p>
                  )}
                </div>
              </div>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-4">
              <Button
                variant="ghost"
                onClick={onBack}
                className="text-purple-200 hover:bg-white/10 hover:text-white"
              >
                <ChevronLeft className="mr-1 h-4 w-4" />
                Geri
              </Button>

              {/* Test Mode: Email Input + Direct Order Button */}
              {isTestMode && onTestSubmit ? (
                <div className="flex flex-1 flex-col gap-2">
                  <div className="flex gap-2">
                    <input
                      type="email"
                      placeholder="E-posta adresinizi girin..."
                      value={testEmail}
                      onChange={(e) => setTestEmail(e.target.value)}
                      className="flex-1 rounded-xl border border-white/20 bg-white/10 px-4 py-3 text-white placeholder-purple-300/50 focus:border-purple-400 focus:outline-none focus:ring-2 focus:ring-purple-400/30"
                    />
                    <motion.button
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      onClick={() => {
                        if (!testEmail || !testEmail.includes("@")) {
                          alert("Lütfen geçerli bir e-posta adresi girin!");
                          return;
                        }
                        onTestSubmit(testEmail);
                      }}
                      disabled={isSubmitting || !testEmail}
                      className="flex items-center justify-center gap-2 whitespace-nowrap rounded-xl bg-gradient-to-r from-green-500 to-emerald-500 px-6 py-3 font-semibold text-white shadow-lg shadow-green-500/30 disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      {isSubmitting ? (
                        <>
                          <div className="h-5 w-5 animate-spin rounded-full border-2 border-white border-t-transparent" />
                          <span>Gönderiliyor...</span>
                        </>
                      ) : (
                        <>
                          <Sparkles className="h-5 w-5" />
                          <span>Gönder</span>
                        </>
                      )}
                    </motion.button>
                  </div>
                </div>
              ) : (
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={onContinue}
                  className="flex flex-1 items-center justify-center gap-3 rounded-xl bg-gradient-to-r from-purple-500 to-pink-500 px-8 py-4 font-semibold text-white shadow-lg shadow-purple-500/30"
                >
                  <span>Devam Et</span>
                  <ChevronRight className="h-5 w-5" />
                </motion.button>
              )}
            </div>

            {/* Test Mode Indicator */}
            {isTestMode && (
              <div className="mt-3 text-center">
                <span className="rounded-full bg-amber-500/20 px-3 py-1 text-xs text-amber-400">
                  🧪 Test Modu: Ödeme adımı atlanacak
                </span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Hidden Audio Element */}
      <audio ref={audioRef} className="hidden" />

      {/* Voice Recording Studio Overlay */}
      <VoiceRecordOverlay
        isOpen={showRecordModal}
        childName={childName}
        onClose={() => setShowRecordModal(false)}
        onRecordingComplete={(audioBase64) => {
          setShowRecordModal(false);
          onVoiceRecorded(audioBase64);
        }}
        isProcessing={isCloningVoice}
      />
    </div>
  );
}
