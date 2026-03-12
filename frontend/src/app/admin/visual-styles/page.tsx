"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAdminAuth } from "@/hooks/use-admin-auth";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { useToast } from "@/hooks/use-toast";
import { Edit, Trash2, Palette, Plus, Code } from "lucide-react";
import { API_BASE_URL } from "@/lib/api";
import { getAdminHeaders as getAuthHeaders } from "@/lib/adminFetch";

interface VisualStyle {
  id: string;
  name: string;
  display_name: string | null;
  thumbnail_url: string;
  prompt_modifier: string;
  is_active: boolean;
}

export default function AdminVisualStylesPage() {
  const [styles, setStyles] = useState<VisualStyle[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingStyle, setEditingStyle] = useState<VisualStyle | null>(null);
  const [saving, setSaving] = useState(false);

  const [formData, setFormData] = useState({
    name: "",
    display_name: "",
    thumbnail_url: "/img/default-style.jpg",
    thumbnail_base64: "",
    prompt_modifier: "",
    is_active: true,
  });
  const [imagePreview, setImagePreview] = useState<string | null>(null);

  const router = useRouter();
  const { toast } = useToast();

  useAdminAuth();

  useEffect(() => {
    fetchStyles();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

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
        toast({
          title: "Oturum süresi doldu veya yetkisizsiniz",
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
        toast({ title: "Hata", description: `Sunucu hatası: ${response.status}`, variant: "destructive" });
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
      prompt_modifier: style.prompt_modifier || "",
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
    if (!name) {
      toast({ title: "Hata", description: "Stil adı gerekli", variant: "destructive" });
      return;
    }
    setSaving(true);

    try {
      const payload: Record<string, unknown> = {
        name,
        display_name: formData.display_name?.trim() || null,
        is_active: formData.is_active,
      };

      // prompt_modifier is only accepted on Creation, not on update.
      if (!editingStyle) {
        payload.prompt_modifier = formData.prompt_modifier.trim();
      }

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
      const detail = typeof data?.detail === "string" ? data.detail : "Hata oluştu";

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
      } else {
        toast({ title: "Hata", description: "Silme başarısız", variant: "destructive" });
      }
    } catch (error) {
      toast({ title: "Hata", description: "Silme başarısız", variant: "destructive" });
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
          <div>
            <h1 className="text-2xl font-bold">Çizim Tarzları</h1>
            <p className="text-gray-600">
              Uygulamada gösterilecek çizim tarzlarının görsellerini ve isimlerini yönetin.
              Stillerin gelişmiş ayarları ve AI promptları artık kod (<code>style_config.py</code>) üzerinden yönetilmektedir.
            </p>
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
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3 lg:grid-cols-4">
          {styles.length === 0 ? (
            <Card className="col-span-full">
              <CardContent className="p-8 text-center text-gray-500">
                Henüz çizim tarzı eklenmemiş
              </CardContent>
            </Card>
          ) : (
            styles.map((style) => (
              <Card key={style.id} className={!style.is_active ? "opacity-50" : ""}>
                <CardContent className="p-4 flex flex-col h-full">
                  <div className="mb-3 aspect-square overflow-hidden rounded-lg bg-gray-100 flex-shrink-0">
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

                  <div className="space-y-2 flex-grow">
                    <div className="flex items-start justify-between">
                      <div>
                        <h3 className="font-semibold">{style.display_name || style.name}</h3>
                        <p className="text-xs text-gray-500 font-mono flex items-center gap-1 mt-1">
                          <Code className="h-3 w-3" />
                          {style.name}
                        </p>
                      </div>
                      {!style.is_active && (
                        <span className="rounded bg-gray-200 px-2 py-0.5 text-xs text-gray-600">
                          Pasif
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-2 pt-4 mt-auto">
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
                      className="text-red-600 hover:text-red-700 hover:bg-red-50"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </div>

        {/* Form Modal */}
        {showForm && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
            <Card className="max-h-[90vh] w-full max-w-lg overflow-y-auto">
              <CardHeader>
                <CardTitle>
                  {editingStyle ? "Çizim Tarzını Düzenle" : "Yeni Çizim Tarzı Oluştur"}
                </CardTitle>
                <CardDescription>
                  Görsel stili form bilgilerini girin. Artık karmaşık parametreler yok!
                </CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleSubmit} className="space-y-5">
                  <div className="space-y-2">
                    <Label>Tarz Gösterim Adı</Label>
                    <Input
                      value={formData.display_name}
                      onChange={(e) => setFormData({ ...formData, display_name: e.target.value })}
                      placeholder="Örn: 3D Süper Kahraman"
                    />
                    <p className="text-xs text-gray-500">Kullanıcının sitede göreceği isimdir.</p>
                  </div>

                  <div className="space-y-2">
                    <Label>Dahili Stil Kodu (İsim) *</Label>
                    <Input
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      placeholder="Örn: superhero_3d"
                      required
                      disabled={!!editingStyle}
                    />
                    <p className="text-xs text-gray-500">
                      Geliştirici anahtarıdır. URL&apos;lerde ve kod içinde kimlik olarak kullanılır.
                    </p>
                  </div>

                  {/* Sadece Yeni Oluşturma sırasında Match Keyword istenebilir, gerçi style_config'de biz name ile eşliyoruz, ama yine de isteyebiliriz */}
                  {!editingStyle && (
                    <div className="space-y-2">
                      <Label>Kod Eşleşme Anahtarı (prompt_modifier)</Label>
                      <Input
                        value={formData.prompt_modifier}
                        onChange={(e) => setFormData({ ...formData, prompt_modifier: e.target.value })}
                        placeholder="Örn: 3D superhero style"
                      />
                      <p className="text-xs text-gray-500">
                        style_config.py&apos;deki stili bulmak için kullanılan anahtar metindir.
                      </p>
                    </div>
                  )}

                  <div className="space-y-2">
                    <Label>Vitrin Görseli</Label>
                    <div className="flex items-center gap-4">
                      <div className="h-24 w-24 flex-shrink-0 overflow-hidden rounded-lg border bg-gray-100">
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
                          className="cursor-pointer text-sm"
                        />
                        <p className="mt-2 text-xs text-gray-500">PNG, JPG (max 2MB)</p>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center justify-between rounded-lg border p-4 bg-gray-50/50">
                    <div>
                      <Label className="text-base font-medium text-gray-800">Aktif Mi?</Label>
                      <p className="text-sm text-gray-500">Kullanıcılar bu tarzı seçebilsin mi?</p>
                    </div>
                    <Switch
                      checked={formData.is_active}
                      onCheckedChange={(val) => setFormData({ ...formData, is_active: val })}
                    />
                  </div>

                  <div className="flex gap-3 pt-4">
                    <Button type="submit" className="flex-1" disabled={saving}>
                      {saving ? "Kaydediliyor..." : "Kaydet"}
                    </Button>
                    <Button
                      type="button"
                      variant="outline"
                      className="flex-1"
                      onClick={() => {
                        setShowForm(false);
                        resetForm();
                      }}
                      disabled={saving}
                    >
                      İptal
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
