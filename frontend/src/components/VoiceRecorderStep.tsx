"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Mic,
  MicOff,
  Square,
  Play,
  Pause,
  RotateCcw,
  Check,
  ChevronLeft,
  Volume2,
  Sparkles,
} from "lucide-react";
import { Button } from "@/components/ui/button";

interface VoiceRecorderStepProps {
  childName: string;
  onRecordingComplete: (audioBase64: string) => void;
  onBack: () => void;
  minDurationSeconds?: number;
  maxDurationSeconds?: number;
}

type RecordingState = "idle" | "countdown" | "recording" | "paused" | "review";

// Sample text to read
const SAMPLE_TEXT = `Bir varmış bir yokmuş, evvel zaman içinde, kalbur saman içinde, develer tellal iken, pireler berber iken...

Uras adında cesur bir çocuk yaşarmış. Bu çocuk yıldızların arasında gezinmeyi çok severmiş. Her gece gökyüzüne bakıp hayaller kurarmış.

Bir gün penceresinden parlak bir ışık gördü. Bu ışık onu büyülü bir maceraya davet ediyordu...`;

// Recording Tips
const TIPS = [
  { icon: "🤫", text: "Sessiz bir oda" },
  { icon: "🎤", text: "Telefonu yakın tutun" },
  { icon: "🗣️", text: "Tane tane konuşun" },
  { icon: "😊", text: "Doğal olun" },
];

// Audio Visualizer Component with real-time levels
function AudioVisualizer({ isActive, audioLevel }: { isActive: boolean; audioLevel: number }) {
  const bars = 32;

  return (
    <div className="flex h-24 items-end justify-center gap-1 px-4">
      {[...Array(bars)].map((_, i) => {
        // Create a wave pattern based on position and audio level
        const centerDistance = Math.abs(i - bars / 2) / (bars / 2);
        const baseHeight = isActive ? 8 + (1 - centerDistance) * audioLevel * 60 : 8;
        const randomVariation = isActive ? Math.sin(Date.now() / 100 + i) * audioLevel * 10 : 0;

        return (
          <motion.div
            key={i}
            className="w-1.5 rounded-full"
            style={{
              background: isActive
                ? `linear-gradient(to top, #ef4444, #f97316, #eab308)`
                : "rgba(255,255,255,0.2)",
            }}
            animate={{
              height: Math.max(8, baseHeight + randomVariation),
              opacity: isActive ? 0.8 + audioLevel * 0.2 : 0.3,
            }}
            transition={{
              duration: 0.05,
              ease: "linear",
            }}
          />
        );
      })}
    </div>
  );
}

// Countdown Overlay
function CountdownOverlay({ count }: { count: number }) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm"
    >
      <motion.div
        key={count}
        initial={{ scale: 0.5, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 1.5, opacity: 0 }}
        transition={{ duration: 0.5 }}
        className="relative"
      >
        {/* Pulsing ring */}
        <motion.div
          animate={{ scale: [1, 1.5, 1], opacity: [0.5, 0, 0.5] }}
          transition={{ duration: 1, repeat: Infinity }}
          className="absolute inset-0 -m-8 h-40 w-40 rounded-full border-4 border-red-500"
        />

        <div className="flex h-24 w-24 items-center justify-center rounded-full bg-gradient-to-br from-red-500 to-orange-500 shadow-2xl shadow-red-500/50">
          <span className="text-5xl font-bold text-white">{count}</span>
        </div>
      </motion.div>

      <motion.p
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="absolute bottom-1/3 text-lg text-white/80"
      >
        Hazır olun...
      </motion.p>
    </motion.div>
  );
}

// Confetti Effect
function ConfettiEffect() {
  const particles = 50;
  const colors = ["#ef4444", "#f97316", "#eab308", "#22c55e", "#3b82f6", "#8b5cf6", "#ec4899"];

  return (
    <div className="pointer-events-none fixed inset-0 z-50 overflow-hidden">
      {[...Array(particles)].map((_, i) => (
        <motion.div
          key={i}
          initial={{
            x: "50vw",
            y: "50vh",
            scale: 0,
            rotate: 0,
          }}
          animate={{
            x: `${Math.random() * 100}vw`,
            y: `${Math.random() * 100}vh`,
            scale: [0, 1, 0.5],
            rotate: Math.random() * 720 - 360,
          }}
          transition={{
            duration: 2 + Math.random(),
            ease: "easeOut",
          }}
          className="absolute h-3 w-3 rounded-sm"
          style={{
            backgroundColor: colors[i % colors.length],
          }}
        />
      ))}
    </div>
  );
}

