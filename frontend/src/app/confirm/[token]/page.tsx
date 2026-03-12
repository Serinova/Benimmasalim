"use client";

import { useState, useEffect, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Image from "next/image";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { API_BASE_URL } from "@/lib/api";

interface StoryPage {
  page_number: number | string;
  text: string;
  page_type?: string;
  is_back_cover?: boolean;
}

interface PreviewData {
  id: string;
  status: string;
  story_title: string;
  child_name: string;
  child_age: number | null;
  parent_name: string;
  product_name: string;
  product_price: number | null;
  page_count: number;
  image_count: number;
  page_images: Record<string, string>;
  story_pages: StoryPage[];
  dedication_note: string | null;
  created_at: string | null;
  page_regenerate_count: number;
  max_page_regenerations: number;
  back_cover_image_url?: string | null;
  cover_spread_image_url?: string | null;
}

interface ConfirmResult {
  success: boolean;
  message: string;
  already_confirmed?: boolean;
  expired?: boolean;
  still_processing?: boolean;
}

interface RegenerateResult {
  success: boolean;
  new_image_url: string;
  page_number: string;
  remaining_regenerations: number;
}

function getPageLabel(key: string): string {
  if (key === "0") return "Kapak";
  if (key === "dedication") return "Karsilama";
  if (key === "back_cover") return "Arka Kapak";
  return `Sayfa ${key}`;
}

function ConfirmButtonLabel({ confirming, busy }: { confirming: boolean; busy: boolean }) {
  if (confirming) {
    return (
      <>
        <span className="mr-2 inline-block h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
        Onaylaniyor...
      </>
    );
  }
  if (busy) return <>Resim yenileniyor...</>;
  return <>Kitabi Onayla</>;
}

// ---------------------------------------------------------------------------
function RegenButtonLabel({ isRegenerating, anotherBusy }: { isRegenerating: boolean; anotherBusy: boolean }) {
  if (isRegenerating) {
    return (
      <>
        <span className="mr-2 inline-block h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
        Yeniden ciziliyor...
      </>
    );
  }
  if (anotherBusy) return <>Baska sayfa ciziliyor...</>;
  return <>Tekrar Ciz</>;
}

// ---------------------------------------------------------------------------
// Lightbox component with swipe + regeneration
// ---------------------------------------------------------------------------
function ImageLightbox({
  orderedKeys,
  currentIndex,
  getImageUrl,
  textByPage,
  onClose,
  onNavigate,
  onRegenerate,
  regeneratingKey,
  regenRemaining,
  canRegenerate,
}: {
  orderedKeys: string[];
  currentIndex: number;
  getImageUrl: (key: string) => string | null;
  textByPage: Record<string, string>;
  onClose: () => void;
  onNavigate: (idx: number) => void;
  onRegenerate: (key: string) => void;
  regeneratingKey: string | null;
  regenRemaining: number;
  canRegenerate: boolean;
}) {
  const key = orderedKeys[currentIndex];
  const url = getImageUrl(key);
  const text = textByPage[key] || "";
  const label = getPageLabel(key);
  const isDedication = key === "dedication";
  const isRegenerating = regeneratingKey === key;
  const swipeThreshold = 50;

  // Lock body scroll while lightbox is open
  useEffect(() => {
    document.body.style.overflow = "hidden";
    return () => { document.body.style.overflow = ""; };
  }, []);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
      if (e.key === "ArrowLeft" && currentIndex > 0) onNavigate(currentIndex - 1);
      if (e.key === "ArrowRight" && currentIndex < orderedKeys.length - 1) onNavigate(currentIndex + 1);
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [currentIndex, orderedKeys.length, onClose, onNavigate]);

  return (
    <div className="fixed inset-0 z-50 flex flex-col bg-black">
      {/* Top bar */}
      <div className="flex items-center justify-between px-3 py-1.5">
        <span className="text-sm font-medium text-white/80">
          {currentIndex + 1} / {orderedKeys.length}
        </span>
        <button
          onClick={onClose}
          className="flex h-8 w-8 items-center justify-center rounded-full bg-white/10 text-white transition hover:bg-white/20"
        >
          ✕
        </button>
      </div>

      {/* Image area with swipe */}
      <div className="relative flex min-h-0 flex-1 items-center justify-center overflow-hidden px-1">
        {/* Desktop prev arrow */}
        {currentIndex > 0 && (
          <button
            onClick={() => onNavigate(currentIndex - 1)}
            className="absolute left-2 z-10 hidden h-12 w-12 items-center justify-center rounded-full bg-white/10 text-2xl text-white transition hover:bg-white/20 md:flex"
          >
            ‹
          </button>
        )}

        <AnimatePresence mode="wait">
          <motion.div
            key={key}
            initial={{ opacity: 0, x: 60 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -60 }}
            transition={{ duration: 0.2 }}
            drag="x"
            dragConstraints={{ left: 0, right: 0 }}
            dragElastic={0.3}
            onDragEnd={(_e, info) => {
              if (info.offset.x < -swipeThreshold && currentIndex < orderedKeys.length - 1) {
                onNavigate(currentIndex + 1);
              } else if (info.offset.x > swipeThreshold && currentIndex > 0) {
                onNavigate(currentIndex - 1);
              }
            }}
            className="flex h-full w-full max-w-7xl cursor-grab items-center justify-center active:cursor-grabbing"
          >
            {url ? (
              <Image
                src={url}
                alt={label}
                width={1920}
                height={1280}
                className="max-h-full max-w-full rounded-lg object-contain"
                style={{ maxHeight: "calc(100vh - 120px)" }}
                unoptimized
                draggable={false}
              />
            ) : (
              <div className="flex h-64 w-full items-center justify-center rounded-lg bg-gray-800 text-gray-400">
                Gorsel yok
              </div>
            )}
          </motion.div>
        </AnimatePresence>

        {/* Desktop next arrow */}
        {currentIndex < orderedKeys.length - 1 && (
          <button
            onClick={() => onNavigate(currentIndex + 1)}
            className="absolute right-2 z-10 hidden h-12 w-12 items-center justify-center rounded-full bg-white/10 text-2xl text-white transition hover:bg-white/20 md:flex"
          >
            ›
          </button>
        )}
      </div>

      {/* Bottom info + actions */}
      <div className="mx-auto w-full max-w-3xl px-3 pb-1 pt-0.5">
        <p className="mb-0 text-center text-xs font-semibold text-purple-300">{label}</p>
        {text && (
          <p className="mx-auto mb-1 max-w-xl text-center text-xs leading-snug text-white/60 line-clamp-2">
            {text}
          </p>
        )}

        {/* Regenerate button */}
        {canRegenerate && !isDedication && url && (
          <div className="flex items-center justify-center gap-3">
            <Button
              variant="outline"
              size="sm"
              disabled={regeneratingKey !== null || regenRemaining <= 0}
              onClick={() => onRegenerate(key)}
              className="border-white/20 bg-white/10 text-white hover:bg-white/20"
            >
              <RegenButtonLabel isRegenerating={isRegenerating} anotherBusy={regeneratingKey !== null} />
            </Button>
            <span className="text-xs text-white/50">
              {regenRemaining > 0
                ? `${regenRemaining} yeniden çizim hakkınız kaldı`
                : "Yeniden çizim hakkınız doldu"}
            </span>
          </div>
        )}
      </div>

      {/* Thumbnail strip */}
      <div className="flex gap-1 overflow-x-auto px-3 pb-1.5">
        {orderedKeys.map((k, i) => {
          const thumbUrl = getImageUrl(k);
          return (
            <button
              key={k}
              onClick={() => onNavigate(i)}
              className={`relative h-9 w-12 flex-shrink-0 overflow-hidden rounded transition ${i === currentIndex
                ? "ring-2 ring-purple-400"
                : "opacity-50 hover:opacity-80"
                }`}
            >
              {thumbUrl ? (
                <Image
                  src={thumbUrl}
                  alt={getPageLabel(k)}
                  fill
                  className="object-cover"
                  unoptimized
                />
              ) : (
                <div className="h-full w-full bg-gray-700" />
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------
export default function ConfirmPage() {
  const params = useParams();
  const router = useRouter();
  const token = params.token as string;

  const [loading, setLoading] = useState(true);
  const [preview, setPreview] = useState<PreviewData | null>(null);
  const [confirming, setConfirming] = useState(false);
  const [confirmed, setConfirmed] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lightboxIndex, setLightboxIndex] = useState<number | null>(null);
  const [regeneratingKey, setRegeneratingKey] = useState<string | null>(null);
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const fetchPreview = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/orders/preview-by-token/${token}`);
      if (!res.ok) {
        const data = await res.json().catch(() => null);
        setError(data?.detail || "Sipariş bulunamadı.");
        return;
      }
      const data: PreviewData = await res.json();
      if (data.status === "CONFIRMED") setConfirmed(true);
      setPreview(data);
    } catch {
      setError("Bağlantı hatası. Lütfen tekrar deneyin.");
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    if (token) fetchPreview();
  }, [token, fetchPreview]);

  const handleConfirm = async () => {
    setShowConfirmDialog(false);
    setConfirming(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE_URL}/orders/confirm/${token}`, { method: "POST" });
      const data: ConfirmResult = await res.json();
      if (data.success) {
        setConfirmed(true);
      } else if (data.still_processing) {
        setError("Kitabınız henüz hazırlanıyor. Lütfen biraz bekleyip tekrar deneyin.");
      } else if (data.expired) {
        setError("Bu onay linkinin süresi dolmuş.");
      } else {
        setError(data.message || "Onaylama başarısız oldu.");
      }
    } catch {
      setError("Bağlantı hatası. Lütfen tekrar deneyin.");
    } finally {
      setConfirming(false);
    }
  };

  const handleRegenerate = async (pageKey: string) => {
    if (!preview || regeneratingKey !== null) return;
    setRegeneratingKey(pageKey);
    setError(null);

    // Save current image URL to detect changes after timeout
    const previousImageUrl = preview.page_images?.[pageKey] || "";

    const controller = new AbortController();
    // 5-minute timeout for the regeneration request
    const timeoutId = setTimeout(() => controller.abort(), 5 * 60 * 1000);

    // Safety net: always clear spinner after 6 minutes no matter what
    const safetyTimeout = setTimeout(() => {
      setRegeneratingKey((current) => {
        if (current === pageKey) {
          setError("İşlem çok uzun sürdü. Sayfayı yenileyerek sonucu kontrol edin.");
          return null;
        }
        return current;
      });
    }, 6 * 60 * 1000);

    try {
      const res = await fetch(
        `${API_BASE_URL}/orders/preview-by-token/${token}/regenerate-page`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ page_number: pageKey }),
          signal: controller.signal,
        },
      );
      clearTimeout(timeoutId);
      if (!res.ok) {
        const err = await res.json().catch(() => null);
        setError(err?.detail || "Yeniden çizim başarısız oldu.");
        return;
      }
      const data: RegenerateResult = await res.json();
      if (data.success) {
        const bustUrl = data.new_image_url.includes("?")
          ? `${data.new_image_url}&_t=${Date.now()}`
          : `${data.new_image_url}?_t=${Date.now()}`;
        setPreview((prev) => {
          if (!prev) return prev;
          return {
            ...prev,
            page_images: { ...prev.page_images, [data.page_number]: bustUrl },
            page_regenerate_count: prev.max_page_regenerations - data.remaining_regenerations,
          };
        });
        const remaining = data.remaining_regenerations;
        const suffix = remaining > 0 ? ` (${remaining} hak kaldı)` : "";
        setSuccessMessage(`${getPageLabel(data.page_number)} yeniden çizildi!${suffix}`);
        setTimeout(() => setSuccessMessage(null), 4000);
      }
    } catch (err: unknown) {
      clearTimeout(timeoutId);
      // On timeout: poll the preview to check if the backend actually succeeded
      if (err instanceof DOMException && err.name === "AbortError") {
        try {
          const pollRes = await fetch(`${API_BASE_URL}/orders/preview-by-token/${token}`);
          if (pollRes.ok) {
            const pollData: PreviewData = await pollRes.json();
            const newUrl = pollData.page_images?.[pageKey];
            if (newUrl && newUrl !== previousImageUrl) {
              // Backend succeeded — image was updated
              const bustUrl = newUrl.includes("?")
                ? `${newUrl}&_t=${Date.now()}`
                : `${newUrl}?_t=${Date.now()}`;
              setPreview((prev) => {
                if (!prev) return prev;
                return {
                  ...prev,
                  page_images: { ...prev.page_images, [pageKey]: bustUrl },
                  page_regenerate_count: pollData.page_regenerate_count,
                };
              });
              setSuccessMessage(`${getPageLabel(pageKey)} yeniden çizildi!`);
              setTimeout(() => setSuccessMessage(null), 4000);
            } else {
              // Backend still processing or failed
              setError("İşlem devam ediyor. Birkaç dakika sonra sayfayı yenileyin.");
            }
          } else {
            setError("Bağlantı zaman aşımına uğradı. Sayfayı yenileyerek kontrol edin.");
          }
        } catch {
          setError("Bağlantı zaman aşımına uğradı. Sayfayı yenileyerek kontrol edin.");
        }
      } else {
        setError("Yeniden çizim sırasında hata oluştu.");
      }
    } finally {
      clearTimeout(safetyTimeout);
      setRegeneratingKey(null);
    }
  };

  const getPageImageUrl = (pageKey: string): string | null => {
    if (!preview) return null;
    if (pageKey === "back_cover") return preview.back_cover_image_url ?? null;
    if (!preview.page_images) return null;
    return preview.page_images[pageKey] ?? preview.page_images[`page_${pageKey}`] ?? null;
  };

  // Loading
  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-purple-50 to-pink-50 p-4">
        <Card className="w-full max-w-md">
          <CardContent className="py-12 text-center">
            <div className="mx-auto mb-4 h-12 w-12 animate-spin rounded-full border-4 border-purple-600 border-t-transparent" />
            <p className="text-gray-600">Kitabınız yükleniyor...</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Error (no preview data)
  if (error && !preview) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-purple-50 to-pink-50 p-4">
        <Card className="w-full max-w-md">
          <CardContent className="py-12 text-center">
            <h2 className="mb-2 text-xl font-bold text-red-600">Hata</h2>
            <p className="mb-6 text-gray-600">{error}</p>
            <Button onClick={() => router.push("/")}>Ana Sayfaya Dön</Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!preview) return null;

  // Processing
  if (preview.status === "PROCESSING" || preview.status === "QUEUE_FAILED") {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-purple-50 to-pink-50 p-4">
        <Card className="w-full max-w-md">
          <CardContent className="py-12 text-center">
            <div className="mx-auto mb-4 h-16 w-16 animate-spin rounded-full border-4 border-purple-600 border-t-transparent" />
            <h2 className="mb-2 text-xl font-bold text-purple-700">Kitabınız Hazırlanıyor</h2>
            <p className="text-gray-600">
              <strong>{preview.child_name}</strong> için &quot;{preview.story_title}&quot;
              kitabı henüz oluşturuluyor. Tamamlandığında size tekrar e-posta göndereceğiz.
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Expired
  if (preview.status === "EXPIRED") {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-orange-50 to-red-50 p-4">
        <Card className="w-full max-w-md">
          <CardContent className="py-12 text-center">
            <h2 className="mb-2 text-xl font-bold text-orange-600">Onay Süresi Doldu</h2>
            <p className="mb-6 text-gray-600">
              Bu onay linkinin süresi dolmuş. Lütfen bizimle iletişime geçin
              veya yeni bir sipariş oluşturun.
            </p>
            <Button onClick={() => router.push("/create-v2")}>Yeni Hikaye Oluştur</Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Confirmed
  if (confirmed || preview.status === "CONFIRMED") {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-green-50 to-emerald-50 p-4">
        <Card className="w-full max-w-md border-green-200">
          <CardHeader className="rounded-t-lg bg-gradient-to-r from-green-500 to-emerald-500 text-center text-white">
            <CardTitle className="text-2xl">Kitap Onaylandı!</CardTitle>
          </CardHeader>
          <CardContent className="py-8 text-center">
            <p className="mb-2 text-lg text-gray-700">
              <strong>{preview.child_name}</strong> için hazırlanan
            </p>
            <p className="mb-4 text-xl font-bold text-purple-700">
              &quot;{preview.story_title}&quot;
            </p>
            <p className="mb-6 text-gray-600">
              Kitabınızı onayladınız! Baskıya hazırlanıyor.
            </p>
            <div className="flex gap-4">
              <Button variant="outline" className="flex-1" onClick={() => router.push("/")}>
                Ana Sayfa
              </Button>
              <Button
                className="flex-1 bg-green-600 hover:bg-green-700"
                onClick={() => router.push("/create-v2")}
              >
                Yeni Hikaye
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // ── PENDING: main preview flow ──
  // Page order: [Front Cover (0)] → [Dedication] → [Inner Pages] → [Back Cover]
  const orderedKeys: string[] = [];
  if (preview.page_images["0"] || preview.page_images["page_0"]) orderedKeys.push("0");
  if (preview.page_images["dedication"]) orderedKeys.push("dedication");
  const numericKeys = Object.keys(preview.page_images)
    .filter((k) => k !== "0" && k !== "page_0" && k !== "dedication")
    .sort((a, b) => {
      const na = Number.parseInt(a.replace("page_", ""), 10);
      const nb = Number.parseInt(b.replace("page_", ""), 10);
      return (Number.isNaN(na) ? 999 : na) - (Number.isNaN(nb) ? 999 : nb);
    });
  orderedKeys.push(...numericKeys);
  // Back cover image appended as last entry if available
  if (preview.back_cover_image_url) orderedKeys.push("back_cover");

  const textByPage: Record<string, string> = {};
  for (const sp of preview.story_pages) {
    textByPage[String(sp.page_number)] = sp.text;
  }
  if (preview.dedication_note) {
    textByPage["dedication"] = preview.dedication_note;
  } else {
    // Use AI-generated dedication text from front_matter story page
    const dedPage = preview.story_pages.find(
      (sp) => sp.page_type === "front_matter"
    );
    if (dedPage?.text) {
      textByPage["dedication"] = dedPage.text;
    }
  }

  const regenRemaining = (preview.max_page_regenerations ?? 4) - (preview.page_regenerate_count ?? 0);
  const canRegenerate = preview.status === "PENDING" || preview.status === "PREVIEW_GENERATED";

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-pink-50 p-4 pb-32">
      {/* Header */}
      <div className="mx-auto mb-6 max-w-4xl text-center">
        <h1 className="mb-1 text-2xl font-bold text-gray-800 sm:text-3xl">
          {preview.story_title}
        </h1>
        <p className="text-base text-gray-600 sm:text-lg">
          {preview.child_name} için hazırlanan kitabınızı inceleyin
        </p>
        <p className="mt-1 text-sm text-gray-500">
          {preview.page_count} sayfa &bull; {preview.image_count} görsel hazır
          {canRegenerate && regenRemaining > 0 && (
            <span className="ml-2 text-purple-600">
              &bull; {regenRemaining} yeniden çizim hakkı
            </span>
          )}
        </p>
      </div>

      {/* Success toast */}
      {successMessage && (
        <div className="mx-auto mb-4 max-w-md rounded-lg bg-green-50 px-4 py-3 text-center text-sm text-green-700">
          {successMessage}
        </div>
      )}

      {/* Error toast */}
      {error && (
        <div className="mx-auto mb-4 max-w-md rounded-lg bg-red-50 px-4 py-3 text-center text-sm text-red-700">
          {error}
          <button onClick={() => setError(null)} className="ml-2 font-bold">
            ✕
          </button>
        </div>
      )}

      {/* Confirm dialog */}
      {showConfirmDialog && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <Card className="w-full max-w-sm">
            <CardContent className="pt-6 text-center">
              <h3 className="mb-2 text-lg font-bold text-gray-800">Kitabı Onaylamak İstiyor musunuz?</h3>
              <p className="mb-6 text-sm text-gray-600">
                Onayladığınızda kitabınız baskıya gönderilecektir. Bu işlem geri alınamaz.
              </p>
              <div className="flex gap-3">
                <Button
                  variant="outline"
                  className="flex-1"
                  onClick={() => setShowConfirmDialog(false)}
                >
                  Vazgeç
                </Button>
                <Button
                  className="flex-1 bg-green-600 hover:bg-green-700"
                  onClick={handleConfirm}
                >
                  Evet, Onayla
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Lightbox */}
      {lightboxIndex !== null && (
        <ImageLightbox
          orderedKeys={orderedKeys}
          currentIndex={lightboxIndex}
          getImageUrl={getPageImageUrl}
          textByPage={textByPage}
          onClose={() => setLightboxIndex(null)}
          onNavigate={setLightboxIndex}
          onRegenerate={handleRegenerate}
          regeneratingKey={regeneratingKey}
          regenRemaining={regenRemaining}
          canRegenerate={canRegenerate}
        />
      )}

      {/* Page gallery — responsive grid */}
      <div className="mx-auto max-w-5xl">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {orderedKeys.map((key, idx) => {
            const url = getPageImageUrl(key);
            const label = getPageLabel(key);
            const text = textByPage[key] || "";
            const isThisRegen = regeneratingKey === key;
            return (
              <div
                key={key}
                role="button"
                tabIndex={0}
                className="group cursor-pointer overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm transition hover:shadow-lg"
                onClick={() => setLightboxIndex(idx)}
                onKeyDown={(e) => { if (e.key === "Enter") setLightboxIndex(idx); }}
              >
                {url ? (
                  <div className="relative">
                    <Image
                      src={url}
                      alt={label}
                      width={900}
                      height={600}
                      className={`aspect-[3/4] w-full object-contain bg-gray-50 transition ${isThisRegen ? "opacity-40" : ""}`}
                      unoptimized
                    />
                    {isThisRegen ? (
                      <div className="absolute inset-0 flex flex-col items-center justify-center bg-black/20">
                        <div className="h-8 w-8 animate-spin rounded-full border-3 border-white border-t-transparent" />
                        <span className="mt-2 text-xs font-medium text-white">Yeniden ciziliyor...</span>
                      </div>
                    ) : (
                      <div className="pointer-events-none absolute inset-0 flex items-center justify-center bg-black/0 transition group-hover:bg-black/10">
                        <span className="scale-0 rounded-full bg-white/90 px-3 py-1.5 text-xs font-medium text-gray-700 shadow transition group-hover:scale-100">
                          Buyut
                        </span>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="flex aspect-[3/4] items-center justify-center bg-gray-100 text-gray-400">
                    Gorsel yok
                  </div>
                )}
                <div className="p-3">
                  <p className="text-sm font-semibold text-purple-600">{label}</p>
                  {text && (
                    <p className="mt-1 line-clamp-3 text-sm leading-relaxed text-gray-600">
                      {text}
                    </p>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Fixed bottom confirmation bar */}
      {!confirmed && (preview.status === "PENDING" || preview.status === "PREVIEW_GENERATED") && (
        <div className="fixed bottom-0 left-0 right-0 border-t border-gray-200 bg-white/95 px-4 py-4 shadow-lg backdrop-blur">
          <div className="mx-auto flex max-w-4xl flex-col items-center gap-3 sm:flex-row sm:justify-between">
            <div className="text-center sm:text-left">
              <p className="font-medium text-gray-800">
                Kitabınız hazır! Beğendiyseniz onaylayın.
              </p>
              <p className="text-sm text-gray-500">
                Onayladığınızda baskı sürecine geçilecektir.
              </p>
            </div>
            <Button
              size="lg"
              className="w-full bg-green-600 px-8 hover:bg-green-700 sm:w-auto"
              onClick={() => setShowConfirmDialog(true)}
              disabled={confirming || regeneratingKey !== null}
            >
              <ConfirmButtonLabel confirming={confirming} busy={regeneratingKey !== null} />
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
