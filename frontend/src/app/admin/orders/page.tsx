"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useToast } from "@/hooks/use-toast";
import { API_BASE_URL } from "@/lib/api";
import JSZip from "jszip";

// ─── Lazy Image Component ────────────────────────────────────────────────
// Only loads image when it enters the viewport via IntersectionObserver
interface LazyImageProps {
  readonly src: string;
  readonly alt: string;
  readonly className?: string;
}

function LazyImage({ src, alt, className }: LazyImageProps) {
  const imgRef = useRef<HTMLDivElement>(null);
  const [isVisible, setIsVisible] = useState(false);
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState(false);

  // Reset all state when src changes (order switch) and re-observe
  useEffect(() => {
    setIsVisible(false);
    setLoaded(false);
    setError(false);

    const el = imgRef.current;
    if (!el) return;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true);
          observer.disconnect();
        }
      },
      { rootMargin: "200px" }
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, [src]);

  return (
    <div ref={imgRef} className={`relative ${className ?? ""}`}>
      {!loaded && !error && (
        <div className="absolute inset-0 flex items-center justify-center rounded bg-gray-100">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-gray-300 border-t-purple-500" />
        </div>
      )}
      {error && (
        <div className="absolute inset-0 flex items-center justify-center rounded bg-gray-100">
          <span className="text-xs text-gray-400">Yüklenemedi</span>
        </div>
      )}
      {isVisible && (
        <img
          key={src}
          src={src}
          alt={alt}
          className={`h-full w-full rounded object-cover ${loaded ? "opacity-100" : "opacity-0"} transition-opacity duration-300`}
          onLoad={() => setLoaded(true)}
          onError={() => setError(true)}
        />
      )}
    </div>
  );
}

interface StoryPageContent {
  text?: string;
  image_prompt?: string;
  visual_prompt?: string; // Görsel üretim promptu (final_prompt)
  is_back_cover?: boolean;
}

interface StoryPreview {
  id: string;
  status: string;
  parent_name: string;
  parent_email: string;
  parent_phone: string | null;
  child_name: string;
  child_age: number;
  child_gender: string | null;
  story_title: string;
  product_name: string | null;
  product_price: number | null;
  scenario_name: string | null;
  visual_style_name: string | null;
  learning_outcomes: string[] | null;
  story_pages: StoryPageContent[] | null;
  page_count: number;
  page_images: Record<string, string> | null;
  dedication_note?: string | null;
  confirmed_at: string | null;
  created_at: string;
  admin_notes?: string | null;
  // Audio book fields
  has_audio_book?: boolean;
  has_coloring_book?: boolean;
  audio_type?: string | null;
  audio_voice_id?: string | null;
  voice_sample_url?: string | null;
  // Generated URLs
  pdf_url?: string | null;
  coloring_pdf_url?: string | null;
  back_cover_image_url?: string | null;
  cover_spread_image_url?: string | null;
  // Generation manifest per page (debug)
  generation_manifest_json?: Record<
    string,
    {
      provider?: string;
      model?: string;
      num_inference_steps?: number;
      guidance_scale?: number;
      width?: number;
      height?: number;
      is_cover?: boolean;
      prompt_hash?: string;
      negative_hash?: string;
      reference_image_used?: boolean;
      final_prompt?: string;
      negative_prompt?: string;
    }
  > | null;
  // Prompt debug: final_prompt, negative_prompt per page
  prompt_debug_json?: Record<
    string,
    {
      final_prompt?: string;
      negative_prompt?: string;
    }
  > | null;
  // Per-page prompt data with metadata (keyed by page_number)
  prompts_by_page?: Record<string, {
    final_prompt: string;
    negative_prompt: string;
    pipeline_version?: string;
    composer_version?: string;
    page_type?: string;
    page_index?: number;
    story_page_number?: number | null;
  }> | null;
  // Pipeline version (V3 only)
  pipeline_version?: string | null;
  pipeline_label?: string | null;
}

interface Stats {
  total: number;
  pending: number;
  confirmed: number;
  expired: number;
  total_revenue: number;
}

interface BackCoverConfig {
  id: string;
  name: string;
  company_name: string;
  company_website: string;
  company_email: string;
  tagline: string;
  tips_title: string;
  tips_content: string;
  copyright_text: string;
  background_color: string;
  primary_color: string;
  text_color: string;
  border_color: string;
  qr_enabled: boolean;
  qr_label: string;
  show_border: boolean;
}

