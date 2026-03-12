"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Switch } from "@/components/ui/switch";
import { useToast } from "@/hooks/use-toast";
import { API_BASE_URL } from "@/lib/api";
import { getAdminHeaders as getAuthHeaders } from "@/lib/adminFetch";
import { useAdminAuth } from "@/hooks/use-admin-auth";

// Türkçe ş/ğ/Ş/Ğ/İ render EDEMEYEN fontlar (mask_size test ile doğrulanmış)
const FONTS_NO_TURKISH = new Set([
  "Schoolbell", "Chewy", "Bubblegum Sans", "Satisfy", "Gaegu",
]);

// Font tanımları - çocuk kitapları için uygun fontlar
const AVAILABLE_FONTS = [
  // El Yazısı / Çocuk Dostu
  { value: "Nunito", label: "Nunito", category: "Sans-Serif", preview: "Merhaba Dünya! 123" },
  { value: "Quicksand", label: "Quicksand", category: "Sans-Serif", preview: "Merhaba Dünya! 123" },
  { value: "Comfortaa", label: "Comfortaa", category: "Sans-Serif", preview: "Merhaba Dünya! 123" },
  { value: "Baloo 2", label: "Baloo 2", category: "Yuvarlak", preview: "Merhaba Dünya! 123" },
  { value: "Bubblegum Sans", label: "Bubblegum Sans \u26a0\ufe0f", category: "E\u011flenceli", preview: "Merhaba D\u00fcnya! 123" },
  { value: "Comic Neue", label: "Comic Neue", category: "Komik", preview: "Merhaba Dünya! 123" },
  { value: "Patrick Hand", label: "Patrick Hand", category: "El Yazısı", preview: "Merhaba Dünya! 123" },
  { value: "Caveat", label: "Caveat", category: "El Yazısı", preview: "Merhaba Dünya! 123" },
  // Dekoratif / Başlık
  { value: "Lobster", label: "Lobster", category: "Dekoratif", preview: "Merhaba Dünya! 123" },
  { value: "Pacifico", label: "Pacifico", category: "El Yazısı", preview: "Merhaba Dünya! 123" },
  { value: "Fredoka One", label: "Fredoka One", category: "Kalın", preview: "Merhaba Dünya! 123" },
  { value: "Bangers", label: "Bangers", category: "Çizgi Roman", preview: "Merhaba Dünya! 123" },
  { value: "Chewy", label: "Chewy \u26a0\ufe0f", category: "E\u011flenceli", preview: "Merhaba D\u00fcnya! 123" },
  { value: "Luckiest Guy", label: "Luckiest Guy", category: "Kalın", preview: "Merhaba Dünya! 123" },
  // Klasik / Okunabilir
  { value: "Poppins", label: "Poppins", category: "Modern", preview: "Merhaba Dünya! 123" },
  { value: "Montserrat", label: "Montserrat", category: "Şık", preview: "Merhaba Dünya! 123" },
  { value: "Open Sans", label: "Open Sans", category: "Klasik", preview: "Merhaba Dünya! 123" },
  { value: "Roboto", label: "Roboto", category: "Temiz", preview: "Merhaba Dünya! 123" },
  // Yeni Eklenen — Çocuk Kitabı Fontları
  { value: "Indie Flower", label: "Indie Flower", category: "El Yazısı", preview: "Merhaba Dünya! 123" },
  { value: "Shadows Into Light", label: "Shadows Into Light", category: "El Yazısı", preview: "Merhaba Dünya! 123" },
  { value: "Pangolin", label: "Pangolin", category: "El Yazısı", preview: "Merhaba Dünya! 123" },
  { value: "Gaegu", label: "Gaegu \u26a0\ufe0f", category: "El Yaz\u0131s\u0131", preview: "Merhaba D\u00fcnya! 123" },
  { value: "Sniglet", label: "Sniglet", category: "Yuvarlak", preview: "Merhaba Dünya! 123" },
  { value: "Itim", label: "Itim", category: "El Yazısı", preview: "Merhaba Dünya! 123" },
  { value: "Schoolbell", label: "Schoolbell \u26a0\ufe0f", category: "El Yaz\u0131s\u0131", preview: "Merhaba D\u00fcnya! 123" },
  { value: "Gloria Hallelujah", label: "Gloria Hallelujah", category: "El Yazısı", preview: "Merhaba Dünya! 123" },
  { value: "Amatic SC", label: "Amatic SC", category: "Dekoratif", preview: "Merhaba Dünya! 123" },
  { value: "Satisfy", label: "Satisfy \u26a0\ufe0f", category: "El Yaz\u0131s\u0131", preview: "Merhaba D\u00fcnya! 123" },
  { value: "Righteous", label: "Righteous", category: "Retro", preview: "Merhaba Dünya! 123" },
  { value: "Architects Daughter", label: "Architects Daughter", category: "El Yazısı", preview: "Merhaba Dünya! 123" },
  // Hikaye / Masalsı Fontlar
  { value: "Kalam", label: "Kalam", category: "El Yazısı", preview: "Merhaba Dünya! 123" },
  { value: "Delius", label: "Delius", category: "El Yazısı", preview: "Merhaba Dünya! 123" },
  { value: "Handlee", label: "Handlee", category: "El Yazısı", preview: "Merhaba Dünya! 123" },
  { value: "Just Another Hand", label: "Just Another Hand", category: "El Yazısı", preview: "Merhaba Dünya! 123" },
  { value: "Reenie Beanie", label: "Reenie Beanie", category: "El Yazısı", preview: "Merhaba Dünya! 123" },
  { value: "Sue Ellen Francisco", label: "Sue Ellen Francisco", category: "El Yazısı", preview: "Merhaba Dünya! 123" },
  { value: "Short Stack", label: "Short Stack", category: "El Yazısı", preview: "Merhaba Dünya! 123" },
  { value: "Coming Soon", label: "Coming Soon", category: "El Yazısı", preview: "Merhaba Dünya! 123" },
  { value: "Covered By Your Grace", label: "Covered By Your Grace", category: "El Yazısı", preview: "Merhaba Dünya! 123" },
  { value: "Permanent Marker", label: "Permanent Marker", category: "Kalem", preview: "Merhaba Dünya! 123" },
  // Sistem Fontları
  { value: "Comic Sans MS", label: "Comic Sans MS", category: "Sistem", preview: "Merhaba Dünya! 123" },
  { value: "Arial", label: "Arial", category: "Sistem", preview: "Merhaba Dünya! 123" },
  { value: "Georgia", label: "Georgia", category: "Serif", preview: "Merhaba Dünya! 123" },
  { value: "Verdana", label: "Verdana", category: "Sistem", preview: "Merhaba Dünya! 123" },
];

// Google Fonts URL'ini oluştur
const googleFontsUrl = `https://fonts.googleapis.com/css2?family=${AVAILABLE_FONTS.filter(
  (f) => !["Comic Sans MS", "Arial", "Georgia", "Verdana"].includes(f.value)
)
  .map((f) => f.value.replace(/ /g, "+") + ":wght@300;400;500;600;700;800;900")
  .join("&family=")}&display=swap`;

interface PageTemplate {
  id?: string;
  name: string;
  page_type: string;
  updated_at?: string | null;
  // Physical dimensions
  page_width_mm: number;
  page_height_mm: number;
  bleed_mm: number;
  // Image settings
  image_width_percent: number;
  image_height_percent: number;
  image_x_percent: number;
  image_y_percent: number;
  image_aspect_ratio: string;
  // Text visibility - NEW: allows hiding text completely (e.g., for covers)
  text_enabled: boolean;
  // Text settings (only used if text_enabled=true)
  text_width_percent: number;
  text_height_percent: number;
  text_x_percent: number;
  text_y_percent: number;
  text_position: string;
  text_vertical_align: string;
  // Typography
  font_family: string;
  font_size_pt: number;
  line_height: number;
  font_color: string;
  font_weight: string;
  text_align: string;
  background_color: string;
  // Text Stroke (Outline)
  text_stroke_enabled: boolean;
  text_stroke_color: string;
  text_stroke_width: number;
  // Text Background Gradient
  text_bg_enabled: boolean;
  text_bg_color: string;
  text_bg_opacity: number;
  text_bg_shape: string;
  text_bg_blur: number;
  text_bg_extend_top: number;
  text_bg_extend_bottom: number;
  text_bg_extend_sides: number;
  text_bg_intensity: number;
  // Cover Title — WordArt kapak başlığı
  cover_title_enabled: boolean;
  cover_title_font_family: string;
  cover_title_font_size_pt: number;
  cover_title_font_color: string;
  cover_title_arc_intensity: number;
  cover_title_shadow_enabled: boolean;
  cover_title_shadow_color: string;
  cover_title_shadow_offset: number;
  cover_title_stroke_width: number;
  cover_title_stroke_color: string;
  cover_title_y_percent: number;
  cover_title_preset: string;
  cover_title_effect: string;
  cover_title_letter_spacing: number;
  // Dedication page
  dedication_default_text?: string;
  is_active: boolean;
}

// Resolution calculation utilities (matching backend logic)
const MM_TO_INCH = 25.4;
const DEFAULT_DPI = 300;
const AI_MAX_SIZE = 1024;

function mmToPx(mm: number, bleedMm: number = 0, dpi: number = DEFAULT_DPI): number {
  const totalMm = mm + 2 * bleedMm;
  return Math.round((totalMm / MM_TO_INCH) * dpi);
}

function calculateGenerationParams(template: PageTemplate) {
  const targetW = mmToPx(template.page_width_mm, template.bleed_mm);
  const targetH = mmToPx(template.page_height_mm, template.bleed_mm);

  const aspect = targetW / targetH;

  let genW: number, genH: number;
  if (targetW >= targetH) {
    genW = Math.min(targetW, AI_MAX_SIZE);
    genH = Math.round(genW / aspect);
    if (genH > AI_MAX_SIZE) {
      genH = AI_MAX_SIZE;
      genW = Math.round(genH * aspect);
    }
  } else {
    genH = Math.min(targetH, AI_MAX_SIZE);
    genW = Math.round(genH * aspect);
    if (genW > AI_MAX_SIZE) {
      genW = AI_MAX_SIZE;
      genH = Math.round(genW / aspect);
    }
  }

  const scale = Math.max(targetW / genW, targetH / genH);
  let upscaleFactor: number;
  let needsUpscale: boolean;

  if (scale <= 1.0) {
    upscaleFactor = 1;
    needsUpscale = false;
  } else if (scale <= 2.0) {
    upscaleFactor = 2;
    needsUpscale = true;
  } else {
    upscaleFactor = 4;
    needsUpscale = true;
  }

  // Calculate aspect ratio string
  const ratio = genW / genH;
  let aspectRatio = "1:1";
  if (Math.abs(ratio - 1.0) < 0.05) aspectRatio = "1:1";
  else if (Math.abs(ratio - 0.75) < 0.05) aspectRatio = "3:4";
  else if (Math.abs(ratio - 1.333) < 0.05) aspectRatio = "4:3";
  else if (Math.abs(ratio - 0.5625) < 0.05) aspectRatio = "9:16";
  else if (Math.abs(ratio - 1.778) < 0.05) aspectRatio = "16:9";

  return {
    generationWidth: genW,
    generationHeight: genH,
    targetWidth: targetW,
    targetHeight: targetH,
    upscaleFactor,
    needsUpscale,
    aspectRatio,
    upscaledWidth: genW * upscaleFactor,
    upscaledHeight: genH * upscaleFactor,
  };
}

interface AIConfig {
  id: string;
  name: string;
  description: string | null;
  image_provider: string;
  image_model: string;
  image_width: number;
  image_height: number;
  story_provider: string;
  story_model: string;
  story_temperature: number;
  is_active: boolean;
  is_default: boolean;
}

