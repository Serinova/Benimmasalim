"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAdminAuth } from "@/hooks/use-admin-auth";
import { motion, AnimatePresence } from "framer-motion";
import {
  Plus,
  Pencil,
  Trash2,
  CheckCircle2,
  AlertCircle,
  RotateCw,
  Wand2,
  FileText,
  Code,
  Copy,
  RefreshCw,
  BookOpen,
  Palette,
  Target,
  Image,
  ExternalLink,
  Link2,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useToast } from "@/hooks/use-toast";
import { API_BASE_URL } from "@/lib/api";
import { getAdminHeaders as getAuthHeaders } from "@/lib/adminFetch";

// ============ TYPES ============
interface PromptTemplate {
  id: string;
  key: string;
  name: string;
  category: string;
  description: string | null;
  content: string;
  content_en: string | null;
  version: number;
  is_active: boolean;
  modified_by: string | null;
  created_at: string | null;
  updated_at: string | null;
}

const CATEGORY_CONFIG: Record<
  string,
  { label: string; icon: React.ReactNode; color: string }
> = {
  story_system: {
    label: "Hikaye Sistemi",
    icon: <BookOpen className="h-4 w-4" />,
    color: "purple",
  },
  visual_template: {
    label: "Görsel Şablon",
    icon: <Palette className="h-4 w-4" />,
    color: "blue",
  },
  negative_prompt: {
    label: "Negatif Prompt",
    // eslint-disable-next-line jsx-a11y/alt-text
    icon: <Image className="h-4 w-4" aria-hidden />,
    color: "red",
  },
  educational: {
    label: "Eğitsel Değerler",
    icon: <Target className="h-4 w-4" />,
    color: "green",
  },
};

