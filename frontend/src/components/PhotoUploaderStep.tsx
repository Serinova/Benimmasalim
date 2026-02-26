"use client";

import { useState, useCallback } from "react";
import { useDropzone, type FileRejection } from "react-dropzone";
import { motion, AnimatePresence } from "framer-motion";
import {
  Upload,
  Camera,
  CheckCircle,
  XCircle,
  Shield,
  Lock,
  Sparkles,
  Sun,
  Moon,
  User,
  UserX,
  Focus,
  Aperture,
  ChevronRight,
  AlertTriangle,
  Image as ImageIcon,
  Trash2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { useToast } from "@/hooks/use-toast";

interface PhotoUploaderStepProps {
  hideNavButtons?: boolean;
  childName: string;
  photoPreview: string;
  // Multi-photo support for better face analysis
  additionalPhotos?: string[];
  onPhotoSelect: (file: File) => void;
  onAdditionalPhotoSelect?: (files: File[]) => void;
  onRemoveAdditionalPhoto?: (index: number) => void;
  onAnalyze: () => Promise<void>;
  isAnalyzing: boolean;
  faceDetected: boolean;
  onContinue: () => void;
  onBack: () => void;
  onClear: () => void;
  /** Parent email for KVKK consent tracking */
  parentEmail?: string;
}

// Guide item component
function GuideItem({
  isGood,
  icon: Icon,
  title,
  description,
}: {
  isGood: boolean;
  icon: React.ElementType;
  title: string;
  description: string;
}) {
  return (
    <div
      className={`flex items-center gap-3 rounded-xl p-3 ${
        isGood ? "border border-green-200 bg-green-50" : "border border-red-200 bg-red-50"
      }`}
    >
      <div
        className={`flex h-10 w-10 items-center justify-center rounded-full ${
          isGood ? "bg-green-100" : "bg-red-100"
        }`}
      >
        <Icon className={`h-5 w-5 ${isGood ? "text-green-600" : "text-red-500"}`} />
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          {isGood ? (
            <CheckCircle className="h-4 w-4 flex-shrink-0 text-green-500" />
          ) : (
            <XCircle className="h-4 w-4 flex-shrink-0 text-red-500" />
          )}
          <span className={`text-sm font-medium ${isGood ? "text-green-700" : "text-red-700"}`}>
            {title}
          </span>
        </div>
        <p className="mt-0.5 text-xs text-gray-500">{description}</p>
      </div>
    </div>
  );
}

// Magical loading spinner
function MagicalSpinner() {
  return (
    <div className="absolute inset-0 flex items-center justify-center rounded-2xl bg-black/30 backdrop-blur-sm">
      <div className="relative">
        {/* Outer ring */}
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
          className="h-20 w-20 rounded-full border-4 border-purple-200 border-t-purple-500"
        />
        {/* Inner sparkles */}
        <div className="absolute inset-0 flex items-center justify-center">
          <motion.div
            animate={{ scale: [1, 1.2, 1], opacity: [0.5, 1, 0.5] }}
            transition={{ duration: 1.5, repeat: Infinity }}
          >
            <Sparkles className="h-8 w-8 text-purple-500" />
          </motion.div>
        </div>
      </div>
      <p className="absolute bottom-8 text-sm font-medium text-white">
        Fotoğraf analiz ediliyor...
      </p>
    </div>
  );
}

// The magical frame border
function MagicalFrame({
  children,
  isDragActive,
  hasPhoto,
  isError,
}: {
  children: React.ReactNode;
  isDragActive: boolean;
  hasPhoto: boolean;
  isError: boolean;
}) {
  return (
    <div className="relative">
      {/* Animated glow background */}
      <motion.div
        animate={{
          opacity: isDragActive ? 1 : hasPhoto ? 0.3 : 0.5,
          scale: isDragActive ? 1.02 : 1,
        }}
        className={`absolute -inset-1 rounded-3xl blur-xl transition-colors ${
          isError
            ? "bg-red-300"
            : isDragActive
              ? "bg-gradient-to-r from-purple-400 via-pink-400 to-orange-400"
              : hasPhoto
                ? "bg-gradient-to-r from-green-300 to-emerald-300"
                : "bg-gradient-to-r from-purple-200 via-pink-200 to-orange-200"
        }`}
      />

      {/* Main frame */}
      <motion.div
        animate={{
          borderColor: isDragActive
            ? "#a855f7"
            : isError
              ? "#ef4444"
              : hasPhoto
                ? "#22c55e"
                : "#e5e7eb",
        }}
        className={`relative overflow-hidden rounded-2xl border-4 bg-white shadow-xl ${
          isDragActive ? "border-dashed" : "border-solid"
        }`}
      >
        {/* Corner decorations */}
        <div className="absolute left-2 top-2 h-6 w-6 rounded-tl-lg border-l-2 border-t-2 border-purple-300" />
        <div className="absolute right-2 top-2 h-6 w-6 rounded-tr-lg border-r-2 border-t-2 border-pink-300" />
        <div className="absolute bottom-2 left-2 h-6 w-6 rounded-bl-lg border-b-2 border-l-2 border-orange-300" />
        <div className="absolute bottom-2 right-2 h-6 w-6 rounded-br-lg border-b-2 border-r-2 border-purple-300" />

        {children}
      </motion.div>
    </div>
  );
}

export default function PhotoUploaderStep({
  childName,
  photoPreview,
  additionalPhotos = [],
  onPhotoSelect,
  onAdditionalPhotoSelect,
  onRemoveAdditionalPhoto,
  onAnalyze,
  isAnalyzing,
  faceDetected,
  onContinue,
  onBack,
  onClear,
  parentEmail,
}: PhotoUploaderStepProps) {
  const [error, setError] = useState<string | null>(null);
  const [isShaking, setIsShaking] = useState(false);
  const { toast } = useToast();

  // Handle file drop
  const onDrop = useCallback(
    (acceptedFiles: File[], rejectedFiles: FileRejection[]) => {
      setError(null);

      if (rejectedFiles.length > 0) {
        const rejection = rejectedFiles[0];
        if (rejection.errors[0]?.code === "file-too-large") {
          setError("Dosya boyutu 10MB'dan küçük olmalı");
        } else if (rejection.errors[0]?.code === "file-invalid-type") {
          setError("Lütfen bir resim dosyası seçin (JPG, PNG)");
        }
        setIsShaking(true);
        setTimeout(() => setIsShaking(false), 500);
        return;
      }

      if (acceptedFiles.length > 0) {
        onPhotoSelect(acceptedFiles[0]);
      }
    },
    [onPhotoSelect]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "image/jpeg": [".jpg", ".jpeg"],
      "image/png": [".png"],
      "image/webp": [".webp"],
    },
    maxSize: 10 * 1024 * 1024, // 10MB
    multiple: false,
  });

  // Handle analyze
  const handleAnalyze = async () => {
    try {
      await onAnalyze();
    } catch (err) {
      toast({
        title: "Hata",
        description: "Fotoğraf analiz edilemedi. Lütfen tekrar deneyin.",
        variant: "destructive",
      });
    }
  };

  const [kvkkConsent, setKvkkConsent] = useState(false);

  const recordConsent = async (checked: boolean) => {
    setKvkkConsent(checked);
    if (!parentEmail) return;
    try {
      const { API_BASE_URL } = await import("@/lib/api");
      await fetch(`${API_BASE_URL}/consent/record`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: parentEmail,
          consent_type: "PHOTO_PROCESSING",
          action: checked ? "given" : "withdrawn",
          consent_version: "1.0",
          source: "PhotoUploaderStep",
        }),
      });
    } catch (_e) {
      // Consent API failure should not block UX — fire-and-forget
      void _e;
    }
  };

  const isValid = photoPreview && faceDetected && kvkkConsent;

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="text-center">
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-2 inline-flex items-center gap-2 rounded-full bg-gradient-to-r from-purple-100 via-pink-100 to-orange-100 px-3 py-1.5"
        >
          <Camera className="h-4 w-4 text-purple-600" />
          <span className="text-sm font-medium text-purple-700">Sihirli Portal</span>
        </motion.div>

        <motion.h1
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="text-2xl font-bold text-gray-800 md:text-3xl"
        >
          Hadi, <span className="text-purple-600">{childName || "Kahramanımızı"}</span>
          <br className="md:hidden" /> Hikayenin İçine Alalım!
        </motion.h1>

        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
          className="mx-auto mt-2 max-w-lg text-sm text-gray-600"
        >
          En iyi sonuç için aydınlık ve net bir yüz fotoğrafı seçin ✨
        </motion.p>
      </div>

      {/* Main Content - Two Columns */}
      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
        {/* Left Column - The Magic Frame Uploader */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.3 }}
          className={isShaking ? "animate-shake" : ""}
          style={{
            animation: isShaking ? "shake 0.5s ease-in-out" : "none",
          }}
        >
          <MagicalFrame isDragActive={isDragActive} hasPhoto={!!photoPreview} isError={!!error}>
            <div
              {...getRootProps()}
              className={`relative aspect-square cursor-pointer transition-all ${
                !photoPreview ? "p-8" : ""
              }`}
            >
              <input {...getInputProps()} />

              {/* Empty State */}
              {!photoPreview && (
                <div className="flex h-full flex-col items-center justify-center text-center">
                  {/* Silhouette */}
                  <motion.div
                    animate={{
                      scale: isDragActive ? 1.1 : 1,
                      y: isDragActive ? -10 : 0,
                    }}
                    className="relative mb-6"
                  >
                    <div className="flex h-32 w-32 items-center justify-center rounded-full bg-gradient-to-br from-gray-100 to-gray-200">
                      <User className="h-16 w-16 text-gray-300" />
                    </div>
                    {/* Sparkle decorations */}
                    <motion.div
                      animate={{
                        scale: [1, 1.2, 1],
                        opacity: [0.5, 1, 0.5],
                      }}
                      transition={{ duration: 2, repeat: Infinity }}
                      className="absolute -right-2 -top-2"
                    >
                      <Sparkles className="h-6 w-6 text-purple-400" />
                    </motion.div>
                    <motion.div
                      animate={{
                        scale: [1, 1.2, 1],
                        opacity: [0.5, 1, 0.5],
                      }}
                      transition={{ duration: 2, repeat: Infinity, delay: 0.5 }}
                      className="absolute -bottom-2 -left-2"
                    >
                      <Sparkles className="h-5 w-5 text-pink-400" />
                    </motion.div>
                  </motion.div>

                  {/* Upload Instructions */}
                  <motion.div
                    animate={{
                      scale: isDragActive ? 1.05 : 1,
                    }}
                  >
                    <div
                      className={`mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full ${
                        isDragActive ? "bg-purple-500 text-white" : "bg-purple-100 text-purple-600"
                      }`}
                    >
                      <Upload className="h-6 w-6" />
                    </div>

                    <p
                      className={`text-lg font-semibold ${
                        isDragActive ? "text-purple-600" : "text-gray-700"
                      }`}
                    >
                      {isDragActive ? "Bırakın!" : "Sürükle & Bırak"}
                    </p>
                    <p className="mt-1 text-sm text-gray-500">veya tıklayarak seçin</p>
                    <p className="mt-3 text-xs text-gray-400">JPG, PNG (max 10MB)</p>
                  </motion.div>
                </div>
              )}

              {/* Photo Preview */}
              {photoPreview && (
                <div className="relative h-full bg-gray-50">
                  <img
                    src={photoPreview}
                    alt="Yüklenen fotoğraf"
                    className="h-full w-full object-contain"
                  />

                  {/* Loading Overlay */}
                  {isAnalyzing && <MagicalSpinner />}

                  {/* Success Overlay */}
                  {faceDetected && !isAnalyzing && (
                    <motion.div
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="absolute left-4 right-4 top-4 flex items-center gap-2 rounded-xl bg-green-500/90 p-3 backdrop-blur-sm"
                    >
                      <CheckCircle className="h-5 w-5 text-white" />
                      <span className="text-sm font-medium text-white">
                        Yüz başarıyla tespit edildi!
                      </span>
                    </motion.div>
                  )}

                  {/* Action Buttons Overlay */}
                  {!isAnalyzing && (
                    <div className="absolute bottom-4 left-4 right-4 flex gap-2">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onClear();
                        }}
                        className="flex flex-1 items-center justify-center gap-2 rounded-lg bg-white/90 py-2 text-gray-700 backdrop-blur-sm transition hover:bg-white"
                      >
                        <Trash2 className="h-4 w-4" />
                        <span className="text-sm font-medium">Değiştir</span>
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          </MagicalFrame>

          {/* Error Message */}
          <AnimatePresence>
            {error && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="mt-4 flex items-center gap-2 rounded-xl border border-red-200 bg-red-50 p-3 text-red-700"
              >
                <AlertTriangle className="h-5 w-5 flex-shrink-0" />
                <p className="text-sm">{error}</p>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Analyze Button */}
          {photoPreview && !faceDetected && !isAnalyzing && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mt-4"
            >
              <Button
                onClick={handleAnalyze}
                className="w-full bg-gradient-to-r from-purple-600 to-pink-500 py-6 hover:from-purple-700 hover:to-pink-600"
              >
                <Sparkles className="mr-2 h-5 w-5" />
                Fotoğrafı Analiz Et
              </Button>
            </motion.div>
          )}

          {/* Multi-Photo Section - For Better Face Analysis */}
          {/* Gösterim: Ana fotoğraf yüklendikten SONRA (analiz gerekmez) */}
          {photoPreview && onAdditionalPhotoSelect && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mt-4"
            >
              <div className="rounded-xl border border-purple-200 bg-gradient-to-r from-purple-50 to-pink-50 p-4">
                <div className="mb-3 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <ImageIcon className="h-4 w-4 text-purple-600" />
                    <span className="text-sm font-medium text-purple-700">
                      Ekstra Fotoğraflar ({additionalPhotos.length}/4) - İsteğe Bağlı
                    </span>
                  </div>
                  {additionalPhotos.length > 0 && (
                    <span className="rounded-full bg-green-100 px-2 py-1 text-xs text-green-700">
                      +{additionalPhotos.length} fotoğraf eklendi
                    </span>
                  )}
                </div>

                {/* Additional Photos Grid */}
                <div className="mb-3 grid grid-cols-4 gap-2">
                  {additionalPhotos.map((photo, index) => (
                    <div
                      key={index}
                      className="relative aspect-square overflow-hidden rounded-lg border-2 border-purple-300 shadow-sm"
                    >
                      <img
                        src={photo}
                        alt={`Ek fotoğraf ${index + 1}`}
                        className="h-full w-full object-cover"
                      />
                      {onRemoveAdditionalPhoto && (
                        <button
                          onClick={() => onRemoveAdditionalPhoto(index)}
                          className="absolute right-1 top-1 flex h-5 w-5 items-center justify-center rounded-full bg-red-500 shadow hover:bg-red-600"
                        >
                          <XCircle className="h-3 w-3 text-white" />
                        </button>
                      )}
                    </div>
                  ))}

                  {/* Add More Button */}
                  {additionalPhotos.length < 4 && (
                    <label className="flex aspect-square cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed border-purple-300 transition-all hover:border-purple-500 hover:bg-purple-100">
                      <input
                        type="file"
                        accept="image/jpeg,image/png,image/webp"
                        multiple
                        className="hidden"
                        onChange={(e) => {
                          if (e.target.files) {
                            const files = Array.from(e.target.files).slice(
                              0,
                              4 - additionalPhotos.length
                            );
                            onAdditionalPhotoSelect(files);
                          }
                        }}
                      />
                      <Upload className="h-5 w-5 text-purple-400" />
                      <span className="mt-1 text-[10px] text-purple-400">Ekle</span>
                    </label>
                  )}
                </div>

                <p className="text-xs text-purple-600">
                  💡 Farklı açılardan 1-4 fotoğraf ekleyin. AI yüz özelliklerini daha iyi tanır ve
                  daha benzer görseller üretir.
                </p>
              </div>
            </motion.div>
          )}
        </motion.div>

        {/* Right Column - The Guide */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.4 }}
          className="space-y-6"
        >
          {/* Tips Card */}
          <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-lg">
            <div className="mb-5 flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-r from-purple-500 to-pink-500">
                <Sparkles className="h-5 w-5 text-white" />
              </div>
              <div>
                <h3 className="font-bold text-gray-800">Mükemmel Bir Hikaye İçin</h3>
                <p className="text-sm text-gray-500">Fotoğraf İpuçları</p>
              </div>
            </div>

            <div className="space-y-3">
              {/* Lighting */}
              <div>
                <p className="mb-2 text-xs font-medium uppercase tracking-wide text-gray-500">
                  Işık
                </p>
                <div className="grid grid-cols-2 gap-2">
                  <GuideItem
                    isGood={true}
                    icon={Sun}
                    title="Aydınlık Ortam"
                    description="Doğal gün ışığı ideal"
                  />
                  <GuideItem
                    isGood={false}
                    icon={Moon}
                    title="Karanlık/Gölge"
                    description="Yüz net görünmeli"
                  />
                </div>
              </div>

              {/* Angle */}
              <div>
                <p className="mb-2 text-xs font-medium uppercase tracking-wide text-gray-500">
                  Açı
                </p>
                <div className="grid grid-cols-2 gap-2">
                  <GuideItem
                    isGood={true}
                    icon={User}
                    title="Tam Karşıdan"
                    description="Kameraya bakıyor olmalı"
                  />
                  <GuideItem
                    isGood={false}
                    icon={UserX}
                    title="Yandan Profil"
                    description="Yan görünüm uygun değil"
                  />
                </div>
              </div>

              {/* Clarity */}
              <div>
                <p className="mb-2 text-xs font-medium uppercase tracking-wide text-gray-500">
                  Netlik
                </p>
                <div className="grid grid-cols-2 gap-2">
                  <GuideItem
                    isGood={true}
                    icon={Focus}
                    title="Net Fotoğraf"
                    description="Yüz detayları görünür"
                  />
                  <GuideItem
                    isGood={false}
                    icon={Aperture}
                    title="Bulanık/Uzaktan"
                    description="Yakın plan tercih edin"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Privacy & Trust Section */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5 }}
            className="rounded-2xl border border-purple-100 bg-gradient-to-br from-purple-50 to-pink-50 p-6"
          >
            <div className="flex items-start gap-4">
              <div className="flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-full bg-gradient-to-r from-purple-500 to-pink-500">
                <Shield className="h-6 w-6 text-white" />
              </div>
              <div>
                <h3 className="flex items-center gap-2 font-bold text-gray-800">
                  Gizliliğiniz Bizim İçin Sihirlidir
                  <Lock className="h-4 w-4 text-purple-500" />
                </h3>
                <p className="mt-2 text-sm leading-relaxed text-gray-600">
                  Bu fotoğraf <strong>sadece</strong> hikayeyi oluşturmak için yapay zeka tarafından
                  anlık işlenir. Asla saklanmaz, paylaşılmaz veya başka bir amaçla kullanılmaz.
                  <span className="font-medium text-purple-600">
                    {" "}
                    İşlem bitince otomatik silinir.
                  </span>
                </p>
                <div className="mt-4 flex items-center gap-4 text-xs text-gray-500">
                  <span className="flex items-center gap-1">
                    <CheckCircle className="h-3 w-3 text-green-500" />
                    KVKK Uyumlu
                  </span>
                  <span className="flex items-center gap-1">
                    <CheckCircle className="h-3 w-3 text-green-500" />
                    SSL Şifreli
                  </span>
                  <span className="flex items-center gap-1">
                    <CheckCircle className="h-3 w-3 text-green-500" />
                    30 Gün Sonra Silme
                  </span>
                </div>
              </div>
            </div>
          </motion.div>
        </motion.div>
      </div>

      {/* KVKK Consent */}
      {photoPreview && faceDetected && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-xl border border-gray-200 bg-white p-4"
        >
          <label className="flex cursor-pointer items-start gap-3">
            <input
              type="checkbox"
              checked={kvkkConsent}
              onChange={(e) => recordConsent(e.target.checked)}
              className="mt-1 h-5 w-5 rounded border-gray-300 text-purple-600 accent-purple-600"
            />
            <span className="text-sm leading-relaxed text-gray-700">
              Çocuğumun fotoğrafının yalnızca hikaye kitabı oluşturma amacıyla yapay zeka
              tarafından işleneceğini, 30 gün sonra otomatik olarak silineceğini kabul
              ediyorum.{" "}
              <a
                href="/kvkk"
                target="_blank"
                rel="noopener noreferrer"
                className="font-medium text-purple-600 underline hover:text-purple-800"
              >
                KVKK Aydınlatma Metni
              </a>
            </span>
          </label>
        </motion.div>
      )}

      {/* Bottom Actions */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6 }}
        className="flex flex-col gap-4 md:flex-row"
      >
        <Button variant="outline" onClick={onBack} className="md:w-auto">
          Geri
        </Button>

        <Button
          onClick={onContinue}
          disabled={!isValid}
          className={`flex-1 py-6 text-lg font-bold transition-all ${
            isValid
              ? "bg-gradient-to-r from-purple-600 via-pink-500 to-orange-400 shadow-lg shadow-purple-200 hover:from-purple-700 hover:via-pink-600 hover:to-orange-500"
              : "cursor-not-allowed bg-gray-200 text-gray-500"
          }`}
        >
          {isValid ? (
            <span className="flex items-center gap-2">
              <Sparkles className="h-5 w-5" />
              Devam Et
              <ChevronRight className="h-5 w-5" />
            </span>
          ) : (
            <span>Fotoğraf Yükleyin ve Analiz Edin</span>
          )}
        </Button>
      </motion.div>

      {/* Custom shake animation style */}
      <style jsx global>{`
        @keyframes shake {
          0%,
          100% {
            transform: translateX(0);
          }
          10%,
          30%,
          50%,
          70%,
          90% {
            transform: translateX(-5px);
          }
          20%,
          40%,
          60%,
          80% {
            transform: translateX(5px);
          }
        }
        .animate-shake {
          animation: shake 0.5s ease-in-out;
        }
      `}</style>
    </div>
  );
}
