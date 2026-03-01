"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { useToast } from "@/hooks/use-toast";
import { ArrowLeft, Plus, Edit, Trash2, Palette, Sliders } from "lucide-react";
import { Slider } from "@/components/ui/slider";
import Link from "next/link";
import { API_BASE_URL } from "@/lib/api";
import { getAdminHeaders as getAuthHeaders } from "@/lib/adminFetch";

interface VisualStyle {
  id: string;
  name: string;
  display_name: string | null;
  thumbnail_url: string;
  prompt_modifier: string;
  style_negative_en: string | null;
  leading_prefix_override: string | null;
  style_block_override: string | null;
  cover_aspect_ratio: string;
  page_aspect_ratio: string;
  // PuLID params
  id_weight: number;
  true_cfg: number | null;
  start_step: number | null;
  // FLUX generation params
  num_inference_steps: number | null;
  guidance_scale: number | null;
  is_active: boolean;
}

const ASPECT_RATIO_OPTIONS = [
  { value: "1:1", label: "1:1 (Kare)" },
  { value: "2:3", label: "2:3 (Dikey)" },
  { value: "3:2", label: "3:2 (Yatay)" },
  { value: "4:3", label: "4:3" },
  { value: "16:9", label: "16:9 (Geniş)" },
];

export default function AdminVisualStylesPage() {
  const [styles, setStyles] = useState<VisualStyle[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingStyle, setEditingStyle] = useState<VisualStyle | null>(null);
  const [saving, setSaving] = useState(false);
  const [testStyle, setTestStyle] = useState<VisualStyle | null>(null);
  const [testImageFile, setTestImageFile] = useState<File | null>(null);
  const [testLoading, setTestLoading] = useState(false);
  const [testResult, setTestResult] = useState<{
    image_url: string;
    final_prompt?: string;
    negative_prompt?: string;
    fal_params?: Record<string, unknown>;
    gemini_params?: Record<string, unknown>;
  } | null>(null);
  const [testError, setTestError] = useState<string | null>(null);
  const [testProviderOverride, setTestProviderOverride] = useState<string>("");

  const [formData, setFormData] = useState({
    name: "",
    display_name: "",
    thumbnail_url: "/img/default-style.jpg",
    thumbnail_base64: "",
    prompt_modifier: "",
    style_negative_en: "",
    leading_prefix_override: "",
    style_block_override: "",
    cover_aspect_ratio: "2:3",
    page_aspect_ratio: "1:1",
    id_weight: 0.9,
    true_cfg: null as number | null,
    start_step: null as number | null,
    num_inference_steps: null as number | null,
    guidance_scale: null as number | null,
    is_active: true,
  });
  const [imagePreview, setImagePreview] = useState<string | null>(null);

  const router = useRouter();
  const { toast } = useToast();

  useEffect(() => {
    checkAuth();
    fetchStyles();
  }, []);

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


  const fetchStyles = async () => {
    try {
      const token = localStorage.getItem("token");
      if (!token) {
        router.push("/auth/login");
        return;
      }
      const response = await fetch(`${API_BASE_URL}/admin/visual-styles?include_inactive=true`, {
        headers: getAuthHeaders(),
      });
      if (response.status === 401 || response.status === 403) {
        // Token expired or insufficient permissions — try refresh
        const refreshToken = localStorage.getItem("refreshToken");
        if (refreshToken) {
          try {
            const refreshResp = await fetch(`${API_BASE_URL}/auth/refresh`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ refresh_token: refreshToken }),
            });
            if (refreshResp.ok) {
              const refreshData = await refreshResp.json();
              localStorage.setItem("token", refreshData.access_token);
              if (refreshData.refresh_token) {
                localStorage.setItem("refreshToken", refreshData.refresh_token);
              }
              // Retry with new token
              const retryResp = await fetch(
                `${API_BASE_URL}/admin/visual-styles?include_inactive=true`,
                {
                  headers: getAuthHeaders(),
                }
              );
              if (retryResp.ok) {
                const data = await retryResp.json();
                setStyles(data);
                setLoading(false);
                return;
              }
            }
          } catch {
            // Refresh failed, redirect to login
          }
        }
        toast({
          title: "Oturum süresi doldu",
          description: "Lütfen tekrar giriş yapın",
          variant: "destructive",
        });
        router.push("/auth/login");
        return;
      }
      if (response.ok) {
        const data = await response.json();
        setStyles(data);
      } else {
        toast({
          title: "Hata",
          description: `Sunucu hatası: ${response.status}`,
          variant: "destructive",
        });
      }
    } catch (error) {
      toast({ title: "Hata", description: "Çizim tarzları yüklenemedi", variant: "destructive" });
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setFormData({
      name: "",
      display_name: "",
      thumbnail_url: "/img/default-style.jpg",
      thumbnail_base64: "",
      prompt_modifier: "",
      style_negative_en: "",
      leading_prefix_override: "",
      style_block_override: "",
      cover_aspect_ratio: "2:3",
      page_aspect_ratio: "1:1",
      id_weight: 0.9,
      true_cfg: null,
      start_step: null,
      num_inference_steps: null,
      guidance_scale: null,
      is_active: true,
    });
    setImagePreview(null);
    setEditingStyle(null);
  };

  const handleEdit = (style: VisualStyle) => {
    setFormData({
      name: style.name,
      display_name: style.display_name || "",
      thumbnail_url: style.thumbnail_url,
      thumbnail_base64: "",
      prompt_modifier: style.prompt_modifier,
      style_negative_en: style.style_negative_en || "",
      leading_prefix_override: style.leading_prefix_override || "",
      style_block_override: style.style_block_override || "",
      cover_aspect_ratio: style.cover_aspect_ratio,
      page_aspect_ratio: style.page_aspect_ratio,
      id_weight: style.id_weight ?? 0.9,
      true_cfg: style.true_cfg ?? null,
      start_step: style.start_step ?? null,
      num_inference_steps: style.num_inference_steps ?? null,
      guidance_scale: style.guidance_scale ?? null,
      is_active: style.is_active,
    });
    setImagePreview(style.thumbnail_url);
    setEditingStyle(style);
    setShowForm(true);
  };

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        const base64 = reader.result as string;
        setFormData({ ...formData, thumbnail_base64: base64 });
        setImagePreview(base64);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const name = formData.name.trim();
    const prompt_modifier = formData.prompt_modifier.trim();
    if (!name) {
      toast({ title: "Hata", description: "Stil adı gerekli", variant: "destructive" });
      return;
    }
    if (!prompt_modifier) {
      toast({
        title: "Hata",
        description: "Prompt metni (çizim tarzı açıklaması) gerekli",
        variant: "destructive",
      });
      return;
    }
    setSaving(true);

    try {
      const payload: Record<string, unknown> = {
        name,
        display_name: formData.display_name?.trim() || null,
        prompt_modifier,
        style_negative_en: formData.style_negative_en || null,
        leading_prefix_override: formData.leading_prefix_override?.trim() || null,
        style_block_override: formData.style_block_override?.trim() || null,
        cover_aspect_ratio: formData.cover_aspect_ratio,
        page_aspect_ratio: formData.page_aspect_ratio,
        id_weight: formData.id_weight,
        true_cfg: formData.true_cfg,
        start_step: formData.start_step,
        num_inference_steps: formData.num_inference_steps,
        guidance_scale: formData.guidance_scale,
        is_active: formData.is_active,
      };
      if (formData.thumbnail_base64) {
        payload.thumbnail_base64 = formData.thumbnail_base64;
      } else if (!editingStyle) {
        payload.thumbnail_url = formData.thumbnail_url;
      }

      const url = editingStyle
        ? `${API_BASE_URL}/admin/visual-styles/${editingStyle.id}`
        : `${API_BASE_URL}/admin/visual-styles`;

      const response = await fetch(url, {
        method: editingStyle ? "PATCH" : "POST",
        headers: getAuthHeaders(),
        body: JSON.stringify(payload),
      });

      const data = await response.json().catch(() => ({}));
      const detail =
        typeof data?.detail === "string"
          ? data.detail
          : Array.isArray(data?.detail)
            ? JSON.stringify(data.detail)
            : "Hata oluştu";

      if (response.ok) {
        toast({
          title: "Başarılı",
          description: editingStyle ? "Çizim tarzı güncellendi" : "Çizim tarzı oluşturuldu",
        });
        setShowForm(false);
        resetForm();
        fetchStyles();
      } else {
        throw new Error(detail);
      }
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : "Kaydetme başarısız";
      toast({ title: "Hata", description: message, variant: "destructive" });
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (styleId: string) => {
    if (!confirm("Bu çizim tarzını silmek istediğinize emin misiniz?")) return;

    try {
      const response = await fetch(`${API_BASE_URL}/admin/visual-styles/${styleId}`, {
        method: "DELETE",
        headers: getAuthHeaders(),
      });

      if (response.ok) {
        toast({ title: "Başarılı", description: "Çizim tarzı silindi" });
        fetchStyles();
      }
    } catch (error) {
      toast({ title: "Hata", description: "Silme başarısız", variant: "destructive" });
    }
  };

  const openTestModal = (style: VisualStyle) => {
    // Warn if user has unsaved edits open for this style
    if (editingStyle?.id === style.id && showForm) {
      toast({
        title: "Kaydedilmemiş değişiklikler",
        description: "Test, kaydedilmiş DB değerlerini kullanır. Önce 'Güncelle' ile kaydedin.",
        variant: "destructive",
      });
    }
    setTestStyle(style);
    setTestImageFile(null);
    setTestResult(null);
    setTestError(null);
    setTestProviderOverride("");
  };

  const runStyleTest = async () => {
    if (!testStyle) return;
    setTestLoading(true);
    setTestResult(null);
    setTestError(null);
    try {
      const formData = new FormData();
      if (testImageFile) formData.append("image", testImageFile);
      if (testProviderOverride && testProviderOverride !== "default") {
        formData.append("image_provider_override", testProviderOverride);
      }
      const token = localStorage.getItem("token");
      const response = await fetch(`${API_BASE_URL}/admin/visual-styles/${testStyle.id}/test`, {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body: formData,
      });
      const data = await response.json().catch(() => ({}));
      if (response.ok) {
        setTestResult({
          image_url: data.image_url ?? "",
          final_prompt: data.final_prompt,
          negative_prompt: data.negative_prompt,
          fal_params: data.fal_params,
          gemini_params: data.gemini_params,
        });
        toast({ title: "Başarılı", description: data.message ?? "Test görseli oluşturuldu" });
      } else {
        const msg = typeof data.detail === "string" ? data.detail : "Test başarısız";
        setTestError(msg);
        toast({ title: "Hata", description: msg, variant: "destructive" });
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Test isteği başarısız";
      setTestError(msg);
      toast({ title: "Hata", description: msg, variant: "destructive" });
    } finally {
      setTestLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-b-2 border-purple-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="mx-auto max-w-6xl">
        {/* Header */}
        <div className="mb-6 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/admin">
              <Button variant="ghost" size="icon">
                <ArrowLeft className="h-5 w-5" />
              </Button>
            </Link>
            <div>
              <h1 className="text-2xl font-bold">Çizim Tarzları Yönetimi</h1>
              <p className="text-gray-600">
                Görsel stil seçeneklerini yönetin. Her kartta mor <strong>Stili test et</strong> ile
                tek görsel üretebilirsiniz.
              </p>
            </div>
          </div>
          <Button
            onClick={() => {
              resetForm();
              setShowForm(true);
            }}
          >
            <Plus className="mr-2 h-4 w-4" />
            Yeni Tarz
          </Button>
        </div>

        {/* Styles Grid */}
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
          {styles.length === 0 ? (
            <Card className="col-span-full">
              <CardContent className="p-8 text-center text-gray-500">
                Henüz çizim tarzı eklenmemiş
              </CardContent>
            </Card>
          ) : (
            styles.map((style) => (
              <Card key={style.id} className={!style.is_active ? "opacity-50" : ""}>
                <CardContent className="overflow-visible p-4">
                  {/* Stil testi — kartın en üstünde, mutlaka görünsün */}
                  <button
                    type="button"
                    onClick={() => openTestModal(style)}
                    data-testid="style-test-btn"
                    className="mb-3 flex w-full items-center justify-center gap-2 rounded-lg border-2 border-violet-600 bg-violet-600 px-4 py-3 text-base font-semibold text-white transition-colors hover:border-violet-700 hover:bg-violet-700"
                  >
                    <span aria-hidden>▶</span>
                    Stili test et (1 görsel)
                  </button>

                  <div className="mb-3 aspect-square overflow-hidden rounded-lg bg-gray-100">
                    {style.thumbnail_url ? (
                      <img
                        src={style.thumbnail_url}
                        alt={style.name}
                        className="h-full w-full object-cover"
                        onError={(e) => {
                          (e.target as HTMLImageElement).src = "/placeholder.svg";
                        }}
                      />
                    ) : (
                      <div className="flex h-full w-full items-center justify-center">
                        <Palette className="h-12 w-12 text-gray-300" />
                      </div>
                    )}
                  </div>

                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <h3 className="font-semibold">{style.name}</h3>
                      {!style.is_active && (
                        <span className="rounded bg-gray-200 px-2 py-0.5 text-xs text-gray-600">
                          Pasif
                        </span>
                      )}
                    </div>

                    <p className="line-clamp-2 text-xs text-gray-500">{style.prompt_modifier}</p>

                    <div className="flex items-center gap-2 text-xs text-gray-400">
                      <span>Kapak: {style.cover_aspect_ratio}</span>
                      <span>|</span>
                      <span>Sayfa: {style.page_aspect_ratio}</span>
                    </div>

                    <div className="flex items-center gap-2 text-xs">
                      <Sliders className="h-3 w-3 text-purple-500" />
                      <span className="text-gray-500">id_weight:</span>
                      <span
                        className={`font-medium ${
                          style.id_weight <= 0.25
                            ? "text-blue-600"
                            : style.id_weight <= 0.4
                              ? "text-green-600"
                              : "text-orange-600"
                        }`}
                      >
                        {style.id_weight?.toFixed(2) ?? "0.35"}
                      </span>
                      <span className="text-gray-400">
                        (
                        {style.id_weight <= 0.25
                          ? "Stilize"
                          : style.id_weight <= 0.4
                            ? "Dengeli"
                            : "Gerçekçi"}
                        )
                      </span>
                    </div>

                    <div className="flex items-center gap-2 pt-2">
                      <Button
                        variant="outline"
                        size="sm"
                        className="flex-1"
                        onClick={() => handleEdit(style)}
                      >
                        <Edit className="mr-1 h-4 w-4" />
                        Düzenle
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleDelete(style.id)}
                        className="text-red-600 hover:text-red-700"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </div>

        {/* Test Modal */}
        {testStyle && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
            <Card className="max-h-[90vh] w-full max-w-2xl overflow-y-auto">
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle>Stil testi: {testStyle.name}</CardTitle>
                  <CardDescription>
                    Bu stille 1 test görseli oluşturulur (5 sayfa yerine). İsteğe bağlı: çocuk
                    fotoğrafı yükle (yüz referansı).
                  </CardDescription>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    setTestStyle(null);
                    setTestResult(null);
                    setTestError(null);
                  }}
                >
                  Kapat
                </Button>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label className="text-sm">Çocuk fotoğrafı (opsiyonel)</Label>
                  <Input
                    type="file"
                    accept="image/*"
                    className="mt-1"
                    onChange={(e) => setTestImageFile(e.target.files?.[0] ?? null)}
                    disabled={testLoading}
                  />
                </div>
                <div>
                  <Label className="text-sm">Bu test için sağlayıcı</Label>
                  <select
                    value={testProviderOverride}
                    onChange={(e) => setTestProviderOverride(e.target.value)}
                    className="mt-1 h-10 w-full rounded-md border bg-background px-3"
                    disabled={testLoading}
                  >
                    <option value="">Varsayılan (Ayarlar)</option>
                    <option value="fal">Fal.ai</option>
                    <option value="gemini_flash">Gemini</option>
                  </select>
                  <p className="mt-0.5 text-xs text-gray-500">
                    Ayarlardaki varsayılan veya bu test için Fal/Gemini seçin.
                  </p>
                </div>
                <Button onClick={runStyleTest} disabled={testLoading}>
                  {testLoading ? "Oluşturuluyor..." : "1 test görseli oluştur"}
                </Button>
                {testError && <p className="text-sm text-red-600">{testError}</p>}
                {testResult?.image_url && (
                  <div className="space-y-2">
                    <Label className="text-sm">Sonuç</Label>
                    <img
                      src={testResult.image_url}
                      alt="Test görseli"
                      className="max-h-[400px] w-full rounded-lg border bg-gray-50 object-contain"
                    />
                    {testResult.final_prompt && (
                      <details className="text-xs" open>
                        <summary className="cursor-pointer font-medium text-gray-600">
                          Fal.ai&apos;ye giden tam prompt (positive)
                        </summary>
                        <p className="mt-1 text-[11px] text-gray-500">
                          <strong>512 = token</strong> (karakter değil; ~4 char/token → ~2048
                          karakter). Uygulama toplam promptu 2048 karakterle sınırlar. Bu metin
                          birebir Fal&apos;a gönderilir.
                        </p>
                        <pre className="mt-1 max-h-40 overflow-auto whitespace-pre-wrap break-words rounded bg-gray-100 p-2">
                          {testResult.final_prompt}
                        </pre>
                      </details>
                    )}
                    {testResult.negative_prompt && (
                      <details className="text-xs">
                        <summary className="cursor-pointer font-medium text-gray-600">
                          Fal.ai&apos;ye giden negative_prompt
                        </summary>
                        <pre className="mt-1 max-h-24 overflow-auto whitespace-pre-wrap break-words rounded bg-gray-100 p-2">
                          {testResult.negative_prompt}
                        </pre>
                      </details>
                    )}
                    {testResult.fal_params && Object.keys(testResult.fal_params).length > 0 && (
                      <details className="text-xs" open>
                        <summary className="cursor-pointer font-medium text-gray-600">
                          Fal.ai parametreler
                        </summary>
                        <p className="mt-1 text-[11px] font-medium text-amber-700">
                          Fal playground varsayılanı <strong>Max Sequence Length = 128</strong>. Biz{" "}
                          <strong>512</strong> gönderiyoruz.
                        </p>
                        <pre className="mt-1 max-h-40 overflow-auto rounded bg-gray-100 p-2 text-[11px]">
                          {JSON.stringify(testResult.fal_params, null, 2)}
                        </pre>
                      </details>
                    )}
                    {testResult.gemini_params &&
                      Object.keys(testResult.gemini_params).length > 0 && (
                        <details className="text-xs">
                          <summary className="cursor-pointer font-medium text-gray-600">
                            Gemini parametreler
                          </summary>
                          <pre className="mt-1 max-h-40 overflow-auto rounded bg-gray-100 p-2 text-[11px]">
                            {JSON.stringify(testResult.gemini_params, null, 2)}
                          </pre>
                        </details>
                      )}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        )}

        {/* Form Modal */}
        {showForm && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
            <Card className="max-h-[90vh] w-full max-w-2xl overflow-y-auto">
              <CardHeader>
                <CardTitle>
                  {editingStyle ? "Çizim Tarzını Düzenle" : "Yeni Çizim Tarzı Oluştur"}
                </CardTitle>
                <CardDescription>Görsel stil bilgilerini girin</CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleSubmit} className="space-y-4">
                  <div className="space-y-2">
                    <Label>Tarz Adı (dahili) *</Label>
                    <Input
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      placeholder="Örn: cinematic_3d — eşleme için değiştirmeyin"
                      required
                    />
                    <p className="text-xs text-gray-500">
                      Kod eşlemesi bu isme göre yapılır. Değiştirirseniz stil seçimi bozulabilir.
                    </p>
                  </div>

                  <div className="space-y-2">
                    <Label>Kullanıcıya gösterilen isim (opsiyonel)</Label>
                    <Input
                      value={formData.display_name}
                      onChange={(e) => setFormData({ ...formData, display_name: e.target.value })}
                      placeholder="Boşsa dahili tarz adı kullanılır. Örn: Sihirli Animasyon"
                    />
                    <p className="text-xs text-gray-500">
                      Stil seçim ekranında kullanıcının gördüğü isim. İstediğiniz gibi değiştirebilirsiniz.
                    </p>
                  </div>

                  <div className="space-y-2">
                    <Label>Tarz Görseli</Label>
                    <div className="flex items-center gap-4">
                      <div className="h-32 w-32 flex-shrink-0 overflow-hidden rounded-lg border bg-gray-100">
                        {imagePreview ? (
                          <img
                            src={imagePreview}
                            alt="Preview"
                            className="h-full w-full object-cover"
                          />
                        ) : (
                          <div className="flex h-full w-full items-center justify-center text-gray-400">
                            <Palette className="h-8 w-8" />
                          </div>
                        )}
                      </div>
                      <div className="flex-1">
                        <Input
                          type="file"
                          accept="image/*"
                          onChange={handleImageChange}
                          className="cursor-pointer"
                        />
                        <p className="mt-1 text-xs text-gray-500">
                          PNG, JPG (max 5MB) - Kare format önerilir
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label>AI Prompt Modifier (style_prompt_en) *</Label>
                    <Textarea
                      value={formData.prompt_modifier}
                      onChange={(e) =>
                        setFormData({ ...formData, prompt_modifier: e.target.value })
                      }
                      placeholder="Örn: in Disney Pixar animation style, vibrant colors, 3D rendered..."
                      rows={4}
                      required
                    />
                    <p className="text-xs text-gray-500">
                      Bu metin resim oluştururken AI promptuna eklenir (EN)
                    </p>
                  </div>

                  <div className="space-y-2">
                    <Label>Stil Negatif Promptu (EN) — V2</Label>
                    <Textarea
                      value={formData.style_negative_en}
                      onChange={(e) =>
                        setFormData({ ...formData, style_negative_en: e.target.value })
                      }
                      placeholder="Örn: realistic, photograph, blurry, low quality..."
                      rows={3}
                    />
                    <p className="text-xs text-gray-500">
                      Bu stil için eklenecek negatif prompt. Temel negatif listeye ek olarak
                      uygulanır.
                    </p>
                  </div>

                  <div className="space-y-2 rounded border border-amber-200 bg-amber-50/50 p-3">
                    <Label className="text-amber-800">
                      Leading prefix override (opsiyonel)
                    </Label>
                    <Textarea
                      value={formData.leading_prefix_override}
                      onChange={(e) =>
                        setFormData({ ...formData, leading_prefix_override: e.target.value })
                      }
                      placeholder="Doluysa kod sabiti yerine bu metin prompt başına eklenir. Boş bırakırsanız sistem varsayılanı kullanılır."
                      rows={3}
                    />
                    <p className="text-xs text-gray-600">
                      Örn: Art style: Pixar-quality 3D CGI animation. Rendered in 3D...
                    </p>
                  </div>

                  <div className="space-y-2 rounded border border-amber-200 bg-amber-50/50 p-3">
                    <Label className="text-amber-800">STYLE bloğu override (opsiyonel)</Label>
                    <Textarea
                      value={formData.style_block_override}
                      onChange={(e) =>
                        setFormData({ ...formData, style_block_override: e.target.value })
                      }
                      placeholder="Doluysa kod sabiti yerine bu metin STYLE: bloğunda kullanılır. Boş bırakırsanız sistem varsayılanı kullanılır."
                      rows={3}
                    />
                    <p className="text-xs text-gray-600">
                      Örn: Pixar-quality 3D CGI children&apos;s book illustration, family-friendly...
                    </p>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Kapak En-Boy Oranı</Label>
                      <select
                        value={formData.cover_aspect_ratio}
                        onChange={(e) =>
                          setFormData({ ...formData, cover_aspect_ratio: e.target.value })
                        }
                        className="h-10 w-full rounded-md border bg-background px-3"
                      >
                        {ASPECT_RATIO_OPTIONS.map((opt) => (
                          <option key={opt.value} value={opt.value}>
                            {opt.label}
                          </option>
                        ))}
                      </select>
                    </div>

                    <div className="space-y-2">
                      <Label>Sayfa En-Boy Oranı</Label>
                      <select
                        value={formData.page_aspect_ratio}
                        onChange={(e) =>
                          setFormData({ ...formData, page_aspect_ratio: e.target.value })
                        }
                        className="h-10 w-full rounded-md border bg-background px-3"
                      >
                        {ASPECT_RATIO_OPTIONS.map((opt) => (
                          <option key={opt.value} value={opt.value}>
                            {opt.label}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>

                  {/* PuLID id_weight Control */}
                  <div className="space-y-3 rounded-lg border bg-gradient-to-r from-purple-50 to-blue-50 p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Sliders className="h-4 w-4 text-purple-600" />
                        <Label className="font-semibold">PuLID id_weight</Label>
                      </div>
                      <span
                        className={`text-lg font-bold ${
                          formData.id_weight <= 0.25
                            ? "text-blue-600"
                            : formData.id_weight <= 0.4
                              ? "text-green-600"
                              : "text-orange-600"
                        }`}
                      >
                        {formData.id_weight.toFixed(2)}
                      </span>
                    </div>

                    <Slider
                      value={[formData.id_weight]}
                      onValueChange={(value) => setFormData({ ...formData, id_weight: value[0] })}
                      min={0.1}
                      max={1}
                      step={0.01}
                      className="w-full"
                    />

                    <div className="flex justify-between text-xs text-gray-500">
                      <span className="text-blue-600">← Stilize (0.1)</span>
                      <span className="text-green-600">Dengeli</span>
                      <span className="text-orange-600">Gerçekçi → (1.0)</span>
                    </div>

                    <div className="grid grid-cols-5 gap-1 text-center text-[10px]">
                      <button
                        type="button"
                        onClick={() => setFormData({ ...formData, id_weight: 0.18 })}
                        className="rounded bg-blue-100 p-1 text-blue-700 hover:bg-blue-200"
                      >
                        Anime (0.18)
                      </button>
                      <button
                        type="button"
                        onClick={() => setFormData({ ...formData, id_weight: 0.25 })}
                        className="rounded bg-cyan-100 p-1 text-cyan-700 hover:bg-cyan-200"
                      >
                        Cartoon (0.25)
                      </button>
                      <button
                        type="button"
                        onClick={() => setFormData({ ...formData, id_weight: 0.35 })}
                        className="rounded bg-green-100 p-1 text-green-700 hover:bg-green-200"
                      >
                        3D/Pixar (0.35)
                      </button>
                      <button
                        type="button"
                        onClick={() => setFormData({ ...formData, id_weight: 0.5 })}
                        className="rounded bg-orange-100 p-1 text-orange-700 hover:bg-orange-200"
                      >
                        Gerçekçi (0.50)
                      </button>
                      <button
                        type="button"
                        onClick={() => setFormData({ ...formData, id_weight: 1 })}
                        className="rounded bg-red-100 p-1 text-red-700 hover:bg-red-200"
                      >
                        Max (1.0)
                      </button>
                    </div>

                    <p className="text-xs text-gray-500">
                      Düşük değer = Stil daha baskın (anime yüz) | Yüksek değer = Yüz daha gerçekçi
                    </p>
                  </div>

                  {/* true_cfg */}
                  <div className="space-y-2 rounded-lg border bg-gradient-to-r from-indigo-50 to-purple-50 p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <Label className="font-semibold text-sm">PuLID true_cfg</Label>
                        <p className="text-xs text-gray-500">Prompt bağlılığı — Düşük = yumuşak, Yüksek = katı</p>
                      </div>
                      <div className="flex items-center gap-2">
                        <button
                          type="button"
                          onClick={() => setFormData({ ...formData, true_cfg: formData.true_cfg === null ? 1 : null })}
                          className={`text-xs px-2 py-1 rounded ${formData.true_cfg === null ? "bg-gray-200 text-gray-600" : "bg-indigo-100 text-indigo-700"}`}
                        >
                          {formData.true_cfg === null ? "Otomatik" : `${formData.true_cfg.toFixed(1)}`}
                        </button>
                      </div>
                    </div>
                    {formData.true_cfg !== null && (
                      <>
                        <Slider
                          value={[formData.true_cfg]}
                          onValueChange={(v) => setFormData({ ...formData, true_cfg: v[0] })}
                          min={0.5} max={3} step={0.1} className="w-full"
                        />
                        <div className="flex justify-between text-[10px] text-gray-500">
                          <span>← Esnek (0.5)</span>
                          <span className="text-green-600">1.0 (varsayılan)</span>
                          <span>Katı → (3.0)</span>
                        </div>
                        <div className="grid grid-cols-4 gap-1 text-center text-[10px]">
                          {[["Esnek", 0.7], ["Dengeli", 1], ["Güçlü", 1.5], ["Katı", 2]].map(([label, val]) => (
                            <button key={val} type="button"
                              onClick={() => setFormData({ ...formData, true_cfg: val as number })}
                              className="rounded bg-indigo-100 p-1 text-indigo-700 hover:bg-indigo-200">
                              {label} ({val})
                            </button>
                          ))}
                        </div>
                      </>
                    )}
                  </div>

                  {/* start_step */}
                  <div className="space-y-2 rounded-lg border bg-gradient-to-r from-teal-50 to-green-50 p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <Label className="font-semibold text-sm">PuLID start_step</Label>
                        <p className="text-xs text-gray-500">Yüz enjeksiyonu başlangıç adımı — Düşük = daha fazla yüz benzerliği</p>
                      </div>
                      <button
                        type="button"
                        onClick={() => setFormData({ ...formData, start_step: formData.start_step === null ? 1 : null })}
                        className={`text-xs px-2 py-1 rounded ${formData.start_step === null ? "bg-gray-200 text-gray-600" : "bg-teal-100 text-teal-700"}`}
                      >
                        {formData.start_step === null ? "Otomatik" : `Adım ${formData.start_step}`}
                      </button>
                    </div>
                    {formData.start_step !== null && (
                      <>
                        <Slider
                          value={[formData.start_step]}
                          onValueChange={(v) => setFormData({ ...formData, start_step: v[0] })}
                          min={0} max={5} step={1} className="w-full"
                        />
                        <div className="grid grid-cols-4 gap-1 text-center text-[10px]">
                          {[["Anime (0)", 0], ["Varsayılan (1)", 1], ["Pixar (2)", 2], ["Stil önce (3)", 3]].map(([label, val]) => (
                            <button key={val} type="button"
                              onClick={() => setFormData({ ...formData, start_step: val as number })}
                              className="rounded bg-teal-100 p-1 text-teal-700 hover:bg-teal-200">
                              {label}
                            </button>
                          ))}
                        </div>
                      </>
                    )}
                  </div>

                  {/* FLUX Generation Parameters */}
                  <div className="rounded-lg border border-orange-200 bg-gradient-to-r from-orange-50 to-amber-50 p-4 space-y-4">
                    <div className="flex items-center gap-2">
                      <Sliders className="h-4 w-4 text-orange-600" />
                      <Label className="font-semibold text-orange-800">FLUX Üretim Parametreleri</Label>
                    </div>

                    {/* num_inference_steps */}
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <div>
                          <Label className="text-sm font-medium">num_inference_steps</Label>
                          <p className="text-xs text-gray-500">Kalite/hız dengesi — Varsayılan: 28</p>
                        </div>
                        <button
                          type="button"
                          onClick={() => setFormData({ ...formData, num_inference_steps: formData.num_inference_steps === null ? 28 : null })}
                          className={`text-xs px-2 py-1 rounded ${formData.num_inference_steps === null ? "bg-gray-200 text-gray-600" : "bg-orange-100 text-orange-700"}`}
                        >
                          {formData.num_inference_steps === null ? "Otomatik (28)" : `${formData.num_inference_steps} adım`}
                        </button>
                      </div>
                      {formData.num_inference_steps !== null && (
                        <>
                          <Slider
                            value={[formData.num_inference_steps]}
                            onValueChange={(v) => setFormData({ ...formData, num_inference_steps: v[0] })}
                            min={10} max={50} step={1} className="w-full"
                          />
                          <div className="grid grid-cols-4 gap-1 text-center text-[10px]">
                            {[["Hızlı (20)", 20], ["Normal (28)", 28], ["Kaliteli (35)", 35], ["Max (50)", 50]].map(([label, val]) => (
                              <button key={val} type="button"
                                onClick={() => setFormData({ ...formData, num_inference_steps: val as number })}
                                className="rounded bg-orange-100 p-1 text-orange-700 hover:bg-orange-200">
                                {label}
                              </button>
                            ))}
                          </div>
                        </>
                      )}
                    </div>

                    {/* guidance_scale */}
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <div>
                          <Label className="text-sm font-medium">guidance_scale (CFG)</Label>
                          <p className="text-xs text-gray-500">Prompt uyumu — Varsayılan: 3.5</p>
                        </div>
                        <button
                          type="button"
                          onClick={() => setFormData({ ...formData, guidance_scale: formData.guidance_scale === null ? 3.5 : null })} // eslint-disable-line
                          className={`text-xs px-2 py-1 rounded ${formData.guidance_scale === null ? "bg-gray-200 text-gray-600" : "bg-amber-100 text-amber-700"}`}
                        >
                          {formData.guidance_scale === null ? "Otomatik (3.5)" : formData.guidance_scale.toFixed(1)}
                        </button>
                      </div>
                      {formData.guidance_scale !== null && (
                        <>
                          <Slider
                            value={[formData.guidance_scale]}
                            onValueChange={(v) => setFormData({ ...formData, guidance_scale: v[0] })}
                            min={1} max={10} step={0.1} className="w-full"
                          />
                          <div className="flex justify-between text-[10px] text-gray-500">
                            <span>← Yaratıcı (1.0)</span>
                            <span className="text-green-600">3.5 (varsayılan)</span>
                            <span>Katı → (10.0)</span>
                          </div>
                          <div className="grid grid-cols-4 gap-1 text-center text-[10px]">
                            {[["Yumuşak (2.5)", 2.5], ["Normal (3.5)", 3.5], ["Güçlü (4.5)", 4.5], ["Sert (6)", 6]].map(([label, val]) => (
                              <button key={val} type="button"
                                onClick={() => setFormData({ ...formData, guidance_scale: val as number })}
                                className="rounded bg-amber-100 p-1 text-amber-700 hover:bg-amber-200">
                                {label}
                              </button>
                            ))}
                          </div>
                        </>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center justify-between rounded-lg border p-3">
                    <div>
                      <Label>Aktif</Label>
                      <p className="text-xs text-gray-500">Kullanıcılara gösterilsin mi?</p>
                    </div>
                    <Switch
                      checked={formData.is_active}
                      onCheckedChange={(checked) =>
                        setFormData({ ...formData, is_active: checked })
                      }
                    />
                  </div>

                  <div className="flex justify-end gap-2 pt-4">
                    <Button
                      type="button"
                      variant="outline"
                      onClick={() => {
                        setShowForm(false);
                        resetForm();
                      }}
                    >
                      İptal
                    </Button>
                    <Button type="submit" disabled={saving}>
                      {saving ? "Kaydediliyor..." : editingStyle ? "Güncelle" : "Oluştur"}
                    </Button>
                  </div>
                </form>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
}