export default function AdminPromptsPage() {
  const [prompts, setPrompts] = useState<PromptTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [isEditorOpen, setIsEditorOpen] = useState(false);
  const [editingPrompt, setEditingPrompt] = useState<PromptTemplate | null>(
    null
  );
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [cacheStats, setCacheStats] = useState<{
    total: number;
    active: number;
  } | null>(null);

  const [formData, setFormData] = useState({
    key: "",
    name: "",
    category: "story_system",
    description: "",
    content: "",
    content_en: "",
  });

  const router = useRouter();
  const { toast } = useToast();

  useAdminAuth();

  useEffect(() => {
    fetchPrompts();
    fetchCacheStats();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);


  const fetchPrompts = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/admin/prompts`, {
        headers: getAuthHeaders(),
      });
      if (response.status === 401) {
        router.push("/auth/login");
        return;
      }
      if (response.ok) {
        const data = await response.json();
        setPrompts(data.prompts || []);
      }
    } catch {
      toast({
        title: "Hata",
        description: "Promptlar yüklenemedi",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const fetchCacheStats = async () => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/admin/prompts/cache-stats`,
        { headers: getAuthHeaders() }
      );
      if (response.ok) {
        const data = await response.json();
        setCacheStats(data);
      }
    } catch {
      // ignore
    }
  };

  const clearCache = async () => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/admin/prompts/clear-cache`,
        { method: "POST", headers: getAuthHeaders() }
      );
      if (response.ok) {
        toast({ title: "Başarılı", description: "Cache temizlendi" });
        fetchCacheStats();
      }
    } catch {
      toast({
        title: "Hata",
        description: "Cache temizlenemedi",
        variant: "destructive",
      });
    }
  };

  const openEditor = (prompt?: PromptTemplate) => {
    if (prompt) {
      setEditingPrompt(prompt);
      setFormData({
        key: prompt.key,
        name: prompt.name,
        category: prompt.category,
        description: prompt.description || "",
        content: prompt.content,
        content_en: prompt.content_en || "",
      });
    } else {
      setEditingPrompt(null);
      setFormData({
        key: "",
        name: "",
        category: "story_system",
        description: "",
        content: "",
        content_en: "",
      });
    }
    setIsEditorOpen(true);
  };

  const closeEditor = () => {
    setIsEditorOpen(false);
    setEditingPrompt(null);
    setFormData({
      key: "",
      name: "",
      category: "story_system",
      description: "",
      content: "",
      content_en: "",
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const url = editingPrompt
        ? `${API_BASE_URL}/admin/prompts/${editingPrompt.key}`
        : `${API_BASE_URL}/admin/prompts`;

      const payload = editingPrompt
        ? {
            name: formData.name,
            description: formData.description,
            content: formData.content,
            content_en: formData.content_en || null,
          }
        : { ...formData, content_en: formData.content_en || null };

      const response = await fetch(url, {
        method: editingPrompt ? "PUT" : "POST",
        headers: getAuthHeaders(),
        body: JSON.stringify(payload),
      });

      if (response.ok) {
        toast({
          title: "Başarılı",
          description: editingPrompt ? "Prompt güncellendi" : "Prompt oluşturuldu",
        });
        closeEditor();
        fetchPrompts();
        await clearCache();
      } else {
        const error = await response.json();
        throw new Error(error.detail || "Hata oluştu");
      }
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Bilinmeyen hata";
      toast({ title: "Hata", description: message, variant: "destructive" });
    }
  };

  const handleDelete = async (key: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/admin/prompts/${key}`, {
        method: "DELETE",
        headers: getAuthHeaders(),
      });
      if (response.ok) {
        toast({ title: "Başarılı", description: "Prompt deaktif edildi" });
        fetchPrompts();
      }
    } catch {
      toast({
        title: "Hata",
        description: "Silme başarısız",
        variant: "destructive",
      });
    } finally {
      setDeleteConfirm(null);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast({ title: "Kopyalandı", description: "Prompt panoya kopyalandı" });
  };

  const filteredPrompts = selectedCategory
    ? prompts.filter((p) => p.category === selectedCategory)
    : prompts;

  const groupedPrompts = filteredPrompts.reduce(
    (acc, prompt) => {
      if (!acc[prompt.category]) acc[prompt.category] = [];
      acc[prompt.category].push(prompt);
      return acc;
    },
    {} as Record<string, PromptTemplate[]>
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="flex items-center gap-2 text-2xl font-bold text-gray-900">
            <Wand2 className="h-6 w-6 text-purple-600" />
            AI Prompt Şablonları
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            Hikaye ve görsel üretimi için AI prompt şablonlarını yönetin
          </p>
        </div>
        <div className="flex items-center gap-2">
          {cacheStats && (
            <div className="mr-4 text-xs text-gray-500">
              Cache: {cacheStats.active}/{cacheStats.total}
            </div>
          )}
          <Button variant="outline" size="sm" onClick={clearCache}>
            <RefreshCw className="mr-1 h-4 w-4" />
            Cache Temizle
          </Button>
          <Button
            onClick={() => openEditor()}
            className="bg-purple-600 hover:bg-purple-700"
          >
            <Plus className="mr-2 h-4 w-4" />
            Yeni Prompt
          </Button>
        </div>
      </div>

      {/* Category Filter */}
      <div className="flex flex-wrap gap-2">
        <Button
          variant={selectedCategory === null ? "default" : "outline"}
          size="sm"
          onClick={() => setSelectedCategory(null)}
        >
          Tümü ({prompts.length})
        </Button>
        {Object.entries(CATEGORY_CONFIG).map(([key, config]) => {
          const count = prompts.filter((p) => p.category === key).length;
          if (count === 0) return null;
          return (
            <Button
              key={key}
              variant={selectedCategory === key ? "default" : "outline"}
              size="sm"
              onClick={() => setSelectedCategory(key)}
              className={
                selectedCategory === key ? `bg-${config.color}-600` : ""
              }
            >
              {config.icon}
              <span className="ml-1">{config.label}</span>
              <Badge variant="secondary" className="ml-2 text-xs">
                {count}
              </Badge>
            </Button>
          );
        })}
      </div>

      {/* Prompts Grid */}
      {loading ? (
        <div className="py-12 text-center">
          <RotateCw className="mx-auto mb-4 h-8 w-8 animate-spin text-purple-600" />
          <p className="text-gray-500">Yükleniyor...</p>
        </div>
      ) : Object.keys(groupedPrompts).length === 0 ? (
        <Card className="border-2 border-dashed">
          <CardContent className="py-16 text-center">
            <Wand2 className="mx-auto mb-4 h-16 w-16 text-gray-300" />
            <h3 className="mb-2 text-xl font-semibold text-gray-700">
              Henüz prompt yok
            </h3>
            <p className="mb-6 text-gray-500">
              Yeni prompt oluşturmak için aşağıdaki butonu kullanın
            </p>
            <Button
              onClick={() => openEditor()}
              className="bg-purple-600 hover:bg-purple-700"
            >
              <Plus className="mr-2 h-4 w-4" />
              İlk Promptu Oluştur
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-8">
          {Object.entries(groupedPrompts).map(([category, categoryPrompts]) => {
            const config = CATEGORY_CONFIG[category] || {
              label: category,
              icon: <FileText className="h-4 w-4" />,
              color: "gray",
            };
            return (
              <div key={category}>
                <div className="mb-4 flex items-center gap-2">
                  <div
                    className={`flex h-8 w-8 items-center justify-center rounded-lg bg-${config.color}-100`}
                  >
                    {config.icon}
                  </div>
                  <h2 className="text-lg font-semibold text-gray-800">
                    {config.label}
                  </h2>
                  <Badge variant="secondary">{categoryPrompts.length}</Badge>
                </div>

                <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
                  {categoryPrompts.map((prompt) => (
                    <Card
                      key={prompt.id}
                      className={`group transition-all hover:shadow-lg ${
                        !prompt.is_active ? "opacity-60" : ""
                      }`}
                    >
                      <CardHeader className="pb-2">
                        <div className="flex items-start justify-between">
                          <div className="min-w-0 flex-1">
                            <CardTitle className="truncate text-base">
                              {prompt.name}
                            </CardTitle>
                            <code className="mt-1 inline-block rounded bg-purple-50 px-1.5 py-0.5 text-xs text-purple-600">
                              {prompt.key}
                            </code>
                          </div>
                          <div className="flex items-center gap-1 opacity-0 transition-opacity group-hover:opacity-100">
                            <Button
                              size="sm"
                              variant="ghost"
                              className="h-8 w-8 p-0"
                              onClick={() => copyToClipboard(prompt.content)}
                            >
                              <Copy className="h-3.5 w-3.5" />
                            </Button>
                            <Button
                              size="sm"
                              variant="ghost"
                              className="h-8 w-8 p-0"
                              onClick={() => openEditor(prompt)}
                            >
                              <Pencil className="h-3.5 w-3.5" />
                            </Button>
                          </div>
                        </div>
                      </CardHeader>
                      <CardContent>
                        <p className="mb-3 line-clamp-2 text-xs text-gray-500">
                          {prompt.description || "Açıklama yok"}
                        </p>
                        <pre className="max-h-24 overflow-hidden whitespace-pre-wrap rounded border bg-gray-50 p-2 text-xs text-gray-600">
                          {prompt.content.substring(0, 200)}
                          {prompt.content.length > 200 && "..."}
                        </pre>
                        {prompt.content_en && (
                          <div className="mt-2">
                            <Badge
                              variant="outline"
                              className="mb-1 text-[10px]"
                            >
                              EN Template
                            </Badge>
                            <pre className="max-h-16 overflow-hidden whitespace-pre-wrap rounded border bg-blue-50 p-2 text-xs text-blue-700">
                              {prompt.content_en.substring(0, 120)}
                              {prompt.content_en.length > 120 && "..."}
                            </pre>
                          </div>
                        )}
                        {prompt.category === "educational" &&
                          prompt.key.startsWith("EDUCATIONAL_") && (
                            <button
                              onClick={() =>
                                router.push("/admin/learning-outcomes")
                              }
                              className="mb-3 flex items-center gap-1 text-xs text-green-600 hover:text-green-700 hover:underline"
                            >
                              <Link2 className="h-3 w-3" />
                              <span>Kazanım Kartını Düzenle</span>
                              <ExternalLink className="h-3 w-3" />
                            </button>
                          )}
                        <div className="mt-3 flex items-center justify-between border-t pt-3">
                          <div className="flex items-center gap-2">
                            <Badge variant="outline" className="text-xs">
                              v{prompt.version}
                            </Badge>
                            {!prompt.is_active && (
                              <Badge variant="secondary" className="text-xs">
                                Pasif
                              </Badge>
                            )}
                          </div>
                          <div className="flex items-center gap-1">
                            <Button
                              size="sm"
                              variant="outline"
                              className="h-7 text-xs"
                              onClick={() => openEditor(prompt)}
                            >
                              <Pencil className="mr-1 h-3 w-3" />
                              Düzenle
                            </Button>
                            <Button
                              size="sm"
                              variant="ghost"
                              className="h-7 w-7 p-0 text-red-500 hover:bg-red-50 hover:text-red-700"
                              onClick={() => setDeleteConfirm(prompt.key)}
                            >
                              <Trash2 className="h-3 w-3" />
                            </Button>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}

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
                <h3 className="mb-2 text-lg font-semibold">
                  Promptu Deaktif Et
                </h3>
                <p className="mb-6 text-sm text-gray-500">
                  Bu prompt pasif duruma alınacak. Sistem hardcoded fallback
                  kullanacak.
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
                    Deaktif Et
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
              <Code className="h-5 w-5 text-purple-600" />
              {editingPrompt ? "Promptu Düzenle" : "Yeni Prompt Oluştur"}
            </SheetTitle>
            <SheetDescription>
              AI sistemlerinin kullanacağı prompt şablonunu düzenleyin
            </SheetDescription>
          </SheetHeader>

          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Anahtar (Key) *</Label>
                  <Input
                    value={formData.key}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        key: e.target.value.toUpperCase().replace(/\s+/g, "_"),
                      })
                    }
                    placeholder="PURE_AUTHOR_SYSTEM"
                    className="mt-1 font-mono"
                    disabled={!!editingPrompt}
                  />
                  <p className="mt-1 text-xs text-gray-400">
                    Sistemde kullanılacak benzersiz anahtar
                  </p>
                </div>
                <div>
                  <Label>Kategori *</Label>
                  <select
                    value={formData.category}
                    onChange={(e) =>
                      setFormData({ ...formData, category: e.target.value })
                    }
                    className="mt-1 h-9 w-full rounded-md border border-input bg-background px-3 text-sm"
                    disabled={!!editingPrompt}
                  >
                    {Object.entries(CATEGORY_CONFIG).map(([key, config]) => (
                      <option key={key} value={key}>
                        {config.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <Label>İsim *</Label>
                <Input
                  value={formData.name}
                  onChange={(e) =>
                    setFormData({ ...formData, name: e.target.value })
                  }
                  placeholder="Hikaye Yazarı Sistem Promptu"
                  className="mt-1"
                />
              </div>

              <div>
                <Label>Açıklama</Label>
                <Input
                  value={formData.description}
                  onChange={(e) =>
                    setFormData({ ...formData, description: e.target.value })
                  }
                  placeholder="Bu prompt ne için kullanılıyor?"
                  className="mt-1"
                />
              </div>
            </div>

            <Separator />

            {/* Content (TR) */}
            <div>
              <Label>Prompt İçeriği (TR) *</Label>
              <Textarea
                name="content"
                value={formData.content}
                onChange={(e) =>
                  setFormData({ ...formData, content: e.target.value })
                }
                placeholder="AI prompt şablonunu buraya yazın..."
                rows={12}
                className="mt-1 font-mono text-sm"
              />
              <div className="mt-1 flex justify-between">
                <p className="text-xs text-gray-400">
                  {formData.content.length} karakter
                </p>
                {editingPrompt && (
                  <p className="text-xs text-gray-400">
                    Versiyon: {editingPrompt.version} →{" "}
                    {editingPrompt.version + 1}
                  </p>
                )}
              </div>
            </div>

            {/* Content EN */}
            <div>
              <Label>İngilizce Şablon (EN)</Label>
              <p className="mb-1 mt-0.5 text-xs text-gray-500">
                Görsel prompt template&apos;leri için kullanılır. Yer tutucular:{" "}
                {"{scene_description}"}, {"{clothing_description}"}
              </p>
              <Textarea
                value={formData.content_en}
                onChange={(e) =>
                  setFormData({ ...formData, content_en: e.target.value })
                }
                placeholder="Örn: A young child wearing {clothing_description}. {scene_description}."
                rows={6}
                className="mt-1 font-mono text-sm"
              />
              <p className="mt-1 text-xs text-gray-400">
                {formData.content_en.length} karakter
              </p>
            </div>

            {/* Submit */}
            <div className="sticky bottom-0 -mx-6 -mb-6 flex gap-3 border-t bg-white p-4">
              <Button
                type="button"
                variant="outline"
                className="flex-1"
                onClick={closeEditor}
              >
                İptal
              </Button>
              <Button
                type="submit"
                className="flex-1 bg-purple-600 hover:bg-purple-700"
                disabled={
                  !formData.key || !formData.name || !formData.content
                }
              >
                <CheckCircle2 className="mr-2 h-4 w-4" />
                {editingPrompt ? "Güncelle" : "Oluştur"}
              </Button>
            </div>
          </form>
        </SheetContent>
      </Sheet>
    </div>
  );
}
