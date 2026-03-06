"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { Slider } from "@/components/ui/slider";
import { useToast } from "@/hooks/use-toast";
import { ArrowLeft, Save, Plus, Eye, BookOpen, QrCode, Palette, Building2, Star } from "lucide-react";
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
  background_gradient_end: string;
  primary_color: string;
  accent_color: string;
  text_color: string;
  qr_enabled: boolean;
  qr_size_mm: number;
  qr_position: string;
  qr_label: string;
  tips_title: string;
  tips_content: string;
  tips_font_size: number;
  tagline: string;
  dedication_text: string;
  copyright_text: string;
  show_stars: boolean;
  show_border: boolean;
  border_color: string;
  show_decorative_lines: boolean;
  is_active: boolean;
  is_default: boolean;
}

const defaultConfig: Omit<BackCoverConfig, "id"> = {
  name: "Varsayılan İç Kapak Arkası",
  company_name: "Benim Masalım",
  company_logo_url: null,
  company_website: "www.benimmasalim.com.tr",
  company_email: "info@benimmasalim.com.tr",
  company_phone: null,
  company_address: null,
  background_color: "#FDF6EC",
  background_gradient_end: "#EDE4F8",
  primary_color: "#6B21A8",
  accent_color: "#F59E0B",
  text_color: "#2D1B4E",
  qr_enabled: true,
  qr_size_mm: 32,
  qr_position: "bottom_right",
  qr_label: "Sesli Kitabı Dinle",
  tips_title: "Sevgili Ebeveyn,",
  tips_content: `• Çocuğunuzla her gün düzenli okuma saati oluşturun
• Okurken soru sorun: "Sence ne olur?" diye merak uyandırın
• Hikayedeki karakterleri birlikte canlandırın ve sesler çıkarın
• Okuma sonrası çocuğunuzun hikayeyi kendi sözleriyle anlatmasını isteyin
• Kitaptaki yerleri ve konuları günlük hayatla ilişkilendirin
• Hayal gücünü desteklemek için birlikte resim çizin`,
  tips_font_size: 9,
  tagline: "Her çocuk kendi masalının kahramanıdır.",
  dedication_text: "Bu kitap, senin için; merakın, cesaretinle büyüyen ve hayal dünyasıyla sınırları zorlayan sen için...",
  copyright_text: `© ${new Date().getFullYear()} Benim Masalım. Tüm hakları saklıdır.`,
  show_stars: true,
  show_border: true,
  border_color: "#C4B5FD",
  show_decorative_lines: true,
  is_active: true,
  is_default: true,
};

