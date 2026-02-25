"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { useToast } from "@/hooks/use-toast";
import { ArrowLeft, Save, Plus, Eye } from "lucide-react";
import Link from "next/link";
import { API_BASE_URL } from "@/lib/api";

interface BackCoverConfig {
  id: string;
  name: string;
  company_name: string;
  company_logo_url: string | null;
  company_website: string;
  company_email: string;
  company_phone: string | null;
  company_address: string | null;
  background_color: string;
  primary_color: string;
  text_color: string;
  qr_enabled: boolean;
  qr_size_mm: number;
  qr_position: string;
  qr_label: string;
  tips_title: string;
  tips_content: string;
  tips_font_size: number;
  tagline: string;
  copyright_text: string;
  show_stars: boolean;
  show_border: boolean;
  border_color: string;
  is_active: boolean;
  is_default: boolean;
}

const defaultConfig: Omit<BackCoverConfig, "id"> = {
  name: "Varsayilan Arka Kapak",
  company_name: "Benim Masalım",
  company_logo_url: null,
  company_website: "www.benimmasalim.com.tr",
  company_email: "info@benimmasalim.com.tr",
  company_phone: null,
  company_address: null,
  background_color: "#F8F4F0",
  primary_color: "#6B46C1",
  text_color: "#333333",
  qr_enabled: true,
  qr_size_mm: 30,
  qr_position: "bottom_right",
  qr_label: "Sesli Kitabı Dinle",
  tips_title: "Ebeveynlere Öneriler",
  tips_content: `• Çocuğunuzla birlikte okuyun, soru sorun
• Her gün düzenli okuma alışkanlığı oluşturun
• Hikayedeki karakterleri birlikte canlandırın
• Çocuğunuzun hayal gücünü destekleyin
• Okuma sonrası hikayeyi birlikte çizin`,
  tips_font_size: 10,
  tagline: "Her çocuk kendi masalının kahramanı!",
  copyright_text: "© 2024 Benim Masalım. Tüm hakları saklıdır.",
  show_stars: true,
  show_border: true,
  border_color: "#E0D4F7",
  is_active: true,
  is_default: true,
};

