"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAdminAuth } from "@/hooks/use-admin-auth";
import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { motion, AnimatePresence } from "framer-motion";
import {
  Plus,
  Pencil,
  Trash2,
  Copy,
  Palette,
  Sparkles,
  Brain,
  Eye,
  EyeOff,
  GripVertical,
  CheckCircle2,
  AlertCircle,
  RotateCw,
  Settings2,
  FileText,
  Users,
  Heart,
  Shield,
  Lightbulb,
  Leaf,
  Target,
  ExternalLink,
  RefreshCw,
  Link2,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Card, CardContent } from "@/components/ui/card";
import { useToast } from "@/hooks/use-toast";
import { getAdminHeaders as getAuthHeaders, API_BASE_URL } from "@/lib/adminFetch";

// ============ TYPES ============
interface LearningOutcome {
  id: string;
  name: string;
  description: string | null;
  icon_url: string | null;
  color_theme: string | null;
  ai_prompt: string | null;
  ai_prompt_instruction: string | null;
  effective_ai_instruction: string | null;
  banned_words_tr: string | null; // V2: yasaklı kelimeler
  category: string;
  category_label: string | null;
  age_group: string;
  display_order: number;
  is_active: boolean;
  // Linked prompt info
  linked_prompt_key?: string;
  linked_prompt_exists?: boolean;
}

// Helper to generate prompt key from name
function getPromptKeyFromName(name: string): string {
  const trMap: Record<string, string> = {
    ş: "s",
    Ş: "S",
    ı: "i",
    İ: "I",
    ö: "o",
    Ö: "O",
    ü: "u",
    Ü: "U",
    ğ: "g",
    Ğ: "G",
    ç: "c",
    Ç: "C",
  };
  let key = name.toLowerCase();
  for (const [tr, en] of Object.entries(trMap)) {
    key = key.split(tr).join(en.toLowerCase());
  }
  key = key
    .replace(/[^a-z0-9_]/g, "_")
    .replace(/_+/g, "_")
    .replace(/^_|_$/g, "");
  return `EDUCATIONAL_${key}`;
}

// Category definitions
const CATEGORIES = [
  { id: "SelfCare", label: "Öz Bakım", icon: Heart, color: "#EC4899" },
  { id: "PersonalGrowth", label: "Kişisel Gelişim", icon: Lightbulb, color: "#F59E0B" },
  { id: "SocialSkills", label: "Sosyal Beceriler", icon: Users, color: "#3B82F6" },
  { id: "EducationNature", label: "Eğitim & Doğa", icon: Leaf, color: "#10B981" },
  { id: "Values", label: "Değerler", icon: Shield, color: "#8B5CF6" },
];

// Preset colors for quick selection
const PRESET_COLORS = [
  "#EC4899",
  "#F43F5E",
  "#F97316",
  "#F59E0B",
  "#EAB308",
  "#84CC16",
  "#22C55E",
  "#10B981",
  "#14B8A6",
  "#06B6D4",
  "#0EA5E9",
  "#3B82F6",
  "#6366F1",
  "#8B5CF6",
  "#A855F7",
  "#D946EF",
  "#F472B6",
  "#FB7185",
];

// ============ FORM SCHEMA ============
const outcomeSchema = z.object({
  name: z.string().min(1, "Kazanım adı zorunludur"),
  description: z.string().optional(),
  icon_url: z.string().optional(),
  color_theme: z.string().optional(),
  ai_prompt_instruction: z.string().optional(),
  ai_prompt: z.string().optional(),
  banned_words_tr: z.string().optional(),
  category: z.string().min(1, "Kategori zorunludur"),
  category_label: z.string().optional(),
  age_group: z.string(),
  display_order: z.number(),
  is_active: z.boolean(),
});

type OutcomeFormData = z.infer<typeof outcomeSchema>;