// Canlı önizleme bileşeni
function BackCoverPreview({ config }: { config: Omit<BackCoverConfig, "id"> }) {
  return (
    <div
      className="relative mx-auto overflow-hidden shadow-2xl"
      style={{
        width: "280px",
        height: "396px", // A5 oranı (148x210mm)
        background: `linear-gradient(160deg, ${config.background_color} 0%, ${config.background_gradient_end} 100%)`,
        fontFamily: "'Georgia', serif",
      }}
    >
      {/* Dekoratif köşe süsü - üst sol */}
      <div
        className="absolute top-0 left-0 w-16 h-16 opacity-20"
        style={{
          background: `radial-gradient(circle at top left, ${config.primary_color}, transparent)`,
        }}
      />
      {/* Dekoratif köşe süsü - alt sağ */}
      <div
        className="absolute bottom-0 right-0 w-20 h-20 opacity-15"
        style={{
          background: `radial-gradient(circle at bottom right, ${config.accent_color}, transparent)`,
        }}
      />

      {/* Çerçeve */}
      {config.show_border && (
        <div
          className="absolute inset-2 rounded pointer-events-none"
          style={{ border: `1.5px solid ${config.border_color}`, opacity: 0.7 }}
        />
      )}

      <div className="relative flex flex-col h-full px-5 py-4">
        {/* ÜST: Marka Bölgesi */}
        <div className="text-center mb-3">
          {config.show_stars && (
            <div className="flex justify-center gap-0.5 mb-1.5">
              {[...Array(5)].map((_, i) => (
                <svg key={i} className="w-3 h-3" viewBox="0 0 20 20" fill={config.accent_color}>
                  <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                </svg>
              ))}
            </div>
          )}
          <div
            className="text-base font-bold tracking-wide"
            style={{ color: config.primary_color, letterSpacing: "0.05em" }}
          >
            {config.company_name}
          </div>
          {config.show_decorative_lines && (
            <div className="flex items-center justify-center gap-2 mt-1.5">
              <div className="h-px w-10" style={{ background: config.accent_color, opacity: 0.6 }} />
              <div className="w-1 h-1 rounded-full" style={{ background: config.accent_color }} />
              <div className="h-px w-10" style={{ background: config.accent_color, opacity: 0.6 }} />
            </div>
          )}
          <p
            className="text-xs italic mt-1.5 leading-relaxed"
            style={{ color: config.text_color, opacity: 0.75 }}
          >
            {config.tagline}
          </p>
        </div>

        {/* İTHAF / KIŞİSEL METİN */}
        {config.dedication_text && (
          <div
            className="text-center px-2 py-2.5 mb-3 rounded"
            style={{
              background: `${config.primary_color}10`,
              borderLeft: `3px solid ${config.accent_color}`,
            }}
          >
            <p
              className="text-xs italic leading-relaxed"
              style={{ color: config.text_color, fontSize: "8px", lineHeight: "1.5" }}
            >
              {config.dedication_text}
            </p>
          </div>
        )}

        {/* ORTA: Ebeveyn Önerileri — sayfanın kalbi */}
        <div className="flex-1">
          <div
            className="text-xs font-bold mb-1.5 text-center tracking-wider uppercase"
            style={{ color: config.primary_color, fontSize: "8px", letterSpacing: "0.12em" }}
          >
            {config.tips_title}
          </div>
          <div className="space-y-0.5">
            {config.tips_content.split("\n").filter(Boolean).map((line, i) => (
              <p
                key={i}
                className="leading-snug"
                style={{
                  color: config.text_color,
                  fontSize: `${Math.min(config.tips_font_size, 8)}px`,
                  lineHeight: "1.45",
                }}
              >
                {line}
              </p>
            ))}
          </div>
        </div>

        {/* AYRAÇ */}
        {config.show_decorative_lines && (
          <div className="flex items-center gap-1.5 my-2">
            <div className="h-px flex-1" style={{ background: config.border_color }} />
            <div className="flex gap-0.5">
              {[...Array(3)].map((_, i) => (
                <div
                  key={i}
                  className="w-0.5 h-0.5 rounded-full"
                  style={{ background: config.accent_color, opacity: 0.7 }}
                />
              ))}
            </div>
            <div className="h-px flex-1" style={{ background: config.border_color }} />
          </div>
        )}

        {/* ALT: QR + İletişim */}
        <div className="flex items-end justify-between gap-2">
          {/* İletişim Bilgileri */}
          <div className="flex-1">
            <p
              className="font-semibold"
              style={{ color: config.primary_color, fontSize: "7px", letterSpacing: "0.04em" }}
            >
              {config.company_website}
            </p>
            <p style={{ color: config.text_color, fontSize: "6.5px", opacity: 0.7 }}>
              {config.company_email}
            </p>
            {config.company_phone && (
              <p style={{ color: config.text_color, fontSize: "6.5px", opacity: 0.7 }}>
                {config.company_phone}
              </p>
            )}
            <p className="mt-1.5" style={{ color: config.text_color, fontSize: "6px", opacity: 0.5 }}>
              {config.copyright_text}
            </p>
          </div>

          {/* QR Kodu */}
          {config.qr_enabled && (
            <div className="text-center shrink-0">
              <div
                className="flex items-center justify-center rounded"
                style={{
                  width: "44px",
                  height: "44px",
                  background: "white",
                  border: `1px solid ${config.border_color}`,
                  padding: "3px",
                }}
              >
                {/* QR grid simülasyonu */}
                <div className="grid grid-cols-5 gap-px w-full h-full">
                  {[...Array(25)].map((_, i) => (
                    <div
                      key={i}
                      className="rounded-sm"
                      style={{
                        background: [0,1,2,5,6,7,10,12,14,17,18,19,22,23,24].includes(i)
                          ? "#111"
                          : "transparent",
                      }}
                    />
                  ))}
                </div>
              </div>
              <p
                className="mt-0.5 text-center leading-tight"
                style={{ color: config.primary_color, fontSize: "6px" }}
              >
                {config.qr_label}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// Renk seçici satır bileşeni
function ColorRow({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <div>
      <Label className="mb-1 block text-xs text-gray-600">{label}</Label>
      <div className="flex items-center gap-2">
        <input
          type="color"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="h-9 w-9 cursor-pointer rounded border border-gray-200 p-0.5"
        />
        <Input
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="h-9 font-mono text-sm uppercase"
        />
      </div>
    </div>
  );
}

export default function BackCoverAdminPage() {
  const [configs, setConfigs] = useState<BackCoverConfig[]>([]);
  const [selectedConfig, setSelectedConfig] = useState<BackCoverConfig | null>(null);
  const [formData, setFormData] = useState<Omit<BackCoverConfig, "id">>(defaultConfig);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const { toast } = useToast();

  const upd = <K extends keyof Omit<BackCoverConfig, "id">>(
    key: K,
    value: Omit<BackCoverConfig, "id">[K]
  ) => setFormData((prev) => ({ ...prev, [key]: value }));

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) { window.location.href = "/auth/login"; return; }
    fetchConfigs();
  }, []);

  const fetchConfigs = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`${API_BASE_URL}/admin/back-cover?include_inactive=true`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setConfigs(data);
        if (data.length > 0) {
          setSelectedConfig(data[0]);
          setFormData(data[0]);
        } else {
          await createDefaultConfig(token);
        }
      } else if (res.status === 401) {
        window.location.href = "/auth/login";
      }
    } catch {
      toast({ title: "Hata", description: "Yapılandırmalar yüklenemedi", variant: "destructive" });
    } finally {
      setLoading(false);
    }
  };

  const createDefaultConfig = async (token: string | null) => {
    try {
      const res = await fetch(`${API_BASE_URL}/admin/back-cover`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify(defaultConfig),
      });
      if (res.ok) {
        const newCfg = await res.json();
        setConfigs([newCfg]);
        setSelectedConfig(newCfg);
        setFormData(newCfg);
        toast({ title: "Başarılı", description: "Varsayılan yapılandırma oluşturuldu" });
      }
    } catch { /* ignore */ }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const token = localStorage.getItem("token");
      const url = selectedConfig
        ? `${API_BASE_URL}/admin/back-cover/${selectedConfig.id}`
        : `${API_BASE_URL}/admin/back-cover`;
      const res = await fetch(url, {
        method: selectedConfig ? "PATCH" : "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify(formData),
      });
      if (res.ok) {
        toast({ title: "Kaydedildi", description: "İç kapak arkası yapılandırması güncellendi." });
        fetchConfigs();
      } else {
        toast({ title: "Hata", description: "Kaydetme başarısız", variant: "destructive" });
      }
    } catch {
      toast({ title: "Hata", description: "Bağlantı hatası", variant: "destructive" });
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="mx-auto max-w-7xl">

        {/* Header */}
        <div className="mb-6 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/admin">
              <Button variant="ghost" size="icon">
                <ArrowLeft className="h-5 w-5" />
              </Button>
            </Link>
            <div>
              <h1 className="text-2xl font-bold">İç Kapak Arkası Yönetimi</h1>
              <p className="text-gray-500 text-sm">
                Kitabın ilk sayfasının arkası — marka kimliği, ebeveyn rehberi ve QR kodu
              </p>
            </div>
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              onClick={() => {
                setSelectedConfig(null);
                setFormData({ ...defaultConfig, name: `Yapılandırma ${configs.length + 1}`, is_default: false });
              }}
            >
              <Plus className="mr-2 h-4 w-4" />
              Yeni
            </Button>
            <Button onClick={handleSave} disabled={saving} className="bg-purple-700 hover:bg-purple-800">
              <Save className="mr-2 h-4 w-4" />
              {saving ? "Kaydediliyor..." : "Kaydet"}
            </Button>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-6 xl:grid-cols-4">

          {/* Sol: Yapılandırma listesi */}
          <div className="xl:col-span-1">
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-semibold text-gray-700">Yapılandırmalar</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 pt-0">
                {loading && <p className="text-xs text-gray-400">Yükleniyor…</p>}
                {!loading && configs.length === 0 && (
                  <p className="text-xs text-gray-400">Henüz yapılandırma yok.</p>
                )}
                {configs.map((cfg) => (
                  <button
                    key={cfg.id}
                    onClick={() => { setSelectedConfig(cfg); setFormData(cfg); }}
                    className={`w-full rounded-lg border p-3 text-left text-sm transition ${
                      selectedConfig?.id === cfg.id
                        ? "border-purple-500 bg-purple-50 font-medium"
                        : "border-gray-200 hover:border-purple-300"
                    }`}
                  >
                    <div className="font-medium">{cfg.name}</div>
                    <div className="flex gap-2 mt-0.5">
                      {cfg.is_default && (
                        <span className="text-xs text-purple-600 font-medium">Varsayılan</span>
                      )}
                      {!cfg.is_active && (
                        <span className="text-xs text-red-400">Pasif</span>
                      )}
                    </div>
                  </button>
                ))}
              </CardContent>
            </Card>

            {/* Canlı önizleme */}
            <Card className="mt-4">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-semibold text-gray-700 flex items-center gap-2">
                  <Eye className="h-4 w-4" />
                  Canlı Önizleme
                </CardTitle>
                <CardDescription className="text-xs">Gerçek sayfa oranlarında (A5)</CardDescription>
              </CardHeader>
              <CardContent className="flex justify-center pt-0 pb-4">
                <BackCoverPreview config={formData} />
              </CardContent>
            </Card>
          </div>

          {/* Sağ: Düzenleme formu */}
          <div className="space-y-5 xl:col-span-3">

            {/* Temel ayarlar */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center gap-2">
                  <BookOpen className="h-4 w-4 text-purple-600" />
                  Temel Bilgiler
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <Label>Yapılandırma Adı</Label>
                    <Input value={formData.name} onChange={(e) => upd("name", e.target.value)} />
                  </div>
                  <div className="flex items-center gap-6 pt-6">
                    <label className="flex items-center gap-2 cursor-pointer">
                      <Switch
                        checked={formData.is_default}
                        onCheckedChange={(v) => upd("is_default", v)}
                      />
                      <span className="text-sm">Varsayılan</span>
                    </label>
                    <label className="flex items-center gap-2 cursor-pointer">
                      <Switch
                        checked={formData.is_active}
                        onCheckedChange={(v) => upd("is_active", v)}
                      />
                      <span className="text-sm">Aktif</span>
                    </label>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Marka & Firma */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center gap-2">
                  <Building2 className="h-4 w-4 text-purple-600" />
                  Marka & Firma Bilgileri
                </CardTitle>
                <CardDescription className="text-xs">Sayfa üstünde görünür — okuyucunun gözüne çarpan ilk bilgi</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Firma / Marka Adı</Label>
                    <Input value={formData.company_name} onChange={(e) => upd("company_name", e.target.value)} />
                  </div>
                  <div>
                    <Label>Slogan <span className="text-gray-400 text-xs">(kapak altı italik metin)</span></Label>
                    <Input value={formData.tagline} onChange={(e) => upd("tagline", e.target.value)} />
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <Label>Website</Label>
                    <Input value={formData.company_website} onChange={(e) => upd("company_website", e.target.value)} />
                  </div>
                  <div>
                    <Label>E-posta</Label>
                    <Input value={formData.company_email} onChange={(e) => upd("company_email", e.target.value)} />
                  </div>
                  <div>
                    <Label>Telefon <span className="text-gray-400 text-xs">(isteğe bağlı)</span></Label>
                    <Input
                      value={formData.company_phone || ""}
                      onChange={(e) => upd("company_phone", e.target.value || null)}
                      placeholder="+90 …"
                    />
                  </div>
                </div>
                <div>
                  <Label>İthaf / Kişisel Mesaj <span className="text-gray-400 text-xs">(italik kutu — boş bırakılabilir)</span></Label>
                  <Textarea
                    value={formData.dedication_text}
                    onChange={(e) => upd("dedication_text", e.target.value)}
                    rows={2}
                    placeholder="Bu kitap, senin için…"
                  />
                </div>
                <div>
                  <Label>Telif Hakkı Metni</Label>
                  <Input value={formData.copyright_text} onChange={(e) => upd("copyright_text", e.target.value)} />
                </div>
              </CardContent>
            </Card>

            {/* Ebeveyn Önerileri */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center gap-2">
                  <Star className="h-4 w-4 text-purple-600" />
                  Ebeveyn Önerileri <span className="text-xs font-normal text-gray-400">(Okuma Rehberi)</span>
                </CardTitle>
                <CardDescription className="text-xs">
                  Sayfanın en geniş alanı — ebeveyne çocukla kitap okuma kılavuzu
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label>Bölüm Başlığı</Label>
                  <Input value={formData.tips_title} onChange={(e) => upd("tips_title", e.target.value)} />
                </div>
                <div>
                  <Label>Öneriler <span className="text-gray-400 text-xs">(her satır ayrı öneri — • ile başlayın)</span></Label>
                  <Textarea
                    value={formData.tips_content}
                    onChange={(e) => upd("tips_content", e.target.value)}
                    rows={8}
                    className="font-mono text-sm"
                  />
                </div>
                <div className="flex items-center gap-4">
                  <div className="flex-1">
                    <Label className="mb-2 block">
                      Yazı Boyutu — <span className="text-purple-700 font-semibold">{formData.tips_font_size}pt</span>
                      <span className="text-gray-400 text-xs ml-2">(önerilen: 8–10pt)</span>
                    </Label>
                    <Slider
                      min={7}
                      max={13}
                      step={0.5}
                      value={[formData.tips_font_size]}
                      onValueChange={([v]) => upd("tips_font_size", v)}
                      className="w-full"
                    />
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* QR Kodu */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center gap-2">
                  <QrCode className="h-4 w-4 text-purple-600" />
                  QR Kodu — Sesli Kitap
                </CardTitle>
                <CardDescription className="text-xs">
                  Alt sağda konumlanır; sesli kitabı dinlemek için telefonla okutulur
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <label className="flex items-center gap-3 cursor-pointer">
                  <Switch checked={formData.qr_enabled} onCheckedChange={(v) => upd("qr_enabled", v)} />
                  <span className="text-sm font-medium">QR Kodu Göster</span>
                </label>
                {formData.qr_enabled && (
                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <Label>Boyut (mm)</Label>
                      <Input
                        type="number"
                        min={20}
                        max={50}
                        value={formData.qr_size_mm}
                        onChange={(e) => upd("qr_size_mm", parseFloat(e.target.value) || 32)}
                      />
                    </div>
                    <div>
                      <Label>Konum</Label>
                      <select
                        value={formData.qr_position}
                        onChange={(e) => upd("qr_position", e.target.value)}
                        className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
                      >
                        <option value="bottom_right">Sağ Alt (önerilen)</option>
                        <option value="bottom_left">Sol Alt</option>
                        <option value="center">Orta</option>
                      </select>
                    </div>
                    <div>
                      <Label>Etiket</Label>
                      <Input
                        value={formData.qr_label}
                        onChange={(e) => upd("qr_label", e.target.value)}
                        placeholder="Sesli Kitabı Dinle"
                      />
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Renkler & Görsel Stil */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center gap-2">
                  <Palette className="h-4 w-4 text-purple-600" />
                  Renkler & Görsel Stil
                </CardTitle>
                <CardDescription className="text-xs">
                  Arka plan gradient, tipografi ve dekoratif öğe renkleri
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-5">
                <div className="grid grid-cols-2 gap-4 md:grid-cols-3">
                  <ColorRow
                    label="Arka Plan Başlangıç"
                    value={formData.background_color}
                    onChange={(v) => upd("background_color", v)}
                  />
                  <ColorRow
                    label="Arka Plan Bitiş (gradient)"
                    value={formData.background_gradient_end}
                    onChange={(v) => upd("background_gradient_end", v)}
                  />
                  <ColorRow
                    label="Ana Renk (başlık, QR etiketi)"
                    value={formData.primary_color}
                    onChange={(v) => upd("primary_color", v)}
                  />
                  <ColorRow
                    label="Vurgu Rengi (yıldız, ayraç)"
                    value={formData.accent_color}
                    onChange={(v) => upd("accent_color", v)}
                  />
                  <ColorRow
                    label="Metin Rengi"
                    value={formData.text_color}
                    onChange={(v) => upd("text_color", v)}
                  />
                  <ColorRow
                    label="Çerçeve Rengi"
                    value={formData.border_color}
                    onChange={(v) => upd("border_color", v)}
                  />
                </div>

                <div className="flex flex-wrap gap-6 pt-2">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <Switch checked={formData.show_border} onCheckedChange={(v) => upd("show_border", v)} />
                    <span className="text-sm">Çerçeve Göster</span>
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <Switch checked={formData.show_stars} onCheckedChange={(v) => upd("show_stars", v)} />
                    <span className="text-sm">Yıldızlar Göster</span>
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <Switch
                      checked={formData.show_decorative_lines}
                      onCheckedChange={(v) => upd("show_decorative_lines", v)}
                    />
                    <span className="text-sm">Dekoratif Çizgi & Ayraçlar</span>
                  </label>
                </div>
              </CardContent>
            </Card>

          </div>
        </div>
      </div>
    </div>
  );
}