// Preview component for visualizing page layout (moved outside to prevent re-renders)
const PagePreview = ({ template }: { template: PageTemplate }) => {
  // Scale factor: 1mm = 0.8px for preview
  const scale = 0.8;

  // Direct conversion from mm to preview pixels
  const previewWidth = template.page_width_mm * scale;
  const previewHeight = template.page_height_mm * scale;

  // Check if areas overflow
  const imageEndX = template.image_x_percent + template.image_width_percent;
  const imageEndY = template.image_y_percent + template.image_height_percent;
  const textEndX = template.text_x_percent + template.text_width_percent;
  const textEndY = template.text_y_percent + template.text_height_percent;

  const hasOverflow = imageEndX > 100 || imageEndY > 100 || textEndX > 100 || textEndY > 100;

  // Check if areas overlap (when not overlay mode)
  const imageBottom = template.image_y_percent + template.image_height_percent;
  const textTop = template.text_y_percent;
  const hasOverlap = template.text_position !== "overlay" && imageBottom > textTop;

  return (
    <div className="flex flex-col items-center">
      <div
        className="relative overflow-hidden rounded border-2 border-gray-400 shadow-md"
        style={{
          width: previewWidth,
          height: previewHeight,
          backgroundColor: template.background_color,
          minWidth: 100,
          minHeight: 100,
        }}
      >
        {/* Image area */}
        <div
          className="absolute flex items-center justify-center border-2 border-purple-500 bg-purple-200 text-xs font-medium text-purple-700"
          style={{
            width: `${template.image_width_percent}%`,
            height: `${template.image_height_percent}%`,
            left: `${template.image_x_percent}%`,
            top: `${template.image_y_percent}%`,
          }}
        >
          Gorsel
        </div>
        {/* Text area - only shown if text_enabled */}
        {template.text_enabled && (
          <div
            className="absolute flex items-center justify-center border-2 border-blue-500 bg-blue-200 text-xs font-medium text-blue-700"
            style={{
              width: `${template.text_width_percent}%`,
              height: `${template.text_height_percent}%`,
              left: `${template.text_x_percent}%`,
              top: `${template.text_y_percent}%`,
              opacity: template.text_position === "overlay" ? 0.8 : 1,
            }}
          >
            Metin
          </div>
        )}
        {/* Text disabled indicator */}
        {!template.text_enabled && (
          <div className="absolute bottom-2 right-2 rounded bg-gray-500 px-2 py-1 text-xs text-white">
            Metin Kapalı
          </div>
        )}
      </div>
      {/* Dimensions label */}
      <p className="mt-2 text-sm font-medium text-gray-600">
        {template.page_width_mm} x {template.page_height_mm} mm
      </p>
      <p className="text-xs text-gray-400">
        (Onizleme: {Math.round(previewWidth)} x {Math.round(previewHeight)} px)
      </p>
      {/* Warning messages */}
      {hasOverflow && (
        <p className="mt-1 text-xs font-medium text-red-500">
          Uyari: Alanlar sayfa disina tasiyor!
        </p>
      )}
      {hasOverlap && (
        <p className="mt-1 text-xs font-medium text-orange-500">
          Uyari: Gorsel ve metin alanlari cakisiyor
        </p>
      )}
    </div>
  );
};