// Recording Ring Animation
function RecordingRing({ isRecording }: { isRecording: boolean }) {
  return (
    <>
      {/* Outer pulsing ring */}
      {isRecording && (
        <motion.div
          animate={{ scale: [1, 1.15, 1], opacity: [0.3, 0.1, 0.3] }}
          transition={{ duration: 1.5, repeat: Infinity }}
          className="absolute inset-0 rounded-full border-4 border-red-500"
        />
      )}
      {/* Second ring */}
      {isRecording && (
        <motion.div
          animate={{ scale: [1, 1.3, 1], opacity: [0.2, 0, 0.2] }}
          transition={{ duration: 2, repeat: Infinity, delay: 0.5 }}
          className="absolute inset-0 rounded-full border-2 border-red-400"
        />
      )}
    </>
  );
}

export default function VoiceRecorderStep({
  childName: _childName,
  onRecordingComplete,
  onBack,
  minDurationSeconds = 30,
  maxDurationSeconds = 90,
}: VoiceRecorderStepProps) {
  // Recording state
  const [recordingState, setRecordingState] = useState<RecordingState>("idle");
  const [recordingTime, setRecordingTime] = useState(0);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [audioBase64, setAudioBase64] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [permissionGranted, setPermissionGranted] = useState(false);
  const [audioLevel, setAudioLevel] = useState(0);
  const [countdownValue, setCountdownValue] = useState(3);
  const [showConfetti, setShowConfetti] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);

  // Refs
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const animationFrameRef = useRef<number | null>(null);

  // Request microphone permission on mount
  useEffect(() => {
    const checkPermission = async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          audio: {
            echoCancellation: true,
            noiseSuppression: true,
            sampleRate: 44100,
          },
        });
        streamRef.current = stream;
        setPermissionGranted(true);

        // Setup audio analyser for visualization
        const AudioContextClass =
          window.AudioContext ||
          (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
        const audioContext = new AudioContextClass();
        const analyser = audioContext.createAnalyser();
        const source = audioContext.createMediaStreamSource(stream);

        analyser.fftSize = 256;
        source.connect(analyser);

        audioContextRef.current = audioContext;
        analyserRef.current = analyser;
      } catch (err) {
        setError("Mikrofon erişimi reddedildi. Lütfen tarayıcı ayarlarından izin verin.");
        setPermissionGranted(false);
      }
    };

    checkPermission();

    return () => {
      // Cleanup
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
      }
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
      if (audioContextRef.current) {
        audioContextRef.current.close();
      }
    };
  }, []);

  // Audio level monitoring
  const updateAudioLevel = useCallback(() => {
    if (analyserRef.current && recordingState === "recording") {
      const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount);
      analyserRef.current.getByteFrequencyData(dataArray);

      // Calculate average level
      const average = dataArray.reduce((a, b) => a + b, 0) / dataArray.length;
      setAudioLevel(average / 255);

      animationFrameRef.current = requestAnimationFrame(updateAudioLevel);
    }
  }, [recordingState]);

  useEffect(() => {
    if (recordingState === "recording") {
      updateAudioLevel();
    } else {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
      setAudioLevel(0);
    }
  }, [recordingState, updateAudioLevel]);

  // Start countdown then recording
  const startRecordingProcess = async () => {
    setError(null);
    setRecordingState("countdown");
    setCountdownValue(3);

    // Countdown
    for (let i = 3; i > 0; i--) {
      setCountdownValue(i);
      await new Promise((resolve) => setTimeout(resolve, 1000));
    }

    // Start actual recording
    startRecording();
  };

  const startRecording = async () => {
    audioChunksRef.current = [];
    setAudioUrl(null);
    setAudioBase64(null);

    try {
      let stream = streamRef.current;

      if (!stream) {
        stream = await navigator.mediaDevices.getUserMedia({
          audio: {
            echoCancellation: true,
            noiseSuppression: true,
            sampleRate: 44100,
          },
        });
        streamRef.current = stream;
      }

      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: "audio/webm;codecs=opus",
      });

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: "audio/webm" });
        const url = URL.createObjectURL(audioBlob);
        setAudioUrl(url);

        // Convert to base64
        const reader = new FileReader();
        reader.onloadend = () => {
          const base64 = reader.result as string;
          setAudioBase64(base64);
        };
        reader.readAsDataURL(audioBlob);

        // Show confetti
        setShowConfetti(true);
        setTimeout(() => setShowConfetti(false), 3000);
      };

      mediaRecorderRef.current = mediaRecorder;
      mediaRecorder.start(100); // Collect data every 100ms for better granularity
      setRecordingState("recording");
      setRecordingTime(0);

      // Start timer
      timerRef.current = setInterval(() => {
        setRecordingTime((prev) => {
          if (prev >= maxDurationSeconds - 1) {
            stopRecording();
            return prev;
          }
          return prev + 1;
        });
      }, 1000);
    } catch (err) {
      setError("Kayıt başlatılamadı. Lütfen mikrofon erişimini kontrol edin.");
      setRecordingState("idle");
    }
  };

  const stopRecording = () => {
    if (
      mediaRecorderRef.current &&
      (recordingState === "recording" || recordingState === "paused")
    ) {
      mediaRecorderRef.current.stop();
      setRecordingState("review");

      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    }
  };

  const resetRecording = () => {
    setAudioUrl(null);
    setAudioBase64(null);
    setRecordingTime(0);
    setRecordingState("idle");
    setIsPlaying(false);
    audioChunksRef.current = [];
  };

  const handlePlayPause = () => {
    if (audioRef.current) {
      if (isPlaying) {
        audioRef.current.pause();
      } else {
        audioRef.current.play();
      }
      setIsPlaying(!isPlaying);
    }
  };

  const handleSaveVoice = () => {
    if (audioBase64) {
      onRecordingComplete(audioBase64);
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
  };

  const progress = Math.min((recordingTime / minDurationSeconds) * 100, 100);
  const isMinDurationMet = recordingTime >= minDurationSeconds;

  return (
    <div className="relative min-h-[80vh] overflow-hidden">
      {/* Background */}
      <div
        className="fixed inset-0 z-0"
        style={{
          background: "linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%)",
        }}
      >
        {/* Subtle grid pattern */}
        <div
          className="absolute inset-0 opacity-5"
          style={{
            backgroundImage: `
              linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px),
              linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)
            `,
            backgroundSize: "50px 50px",
          }}
        />

        {/* Gradient orbs */}
        <div className="absolute left-1/4 top-1/4 h-96 w-96 rounded-full bg-purple-600/10 blur-3xl" />
        <div className="absolute bottom-1/4 right-1/4 h-96 w-96 rounded-full bg-red-600/10 blur-3xl" />
      </div>

      {/* Content */}
      <div className="relative z-10 mx-auto max-w-2xl px-4 py-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-4 text-center"
        >
          <div className="mb-4 flex items-center justify-center gap-3">
            <motion.div
              animate={{ rotate: [0, 10, -10, 0] }}
              transition={{ duration: 2, repeat: Infinity }}
            >
              <Mic className="h-8 w-8 text-red-400" />
            </motion.div>
          </div>

          <h1 className="mb-2 text-2xl font-bold text-white">Sesinizi Tanıtalım</h1>
          <p className="text-gray-400">Aşağıdaki metni doğal ses tonunuzla okuyun</p>
        </motion.div>

        {/* Tips Banner */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="mb-4 flex flex-wrap items-center justify-center gap-4"
        >
          {TIPS.map((tip, i) => (
            <div key={i} className="flex items-center gap-2 text-sm text-gray-400">
              <span className="text-lg">{tip.icon}</span>
              <span>{tip.text}</span>
            </div>
          ))}
        </motion.div>

        {/* Error Message */}
        {error && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="mb-6 rounded-xl border border-red-500/30 bg-red-500/20 p-4 text-center text-red-300"
          >
            <MicOff className="mx-auto mb-2 h-6 w-6" />
            {error}
          </motion.div>
        )}

        {/* Permission Waiting */}
        {!permissionGranted && !error && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="mb-6 rounded-xl border border-amber-500/30 bg-amber-500/20 p-4 text-center text-amber-300"
          >
            <Mic className="mx-auto mb-2 h-6 w-6 animate-pulse" />
            Mikrofon izni bekleniyor...
          </motion.div>
        )}

        {/* Main Studio Container */}
        {permissionGranted && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="overflow-hidden rounded-3xl border border-white/10 bg-white/5 backdrop-blur-xl"
          >
            {/* Teleprompter Section */}
            <div className="border-b border-white/10 p-6">
              <div className="mb-4 flex items-center gap-2">
                <Volume2 className="h-4 w-4 text-gray-500" />
                <span className="text-sm uppercase tracking-wider text-gray-500">
                  Okunacak Metin
                </span>
              </div>

              <div
                className="max-h-48 overflow-y-auto rounded-2xl bg-black/30 p-6"
                style={{
                  scrollbarWidth: "thin",
                  scrollbarColor: "rgba(255,255,255,0.2) transparent",
                }}
              >
                <p className="whitespace-pre-line font-serif text-xl leading-relaxed text-white/90">
                  {SAMPLE_TEXT}
                </p>
              </div>
            </div>

            {/* Visualizer Section */}
            <div className="border-b border-white/10 bg-black/20 p-6">
              <AudioVisualizer isActive={recordingState === "recording"} audioLevel={audioLevel} />

              {/* Timer */}
              <div className="mt-4 text-center">
                <div className="inline-flex items-center gap-4 rounded-full bg-black/30 px-6 py-2">
                  {/* Recording indicator */}
                  {recordingState === "recording" && (
                    <motion.div
                      animate={{ opacity: [1, 0.3, 1] }}
                      transition={{ duration: 1, repeat: Infinity }}
                      className="h-3 w-3 rounded-full bg-red-500"
                    />
                  )}

                  <span className="font-mono text-2xl text-white">{formatTime(recordingTime)}</span>

                  <span className="text-gray-500">/</span>

                  <span className="font-mono text-lg text-gray-500">
                    {formatTime(minDurationSeconds)}
                  </span>
                </div>

                {/* Progress bar */}
                {recordingState === "recording" && (
                  <div className="mx-auto mt-4 h-1.5 max-w-xs overflow-hidden rounded-full bg-white/10">
                    <motion.div
                      className={`h-full rounded-full ${
                        isMinDurationMet
                          ? "bg-gradient-to-r from-green-500 to-emerald-400"
                          : "bg-gradient-to-r from-red-500 to-orange-400"
                      }`}
                      style={{ width: `${progress}%` }}
                    />
                  </div>
                )}

                {recordingState === "recording" && (
                  <p className="mt-2 text-xs text-gray-500">
                    {isMinDurationMet
                      ? "✓ Minimum süre tamamlandı"
                      : `En az ${minDurationSeconds - recordingTime} saniye daha`}
                  </p>
                )}
              </div>
            </div>

            {/* Controls Section */}
            <div className="p-8">
              {/* Idle State */}
              {recordingState === "idle" && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="text-center"
                >
                  <button onClick={startRecordingProcess} className="group relative">
                    {/* Glow effect */}
                    <div className="absolute inset-0 rounded-full bg-red-500 opacity-30 blur-xl transition-opacity group-hover:opacity-50" />

                    {/* Button */}
                    <div className="relative flex h-28 w-28 items-center justify-center rounded-full bg-gradient-to-br from-red-500 to-red-600 shadow-2xl shadow-red-500/30 transition-transform group-hover:scale-105">
                      <Mic className="h-12 w-12 text-white" />
                    </div>
                  </button>

                  <p className="mt-6 font-medium text-white">Bas ve Okumaya Başla</p>
                  <p className="mt-1 text-sm text-gray-500">
                    3 saniyelik geri sayımdan sonra kayıt başlar
                  </p>
                </motion.div>
              )}

              {/* Recording State */}
              {recordingState === "recording" && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="text-center"
                >
                  <button
                    onClick={stopRecording}
                    className="group relative"
                    disabled={!isMinDurationMet}
                  >
                    {/* Pulsing rings */}
                    <div className="absolute inset-0 flex items-center justify-center">
                      <RecordingRing isRecording={true} />
                    </div>

                    {/* Button */}
                    <div
                      className={`relative flex h-28 w-28 items-center justify-center rounded-full shadow-2xl transition-all ${
                        isMinDurationMet
                          ? "bg-gradient-to-br from-green-500 to-emerald-600 shadow-green-500/30 group-hover:scale-105"
                          : "bg-gradient-to-br from-red-500 to-red-600 shadow-red-500/30"
                      }`}
                    >
                      <Square className="h-10 w-10 text-white" fill="white" />
                    </div>
                  </button>

                  <p className="mt-6 font-medium text-white">
                    {isMinDurationMet ? "Kaydı Bitir" : "Kayıt Devam Ediyor..."}
                  </p>
                  <p className="mt-1 text-sm text-gray-500">
                    {isMinDurationMet ? "Hazır olduğunuzda durdurun" : "Minimum süreye ulaşılmadı"}
                  </p>
                </motion.div>
              )}

              {/* Review State */}
              {recordingState === "review" && audioUrl && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="space-y-6"
                >
                  {/* Success Message */}
                  <div className="text-center">
                    <motion.div
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      transition={{ type: "spring" }}
                      className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-green-500/20"
                    >
                      <Check className="h-8 w-8 text-green-400" />
                    </motion.div>
                    <h3 className="text-xl font-bold text-white">Harika!</h3>
                    <p className="mt-1 text-gray-400">{formatTime(recordingTime)} kayıt yapıldı</p>
                  </div>

                  {/* Audio Player */}
                  <div className="rounded-2xl bg-black/30 p-4">
                    <audio
                      ref={audioRef}
                      src={audioUrl}
                      onEnded={() => setIsPlaying(false)}
                      className="hidden"
                    />

                    {/* Custom Player UI */}
                    <div className="flex items-center gap-4">
                      <button
                        onClick={handlePlayPause}
                        className="flex h-14 w-14 items-center justify-center rounded-full bg-white/10 transition-colors hover:bg-white/20"
                      >
                        {isPlaying ? (
                          <Pause className="h-6 w-6 text-white" />
                        ) : (
                          <Play className="ml-1 h-6 w-6 text-white" />
                        )}
                      </button>

                      <div className="flex-1">
                        <p className="font-medium text-white">Kaydınızı Dinleyin</p>
                        <p className="text-sm text-gray-500">
                          {isPlaying ? "Çalıyor..." : "Oynatmak için tıklayın"}
                        </p>
                      </div>

                      <span className="font-mono text-gray-400">{formatTime(recordingTime)}</span>
                    </div>
                  </div>

                  {/* Action Buttons */}
                  <div className="grid grid-cols-2 gap-4">
                    <button
                      onClick={resetRecording}
                      className="flex items-center justify-center gap-2 rounded-xl border border-white/10 bg-white/5 px-6 py-4 text-white transition-colors hover:bg-white/10"
                    >
                      <RotateCcw className="h-5 w-5" />
                      <span>Tekrar Kaydet</span>
                    </button>

                    <button
                      onClick={handleSaveVoice}
                      className="flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-green-500 to-emerald-600 px-6 py-4 font-semibold text-white shadow-lg shadow-green-500/30 transition-all hover:scale-[1.02] hover:shadow-green-500/50"
                    >
                      <Sparkles className="h-5 w-5" />
                      <span>Bu Sesi Kullan</span>
                    </button>
                  </div>
                </motion.div>
              )}
            </div>
          </motion.div>
        )}

        {/* Back Button */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="mt-8 text-center"
        >
          <Button
            variant="ghost"
            onClick={onBack}
            className="text-gray-400 hover:bg-white/10 hover:text-white"
          >
            <ChevronLeft className="mr-2 h-4 w-4" />
            Geri Dön
          </Button>
        </motion.div>
      </div>

      {/* Countdown Overlay */}
      <AnimatePresence>
        {recordingState === "countdown" && <CountdownOverlay count={countdownValue} />}
      </AnimatePresence>

      {/* Confetti Effect */}
      <AnimatePresence>{showConfetti && <ConfettiEffect />}</AnimatePresence>
    </div>
  );
}
