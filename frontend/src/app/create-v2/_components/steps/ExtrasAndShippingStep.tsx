"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Headphones,
  MapPin,
  Mic,
  Play,
  Square,
  Palette,
  CheckCircle2,
} from "lucide-react";
import FormField, { FormTextarea } from "../ui/FormField";
import StickyCTA from "../StickyCTA";
import type { ShippingInfo } from "../../_hooks/useOrderDraft";
import {
  validateFullName,
  validateEmail,
  validatePhone,
  validateAddress,
  validateCity,
  validateDedication,
  validateStep4Shipping,
} from "../../_lib/validations";
import { API_BASE_URL } from "@/lib/api";

interface ExtrasAndShippingStepProps {
  childName: string;
  hasAudioBook: boolean;
  audioType: "system" | "cloned";
  clonedVoiceId: string;
  hasColoringBook: boolean;
  coloringBookPrice: number;
  dedicationNote: string;
  shipping: ShippingInfo;
  onAudioChange: (has: boolean, type: "system" | "cloned") => void;
  onColoringBookChange: (has: boolean) => void;
  onDedicationChange: (note: string) => void;
  onShippingFieldChange: (field: keyof ShippingInfo, value: string) => void;
  onContinue: () => void;
  onBack: () => void;
}

interface SavedAddress {
  id: string;
  label: string;
  full_name: string;
  phone: string;
  address_line: string;
  city: string;
  district: string;
  postal_code: string;
  is_default: boolean;
}

const SYSTEM_VOICES = [
  { id: "female", label: "Ayşe Teyze", desc: "Sıcak kadın sesi", emoji: "👩‍🏫" },
  { id: "male", label: "Mert Amca", desc: "Güven veren erkek sesi", emoji: "👨‍🏫" },
];

