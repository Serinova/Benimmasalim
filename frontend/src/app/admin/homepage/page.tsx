"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/hooks/use-toast";
import {
  Eye,
  Save,
  GripVertical,
  ChevronDown,
  ChevronUp,
  LayoutDashboard,
  Sparkles,
  Shield,
  HelpCircle,
  Star,
  Image,
  CreditCard,
  MessageSquareQuote,
  Megaphone,
  Globe,
  Upload,
  Trash2,
  Plus,
  Loader2,
  ImageIcon,
} from "lucide-react";
import { API_BASE_URL } from "@/lib/api";

/* ─── Types ───────────────────────────────────────────────────────── */

interface HomepageSection {
  id: string;
  section_type: string;
  title: string | null;
  subtitle: string | null;
  is_visible: boolean;
  sort_order: number;
  data: Record<string, unknown>;
}

/* ─── Helpers ─────────────────────────────────────────────────────── */

const SECTION_META: Record<
  string,
  { label: string; icon: React.ReactNode; description: string }
> = {
  HERO: {
    label: "Hero / Ana Bölüm",
    icon: <Sparkles className="h-5 w-5" />,
    description: "Ana başlık, alt metin, CTA butonları",
  },
  TRUST_BAR: {
    label: "Güven Göstergeleri",
    icon: <Shield className="h-5 w-5" />,
    description: "KVKK, güvenli ödeme, teslimat",
  },
  HOW_IT_WORKS: {
    label: "Nasıl Çalışır?",
    icon: <LayoutDashboard className="h-5 w-5" />,
    description: "3 adım akışı",
  },
  FEATURES: {
    label: "Özellikler",
    icon: <Star className="h-5 w-5" />,
    description: "Değer önerileri kartları",
  },
  PREVIEW: {
    label: "Örnek Sayfalar",
    // Decorative Lucide icon (SVG), not <img>; alt not applicable
    /* eslint-disable-next-line jsx-a11y/alt-text */
    icon: <Image className="h-5 w-5" aria-hidden />,
    description: "Kitap sayfa önizlemeleri",
  },
  TESTIMONIALS: {
    label: "Müşteri Yorumları",
    icon: <MessageSquareQuote className="h-5 w-5" />,
    description: "Aile yorumları",
  },
  PRICING: {
    label: "Fiyatlandırma",
    icon: <CreditCard className="h-5 w-5" />,
    description: "Paket ve fiyat bilgisi",
  },
  FAQ: {
    label: "Sıkça Sorulan Sorular",
    icon: <HelpCircle className="h-5 w-5" />,
    description: "SSS accordion",
  },
  CTA_BAND: {
    label: "CTA Bandı",
    icon: <Megaphone className="h-5 w-5" />,
    description: "Son dönüşüm çağrısı",
  },
  FOOTER: {
    label: "Footer",
    icon: <Globe className="h-5 w-5" />,
    description: "Alt menü, linkler, marka",
  },
};

function getAuthHeaders(): Record<string, string> {
  const token = localStorage.getItem("token");
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

function checkAuth(router: ReturnType<typeof useRouter>): boolean {
  const userStr = localStorage.getItem("user");
  if (!userStr) {
    router.push("/auth/login");
    return false;
  }
  try {
    const u = JSON.parse(userStr);
    if (u.role !== "admin") {
      router.push("/");
      return false;
    }
    return true;
  } catch {
    router.push("/auth/login");
    return false;
  }
}

/* ─── JSON Editor Component ───────────────────────────────────────── */

function JsonDataEditor({
  data,
  onChange,
}: {
  data: Record<string, unknown>;
  onChange: (d: Record<string, unknown>) => void;
}) {
  const [raw, setRaw] = useState(JSON.stringify(data, null, 2));
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setRaw(JSON.stringify(data, null, 2));
    setError(null);
  }, [data]);

  const handleBlur = () => {
    try {
      const parsed = JSON.parse(raw);
      setError(null);
      onChange(parsed);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Geçersiz JSON");
    }
  };

  return (
    <div className="space-y-2">
      <Label className="text-xs font-medium text-slate-500">
        Bölüm Verileri (JSON)
      </Label>
      <textarea
        className="w-full rounded-lg border bg-slate-50 p-3 font-mono text-xs leading-relaxed focus:border-indigo-300 focus:outline-none focus:ring-2 focus:ring-indigo-100"
        rows={Math.min(Math.max(raw.split("\n").length, 6), 20)}
        value={raw}
        onChange={(e) => setRaw(e.target.value)}
        onBlur={handleBlur}
        spellCheck={false}
      />
      {error && (
        <p className="text-xs font-medium text-red-500">JSON Hatası: {error}</p>
      )}
    </div>
  );
}