// ============ COLOR PICKER ============
function ColorPicker({ value, onChange }: { value: string; onChange: (color: string) => void }) {
  const [customColor, setCustomColor] = useState(value || "#8B5CF6");

  return (
    <div className="space-y-3">
      {/* Preset colors */}
      <div className="flex flex-wrap gap-2">
        {PRESET_COLORS.map((color) => (
          <button
            key={color}
            type="button"
            onClick={() => onChange(color)}
            className={`h-8 w-8 rounded-full border-2 transition-all hover:scale-110 ${
              value === color
                ? "border-gray-800 ring-2 ring-gray-400 ring-offset-2"
                : "border-transparent"
            }`}
            style={{ backgroundColor: color }}
          />
        ))}
      </div>

      {/* Custom color input */}
      <div className="flex items-center gap-2">
        <Input
          type="color"
          value={customColor}
          onChange={(e) => {
            setCustomColor(e.target.value);
            onChange(e.target.value);
          }}
          className="h-10 w-12 cursor-pointer p-1"
        />
        <Input
          value={value || ""}
          onChange={(e) => onChange(e.target.value)}
          placeholder="#RRGGBB"
          className="font-mono"
        />
      </div>
    </div>
  );
}

// ============ OUTCOME CARD PREVIEW ============
function OutcomeCardPreview({ outcome }: { outcome: Partial<LearningOutcome> }) {
  const category = CATEGORIES.find((c) => c.id === outcome.category);
  const CategoryIcon = category?.icon || Sparkles;
  const color = outcome.color_theme || category?.color || "#8B5CF6";

  return (
    <div className="rounded-xl border-2 bg-white p-4 transition-all" style={{ borderColor: color }}>
      {/* Header */}
      <div className="flex items-start gap-3">
        <div
          className="flex h-12 w-12 items-center justify-center rounded-xl"
          style={{ backgroundColor: `${color}20` }}
        >
          {outcome.icon_url ? (
            <img src={outcome.icon_url} alt="" className="h-7 w-7" />
          ) : (
            <CategoryIcon className="h-6 w-6" style={{ color }} />
          )}
        </div>
        <div className="min-w-0 flex-1">
          <h4 className="truncate font-semibold text-gray-900">{outcome.name || "Kazanım Adı"}</h4>
          <p className="line-clamp-2 text-sm text-gray-500">
            {outcome.description || "Açıklama..."}
          </p>
        </div>
      </div>

      {/* Category badge */}
      <div className="mt-3 flex items-center gap-2">
        <Badge
          variant="secondary"
          className="text-xs"
          style={{ backgroundColor: `${color}15`, color }}
        >
          {outcome.category_label || category?.label || "Kategori"}
        </Badge>
        {outcome.is_active === false && (
          <Badge variant="secondary" className="text-xs">
            <EyeOff className="mr-1 h-3 w-3" />
            Pasif
          </Badge>
        )}
      </div>

      {/* AI Instruction preview */}
      {outcome.ai_prompt_instruction && (
        <div className="mt-3 rounded-lg bg-gray-50 p-2">
          <p className="mb-1 flex items-center gap-1 text-xs text-gray-500">
            <Brain className="h-3 w-3" />
            AI Talimatı
          </p>
          <p className="line-clamp-2 text-xs text-gray-600">{outcome.ai_prompt_instruction}</p>
        </div>
      )}
    </div>
  );
}

// Sync status type
interface SyncStatus {
  total_outcomes: number;
  total_educational_prompts: number;
  outcomes_with_prompt: number;
  outcomes_without_prompt: number;
  orphan_prompts: number;
  orphan_prompt_list: Array<{ id: string; key: string; name: string; is_active: boolean }>;
}