export default function ExtrasAndShippingStep({
  childName,
  hasAudioBook,
  audioType,
  hasColoringBook,
  coloringBookPrice,
  dedicationNote,
  shipping,
  onAudioChange,
  onColoringBookChange,
  onDedicationChange,
  onShippingFieldChange,
  onContinue,
  onBack,
}: ExtrasAndShippingStepProps) {
  const [touched, setTouched] = useState<Record<string, boolean>>({});
  const [savedAddresses, setSavedAddresses] = useState<SavedAddress[]>([]);
  const [selectedVoice, setSelectedVoice] = useState("female");
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [hasRecording, setHasRecording] = useState(false);
  const [playingVoice, setPlayingVoice] = useState<string | null>(null);
  const [micError, setMicError] = useState<string | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  const MIN_RECORDING_SECONDS = 45;

  // Preload browser voices (Chrome loads them async)
  useEffect(() => {
    if (typeof window !== "undefined" && window.speechSynthesis) {
      window.speechSynthesis.getVoices();
      window.speechSynthesis.onvoiceschanged = () => {
        window.speechSynthesis.getVoices();
      };
    }
    return () => {
      // Cleanup: stop any playing speech on unmount
      if (typeof window !== "undefined" && window.speechSynthesis) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  const touch = (field: string) =>
    setTouched((prev) => ({ ...prev, [field]: true }));

  const canContinue = validateStep4Shipping({
    fullName: shipping.fullName,
    email: shipping.email,
    phone: shipping.phone,
    address: shipping.address,
    city: shipping.city,
  });

  // Safe coloring book price — guard against absurd values
  const safeColoringPrice = coloringBookPrice > 0 && coloringBookPrice < 1000
    ? coloringBookPrice
    : 150;

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) return;
    fetch(`${API_BASE_URL}/profile/addresses`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((r) => (r.ok ? r.json() : []))
      .then((data) => {
        if (Array.isArray(data)) setSavedAddresses(data);
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (!shipping.fullName && !shipping.email) {
      try {
        const u = JSON.parse(localStorage.getItem("user") || "{}");
        if (u.full_name) onShippingFieldChange("fullName", u.full_name);
        if (u.email) onShippingFieldChange("email", u.email);
        if (u.phone) onShippingFieldChange("phone", u.phone);
      } catch { /* ignore */ }
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const applySavedAddress = (addr: SavedAddress) => {
    onShippingFieldChange("fullName", addr.full_name);
    onShippingFieldChange("phone", addr.phone);
    onShippingFieldChange("address", addr.address_line);
    onShippingFieldChange("city", addr.city);
    onShippingFieldChange("district", addr.district);
    onShippingFieldChange("postalCode", addr.postal_code);
  };

  /* ── Voice Preview via Web Speech API ── */
  const synthRef = useRef<SpeechSynthesisUtterance | null>(null);

  const playVoicePreview = useCallback((voiceId: string) => {
    const synth = window.speechSynthesis;

    // If same voice is playing, stop it
    if (playingVoice === voiceId) {
      synth.cancel();
      setPlayingVoice(null);
      return;
    }

    // Stop any currently playing preview
    synth.cancel();

    const sampleText =
      "Bir varmış bir yokmuş, uzak diyarlarda küçük bir kahraman yaşarmış. Bu kahraman cesur ve meraklıymış.";

    const utterance = new SpeechSynthesisUtterance(sampleText);
    utterance.lang = "tr-TR";
    utterance.rate = 0.9;

    // Pick a matching voice from available Turkish voices
    const voices = synth.getVoices();
    const turkishVoices = voices.filter((v) => v.lang.startsWith("tr"));

    if (voiceId === "female") {
      // Prefer a female Turkish voice, fallback to first Turkish or default
      const femaleVoice = turkishVoices.find(
        (v) => v.name.toLowerCase().includes("female") || v.name.toLowerCase().includes("kadın")
      ) || turkishVoices[0];
      if (femaleVoice) utterance.voice = femaleVoice;
      utterance.pitch = 1.15;
    } else {
      // Prefer a male Turkish voice
      const maleVoice = turkishVoices.find(
        (v) => v.name.toLowerCase().includes("male") || v.name.toLowerCase().includes("erkek")
      ) || turkishVoices[1] || turkishVoices[0];
      if (maleVoice) utterance.voice = maleVoice;
      utterance.pitch = 0.8;
    }

    utterance.onend = () => setPlayingVoice(null);
    utterance.onerror = () => setPlayingVoice(null);
    synthRef.current = utterance;

    synth.speak(utterance);
    setPlayingVoice(voiceId);
  }, [playingVoice]);

  /* ── Voice Recording ── */
  const startRecording = useCallback(async () => {
    setMicError(null);
    try {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        setMicError("Tarayıcınız mikrofon erişimini desteklemiyor. Lütfen HTTPS üzerinden deneyin.");
        return;
      }
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      mediaRecorderRef.current = recorder;
      setIsRecording(true);
      setRecordingTime(0);

      timerRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1);
      }, 1000);

      recorder.ondataavailable = () => {
        setHasRecording(true);
      };

      recorder.onstop = () => {
        stream.getTracks().forEach(t => t.stop());
        if (timerRef.current) clearInterval(timerRef.current);
      };

      recorder.start();
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Bilinmeyen hata";
      if (msg.includes("Permission") || msg.includes("NotAllowed")) {
        setMicError("Mikrofon izni reddedildi. Lütfen tarayıcı ayarlarından mikrofon iznini açın.");
      } else {
        setMicError(`Mikrofon erişimi başarısız: ${msg}`);
      }
    }
  }, []);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === "recording") {
      mediaRecorderRef.current.stop();
    }
    setIsRecording(false);
    if (timerRef.current) clearInterval(timerRef.current);
  }, []);

  const formatTime = (seconds: number) => {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m}:${s.toString().padStart(2, "0")}`;
  };

  return (
    <div className="pb-24 space-y-5">
      {/* ── Header ── */}
      <header>
        <p className="text-[10px] sm:text-xs font-bold text-violet-500 uppercase tracking-wider mb-0.5">
          Adım 4
        </p>
        <h2 className="text-lg sm:text-xl font-bold text-slate-800">
          Ekstralar & Teslimat
        </h2>
        <p className="text-xs sm:text-sm text-slate-500 mt-1">
          {childName} için kitabınızı özelleştirin ve teslimat bilgilerinizi girin.
        </p>
      </header>

      {/* ══════════ SECTION: Audio ══════════ */}
      <section className="rounded-2xl border border-slate-100 bg-white shadow-sm overflow-hidden">
        <div className="px-4 pt-3.5 pb-2.5 border-b border-slate-50 flex items-center gap-2">
          <Headphones className="h-4 w-4 text-violet-500" />
          <span className="text-sm font-semibold text-slate-700">Sesli Kitap</span>
          <span className="text-[10px] text-slate-400 bg-slate-50 px-2 py-0.5 rounded-full ml-auto">
            QR ile masal dinle
          </span>
        </div>

        <div className="p-3 space-y-2">
          {/* Option 1: No audio */}
          <AudioOptionCard
            active={!hasAudioBook}
            onClick={() => onAudioChange(false, "system")}
            emoji="📖"
            label="Sadece Kitap"
            desc="Sesli kitap olmadan"
            price={null}
          />

          {/* Option 2: System voice */}
          <AudioOptionCard
            active={hasAudioBook && audioType === "system"}
            onClick={() => onAudioChange(true, "system")}
            emoji="🎙️"
            label="Profesyonel Masalcı"
            desc="Pedagojik eğitimli sesler"
            price={150}
            recommended
          />

          {/* System voice sub-options */}
          <AnimatePresence>
            {hasAudioBook && audioType === "system" && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                className="overflow-hidden"
              >
                <div className="pl-4 pr-3 pb-2 space-y-1.5">
                  <p className="text-[11px] font-semibold text-slate-500 mb-1">Ses Seçin:</p>
                  <div className="grid grid-cols-2 gap-2">
                    {SYSTEM_VOICES.map(voice => (
                      <div key={voice.id} className="space-y-1">
                        <button
                          type="button"
                          onClick={() => setSelectedVoice(voice.id)}
                          className={`
                            w-full flex items-center gap-2 rounded-xl border-2 p-2.5 transition-all text-left
                            ${selectedVoice === voice.id
                              ? "border-violet-500 bg-violet-50"
                              : "border-slate-100 bg-slate-50 hover:border-slate-200"
                            }
                          `}
                        >
                          <span className="text-xl">{voice.emoji}</span>
                          <div>
                            <p className={`text-xs font-bold ${selectedVoice === voice.id ? "text-violet-700" : "text-slate-700"}`}>
                              {voice.label}
                            </p>
                            <p className="text-[10px] text-slate-400">{voice.desc}</p>
                          </div>
                        </button>
                        {/* Audio preview button per voice */}
                        <button
                          type="button"
                          onClick={() => playVoicePreview(voice.id)}
                          className={`w-full flex items-center justify-center gap-1.5 py-1.5 rounded-lg text-[10px] font-medium transition-all ${
                            playingVoice === voice.id
                              ? "bg-violet-100 text-violet-700"
                              : "bg-slate-50 text-slate-400 hover:text-violet-500"
                          }`}
                        >
                          {playingVoice === voice.id ? (
                            <><Square className="h-3 w-3" /> Durdur</>
                          ) : (
                            <><Play className="h-3 w-3" /> Önizle</>
                          )}
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Option 3: Cloned voice */}
          <AudioOptionCard
            active={hasAudioBook && audioType === "cloned"}
            onClick={() => onAudioChange(true, "cloned")}
            emoji="🎤"
            label="Sizin Sesinizle"
            desc="Yapay zeka sesinizi kopyalar"
            price={300}
            premium
          />

          {/* Voice recording UI */}
          <AnimatePresence>
            {hasAudioBook && audioType === "cloned" && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                className="overflow-hidden"
              >
                <div className="mx-3 mb-2 rounded-xl border border-amber-200 bg-amber-50/50 p-4 space-y-3">
                  <div className="text-center">
                    <p className="text-sm font-bold text-amber-900 mb-1">
                      Ses Kaydı
                    </p>
                    <p className="text-xs text-amber-700">
                      Aşağıdaki metni doğal sesinizle okuyun. Yapay zeka sesinizi klonlayarak tüm masalı sizin sesinizle anlatacak.
                    </p>
                  </div>

                  {/* Sample text to read */}
                  <div className="rounded-lg bg-white p-3 border border-amber-100">
                    <p className="text-xs text-slate-600 italic leading-relaxed">
                      &ldquo;Bir varmış bir yokmuş, uzak diyarlarda küçük bir kahraman yaşarmış.
                      Bu kahraman cesur, meraklı ve her zaman maceraya hazırmış.
                      Bir sabah güneş doğarken pencereden dışarı baktığında,
                      bahçedeki en büyük ağacın altında parıldayan bir şey gördü.
                      Heyecanla merdivenlerden koşarak indi ve kapıyı açtı.
                      Ayaklarının altındaki çimenler sabah çiyiyle ıslanmıştı.
                      Parıltılı nesneye yaklaştığında, bunun sihirli bir harita olduğunu anladı.
                      Haritanın üzerinde renkli çizgiler, gizemli semboller ve küçük bir pusula vardı.
                      Kahramanımız haritayı eline aldığında, pusula kendi kendine dönmeye başladı
                      ve muhteşem bir macera böylece başlamış oldu.&rdquo;
                    </p>
                  </div>

                  {micError && (
                    <div className="rounded-lg bg-red-50 border border-red-200 p-2.5 text-xs text-red-700">
                      ⚠️ {micError}
                    </div>
                  )}

                  {/* Recording button */}
                  <div className="flex flex-col items-center gap-2">
                    {isRecording ? (
                      <>
                        {/* Waveform animation */}
                        <div className="flex items-center gap-0.5 h-8">
                          {[...Array(20)].map((_, i) => (
                            <motion.div
                              key={i}
                              className="w-1 bg-red-500 rounded-full"
                              animate={{
                                height: [4, Math.random() * 28 + 4, 4],
                              }}
                              transition={{
                                repeat: Infinity,
                                duration: 0.5 + Math.random() * 0.5,
                                delay: i * 0.05,
                              }}
                            />
                          ))}
                        </div>
                        <p className="text-sm font-bold text-red-600 tabular-nums">
                          {formatTime(recordingTime)}
                          {recordingTime < MIN_RECORDING_SECONDS && (
                            <span className="text-[10px] text-slate-400 font-normal ml-2">
                              (min {MIN_RECORDING_SECONDS}sn)
                            </span>
                          )}
                        </p>
                        {/* Progress bar to 45s */}
                        <div className="w-full bg-red-100 rounded-full h-1.5">
                          <div
                            className={`h-1.5 rounded-full transition-all ${recordingTime >= MIN_RECORDING_SECONDS ? 'bg-emerald-500' : 'bg-red-500'}`}
                            style={{ width: `${Math.min(100, (recordingTime / MIN_RECORDING_SECONDS) * 100)}%` }}
                          />
                        </div>
                        <motion.button
                          type="button"
                          whileTap={{ scale: 0.95 }}
                          onClick={stopRecording}
                          disabled={recordingTime < MIN_RECORDING_SECONDS}
                          className={`flex items-center gap-2 rounded-xl px-5 py-2.5 text-sm font-bold text-white shadow-md ${
                            recordingTime >= MIN_RECORDING_SECONDS
                              ? 'bg-red-600 shadow-red-200'
                              : 'bg-slate-300 cursor-not-allowed shadow-none'
                          }`}
                        >
                          <Square className="h-3.5 w-3.5" />
                          {recordingTime >= MIN_RECORDING_SECONDS ? 'Kaydı Durdur' : `${MIN_RECORDING_SECONDS - recordingTime}sn kaldı`}
                        </motion.button>
                      </>
                    ) : hasRecording ? (
                      <>
                        <div className="flex items-center gap-2 text-emerald-600">
                          <CheckCircle2 className="h-5 w-5" />
                          <span className="text-sm font-bold">Ses kaydı hazır!</span>
                        </div>
                        <div className="flex gap-2">
                          <button
                            type="button"
                            className="flex items-center gap-1.5 rounded-xl bg-slate-100 px-4 py-2 text-xs font-medium text-slate-600"
                          >
                            <Play className="h-3 w-3" />
                            Dinle
                          </button>
                          <button
                            type="button"
                            onClick={() => {
                              setHasRecording(false);
                              startRecording();
                            }}
                            className="flex items-center gap-1.5 rounded-xl bg-amber-100 px-4 py-2 text-xs font-medium text-amber-700"
                          >
                            <Mic className="h-3 w-3" />
                            Tekrar Kaydet
                          </button>
                        </div>
                      </>
                    ) : (
                      <motion.button
                        type="button"
                        whileTap={{ scale: 0.95 }}
                        onClick={startRecording}
                        className="flex items-center gap-2 rounded-xl bg-amber-500 px-5 py-2.5 text-sm font-bold text-white shadow-md shadow-amber-200 hover:bg-amber-600"
                      >
                        <Mic className="h-4 w-4" />
                        Kaydı Başlat
                      </motion.button>
                    )}
                  </div>

                  <p className="text-[10px] text-amber-600 text-center">
                    En az {MIN_RECORDING_SECONDS} saniye kayıt yapmanız gerekmektedir
                  </p>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </section>

      {/* ══════════ SECTION: Coloring Book ══════════ */}
      <section className="rounded-2xl border border-slate-100 bg-white shadow-sm overflow-hidden">
        <div className="px-4 pt-3.5 pb-2.5 border-b border-slate-50 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Palette className="h-4 w-4 text-violet-500" />
            <span className="text-sm font-semibold text-slate-700">Boyama Kitabı</span>
          </div>
          <span className="text-sm font-bold text-emerald-600">+{safeColoringPrice} ₺</span>
        </div>
        <div className="p-4">
          <p className="text-xs text-slate-500 mb-3">
            Hikayedeki sahnelerin siyah-beyaz boyama versiyonu. Çocuğunuz kendi hikayesini boyasın!
          </p>
          <button
            type="button"
            onClick={() => onColoringBookChange(!hasColoringBook)}
            className={`w-full py-3 rounded-xl font-bold text-sm transition-all flex items-center justify-center gap-2 ${
              hasColoringBook
                ? "bg-gradient-to-r from-emerald-500 to-teal-500 text-white shadow-lg shadow-emerald-200"
                : "bg-white border-2 border-emerald-300 text-emerald-700 hover:bg-emerald-50"
            }`}
          >
            {hasColoringBook ? (
              <>
                <CheckCircle2 className="h-4 w-4" />
                Boyama Kitabı Eklendi
              </>
            ) : (
              `🎨 Boyama Kitabı Ekle · ${safeColoringPrice} ₺`
            )}
          </button>
        </div>
      </section>

      {/* ══════════ SECTION: Dedication ══════════ */}
      <section className="rounded-2xl border border-slate-100 bg-white shadow-sm p-4">
        <FormTextarea
          label="İthaf Notu (İsteğe Bağlı)"
          value={dedicationNote}
          onChange={(e) => onDedicationChange(e.target.value)}
          onBlur={() => touch("dedication")}
          placeholder={`Sevgili ${childName || "..."}, bu kitap senin için...`}
          maxLength={300}
          rows={2}
          error={touched.dedication ? validateDedication(dedicationNote) : null}
          touched={!!touched.dedication}
          hint={`${dedicationNote.length}/300`}
        />
      </section>

      {/* ══════════ SECTION: Shipping ══════════ */}
      <section className="rounded-2xl border border-slate-100 bg-white shadow-sm overflow-hidden">
        <div className="px-4 pt-3.5 pb-2.5 border-b border-slate-50 flex items-center gap-2">
          <MapPin className="h-4 w-4 text-violet-500" />
          <span className="text-sm font-semibold text-slate-700">Teslimat Bilgileri</span>
        </div>

        <div className="p-4 space-y-3">
          {savedAddresses.length > 0 && (
            <div className="mb-3 space-y-2">
              <p className="text-[11px] font-semibold text-slate-500">Kayıtlı Adresler</p>
              {savedAddresses.map((addr) => (
                <button
                  key={addr.id}
                  type="button"
                  onClick={() => applySavedAddress(addr)}
                  className="w-full text-left rounded-xl border border-slate-200 bg-white p-3 text-sm hover:border-violet-300 transition-colors"
                >
                  <p className="font-semibold text-slate-800">{addr.label || addr.full_name}</p>
                  <p className="text-xs text-slate-500 truncate">{addr.address_line}, {addr.city}</p>
                </button>
              ))}
            </div>
          )}

          <FormField
            label="Ad Soyad"
            value={shipping.fullName}
            onChange={(e) => onShippingFieldChange("fullName", e.target.value)}
            onBlur={() => touch("fullName")}
            placeholder="Ad Soyad"
            autoComplete="name"
            error={touched.fullName ? validateFullName(shipping.fullName) : null}
            touched={!!touched.fullName}
          />

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <FormField
              label="E-posta"
              type="email"
              value={shipping.email}
              onChange={(e) => onShippingFieldChange("email", e.target.value)}
              onBlur={() => touch("email")}
              placeholder="ornek@email.com"
              autoComplete="email"
              error={touched.email ? validateEmail(shipping.email) : null}
              touched={!!touched.email}
            />
            <FormField
              label="Telefon"
              type="tel"
              value={shipping.phone}
              onChange={(e) => onShippingFieldChange("phone", e.target.value)}
              onBlur={() => touch("phone")}
              placeholder="05XX XXX XX XX"
              autoComplete="tel"
              error={touched.phone ? validatePhone(shipping.phone) : null}
              touched={!!touched.phone}
            />
          </div>

          <FormField
            label="Adres"
            value={shipping.address}
            onChange={(e) => onShippingFieldChange("address", e.target.value)}
            onBlur={() => touch("address")}
            placeholder="Mahalle, sokak, bina no, daire no"
            autoComplete="street-address"
            error={touched.address ? validateAddress(shipping.address) : null}
            touched={!!touched.address}
          />

          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            <FormField
              label="Şehir"
              value={shipping.city}
              onChange={(e) => onShippingFieldChange("city", e.target.value)}
              onBlur={() => touch("city")}
              placeholder="İstanbul"
              autoComplete="address-level1"
              error={touched.city ? validateCity(shipping.city) : null}
              touched={!!touched.city}
            />
            <FormField
              label="İlçe"
              value={shipping.district}
              onChange={(e) => onShippingFieldChange("district", e.target.value)}
              placeholder="İlçe (isteğe bağlı)"
              autoComplete="address-level2"
            />
            <FormField
              label="Posta Kodu"
              value={shipping.postalCode}
              onChange={(e) => onShippingFieldChange("postalCode", e.target.value)}
              placeholder="34000"
              autoComplete="postal-code"
            />
          </div>
        </div>
      </section>

      <StickyCTA
        primaryLabel={canContinue ? "Ödemeye Geç →" : "Bilgileri Tamamlayın"}
        onPrimary={onContinue}
        primaryDisabled={!canContinue}
        secondaryLabel="← Geri"
        onSecondary={onBack}
      />
    </div>
  );
}

/* ── Audio Option Card ── */
function AudioOptionCard({
  active,
  onClick,
  emoji,
  label,
  desc,
  price,
  recommended,
  premium,
}: {
  active: boolean;
  onClick: () => void;
  emoji: string;
  label: string;
  desc: string;
  price: number | null;
  recommended?: boolean;
  premium?: boolean;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`
        w-full flex items-center gap-3 p-3 rounded-xl border-2 transition-all text-left relative
        ${active
          ? premium
            ? "border-amber-400 bg-amber-50/70 shadow-sm"
            : "border-violet-500 bg-violet-50/70 shadow-sm"
          : "border-slate-100 bg-slate-50/50 hover:border-slate-200"
        }
      `}
    >
      {recommended && (
        <span className="absolute -top-2.5 right-3 text-[9px] font-bold bg-violet-600 text-white px-2 py-0.5 rounded-full">
          ÖNERİLEN
        </span>
      )}
      <div className={`flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-lg text-base ${
        active ? (premium ? "bg-amber-100" : "bg-violet-100") : "bg-slate-100"
      }`}>
        {emoji}
      </div>
      <div className="flex-1 min-w-0">
        <p className={`font-bold text-sm ${
          active ? (premium ? "text-amber-900" : "text-violet-800") : "text-slate-700"
        }`}>{label}</p>
        <p className="text-[11px] text-slate-500">{desc}</p>
      </div>
      {price !== null ? (
        <p className={`text-sm font-bold flex-shrink-0 ${
          active ? (premium ? "text-amber-600" : "text-violet-600") : "text-slate-400"
        }`}>+{price} ₺</p>
      ) : (
        <p className="text-xs font-medium text-slate-400 flex-shrink-0">Sıfır Ekstra</p>
      )}
      {active && (
        <div className={`flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full text-white text-xs ${
          premium ? "bg-amber-500" : "bg-violet-500"
        }`}>✓</div>
      )}
    </button>
  );
}