/* ─── Preview Items Editor (image upload + add/remove) ────────────── */

interface PreviewItemData {
  title: string;
  description: string;
  color?: string;
  image?: string;
}

function PreviewItemsEditor({
  items,
  onChange,
}: {
  items: PreviewItemData[];
  onChange: (items: PreviewItemData[]) => void;
}) {
  const [uploadingIdx, setUploadingIdx] = useState<number | null>(null);
  const { toast } = useToast();

  const uploadImage = async (file: File, idx: number) => {
    setUploadingIdx(idx);
    try {
      const formData = new FormData();
      formData.append("image", file);

      const token = localStorage.getItem("token");
      const res = await fetch(`${API_BASE_URL}/admin/homepage/upload-image`, {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body: formData,
      });

      if (!res.ok) {
        const err = await res.json().catch(() => null);
        throw new Error(err?.detail ?? "Resim yüklenemedi");
      }

      const { url } = (await res.json()) as { url: string };
      if (!url) throw new Error("URL döndürülemedi");
      const updated = items.map((item, i) =>
        i === idx ? { ...item, image: url } : item
      );
      onChange(updated);
      toast({ title: "Başarılı", description: `Resim yüklendi` });
    } catch (err: unknown) {
      toast({
        title: "Hata",
        description: err instanceof Error ? err.message : "Yükleme başarısız",
        variant: "destructive",
      });
    } finally {
      setUploadingIdx(null);
    }
  };

  const addItem = () => {
    onChange([
      ...items,
      { title: "Yeni Sayfa", description: "Açıklama ekleyin", color: "from-slate-100 to-slate-200" },
    ]);
  };

  const removeItem = (idx: number) => {
    const updated = items.filter((_, i) => i !== idx);
    onChange(updated);
  };

  const updateField = (idx: number, field: keyof PreviewItemData, value: string) => {
    const updated = [...items];
    updated[idx] = { ...updated[idx], [field]: value };
    onChange(updated);
  };

  const removeImage = (idx: number) => {
    const updated = [...items];
    const { image: _removed, ...rest } = updated[idx];
    updated[idx] = rest as PreviewItemData;
    onChange(updated);
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <Label className="text-xs font-medium text-slate-500">
          Örnek Sayfalar ({items.length} adet)
        </Label>
        <Button variant="outline" size="sm" onClick={addItem} className="gap-1.5 text-xs">
          <Plus className="h-3.5 w-3.5" /> Yeni Sayfa Ekle
        </Button>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        {items.map((item, idx) => (
          <div
            key={idx}
            className="relative rounded-lg border bg-white p-3 shadow-sm"
          >
            {/* Image area */}
            <div className="relative mb-3 aspect-[3/4] overflow-hidden rounded-lg bg-slate-50">
              {item.image ? (
                <>
                  <img
                    src={item.image}
                    alt={item.title}
                    className="h-full w-full object-cover"
                  />
                  <button
                    onClick={() => removeImage(idx)}
                    className="absolute right-2 top-2 rounded-full bg-red-500 p-1.5 text-white shadow-md transition-colors hover:bg-red-600"
                    title="Resmi kaldır"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </>
              ) : (
                <div className={`flex h-full w-full items-center justify-center bg-gradient-to-br ${item.color ?? "from-slate-100 to-slate-200"}`}>
                  <ImageIcon className="h-8 w-8 text-slate-300" />
                </div>
              )}

              {/* Upload overlay */}
              <label
                className="absolute inset-0 flex cursor-pointer items-center justify-center bg-black/0 transition-colors hover:bg-black/30"
                title="Resim yükle"
              >
                {uploadingIdx === idx ? (
                  <Loader2 className="h-8 w-8 animate-spin text-white" />
                ) : (
                  <div className="flex flex-col items-center gap-1 opacity-0 transition-opacity hover:opacity-100">
                    <Upload className="h-8 w-8 text-white drop-shadow-lg" />
                    <span className="text-xs font-medium text-white drop-shadow-lg">
                      Resim Yükle
                    </span>
                  </div>
                )}
                <input
                  type="file"
                  accept="image/jpeg,image/png,image/webp"
                  className="hidden"
                  onChange={(e) => {
                    const file = e.target.files?.[0];
                    if (file) uploadImage(file, idx);
                    e.target.value = "";
                  }}
                  disabled={uploadingIdx !== null}
                />
              </label>
            </div>

            {/* Title */}
            <Input
              value={item.title}
              onChange={(e) => updateField(idx, "title", e.target.value)}
              placeholder="Başlık..."
              className="mb-2 text-sm font-semibold"
            />

            {/* Description */}
            <Input
              value={item.description}
              onChange={(e) => updateField(idx, "description", e.target.value)}
              placeholder="Açıklama..."
              className="text-xs"
            />

            {/* Remove button */}
            {items.length > 1 && (
              <button
                onClick={() => removeItem(idx)}
                className="absolute -right-2 -top-2 rounded-full border bg-white p-1 text-red-500 shadow-sm transition-colors hover:bg-red-50"
                title="Sayfayı sil"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

/* ─── Showcase Book Pages Editor (HERO section) ───────────────────── */

function ShowcaseBookEditor({
  pages,
  onChange,
}: {
  pages: string[];
  onChange: (pages: string[]) => void;
}) {
  const [uploadingIdx, setUploadingIdx] = useState<number | null>(null);
  const { toast } = useToast();

  const uploadImage = async (file: File, idx: number) => {
    setUploadingIdx(idx);
    try {
      const formData = new FormData();
      formData.append("image", file);
      const token = localStorage.getItem("token");
      const res = await fetch(`${API_BASE_URL}/admin/homepage/upload-image`, {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body: formData,
      });
      if (!res.ok) {
        const err = await res.json().catch(() => null);
        throw new Error(err?.detail ?? "Resim yüklenemedi");
      }
      const { url } = (await res.json()) as { url: string };
      const updated = [...pages];
      updated[idx] = url;
      onChange(updated);
      toast({ title: "Başarılı", description: `Sayfa ${idx + 1} yüklendi` });
    } catch (err: unknown) {
      toast({
        title: "Hata",
        description: err instanceof Error ? err.message : "Yükleme başarısız",
        variant: "destructive",
      });
    } finally {
      setUploadingIdx(null);
    }
  };

  const addPage = () => onChange([...pages, ""]);
  const removePage = (idx: number) => onChange(pages.filter((_, i) => i !== idx));

  return (
    <div className="space-y-4 rounded-lg border border-amber-200 bg-amber-50/50 p-4">
      <div className="flex items-center justify-between">
        <div>
          <Label className="text-sm font-semibold text-amber-800">
            Vitrin Kitabı Sayfaları
          </Label>
          <p className="text-xs text-amber-600">
            Hero alanında yatay dergi formatında gösterilir. Tıklanınca tam ekran sayfa çevirme ile açılır.
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={addPage} className="gap-1.5 text-xs">
          <Plus className="h-3.5 w-3.5" /> Sayfa Ekle
        </Button>
      </div>

      {pages.length === 0 ? (
        <div className="rounded-lg border-2 border-dashed border-amber-300 p-6 text-center text-sm text-amber-600">
          Henüz sayfa eklenmedi. &quot;Sayfa Ekle&quot; ile başlayın.
        </div>
      ) : (
        <div className="grid grid-cols-3 gap-3 sm:grid-cols-4 md:grid-cols-5">
          {pages.map((url, idx) => (
            <div key={idx} className="group relative">
              <div className="relative aspect-[297/210] overflow-hidden rounded-lg border-2 border-amber-200 bg-white shadow-sm">
                {url ? (
                  <img src={url} alt={`Sayfa ${idx + 1}`} className="h-full w-full object-cover" />
                ) : (
                  <div className="flex h-full w-full items-center justify-center bg-gradient-to-br from-amber-50 to-orange-50">
                    <ImageIcon className="h-8 w-8 text-amber-300" />
                  </div>
                )}
                {/* Upload overlay */}
                <label className="absolute inset-0 flex cursor-pointer items-center justify-center bg-black/0 transition-colors hover:bg-black/30">
                  {uploadingIdx === idx ? (
                    <Loader2 className="h-6 w-6 animate-spin text-white" />
                  ) : (
                    <Upload className="h-6 w-6 text-white opacity-0 drop-shadow-lg transition-opacity group-hover:opacity-100" />
                  )}
                  <input
                    type="file"
                    accept="image/jpeg,image/png,image/webp"
                    className="hidden"
                    onChange={(e) => {
                      const file = e.target.files?.[0];
                      if (file) uploadImage(file, idx);
                      e.target.value = "";
                    }}
                    disabled={uploadingIdx !== null}
                  />
                </label>
              </div>
              {/* Page number + remove */}
              <div className="mt-1 flex items-center justify-between">
                <span className="text-[10px] font-medium text-amber-700">
                  {idx === 0 ? "Kapak" : `Sayfa ${idx}`}
                </span>
                <button
                  onClick={() => removePage(idx)}
                  className="rounded p-0.5 text-red-400 transition-colors hover:bg-red-50 hover:text-red-600"
                  title="Sayfayı sil"
                >
                  <Trash2 className="h-3 w-3" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

/* ─── Section Card Component ──────────────────────────────────────── */

function SectionCard({
  section,
  onUpdate,
  onToggleVisibility,
}: {
  section: HomepageSection;
  onUpdate: (id: string, payload: Partial<HomepageSection>) => Promise<void>;
  onToggleVisibility: (id: string) => Promise<void>;
}) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [localTitle, setLocalTitle] = useState(section.title ?? "");
  const [localSubtitle, setLocalSubtitle] = useState(section.subtitle ?? "");
  const [localData, setLocalData] = useState(section.data);
  const [saving, setSaving] = useState(false);

  const meta = SECTION_META[section.section_type] ?? {
    label: section.section_type,
    icon: <LayoutDashboard className="h-5 w-5" />,
    description: "",
  };

  const isDirty =
    localTitle !== (section.title ?? "") ||
    localSubtitle !== (section.subtitle ?? "") ||
    JSON.stringify(localData) !== JSON.stringify(section.data);

  const handleSave = async () => {
    setSaving(true);
    try {
      await onUpdate(section.id, {
        title: localTitle || null,
        subtitle: localSubtitle || null,
        data: localData,
      });
    } finally {
      setSaving(false);
    }
  };

  return (
    <Card
      className={`transition-all ${!section.is_visible ? "opacity-60" : ""}`}
    >
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <GripVertical className="h-4 w-4 cursor-grab text-slate-400" />
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-indigo-50 text-indigo-600">
              {meta.icon}
            </div>
            <div>
              <CardTitle className="text-base">{meta.label}</CardTitle>
              <CardDescription className="text-xs">
                {meta.description}
              </CardDescription>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {isDirty && (
              <Badge variant="warning" className="text-xs">
                Kaydedilmedi
              </Badge>
            )}
            <Badge
              variant={section.is_visible ? "success" : "secondary"}
              className="text-xs"
            >
              {section.is_visible ? "Görünür" : "Gizli"}
            </Badge>

            <Switch
              checked={section.is_visible}
              onCheckedChange={() => onToggleVisibility(section.id)}
              aria-label="Görünürlüğü değiştir"
            />

            <Button
              variant="ghost"
              size="icon"
              onClick={() => setIsExpanded(!isExpanded)}
              aria-label={isExpanded ? "Kapat" : "Düzenle"}
            >
              {isExpanded ? (
                <ChevronUp className="h-4 w-4" />
              ) : (
                <ChevronDown className="h-4 w-4" />
              )}
            </Button>
          </div>
        </div>
      </CardHeader>

      {isExpanded && (
        <CardContent className="space-y-4 border-t pt-4">
          {/* Title & subtitle */}
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-1.5">
              <Label htmlFor={`title-${section.id}`} className="text-xs text-slate-500">
                Başlık
              </Label>
              <Input
                id={`title-${section.id}`}
                value={localTitle}
                onChange={(e) => setLocalTitle(e.target.value)}
                placeholder="Bölüm başlığı..."
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor={`subtitle-${section.id}`} className="text-xs text-slate-500">
                Alt Başlık
              </Label>
              <Input
                id={`subtitle-${section.id}`}
                value={localSubtitle}
                onChange={(e) => setLocalSubtitle(e.target.value)}
                placeholder="Bölüm alt başlığı..."
              />
            </div>
          </div>

          {/* Section-specific data editors */}
          {section.section_type === "HERO" && (
            <ShowcaseBookEditor
              pages={(localData.showcase_pages as string[] | undefined) ?? []}
              onChange={(newPages) =>
                setLocalData((prev) => ({ ...prev, showcase_pages: newPages }))
              }
            />
          )}

          {section.section_type === "PREVIEW" ? (
            <PreviewItemsEditor
              items={(localData.items as PreviewItemData[] | undefined) ?? []}
              onChange={(newItems) =>
                setLocalData((prev) => ({ ...prev, items: newItems }))
              }
            />
          ) : (
            <JsonDataEditor data={localData} onChange={setLocalData} />
          )}

          {/* Save */}
          <div className="flex justify-end">
            <Button
              onClick={handleSave}
              disabled={!isDirty || saving}
              className="gap-2"
            >
              <Save className="h-4 w-4" />
              {saving ? "Kaydediliyor..." : "Kaydet"}
            </Button>
          </div>
        </CardContent>
      )}
    </Card>
  );
}

/* ─── Main Page ───────────────────────────────────────────────────── */

export default function AdminHomepagePage() {
  const router = useRouter();
  const { toast } = useToast();
  const [sections, setSections] = useState<HomepageSection[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchSections = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/admin/homepage`, {
        headers: getAuthHeaders(),
      });
      if (res.status === 401) {
        localStorage.removeItem("token");
        localStorage.removeItem("user");
        router.push("/auth/login");
        return;
      }
      if (!res.ok) throw new Error("Bölümler yüklenemedi");
      const data: HomepageSection[] = await res.json();
      setSections(data);
    } catch (err: unknown) {
      toast({
        title: "Hata",
        description: err instanceof Error ? err.message : "Bilinmeyen hata",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  }, [router, toast]);

  useEffect(() => {
    if (!checkAuth(router)) return;
    fetchSections();
  }, [router, fetchSections]);

  const handleUpdate = async (
    id: string,
    payload: Partial<HomepageSection>
  ) => {
    try {
      const res = await fetch(`${API_BASE_URL}/admin/homepage/${id}`, {
        method: "PATCH",
        headers: getAuthHeaders(),
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const errData = await res.json().catch(() => null);
        throw new Error(errData?.detail ?? "Güncelleme başarısız");
      }
      toast({ title: "Başarılı", description: "Bölüm güncellendi" });
      await fetchSections();
    } catch (err: unknown) {
      toast({
        title: "Hata",
        description: err instanceof Error ? err.message : "Bilinmeyen hata",
        variant: "destructive",
      });
    }
  };

  const handleToggleVisibility = async (id: string) => {
    try {
      const res = await fetch(
        `${API_BASE_URL}/admin/homepage/${id}/visibility`,
        { method: "PATCH", headers: getAuthHeaders() }
      );
      if (!res.ok) throw new Error("Görünürlük değiştirilemedi");
      toast({ title: "Başarılı", description: "Görünürlük güncellendi" });
      await fetchSections();
    } catch (err: unknown) {
      toast({
        title: "Hata",
        description: err instanceof Error ? err.message : "Bilinmeyen hata",
        variant: "destructive",
      });
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-200 border-t-indigo-600" />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900">
          Ana Sayfa Yönetimi
        </h1>
        <p className="mt-1 text-sm text-slate-500">
          Homepage bölümlerinin içeriklerini düzenleyin, gizleyin veya sıralayın.
        </p>
      </div>

      {/* Info badge */}
      <div className="flex items-start gap-3 rounded-lg border border-indigo-100 bg-indigo-50 p-4">
        <Eye className="mt-0.5 h-5 w-5 shrink-0 text-indigo-600" />
        <div className="text-sm text-indigo-800">
          <p className="font-medium">Bölüm Yönetimi</p>
          <p className="mt-1 text-indigo-600">
            Her bölümün başlığını, alt başlığını ve verilerini (JSON) düzenleyebilirsiniz.
            Gizle/göster anahtarıyla bölümleri anında kapatabilirsiniz.
          </p>
        </div>
      </div>

      {/* Section list */}
      <div className="space-y-3">
        {sections.map((section) => (
          <SectionCard
            key={section.id}
            section={section}
            onUpdate={handleUpdate}
            onToggleVisibility={handleToggleVisibility}
          />
        ))}
      </div>

      {sections.length === 0 && (
        <Card>
          <CardContent className="py-12 text-center text-sm text-slate-500">
            Henüz homepage bölümü bulunamadı. Migration çalıştırıldığından emin
            olun.
          </CardContent>
        </Card>
      )}
    </div>
  );
}