export default function BackCoverAdminPage() {
  const [configs, setConfigs] = useState<BackCoverConfig[]>([]);
  const [selectedConfig, setSelectedConfig] = useState<BackCoverConfig | null>(null);
  const [formData, setFormData] = useState<Omit<BackCoverConfig, "id">>(defaultConfig);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const { toast } = useToast();

  useEffect(() => {
    // Check auth
    const token = localStorage.getItem("token");
    if (!token) {
      window.location.href = "/auth/login";
      return;
    }
    fetchConfigs();
  }, []);

  const fetchConfigs = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`${API_BASE_URL}/admin/back-cover?include_inactive=true`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        setConfigs(data);
        if (data.length > 0) {
          setSelectedConfig(data[0]);
          setFormData(data[0]);
        } else {
          // Ilk yapilandirmayi otomatik olustur
          await createDefaultConfig(token);
        }
      } else if (response.status === 401) {
        window.location.href = "/auth/login";
      }
    } catch (error) {
      toast({ title: "Hata", description: "Yapılandırmalar yüklenemedi", variant: "destructive" });
    } finally {
      setLoading(false);
    }
  };

  const createDefaultConfig = async (token: string | null) => {
    try {
      const response = await fetch(`${API_BASE_URL}/admin/back-cover`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(defaultConfig),
      });
      if (response.ok) {
        const newConfig = await response.json();
        setConfigs([newConfig]);
        setSelectedConfig(newConfig);
        setFormData(newConfig);
        toast({ title: "Başarılı", description: "Varsayılan yapılandırma oluşturuldu" });
      }
    } catch (error) {
      console.error("Failed to create default config", error);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const token = localStorage.getItem("token");
      const url = selectedConfig
        ? `${API_BASE_URL}/admin/back-cover/${selectedConfig.id}`
        : `${API_BASE_URL}/admin/back-cover`;

      const response = await fetch(url, {
        method: selectedConfig ? "PATCH" : "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(formData),
      });

      if (response.ok) {
        toast({ title: "Başarılı", description: "Arka kapak yapılandırması kaydedildi" });
        fetchConfigs();
      } else {
        toast({ title: "Hata", description: "Kaydetme başarısız", variant: "destructive" });
      }
    } catch (error) {
      toast({
        title: "Hata",
        description: "Kaydetme sırasında hata oluştu",
        variant: "destructive",
      });
    } finally {
      setSaving(false);
    }
  };

  const handleNewConfig = () => {
    setSelectedConfig(null);
    setFormData({ ...defaultConfig, name: `Arka Kapak ${configs.length + 1}`, is_default: false });
  };

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
              <h1 className="text-2xl font-bold">Arka Kapak Yönetimi</h1>
              <p className="text-gray-500">Kitap arka kapak tasarımını yapılandırın</p>
            </div>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={handleNewConfig}>
              <Plus className="mr-2 h-4 w-4" />
              Yeni Yapilandirma
            </Button>
            <Button onClick={handleSave} disabled={saving}>
              <Save className="mr-2 h-4 w-4" />
              {saving ? "Kaydediliyor..." : "Kaydet"}
            </Button>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          {/* Left: Config List */}
          <div className="lg:col-span-1">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Yapilandirmalar</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {configs.length === 0 && !loading && (
                  <p className="text-sm text-gray-500">Henuz yapilandirma yok</p>
                )}
                {configs.map((config) => (
                  <button
                    key={config.id}
                    onClick={() => {
                      setSelectedConfig(config);
                      setFormData(config);
                    }}
                    className={`w-full rounded-lg border p-3 text-left transition ${
                      selectedConfig?.id === config.id
                        ? "border-purple-500 bg-purple-50"
                        : "border-gray-200 hover:border-purple-300"
                    }`}
                  >
                    <div className="font-medium">{config.name}</div>
                    <div className="text-xs text-gray-500">
                      {config.is_default && (
                        <span className="mr-2 text-purple-600">Varsayilan</span>
                      )}
                      {!config.is_active && <span className="text-red-500">Pasif</span>}
                    </div>
                  </button>
                ))}
              </CardContent>
            </Card>
          </div>

          {/* Right: Edit Form */}
          <div className="space-y-6 lg:col-span-2">
            {/* Basic Info */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Temel Bilgiler</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Yapilandirma Adi</Label>
                    <Input
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    />
                  </div>
                  <div className="flex items-center gap-4 pt-6">
                    <div className="flex items-center gap-2">
                      <Switch
                        checked={formData.is_default}
                        onCheckedChange={(checked) =>
                          setFormData({ ...formData, is_default: checked })
                        }
                      />
                      <Label>Varsayilan</Label>
                    </div>
                    <div className="flex items-center gap-2">
                      <Switch
                        checked={formData.is_active}
                        onCheckedChange={(checked) =>
                          setFormData({ ...formData, is_active: checked })
                        }
                      />
                      <Label>Aktif</Label>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Company Info */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Firma Bilgileri</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Firma Adi</Label>
                    <Input
                      value={formData.company_name}
                      onChange={(e) => setFormData({ ...formData, company_name: e.target.value })}
                    />
                  </div>
                  <div>
                    <Label>Website</Label>
                    <Input
                      value={formData.company_website}
                      onChange={(e) =>
                        setFormData({ ...formData, company_website: e.target.value })
                      }
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>E-posta</Label>
                    <Input
                      value={formData.company_email}
                      onChange={(e) => setFormData({ ...formData, company_email: e.target.value })}
                    />
                  </div>
                  <div>
                    <Label>Telefon</Label>
                    <Input
                      value={formData.company_phone || ""}
                      onChange={(e) =>
                        setFormData({ ...formData, company_phone: e.target.value || null })
                      }
                    />
                  </div>
                </div>
                <div>
                  <Label>Slogan</Label>
                  <Input
                    value={formData.tagline}
                    onChange={(e) => setFormData({ ...formData, tagline: e.target.value })}
                  />
                </div>
                <div>
                  <Label>Telif Hakki Metni</Label>
                  <Input
                    value={formData.copyright_text}
                    onChange={(e) => setFormData({ ...formData, copyright_text: e.target.value })}
                  />
                </div>
              </CardContent>
            </Card>

            {/* Parent Tips */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Ebeveyn Onerileri</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label>Baslik</Label>
                  <Input
                    value={formData.tips_title}
                    onChange={(e) => setFormData({ ...formData, tips_title: e.target.value })}
                  />
                </div>
                <div>
                  <Label>Icerik (her satir bir oneri)</Label>
                  <Textarea
                    value={formData.tips_content}
                    onChange={(e) => setFormData({ ...formData, tips_content: e.target.value })}
                    rows={6}
                  />
                </div>
                <div className="w-32">
                  <Label>Font Boyutu</Label>
                  <Input
                    type="number"
                    value={formData.tips_font_size}
                    onChange={(e) =>
                      setFormData({ ...formData, tips_font_size: parseInt(e.target.value) || 10 })
                    }
                  />
                </div>
              </CardContent>
            </Card>

            {/* QR Code Settings */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">QR Kod Ayarları</CardTitle>
                <CardDescription>Sesli kitap için QR kod ayarları</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center gap-2">
                  <Switch
                    checked={formData.qr_enabled}
                    onCheckedChange={(checked) => setFormData({ ...formData, qr_enabled: checked })}
                  />
                  <Label>QR Kod Göster</Label>
                </div>
                {formData.qr_enabled && (
                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <Label>Boyut (mm)</Label>
                      <Input
                        type="number"
                        value={formData.qr_size_mm}
                        onChange={(e) =>
                          setFormData({ ...formData, qr_size_mm: parseFloat(e.target.value) || 30 })
                        }
                      />
                    </div>
                    <div>
                      <Label>Konum</Label>
                      <select
                        value={formData.qr_position}
                        onChange={(e) => setFormData({ ...formData, qr_position: e.target.value })}
                        className="h-10 w-full rounded-md border px-3"
                      >
                        <option value="bottom_right">Sag Alt</option>
                        <option value="bottom_left">Sol Alt</option>
                        <option value="center">Orta</option>
                      </select>
                    </div>
                    <div>
                      <Label>Etiket</Label>
                      <Input
                        value={formData.qr_label}
                        onChange={(e) => setFormData({ ...formData, qr_label: e.target.value })}
                      />
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Colors */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Renkler ve Stil</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-4 gap-4">
                  <div>
                    <Label>Arka Plan</Label>
                    <div className="flex gap-2">
                      <Input
                        type="color"
                        value={formData.background_color}
                        onChange={(e) =>
                          setFormData({ ...formData, background_color: e.target.value })
                        }
                        className="h-10 w-12 p-1"
                      />
                      <Input
                        value={formData.background_color}
                        onChange={(e) =>
                          setFormData({ ...formData, background_color: e.target.value })
                        }
                        className="flex-1"
                      />
                    </div>
                  </div>
                  <div>
                    <Label>Ana Renk</Label>
                    <div className="flex gap-2">
                      <Input
                        type="color"
                        value={formData.primary_color}
                        onChange={(e) =>
                          setFormData({ ...formData, primary_color: e.target.value })
                        }
                        className="h-10 w-12 p-1"
                      />
                      <Input
                        value={formData.primary_color}
                        onChange={(e) =>
                          setFormData({ ...formData, primary_color: e.target.value })
                        }
                        className="flex-1"
                      />
                    </div>
                  </div>
                  <div>
                    <Label>Metin Rengi</Label>
                    <div className="flex gap-2">
                      <Input
                        type="color"
                        value={formData.text_color}
                        onChange={(e) => setFormData({ ...formData, text_color: e.target.value })}
                        className="h-10 w-12 p-1"
                      />
                      <Input
                        value={formData.text_color}
                        onChange={(e) => setFormData({ ...formData, text_color: e.target.value })}
                        className="flex-1"
                      />
                    </div>
                  </div>
                  <div>
                    <Label>Cerceve Rengi</Label>
                    <div className="flex gap-2">
                      <Input
                        type="color"
                        value={formData.border_color}
                        onChange={(e) => setFormData({ ...formData, border_color: e.target.value })}
                        className="h-10 w-12 p-1"
                      />
                      <Input
                        value={formData.border_color}
                        onChange={(e) => setFormData({ ...formData, border_color: e.target.value })}
                        className="flex-1"
                      />
                    </div>
                  </div>
                </div>
                <div className="flex gap-4">
                  <div className="flex items-center gap-2">
                    <Switch
                      checked={formData.show_border}
                      onCheckedChange={(checked) =>
                        setFormData({ ...formData, show_border: checked })
                      }
                    />
                    <Label>Cerceve Goster</Label>
                  </div>
                  <div className="flex items-center gap-2">
                    <Switch
                      checked={formData.show_stars}
                      onCheckedChange={(checked) =>
                        setFormData({ ...formData, show_stars: checked })
                      }
                    />
                    <Label>Yildizlar Goster</Label>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Preview */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-lg">
                  <Eye className="h-5 w-5" />
                  Onizleme
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div
                  className="mx-auto aspect-[3/4] max-w-md overflow-hidden rounded-lg shadow-lg"
                  style={{ backgroundColor: formData.background_color }}
                >
                  {/* Preview content */}
                  <div
                    className="flex h-full flex-col p-6"
                    style={{
                      border: formData.show_border ? `2px solid ${formData.border_color}` : "none",
                      margin: "8px",
                      borderRadius: "8px",
                    }}
                  >
                    {/* Top: Company */}
                    <div className="mb-4 text-center">
                      <h2 style={{ color: formData.primary_color }} className="text-lg font-bold">
                        {formData.company_name}
                      </h2>
                      <p style={{ color: formData.text_color }} className="text-sm italic">
                        {formData.tagline}
                      </p>
                    </div>

                    <hr style={{ borderColor: formData.primary_color }} className="mb-4" />

                    {/* Middle: Tips */}
                    <div className="flex-1">
                      <h3
                        style={{ color: formData.primary_color }}
                        className="mb-2 text-center font-semibold"
                      >
                        {formData.tips_title}
                      </h3>
                      <div
                        style={{
                          color: formData.text_color,
                          fontSize: `${formData.tips_font_size}px`,
                        }}
                      >
                        {formData.tips_content.split("\n").map((line, i) => (
                          <p key={i} className="mb-1">
                            {line}
                          </p>
                        ))}
                      </div>
                    </div>

                    {/* Bottom: QR and Info */}
                    <div className="mt-4">
                      {formData.qr_enabled && (
                        <div
                          className={`flex ${formData.qr_position === "center" ? "justify-center" : formData.qr_position === "bottom_left" ? "justify-start" : "justify-end"} mb-2`}
                        >
                          <div className="rounded bg-white p-2 text-center">
                            <div className="flex h-16 w-16 items-center justify-center bg-gray-200 text-xs">
                              QR
                            </div>
                            <p style={{ color: formData.primary_color }} className="mt-1 text-xs">
                              {formData.qr_label}
                            </p>
                          </div>
                        </div>
                      )}
                      <div className="text-center" style={{ color: formData.text_color }}>
                        <p className="text-xs">{formData.company_website}</p>
                        <p className="text-xs">{formData.company_email}</p>
                      </div>
                      <p className="mt-2 text-center text-xs" style={{ color: "#888" }}>
                        {formData.copyright_text}
                      </p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