// ============ MAIN PAGE COMPONENT ============
export default function AdminLearningOutcomesPage() {
  const [outcomes, setOutcomes] = useState<LearningOutcome[]>([]);
  const [loading, setLoading] = useState(true);
  const [isEditorOpen, setIsEditorOpen] = useState(false);
  const [editingOutcome, setEditingOutcome] = useState<LearningOutcome | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);
  const [activeFilter, setActiveFilter] = useState<string>("all");
  const [syncStatus, setSyncStatus] = useState<SyncStatus | null>(null);
  const [syncing, setSyncing] = useState(false);

  const router = useRouter();
  const { toast } = useToast();


  const form = useForm<OutcomeFormData>({
    resolver: zodResolver(outcomeSchema),
    defaultValues: {
      name: "",
      description: "",
      icon_url: "",
      color_theme: "",
      ai_prompt_instruction: "",
      ai_prompt: "",
      banned_words_tr: "",
      category: "PersonalGrowth",
      category_label: "Kişisel Gelişim",
      age_group: "3-10",
      display_order: 0,
      is_active: true,
    },
  });

  const watchedValues = form.watch();

  useAdminAuth();

  useEffect(() => {
    fetchOutcomes();
    fetchSyncStatus();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);


  const fetchOutcomes = async () => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/admin/learning-outcomes?include_inactive=true`,
        { headers: getAuthHeaders() }
      );
      if (response.status === 401) {
        router.push("/auth/login");
        return;
      }
      if (response.ok) {
        const data = await response.json();
        setOutcomes(data);
      }
    } catch (error) {
      toast({ title: "Hata", description: "Kazanımlar yüklenemedi", variant: "destructive" });
    } finally {
      setLoading(false);
    }
  };

  const fetchSyncStatus = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/admin/learning-outcomes/sync/status`, {
        headers: getAuthHeaders(),
      });
      if (response.ok) {
        const data = await response.json();
        setSyncStatus(data);
      }
    } catch (error) {
      console.error("Failed to fetch sync status:", error);
    }
  };

  const executeSync = async () => {
    setSyncing(true);
    try {
      const response = await fetch(
        `${API_BASE_URL}/admin/learning-outcomes/sync/execute?delete_orphans=true&create_missing=true`,
        { method: "POST", headers: getAuthHeaders() }
      );
      if (response.ok) {
        const data = await response.json();
        toast({
          title: "Senkronizasyon Tamamlandı",
          description: data.message,
        });
        fetchOutcomes();
        fetchSyncStatus();
      } else {
        const error = await response.json();
        throw new Error(error.detail || "Senkronizasyon başarısız");
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : "Bilinmeyen hata";
      toast({ title: "Hata", description: message, variant: "destructive" });
    } finally {
      setSyncing(false);
    }
  };

  const openEditor = (outcome?: LearningOutcome) => {
    if (outcome) {
      setEditingOutcome(outcome);
      form.reset({
        name: outcome.name,
        description: outcome.description || "",
        icon_url: outcome.icon_url || "",
        color_theme: outcome.color_theme || "",
        ai_prompt_instruction: outcome.ai_prompt_instruction || "",
        ai_prompt: outcome.ai_prompt || "",
        banned_words_tr: outcome.banned_words_tr || "",
        category: outcome.category,
        category_label: outcome.category_label || "",
        age_group: outcome.age_group,
        display_order: outcome.display_order,
        is_active: outcome.is_active,
      });
    } else {
      setEditingOutcome(null);
      const nextOrder =
        outcomes.length > 0 ? Math.max(...outcomes.map((o) => o.display_order)) + 1 : 0;
      form.reset({
        name: "",
        description: "",
        icon_url: "",
        color_theme: "",
        ai_prompt_instruction: "",
        ai_prompt: "",
        banned_words_tr: "",
        category: "PersonalGrowth",
        category_label: "Kişisel Gelişim",
        age_group: "3-10",
        display_order: nextOrder,
        is_active: true,
      });
    }
    setIsEditorOpen(true);
  };

  const closeEditor = () => {
    setIsEditorOpen(false);
    setEditingOutcome(null);
    form.reset();
  };

  const onSubmit = async (data: OutcomeFormData) => {
    try {
      const payload = {
        ...data,
        icon_url: data.icon_url || null,
        color_theme: data.color_theme || null,
        ai_prompt_instruction: data.ai_prompt_instruction || null,
        ai_prompt: data.ai_prompt || null,
        banned_words_tr: data.banned_words_tr || null,
        category_label:
          data.category_label || CATEGORIES.find((c) => c.id === data.category)?.label || null,
      };

      const url = editingOutcome
        ? `${API_BASE_URL}/admin/learning-outcomes/${editingOutcome.id}`
        : `${API_BASE_URL}/admin/learning-outcomes`;

      const response = await fetch(url, {
        method: editingOutcome ? "PATCH" : "POST",
        headers: getAuthHeaders(),
        body: JSON.stringify(payload),
      });

      if (response.ok) {
        toast({
          title: "Başarılı",
          description: editingOutcome ? "Kazanım güncellendi" : "Kazanım oluşturuldu",
        });
        closeEditor();
        fetchOutcomes();
      } else {
        const error = await response.json();
        throw new Error(error.detail || "Hata oluştu");
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : "Bilinmeyen hata";
      toast({ title: "Hata", description: message, variant: "destructive" });
    }
  };

  const handleDelete = async (outcomeId: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/admin/learning-outcomes/${outcomeId}`, {
        method: "DELETE",
        headers: getAuthHeaders(),
      });

      if (response.ok) {
        toast({ title: "Başarılı", description: "Kazanım devre dışı bırakıldı" });
        fetchOutcomes();
      }
    } catch (error) {
      toast({ title: "Hata", description: "Silme başarısız", variant: "destructive" });
    } finally {
      setDeleteConfirm(null);
    }
  };

  const handleDuplicate = async (outcomeId: string) => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/admin/learning-outcomes/${outcomeId}/duplicate`,
        { method: "POST", headers: getAuthHeaders() }
      );

      if (response.ok) {
        toast({ title: "Başarılı", description: "Kazanım kopyalandı" });
        fetchOutcomes();
      }
    } catch (error) {
      toast({ title: "Hata", description: "Kopyalama başarısız", variant: "destructive" });
    }
  };

  const toggleActive = async (outcome: LearningOutcome) => {
    try {
      const response = await fetch(`${API_BASE_URL}/admin/learning-outcomes/${outcome.id}`, {
        method: "PATCH",
        headers: getAuthHeaders(),
        body: JSON.stringify({ is_active: !outcome.is_active }),
      });

      if (response.ok) {
        toast({ title: "Başarılı", description: "Durum güncellendi" });
        fetchOutcomes();
      }
    } catch (error) {
      toast({ title: "Hata", description: "Güncelleme başarısız", variant: "destructive" });
    }
  };

  // Filter outcomes
  const filteredOutcomes = outcomes.filter((o) => {
    if (activeFilter === "all") return true;
    if (activeFilter === "active") return o.is_active;
    if (activeFilter === "inactive") return !o.is_active;
    return o.category === activeFilter;
  });

  // Group by category for display
  const groupedOutcomes = filteredOutcomes.reduce(
    (acc, outcome) => {
      const cat = outcome.category;
      if (!acc[cat]) acc[cat] = [];
      acc[cat].push(outcome);
      return acc;
    },
    {} as Record<string, LearningOutcome[]>
  );

  // Preview data for form
  const previewData: Partial<LearningOutcome> = {
    name: watchedValues.name,
    description: watchedValues.description,
    icon_url: watchedValues.icon_url,
    color_theme: watchedValues.color_theme,
    category: watchedValues.category,
    category_label: watchedValues.category_label,
    ai_prompt_instruction: watchedValues.ai_prompt_instruction,
    is_active: watchedValues.is_active,
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header */}
      <header className="sticky top-0 z-40 border-b bg-white shadow-sm">
        <div className="mx-auto flex max-w-[1600px] items-center justify-between px-6 py-4">
          <div>
            <h1 className="flex items-center gap-2 text-2xl font-bold text-gray-900">
              <Target className="h-6 w-6 text-purple-600" />
              Kazanım Yönetimi
            </h1>
            <p className="mt-0.5 text-sm text-gray-500">
              Hikaye eğitim kazanımlarını ve AI talimatlarını yönetin
            </p>
          </div>
          <Button onClick={() => openEditor()} className="bg-purple-600 hover:bg-purple-700">
            <Plus className="mr-2 h-4 w-4" />
            Yeni Kazanım
          </Button>
        </div>
      </header>

      <main className="mx-auto max-w-[1600px] px-6 py-8">
        {/* Stats & Filters */}
        <div className="mb-8 flex flex-wrap items-center gap-4">
          <div className="flex items-center gap-2 text-sm">
            <span className="text-gray-500">Toplam:</span>
            <Badge variant="secondary">{outcomes.length}</Badge>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <span className="text-gray-500">Aktif:</span>
            <Badge className="bg-green-100 text-green-700">
              {outcomes.filter((o) => o.is_active).length}
            </Badge>
          </div>

          <Separator orientation="vertical" className="h-6" />

          {/* Category filters */}
          <div className="flex flex-wrap gap-2">
            <Button
              variant={activeFilter === "all" ? "default" : "outline"}
              size="sm"
              onClick={() => setActiveFilter("all")}
            >
              Tümü
            </Button>
            {CATEGORIES.map((cat) => {
              const Icon = cat.icon;
              const count = outcomes.filter((o) => o.category === cat.id).length;
              return (
                <Button
                  key={cat.id}
                  variant={activeFilter === cat.id ? "default" : "outline"}
                  size="sm"
                  onClick={() => setActiveFilter(cat.id)}
                  className="gap-1"
                >
                  <Icon className="h-3 w-3" />
                  {cat.label}
                  <span className="text-xs opacity-70">({count})</span>
                </Button>
              );
            })}
          </div>
        </div>

        {/* Sync Status Panel */}
        {syncStatus &&
          (syncStatus.orphan_prompts > 0 || syncStatus.outcomes_without_prompt > 0) && (
            <Card className="mb-6 border-amber-200 bg-amber-50">
              <CardContent className="py-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="flex h-10 w-10 items-center justify-center rounded-full bg-amber-100">
                      <Link2 className="h-5 w-5 text-amber-600" />
                    </div>
                    <div>
                      <h3 className="font-medium text-amber-800">Senkronizasyon Gerekli</h3>
                      <p className="text-sm text-amber-600">
                        {syncStatus.orphan_prompts > 0 && (
                          <span className="mr-3">⚠️ {syncStatus.orphan_prompts} yetim prompt</span>
                        )}
                        {syncStatus.outcomes_without_prompt > 0 && (
                          <span>
                            ⚠️ {syncStatus.outcomes_without_prompt} kazanımın promptu eksik
                          </span>
                        )}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => router.push("/admin/prompts")}
                    >
                      <ExternalLink className="mr-1 h-4 w-4" />
                      Promptları Gör
                    </Button>
                    <Button
                      size="sm"
                      onClick={executeSync}
                      disabled={syncing}
                      className="bg-amber-600 hover:bg-amber-700"
                    >
                      {syncing ? (
                        <>
                          <RotateCw className="mr-1 h-4 w-4 animate-spin" />
                          Senkronize Ediliyor...
                        </>
                      ) : (
                        <>
                          <RefreshCw className="mr-1 h-4 w-4" />
                          Senkronize Et
                        </>
                      )}
                    </Button>
                  </div>
                </div>
                {syncStatus.orphan_prompts > 0 && (
                  <div className="mt-3 border-t border-amber-200 pt-3">
                    <p className="mb-2 text-xs text-amber-700">Silinecek yetim promptlar:</p>
                    <div className="flex flex-wrap gap-1">
                      {syncStatus.orphan_prompt_list.map((p) => (
                        <code
                          key={p.id}
                          className="rounded bg-amber-100 px-1.5 py-0.5 text-xs text-amber-800"
                        >
                          {p.key}
                        </code>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

        {/* Outcomes Grid */}
        {loading ? (
          <div className="py-12 text-center">
            <RotateCw className="mx-auto mb-4 h-8 w-8 animate-spin text-purple-600" />
            <p className="text-gray-500">Yükleniyor...</p>
          </div>
        ) : outcomes.length === 0 ? (
          <Card className="border-2 border-dashed">
            <CardContent className="py-16 text-center">
              <Target className="mx-auto mb-4 h-16 w-16 text-gray-300" />
              <h3 className="mb-2 text-xl font-semibold text-gray-700">Henüz kazanım yok</h3>
              <p className="mb-6 text-gray-500">İlk eğitim kazanımınızı oluşturun</p>
              <Button onClick={() => openEditor()} className="bg-purple-600 hover:bg-purple-700">
                <Plus className="mr-2 h-4 w-4" />
                İlk Kazanımı Oluştur
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-8">
            {Object.entries(groupedOutcomes).map(([category, items]) => {
              const cat = CATEGORIES.find((c) => c.id === category);
              const Icon = cat?.icon || Sparkles;

              return (
                <div key={category}>
                  {/* Category Header */}
                  <div className="mb-4 flex items-center gap-3">
                    <div
                      className="flex h-10 w-10 items-center justify-center rounded-xl"
                      style={{ backgroundColor: `${cat?.color || "#8B5CF6"}20` }}
                    >
                      <Icon className="h-5 w-5" style={{ color: cat?.color || "#8B5CF6" }} />
                    </div>
                    <div>
                      <h2 className="font-semibold text-gray-900">{cat?.label || category}</h2>
                      <p className="text-sm text-gray-500">{items.length} kazanım</p>
                    </div>
                  </div>

                  {/* Items Grid */}
                  <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
                    {items
                      .sort((a, b) => a.display_order - b.display_order)
                      .map((outcome) => {
                        const color = outcome.color_theme || cat?.color || "#8B5CF6";

                        return (
                          <Card
                            key={outcome.id}
                            className={`group overflow-hidden transition-all hover:shadow-lg ${
                              !outcome.is_active ? "opacity-60" : ""
                            }`}
                          >
                            <CardContent className="p-4">
                              {/* Header */}
                              <div className="mb-3 flex items-start gap-3">
                                <div
                                  className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg"
                                  style={{ backgroundColor: `${color}20` }}
                                >
                                  {outcome.icon_url ? (
                                    <img src={outcome.icon_url} alt="" className="h-6 w-6" />
                                  ) : (
                                    <Icon className="h-5 w-5" style={{ color }} />
                                  )}
                                </div>
                                <div className="min-w-0 flex-1">
                                  <h3 className="truncate font-medium text-gray-900">
                                    {outcome.name}
                                  </h3>
                                  <p className="line-clamp-1 text-xs text-gray-500">
                                    {outcome.description || "Açıklama yok"}
                                  </p>
                                </div>
                              </div>

                              {/* AI Instruction indicator with link to prompt */}
                              <div className="mb-3 flex items-center gap-1 text-xs text-purple-600">
                                <Brain className="h-3 w-3" />
                                <button
                                  onClick={() =>
                                    router.push(
                                      `/admin/prompts?highlight=${getPromptKeyFromName(outcome.name)}`
                                    )
                                  }
                                  className="flex items-center gap-1 truncate hover:underline"
                                >
                                  {outcome.effective_ai_instruction
                                    ? "AI talimatı tanımlı"
                                    : "Prompt düzenle"}
                                  <ExternalLink className="h-3 w-3" />
                                </button>
                              </div>

                              {/* Meta */}
                              <div className="mb-3 flex items-center gap-2 text-xs text-gray-400">
                                <span className="flex items-center gap-1">
                                  <GripVertical className="h-3 w-3" />#{outcome.display_order}
                                </span>
                                <span>•</span>
                                <span>{outcome.age_group} yaş</span>
                                {!outcome.is_active && (
                                  <>
                                    <span>•</span>
                                    <span className="text-amber-600">Pasif</span>
                                  </>
                                )}
                              </div>

                              {/* Actions */}
                              <div className="flex items-center gap-2">
                                <Button
                                  size="sm"
                                  variant="outline"
                                  className="flex-1 text-xs"
                                  onClick={() => openEditor(outcome)}
                                >
                                  <Pencil className="mr-1 h-3 w-3" />
                                  Düzenle
                                </Button>
                                <Button
                                  size="sm"
                                  variant="ghost"
                                  onClick={() => handleDuplicate(outcome.id)}
                                >
                                  <Copy className="h-3 w-3" />
                                </Button>
                                <Button
                                  size="sm"
                                  variant="ghost"
                                  onClick={() => toggleActive(outcome)}
                                >
                                  {outcome.is_active ? (
                                    <EyeOff className="h-3 w-3" />
                                  ) : (
                                    <Eye className="h-3 w-3" />
                                  )}
                                </Button>
                                <Button
                                  size="sm"
                                  variant="ghost"
                                  className="text-red-500 hover:bg-red-50 hover:text-red-700"
                                  onClick={() => setDeleteConfirm(outcome.id)}
                                >
                                  <Trash2 className="h-3 w-3" />
                                </Button>
                              </div>
                            </CardContent>
                          </Card>
                        );
                      })}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </main>

      {/* Delete Confirmation */}
      <AnimatePresence>
        {deleteConfirm && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4"
            onClick={() => setDeleteConfirm(null)}
          >
            <div className="absolute inset-0 bg-black/50" />
            <motion.div
              initial={{ scale: 0.95 }}
              animate={{ scale: 1 }}
              exit={{ scale: 0.95 }}
              onClick={(e) => e.stopPropagation()}
              className="relative w-full max-w-sm rounded-2xl bg-white p-6 shadow-2xl"
            >
              <div className="text-center">
                <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-red-100">
                  <AlertCircle className="h-6 w-6 text-red-600" />
                </div>
                <h3 className="mb-2 text-lg font-semibold">Kazanımı Devre Dışı Bırak</h3>
                <p className="mb-6 text-sm text-gray-500">
                  Bu kazanım pasif duruma alınacak ve müşterilere gösterilmeyecek. Emin misiniz?
                </p>
                <div className="flex gap-3">
                  <Button
                    variant="outline"
                    className="flex-1"
                    onClick={() => setDeleteConfirm(null)}
                  >
                    İptal
                  </Button>
                  <Button
                    variant="destructive"
                    className="flex-1"
                    onClick={() => handleDelete(deleteConfirm)}
                  >
                    Devre Dışı Bırak
                  </Button>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Editor Sheet */}
      <Sheet open={isEditorOpen} onOpenChange={setIsEditorOpen}>
        <SheetContent className="w-full overflow-y-auto sm:max-w-2xl">
          <SheetHeader className="mb-6">
            <SheetTitle className="flex items-center gap-2">
              <Settings2 className="h-5 w-5 text-purple-600" />
              {editingOutcome ? "Kazanımı Düzenle" : "Yeni Kazanım Oluştur"}
            </SheetTitle>
            <SheetDescription>
              Eğitim kazanımı, görsel tema ve AI hikaye talimatını yapılandırın
            </SheetDescription>
          </SheetHeader>

          <div className="grid gap-6 lg:grid-cols-3">
            {/* Form */}
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6 lg:col-span-2">
              {/* Basic Info */}
              <div className="space-y-4">
                <div className="flex items-center gap-2 text-sm font-medium text-gray-700">
                  <FileText className="h-4 w-4 text-purple-600" />
                  Temel Bilgiler
                </div>

                <div>
                  <Label>Kazanım Adı *</Label>
                  <Input
                    {...form.register("name")}
                    placeholder="Örn: Doğa Sevgisi"
                    className="mt-1"
                  />
                  {form.formState.errors.name && (
                    <p className="mt-1 text-xs text-red-500">
                      {form.formState.errors.name.message}
                    </p>
                  )}
                </div>

                <div>
                  <Label>Açıklama</Label>
                  <Textarea
                    {...form.register("description")}
                    placeholder="Kazanım hakkında kısa açıklama"
                    rows={2}
                    className="mt-1"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Kategori *</Label>
                    <Controller
                      control={form.control}
                      name="category"
                      render={({ field }) => (
                        <Select
                          value={field.value}
                          onValueChange={(val) => {
                            field.onChange(val);
                            const cat = CATEGORIES.find((c) => c.id === val);
                            if (cat) {
                              form.setValue("category_label", cat.label);
                              if (!form.getValues("color_theme")) {
                                form.setValue("color_theme", cat.color);
                              }
                            }
                          }}
                        >
                          <SelectTrigger className="mt-1">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {CATEGORIES.map((cat) => {
                              const Icon = cat.icon;
                              return (
                                <SelectItem key={cat.id} value={cat.id}>
                                  <div className="flex items-center gap-2">
                                    <Icon className="h-4 w-4" style={{ color: cat.color }} />
                                    {cat.label}
                                  </div>
                                </SelectItem>
                              );
                            })}
                          </SelectContent>
                        </Select>
                      )}
                    />
                  </div>
                  <div>
                    <Label>Yaş Grubu</Label>
                    <Controller
                      control={form.control}
                      name="age_group"
                      render={({ field }) => (
                        <Select value={field.value} onValueChange={field.onChange}>
                          <SelectTrigger className="mt-1">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="3-6">3-6 yaş</SelectItem>
                            <SelectItem value="3-10">3-10 yaş</SelectItem>
                            <SelectItem value="6-10">6-10 yaş</SelectItem>
                            <SelectItem value="7-12">7-12 yaş</SelectItem>
                          </SelectContent>
                        </Select>
                      )}
                    />
                  </div>
                </div>
              </div>

              <Separator />

              {/* Visual Theme */}
              <div className="space-y-4">
                <div className="flex items-center gap-2 text-sm font-medium text-gray-700">
                  <Palette className="h-4 w-4 text-purple-600" />
                  Görsel Tema
                </div>

                <div>
                  <Label>İkon URL</Label>
                  <Input
                    {...form.register("icon_url")}
                    placeholder="https://... (SVG/PNG)"
                    className="mt-1"
                  />
                  <p className="mt-1 text-xs text-gray-500">
                    Boş bırakılırsa kategori ikonu kullanılır
                  </p>
                </div>

                <div>
                  <Label>Renk Teması</Label>
                  <div className="mt-2">
                    <Controller
                      control={form.control}
                      name="color_theme"
                      render={({ field }) => (
                        <ColorPicker value={field.value || ""} onChange={field.onChange} />
                      )}
                    />
                  </div>
                </div>
              </div>

              <Separator />

              {/* AI Instructions */}
              <div className="space-y-4">
                <div className="flex items-center gap-2 text-sm font-medium text-gray-700">
                  <Brain className="h-4 w-4 text-purple-600" />
                  AI Hikaye Talimatı
                </div>

                <div>
                  <Label>AI Prompt Talimatı (Önerilen)</Label>
                  <Textarea
                    {...form.register("ai_prompt_instruction")}
                    placeholder="Hikayenin bir noktasında {child_name} zor durumda olan bir hayvana rastlasın. Onu iyileştirmek için oyununu bıraksın ve doğayla bağ kursun."
                    rows={4}
                    className="mt-1 font-mono text-sm"
                  />
                  <p className="mt-1 text-xs text-gray-500">
                    <code className="rounded bg-gray-100 px-1">{"{child_name}"}</code> değişkenini
                    kullanarak çocuğun adını ekleyebilirsiniz
                  </p>
                </div>

                <div>
                  <Label>Eski AI Prompt (Legacy)</Label>
                  <Input
                    {...form.register("ai_prompt")}
                    placeholder="Opsiyonel - geriye uyumluluk için"
                    className="mt-1"
                  />
                </div>

                <div>
                  <Label>Yasaklı Kelimeler (TR) — V2</Label>
                  <p className="mb-1 mt-0.5 text-xs text-gray-500">
                    Hikayede kullanılmaması gereken kelimeler (virgülle ayırın)
                  </p>
                  <Input
                    {...form.register("banned_words_tr")}
                    placeholder="Örn: şiddet, kavga, silah"
                    className="mt-1"
                  />
                </div>
              </div>

              <Separator />

              {/* Display Settings */}
              <div className="space-y-4">
                <div className="flex items-center gap-2 text-sm font-medium text-gray-700">
                  <Settings2 className="h-4 w-4 text-purple-600" />
                  Görünüm Ayarları
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Sıralama</Label>
                    <Controller
                      control={form.control}
                      name="display_order"
                      render={({ field }) => (
                        <Input
                          type="number"
                          {...field}
                          onChange={(e) => field.onChange(Number(e.target.value))}
                          className="mt-1"
                        />
                      )}
                    />
                  </div>
                  <div className="flex items-center justify-between rounded-lg border p-3">
                    <Label>Aktif</Label>
                    <Controller
                      control={form.control}
                      name="is_active"
                      render={({ field }) => (
                        <Switch checked={field.value} onCheckedChange={field.onChange} />
                      )}
                    />
                  </div>
                </div>
              </div>

              {/* Submit */}
              <div className="sticky bottom-0 -mx-6 -mb-6 flex gap-3 border-t bg-white p-4">
                <Button type="button" variant="outline" className="flex-1" onClick={closeEditor}>
                  İptal
                </Button>
                <Button
                  type="submit"
                  className="flex-1 bg-purple-600 hover:bg-purple-700"
                  disabled={form.formState.isSubmitting}
                >
                  {form.formState.isSubmitting ? (
                    <>
                      <RotateCw className="mr-2 h-4 w-4 animate-spin" />
                      Kaydediliyor...
                    </>
                  ) : (
                    <>
                      <CheckCircle2 className="mr-2 h-4 w-4" />
                      {editingOutcome ? "Güncelle" : "Oluştur"}
                    </>
                  )}
                </Button>
              </div>
            </form>

            {/* Preview */}
            <div className="space-y-4">
              <div className="flex items-center gap-2 text-sm font-medium text-gray-700">
                <Eye className="h-4 w-4 text-purple-600" />
                Önizleme
              </div>
              <OutcomeCardPreview outcome={previewData} />
            </div>
          </div>
        </SheetContent>
      </Sheet>
    </div>
  );
}