// Page template form component (moved outside to prevent re-renders)
const PageTemplateForm = ({
  template,
  setTemplate,
  pageType: _pageType,
  title,
  saving,
  onSave,
}: {
  template: PageTemplate;
  setTemplate: (t: PageTemplate) => void;
  pageType: string;
  title: string;
  saving: boolean;
  onSave: () => void;
}) => (
  <div className="space-y-6">
    {/* Template Name Input */}
    <Card className="border-2 border-purple-200">
      <CardHeader className="bg-purple-50">
        <CardTitle className="text-lg text-purple-800">Sablon Bilgileri</CardTitle>
        <CardDescription>Bu sablona bir isim verin</CardDescription>
      </CardHeader>
      <CardContent className="pt-4">
        <div className="space-y-2">
          <Label>Sablon Adi *</Label>
          <Input
            value={template.name}
            onChange={(e) => setTemplate({ ...template, name: e.target.value })}
            placeholder={`Orn: ${title} - A4 Boyut`}
            className="text-lg font-medium"
          />
          <p className="text-xs text-gray-500">
            Bu isim kaydedilmis sablonlar listesinde gorunecek
          </p>
        </div>
      </CardContent>
    </Card>

    {/* Preview and Physical Dimensions side by side */}
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
      {/* Physical Dimensions Card */}
      <Card>
        <CardHeader className="bg-gray-50">
          <CardTitle className="text-lg">Fiziksel Boyutlar</CardTitle>
          <CardDescription>Baski icin sayfa olculeri (mm)</CardDescription>
        </CardHeader>
        <CardContent className="pt-4">
          <div className="grid grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label>Genislik (mm)</Label>
              <Input
                type="number"
                value={template.page_width_mm}
                onChange={(e) =>
                  setTemplate({ ...template, page_width_mm: parseFloat(e.target.value) || 0 })
                }
              />
            </div>
            <div className="space-y-2">
              <Label>Yukseklik (mm)</Label>
              <Input
                type="number"
                value={template.page_height_mm}
                onChange={(e) =>
                  setTemplate({ ...template, page_height_mm: parseFloat(e.target.value) || 0 })
                }
              />
            </div>
            <div className="space-y-2">
              <Label>Tasma Payi (mm)</Label>
              <Input
                type="number"
                value={template.bleed_mm}
                onChange={(e) =>
                  setTemplate({ ...template, bleed_mm: parseFloat(e.target.value) || 0 })
                }
              />
            </div>
          </div>
          <div className="mt-4 rounded-lg bg-blue-50 p-3">
            <p className="text-sm font-medium text-blue-800">Hedef Cozunurluk (300 DPI)</p>
            <p className="mt-1 text-xs text-blue-600">
              Bleed dahil: {mmToPx(template.page_width_mm, template.bleed_mm)} x{" "}
              {mmToPx(template.page_height_mm, template.bleed_mm)} px
            </p>
            <p className="text-xs text-gray-500">
              Bleed haric: {mmToPx(template.page_width_mm, 0)} x{" "}
              {mmToPx(template.page_height_mm, 0)} px
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Preview Card */}
      <Card>
        <CardHeader className="bg-gray-50">
          <CardTitle className="text-lg">Onizleme</CardTitle>
          <CardDescription>Sayfa duzeni gorunumu</CardDescription>
        </CardHeader>
        <CardContent className="flex justify-center pt-4">
          <PagePreview template={template} />
        </CardContent>
      </Card>
    </div>

    {/* AI Generation Strategy Info */}
    <Card className="border-purple-200 bg-gradient-to-r from-purple-50 to-blue-50">
      <CardHeader>
        <CardTitle className="text-lg text-purple-800">AI Uretim Stratejisi</CardTitle>
        <CardDescription>Baski kalitesi icin otomatik hesaplanan degerler</CardDescription>
      </CardHeader>
      <CardContent>
        {(() => {
          const params = calculateGenerationParams(template);
          return (
            <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
              <div className="rounded-lg bg-white p-3 shadow-sm">
                <p className="text-xs text-gray-500">Hedef Boyut</p>
                <p className="text-lg font-bold text-purple-700">
                  {params.targetWidth} x {params.targetHeight}
                </p>
                <p className="text-xs text-gray-400">piksel (300 DPI)</p>
              </div>
              <div className="rounded-lg bg-white p-3 shadow-sm">
                <p className="text-xs text-gray-500">AI Uretim</p>
                <p className="text-lg font-bold text-blue-700">
                  {params.generationWidth} x {params.generationHeight}
                </p>
                <p className="text-xs text-gray-400">piksel (max 1024)</p>
              </div>
              <div className="rounded-lg bg-white p-3 shadow-sm">
                <p className="text-xs text-gray-500">Upscale</p>
                <p className="text-lg font-bold text-green-700">
                  {params.needsUpscale ? `${params.upscaleFactor}x` : "Gerekli degil"}
                </p>
                <p className="text-xs text-gray-400">
                  {params.needsUpscale
                    ? `${params.upscaledWidth} x ${params.upscaledHeight} px`
                    : "Direkt kullanim"}
                </p>
              </div>
              <div className="rounded-lg bg-white p-3 shadow-sm">
                <p className="text-xs text-gray-500">Aspect Ratio</p>
                <p className="text-lg font-bold text-orange-700">{params.aspectRatio}</p>
                <p className="text-xs text-gray-400">AI icin onerilen</p>
              </div>
            </div>
          );
        })()}
        <div className="mt-4 rounded-lg bg-white p-3 text-sm text-gray-600">
          <strong>Akis:</strong> AI {calculateGenerationParams(template).generationWidth}x
          {calculateGenerationParams(template).generationHeight}px uretir
          {calculateGenerationParams(template).needsUpscale && (
            <> → Real-ESRGAN {calculateGenerationParams(template).upscaleFactor}x upscale → </>
          )}
          → LANCZOS resize → {calculateGenerationParams(template).targetWidth}x
          {calculateGenerationParams(template).targetHeight}px baski kalitesi
        </div>
      </CardContent>
    </Card>

    {/* Image Settings */}
    <Card>
      <CardHeader className="bg-purple-50">
        <CardTitle className="text-lg text-purple-800">Gorsel Ayarlari</CardTitle>
        <CardDescription>
          AI tarafindan olusturulacak gorselin sayfa icindeki konumu
        </CardDescription>
      </CardHeader>
      <CardContent className="pt-4">
        <div className="grid grid-cols-2 gap-4 md:grid-cols-5">
          <div className="space-y-2">
            <Label>Genislik (%)</Label>
            <Input
              type="number"
              value={template.image_width_percent}
              onChange={(e) =>
                setTemplate({ ...template, image_width_percent: parseFloat(e.target.value) || 0 })
              }
            />
          </div>
          <div className="space-y-2">
            <Label>Yukseklik (%)</Label>
            <Input
              type="number"
              value={template.image_height_percent}
              onChange={(e) =>
                setTemplate({ ...template, image_height_percent: parseFloat(e.target.value) || 0 })
              }
            />
          </div>
          <div className="space-y-2">
            <Label>X Konumu (%)</Label>
            <Input
              type="number"
              value={template.image_x_percent}
              onChange={(e) =>
                setTemplate({ ...template, image_x_percent: parseFloat(e.target.value) || 0 })
              }
            />
          </div>
          <div className="space-y-2">
            <Label>Y Konumu (%)</Label>
            <Input
              type="number"
              value={template.image_y_percent}
              onChange={(e) =>
                setTemplate({ ...template, image_y_percent: parseFloat(e.target.value) || 0 })
              }
            />
          </div>
          <div className="space-y-2">
            <Label>En-Boy Orani</Label>
            <select
              className="w-full rounded-md border p-2"
              value={template.image_aspect_ratio}
              onChange={(e) => setTemplate({ ...template, image_aspect_ratio: e.target.value })}
            >
              <option value="1:1">1:1 (Kare)</option>
              <option value="3:4">3:4 (Dikey)</option>
              <option value="4:3">4:3 (Yatay)</option>
              <option value="16:9">16:9 (Genis)</option>
              <option value="9:16">9:16 (Uzun Dikey)</option>
            </select>
          </div>
        </div>
      </CardContent>
    </Card>

    {/* Text Settings */}
    <Card>
      <CardHeader className="bg-blue-50">
        <CardTitle className="text-lg text-blue-800">Metin Ayarlari</CardTitle>
        <CardDescription>Hikaye metninin sayfa icindeki konumu</CardDescription>
      </CardHeader>
      <CardContent className="pt-4">
        {/* Text Visibility Toggle */}
        <div className="mb-4 flex items-center justify-between rounded-lg border border-blue-200 bg-blue-50 p-4">
          <div>
            <Label className="text-base font-semibold text-blue-800">Metni Göster</Label>
            <p className="text-sm text-blue-600">Kapalı olursa bu sayfa tipinde metin görünmez</p>
          </div>
          <Switch
            checked={template.text_enabled}
            onCheckedChange={(checked) => setTemplate({ ...template, text_enabled: checked })}
          />
        </div>

        {/* Text Position Settings - only shown if text is enabled */}
        <div
          className={`grid grid-cols-2 gap-4 md:grid-cols-5 ${!template.text_enabled ? "pointer-events-none opacity-50" : ""}`}
        >
          <div className="space-y-2">
            <Label>Genislik (%)</Label>
            <Input
              type="number"
              value={template.text_width_percent}
              onChange={(e) =>
                setTemplate({ ...template, text_width_percent: parseFloat(e.target.value) || 0 })
              }
            />
          </div>
          <div className="space-y-2">
            <Label>Yukseklik (%)</Label>
            <Input
              type="number"
              value={template.text_height_percent}
              onChange={(e) =>
                setTemplate({ ...template, text_height_percent: parseFloat(e.target.value) || 0 })
              }
            />
          </div>
          <div className="space-y-2">
            <Label>X Konumu (%)</Label>
            <Input
              type="number"
              value={template.text_x_percent}
              onChange={(e) =>
                setTemplate({ ...template, text_x_percent: parseFloat(e.target.value) || 0 })
              }
            />
          </div>
          <div className="space-y-2">
            <Label>Y Konumu (%)</Label>
            <Input
              type="number"
              value={template.text_y_percent}
              onChange={(e) =>
                setTemplate({ ...template, text_y_percent: parseFloat(e.target.value) || 0 })
              }
            />
          </div>
          <div className="space-y-2">
            <Label>Konum Tipi</Label>
            <select
              className="w-full rounded-md border p-2"
              value={template.text_position}
              onChange={(e) => {
                const pos = e.target.value;
                const next = { ...template, text_position: pos };
                if (pos === "bottom" && template.text_y_percent < 50) next.text_y_percent = 72;
                if (pos === "top" && template.text_y_percent > 50) next.text_y_percent = 10;
                setTemplate(next);
              }}
            >
              <option value="top">Ustte</option>
              <option value="bottom">Altta</option>
              <option value="left">Solda</option>
              <option value="right">Sagda</option>
              <option value="overlay">Gorsel Uzerinde</option>
            </select>
          </div>
          <div className="space-y-2">
            <Label>Dikey Hizalama</Label>
            <select
              className="w-full rounded-md border p-2"
              value={template.text_vertical_align}
              onChange={(e) =>
                setTemplate({ ...template, text_vertical_align: e.target.value })
              }
            >
              <option value="top">Yukarı (kutu üstüne hizala)</option>
              <option value="center">Ortala</option>
              <option value="bottom">Aşağı (kutu altına hizala)</option>
            </select>
            <p className="text-[10px] text-gray-500">
              &quot;Aşağı&quot; seçilirse kısa metin kutunun altına yapışır, uzun metin yukarı doğru büyür.
            </p>
          </div>
          <p className="col-span-2 text-xs text-amber-700 md:col-span-5">
            Metin konumu ve font boyutu kaydettikten sonra yeni oluşturulan (veya tamamlanan)
            kitaplarda uygulanır; mevcut önizleme sayfaları otomatik güncellenmez.
          </p>
        </div>
      </CardContent>
    </Card>

    {/* Typography */}
    <Card>
      <CardHeader className="bg-green-50">
        <CardTitle className="text-lg text-green-800">Tipografi</CardTitle>
        <CardDescription>Yazı tipi ve renk ayarları</CardDescription>
      </CardHeader>
      <CardContent className="pt-4">
        {/* Google Fonts yükle */}
        <link href={googleFontsUrl} rel="stylesheet" />

        {/* Font Seçimi ve Önizleme */}
        <div className="mb-6">
          <Label className="mb-3 block text-base font-semibold">Font Ailesi</Label>
          <div className="grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-4">
            {AVAILABLE_FONTS.map((font) => (
              <button
                key={font.value}
                type="button"
                onClick={() => setTemplate({ ...template, font_family: font.value })}
                className={`rounded-lg border-2 p-3 text-left transition-all hover:shadow-md ${
                  template.font_family === font.value
                    ? "border-green-500 bg-green-50 shadow-md"
                    : "border-gray-200 hover:border-green-300"
                }`}
              >
                <div className="mb-1 flex items-center justify-between">
                  <span className="text-xs font-medium text-gray-500">{font.category}</span>
                  {template.font_family === font.value && (
                    <span className="h-2 w-2 rounded-full bg-green-500" />
                  )}
                </div>
                <p className="truncate text-lg" style={{ fontFamily: font.value }}>
                  {font.preview}
                </p>
                <p className="mt-1 text-xs text-gray-600">{font.label}</p>
                {FONTS_NO_TURKISH.has(font.value) && (
                  <p className="mt-0.5 text-[10px] text-amber-600">⚠ Türkçe ş/ğ desteklemez</p>
                )}
              </button>
            ))}
          </div>
        </div>

        {/* Diğer Tipografi Ayarları */}
        <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
          {/* Font Önizleme Paneli */}
          <div
            className="col-span-2 rounded-lg border-2 border-dashed border-green-300 p-4 md:col-span-4"
            style={{ backgroundColor: template.background_color }}
          >
            <Label className="mb-2 block inline-block rounded bg-white/80 px-2 py-1 text-sm font-semibold text-green-700">
              Font Önizleme: {template.font_family} {template.text_stroke_enabled && "(+ Stroke)"}
            </Label>
            <div
              className="space-y-2"
              style={{
                fontFamily: template.font_family,
                color: template.font_color,
                fontWeight: template.font_weight === "normal" ? 400
                  : template.font_weight === "light" ? 300
                  : template.font_weight === "bold" ? 700
                  : template.font_weight === "extrabold" ? 800
                  : template.font_weight === "black" ? 900
                  : parseInt(template.font_weight) || 400,
                ...(template.text_stroke_enabled && {
                  WebkitTextStroke: `${template.text_stroke_width}px ${template.text_stroke_color}`,
                  paintOrder: "stroke fill",
                }),
              }}
            >
              <p className="text-3xl">Bir varmış bir yokmuş, uzak diyarlarda...</p>
              <p className="text-xl">Küçük prenses maceraya atıldı!</p>
              <p className="text-base">
                ABCÇDEFGĞHIİJKLMNOÖPRSŞTUÜVYZ abcçdefgğhıijklmnoöprsştuüvyz 0123456789
              </p>
              <p className="text-sm italic">İtalik metin örneği - &quot;Güzel bir gün!&quot;</p>
              <p className="text-base font-bold">Kalın metin örneği</p>
            </div>
          </div>
          <div className="space-y-2">
            <Label>Font Boyutu (pt)</Label>
            <Input
              type="number"
              min={8}
              max={732}
              step={1}
              value={template.font_size_pt}
              onChange={(e) => {
                const raw = parseInt(e.target.value, 10);
                const clamped = Number.isNaN(raw)
                  ? 14
                  : Math.min(732, Math.max(8, raw));
                setTemplate({ ...template, font_size_pt: clamped });
              }}
            />
            <p className="text-xs text-gray-500">
              Sayfa altındaki metnin punto boyutu (8–732). Baskıda bu boyut kullanılır; ekranda
              önizleme küçük görünebilir.
            </p>
          </div>
          {/* Satır Aralığı */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label>Satır Aralığı</Label>
              <span className="rounded bg-blue-50 px-2 py-0.5 font-mono text-sm font-bold text-blue-700">
                {((template.line_height ?? 1.35)).toFixed(2)}×
              </span>
            </div>
            <input
              type="range"
              min={1.00}
              max={3.00}
              step={0.05}
              value={template.line_height ?? 1.35}
              onChange={(e) => setTemplate({ ...template, line_height: parseFloat(e.target.value) })}
              className="w-full accent-blue-600"
            />
            <div className="flex justify-between text-xs text-gray-400">
              <span>Sıkışık (1.00)</span>
              <span>Normal (1.35)</span>
              <span>Geniş (3.00)</span>
            </div>
            <div className="flex items-center gap-2">
              <Input
                type="number"
                min={1.00}
                max={3.00}
                step={0.05}
                value={template.line_height ?? 1.35}
                onChange={(e) => {
                  const v = parseFloat(e.target.value);
                  if (!isNaN(v)) setTemplate({ ...template, line_height: Math.min(3.0, Math.max(1.0, v)) });
                }}
                className="w-24 font-mono text-sm"
              />
              <button
                type="button"
                onClick={() => setTemplate({ ...template, line_height: 1.35 })}
                className="rounded border px-3 py-1 text-xs text-gray-500 hover:bg-gray-100"
              >
                Sıfırla
              </button>
            </div>
            <p className="text-xs text-gray-500">
              Satırlar arası boşluk çarpanı. 1.00 = tek satır; 1.35 = varsayılan; 2.00 = çift aralık.
            </p>
          </div>
          <div className="space-y-2">
            <Label>Harf Kalınlığı</Label>
            <select
              className="w-full rounded-md border p-2"
              value={template.font_weight}
              onChange={(e) => setTemplate({ ...template, font_weight: e.target.value })}
            >
              <option value="light">İnce (Light / 300)</option>
              <option value="normal">Normal (Regular / 400)</option>
              <option value="500">Orta (Medium / 500)</option>
              <option value="600">Yarı Kalın (SemiBold / 600)</option>
              <option value="bold">Kalın (Bold / 700)</option>
              <option value="extrabold">Çok Kalın (ExtraBold / 800)</option>
              <option value="black">En Kalın (Black / 900)</option>
            </select>
          </div>
          <div className="space-y-2">
            <Label>Hizalama</Label>
            <select
              className="w-full rounded-md border p-2"
              value={template.text_align}
              onChange={(e) => setTemplate({ ...template, text_align: e.target.value })}
            >
              <option value="left">Sola</option>
              <option value="center">Ortaya</option>
              <option value="right">Saga</option>
              <option value="justify">Iki Yana</option>
            </select>
          </div>
          <div className="space-y-2">
            <Label>Font Rengi</Label>
            <div className="flex gap-2">
              <Input
                type="color"
                value={template.font_color}
                onChange={(e) => setTemplate({ ...template, font_color: e.target.value })}
                className="h-10 w-12 p-1"
              />
              <Input
                type="text"
                value={template.font_color}
                onChange={(e) => setTemplate({ ...template, font_color: e.target.value })}
                className="flex-1"
              />
            </div>
          </div>
          <div className="space-y-2">
            <Label>Arka Plan</Label>
            <div className="flex gap-2">
              <Input
                type="color"
                value={template.background_color}
                onChange={(e) => setTemplate({ ...template, background_color: e.target.value })}
                className="h-10 w-12 p-1"
              />
              <Input
                type="text"
                value={template.background_color}
                onChange={(e) => setTemplate({ ...template, background_color: e.target.value })}
                className="flex-1"
              />
            </div>
          </div>
        </div>

        {/* Text Stroke (Kenar Çizgisi) */}
        <div className="mt-6 rounded-lg border-2 border-dashed border-orange-300 bg-orange-50 p-4">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <Label className="text-base font-semibold text-orange-800">
                Metin Kenar Çizgisi (Stroke)
              </Label>
              <p className="text-xs text-orange-600">Yazının etrafına kontur ekler</p>
            </div>
            <Switch
              checked={template.text_stroke_enabled}
              onCheckedChange={(checked) =>
                setTemplate({ ...template, text_stroke_enabled: checked })
              }
            />
          </div>

          {template.text_stroke_enabled && (
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Kenar Rengi</Label>
                <div className="flex gap-2">
                  <Input
                    type="color"
                    value={template.text_stroke_color}
                    onChange={(e) =>
                      setTemplate({ ...template, text_stroke_color: e.target.value })
                    }
                    className="h-10 w-12 p-1"
                  />
                  <Input
                    type="text"
                    value={template.text_stroke_color}
                    onChange={(e) =>
                      setTemplate({ ...template, text_stroke_color: e.target.value })
                    }
                    className="flex-1"
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label>Kenar Kalınlığı (px)</Label>
                <Input
                  type="number"
                  min={0}
                  max={10}
                  step={0.5}
                  value={template.text_stroke_width}
                  onChange={(e) =>
                    setTemplate({ ...template, text_stroke_width: parseFloat(e.target.value) || 0 })
                  }
                />
                <p className="text-xs text-gray-500">Önerilen: 1-3px</p>
              </div>
            </div>
          )}

          {/* Stroke Önizleme */}
          {template.text_stroke_enabled && (
            <div
              className="mt-4 rounded-lg p-4"
              style={{ backgroundColor: template.background_color }}
            >
              <p
                className="text-center text-2xl"
                style={{
                  fontFamily: template.font_family,
                  color: template.font_color,
                  WebkitTextStroke: `${template.text_stroke_width}px ${template.text_stroke_color}`,
                  paintOrder: "stroke fill",
                }}
              >
                Stroke Önizleme: Merhaba Dünya!
              </p>
            </div>
          )}
        </div>

        {/* Metin Arkaplan Gradient (Gölge) */}
        <div className="mt-6 rounded-lg border-2 border-dashed border-indigo-300 bg-indigo-50 p-4">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <Label className="text-base font-semibold text-indigo-800">
                Metin Arkaplan Gölgesi (Bulut Overlay)
              </Label>
              <p className="text-xs text-indigo-600">
                Metnin arkasına yarı saydam bulut/gradient ekleyerek okunabilirliği artırır. Genişlik, yükseklik ve yoğunluk ayarlanabilir.
              </p>
            </div>
            <Switch
              checked={template.text_bg_enabled}
              onCheckedChange={(checked) =>
                setTemplate({ ...template, text_bg_enabled: checked })
              }
            />
          </div>

          {template.text_bg_enabled && (
            <>
              {/* Çerçeve Şekli Seçimi */}
              <div className="mb-4">
                <Label className="mb-2 block text-sm font-semibold">Çerçeve Şekli</Label>
                <div className="grid grid-cols-2 gap-3 md:grid-cols-5">
                  {[
                    { value: "rectangle", label: "Düz Dikdörtgen", icon: "▬", desc: "Sert kenar" },
                    { value: "rounded", label: "Yuvarlatılmış", icon: "▢", desc: "Yumuşak köşeler" },
                    { value: "soft_vignette", label: "Yumuşak Geçiş", icon: "◎", desc: "Vignette efekti" },
                    { value: "wavy", label: "Dalgalı", icon: "〰", desc: "Organik dalgalar" },
                    { value: "cloud", label: "Bulutsu", icon: "☁", desc: "Tam kaplama bulut" },
                  ].map((shape) => (
                    <button
                      key={shape.value}
                      type="button"
                      onClick={() => setTemplate({ ...template, text_bg_shape: shape.value })}
                      className={`rounded-lg border-2 p-3 text-center transition-all hover:shadow-md ${
                        template.text_bg_shape === shape.value
                          ? "border-indigo-500 bg-indigo-50 shadow-md"
                          : "border-gray-200 hover:border-indigo-300"
                      }`}
                    >
                      <div className="text-2xl">{shape.icon}</div>
                      <p className="mt-1 text-sm font-medium">{shape.label}</p>
                      <p className="text-xs text-gray-500">{shape.desc}</p>
                    </button>
                  ))}
                </div>
              </div>

              {/* Renk + Opaklık */}
              <div className="mb-4 grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Arkaplan Rengi</Label>
                  <div className="flex gap-2">
                    <Input
                      type="color"
                      value={template.text_bg_color}
                      onChange={(e) =>
                        setTemplate({ ...template, text_bg_color: e.target.value })
                      }
                      className="h-10 w-12 p-1"
                    />
                    <Input
                      type="text"
                      value={template.text_bg_color}
                      onChange={(e) =>
                        setTemplate({ ...template, text_bg_color: e.target.value })
                      }
                      className="flex-1"
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Saydamlık: {template.text_bg_opacity}/255</Label>
                  <input
                    type="range"
                    min={0}
                    max={255}
                    step={5}
                    value={template.text_bg_opacity}
                    onChange={(e) =>
                      setTemplate({ ...template, text_bg_opacity: parseInt(e.target.value) || 0 })
                    }
                    className="w-full accent-indigo-600"
                  />
                  <div className="flex justify-between text-[10px] text-gray-400">
                    <span>Saydam</span>
                    <span>Opak (resmi kapatır)</span>
                  </div>
                </div>
              </div>

              {/* Kenar Yumuşaklığı + İç Yoğunluk */}
              <div className="mb-4 grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Kenar Yumuşaklığı (Blur): {template.text_bg_blur}px</Label>
                  <input
                    type="range"
                    min={0}
                    max={200}
                    step={5}
                    value={template.text_bg_blur}
                    onChange={(e) =>
                      setTemplate({ ...template, text_bg_blur: parseInt(e.target.value) || 0 })
                    }
                    className="w-full accent-indigo-600"
                  />
                  <div className="flex justify-between text-[10px] text-gray-400">
                    <span>Keskin</span>
                    <span>Çok yumuşak</span>
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>İç Alan Yoğunluğu: %{template.text_bg_intensity}</Label>
                  <input
                    type="range"
                    min={50}
                    max={100}
                    step={5}
                    value={template.text_bg_intensity}
                    onChange={(e) =>
                      setTemplate({ ...template, text_bg_intensity: parseInt(e.target.value) || 100 })
                    }
                    className="w-full accent-indigo-600"
                  />
                  <div className="flex justify-between text-[10px] text-gray-400">
                    <span>%50 yarı saydam</span>
                    <span>%100 tam opak</span>
                  </div>
                </div>
              </div>

              {/* Gölge Boyut Kontrolleri — TÜM şekiller için */}
              <div className="mb-4 rounded-lg border border-indigo-200 bg-white p-4">
                <Label className="mb-3 block text-sm font-semibold text-indigo-700">
                  Gölge Boyut ve Kapsama Ayarları
                </Label>
                <p className="mb-3 text-[11px] text-gray-500">
                  Gölgenin metin alanının ne kadar üstüne/altına/yanlarına taşacağını ayarlayın. Yan Genişlik metin kutusunun her iki yanına % uzantı ekler. Resmi tamamen kapatmak için değerleri yükseltin.
                </p>
                <div className="grid grid-cols-3 gap-4">
                    <div className="space-y-2">
                      <Label className="text-xs">Üste Uzantı: %{template.text_bg_extend_top}</Label>
                      <input
                        type="range"
                        min={0}
                        max={200}
                        step={5}
                      value={template.text_bg_extend_top}
                      onChange={(e) =>
                        setTemplate({ ...template, text_bg_extend_top: parseInt(e.target.value) || 0 })
                      }
                      className="w-full accent-indigo-600"
                    />
                    <div className="flex justify-between text-[10px] text-gray-400">
                      <span>Metin hizası</span>
                      <span>Çok yukarı</span>
                    </div>
                  </div>
                    <div className="space-y-2">
                      <Label className="text-xs">Alta Uzantı: %{template.text_bg_extend_bottom}</Label>
                      <input
                        type="range"
                        min={0}
                        max={100}
                        step={5}
                      value={template.text_bg_extend_bottom}
                      onChange={(e) =>
                        setTemplate({ ...template, text_bg_extend_bottom: parseInt(e.target.value) || 0 })
                      }
                      className="w-full accent-indigo-600"
                    />
                    <div className="flex justify-between text-[10px] text-gray-400">
                      <span>Metin hizası</span>
                      <span>Aşağı taşır</span>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label className="text-xs">Yan Genişlik (sayfa %): %{template.text_bg_extend_sides}</Label>
                    <input
                      type="range"
                      min={0}
                      max={50}
                      step={2}
                      value={template.text_bg_extend_sides}
                      onChange={(e) =>
                        setTemplate({ ...template, text_bg_extend_sides: parseInt(e.target.value) || 0 })
                      }
                      className="w-full accent-indigo-600"
                    />
                    <div className="flex justify-between text-[10px] text-gray-400">
                      <span>Metin kutusu kadar</span>
                      <span>+sayfa %50 her yana</span>
                    </div>
                  </div>
                </div>
              </div>
            </>
          )}

          {/* Gradient Önizleme */}
          {template.text_bg_enabled && (() => {
            const hexAlpha = Math.round(template.text_bg_opacity * (template.text_bg_intensity / 100)).toString(16).padStart(2, "0");
            const bgHex = `${template.text_bg_color}${hexAlpha}`;
            const extTop = template.text_bg_extend_top;
            const extBot = template.text_bg_extend_bottom;
            const extSide = template.text_bg_extend_sides;
            const topPct = Math.max(0, 100 - 30 - extTop * 0.3);
            const botPct = Math.min(100, 70 + extBot * 0.3);
            const vAlign = template.text_vertical_align || "bottom";

            const gradientBg = (() => {
              switch (template.text_bg_shape) {
                case "rectangle": return bgHex;
                case "rounded": return bgHex;
                case "cloud": return `radial-gradient(ellipse ${100 - extSide * 2}% ${extTop + extBot + 60}% at 50% ${50 + (extTop - extBot) * 0.2}%, ${bgHex} 50%, transparent 85%)`;
                case "wavy": return `radial-gradient(ellipse ${100 - extSide * 2}% ${extTop + extBot + 60}% at 50% 60%, ${bgHex} 40%, transparent 75%)`;
                case "soft_vignette": return `radial-gradient(ellipse ${100 - extSide * 2}% ${extTop + extBot + 50}% at 50% 55%, ${bgHex} 35%, transparent 70%)`;
                default: return bgHex;
              }
            })();

            const borderRadius = (() => {
              switch (template.text_bg_shape) {
                case "rounded": return "16px";
                case "cloud": return "50%";
                case "wavy": return "40% 40% 0 0 / 20% 20% 0 0";
                case "soft_vignette": return "50%";
                default: return "0";
              }
            })();

            const textStyle = {
              fontFamily: template.font_family,
              color: template.font_color,
              ...(template.text_stroke_enabled && {
                WebkitTextStroke: `${template.text_stroke_width}px ${template.text_stroke_color}` as string,
                paintOrder: "stroke fill" as string,
              }),
            };

            return (
              <div
                className="relative mt-4 overflow-hidden rounded-lg"
                style={{ height: 200 }}
              >
                <div className="absolute inset-0" style={{ background: "linear-gradient(135deg, #8BC6EC 0%, #9599E2 50%, #c3a7e0 100%)" }} />
                <div
                  className="absolute"
                  style={{
                    top: `${topPct}%`,
                    bottom: `${100 - botPct}%`,
                    left: `${extSide}%`,
                    right: `${extSide}%`,
                    background: gradientBg,
                    borderRadius,
                    filter: `blur(${Math.max(template.text_bg_blur / 4, 2)}px)`,
                  }}
                />
                <div
                  className="absolute left-4 right-4 flex flex-col gap-1"
                  style={{
                    top: vAlign === "top" ? "8%" : vAlign === "center" ? "50%" : undefined,
                    bottom: vAlign === "bottom" ? "6%" : undefined,
                    transform: vAlign === "center" ? "translateY(-50%)" : undefined,
                  }}
                >
                  <p className="text-center text-base leading-relaxed" style={textStyle}>
                    Bir varmış bir yokmuş, uzak diyarlarda
                  </p>
                  <p className="text-center text-base leading-relaxed" style={textStyle}>
                    küçük bir kahraman büyük bir maceraya atılmış...
                  </p>
                </div>
                <span className="absolute right-2 top-2 rounded bg-black/40 px-2 py-1 text-xs text-white">
                  {template.text_bg_shape} | hiza: {vAlign} | üst:{extTop}% alt:{extBot}% yan:{extSide}%
                </span>
              </div>
            );
          })()}
        </div>
      </CardContent>
    </Card>

    {/* ── Kapak Başlık Stili (sadece cover page_type için) ── */}
    {template.page_type === "cover" && (
      <Card className="border-2 border-amber-200">
        <CardHeader className="bg-amber-50">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-lg text-amber-800">Kapak Başlık Stili (WordArt)</CardTitle>
              <CardDescription>
                Kapak fotoğrafına eklenen kitap başlığının stil ayarları
              </CardDescription>
            </div>
            <Switch
              checked={template.cover_title_enabled}
              onCheckedChange={(checked) =>
                setTemplate({ ...template, cover_title_enabled: checked })
              }
            />
          </div>
        </CardHeader>

        {template.cover_title_enabled && (
          <CardContent className="space-y-5 pt-4">
            {/* Preset Seçimi */}
            <div className="space-y-2">
              <Label className="font-semibold">Başlık Preset</Label>
              <div className="grid grid-cols-3 gap-3">
                {[
                  { value: "minimal", label: "Minimal", desc: "Sadece güçlü stroke" },
                  { value: "classic", label: "Classic", desc: "Stroke + bulanık gölge" },
                  { value: "premium", label: "Premium", desc: "Stroke + gölge + banner" },
                ].map((p) => (
                  <button
                    key={p.value}
                    type="button"
                    onClick={() => setTemplate({ ...template, cover_title_preset: p.value })}
                    className={`rounded-lg border-2 p-3 text-left transition-all ${
                      template.cover_title_preset === p.value
                        ? "border-amber-500 bg-amber-50 ring-2 ring-amber-200"
                        : "border-gray-200 hover:border-amber-300"
                    }`}
                  >
                    <div className="font-semibold text-sm">{p.label}</div>
                    <div className="text-xs text-gray-500 mt-1">{p.desc}</div>
                  </button>
                ))}
              </div>
            </div>
            {/* Parıltı Efekti Seçimi */}
            <div className="space-y-2">
              <Label className="font-semibold">Parıltı / Shine Efekti</Label>
              <div className="grid grid-cols-5 gap-2">
                {[
                  { value: "none", label: "Yok", desc: "Düz renk", gradient: "linear-gradient(#888, #888)" },
                  { value: "gold_shine", label: "Altın", desc: "Gold shine", gradient: "linear-gradient(180deg, #FFF8DC, #FFD700, #B8860B, #FFD700, #FFF8DC)" },
                  { value: "silver_shine", label: "Gümüş", desc: "Silver shine", gradient: "linear-gradient(180deg, #FFF, #C0C0C0, #808080, #C0C0C0, #FFF)" },
                  { value: "bronze_shine", label: "Bronz", desc: "Bronze shine", gradient: "linear-gradient(180deg, #FFDEAD, #CD853F, #8B4513, #CD853F, #FFDEAD)" },
                  { value: "rainbow", label: "Gökkuşağı", desc: "Rainbow", gradient: "linear-gradient(180deg, #FF6B6B, #FECA57, #48DBFB, #FF9FF3, #54A0FF)" },
                ].map((e) => (
                  <button
                    key={e.value}
                    type="button"
                    onClick={() => setTemplate({ ...template, cover_title_effect: e.value })}
                    className={`rounded-lg border-2 p-2 text-center transition-all ${
                      template.cover_title_effect === e.value
                        ? "border-amber-500 ring-2 ring-amber-200"
                        : "border-gray-200 hover:border-amber-300"
                    }`}
                  >
                    <div
                      className="mx-auto mb-1 h-6 w-full rounded"
                      style={{ background: e.gradient }}
                    />
                    <div className="text-xs font-semibold">{e.label}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* Harf Aralığı */}
            <div className="space-y-2">
              <Label className="font-semibold">
                Harf Aralığı (Letter Spacing): {template.cover_title_letter_spacing}px
              </Label>
              <input
                type="range"
                min={-5}
                max={20}
                step={1}
                value={template.cover_title_letter_spacing}
                onChange={(e) =>
                  setTemplate({ ...template, cover_title_letter_spacing: parseInt(e.target.value) })
                }
                className="w-full"
              />
              <p className="text-xs text-gray-500">
                Harfler arası ek boşluk. Negatif değerler harfleri yakınlaştırır.
              </p>
            </div>

            {/* Font ve Boyut */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label className="font-semibold">Başlık Fontu</Label>
                <select
                  value={template.cover_title_font_family}
                  onChange={(e) =>
                    setTemplate({ ...template, cover_title_font_family: e.target.value })
                  }
                  className="w-full rounded-md border p-2"
                  style={{ fontFamily: template.cover_title_font_family }}
                >
                  {AVAILABLE_FONTS.map((f) => (
                    <option key={f.value} value={f.value} style={{ fontFamily: f.value }}>
                      {f.label} ({f.category})
                    </option>
                  ))}
                </select>
              </div>
              <div className="space-y-2">
                <Label className="font-semibold">Font Boyutu (pt): {template.cover_title_font_size_pt}</Label>
                <input
                  type="range"
                  min={16}
                  max={96}
                  step={2}
                  value={template.cover_title_font_size_pt}
                  onChange={(e) =>
                    setTemplate({ ...template, cover_title_font_size_pt: parseInt(e.target.value) })
                  }
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-gray-400">
                  <span>16pt</span>
                  <span>96pt</span>
                </div>
              </div>
            </div>

            {/* Renk ve Dikey Konum */}
            <div className="grid grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label className="font-semibold">Başlık Rengi</Label>
                <div className="flex gap-2">
                  <Input
                    type="color"
                    value={template.cover_title_font_color}
                    onChange={(e) =>
                      setTemplate({ ...template, cover_title_font_color: e.target.value })
                    }
                    className="h-10 w-12 p-1"
                  />
                  <Input
                    type="text"
                    value={template.cover_title_font_color}
                    onChange={(e) =>
                      setTemplate({ ...template, cover_title_font_color: e.target.value })
                    }
                    className="flex-1"
                  />
                </div>
                {/* Hızlı renk seçenekleri */}
                <div className="flex gap-1">
                  {[
                    { color: "#FFD700", label: "Altın" },
                    { color: "#FFFFFF", label: "Beyaz" },
                    { color: "#FF6B35", label: "Turuncu" },
                    { color: "#E91E63", label: "Pembe" },
                    { color: "#4FC3F7", label: "Mavi" },
                  ].map((c) => (
                    <button
                      key={c.color}
                      type="button"
                      onClick={() =>
                        setTemplate({ ...template, cover_title_font_color: c.color })
                      }
                      className="h-6 w-6 rounded-full border-2 border-gray-300 hover:scale-110 transition-transform"
                      style={{ backgroundColor: c.color }}
                      title={c.label}
                    />
                  ))}
                </div>
              </div>
              <div className="space-y-2">
                <Label className="font-semibold">Dikey Konum (%): {template.cover_title_y_percent}</Label>
                <input
                  type="range"
                  min={0}
                  max={50}
                  step={1}
                  value={template.cover_title_y_percent}
                  onChange={(e) =>
                    setTemplate({ ...template, cover_title_y_percent: parseFloat(e.target.value) })
                  }
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-gray-400">
                  <span>En üst</span>
                  <span>Orta</span>
                </div>
              </div>
              <div className="space-y-2">
                <Label className="font-semibold">Kavis Yoğunluğu: {template.cover_title_arc_intensity}</Label>
                <input
                  type="range"
                  min={0}
                  max={100}
                  step={5}
                  value={template.cover_title_arc_intensity}
                  onChange={(e) =>
                    setTemplate({ ...template, cover_title_arc_intensity: parseInt(e.target.value) })
                  }
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-gray-400">
                  <span>Düz</span>
                  <span>Çok Kavisli</span>
                </div>
              </div>
            </div>

            {/* Gölge Ayarları */}
            <div className="rounded-lg border p-3 bg-gray-50">
              <div className="flex items-center justify-between mb-3">
                <Label className="font-semibold">Gölge (Drop Shadow)</Label>
                <Switch
                  checked={template.cover_title_shadow_enabled}
                  onCheckedChange={(checked) =>
                    setTemplate({ ...template, cover_title_shadow_enabled: checked })
                  }
                />
              </div>
              {template.cover_title_shadow_enabled && (
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Gölge Rengi</Label>
                    <div className="flex gap-2">
                      <Input
                        type="color"
                        value={template.cover_title_shadow_color}
                        onChange={(e) =>
                          setTemplate({ ...template, cover_title_shadow_color: e.target.value })
                        }
                        className="h-10 w-12 p-1"
                      />
                      <Input
                        type="text"
                        value={template.cover_title_shadow_color}
                        onChange={(e) =>
                          setTemplate({ ...template, cover_title_shadow_color: e.target.value })
                        }
                        className="flex-1"
                      />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label>Gölge Kaydırma (px): {template.cover_title_shadow_offset}</Label>
                    <input
                      type="range"
                      min={0}
                      max={15}
                      step={1}
                      value={template.cover_title_shadow_offset}
                      onChange={(e) =>
                        setTemplate({ ...template, cover_title_shadow_offset: parseInt(e.target.value) })
                      }
                      className="w-full"
                    />
                  </div>
                </div>
              )}
            </div>

            {/* Kenar Çizgisi (Stroke) */}
            <div className="rounded-lg border p-3 bg-gray-50">
              <Label className="font-semibold mb-3 block">Kenar Çizgisi (Stroke)</Label>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Çizgi Rengi</Label>
                  <div className="flex gap-2">
                    <Input
                      type="color"
                      value={template.cover_title_stroke_color}
                      onChange={(e) =>
                        setTemplate({ ...template, cover_title_stroke_color: e.target.value })
                      }
                      className="h-10 w-12 p-1"
                    />
                    <Input
                      type="text"
                      value={template.cover_title_stroke_color}
                      onChange={(e) =>
                        setTemplate({ ...template, cover_title_stroke_color: e.target.value })
                      }
                      className="flex-1"
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Çizgi Kalınlığı: {template.cover_title_stroke_width}</Label>
                  <input
                    type="range"
                    min={0}
                    max={10}
                    step={0.5}
                    value={template.cover_title_stroke_width}
                    onChange={(e) =>
                      setTemplate({ ...template, cover_title_stroke_width: parseFloat(e.target.value) })
                    }
                    className="w-full"
                  />
                </div>
              </div>
            </div>

            {/* Canlı Önizleme */}
            <div
              className="relative overflow-hidden rounded-lg"
              style={{ height: 140 }}
            >
              {/* Arkaplan: kapak simülasyonu */}
              <div
                className="absolute inset-0"
                style={{
                  background: "linear-gradient(135deg, #87CEEB 0%, #98D8C8 50%, #F7DC6F 100%)",
                }}
              />
              {/* Banner (premium) */}
              {template.cover_title_preset === "premium" && (
                <div
                  className="absolute left-1/2 -translate-x-1/2"
                  style={{
                    top: `calc(${Math.max(6, template.cover_title_y_percent)}% - 10px)`,
                    background: "rgba(11,27,43,0.32)",
                    borderRadius: "22px",
                    padding: "10px 32px",
                    backdropFilter: "blur(4px)",
                  }}
                />
              )}
              {/* Başlık metni */}
              {(() => {
                const effectGradients: Record<string, string> = {
                  gold_shine: "linear-gradient(180deg, #FFF8DC, #FFD700, #B8860B, #FFD700, #FFF8DC)",
                  silver_shine: "linear-gradient(180deg, #FFF, #C0C0C0, #808080, #C0C0C0, #FFF)",
                  bronze_shine: "linear-gradient(180deg, #FFDEAD, #CD853F, #8B4513, #CD853F, #FFDEAD)",
                  rainbow: "linear-gradient(180deg, #FF6B6B, #FECA57, #48DBFB, #FF9FF3, #54A0FF)",
                };
                const hasEffect = template.cover_title_effect !== "none" && effectGradients[template.cover_title_effect];
                const effectStroke: Record<string, string> = {
                  gold_shine: "#5C4000",
                  silver_shine: "#2F2F3F",
                  bronze_shine: "#3D1F00",
                  rainbow: "#1A1A3E",
                };
                return (
                  <div
                    className="absolute left-0 right-0 text-center px-[10%]"
                    style={{
                      top: `${Math.max(6, template.cover_title_y_percent)}%`,
                      fontFamily: template.cover_title_font_family,
                      fontSize: `${Math.min(template.cover_title_font_size_pt * 0.6, 36)}px`,
                      color: hasEffect ? "transparent" : template.cover_title_font_color,
                      ...(hasEffect ? {
                        background: effectGradients[template.cover_title_effect],
                        WebkitBackgroundClip: "text",
                        backgroundClip: "text",
                      } : {}),
                      textShadow: template.cover_title_preset !== "minimal"
                        ? `0 3px 8px rgba(0,0,0,0.45)${hasEffect ? `, 0 0 20px ${template.cover_title_effect === "gold_shine" ? "rgba(255,200,50,0.6)" : template.cover_title_effect === "silver_shine" ? "rgba(200,200,255,0.6)" : "rgba(200,150,80,0.5)"}` : ""}`
                        : "none",
                      WebkitTextStroke: `${Math.max(1.5, template.cover_title_font_size_pt * 0.04)}px ${hasEffect ? effectStroke[template.cover_title_effect] || template.cover_title_stroke_color : template.cover_title_stroke_color}`,
                      paintOrder: "stroke fill",
                      letterSpacing: `${template.cover_title_letter_spacing}px`,
                      fontWeight: 700,
                    }}
                  >
                    <span style={{
                      display: "inline-block",
                      transform: template.cover_title_arc_intensity > 0
                        ? `perspective(200px) rotateX(${template.cover_title_arc_intensity * 0.08}deg)`
                        : "none",
                      ...(template.cover_title_preset === "premium" ? {
                        background: hasEffect ? effectGradients[template.cover_title_effect] : "rgba(11,27,43,0.30)",
                        WebkitBackgroundClip: hasEffect ? "text" : undefined,
                        backgroundClip: hasEffect ? "text" : undefined,
                        color: hasEffect ? "transparent" : undefined,
                        borderRadius: hasEffect ? undefined : "18px",
                        padding: hasEffect ? undefined : "6px 20px",
                      } : {}),
                    }}>
                      Uras&apos;ın Kapadokya Macerası
                    </span>
                  </div>
                );
              })()}
              {/* Label */}
              <span className="absolute right-2 top-2 rounded bg-black/40 px-2 py-1 text-xs text-white">
                Kapak Başlık Önizleme
              </span>
            </div>
          </CardContent>
        )}
      </Card>
    )}

    <Button onClick={onSave} disabled={saving} className="w-full" size="lg">
      {saving ? "Kaydediliyor..." : `${title} Sablonunu Kaydet`}
    </Button>
  </div>
);

// Saved templates list component (moved outside to prevent re-renders)
const SavedTemplatesList = ({
  pageTemplates,
  pageType,
  title,
  defaultTemplate,
  onLoadTemplate,
}: {
  pageTemplates: PageTemplate[];
  pageType: string;
  title: string;
  defaultTemplate: PageTemplate;
  onLoadTemplate: (t: PageTemplate) => void;
}) => {
  const filteredTemplates = pageTemplates.filter((t) => t.page_type === pageType);

  if (filteredTemplates.length === 0) {
    return (
      <Card className="mb-6 border-dashed">
        <CardContent className="py-8 text-center text-gray-500">
          <p>Henuz kayitli {title.toLowerCase()} sablonu yok</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="mb-6">
      <CardHeader className="bg-gray-50">
        <CardTitle className="text-lg">Kayitli {title} Sablonlari</CardTitle>
        <CardDescription>{filteredTemplates.length} adet sablon bulundu</CardDescription>
      </CardHeader>
      <CardContent className="pt-4">
        <div className="space-y-2">
          {filteredTemplates.map((t) => (
            <div
              key={t.id}
              className="flex cursor-pointer items-center justify-between rounded-lg border bg-white p-4 hover:bg-gray-50"
              onClick={() => onLoadTemplate({ ...defaultTemplate, ...t })}
            >
              <div>
                <p className="font-medium text-gray-900">{t.name}</p>
                <p className="text-sm text-gray-500">
                  {t.page_width_mm} x {t.page_height_mm} mm | Bleed: {t.bleed_mm}mm | Hedef:{" "}
                  {mmToPx(t.page_width_mm, t.bleed_mm)} x {mmToPx(t.page_height_mm, t.bleed_mm)} px
                </p>
              </div>
              <div className="flex items-center gap-2">
                {t.is_active && (
                  <span className="rounded bg-green-100 px-2 py-1 text-xs text-green-800">
                    Aktif
                  </span>
                )}
                <Button
                  size="sm"
                  variant="outline"
                  onClick={(e) => {
                    e.stopPropagation();
                    onLoadTemplate({ ...defaultTemplate, ...t });
                  }}
                >
                  Duzenle
                </Button>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
};

// Default templates for each page type with YOUR dimensions
const defaultCoverTemplate: PageTemplate = {
  name: "Ön Kapak",
  page_type: "cover",
  // Your dimensions: 246 x 326 mm
  page_width_mm: 326,
  page_height_mm: 246,
  bleed_mm: 3,
  // Image covers full page for cover
  image_width_percent: 100,
  image_height_percent: 100,
  image_x_percent: 0,
  image_y_percent: 0,
  image_aspect_ratio: "4:3",
  // Text visibility - cover typically has no text overlay
  text_enabled: false,
  // Title overlay (if enabled)
  text_width_percent: 80,
  text_height_percent: 20,
  text_x_percent: 10,
  text_y_percent: 75,
  text_position: "overlay",
  text_vertical_align: "center",
  font_family: "Nunito",
  font_size_pt: 32,
  line_height: 1.35,
  font_color: "#FFFFFF",
  font_weight: "normal",
  text_align: "center",
  background_color: "#000000",
  // Text stroke for better visibility on images
  text_stroke_enabled: true,
  text_stroke_color: "#000000",
  text_stroke_width: 2,
  // Text background gradient
  text_bg_enabled: true,
  text_bg_color: "#FFFFFF",
  text_bg_opacity: 230,
  text_bg_shape: "cloud",
  text_bg_blur: 50,
  text_bg_extend_top: 60,
  text_bg_extend_bottom: 15,
  text_bg_extend_sides: 10,
  text_bg_intensity: 100,
  // Cover Title — WordArt
  cover_title_enabled: true,
  cover_title_font_family: "Lobster",
  cover_title_font_size_pt: 48,
  cover_title_font_color: "#FFD700",
  cover_title_arc_intensity: 35,
  cover_title_shadow_enabled: true,
  cover_title_shadow_color: "#000000",
  cover_title_shadow_offset: 3,
  cover_title_stroke_width: 2,
  cover_title_stroke_color: "#8B6914",
  cover_title_y_percent: 5,
  cover_title_preset: "premium",
  cover_title_effect: "gold_shine",
  cover_title_letter_spacing: 0,
  is_active: true,
};

const defaultBackCoverTemplate: PageTemplate = {
  name: "Arka Kapak",
  page_type: "back",
  // Your dimensions: 246 x 311 mm
  page_width_mm: 311,
  page_height_mm: 246,
  bleed_mm: 3,
  // Smaller image for back
  image_width_percent: 40,
  image_height_percent: 40,
  image_x_percent: 30,
  image_y_percent: 10,
  image_aspect_ratio: "1:1",
  // Text visibility
  text_enabled: true,
  // Summary text below
  text_width_percent: 80,
  text_height_percent: 35,
  text_x_percent: 10,
  text_y_percent: 55,
  text_position: "bottom",
  text_vertical_align: "center",
  font_family: "Nunito",
  font_size_pt: 12,
  line_height: 1.35,
  font_color: "#333333",
  font_weight: "normal",
  text_align: "center",
  background_color: "#F5F5F5",
  // Text stroke
  text_stroke_enabled: false,
  text_stroke_color: "#000000",
  text_stroke_width: 1,
  // Text background gradient
  text_bg_enabled: false,
  text_bg_color: "#000000",
  text_bg_opacity: 120,
  text_bg_shape: "soft_vignette",
  text_bg_blur: 30,
  text_bg_extend_top: 30,
  text_bg_extend_bottom: 10,
  text_bg_extend_sides: 10,
  text_bg_intensity: 100,
  // Cover title (arka kapakta kullanılmaz ama interface gerektirir)
  cover_title_enabled: false,
  cover_title_font_family: "Lobster",
  cover_title_font_size_pt: 48,
  cover_title_font_color: "#FFD700",
  cover_title_arc_intensity: 35,
  cover_title_shadow_enabled: true,
  cover_title_shadow_color: "#000000",
  cover_title_shadow_offset: 3,
  cover_title_stroke_width: 2,
  cover_title_stroke_color: "#8B6914",
  cover_title_y_percent: 5,
  cover_title_preset: "premium",
  cover_title_effect: "gold_shine",
  cover_title_letter_spacing: 0,
  is_active: true,
};

const defaultInnerTemplate: PageTemplate = {
  name: "İç Sayfa",
  page_type: "inner",
  // Your dimensions: 210 x 297 mm
  page_width_mm: 297,
  page_height_mm: 210,
  bleed_mm: 3,
  // Large image on top
  image_width_percent: 90,
  image_height_percent: 55,
  image_x_percent: 5,
  image_y_percent: 5,
  image_aspect_ratio: "16:9",
  // Text visibility
  text_enabled: true,
  // Text below image
  text_width_percent: 90,
  text_height_percent: 30,
  text_x_percent: 5,
  text_y_percent: 65,
  text_position: "bottom",
  text_vertical_align: "bottom",
  font_family: "Nunito",
  font_size_pt: 16,
  line_height: 1.35,
  font_color: "#333333",
  font_weight: "normal",
  text_align: "center",
  background_color: "#FFFFFF",
  // Text stroke
  text_stroke_enabled: false,
  text_stroke_color: "#000000",
  text_stroke_width: 1,
  // Text background gradient
  text_bg_enabled: true,
  text_bg_color: "#FFFFFF",
  text_bg_opacity: 230,
  text_bg_shape: "cloud",
  text_bg_blur: 50,
  text_bg_extend_top: 60,
  text_bg_extend_bottom: 15,
  text_bg_extend_sides: 10,
  text_bg_intensity: 100,
  // Cover title (iç sayfada kullanılmaz ama interface gerektirir)
  cover_title_enabled: false,
  cover_title_font_family: "Lobster",
  cover_title_font_size_pt: 48,
  cover_title_font_color: "#FFD700",
  cover_title_arc_intensity: 35,
  cover_title_shadow_enabled: true,
  cover_title_shadow_color: "#000000",
  cover_title_shadow_offset: 3,
  cover_title_stroke_width: 2,
  cover_title_stroke_color: "#8B6914",
  cover_title_y_percent: 5,
  cover_title_preset: "premium",
  cover_title_effect: "gold_shine",
  cover_title_letter_spacing: 0,
  is_active: true,
};

const defaultDedicationTemplate: PageTemplate = {
  name: "Karşılama Sayfası",
  page_type: "dedication",
  page_width_mm: 297,
  page_height_mm: 210,
  bleed_mm: 3,
  image_width_percent: 0,
  image_height_percent: 0,
  image_x_percent: 0,
  image_y_percent: 0,
  image_aspect_ratio: "1:1",
  text_enabled: true,
  text_width_percent: 70,
  text_height_percent: 50,
  text_x_percent: 15,
  text_y_percent: 25,
  text_position: "overlay",
  text_vertical_align: "center",
  font_family: "Nunito",
  font_size_pt: 28,
  line_height: 1.35,
  font_color: "#5B4636",
  font_weight: "normal",
  text_align: "center",
  background_color: "#FFF5E6",
  text_stroke_enabled: false,
  text_stroke_color: "#000000",
  text_stroke_width: 0,
  text_bg_enabled: false,
  text_bg_color: "#000000",
  text_bg_opacity: 0,
  text_bg_shape: "soft_vignette",
  text_bg_blur: 0,
  text_bg_extend_top: 30,
  text_bg_extend_bottom: 10,
  text_bg_extend_sides: 10,
  text_bg_intensity: 100,
  cover_title_enabled: false,
  cover_title_font_family: "Lobster",
  cover_title_font_size_pt: 48,
  cover_title_font_color: "#FFD700",
  cover_title_arc_intensity: 0,
  cover_title_shadow_enabled: false,
  cover_title_shadow_color: "#000000",
  cover_title_shadow_offset: 0,
  cover_title_stroke_width: 0,
  cover_title_stroke_color: "#8B6914",
  cover_title_y_percent: 5,
  cover_title_preset: "premium",
  cover_title_effect: "none",
  cover_title_letter_spacing: 0,
  dedication_default_text: "Bu kitap {child_name} için özel hazırlanmıştır ✨",
  is_active: true,
};

export default function AdminConfigPage() {
  const [pageTemplates, setPageTemplates] = useState<PageTemplate[]>([]);
  const [aiConfigs, setAIConfigs] = useState<AIConfig[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [activeTab, setActiveTab] = useState("cover");

  // Separate states for each page type
  const [coverTemplate, setCoverTemplate] = useState<PageTemplate>({ ...defaultCoverTemplate });
  const [backCoverTemplate, setBackCoverTemplate] = useState<PageTemplate>({
    ...defaultBackCoverTemplate,
  });
  const [innerTemplate, setInnerTemplate] = useState<PageTemplate>({ ...defaultInnerTemplate });
  const [dedicationTemplate, setDedicationTemplate] = useState<PageTemplate>({
    ...defaultDedicationTemplate,
  });
  const [defaultIntroText, setDefaultIntroText] = useState(
    "{story_title} macerasına hoş geldin, sevgili {child_name}!\n\nBu özel yolculukta seni harika sürprizler bekliyor. Her sayfayı çevirirken gözlerin parlasın, hayal gücün kanatlanasın!"
  );
  const [savingIntroText, setSavingIntroText] = useState(false);

  const [newAIConfig, setNewAIConfig] = useState({
    name: "",
    description: "",
    image_provider: "gemini_flash",
    image_model: "gemini-2.0-flash-exp-image-generation",
    image_width: 1024,
    image_height: 1024,
    story_provider: "gemini",
    story_model: "gemini-2.0-flash",
    story_temperature: 0.7,
  });

  const [invoiceSettings, setInvoiceSettings] = useState({
    invoice_company_name: "",
    invoice_company_address: "",
    invoice_company_tax_id: "",
    invoice_company_tax_office: "",
    invoice_company_phone: "",
    invoice_company_email: "",
  });
  const [savingInvoice, setSavingInvoice] = useState(false);

  const router = useRouter();
  const { toast } = useToast();

  useAdminAuth();

  useEffect(() => {
    fetchData();
    fetchInvoiceSettings();
  }, []);




  const fetchInvoiceSettings = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/admin/settings/invoice`, {
        headers: getAuthHeaders(),
      });
      if (res.ok) {
        const data = await res.json();
        setInvoiceSettings(data);
      }
    } catch {
      // non-fatal
    }
  };

  const saveInvoiceSettings = async () => {
    setSavingInvoice(true);
    try {
      const res = await fetch(`${API_BASE_URL}/admin/settings/invoice`, {
        method: "PUT",
        headers: getAuthHeaders(),
        body: JSON.stringify(invoiceSettings),
      });
      if (res.ok) {
        toast({ title: "Fatura ayarları kaydedildi" });
      } else {
        const err = await res.json();
        toast({ title: "Hata", description: err.detail || "Kayıt başarısız", variant: "destructive" });
      }
    } catch {
      toast({ title: "Hata", description: "Bağlantı hatası", variant: "destructive" });
    } finally {
      setSavingInvoice(false);
    }
  };

  const fetchData = async () => {
    try {
      const [pageRes, aiRes, introRes] = await Promise.all([
        fetch(`${API_BASE_URL}/admin/book-config/page-templates`, {
          headers: getAuthHeaders(),
        }),
        fetch(`${API_BASE_URL}/admin/book-config/ai-configs`, {
          headers: getAuthHeaders(),
        }),
        fetch(`${API_BASE_URL}/admin/settings/app-setting/default_intro_text`, {
          headers: getAuthHeaders(),
        }),
      ]);

      if (pageRes.ok) {
        const templates = await pageRes.json();
        setPageTemplates(templates);

        // Backend compose uses "en son güncellenen" şablon (updated_at desc). Aynı şablonu forma yükle.
        const latest = (arr: PageTemplate[], pageType: string) =>
          arr
            .filter((t) => t.page_type === pageType)
            .sort((a, b) => (b.updated_at || "").localeCompare(a.updated_at || ""))[0];

        const cover = latest(templates, "cover");
        const back = latest(templates, "back");
        const inner = latest(templates, "inner");
        const dedication = latest(templates, "dedication");

        if (cover) setCoverTemplate({ ...defaultCoverTemplate, ...cover });
        if (back) setBackCoverTemplate({ ...defaultBackCoverTemplate, ...back });
        if (inner) setInnerTemplate({ ...defaultInnerTemplate, ...inner });
        if (dedication) setDedicationTemplate({ ...defaultDedicationTemplate, ...dedication });
      }
      if (aiRes.ok) setAIConfigs(await aiRes.json());
      if (introRes.ok) {
        const introData = await introRes.json();
        if (introData.value) setDefaultIntroText(introData.value);
      }
    } catch (error) {
      console.error("Failed to fetch config:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleAuthError = (response: Response) => {
    if (response.status === 401) {
      toast({
        title: "Oturum Suresi Doldu",
        description: "Lutfen tekrar giris yapin",
        variant: "destructive",
      });
      localStorage.removeItem("token");
      localStorage.removeItem("user");
      router.push("/auth/login");
      return true;
    }
    return false;
  };

  const savePageTemplate = async (template: PageTemplate, pageType: string) => {
    setSaving(true);
    try {
      // Düzenlediğimiz şablon = formdaki id varsa onu bul, yoksa bu page_type için ilk kayıt
      const existing = template.id
        ? pageTemplates.find((t) => t.id === template.id)
        : pageTemplates.find((t) => t.page_type === pageType);

      const url = existing
        ? `${API_BASE_URL}/admin/book-config/page-templates/${existing.id}`
        : `${API_BASE_URL}/admin/book-config/page-templates`;

      const method = existing ? "PATCH" : "POST";

      const response = await fetch(url, {
        method,
        headers: getAuthHeaders(),
        body: JSON.stringify({ ...template, page_type: pageType }),
      });

      // Check for auth error first
      if (handleAuthError(response)) {
        return;
      }

      if (response.ok) {
        const pageNames: Record<string, string> = {
          cover: "Ön Kapak",
          back: "Arka Kapak",
          inner: "İç Sayfa",
          dedication: "Karşılama Sayfası",
        };
        toast({
          title: "Basarili",
          description: `${pageNames[pageType]} sablonu kaydedildi`,
        });
        fetchData();
      } else {
        const error = await response.json();
        throw new Error(error.detail || "Hata olustu");
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : "Hata oluştu";
      toast({ title: "Hata", description: message, variant: "destructive" });
    } finally {
      setSaving(false);
    }
  };

  const createAIConfig = async () => {
    setSaving(true);
    try {
      const response = await fetch(`${API_BASE_URL}/admin/book-config/ai-configs`, {
        method: "POST",
        headers: getAuthHeaders(),
        body: JSON.stringify(newAIConfig),
      });

      if (response.ok) {
        toast({ title: "Başarılı", description: "AI yapılandırması oluşturuldu" });
        fetchData();
      } else {
        const error = await response.json();
        throw new Error(error.detail || "Hata oluştu");
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : "Hata oluştu";
      toast({ title: "Hata", description: message, variant: "destructive" });
    } finally {
      setSaving(false);
    }
  };

  const deleteAIConfig = async (id: string) => {
    if (!confirm("Bu yapılandırmayı silmek istediğinize emin misiniz?")) return;

    try {
      const response = await fetch(`${API_BASE_URL}/admin/book-config/ai-configs/${id}`, {
        method: "DELETE",
        headers: getAuthHeaders(),
      });

      if (response.ok) {
        toast({ title: "Başarılı", description: "Yapılandırma silindi" });
        fetchData();
      }
    } catch (error) {
      toast({
        title: "Hata",
        description: "Silme işlemi başarısız",
        variant: "destructive",
      });
    }
  };

  // Handler for loading template with toast
  const handleLoadTemplate = (template: PageTemplate, pageType: string) => {
    if (pageType === "cover") setCoverTemplate(template);
    else if (pageType === "back") setBackCoverTemplate(template);
    else if (pageType === "inner") setInnerTemplate(template);
    else if (pageType === "dedication") setDedicationTemplate(template);
    toast({ title: "Sablon Yuklendi", description: `"${template.name}" foruma yuklendi` });
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4">
          <h1 className="text-2xl font-bold text-purple-800">Kitap Yapılandırması</h1>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-4 py-8">
        {loading ? (
          <div className="py-8 text-center">Yükleniyor...</div>
        ) : (
          <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
            <TabsList className="grid w-full grid-cols-6">
              <TabsTrigger value="cover">Ön Kapak</TabsTrigger>
              <TabsTrigger value="inner">İç Sayfalar</TabsTrigger>
              <TabsTrigger value="dedication">Karşılama</TabsTrigger>
              <TabsTrigger value="back">Arka Kapak</TabsTrigger>
              <TabsTrigger value="ai">AI Ayarları</TabsTrigger>
              <TabsTrigger value="invoice">Fatura</TabsTrigger>
            </TabsList>

            {/* Cover Template Tab */}
            <TabsContent value="cover">
              <SavedTemplatesList
                pageTemplates={pageTemplates}
                pageType="cover"
                title="On Kapak"
                defaultTemplate={defaultCoverTemplate}
                onLoadTemplate={(t) => handleLoadTemplate(t, "cover")}
              />
              <Card className="mb-6">
                <CardHeader>
                  <CardTitle>On Kapak Sablonu</CardTitle>
                  <CardDescription>
                    Kitabin on kapagi icin gorsel ve baslik yerlesimi -{" "}
                    {coverTemplate.page_width_mm} x {coverTemplate.page_height_mm} mm
                  </CardDescription>
                </CardHeader>
              </Card>
              <PageTemplateForm
                template={coverTemplate}
                setTemplate={setCoverTemplate}
                pageType="cover"
                title="On Kapak"
                saving={saving}
                onSave={() => savePageTemplate(coverTemplate, "cover")}
              />
            </TabsContent>

            {/* Inner Pages Template Tab */}
            <TabsContent value="inner">
              <SavedTemplatesList
                pageTemplates={pageTemplates}
                pageType="inner"
                title="Ic Sayfa"
                defaultTemplate={defaultInnerTemplate}
                onLoadTemplate={(t) => handleLoadTemplate(t, "inner")}
              />
              <Card className="mb-6">
                <CardHeader>
                  <CardTitle>Ic Sayfa Sablonu</CardTitle>
                  <CardDescription>
                    Hikaye sayfalari icin gorsel ve metin yerlesimi - {innerTemplate.page_width_mm}{" "}
                    x {innerTemplate.page_height_mm} mm
                  </CardDescription>
                </CardHeader>
              </Card>
              <PageTemplateForm
                template={innerTemplate}
                setTemplate={setInnerTemplate}
                pageType="inner"
                title="Ic Sayfa"
                saving={saving}
                onSave={() => savePageTemplate(innerTemplate, "inner")}
              />
            </TabsContent>

            {/* Dedication Page Template Tab */}
            <TabsContent value="dedication">
              <SavedTemplatesList
                pageTemplates={pageTemplates}
                pageType="dedication"
                title="Karşılama Sayfası"
                defaultTemplate={defaultDedicationTemplate}
                onLoadTemplate={(t) => handleLoadTemplate(t, "dedication")}
              />
              <Card className="mb-6">
                <CardHeader>
                  <CardTitle>Karşılama Sayfası Şablonu</CardTitle>
                  <CardDescription>
                    Kapaktan sonra yer alan ithaf/karşılama sayfası ayarları
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  {/* Background Color */}
                  <div className="space-y-2">
                    <Label>Arka Plan Rengi</Label>
                    <div className="flex items-center gap-3">
                      <input
                        type="color"
                        value={dedicationTemplate.background_color}
                        onChange={(e) =>
                          setDedicationTemplate({ ...dedicationTemplate, background_color: e.target.value })
                        }
                        className="h-10 w-10 cursor-pointer rounded border"
                      />
                      <Input
                        value={dedicationTemplate.background_color}
                        onChange={(e) =>
                          setDedicationTemplate({ ...dedicationTemplate, background_color: e.target.value })
                        }
                        className="w-32"
                      />
                      {/* Pastel preset buttons */}
                      <div className="flex gap-1">
                        {[
                          { color: "#FFF5E6", label: "Krem" },
                          { color: "#FDE8E8", label: "Pembe" },
                          { color: "#E8F5E9", label: "Yeşil" },
                          { color: "#E3F2FD", label: "Mavi" },
                          { color: "#F3E5F5", label: "Lila" },
                          { color: "#FFFDE7", label: "Sarı" },
                        ].map((preset) => (
                          <button
                            key={preset.color}
                            type="button"
                            title={preset.label}
                            onClick={() =>
                              setDedicationTemplate({ ...dedicationTemplate, background_color: preset.color })
                            }
                            className="h-8 w-8 rounded-full border-2 border-gray-200 transition hover:scale-110"
                            style={{ backgroundColor: preset.color }}
                          />
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* Font Settings */}
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Font</Label>
                      <select
                        value={dedicationTemplate.font_family}
                        onChange={(e) =>
                          setDedicationTemplate({ ...dedicationTemplate, font_family: e.target.value })
                        }
                        className="w-full rounded-md border p-2"
                      >
                        {AVAILABLE_FONTS.map((f) => (
                          <option key={f.value} value={f.value}>
                            {f.label} ({f.category})
                          </option>
                        ))}
                      </select>
                    </div>
                    <div className="space-y-2">
                      <Label>Font Boyutu (pt): {dedicationTemplate.font_size_pt}</Label>
                      <input
                        type="range"
                        min="16"
                        max="120"
                        value={dedicationTemplate.font_size_pt}
                        onChange={(e) =>
                          setDedicationTemplate({
                            ...dedicationTemplate,
                            font_size_pt: Number(e.target.value),
                          })
                        }
                        className="w-full"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Font Rengi</Label>
                      <div className="flex items-center gap-2">
                        <input
                          type="color"
                          value={dedicationTemplate.font_color}
                          onChange={(e) =>
                            setDedicationTemplate({ ...dedicationTemplate, font_color: e.target.value })
                          }
                          className="h-8 w-8 cursor-pointer rounded border"
                        />
                        <Input
                          value={dedicationTemplate.font_color}
                          onChange={(e) =>
                            setDedicationTemplate({ ...dedicationTemplate, font_color: e.target.value })
                          }
                          className="w-32"
                        />
                      </div>
                    </div>
                    <div className="space-y-2">
                      <Label>Metin Hizalama</Label>
                      <select
                        value={dedicationTemplate.text_align}
                        onChange={(e) =>
                          setDedicationTemplate({ ...dedicationTemplate, text_align: e.target.value })
                        }
                        className="w-full rounded-md border p-2"
                      >
                        <option value="left">Sola</option>
                        <option value="center">Ortala</option>
                        <option value="right">Sağa</option>
                      </select>
                    </div>
                  </div>

                  {/* Default Text */}
                  <div className="space-y-2">
                    <Label>Varsayılan Karşılama Metni</Label>
                    <Textarea
                      value={dedicationTemplate.dedication_default_text || ""}
                      onChange={(e) =>
                        setDedicationTemplate({
                          ...dedicationTemplate,
                          dedication_default_text: e.target.value,
                        })
                      }
                      placeholder="Bu kitap {child_name} için özel hazırlanmıştır"
                      rows={3}
                    />
                    <p className="text-xs text-gray-500">
                      <code>{"{child_name}"}</code> yerine çocuğun adı otomatik yazılır.
                    </p>
                  </div>

                  {/* Preview */}
                  <div className="space-y-2">
                    <Label>Önizleme</Label>
                    <div
                      className="mx-auto flex items-center justify-center rounded-lg border-2 border-dashed"
                      style={{
                        backgroundColor: dedicationTemplate.background_color,
                        width: "100%",
                        maxWidth: 500,
                        aspectRatio: "297/210",
                      }}
                    >
                      <p
                        style={{
                          fontFamily: dedicationTemplate.font_family,
                          fontSize: `${Math.min(dedicationTemplate.font_size_pt, 28)}px`,
                          color: dedicationTemplate.font_color,
                          textAlign: dedicationTemplate.text_align as "left" | "center" | "right",
                          padding: "2rem",
                          lineHeight: 1.6,
                        }}
                      >
                        {(dedicationTemplate.dedication_default_text || "Bu kitap {child_name} için özel hazırlanmıştır").replace("{child_name}", "Uras")}
                      </p>
                    </div>
                  </div>

                  <Button
                    onClick={() => savePageTemplate(dedicationTemplate, "dedication")}
                    disabled={saving}
                    className="w-full"
                  >
                    {saving ? "Kaydediliyor..." : "Karşılama 1 Ayarlarını Kaydet"}
                  </Button>
                </CardContent>
              </Card>

              {/* ── Karşılama 2 (Senaryo Tanıtım Sayfası) ── */}
              <Card className="mt-6">
                <CardHeader>
                  <CardTitle className="text-base">Karşılama 2 — Senaryo Tanıtım Sayfası</CardTitle>
                  <p className="text-xs text-gray-500">
                    Kapaktan sonra 2. sayfada gösterilir. Senaryo açıklaması varsa onu kullanır;
                    yoksa buradaki varsayılan metin kullanılır.
                    <br />
                    <code className="bg-gray-100 px-1 rounded">{"{child_name}"}</code> ve{" "}
                    <code className="bg-gray-100 px-1 rounded">{"{story_title}"}</code> otomatik doldurulur.
                  </p>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label>Varsayılan Karşılama 2 Metni</Label>
                    <Textarea
                      value={defaultIntroText}
                      onChange={(e) => setDefaultIntroText(e.target.value)}
                      placeholder="{story_title} macerasına hoş geldin, {child_name}!"
                      rows={5}
                    />
                  </div>
                  <div
                    className="mx-auto flex items-center justify-center rounded-lg border-2 border-dashed bg-amber-50"
                    style={{ width: "100%", maxWidth: 500, aspectRatio: "297/210" }}
                  >
                    <p className="p-8 text-center text-sm leading-relaxed text-slate-700"
                      style={{ fontFamily: dedicationTemplate.font_family }}>
                      {defaultIntroText
                        .replace("{child_name}", "Uras")
                        .replace("{story_title}", "Uzay Macerası")}
                    </p>
                  </div>
                  <Button
                    onClick={async () => {
                      setSavingIntroText(true);
                      try {
                        const res = await fetch(`${API_BASE_URL}/admin/settings/app-setting`, {
                          method: "PUT",
                          headers: getAuthHeaders(),
                          body: JSON.stringify({ key: "default_intro_text", value: defaultIntroText }),
                        });
                        if (res.ok) {
                          toast({ title: "Başarılı", description: "Karşılama 2 metni kaydedildi" });
                        } else {
                          toast({ title: "Hata", description: "Kayıt başarısız", variant: "destructive" });
                        }
                      } catch {
                        toast({ title: "Hata", description: "Bağlantı hatası", variant: "destructive" });
                      } finally {
                        setSavingIntroText(false);
                      }
                    }}
                    disabled={savingIntroText}
                    className="w-full"
                  >
                    {savingIntroText ? "Kaydediliyor..." : "Karşılama 2 Metnini Kaydet"}
                  </Button>
                </CardContent>
              </Card>
            </TabsContent>

            {/* Back Cover Template Tab */}
            <TabsContent value="back">
              <SavedTemplatesList
                pageTemplates={pageTemplates}
                pageType="back"
                title="Arka Kapak"
                defaultTemplate={defaultBackCoverTemplate}
                onLoadTemplate={(t) => handleLoadTemplate(t, "back")}
              />
              <Card className="mb-6">
                <CardHeader>
                  <CardTitle>Arka Kapak Sablonu</CardTitle>
                  <CardDescription>
                    Kitabin arka kapagi icin ozet ve gorsel yerlesimi -{" "}
                    {backCoverTemplate.page_width_mm} x {backCoverTemplate.page_height_mm} mm
                  </CardDescription>
                </CardHeader>
              </Card>
              <PageTemplateForm
                template={backCoverTemplate}
                setTemplate={setBackCoverTemplate}
                pageType="back"
                title="Arka Kapak"
                saving={saving}
                onSave={() => savePageTemplate(backCoverTemplate, "back")}
              />
            </TabsContent>

            {/* AI Config Tab */}
            <TabsContent value="ai" className="space-y-6">
              {/* Info Card */}
              <Card className="border-green-200 bg-green-50">
                <CardHeader>
                  <CardTitle className="text-green-800">Dinamik Cozunurluk Sistemi Aktif</CardTitle>
                </CardHeader>
                <CardContent className="text-sm text-green-700">
                  <p>
                    Gorsel boyutlari artik <strong>PageTemplate</strong> boyutlarindan otomatik
                    hesaplaniyor. Asagidaki AI boyut ayarlari sadece referans icin gosteriliyor.
                  </p>
                  <ul className="mt-2 list-inside list-disc space-y-1">
                    <li>AI max 1024px uretir (API limiti)</li>
                    <li>Real-ESRGAN ile 2x veya 4x upscale yapilir</li>
                    <li>LANCZOS ile hedef boyuta resize edilir</li>
                    <li>Sonuc: 300 DPI baski kalitesi</li>
                  </ul>
                </CardContent>
              </Card>

              {/* Fal.ai Info Card */}
              <Card className="border-purple-200 bg-purple-50">
                <CardHeader>
                  <CardTitle className="text-purple-800">
                    🎨 Fal.ai Flux PuLID - Yüz Tutarlılığı
                  </CardTitle>
                </CardHeader>
                <CardContent className="text-sm text-purple-700">
                  <p className="mb-2">
                    <strong>Fal.ai Flux PuLID</strong> seçildiğinde çocuk kitapları için SOTA
                    (State-of-the-Art) yüz benzerliği sağlanır:
                  </p>
                  <ul className="list-inside list-disc space-y-1">
                    <li>
                      <strong>PuLID:</strong> Yüklenen fotoğraftan yüz kimliği korunur
                    </li>
                    <li>
                      <strong>Kıyafet Tutarlılığı:</strong> Aynı kıyafet tüm sayfalarda
                    </li>
                    <li>
                      <strong>Flux Modeli:</strong> Doğal dil promptları ile yüksek kalite
                    </li>
                    <li>
                      <strong>id_weight:</strong> 0.8 (yüz benzerlik gücü)
                    </li>
                  </ul>
                  <p className="mt-3 rounded bg-purple-100 p-2 text-xs">
                    💡 Gemini generic yüzler üretirken, Fal.ai PuLID çocuğun gerçek yüzünü korur.
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>AI Yapilandirmasi</CardTitle>
                  <CardDescription>
                    Gorsel ve hikaye uretimi icin yapay zeka ayarlari
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4 md:grid-cols-3">
                    <div className="space-y-2">
                      <Label>Yapılandırma Adı</Label>
                      <Input
                        value={newAIConfig.name}
                        onChange={(e) => setNewAIConfig({ ...newAIConfig, name: e.target.value })}
                        placeholder="Örn: Varsayılan AI"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Görsel Sağlayıcı</Label>
                      <select
                        className="w-full rounded-md border p-2"
                        value={newAIConfig.image_provider}
                        onChange={(e) => {
                          const provider = e.target.value;
                          let model = newAIConfig.image_model;
                          // Auto-select appropriate model for provider
                          if (provider === "fal") {
                            model = "fal-ai/flux-pulid";
                          } else if (provider === "gemini_flash") {
                            model = "gemini-2.0-flash-exp-image-generation";
                          } else if (provider === "gemini") {
                            model = "imagen-3.0-generate-002";
                          }
                          setNewAIConfig({
                            ...newAIConfig,
                            image_provider: provider,
                            image_model: model,
                          });
                        }}
                      >
                        <option value="gemini_flash">Gemini Flash (Hızlı)</option>
                        <option value="gemini">Gemini Imagen (Kaliteli)</option>
                        <option value="fal">Fal.ai Flux PuLID (Yüz Tutarlılığı)</option>
                      </select>
                    </div>
                    <div className="space-y-2">
                      <Label>Görsel Model</Label>
                      {newAIConfig.image_provider === "fal" ? (
                        <select
                          className="w-full rounded-md border p-2"
                          value={newAIConfig.image_model}
                          onChange={(e) =>
                            setNewAIConfig({ ...newAIConfig, image_model: e.target.value })
                          }
                        >
                          <option value="fal-ai/flux-pulid">Flux PuLID (Yüz Tutarlılığı)</option>
                          <option value="fal-ai/flux/dev">Flux Dev (Yüksek Kalite)</option>
                          <option value="fal-ai/flux/schnell">Flux Schnell (Hızlı)</option>
                          <option value="fal-ai/flux-lora">Flux LoRA (Özel Stiller)</option>
                        </select>
                      ) : (
                        <Input
                          value={newAIConfig.image_model}
                          onChange={(e) =>
                            setNewAIConfig({ ...newAIConfig, image_model: e.target.value })
                          }
                        />
                      )}
                    </div>
                    <div className="space-y-2">
                      <Label>
                        Gorsel Genislik (px){" "}
                        <span className="text-xs text-gray-400">(referans)</span>
                      </Label>
                      <Input
                        type="number"
                        value={newAIConfig.image_width}
                        onChange={(e) =>
                          setNewAIConfig({
                            ...newAIConfig,
                            image_width: parseInt(e.target.value),
                          })
                        }
                        className="bg-gray-50"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>
                        Gorsel Yukseklik (px){" "}
                        <span className="text-xs text-gray-400">(referans)</span>
                      </Label>
                      <Input
                        type="number"
                        value={newAIConfig.image_height}
                        onChange={(e) =>
                          setNewAIConfig({
                            ...newAIConfig,
                            image_height: parseInt(e.target.value),
                          })
                        }
                        className="bg-gray-50"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Hikaye Yaratıcılık (0-2)</Label>
                      <Input
                        type="number"
                        step="0.1"
                        min="0"
                        max="2"
                        value={newAIConfig.story_temperature}
                        onChange={(e) =>
                          setNewAIConfig({
                            ...newAIConfig,
                            story_temperature: parseFloat(e.target.value),
                          })
                        }
                      />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label>Açıklama</Label>
                    <Textarea
                      value={newAIConfig.description || ""}
                      onChange={(e) =>
                        setNewAIConfig({ ...newAIConfig, description: e.target.value })
                      }
                      placeholder="Bu yapılandırma hakkında notlar..."
                    />
                  </div>
                  <Button onClick={createAIConfig} disabled={saving || !newAIConfig.name}>
                    {saving ? "Kaydediliyor..." : "Yapılandırma Oluştur"}
                  </Button>
                </CardContent>
              </Card>

              {/* Existing AI Configs */}
              <Card>
                <CardHeader>
                  <CardTitle>Kayıtlı AI Yapılandırmaları</CardTitle>
                </CardHeader>
                <CardContent>
                  {aiConfigs.length === 0 ? (
                    <p className="py-4 text-center text-gray-500">
                      Henüz yapılandırma oluşturulmamış
                    </p>
                  ) : (
                    <div className="space-y-2">
                      {aiConfigs.map((c) => (
                        <div
                          key={c.id}
                          className="flex items-center justify-between rounded-lg bg-gray-50 p-4"
                        >
                          <div>
                            <p className="font-medium">{c.name}</p>
                            <p className="text-sm text-gray-500">
                              {c.image_provider} | {c.image_width}x{c.image_height}px | Yaratıcılık:{" "}
                              {c.story_temperature}
                            </p>
                          </div>
                          <div className="flex gap-2">
                            {c.is_default && (
                              <span className="rounded bg-green-100 px-2 py-1 text-xs text-green-800">
                                Varsayılan
                              </span>
                            )}
                            <Button
                              size="sm"
                              variant="destructive"
                              onClick={() => deleteAIConfig(c.id)}
                            >
                              Sil
                            </Button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            {/* Invoice Settings Tab */}
            <TabsContent value="invoice" className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Fatura Şirket Bilgileri</CardTitle>
                  <CardDescription>
                    Müşterilere gönderilen PDF faturalarda görünecek firma bilgileri.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                    <div className="space-y-2">
                      <Label htmlFor="inv_company_name">Firma Adı</Label>
                      <Input
                        id="inv_company_name"
                        value={invoiceSettings.invoice_company_name}
                        onChange={(e) =>
                          setInvoiceSettings((s) => ({ ...s, invoice_company_name: e.target.value }))
                        }
                        placeholder="Benim Masalım"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="inv_email">E-posta</Label>
                      <Input
                        id="inv_email"
                        type="email"
                        value={invoiceSettings.invoice_company_email}
                        onChange={(e) =>
                          setInvoiceSettings((s) => ({ ...s, invoice_company_email: e.target.value }))
                        }
                        placeholder="info@benimmasalim.com"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="inv_phone">Telefon</Label>
                      <Input
                        id="inv_phone"
                        value={invoiceSettings.invoice_company_phone}
                        onChange={(e) =>
                          setInvoiceSettings((s) => ({ ...s, invoice_company_phone: e.target.value }))
                        }
                        placeholder="+90 212 000 00 00"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="inv_tax_id">Vergi Kimlik No (VKN)</Label>
                      <Input
                        id="inv_tax_id"
                        value={invoiceSettings.invoice_company_tax_id}
                        onChange={(e) =>
                          setInvoiceSettings((s) => ({ ...s, invoice_company_tax_id: e.target.value }))
                        }
                        placeholder="1234567890"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="inv_tax_office">Vergi Dairesi</Label>
                      <Input
                        id="inv_tax_office"
                        value={invoiceSettings.invoice_company_tax_office}
                        onChange={(e) =>
                          setInvoiceSettings((s) => ({ ...s, invoice_company_tax_office: e.target.value }))
                        }
                        placeholder="Beşiktaş V.D."
                      />
                    </div>
                    <div className="space-y-2 md:col-span-2">
                      <Label htmlFor="inv_address">Firma Adresi</Label>
                      <Input
                        id="inv_address"
                        value={invoiceSettings.invoice_company_address}
                        onChange={(e) =>
                          setInvoiceSettings((s) => ({ ...s, invoice_company_address: e.target.value }))
                        }
                        placeholder="Örnek Mah. Örnek Cad. No:1 İstanbul"
                      />
                    </div>
                  </div>
                  <div className="flex justify-end pt-2">
                    <Button onClick={saveInvoiceSettings} disabled={savingInvoice}>
                      {savingInvoice ? "Kaydediliyor..." : "Kaydet"}
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        )}
      </main>
    </div>
  );
}