export default function AdminOrdersPage() {
  const [previews, setPreviews] = useState<StoryPreview[]>([]);
  const [totalPreviews, setTotalPreviews] = useState(0);
  const [currentPage, setCurrentPage] = useState(0); // 0-based page index
  const PAGE_SIZE = 30;
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>(""); // Show all by default
  const [selectedPreview, setSelectedPreview] = useState<StoryPreview | null>(null);
  const [detailData, setDetailData] = useState<StoryPreview | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [backCoverConfig, setBackCoverConfig] = useState<BackCoverConfig | null>(null);
  const [pdfDownloading, setPdfDownloading] = useState(false);
  const [zipDownloading, setZipDownloading] = useState(false);

  // AbortController ref — cancel stale detail fetches when switching orders
  const detailAbortRef = useRef<AbortController | null>(null);

  const router = useRouter();
  const { toast } = useToast();

  /** Image proxy URL — now returns direct page_images URL from detail data */
  const pageImageProxyUrl = (_previewId: string, pageKey: string, _thumbWidth?: number): string => {
    // Proxy endpoint removed; use direct GCS URLs from page_images in detail data
    if (detailData?.page_images) {
      const url = detailData.page_images[pageKey] || detailData.page_images[String(pageKey)];
      if (url) return url;
    }
    // Fallback: return empty string (image won't load but won't crash)
    return "";
  };

  useEffect(() => {
    checkAuth();
    fetchStats();
    setCurrentPage(0);
    fetchPreviews(0);
    fetchBackCoverConfig();
  }, [statusFilter]);

  // PROCESSING veya CONFIRMED ama eksik sayfa varsa periyodik yenile (progressive backoff)
  const pollTickRef = useRef(0);
  useEffect(() => {
    if (!selectedPreview?.id || !detailData) return;
    const isProcessing = detailData.status === "PROCESSING";
    const pageCount = detailData.page_count ?? 0;
    const imageCount = detailData.page_images ? Object.keys(detailData.page_images).length : 0;
    const isIncompleteConfirmed =
      detailData.status === "CONFIRMED" && pageCount > 0 && imageCount < pageCount;
    if (!isProcessing && !isIncompleteConfirmed) {
      pollTickRef.current = 0;
      return;
    }
    // Progressive backoff: 5s, 10s, 15s, 30s, 30s, ...
    const BACKOFF = [5000, 10000, 15000, 30000];
    const delay = BACKOFF[Math.min(pollTickRef.current, BACKOFF.length - 1)];
    const timer = setTimeout(async () => {
      try {
        // Polling: sessiz fetch, toast atma — hata olursa sadece loglayip devam et
        await fetchPreviewDetail(selectedPreview.id);
        // Liste için sessiz fetch (mevcut sayfa, toast spam önlemek için)
        const params = new URLSearchParams();
        if (statusFilter) params.set("status", statusFilter);
        params.set("limit", String(PAGE_SIZE));
        params.set("offset", String(currentPage * PAGE_SIZE));
        const url = `${API_BASE_URL}/admin/orders/previews?${params.toString()}`;
        const res = await fetch(url, { headers: getAuthHeaders() });
        if (res.ok) {
          const data = await res.json();
          if (data.items) {
            setPreviews(data.items);
            setTotalPreviews(data.total ?? data.items.length);
          } else if (Array.isArray(data)) {
            setPreviews(data);
          }
        }
      } catch {
        // Polling hatası - sessizce atla, sonraki tick'te tekrar dene
      }
      pollTickRef.current += 1;
    }, delay);
    return () => clearTimeout(timer);
  }, [selectedPreview?.id, detailData?.status, detailData?.page_count, detailData?.page_images, pollTickRef.current]);

  const fetchBackCoverConfig = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/admin/back-cover/default`, { headers: getAuthHeaders() });
      if (response.ok) {
        const data = await response.json();
        setBackCoverConfig(data);
      }
    } catch (error) {
      console.error("Failed to fetch back cover config:", error);
    }
  };

  const checkAuth = () => {
    const user = localStorage.getItem("user");
    if (!user) {
      router.push("/auth/login");
      return;
    }
    const userData = JSON.parse(user);
    if (userData.role !== "admin") {
      router.push("/");
    }
  };

  const getAuthHeaders = () => {
    const token = localStorage.getItem("token");
    return {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    };
  };

  const fetchStats = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/admin/orders/stats/previews`, {
        headers: getAuthHeaders(),
      });
      if (response.ok) {
        const data = await response.json();
        setStats({
          total: data.total ?? 0,
          pending: data.pending ?? 0,
          confirmed: data.confirmed ?? 0,
          expired: data.expired ?? 0,
          total_revenue: data.total_revenue ?? 0,
        });
      }
    } catch (error) {
      console.error("Failed to fetch stats:", error);
    }
  };

  const fetchPreviews = async (page?: number) => {
    setLoading(true);
    try {
      const pg = page ?? currentPage;
      const params = new URLSearchParams();
      if (statusFilter) params.set("status", statusFilter);
      params.set("limit", String(PAGE_SIZE));
      params.set("offset", String(pg * PAGE_SIZE));
      const url = `${API_BASE_URL}/admin/orders/previews?${params.toString()}`;

      const response = await fetch(url, { headers: getAuthHeaders() });
      if (response.ok) {
        const data = await response.json();
        // New paginated format: { items, total, limit, offset }
        if (data.items) {
          setPreviews(data.items);
          setTotalPreviews(data.total ?? data.items.length);
        } else if (Array.isArray(data)) {
          // Backward compat: old format returns plain array
          setPreviews(data);
          setTotalPreviews(data.length);
        }
      } else {
        const errorData = await response.json().catch(() => ({}));
        console.error("API Error:", response.status, errorData);
        const detail = errorData.detail;
        const msg = typeof detail === "string" ? detail : Array.isArray(detail) ? detail.map((d: { msg?: string }) => d.msg || JSON.stringify(d)).join(", ") : "Siparişler yüklenemedi";
        toast({
          title: "Hata",
          description: msg,
          variant: "destructive",
        });
      }
    } catch (error) {
      console.error("Failed to fetch previews:", error);
      toast({
        title: "Bağlantı Hatası",
        description: "Backend'e bağlanılamadı",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const fetchPreviewDetail = useCallback(async (id: string) => {
    // Cancel any in-flight detail request
    if (detailAbortRef.current) {
      detailAbortRef.current.abort();
    }
    const controller = new AbortController();
    detailAbortRef.current = controller;

    setDetailLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/admin/orders/previews/${id}`, {
        headers: getAuthHeaders(),
        signal: controller.signal,
      });
      if (response.ok) {
        const data = await response.json();
        // Only set if this request wasn't aborted
        if (!controller.signal.aborted) {
          setDetailData(data);
          setDetailLoading(false);
        }
      } else {
        if (!controller.signal.aborted) {
          console.error("Failed to fetch detail:", response.status);
          setDetailLoading(false);
        }
      }
    } catch (error) {
      if (error instanceof DOMException && error.name === "AbortError") {
        // Request was cancelled — expected when switching orders quickly
        return;
      }
      console.error("Failed to fetch detail:", error);
      setDetailLoading(false);
    }
  }, []);

  const updateStatus = async (id: string, newStatus: string) => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/admin/orders/previews/${id}/status?status=${newStatus}`,
        { method: "PATCH", headers: getAuthHeaders() }
      );
      if (response.ok) {
        toast({ title: "Başarılı", description: `Durum ${newStatus} olarak güncellendi` });
        fetchPreviews(currentPage);
        fetchStats();
        // Immediately fetch updated details to reflect status change without page reload
        fetchPreviewDetail(id);
      } else {
        const errorData = await response.json().catch(() => ({}));
        toast({
          title: "Hata",
          description: errorData.detail || "Güncelleme başarısız",
          variant: "destructive",
        });
      }
    } catch (error) {
      toast({ title: "Hata", description: "Güncelleme başarısız", variant: "destructive" });
    }
  };

  const generateBook = async (previewId: string) => {
    const token = localStorage.getItem("token");
    if (!token) {
      router.push("/auth/login");
      return;
    }

    try {
      toast({
        title: "Kitap oluşturuluyor...",
        description: "Bu işlem birkaç dakika sürebilir. Lütfen bekleyin.",
      });

      const response = await fetch(
        `${API_BASE_URL}/admin/orders/previews/${previewId}/generate-book`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        }
      );

      if (response.status === 401) {
        toast({ title: "Oturum süresi doldu", description: "Lütfen tekrar giriş yapın.", variant: "destructive" });
        localStorage.removeItem("token");
        router.push("/auth/login");
        return;
      }

      const data = await response.json();

      if (response.ok && data.success) {
        // Store PDF URL immediately in state so download button works right away
        if (data.pdf_url) {
          setDetailData((prev) => (prev ? { ...prev, pdf_url: data.pdf_url } : prev));
          toast({
            title: "Kitap Hazır!",
            description: "PDF indirme bağlantısı açılıyor...",
          });
          // Auto-download: open PDF in new tab
          window.open(data.pdf_url, "_blank");
        } else if (data.pdf_error) {
          toast({
            title: "PDF oluşturulamadı",
            description: `Hata: ${data.pdf_error}. Lütfen tekrar deneyin.`,
            variant: "destructive",
          });
        } else {
          toast({
            title: "Kitap oluşturuldu",
            description: data.audio_url
              ? "Ses dosyası hazır. PDF oluşturulurken sorun oluştu, tekrar deneyin."
              : "İşlem tamamlandı ancak PDF oluşturulamadı. Tekrar deneyin.",
            variant: "destructive",
          });
        }

        // Refresh detail data (picks up pdf_url from backend too)
        fetchPreviewDetail(previewId);
      } else {
        throw new Error(data.detail || "Kitap oluşturma başarısız");
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : "Kitap oluşturma başarısız";
      toast({
        title: "Hata",
        description: message,
        variant: "destructive",
      });
    }
  };

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      PENDING: "bg-yellow-100 text-yellow-800",
      CONFIRMED: "bg-green-100 text-green-800",
      EXPIRED: "bg-gray-100 text-gray-600",
      CANCELLED: "bg-red-100 text-red-800",
      PROCESSING: "bg-blue-100 text-blue-800",
      FAILED: "bg-red-100 text-red-800",
      QUEUE_FAILED: "bg-orange-100 text-orange-800",
    };
    return colors[status] || "bg-gray-100 text-gray-800";
  };

  const getStatusLabel = (status: string) => {
    const labels: Record<string, string> = {
      PENDING: "Beklemede",
      CONFIRMED: "Onaylandı",
      EXPIRED: "Süresi Doldu",
      CANCELLED: "İptal",
      PROCESSING: "İşleniyor",
      FAILED: "Başarısız",
      QUEUE_FAILED: "Kuyruk Hatası",
    };
    return labels[status] || status;
  };

  /** Tek bir resmi indir (blob ile) */
  const downloadSingleImage = async (url: string, filename: string) => {
    try {
      const res = await fetch(url);
      if (!res.ok) throw new Error("Resim indirilemedi");
      const blob = await res.blob();
      const blobUrl = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = blobUrl;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(blobUrl);
    } catch {
      toast({ title: "Hata", description: `"${filename}" indirilemedi`, variant: "destructive" });
    }
  };

  /** Tum resimleri ZIP olarak indir */
  const downloadAllImages = async () => {
    if (!detailData?.page_images || zipDownloading) return;
    setZipDownloading(true);

    const childName = (detailData.child_name || "kitap").replace(/\s+/g, "_");
    const zipFilename = `${childName}_gorseller.zip`;

    try {
      const zip = new JSZip();
      const entries = Object.entries(detailData.page_images).sort(([a], [b]) => {
        const order = (k: string) => {
          if (k === "dedication") return -2;
          if (k === "intro") return -1;
          return parseInt(k) || 0;
        };
        return order(a) - order(b);
      });

      // Include back cover image in ZIP
      if (detailData.back_cover_image_url) {
        entries.push(["back_cover", detailData.back_cover_image_url]);
      }

      let downloaded = 0;
      toast({
        title: "Resimler indiriliyor...",
        description: `0 / ${entries.length} tamamlandı`,
      });

      for (const [pageKey, url] of entries) {
        try {
          const res = await fetch(url);
          if (!res.ok) continue;
          const blob = await res.blob();
          const ext = blob.type.includes("png") ? "png" : "jpg";
          const name =
            pageKey === "dedication"
              ? `00_karsilama_1.${ext}`
              : pageKey === "intro"
                ? `01_karsilama_2.${ext}`
                : pageKey === "back_cover"
                  ? `99_arka_kapak.${ext}`
                  : `${String(parseInt(pageKey) + 2).padStart(2, "0")}_sayfa.${ext}`;
          zip.file(name, blob);
          downloaded++;
        } catch {
          // skip failed images
        }
      }

      if (downloaded === 0) {
        toast({ title: "Hata", description: "Hiçbir resim indirilemedi", variant: "destructive" });
        return;
      }

      const zipBlob = await zip.generateAsync({ type: "blob" });
      const blobUrl = URL.createObjectURL(zipBlob);
      const link = document.createElement("a");
      link.href = blobUrl;
      link.download = zipFilename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(blobUrl);

      toast({
        title: "Tamamlandı",
        description: `${downloaded} resim ZIP olarak indirildi`,
      });
    } catch {
      toast({ title: "Hata", description: "ZIP oluşturulamadı", variant: "destructive" });
    } finally {
      setZipDownloading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4">
          <div className="flex items-center gap-4">
            <Button variant="outline" onClick={() => router.push("/admin")}>
              ← Geri
            </Button>
            <h1 className="text-2xl font-bold text-purple-800">Sipariş Yönetimi</h1>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-[1800px] px-4 py-6">
        {/* Stats Cards - Compact */}
        {stats && (
          <div className="mb-6 grid grid-cols-5 gap-3">
            <Card className="py-2">
              <CardHeader className="px-3 pb-1 pt-2">
                <CardDescription className="text-xs">Toplam</CardDescription>
                <CardTitle className="text-xl">{stats.total}</CardTitle>
              </CardHeader>
            </Card>
            <Card className="border-yellow-200 py-2">
              <CardHeader className="px-3 pb-1 pt-2">
                <CardDescription className="text-xs">Beklemede</CardDescription>
                <CardTitle className="text-xl text-yellow-600">{stats.pending}</CardTitle>
              </CardHeader>
            </Card>
            <Card className="border-green-200 py-2">
              <CardHeader className="px-3 pb-1 pt-2">
                <CardDescription className="text-xs">Onaylanan</CardDescription>
                <CardTitle className="text-xl text-green-600">{stats.confirmed}</CardTitle>
              </CardHeader>
            </Card>
            <Card className="py-2">
              <CardHeader className="px-3 pb-1 pt-2">
                <CardDescription className="text-xs">Süresi Dolan</CardDescription>
                <CardTitle className="text-xl text-gray-500">{stats.expired}</CardTitle>
              </CardHeader>
            </Card>
            <Card className="border-purple-200 py-2">
              <CardHeader className="px-3 pb-1 pt-2">
                <CardDescription className="text-xs">Toplam Gelir</CardDescription>
                <CardTitle className="text-xl text-purple-600">
                  {stats.total_revenue.toLocaleString("tr-TR")} TL
                </CardTitle>
              </CardHeader>
            </Card>
          </div>
        )}

        {/* Filters */}
        <div className="mb-4 flex gap-2">
          {["", "PENDING", "PROCESSING", "CONFIRMED", "FAILED", "QUEUE_FAILED", "EXPIRED", "CANCELLED"].map(
            (status) => (
              <Button
                key={status || "all"}
                variant={statusFilter === status ? "default" : "outline"}
                size="sm"
                onClick={() => setStatusFilter(status)}
              >
                {status === "" ? "Tümü" : getStatusLabel(status)}
              </Button>
            )
          )}
        </div>

        {/* Main Layout - Fixed sidebar + Flexible content */}
        <div className="flex gap-6">
          {/* Left: Order List - Fixed width */}
          <div className="w-[340px] flex-shrink-0 space-y-3">
            {loading ? (
              <div className="py-8 text-center">Yükleniyor...</div>
            ) : previews.length === 0 ? (
              <Card>
                <CardContent className="py-8 text-center text-gray-500">
                  Bu kategoride sipariş yok
                </CardContent>
              </Card>
            ) : (
              previews.map((preview: StoryPreview) => {
                // Liste verisi artik hafif: has_cover flag ile kapak var mi kontrol et
                const coverUrl = preview.page_images?.["0"] ?? preview.page_images?.["page_0"] ?? null;
                const coverSrc = coverUrl || null;
                return (
                  <Card
                    key={preview.id}
                    className={`cursor-pointer transition hover:shadow-md ${selectedPreview?.id === preview.id
                      ? "bg-purple-50 ring-2 ring-purple-500"
                      : ""
                      }`}
                    onClick={() => {
                      if (selectedPreview?.id === preview.id) return; // same order, no-op
                      setSelectedPreview(preview);
                      setDetailData(null); // clear old data immediately
                      fetchPreviewDetail(preview.id);
                    }}
                  >
                    <CardContent className="px-3 py-3">
                      <div className="flex gap-2">
                        {/* Cover Thumbnail - Smaller */}
                        {coverSrc ? (
                          <LazyImage
                            src={coverSrc}
                            alt="Kapak"
                            className="h-16 w-12 flex-shrink-0 overflow-hidden rounded bg-gray-100"
                          />
                        ) : (
                          <div className="flex h-16 w-12 flex-shrink-0 items-center justify-center rounded bg-gray-100">
                            <span className="text-lg">📖</span>
                          </div>
                        )}

                        {/* Info - Compact */}
                        <div className="min-w-0 flex-1">
                          <div className="mb-0.5 flex items-center gap-1.5">
                            <span
                              className={`rounded px-1.5 py-0.5 text-[10px] font-medium ${getStatusColor(preview.status)}`}
                            >
                              {getStatusLabel(preview.status)}
                            </span>
                            {preview.product_price && (
                              <span className="text-xs font-medium text-purple-600">
                                {preview.product_price} TL
                              </span>
                            )}
                          </div>
                          <h3 className="truncate text-sm font-semibold leading-tight">
                            {preview.story_title}
                          </h3>
                          <p className="truncate text-xs text-gray-600">
                            {preview.child_name} ({preview.child_age} yaş)
                          </p>
                          <p className="truncate text-[10px] text-gray-400">
                            {preview.parent_name}
                          </p>
                          <p className="text-[10px] text-gray-400">
                            {preview.page_count} sayfa
                            {preview.page_images &&
                              Object.keys(preview.page_images).length > 0 &&
                              ` (${Object.keys(preview.page_images).length} görsel)`}
                            {" • "}
                            {new Date(preview.created_at).toLocaleDateString("tr-TR")}
                          </p>

                          {/* Style & Scenario Info */}
                          <div className="mt-1 flex flex-wrap gap-1">
                            {preview.scenario_name && (
                              <span className="rounded bg-purple-100 px-1.5 py-0.5 text-[9px] text-purple-700">
                                📍 {preview.scenario_name}
                              </span>
                            )}
                            {preview.visual_style_name && (
                              <span className="rounded bg-blue-100 px-1.5 py-0.5 text-[9px] text-blue-700">
                                🎨 {preview.visual_style_name}
                              </span>
                            )}
                            {preview.has_audio_book && (
                              <span className="rounded bg-indigo-100 px-1.5 py-0.5 text-[9px] text-indigo-700">
                                🎧 Sesli
                              </span>
                            )}
                            {preview.has_coloring_book && (
                              <span className="rounded bg-pink-100 px-1.5 py-0.5 text-[9px] text-pink-700 font-semibold" title="Bu siparişe Boyama Kitabı dahil edilmiştir.">
                                🖍️ Boyama Kitabı
                              </span>
                            )}
                          </div>

                          {/* Learning Outcomes */}
                          {preview.learning_outcomes && preview.learning_outcomes.length > 0 && (
                            <div className="mt-1 flex flex-wrap gap-1">
                              {preview.learning_outcomes.slice(0, 3).map((outcome: string, idx: number) => (
                                <span
                                  key={idx}
                                  className="rounded bg-yellow-100 px-1.5 py-0.5 text-[9px] text-yellow-700"
                                >
                                  ⭐ {outcome}
                                </span>
                              ))}
                              {preview.learning_outcomes.length > 3 && (
                                <span className="text-[9px] text-gray-500">
                                  +{preview.learning_outcomes.length - 3}
                                </span>
                              )}
                            </div>
                          )}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                );
              })
            )}

            {/* Pagination */}
            {totalPreviews > PAGE_SIZE && (
              <div className="flex items-center justify-between pt-2">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={currentPage === 0}
                  onClick={() => {
                    const prev = currentPage - 1;
                    setCurrentPage(prev);
                    fetchPreviews(prev);
                  }}
                >
                  ← Önceki
                </Button>
                <span className="text-xs text-gray-500">
                  {currentPage * PAGE_SIZE + 1}–{Math.min((currentPage + 1) * PAGE_SIZE, totalPreviews)} / {totalPreviews}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={(currentPage + 1) * PAGE_SIZE >= totalPreviews}
                  onClick={() => {
                    const next = currentPage + 1;
                    setCurrentPage(next);
                    fetchPreviews(next);
                  }}
                >
                  Sonraki →
                </Button>
              </div>
            )}
          </div>

          {/* Right: Order Detail - Flexible width */}
          <div className="min-w-0 flex-1">
            {selectedPreview && detailLoading && !detailData ? (
              <Card>
                <CardContent className="py-12 text-center text-gray-500">
                  <div className="border-3 mx-auto mb-3 h-8 w-8 animate-spin rounded-full border-gray-300 border-t-purple-500" />
                  <p className="text-sm">Sipariş detayları yükleniyor...</p>
                </CardContent>
              </Card>
            ) : selectedPreview && detailData ? (
              <Card className="sticky top-4">
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <CardTitle className="text-xl">{detailData.story_title}</CardTitle>
                        {detailData.has_coloring_book && (
                          <span className="rounded bg-pink-100 px-2 py-0.5 text-xs font-semibold text-pink-700">
                            🖍️ Boyama Kitabı
                          </span>
                        )}
                      </div>
                      <CardDescription>
                        {detailData.child_name} için - {detailData.story_pages?.length || 0} sayfa
                      </CardDescription>
                    </div>
                    <div className="flex items-center gap-2">
                      {(() => {
                        const manifest = detailData.generation_manifest_json;
                        const anyMissingRef =
                          manifest &&
                          Object.values(manifest).some((m) => m?.reference_image_used === false);
                        return anyMissingRef ? (
                          <span
                            className="rounded-full bg-amber-100 px-2 py-1 text-xs font-medium text-amber-800"
                            title="En az bir sayfada referans (PuLID) kullanılmadı"
                          >
                            ⚠ Referans yok
                          </span>
                        ) : null;
                      })()}
                      <span
                        className={`rounded-full px-3 py-1 text-sm font-medium ${getStatusColor(detailData.status)}`}
                      >
                        {getStatusLabel(detailData.status)}
                      </span>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="max-h-[85vh] space-y-3 overflow-y-auto">
                  {/* FAILED: hata mesajı en üstte, hemen görünsün */}
                  {detailData.status === "FAILED" && (
                    <div className="rounded-lg border-2 border-red-300 bg-red-50 p-4">
                      <p className="text-sm font-semibold text-red-800">
                        Arka plan işlemi başarısız
                      </p>
                      <p className="mt-2 whitespace-pre-wrap font-mono text-sm text-red-700">
                        {detailData.admin_notes || "Hata mesajı kaydedilmemiş."}
                      </p>
                    </div>
                  )}

                  {/* Quick Info Grid - 4 columns */}
                  <div className="grid grid-cols-4 gap-2">
                    <div className="rounded-lg bg-gray-50 p-2">
                      <p className="text-[10px] text-gray-500">Ebeveyn</p>
                      <p className="truncate text-xs font-medium">{detailData.parent_name}</p>
                      <p className="truncate text-[10px] text-gray-600">
                        {detailData.parent_email}
                      </p>
                    </div>
                    <div className="rounded-lg bg-blue-50 p-2">
                      <p className="text-[10px] text-gray-500">Çocuk</p>
                      <p className="text-xs font-medium">{detailData.child_name}</p>
                      <p className="text-[10px] text-gray-600">
                        {detailData.child_age} yaş{" "}
                        {detailData.child_gender === "erkek"
                          ? "👦"
                          : detailData.child_gender === "kiz"
                            ? "👧"
                            : ""}
                      </p>
                    </div>
                    <div className="rounded-lg bg-purple-50 p-2">
                      <p className="text-[10px] text-gray-500">Ürün</p>
                      <p className="truncate text-xs font-medium">
                        {detailData.product_name || "-"}
                      </p>
                      <p className="text-sm font-bold text-purple-600">
                        {detailData.product_price ? `${detailData.product_price} TL` : "-"}
                      </p>
                    </div>
                    <div className="rounded-lg bg-green-50 p-2">
                      <p className="text-[10px] text-gray-500">Senaryo & Stil</p>
                      <p className="truncate text-xs font-medium">
                        {detailData.scenario_name || "-"}
                      </p>
                      <p className="truncate text-[10px] text-gray-600">
                        {detailData.visual_style_name || ""}
                      </p>
                    </div>
                  </div>

                  {/* PROCESSING: info */}
                  {detailData.status === "PROCESSING" && (
                    <div className="rounded-lg border border-blue-200 bg-blue-50 p-3">
                      <p className="text-sm text-blue-800">
                        Görseller arka planda üretiliyor. Birkaç dakika sonra sayfayı yenileyin veya
                        detayı tekrar açın.
                      </p>
                    </div>
                  )}

                  {/* Actions (Moved Above Images) */}
                  <div className="flex gap-2 border-t border-b py-3 mt-2 mb-2">
                    {detailData.status === "PENDING" && (
                      <>
                        <Button
                          size="sm"
                          className="flex-1 bg-green-600 hover:bg-green-700"
                          onClick={() => updateStatus(detailData.id, "CONFIRMED")}
                        >
                          ✓ Onayla
                        </Button>
                        <Button
                          size="sm"
                          variant="destructive"
                          className="flex-1"
                          onClick={() => updateStatus(detailData.id, "CANCELLED")}
                        >
                          ✗ İptal Et
                        </Button>
                      </>
                    )}
                    {detailData.status === "CONFIRMED" && (
                      <>
                        <Button
                          size="sm"
                          className="flex-1 bg-green-600 hover:bg-green-700"
                          onClick={() => generateBook(detailData.id)}
                        >
                          🎵 {detailData.has_audio_book ? "Kitap + Ses Üret" : "Kitap Üret"}
                        </Button>
                        <Button
                          size="sm"
                          className="flex-1 bg-blue-600 hover:bg-blue-700"
                          disabled={pdfDownloading}
                          onClick={async () => {
                            if (pdfDownloading) return;
                            const token = localStorage.getItem("token");
                            if (!token) { router.push("/auth/login"); return; }
                            setPdfDownloading(true);
                            try {
                              // 1. Use cached pdf_url from state if available (fastest path)
                              let pdfUrl: string | null = detailData.pdf_url ?? null;

                              if (!pdfUrl) {
                                // 2. Ask backend for PDF URL
                                toast({ title: "PDF aranıyor...", description: "Lütfen bekleyin." });
                                const res = await fetch(
                                  `${API_BASE_URL}/admin/orders/previews/${detailData.id}/download-pdf`,
                                  { headers: { Authorization: `Bearer ${token}` } }
                                );

                                if (res.status === 401) {
                                  toast({ title: "Oturum süresi doldu", description: "Lütfen tekrar giriş yapın.", variant: "destructive" });
                                  localStorage.removeItem("token");
                                  router.push("/auth/login");
                                  return;
                                }

                                if (res.status === 404) {
                                  toast({ title: "PDF bulunamadı", description: "Önce 'Kitap Üret' butonuna basın.", variant: "destructive" });
                                  return;
                                }

                                let resData: Record<string, unknown>;
                                try { resData = await res.json(); } catch { throw new Error(`Sunucu hatası (HTTP ${res.status})`); }
                                if (!res.ok) throw new Error(typeof resData.detail === "string" ? resData.detail : "PDF alınamadı");
                                pdfUrl = resData.pdf_url as string;
                              }

                              if (!pdfUrl) throw new Error("PDF URL alınamadı");

                              // 3. Download the PDF
                              toast({ title: "PDF indiriliyor...", description: "Lütfen bekleyin." });
                              const pdfRes = await fetch(pdfUrl);
                              if (!pdfRes.ok) throw new Error("PDF dosyası indirilemedi");
                              const blob = await pdfRes.blob();
                              const sizeMb = (blob.size / 1024 / 1024).toFixed(1);
                              const downloadUrl = URL.createObjectURL(blob);
                              const link = document.createElement("a");
                              link.href = downloadUrl;
                              link.download = `kitap_${detailData.child_name || detailData.id}.pdf`;
                              document.body.appendChild(link);
                              link.click();
                              document.body.removeChild(link);
                              URL.revokeObjectURL(downloadUrl);
                              // Cache the url in state
                              setDetailData((prev) => (prev ? { ...prev, pdf_url: pdfUrl } : prev));
                              toast({ title: "PDF indirildi! ✅", description: `${sizeMb} MB` });
                            } catch (err: unknown) {
                              const message = err instanceof Error ? err.message : "PDF indirilemedi";
                              toast({ title: "Hata", description: message, variant: "destructive" });
                            } finally {
                              setPdfDownloading(false);
                            }
                          }}
                        >
                          {pdfDownloading ? "⏳ PDF Hazırlanıyor..." : "📥 PDF İndir"}
                        </Button>
                        <Button
                          size="sm"
                          className="flex-1 bg-purple-600 hover:bg-purple-700"
                          onClick={() => window.print()}
                        >
                          🖨️ Yazdır
                        </Button>
                        {detailData.has_coloring_book && (
                          <Button
                            size="sm"
                            className="flex-1 bg-pink-600 hover:bg-pink-700"
                            onClick={async () => {
                              if (detailData.coloring_pdf_url) {
                                window.open(detailData.coloring_pdf_url, "_blank");
                                toast({ title: "Açılıyor", description: "Boyama Kitabı PDF'i yeni sekmede açılıyor." });
                              } else {
                                // Trigger coloring book generation via admin API
                                const token = localStorage.getItem("token");
                                if (!token) { router.push("/auth/login"); return; }
                                toast({ title: "Başlatılıyor...", description: "Boyama kitabı üretimi arka planda tetikleniyor." });
                                try {
                                  const res = await fetch(
                                    `${API_BASE_URL}/admin/orders/previews/${detailData.id}/generate-coloring-book`,
                                    { method: "POST", headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" } }
                                  );
                                  const data = await res.json();
                                  if (res.ok && data.success) {
                                    if (data.coloring_pdf_url) {
                                      // Already exists, open it
                                      window.open(data.coloring_pdf_url, "_blank");
                                      setDetailData((prev) => prev ? { ...prev, coloring_pdf_url: data.coloring_pdf_url } : prev);
                                      toast({ title: "Boyama Kitabı Hazır!", description: "PDF yeni sekmede açılıyor." });
                                    } else {
                                      toast({ title: "Başlatıldı ✅", description: data.message || "Arka planda üretiliyor, birkaç dakika bekleyin." });
                                    }
                                  } else {
                                    toast({ title: "Hata", description: data.detail || "İşlem başarısız", variant: "destructive" });
                                  }
                                } catch {
                                  toast({ title: "Hata", description: "Sunucuya bağlanılamadı", variant: "destructive" });
                                }
                              }
                            }}
                          >
                            🖍️ Boyama PDF'i {detailData.coloring_pdf_url ? "İndir" : "Üret"}
                          </Button>
                        )}
                      </>
                    )}
                  </div>

                  {/* Generation manifest (debug) */}
                  {detailData.generation_manifest_json &&
                    Object.keys(detailData.generation_manifest_json).length > 0 && (
                      <details className="overflow-hidden rounded-lg border bg-gray-50" open>
                        <summary className="cursor-pointer select-none bg-gray-100 px-3 py-2 text-sm font-medium hover:bg-gray-200">
                          🔧 Generation manifest (debug)
                        </summary>
                        <details className="border-b bg-gray-50 px-3 py-2">
                          <summary className="cursor-pointer text-[10px] text-gray-500 hover:text-gray-700">
                            Alan açıklamaları
                          </summary>
                          <ul className="mt-2 list-inside list-disc space-y-1 text-[10px] text-gray-600">
                            <li>
                              <strong>provider</strong> — API sağlayıcı (fal = Fal.ai)
                            </li>
                            <li>
                              <strong>model</strong> — Kullanılan model (örn. fal-ai/flux-pulid)
                            </li>
                            <li>
                              <strong>steps</strong> — Çıkarım adım sayısı (28 = kalite / hız
                              dengesi)
                            </li>
                            <li>
                              <strong>guidance</strong> — Prompt bağlılığı (3.5 = orta-yüksek)
                            </li>
                            <li>
                              <strong>width × height</strong> — Görsel boyutu (Kapak: 768×1024, iç
                              sayfalar: 1024×768)
                            </li>
                            <li>
                              <strong>is_cover</strong> — Kapak sayfası mı (true/false)
                            </li>
                            <li>
                              <strong>prompt_hash</strong> — final_prompt’un SHA256 kısa hash’i
                              (değişiklik takibi)
                            </li>
                            <li>
                              <strong>negative_hash</strong> — negative_prompt hash’i
                            </li>
                            <li>
                              <strong>reference_image_used</strong> — PuLID yüz referansı kullanıldı
                              mı (true = çocuk yüzü eklendi)
                            </li>
                          </ul>
                        </details>
                        <div className="space-y-3 p-3">
                          {Object.keys(detailData.generation_manifest_json)
                            .sort((a, b) => Number(a) - Number(b))
                            .map((pageKey) => {
                              const m = detailData.generation_manifest_json![pageKey] as Record<
                                string,
                                unknown
                              >;
                              return (
                                <div
                                  key={pageKey}
                                  className="rounded border bg-white p-2 font-mono text-xs"
                                >
                                  <div className="mb-1 font-semibold text-gray-700">
                                    Sayfa {Number(pageKey) + 1} {m?.is_cover ? "(Kapak)" : ""}
                                  </div>
                                  <dl className="mb-2 grid grid-cols-2 gap-x-4 gap-y-0.5">
                                    <dt className="text-gray-500">provider</dt>
                                    <dd>{String(m?.provider ?? "-")}</dd>
                                    <dt className="text-gray-500">model</dt>
                                    <dd className="truncate">{String(m?.model ?? "-")}</dd>
                                    <dt className="text-gray-500">steps</dt>
                                    <dd>{String(m?.num_inference_steps ?? "-")}</dd>
                                    <dt className="text-gray-500">guidance</dt>
                                    <dd>{String(m?.guidance_scale ?? "-")}</dd>
                                    <dt className="text-gray-500">width × height</dt>
                                    <dd>
                                      {String(m?.width ?? "-")} × {String(m?.height ?? "-")}
                                    </dd>
                                    <dt className="text-gray-500">is_cover</dt>
                                    <dd>{String(m?.is_cover ?? "-")}</dd>
                                    <dt className="text-gray-500">prompt_hash</dt>
                                    <dd className="truncate">{String(m?.prompt_hash ?? "-")}</dd>
                                    <dt className="text-gray-500">negative_hash</dt>
                                    <dd className="truncate">{String(m?.negative_hash ?? "-")}</dd>
                                    <dt className="text-gray-500">reference_image_used</dt>
                                    <dd
                                      className={
                                        m?.reference_image_used === false
                                          ? "font-medium text-amber-600"
                                          : ""
                                      }
                                    >
                                      {String(m?.reference_image_used ?? "-")}
                                    </dd>
                                  </dl>
                                </div>
                              );
                            })}
                        </div>
                      </details>
                    )}

                  {/* PROMPTLAR - Açılır kapanır (manifest gibi) */}
                  {detailData.prompts_by_page &&
                    Object.keys(detailData.prompts_by_page).length > 0 && (
                      <details className="group/details overflow-hidden rounded-lg border border-green-200 bg-green-50">
                        <summary className="flex cursor-pointer select-none list-none items-center gap-2 bg-green-100 px-3 py-2 text-sm font-medium text-green-800 hover:bg-green-200 [&::-webkit-details-marker]:hidden">
                          <span className="transition-transform group-open/details:rotate-90">
                            ▶
                          </span>
                          📝 Prompts (final_prompt + negative_prompt)
                          {detailData.pipeline_version && (
                            <span className={`ml-2 rounded-full px-2 py-0.5 text-[10px] font-bold uppercase ${detailData.pipeline_version === "v3"
                              ? "bg-emerald-200 text-emerald-800"
                              : "bg-orange-200 text-orange-800"
                              }`}>
                              Pipeline {detailData.pipeline_version}
                            </span>
                          )}
                        </summary>
                        <div className="space-y-4 p-3">
                          {Object.keys(detailData.prompts_by_page)
                            .sort((a, b) => Number(a) - Number(b))
                            .map((pageKey) => {
                              const pb = detailData.prompts_by_page![pageKey];
                              const finalP = pb?.final_prompt ?? "";
                              const negP = pb?.negative_prompt ?? "";
                              const pagePipeline = pb?.pipeline_version ?? "";
                              const composerVer = pb?.composer_version ?? "";
                              const pageType = pb?.page_type ?? "inner";
                              const pageIdx = pb?.page_index ?? Number(pageKey);
                              const storyNum = pb?.story_page_number;
                              const copyBoth = () => {
                                const text = `=== Pipeline: ${composerVer || pagePipeline || "unknown"} | Type: ${pageType} | Index: ${pageIdx} ===\n=== final_prompt ===\n${finalP}\n\n=== negative_prompt ===\n${negP}`;
                                void navigator.clipboard.writeText(text).then(() => {
                                  toast({
                                    title: "Kopyalandı",
                                    description: "Her iki prompt panoya kopyalandı",
                                  });
                                });
                              };
                              return (
                                <div
                                  key={pageKey}
                                  className="relative rounded border border-green-100 bg-white p-3"
                                >
                                  <div className="mb-2 flex items-center justify-between">
                                    <div className="flex items-center gap-2 font-semibold text-gray-800">
                                      {pageType === "cover"
                                        ? "Kapak"
                                        : pageType === "front_matter"
                                          ? `İthaf (Sayfa ${storyNum ?? pageIdx})`
                                          : `Sayfa ${storyNum ?? pageIdx}`}
                                      {(composerVer || pagePipeline) && (
                                        <span className={`rounded px-1.5 py-0.5 text-[9px] font-bold uppercase ${(composerVer || pagePipeline) === "v3"
                                          ? "bg-emerald-100 text-emerald-700"
                                          : "bg-orange-100 text-orange-700"
                                          }`}>
                                          {composerVer || pagePipeline}
                                        </span>
                                      )}
                                      <span className="rounded bg-gray-100 px-1 py-0.5 text-[8px] text-gray-500">
                                        idx:{pageIdx} | type:{pageType}
                                      </span>
                                    </div>
                                    <Button
                                      type="button"
                                      variant="outline"
                                      size="sm"
                                      className="h-7 text-xs"
                                      onClick={copyBoth}
                                    >
                                      📋 İkisini kopyala
                                    </Button>
                                  </div>
                                  {finalP ? (
                                    <div className="mb-2">
                                      <p className="mb-1 text-xs font-medium text-gray-600">
                                        final_prompt
                                      </p>
                                      <pre className="max-h-48 overflow-y-auto whitespace-pre-wrap break-words rounded border bg-gray-50 p-2 text-xs">
                                        {finalP}
                                      </pre>
                                    </div>
                                  ) : null}
                                  {negP ? (
                                    <div>
                                      <p className="mb-1 text-xs font-medium text-gray-600">
                                        negative_prompt
                                      </p>
                                      <pre className="max-h-32 overflow-y-auto whitespace-pre-wrap break-words rounded border bg-gray-50 p-2 text-xs">
                                        {negP}
                                      </pre>
                                    </div>
                                  ) : null}
                                </div>
                              );
                            })}
                        </div>
                      </details>
                    )}

                  {/* Learning Outcomes + Audio in same row */}
                  <div className="flex gap-2">
                    {detailData.learning_outcomes && detailData.learning_outcomes.length > 0 && (
                      <div className="flex-1 rounded-lg bg-yellow-50 p-2">
                        <p className="mb-1 text-[10px] text-gray-500">Kazanımlar</p>
                        <div className="flex flex-wrap gap-1">
                          {detailData.learning_outcomes.map((outcome: string, idx: number) => (
                            <span
                              key={idx}
                              className="rounded bg-yellow-100 px-1.5 py-0.5 text-[10px]"
                            >
                              {outcome}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {detailData.has_audio_book && (
                      <div className="w-48 flex-shrink-0 rounded-lg bg-indigo-50 p-2">
                        <p className="text-[10px] text-gray-500">🎧 Sesli Kitap</p>
                        <p className="text-xs font-medium">
                          {detailData.audio_type === "cloned" ? "Klonlanmış" : "Sistem"}
                        </p>
                      </div>
                    )}
                  </div>

                  {/* PRINT READY VIEW - All Pages */}
                  <div className="border-t pt-4">
                    <div className="mb-3 flex items-center justify-between">
                      <h4 className="text-lg font-bold">📖 Baskıya Hazır Görünüm</h4>
                      <div className="flex items-center gap-2">
                        <span className="text-sm text-gray-500">
                          {detailData.story_pages?.length || 0} sayfa
                        </span>
                        {detailData.page_images && Object.keys(detailData.page_images).length > 0 && (
                          <Button
                            size="sm"
                            variant="outline"
                            disabled={zipDownloading}
                            onClick={downloadAllImages}
                            className="gap-1 text-xs"
                          >
                            {zipDownloading ? (
                              <>
                                <span className="h-3 w-3 animate-spin rounded-full border-2 border-gray-300 border-t-purple-500" />
                                İndiriliyor...
                              </>
                            ) : (
                              <>📦 Tüm Resimleri İndir (ZIP)</>
                            )}
                          </Button>
                        )}
                      </div>
                    </div>

                    {/* Print Info Badge */}
                    <div className="mb-4 rounded-lg border border-blue-200 bg-blue-50 p-3">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="text-blue-600">🖨️</span>
                          <span className="font-medium text-blue-800">Baskı Formatı:</span>
                          <span className="text-blue-700">
                            {detailData.product_name?.includes("Yatay")
                              ? "Yatay A4 (297×210mm)"
                              : detailData.product_name?.includes("Kare")
                                ? "Kare (210×210mm)"
                                : detailData.product_name?.includes("Cep")
                                  ? "Cep Boy (148×210mm)"
                                  : "A4 (210×297mm)"}
                          </span>
                        </div>
                        <span className="text-xs text-blue-500">Bleed: 3mm</span>
                      </div>
                    </div>

                    {/* Eksik Sayfaları Oluştur + Yeniden Compose Et */}
                    <div className="flex justify-end gap-2 mb-2">
                      {/* Eksik sayfa görseli varsa buton göster */}
                      {(() => {
                        const numericKeys = detailData.page_images
                          ? Object.keys(detailData.page_images).filter((k) => /^\d+$/.test(k))
                          : [];
                        const totalPages = detailData.story_pages?.length || 0;
                        const missingCount = totalPages - numericKeys.length;
                        if (missingCount <= 0) return null;
                        return (
                          <button
                            type="button"
                            onClick={async () => {
                              try {
                                const res = await fetch(
                                  `${API_BASE_URL}/admin/orders/previews/${detailData.id}/generate-remaining`,
                                  { method: "POST", headers: getAuthHeaders() }
                                );
                                if (res.ok) {
                                  const data = await res.json();
                                  toast({
                                    title: "Başarılı",
                                    description: data.message || `${missingCount} eksik sayfa oluşturuluyor...`,
                                  });
                                } else {
                                  toast({ title: "Hata", description: "İşlem başarısız", variant: "destructive" });
                                }
                              } catch {
                                toast({ title: "Hata", description: "Bağlantı hatası", variant: "destructive" });
                              }
                            }}
                            className="rounded-md bg-red-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-red-700 transition-colors"
                          >
                            ⚠️ {missingCount} Eksik Sayfa Oluştur
                          </button>
                        );
                      })()}
                      <button
                        type="button"
                        onClick={async () => {
                          try {
                            const res = await fetch(
                              `${API_BASE_URL}/admin/orders/previews/${detailData.id}/composed-images?force_recompose=true`,
                              { headers: getAuthHeaders() }
                            );
                            if (res.ok) {
                              toast({ title: "Başarılı", description: "Kapak güncel template ile yeniden compose edildi. Sayfayı yenileyin." });
                              // Detayı yeniden çek
                              const r2 = await fetch(`${API_BASE_URL}/admin/orders/previews/${detailData.id}`, { headers: getAuthHeaders() });
                              if (r2.ok) {
                                const d = await r2.json();
                                setDetailData(d);
                              }
                            } else {
                              toast({ title: "Hata", description: "Recompose başarısız", variant: "destructive" });
                            }
                          } catch {
                            toast({ title: "Hata", description: "Bağlantı hatası", variant: "destructive" });
                          }
                        }}
                        className="rounded-md bg-amber-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-amber-700 transition-colors"
                      >
                        🔄 Güncel Template ile Yeniden Compose Et
                      </button>
                    </div>

                    {detailData.story_pages && detailData.story_pages.length > 0 ? (
                      <div className="grid grid-cols-2 gap-4 xl:grid-cols-3">
                        {/* Karşılama Sayfası (dedication) — page_images["dedication"] varsa göster */}
                        {/* Karşılama 1 (dedication) */}
                        {detailData.page_images?.["dedication"] && (
                          <div className="overflow-hidden rounded-lg border-2 border-amber-400 bg-amber-50 shadow-sm">
                            <div className="flex items-center justify-between bg-amber-100 px-2 py-1.5">
                              <span className="text-xs font-medium text-amber-800">
                                💝 Karşılama 1 (İthaf)
                              </span>
                              <div className="flex items-center gap-2">
                                <button
                                  type="button"
                                  onClick={() =>
                                    downloadSingleImage(
                                      detailData.page_images!["dedication"],
                                      `${detailData.child_name || "kitap"}_karsilama_1.jpg`
                                    )
                                  }
                                  className="rounded bg-amber-600 px-1.5 py-0.5 text-[10px] font-medium text-white transition-colors hover:bg-amber-700"
                                  title="Bu resmi indir"
                                >
                                  ⬇ İndir
                                </button>
                                <a
                                  href={detailData.page_images["dedication"]}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="text-[10px] text-blue-600 hover:underline"
                                >
                                  Tam boyut
                                </a>
                              </div>
                            </div>
                            <div className="p-2">
                              <LazyImage
                                src={detailData.page_images["dedication"]}
                                alt="Karşılama 1"
                                className="w-full rounded border aspect-[297/210]"
                              />
                              {detailData.dedication_note && (
                                <div className="mt-2 rounded bg-amber-50 p-2">
                                  <p className="text-[11px] italic text-amber-900">{detailData.dedication_note}</p>
                                </div>
                              )}
                            </div>
                          </div>
                        )}

                        {/* Karşılama 2 (senaryo intro) */}
                        {detailData.page_images?.["intro"] && (
                          <div className="overflow-hidden rounded-lg border-2 border-teal-400 bg-teal-50 shadow-sm">
                            <div className="flex items-center justify-between bg-teal-100 px-2 py-1.5">
                              <span className="text-xs font-medium text-teal-800">
                                📖 Karşılama 2 (Senaryo Tanıtım)
                              </span>
                              <div className="flex items-center gap-2">
                                <button
                                  type="button"
                                  onClick={() =>
                                    downloadSingleImage(
                                      detailData.page_images!["intro"],
                                      `${detailData.child_name || "kitap"}_karsilama_2.jpg`
                                    )
                                  }
                                  className="rounded bg-teal-600 px-1.5 py-0.5 text-[10px] font-medium text-white transition-colors hover:bg-teal-700"
                                  title="Bu resmi indir"
                                >
                                  ⬇ İndir
                                </button>
                                <a
                                  href={detailData.page_images["intro"]}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="text-[10px] text-blue-600 hover:underline"
                                >
                                  Tam boyut
                                </a>
                              </div>
                            </div>
                            <div className="p-2">
                              <LazyImage
                                src={detailData.page_images["intro"]}
                                alt="Karşılama 2 - Senaryo Tanıtım"
                                className="w-full rounded border aspect-[297/210]"
                              />
                              <p className="mt-1 text-[10px] text-teal-700">
                                {detailData.scenario_name || "Senaryo"} hakkında tanıtım sayfası
                              </p>
                            </div>
                          </div>
                        )}

                        {detailData.story_pages.map((page: StoryPageContent, idx: number) => {
                          const rawUrl =
                            detailData.page_images?.[idx.toString()] ||
                            detailData.page_images?.[`page_${idx}`];
                          const hasImage = rawUrl != null;
                          const imageUrl = hasImage
                            ? pageImageProxyUrl(detailData.id, idx.toString(), 500)
                            : null;
                          const fullImageUrl = hasImage
                            ? pageImageProxyUrl(detailData.id, idx.toString())
                            : null;
                          // Determine aspect ratio based on product (landscape vs portrait)
                          const isLandscape = detailData.product_name?.includes("Yatay");
                          const aspectRatio = isLandscape
                            ? "aspect-[297/210]"
                            : detailData.product_name?.includes("Kare")
                              ? "aspect-square"
                              : "aspect-[210/297]";
                          return (
                            <div
                              key={`${detailData.id}-${idx}`}
                              className="overflow-hidden rounded-lg border bg-white shadow-sm"
                            >
                              {/* Page Header */}
                              <div className="flex items-center justify-between bg-gray-100 px-2 py-1.5">
                                <span className="text-xs font-medium">
                                  {idx + 1} {idx === 0 && "(Kapak)"}
                                </span>
                                <div className="flex items-center gap-2">
                                  {fullImageUrl && (
                                    <button
                                      type="button"
                                      onClick={() =>
                                        downloadSingleImage(
                                          fullImageUrl,
                                          `${detailData.child_name || "kitap"}_sayfa_${idx + 1}.jpg`
                                        )
                                      }
                                      className="rounded bg-purple-600 px-1.5 py-0.5 text-[10px] font-medium text-white transition-colors hover:bg-purple-700"
                                      title="Bu resmi indir"
                                    >
                                      ⬇ İndir
                                    </button>
                                  )}
                                  {fullImageUrl && (
                                    <a
                                      href={fullImageUrl}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="text-[10px] text-blue-600 hover:underline"
                                    >
                                      Tam boyut
                                    </a>
                                  )}
                                </div>
                              </div>

                              {/* Page Content */}
                              <div className="p-2">
                                {imageUrl ? (
                                  <LazyImage
                                    src={imageUrl}
                                    alt={`Sayfa ${idx + 1}`}
                                    className={`w-full rounded border ${aspectRatio}`}
                                  />
                                ) : (
                                  <div
                                    className={`bg-gray-100 ${aspectRatio} flex items-center justify-center rounded`}
                                  >
                                    <span className="text-xs text-gray-400">Görsel yok</span>
                                  </div>
                                )}

                                {/* Page Text - Collapsed */}
                                {page.text && (
                                  <div className="mt-2 rounded bg-gray-50 p-2">
                                    <p className="line-clamp-3 text-[11px]">{page.text}</p>
                                  </div>
                                )}
                                {/* Visual prompt (görsel üretim promptu) */}
                                {page.visual_prompt && (
                                  <details className="mt-2">
                                    <summary className="cursor-pointer text-[10px] text-gray-500 hover:text-gray-700">
                                      📝 Prompt
                                    </summary>
                                    <pre className="mt-1 max-h-24 overflow-y-auto whitespace-pre-wrap break-words rounded border border-gray-100 bg-gray-50 p-1.5 text-[9px]">
                                      {page.visual_prompt}
                                    </pre>
                                  </details>
                                )}
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    ) : detailData.page_images && Object.keys(detailData.page_images).length > 0 ? (
                      /* Fallback: Just show images if no story_pages */
                      <div className="grid grid-cols-2 gap-3 xl:grid-cols-3">
                        {Object.entries(detailData.page_images)
                          .sort(([a], [b]) => {
                            const order = (k: string) => {
                              if (k === "dedication") return -2;
                              if (k === "intro") return -1;
                              return parseInt(k) || 0;
                            };
                            return order(a) - order(b);
                          })
                          .map(([pageNum]) => {
                            const isDedication = pageNum === "dedication";
                            const isIntro = pageNum === "intro";
                            const isSpecial = isDedication || isIntro;
                            const thumbSrc = isSpecial
                              ? detailData.page_images![pageNum]
                              : pageImageProxyUrl(detailData.id, pageNum, 500);
                            const fullSrc = isSpecial
                              ? detailData.page_images![pageNum]
                              : pageImageProxyUrl(detailData.id, pageNum);
                            const isLandscape = detailData.product_name?.includes("Yatay");
                            const aspectRatio = isLandscape
                              ? "aspect-[297/210]"
                              : detailData.product_name?.includes("Kare")
                                ? "aspect-square"
                                : "aspect-[210/297]";
                            const label = isDedication
                              ? "💝 Karşılama 1"
                              : isIntro
                                ? "📖 Karşılama 2"
                                : String(parseInt(pageNum) + 1);
                            const borderClass = isDedication
                              ? "border-2 border-amber-400"
                              : isIntro
                                ? "border-2 border-teal-400"
                                : "";
                            const headerClass = isDedication
                              ? "bg-amber-100"
                              : isIntro
                                ? "bg-teal-100"
                                : "bg-gray-100";
                            return (
                              <div
                                key={`${detailData.id}-${pageNum}`}
                                className={`overflow-hidden rounded border ${borderClass}`}
                              >
                                <div className={`flex justify-between px-2 py-1 text-xs font-medium ${headerClass}`}>
                                  <span>{label}</span>
                                  <div className="flex items-center gap-2">
                                    <button
                                      type="button"
                                      onClick={() => {
                                        const ext = isDedication
                                          ? "karsilama_1"
                                          : isIntro
                                            ? "karsilama_2"
                                            : `sayfa_${parseInt(pageNum) + 1}`;
                                        downloadSingleImage(
                                          fullSrc,
                                          `${detailData.child_name || "kitap"}_${ext}.jpg`
                                        );
                                      }}
                                      className="rounded bg-purple-600 px-1.5 py-0.5 text-[10px] font-medium text-white transition-colors hover:bg-purple-700"
                                      title="Bu resmi indir"
                                    >
                                      ⬇ İndir
                                    </button>
                                    <a
                                      href={fullSrc}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="text-[10px] text-blue-600 hover:underline"
                                    >
                                      Tam boyut
                                    </a>
                                  </div>
                                </div>
                                <LazyImage
                                  src={thumbSrc}
                                  alt={isDedication ? "Karşılama 1" : isIntro ? "Karşılama 2" : `Sayfa ${pageNum}`}
                                  className={`w-full ${aspectRatio}`}
                                />
                              </div>
                            );
                          })}
                      </div>
                    ) : (
                      <div className="py-8 text-center text-gray-400">Henüz sayfa görseli yok</div>
                    )}

                    {/* BACK COVER PREVIEW */}
                    {(detailData.back_cover_image_url || backCoverConfig) && (
                      <div className="mt-4 overflow-hidden rounded-lg border bg-white shadow-sm">
                        <div className="flex items-center justify-between bg-purple-100 px-3 py-2">
                          <span className="text-sm font-medium text-purple-800">📘 Arka Kapak (Görsel)</span>
                          <div className="flex items-center gap-2">
                            {detailData.back_cover_image_url && (
                              <>
                                <button
                                  type="button"
                                  onClick={() =>
                                    downloadSingleImage(
                                      detailData.back_cover_image_url!,
                                      `${detailData.child_name || "kitap"}_arka_kapak.jpg`
                                    )
                                  }
                                  className="rounded bg-purple-600 px-1.5 py-0.5 text-[10px] font-medium text-white transition-colors hover:bg-purple-700"
                                >
                                  ⬇ İndir
                                </button>
                                <a
                                  href={detailData.back_cover_image_url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="text-[10px] text-blue-600 hover:underline"
                                >
                                  Tam boyut
                                </a>
                              </>
                            )}
                            {!detailData.back_cover_image_url && (
                              <span className="text-xs text-purple-600">Henüz üretilmedi</span>
                            )}
                          </div>
                        </div>
                        {detailData.back_cover_image_url ? (
                          <div className="p-2">
                            <LazyImage
                              src={detailData.back_cover_image_url}
                              alt="Arka Kapak Görseli"
                              className="w-full rounded border aspect-[297/210]"
                            />
                          </div>
                        ) : backCoverConfig && (
                          <div
                            className="p-4"
                            style={{ backgroundColor: backCoverConfig.background_color }}
                          >
                            <div
                              className="rounded-lg p-4"
                              style={{
                                border: backCoverConfig.show_border
                                  ? `2px solid ${backCoverConfig.border_color}`
                                  : "none",
                              }}
                            >
                              <div className="mb-3 text-center">
                                <h3
                                  className="text-lg font-bold"
                                  style={{ color: backCoverConfig.primary_color }}
                                >
                                  {backCoverConfig.company_name}
                                </h3>
                                <p
                                  className="text-sm italic"
                                  style={{ color: backCoverConfig.text_color }}
                                >
                                  {backCoverConfig.tagline}
                                </p>
                              </div>
                              <hr
                                style={{ borderColor: backCoverConfig.primary_color }}
                                className="my-3"
                              />
                              <div className="mb-3">
                                <h4
                                  className="mb-2 text-center text-sm font-semibold"
                                  style={{ color: backCoverConfig.primary_color }}
                                >
                                  {backCoverConfig.tips_title}
                                </h4>
                                <div
                                  className="space-y-1 text-xs"
                                  style={{ color: backCoverConfig.text_color }}
                                >
                                  {backCoverConfig.tips_content.split("\n").map((line, i) => (
                                    <p key={i}>{line}</p>
                                  ))}
                                </div>
                              </div>
                              {backCoverConfig.qr_enabled && (
                                <div className="mb-3 flex justify-end">
                                  <div className="rounded bg-white p-2 text-center">
                                    <div className="flex h-12 w-12 items-center justify-center border bg-gray-200 text-xs">
                                      QR
                                    </div>
                                    <p
                                      className="mt-1 text-xs"
                                      style={{ color: backCoverConfig.primary_color }}
                                    >
                                      {backCoverConfig.qr_label}
                                    </p>
                                  </div>
                                </div>
                              )}
                              <div
                                className="text-center text-xs"
                                style={{ color: backCoverConfig.text_color }}
                              >
                                <p>{backCoverConfig.company_website}</p>
                                <p>{backCoverConfig.company_email}</p>
                                <p className="mt-2 text-gray-400">{backCoverConfig.copyright_text}</p>
                              </div>
                              <p
                                className="mt-3 text-center text-xs italic"
                                style={{ color: backCoverConfig.primary_color }}
                              >
                                Bu kitap {detailData.child_name} için özel olarak hazırlandı
                              </p>
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>

                  {/* Timestamps (Moved Below Actions) */}
                  <div className="space-y-1 border-t pt-3 mt-4 text-xs text-gray-500">
                    <p>Oluşturulma: {new Date(detailData.created_at).toLocaleString("tr-TR")}</p>
                    {detailData.confirmed_at && (
                      <p className="text-green-600">
                        Onaylanma: {new Date(detailData.confirmed_at).toLocaleString("tr-TR")}
                      </p>
                    )}
                  </div>
                </CardContent>
              </Card>
            ) : (
              <Card>
                <CardContent className="py-12 text-center text-gray-500">
                  <p className="mb-2 text-lg">👈 Bir sipariş seçin</p>
                  <p className="text-sm">
                    Detayları ve baskıya hazır görünümü görmek için soldaki listeden bir sipariş
                    seçin
                  </p>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
