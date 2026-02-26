"use client";

import { useState, useEffect, useRef, forwardRef, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import HTMLFlipBook from "react-pageflip";
import { motion, AnimatePresence } from "framer-motion";
import {
  Plus,
  Pencil,
  Trash2,
  Copy,
  Eye,
  Upload,
  X,
  ChevronLeft,
  Book,
  Ruler,
  DollarSign,
  Image as ImageIcon,
  Settings2,
  LayoutGrid,
  RotateCw,
  Check,
  AlertCircle,
  Sparkles,
  BookOpen,
  Monitor,
  Star,
  Video,
  Gift,
  TrendingUp,
  MessageSquare,
  ListChecks,
  Palette,
  Headphones,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Slider } from "@/components/ui/slider";
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
import { API_BASE_URL } from "@/lib/api";

// ============ TYPES ============
interface Template {
  id: string;
  name: string;
  page_width_mm?: number;
  page_height_mm?: number;
}

interface AIConfig {
  id: string;
  name: string;
  image_provider: string;
}

interface Product {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  short_description: string | null;
  // Product Type
  product_type?: string; // "story_book" | "coloring_book" | "audio_addon"
  type_specific_data?: Record<string, unknown> | null;
  // Template objects (from list endpoint)
  cover_template: Template | null;
  inner_template: Template | null;
  back_template: Template | null;
  ai_config: AIConfig | null;
  // Template IDs (for form binding)
  cover_template_id?: string | null;
  inner_template_id?: string | null;
  back_template_id?: string | null;
  ai_config_id?: string | null;
  // Page settings
  default_page_count: number;
  min_page_count: number;
  max_page_count: number;
  // Paper & Cover
  paper_type: string;
  paper_finish: string;
  cover_type: string;
  lamination: string | null;
  // Pricing
  base_price: number;
  discounted_price?: number | null;
  extra_page_price: number;
  discount_percentage?: number | null;
  // Status
  is_active: boolean;
  is_featured: boolean;
  display_order: number;
  // Media
  thumbnail_url: string | null;
  video_url?: string | null;
  sample_images?: string[];
  orientation?: string;
  // Marketing & Urgency
  promo_badge?: string | null;
  promo_end_date?: string | null;
  promo_days_remaining?: number | null;
  is_gift_wrapped?: boolean;
  // Social Proof
  rating?: number | null;
  review_count?: number;
  social_proof_text?: string | null;
  // Features
  feature_list?: string[];
}

interface TemplateOptions {
  cover_templates: Template[];
  inner_templates: Template[];
  back_templates: Template[];
  ai_configs: AIConfig[];
}

interface ScenarioForProduct {
  id: string;
  name: string;
  thumbnail_url: string;
  tagline?: string | null;
  marketing_badge?: string | null;
}

// ============ FORM SCHEMA ============
const productSchema = z.object({
  // Basic Info
  name: z.string().min(1, "Ürün adı zorunludur"),
  slug: z.string().optional(),
  description: z.string().optional(),
  short_description: z.string().optional(),
  // Product Type
  product_type: z.string().default("story_book"),
  // Template references
  cover_template_id: z.string().optional().nullable(),
  inner_template_id: z.string().optional().nullable(),
  back_template_id: z.string().optional().nullable(),
  ai_config_id: z.string().optional().nullable(),
  // Page settings
  default_page_count: z.number().min(4).max(64),
  min_page_count: z.number().min(4).max(64),
  max_page_count: z.number().min(4).max(64),
  // Physical dimensions (for reference/display)
  width_mm: z.number().min(50).max(500),
  height_mm: z.number().min(50).max(500),
  // Paper & Cover
  paper_type: z.string(),
  paper_finish: z.string(),
  cover_type: z.string(),
  lamination: z.string().optional(),
  // Pricing
  base_price: z.number().min(1),
  discounted_price: z.number().optional().nullable(),
  extra_page_price: z.number().min(0),
  // Status
  is_active: z.boolean(),
  is_featured: z.boolean(),
  display_order: z.number(),
  // Media
  thumbnail_url: z.string().optional().nullable(),
  video_url: z.string().optional().nullable(),
  orientation: z.string().optional(),
  // Marketing & Urgency
  promo_badge: z.string().optional().nullable(),
  promo_end_date: z.string().optional().nullable(),
  is_gift_wrapped: z.boolean().optional(),
  // Social Proof
  rating: z.number().min(0).max(5).optional().nullable(),
  review_count: z.number().min(0).optional(),
  social_proof_text: z.string().optional().nullable(),
});

type ProductFormData = z.infer<typeof productSchema>;

// ============ PAGE COMPONENT FOR FLIPBOOK ============
const FlipBookPage = forwardRef<HTMLDivElement, { imageUrl: string; pageNumber: number }>(
  ({ imageUrl, pageNumber }, ref) => {
    return (
      <div ref={ref} className="h-full w-full bg-white shadow-md">
        {imageUrl ? (
          <img
            src={imageUrl}
            alt={`Sayfa ${pageNumber}`}
            className="h-full w-full object-cover"
            draggable={false}
          />
        ) : (
          <div className="flex h-full w-full items-center justify-center bg-gradient-to-br from-amber-50 to-amber-100">
            <div className="text-center text-amber-400">
              <BookOpen className="mx-auto mb-2 h-8 w-8 opacity-50" />
              <p className="text-xs">Sayfa {pageNumber + 1}</p>
            </div>
          </div>
        )}
      </div>
    );
  }
);
FlipBookPage.displayName = "FlipBookPage";

// ============ DIMENSION CALCULATOR ============
function DimensionCalculator({ width, height }: { width: number; height: number }) {
  const DPI = 300;
  const pixelWidth = Math.round((width / 25.4) * DPI);
  const pixelHeight = Math.round((height / 25.4) * DPI);
  const orientation = width > height ? "Yatay" : width < height ? "Dikey" : "Kare";
  const aspectRatio = (width / height).toFixed(2);

  return (
    <div className="mt-3 rounded-lg border border-blue-200 bg-gradient-to-r from-blue-50 to-indigo-50 p-4">
      <div className="mb-3 flex items-center gap-2">
        <Monitor className="h-4 w-4 text-blue-600" />
        <span className="text-sm font-medium text-blue-800">Çıktı Hesaplaması</span>
      </div>
      <div className="grid grid-cols-2 gap-3 text-sm">
        <div>
          <p className="text-xs text-gray-500">Hedef Çözünürlük</p>
          <p className="font-mono font-semibold text-blue-700">
            {pixelWidth} × {pixelHeight} px
          </p>
        </div>
        <div>
          <p className="text-xs text-gray-500">DPI / Oryantasyon</p>
          <p className="font-mono font-semibold text-blue-700">
            {DPI} DPI • {orientation}
          </p>
        </div>
        <div>
          <p className="text-xs text-gray-500">En-Boy Oranı</p>
          <p className="font-mono font-semibold text-blue-700">{aspectRatio}:1</p>
        </div>
        <div>
          <p className="text-xs text-gray-500">Tahmini Dosya Boyutu</p>
          <p className="font-mono font-semibold text-blue-700">
            ~{((pixelWidth * pixelHeight * 3) / 1024 / 1024).toFixed(1)} MB
          </p>
        </div>
      </div>
    </div>
  );
}

// ============ FLIPBOOK PREVIEW ============
function FlipbookPreview({
  images,
  width,
  height,
  bookThickness,
}: {
  images: string[];
  width: number;
  height: number;
  bookThickness: number;
}) {
  const bookRef = useRef<HTMLDivElement | null>(null);
  const isLandscape = width > height;

  // Calculate display dimensions (max 400px width)
  const maxWidth = 350;
  const scale = maxWidth / width;
  const displayWidth = Math.round(width * scale);
  const displayHeight = Math.round(height * scale);

  // Ensure we have at least 4 pages for the flipbook
  const pageImages =
    images.length > 0
      ? [...images, ...Array(Math.max(0, 4 - images.length)).fill("")]
      : ["", "", "", ""];

  return (
    <div className="relative">
      {/* Book shadow */}
      <div
        className="absolute -bottom-4 left-1/2 -translate-x-1/2 rounded-[50%] opacity-40"
        style={{
          width: displayWidth * 1.8,
          height: 20,
          background: "radial-gradient(ellipse at center, rgba(0,0,0,0.5) 0%, transparent 70%)",
          filter: "blur(4px)",
        }}
      />

      {/* Book container with 3D effect */}
      <div
        className="relative mx-auto"
        style={{
          perspective: "1500px",
          transformStyle: "preserve-3d",
        }}
      >
        {/* Book spine effect */}
        <div
          className="absolute left-1/2 top-0 z-10 -translate-x-1/2 rounded-sm bg-gradient-to-r from-amber-900 via-amber-800 to-amber-900"
          style={{
            width: bookThickness * 3,
            height: displayHeight,
            transform: `translateZ(-${bookThickness}px)`,
            boxShadow: "inset 0 0 10px rgba(0,0,0,0.3)",
          }}
        />

        {/* Flipbook */}
        <div
          className="relative overflow-hidden rounded-lg bg-white"
          style={{
            boxShadow: `
              0 ${bookThickness}px ${bookThickness * 2}px rgba(0,0,0,0.15),
              0 4px 6px rgba(0,0,0,0.1),
              inset 0 0 0 1px rgba(0,0,0,0.05)
            `,
          }}
        >
          <HTMLFlipBook
            ref={bookRef}
            width={displayWidth / 2}
            height={displayHeight}
            size="fixed"
            minWidth={displayWidth / 2}
            maxWidth={displayWidth / 2}
            minHeight={displayHeight}
            maxHeight={displayHeight}
            showCover={true}
            mobileScrollSupport={true}
            className="flipbook-preview"
            style={{}}
            startPage={0}
            drawShadow={true}
            flippingTime={600}
            usePortrait={!isLandscape}
            startZIndex={0}
            autoSize={false}
            maxShadowOpacity={0.4}
            showPageCorners={true}
            disableFlipByClick={false}
            swipeDistance={20}
            clickEventForward={true}
            useMouseEvents={true}
          >
            {pageImages.map((img, idx) => (
              <FlipBookPage key={idx} imageUrl={img} pageNumber={idx} />
            ))}
          </HTMLFlipBook>
        </div>
      </div>

      {/* Instructions */}
      {images.length > 0 && (
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="mt-4 text-center text-xs text-gray-400"
        >
          Sayfaları çevirmek için tıklayın veya sürükleyin
        </motion.p>
      )}
    </div>
  );
}

// ============ IMAGE UPLOAD DROPZONE ============
// Helper function to compress image
function compressImage(file: File, maxWidth: number = 800, quality: number = 0.7): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const img = new window.Image();
      img.onload = () => {
        const canvas = document.createElement("canvas");
        let width = img.width;
        let height = img.height;

        // Scale down if too large
        if (width > maxWidth) {
          height = (height * maxWidth) / width;
          width = maxWidth;
        }

        canvas.width = width;
        canvas.height = height;

        const ctx = canvas.getContext("2d");
        if (!ctx) {
          reject(new Error("Canvas context not available"));
          return;
        }

        ctx.drawImage(img, 0, 0, width, height);
        const compressedDataUrl = canvas.toDataURL("image/jpeg", quality);
        resolve(compressedDataUrl);
      };
      img.onerror = () => reject(new Error("Image load failed"));
      img.src = e.target?.result as string;
    };
    reader.onerror = () => reject(new Error("File read failed"));
    reader.readAsDataURL(file);
  });
}

// Single image uploader for thumbnail
function SingleImageUploader({
  value,
  onChange,
  label: _label = "Görsel Yükle",
}: {
  value: string | null | undefined;
  onChange: (url: string | null) => void;
  label?: string;
}) {
  const [isDragging, setIsDragging] = useState(false);
  const [isCompressing, setIsCompressing] = useState(false);
  const [urlInput, setUrlInput] = useState("");
  const [showUrlInput, setShowUrlInput] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFile = useCallback(
    async (file: File | null) => {
      if (!file || !file.type.startsWith("image/")) return;

      setIsCompressing(true);
      try {
        const compressedImage = await compressImage(file, 800, 0.7);
        onChange(compressedImage);
      } catch (error) {
        console.error("Image compression failed:", error);
        // Fallback to original
        const reader = new FileReader();
        reader.onload = (e) => onChange(e.target?.result as string);
        reader.readAsDataURL(file);
      } finally {
        setIsCompressing(false);
      }
    },
    [onChange]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  const handleAddUrl = () => {
    if (urlInput.trim() && (urlInput.startsWith("http://") || urlInput.startsWith("https://"))) {
      onChange(urlInput.trim());
      setUrlInput("");
      setShowUrlInput(false);
    }
  };

  if (value) {
    return (
      <div className="group relative">
        <div className="h-40 w-full overflow-hidden rounded-xl border-2 border-gray-200 bg-gray-50">
          <img
            src={value}
            alt="Thumbnail"
            className="h-full w-full object-cover"
            onError={(e) => {
              (e.target as HTMLImageElement).src =
                "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='100' height='100'%3E%3Crect fill='%23f3f4f6' width='100' height='100'/%3E%3Ctext x='50%25' y='50%25' fill='%239ca3af' text-anchor='middle' dy='.3em' font-size='12'%3EHata%3C/text%3E%3C/svg%3E";
            }}
          />
        </div>
        <div className="absolute inset-0 flex items-center justify-center gap-2 rounded-xl bg-black/50 opacity-0 transition-opacity group-hover:opacity-100">
          <Button
            type="button"
            size="sm"
            variant="secondary"
            onClick={() => fileInputRef.current?.click()}
          >
            <Upload className="mr-1 h-4 w-4" />
            Değiştir
          </Button>
          <Button type="button" size="sm" variant="destructive" onClick={() => onChange(null)}>
            <X className="h-4 w-4" />
          </Button>
        </div>
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          onChange={(e) => handleFile(e.target.files?.[0] || null)}
          className="hidden"
        />
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {/* Upload Zone */}
      <div
        onClick={() => fileInputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        className={`
          cursor-pointer rounded-xl border-2 border-dashed p-6 text-center transition-all
          ${
            isDragging
              ? "border-purple-500 bg-purple-50"
              : "border-gray-300 hover:border-purple-400 hover:bg-purple-50/50"
          }
          ${isCompressing ? "pointer-events-none opacity-50" : ""}
        `}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          onChange={(e) => handleFile(e.target.files?.[0] || null)}
          className="hidden"
        />
        {isCompressing ? (
          <div className="flex flex-col items-center gap-2">
            <RotateCw className="h-8 w-8 animate-spin text-purple-500" />
            <span className="text-sm text-gray-500">Sıkıştırılıyor...</span>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-2">
            <Upload className="h-8 w-8 text-gray-400" />
            <span className="text-sm text-gray-500">Tıklayın veya sürükleyin</span>
          </div>
        )}
      </div>

      {/* URL Option */}
      {showUrlInput ? (
        <div className="flex gap-2">
          <Input
            type="url"
            placeholder="https://..."
            value={urlInput}
            onChange={(e) => setUrlInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), handleAddUrl())}
            className="flex-1"
            autoFocus
          />
          <Button type="button" size="sm" onClick={handleAddUrl} disabled={!urlInput.trim()}>
            <Check className="h-4 w-4" />
          </Button>
          <Button type="button" size="sm" variant="ghost" onClick={() => setShowUrlInput(false)}>
            <X className="h-4 w-4" />
          </Button>
        </div>
      ) : (
        <button
          type="button"
          onClick={() => setShowUrlInput(true)}
          className="text-xs text-purple-600 hover:text-purple-700 hover:underline"
        >
          veya URL ile ekle
        </button>
      )}
    </div>
  );
}

function ImageUploader({
  images,
  onImagesChange,
}: {
  images: string[];
  onImagesChange: (images: string[]) => void;
}) {
  const [isDragging, setIsDragging] = useState(false);
  const [urlInput, setUrlInput] = useState("");
  const [isCompressing, setIsCompressing] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFiles = useCallback(
    async (files: FileList | null) => {
      if (!files) return;

      setIsCompressing(true);
      const newImages: string[] = [];

      for (const file of Array.from(files)) {
        if (file.type.startsWith("image/")) {
          try {
            // Compress image to reduce size (max 800px width, 70% quality)
            const compressedImage = await compressImage(file, 800, 0.7);
            newImages.push(compressedImage);
          } catch (error) {
            console.error("Image compression failed:", error);
            // Fallback to original if compression fails
            const reader = new FileReader();
            const result = await new Promise<string>((resolve) => {
              reader.onload = (e) => resolve(e.target?.result as string);
              reader.readAsDataURL(file);
            });
            newImages.push(result);
          }
        }
      }

      onImagesChange([...images, ...newImages]);
      setIsCompressing(false);
    },
    [images, onImagesChange]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      handleFiles(e.dataTransfer.files);
    },
    [handleFiles]
  );

  const handleAddUrl = () => {
    if (urlInput.trim() && (urlInput.startsWith("http://") || urlInput.startsWith("https://"))) {
      onImagesChange([...images, urlInput.trim()]);
      setUrlInput("");
    }
  };

  const removeImage = (index: number) => {
    onImagesChange(images.filter((_, i) => i !== index));
  };

  const moveImage = (from: number, to: number) => {
    const newImages = [...images];
    const [removed] = newImages.splice(from, 1);
    newImages.splice(to, 0, removed);
    onImagesChange(newImages);
  };

  return (
    <div className="space-y-4">
      {/* URL Input Option */}
      <div className="flex gap-2">
        <Input
          type="url"
          placeholder="Görsel URL'si yapıştırın (https://...)"
          value={urlInput}
          onChange={(e) => setUrlInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), handleAddUrl())}
          className="flex-1"
        />
        <Button type="button" variant="outline" onClick={handleAddUrl} disabled={!urlInput.trim()}>
          <Plus className="mr-1 h-4 w-4" />
          Ekle
        </Button>
      </div>

      <div className="relative text-center">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-gray-200" />
        </div>
        <span className="relative bg-white px-3 text-xs text-gray-400">veya dosya yükle</span>
      </div>

      {/* Upload Zone */}
      <div
        onClick={() => fileInputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        className={`
          cursor-pointer rounded-xl border-2 border-dashed p-6 text-center transition-all
          ${
            isDragging
              ? "border-purple-500 bg-purple-50"
              : "border-gray-300 hover:border-purple-400 hover:bg-purple-50/50"
          }
          ${isCompressing ? "pointer-events-none opacity-50" : ""}
        `}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept="image/*"
          onChange={(e) => handleFiles(e.target.files)}
          className="hidden"
        />
        {isCompressing ? (
          <>
            <RotateCw className="mx-auto mb-3 h-10 w-10 animate-spin text-purple-500" />
            <p className="mb-1 text-sm text-gray-600">Görseller sıkıştırılıyor...</p>
          </>
        ) : (
          <>
            <Upload
              className={`mx-auto mb-3 h-10 w-10 ${isDragging ? "text-purple-500" : "text-gray-400"}`}
            />
            <p className="mb-1 text-sm text-gray-600">Örnek sayfaları sürükleyin veya tıklayın</p>
            <p className="text-xs text-gray-400">
              PNG, JPG (otomatik sıkıştırılır) • Sıralama değiştirilebilir
            </p>
          </>
        )}
      </div>

      {/* Image Thumbnails */}
      {images.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-700">
              Yüklenen Sayfalar ({images.length})
            </span>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => onImagesChange([])}
              className="text-red-500 hover:bg-red-50 hover:text-red-700"
            >
              <Trash2 className="mr-1 h-4 w-4" />
              Tümünü Sil
            </Button>
          </div>

          <div className="grid grid-cols-4 gap-2">
            {images.map((img, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                className="group relative aspect-[3/4] overflow-hidden rounded-lg border border-gray-200 bg-gray-50"
              >
                <img
                  src={img}
                  alt={`Page ${idx + 1}`}
                  className="h-full w-full object-cover"
                  onError={(e) => {
                    (e.target as HTMLImageElement).src =
                      "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='100' height='100'%3E%3Crect fill='%23f3f4f6' width='100' height='100'/%3E%3Ctext x='50%25' y='50%25' dominant-baseline='middle' text-anchor='middle' fill='%239ca3af' font-size='12'%3EHata%3C/text%3E%3C/svg%3E";
                  }}
                />

                {/* Page number badge */}
                <div className="absolute left-1 top-1 rounded bg-black/60 px-1.5 py-0.5 text-[10px] font-medium text-white">
                  {idx === 0 ? "Kapak" : `S.${idx}`}
                </div>

                {/* URL indicator */}
                {img.startsWith("http") && (
                  <div className="absolute right-1 top-1 rounded bg-blue-500 px-1.5 py-0.5 text-[10px] font-medium text-white">
                    URL
                  </div>
                )}

                {/* Actions overlay */}
                <div className="absolute inset-0 flex items-center justify-center gap-1 bg-black/50 opacity-0 transition-opacity group-hover:opacity-100">
                  {idx > 0 && (
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        moveImage(idx, idx - 1);
                      }}
                      className="rounded-full bg-white/90 p-1.5 hover:bg-white"
                    >
                      <ChevronLeft className="h-3 w-3" />
                    </button>
                  )}
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      removeImage(idx);
                    }}
                    className="rounded-full bg-red-500 p-1.5 text-white hover:bg-red-600"
                  >
                    <X className="h-3 w-3" />
                  </button>
                  {idx < images.length - 1 && (
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        moveImage(idx, idx + 1);
                      }}
                      className="rounded-full bg-white/90 p-1.5 hover:bg-white"
                    >
                      <ChevronLeft className="h-3 w-3 rotate-180" />
                    </button>
                  )}
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ============ MAIN PAGE COMPONENT ============
export default function AdminProductsPage() {
  const [activeProductType, setActiveProductType] = useState<string>("story_book");
  const [products, setProducts] = useState<Product[]>([]);
  const [options, setOptions] = useState<TemplateOptions>({
    cover_templates: [],
    inner_templates: [],
    back_templates: [],
    ai_configs: [],
  });
  const [loading, setLoading] = useState(true);
  const [isEditorOpen, setIsEditorOpen] = useState(false);
  const [editingProduct, setEditingProduct] = useState<Product | null>(null);
  const [sampleImages, setSampleImages] = useState<string[]>([]);
  const [featureList, setFeatureList] = useState<string[]>([]);
  const [newFeature, setNewFeature] = useState("");
  const [bookThickness, setBookThickness] = useState([8]);
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);
  const [operatingId, setOperatingId] = useState<string | null>(null);
  const [activeSection, setActiveSection] = useState<"technical" | "marketing" | "scenarios">("technical");
  const [scenariosForProduct, setScenariosForProduct] = useState<ScenarioForProduct[]>([]);

  const router = useRouter();
  const { toast } = useToast();

  const form = useForm<ProductFormData>({
    resolver: zodResolver(productSchema),
    defaultValues: {
      name: "",
      slug: "",
      description: "",
      short_description: "",
      product_type: "story_book",
      cover_template_id: null,
      inner_template_id: null,
      back_template_id: null,
      ai_config_id: null,
      default_page_count: 16,
      min_page_count: 12,
      max_page_count: 32,
      width_mm: 297,
      height_mm: 210,
      paper_type: "Kuşe 170gr",
      paper_finish: "Mat",
      cover_type: "Sert Kapak",
      lamination: "",
      base_price: 299,
      discounted_price: null,
      extra_page_price: 5,
      is_active: true,
      is_featured: false,
      display_order: 0,
      thumbnail_url: "",
      video_url: "",
      orientation: "landscape",
      // Marketing
      promo_badge: "",
      promo_end_date: "",
      is_gift_wrapped: false,
      // Social Proof
      rating: null,
      review_count: 0,
      social_proof_text: "",
    },
  });

  const watchWidth = form.watch("width_mm");
  const watchHeight = form.watch("height_mm");

  useEffect(() => {
    checkAuth();
    fetchData();
  }, []);
  
  useEffect(() => {
    if (!loading) {
      fetchData();
    }
  }, [activeProductType]);

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

  const fetchData = async () => {
    try {
      const productTypeParam = activeProductType ? `&product_type=${activeProductType}` : "";
      const [productsRes, optionsRes, scenariosRes] = await Promise.all([
        fetch(`${API_BASE_URL}/admin/products?include_inactive=true${productTypeParam}`, {
          headers: getAuthHeaders(),
        }),
        fetch(`${API_BASE_URL}/admin/products/options/templates`, {
          headers: getAuthHeaders(),
        }),
        fetch(`${API_BASE_URL}/admin/scenarios?include_inactive=true`, {
          headers: getAuthHeaders(),
        }),
      ]);

      if (productsRes.ok) {
        setProducts(await productsRes.json());
      }
      if (optionsRes.ok) {
        setOptions(await optionsRes.json());
      }
      if (scenariosRes.ok) {
        const scenarioData = await scenariosRes.json();
        setScenariosForProduct(scenarioData.map((s: {id: string; name: string; thumbnail_url: string; tagline?: string | null; marketing_badge?: string | null}) => ({
          id: s.id,
          name: s.name,
          thumbnail_url: s.thumbnail_url,
          tagline: s.tagline,
          marketing_badge: s.marketing_badge,
        })));
      }
    } catch (error) {
      console.error("Failed to fetch data:", error);
    } finally {
      setLoading(false);
    }
  };

  const openEditor = (product?: Product) => {
    if (product) {
      setEditingProduct(product);
      form.reset({
        name: product.name,
        slug: product.slug,
        description: product.description || "",
        short_description: product.short_description || "",
        product_type: product.product_type || "story_book",
        // Template IDs - use direct IDs or extract from template objects
        cover_template_id: product.cover_template?.id || null,
        inner_template_id: product.inner_template?.id || null,
        back_template_id: product.back_template?.id || null,
        ai_config_id: product.ai_config?.id || null,
        // Page settings
        default_page_count: product.default_page_count,
        min_page_count: product.min_page_count,
        max_page_count: product.max_page_count,
        // Dimensions from inner template
        width_mm: product.inner_template?.page_width_mm || 210,
        height_mm: product.inner_template?.page_height_mm || 297,
        // Paper & Cover
        paper_type: product.paper_type || "Kuşe 170gr",
        paper_finish: product.paper_finish || "Mat",
        cover_type: product.cover_type || "Sert Kapak",
        lamination: product.lamination || "",
        // Pricing
        base_price: product.base_price,
        discounted_price: product.discounted_price || null,
        extra_page_price: product.extra_page_price,
        // Status
        is_active: product.is_active,
        is_featured: product.is_featured,
        display_order: product.display_order,
        // Media
        thumbnail_url: product.thumbnail_url || "",
        video_url: product.video_url || "",
        orientation: product.orientation || "landscape",
        // Marketing
        promo_badge: product.promo_badge || "",
        promo_end_date: product.promo_end_date ? product.promo_end_date.split("T")[0] : "",
        is_gift_wrapped: product.is_gift_wrapped || false,
        // Social Proof
        rating: product.rating || null,
        review_count: product.review_count || 0,
        social_proof_text: product.social_proof_text || "",
      });
      setSampleImages(product.sample_images || []);
      setFeatureList(product.feature_list || []);
    } else {
      setEditingProduct(null);
      form.reset({
        name: "",
        slug: "",
        description: "",
        short_description: "",
        product_type: activeProductType,
        cover_template_id: null,
        inner_template_id: null,
        back_template_id: null,
        ai_config_id: null,
        default_page_count: 16,
        min_page_count: 12,
        max_page_count: 32,
        width_mm: 297,
        height_mm: 210,
        paper_type: "Kuşe 170gr",
        paper_finish: "Mat",
        cover_type: "Sert Kapak",
        lamination: "",
        base_price: 299,
        discounted_price: null,
        extra_page_price: 5,
        is_active: true,
        is_featured: false,
        display_order: 0,
        thumbnail_url: "",
        video_url: "",
        orientation: "landscape",
        // Marketing
        promo_badge: "",
        promo_end_date: "",
        is_gift_wrapped: false,
        // Social Proof
        rating: null,
        review_count: 0,
        social_proof_text: "",
      });
      setSampleImages([]);
      setFeatureList([]);
    }
    setBookThickness([8]);
    setActiveSection("technical");
    setIsEditorOpen(true);
  };

  const closeEditor = () => {
    setIsEditorOpen(false);
    setEditingProduct(null);
    setSampleImages([]);
    setFeatureList([]);
    setNewFeature("");
    form.reset();
  };

  const onSubmit = async (data: ProductFormData) => {
    try {
      // Build payload - explicitly handle nullable fields
      const payload: Record<string, unknown> = {
        name: data.name,
        slug: data.slug || undefined,
        description: data.description || undefined,
        short_description: data.short_description || undefined,
        // Template IDs - convert "none" or empty to null
        cover_template_id:
          data.cover_template_id && data.cover_template_id !== "none"
            ? data.cover_template_id
            : null,
        inner_template_id:
          data.inner_template_id && data.inner_template_id !== "none"
            ? data.inner_template_id
            : null,
        back_template_id:
          data.back_template_id && data.back_template_id !== "none" ? data.back_template_id : null,
        ai_config_id: data.ai_config_id && data.ai_config_id !== "none" ? data.ai_config_id : null,
        // Page settings
        default_page_count: data.default_page_count,
        min_page_count: data.min_page_count,
        max_page_count: data.max_page_count,
        // Paper & Cover
        paper_type: data.paper_type,
        paper_finish: data.paper_finish,
        cover_type: data.cover_type,
        lamination: data.lamination || null,
        // Pricing
        base_price: data.base_price,
        discounted_price: data.discounted_price || null,
        extra_page_price: data.extra_page_price,
        // Status
        is_active: data.is_active,
        is_featured: data.is_featured,
        display_order: data.display_order,
        // Media
        thumbnail_url: data.thumbnail_url || null,
        video_url: data.video_url || null,
        sample_images: sampleImages,
        orientation: data.orientation || "landscape",
        // Marketing & Urgency
        promo_badge: data.promo_badge || null,
        promo_end_date: data.promo_end_date ? new Date(data.promo_end_date).toISOString() : null,
        is_gift_wrapped: data.is_gift_wrapped || false,
        // Social Proof
        rating: data.rating || null,
        review_count: data.review_count || 0,
        social_proof_text: data.social_proof_text || null,
        // Features
        feature_list: featureList,
      };

      const url = editingProduct
        ? `${API_BASE_URL}/admin/products/${editingProduct.id}`
        : `${API_BASE_URL}/admin/products`;

      // Log payload size for debugging
      const payloadStr = JSON.stringify(payload);
      const payloadSizeKB = (payloadStr.length / 1024).toFixed(1);
      // eslint-disable-next-line no-console -- debug payload size
      console.log(
        `[Product Save] Payload size: ${payloadSizeKB} KB, Images: ${sampleImages.length}`
      );

      // Warn if payload is too large (>5MB)
      if (payloadStr.length > 5 * 1024 * 1024) {
        toast({
          title: "Uyarı",
          description:
            "Görsel boyutu çok büyük. Lütfen daha küçük görseller kullanın veya URL ekleyin.",
          variant: "destructive",
        });
        return;
      }

      const response = await fetch(url, {
        method: editingProduct ? "PATCH" : "POST",
        headers: getAuthHeaders(),
        body: payloadStr,
      });

      if (response.ok) {
        toast({
          title: "Başarılı",
          description: editingProduct ? "Ürün güncellendi" : "Ürün oluşturuldu",
        });
        closeEditor();
        fetchData();
      } else {
        const errorText = await response.text();
        console.error("[Product Save] Error response:", errorText);
        let errorMessage = "Hata oluştu";
        try {
          const errorData = JSON.parse(errorText);
          errorMessage = errorData.detail || errorMessage;
        } catch {
          errorMessage = errorText || errorMessage;
        }
        throw new Error(errorMessage);
      }
    } catch (error) {
      console.error("[Product Save] Error:", error);
      const message = error instanceof Error ? error.message : "Bilinmeyen hata";
      toast({ title: "Hata", description: message, variant: "destructive" });
    }
  };

  const handleDelete = async (productId: string) => {
    setOperatingId(productId);
    try {
      const response = await fetch(`${API_BASE_URL}/admin/products/${productId}`, {
        method: "DELETE",
        headers: getAuthHeaders(),
      });

      if (response.ok) {
        toast({ title: "Başarılı", description: "Ürün silindi" });
        fetchData();
      } else {
        toast({ title: "Hata", description: "Silme başarısız", variant: "destructive" });
      }
    } catch {
      toast({ title: "Hata", description: "Silme başarısız", variant: "destructive" });
    } finally {
      setDeleteConfirm(null);
      setOperatingId(null);
    }
  };

  const handleDuplicate = async (productId: string) => {
    setOperatingId(productId);
    try {
      const response = await fetch(`${API_BASE_URL}/admin/products/${productId}/duplicate`, {
        method: "POST",
        headers: getAuthHeaders(),
      });

      if (response.ok) {
        toast({ title: "Başarılı", description: "Ürün kopyalandı" });
        fetchData();
      } else {
        toast({ title: "Hata", description: "Kopyalama başarısız", variant: "destructive" });
      }
    } catch {
      toast({ title: "Hata", description: "Kopyalama başarısız", variant: "destructive" });
    } finally {
      setOperatingId(null);
    }
  };

  const toggleActive = async (product: Product) => {
    setOperatingId(product.id);
    try {
      const response = await fetch(`${API_BASE_URL}/admin/products/${product.id}`, {
        method: "PATCH",
        headers: getAuthHeaders(),
        body: JSON.stringify({ is_active: !product.is_active }),
      });

      if (response.ok) {
        toast({ title: "Başarılı", description: "Durum güncellendi" });
        fetchData();
      } else {
        toast({ title: "Hata", description: "Güncelleme başarısız", variant: "destructive" });
      }
    } catch {
      toast({ title: "Hata", description: "Güncelleme başarısız", variant: "destructive" });
    } finally {
      setOperatingId(null);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header */}
      <header className="sticky top-0 z-40 border-b bg-white shadow-sm">
        <div className="mx-auto flex max-w-[1600px] items-center justify-between px-6 py-4">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="sm" onClick={() => router.push("/admin")}>
              <ChevronLeft className="mr-1 h-4 w-4" />
              Geri
            </Button>
            <div>
              <h1 className="flex items-center gap-2 text-2xl font-bold text-gray-900">
                <Book className="h-6 w-6 text-purple-600" />
                Ürün Yönetimi
              </h1>
              <p className="mt-0.5 text-sm text-gray-500">
                Kitap formatlarını ve önizleme görsellerini yönetin
              </p>
            </div>
          </div>
          <Button onClick={() => openEditor()} className="bg-purple-600 hover:bg-purple-700">
            <Plus className="mr-2 h-4 w-4" />
            Yeni Format Ekle
          </Button>
        </div>
      </header>

      <main className="mx-auto max-w-[1600px] px-6 py-8">
        {/* Product Type Tabs */}
        <div className="mb-6 flex gap-2 rounded-lg bg-white p-2 shadow-sm">
          <button
            onClick={() => setActiveProductType("story_book")}
            className={`flex flex-1 items-center justify-center gap-2 rounded-md px-4 py-3 text-sm font-medium transition-all ${
              activeProductType === "story_book"
                ? "bg-purple-600 text-white shadow-md"
                : "text-gray-600 hover:bg-gray-100"
            }`}
          >
            <Book className="h-5 w-5" />
            Hikaye Kitabı
          </button>
          <button
            onClick={() => setActiveProductType("coloring_book")}
            className={`flex flex-1 items-center justify-center gap-2 rounded-md px-4 py-3 text-sm font-medium transition-all ${
              activeProductType === "coloring_book"
                ? "bg-purple-600 text-white shadow-md"
                : "text-gray-600 hover:bg-gray-100"
            }`}
          >
            <Palette className="h-5 w-5" />
            Boyama Kitabı
          </button>
          <button
            onClick={() => setActiveProductType("audio_addon")}
            className={`flex flex-1 items-center justify-center gap-2 rounded-md px-4 py-3 text-sm font-medium transition-all ${
              activeProductType === "audio_addon"
                ? "bg-purple-600 text-white shadow-md"
                : "text-gray-600 hover:bg-gray-100"
            }`}
          >
            <Headphones className="h-5 w-5" />
            Sesli Kitap Eklentisi
          </button>
        </div>

        {/* Stats Row */}
        <div className="mb-8 grid grid-cols-4 gap-4">
          {[
            { label: "Toplam Ürün", value: products.length, icon: LayoutGrid, bgClass: "bg-purple-100", textClass: "text-purple-600" },
            {
              label: "Aktif",
              value: products.filter((p) => p.is_active).length,
              icon: Check,
              bgClass: "bg-green-100",
              textClass: "text-green-600",
            },
            {
              label: "Taslak",
              value: products.filter((p) => !p.is_active).length,
              icon: Pencil,
              bgClass: "bg-amber-100",
              textClass: "text-amber-600",
            },
            {
              label: "Öne Çıkan",
              value: products.filter((p) => p.is_featured).length,
              icon: Sparkles,
              bgClass: "bg-blue-100",
              textClass: "text-blue-600",
            },
          ].map((stat) => (
            <Card key={stat.label} className="border-0 shadow-sm">
              <CardContent className="flex items-center gap-4 p-4">
                <div
                  className={`h-12 w-12 rounded-xl flex items-center justify-center ${stat.bgClass}`}
                >
                  <stat.icon className={`h-6 w-6 ${stat.textClass}`} />
                </div>
                <div>
                  <p className="text-2xl font-bold">{stat.value}</p>
                  <p className="text-sm text-gray-500">{stat.label}</p>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Products Grid */}
        {loading ? (
          <div className="py-12 text-center">
            <RotateCw className="mx-auto mb-4 h-8 w-8 animate-spin text-purple-600" />
            <p className="text-gray-500">Yükleniyor...</p>
          </div>
        ) : products.length === 0 ? (
          <Card className="border-2 border-dashed">
            <CardContent className="py-16 text-center">
              <Book className="mx-auto mb-4 h-16 w-16 text-gray-300" />
              <h3 className="mb-2 text-xl font-semibold text-gray-700">Henüz ürün yok</h3>
              <p className="mb-6 text-gray-500">İlk kitap formatınızı oluşturmak için başlayın</p>
              <Button onClick={() => openEditor()} className="bg-purple-600 hover:bg-purple-700">
                <Plus className="mr-2 h-4 w-4" />
                İlk Ürünü Oluştur
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2 xl:grid-cols-3">
            {products.map((product) => {
              const dimensions = product.inner_template
                ? `${product.inner_template.page_width_mm}×${product.inner_template.page_height_mm}mm`
                : "—";
              const orientation = product.inner_template
                ? (product.inner_template.page_width_mm || 0) >
                  (product.inner_template.page_height_mm || 0)
                  ? "Yatay"
                  : "Dikey"
                : "";

              return (
                <Card
                  key={product.id}
                  className={`group transition-all hover:shadow-lg ${!product.is_active ? "opacity-70" : ""}`}
                >
                  <CardContent className="p-0">
                    {/* Thumbnail */}
                    <div className="relative h-48 overflow-hidden rounded-t-lg bg-gradient-to-br from-purple-100 to-pink-100">
                      {product.thumbnail_url ? (
                        <img
                          src={product.thumbnail_url}
                          alt={product.name}
                          className="h-full w-full object-cover"
                        />
                      ) : (
                        <div className="flex h-full w-full items-center justify-center">
                          <Book className="h-16 w-16 text-purple-300" />
                        </div>
                      )}

                      {/* Badges */}
                      <div className="absolute left-3 top-3 flex flex-wrap gap-2">
                        {product.promo_badge && (
                          <Badge className="bg-red-500 text-white shadow-sm">
                            {product.promo_badge}
                          </Badge>
                        )}
                        {product.is_featured && (
                          <Badge variant="warning" className="shadow-sm">
                            <Sparkles className="mr-1 h-3 w-3" />
                            Öne Çıkan
                          </Badge>
                        )}
                        {!product.is_active && (
                          <Badge variant="secondary" className="shadow-sm">
                            Taslak
                          </Badge>
                        )}
                      </div>

                      {/* Quick Actions */}
                      <div className="absolute right-3 top-3 flex gap-1 opacity-0 transition-opacity group-hover:opacity-100">
                        <Button
                          size="sm"
                          variant="secondary"
                          className="h-8 w-8 bg-white/90 p-0 shadow-sm hover:bg-white"
                          onClick={() => openEditor(product)}
                        >
                          <Pencil className="h-3.5 w-3.5" />
                        </Button>
                        <Button
                          size="sm"
                          variant="secondary"
                          className="h-8 w-8 bg-white/90 p-0 shadow-sm hover:bg-white"
                          onClick={() => handleDuplicate(product.id)}
                        >
                          <Copy className="h-3.5 w-3.5" />
                        </Button>
                      </div>
                    </div>

                    {/* Info */}
                    <div className="p-4">
                      <div className="mb-3 flex items-start justify-between">
                        <div className="min-w-0 flex-1">
                          <h3 className="font-semibold text-gray-900">{product.name}</h3>
                          <p className="line-clamp-1 text-sm text-gray-500">
                            {product.short_description || "Açıklama yok"}
                          </p>
                          {/* Rating */}
                          {product.rating && product.rating > 0 && (
                            <div className="mt-1 flex items-center gap-1">
                              <Star className="h-3.5 w-3.5 fill-amber-400 text-amber-400" />
                              <span className="text-sm font-medium text-gray-700">
                                {product.rating.toFixed(1)}
                              </span>
                              {product.review_count && product.review_count > 0 && (
                                <span className="text-xs text-gray-400">
                                  ({product.review_count})
                                </span>
                              )}
                            </div>
                          )}
                        </div>
                        <div className="ml-2 flex-shrink-0 text-right">
                          {product.discounted_price ? (
                            <>
                              <p className="text-sm text-gray-400 line-through">
                                {product.base_price} TL
                              </p>
                              <p className="text-lg font-bold text-green-600">
                                {product.discounted_price} TL
                              </p>
                            </>
                          ) : (
                            <p className="text-lg font-bold text-purple-600">
                              {product.base_price} TL
                            </p>
                          )}
                        </div>
                      </div>

                      {/* Specs Grid */}
                      <div className="mb-4 grid grid-cols-3 gap-2 text-xs">
                        <div className="rounded-lg bg-gray-50 p-2 text-center">
                          <p className="mb-0.5 text-gray-400">Boyut</p>
                          <p className="font-medium text-gray-700">{dimensions}</p>
                        </div>
                        <div className="rounded-lg bg-gray-50 p-2 text-center">
                          <p className="mb-0.5 text-gray-400">Sayfa</p>
                          <p className="font-medium text-gray-700">{product.default_page_count}</p>
                        </div>
                        <div className="rounded-lg bg-gray-50 p-2 text-center">
                          <p className="mb-0.5 text-gray-400">Yön</p>
                          <p className="font-medium text-gray-700">{orientation || "—"}</p>
                        </div>
                      </div>

                      {/* Actions */}
                      <div className="flex items-center gap-2">
                        <Button
                          size="sm"
                          variant={product.is_active ? "outline" : "default"}
                          className="flex-1 text-xs"
                          disabled={operatingId === product.id}
                          onClick={() => toggleActive(product)}
                        >
                          {operatingId === product.id ? "İşleniyor..." : product.is_active ? "Pasif Yap" : "Aktif Yap"}
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          className="text-red-500 hover:bg-red-50 hover:text-red-700"
                          onClick={() => setDeleteConfirm(product.id)}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        )}
      </main>

      {/* Delete Confirmation Dialog */}
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
                <h3 className="mb-2 text-lg font-semibold">Ürünü Sil</h3>
                <p className="mb-6 text-sm text-gray-500">
                  Bu ürünü silmek istediğinize emin misiniz? Bu işlem geri alınamaz.
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
                    Sil
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
          <SheetHeader className="mb-4">
            <SheetTitle className="flex items-center gap-2">
              <Settings2 className="h-5 w-5 text-purple-600" />
              {editingProduct ? "Ürünü Düzenle" : "Yeni Ürün Oluştur"}
            </SheetTitle>
            <SheetDescription>
              Kitap formatı, baskı ayarları ve pazarlama özelliklerini yapılandırın
            </SheetDescription>
          </SheetHeader>

          {/* Section Tabs */}
          <div className="mb-6 flex gap-1 rounded-lg bg-gray-100 p-1">
            <button
              type="button"
              onClick={() => setActiveSection("technical")}
              className={`flex flex-1 items-center justify-center gap-1.5 rounded-md px-3 py-2.5 text-xs font-medium transition-all ${
                activeSection === "technical"
                  ? "bg-white text-purple-700 shadow-sm"
                  : "text-gray-600 hover:text-gray-800"
              }`}
            >
              <Settings2 className="h-4 w-4" />
              Teknik & Baskı
            </button>
            <button
              type="button"
              onClick={() => setActiveSection("marketing")}
              className={`flex flex-1 items-center justify-center gap-1.5 rounded-md px-3 py-2.5 text-xs font-medium transition-all ${
                activeSection === "marketing"
                  ? "bg-white text-green-700 shadow-sm"
                  : "text-gray-600 hover:text-gray-800"
              }`}
            >
              <TrendingUp className="h-4 w-4" />
              Pazarlama
            </button>
            <button
              type="button"
              onClick={() => setActiveSection("scenarios")}
              className={`flex flex-1 items-center justify-center gap-1.5 rounded-md px-3 py-2.5 text-xs font-medium transition-all ${
                activeSection === "scenarios"
                  ? "bg-white text-orange-600 shadow-sm"
                  : "text-gray-600 hover:text-gray-800"
              }`}
            >
              <BookOpen className="h-4 w-4" />
              Senaryolar
            </button>
          </div>

          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-8">
            {/* ==================== TECHNICAL SECTION ==================== */}
            {activeSection === "technical" && (
              <>
                {/* Section: General Info */}
                <div className="space-y-4">
                  <div className="flex items-center gap-2 text-sm font-medium text-gray-700">
                    <Book className="h-4 w-4 text-purple-600" />
                    Genel Bilgiler
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div className="col-span-2">
                      <Label>Ürün Adı *</Label>
                      <Input
                        {...form.register("name")}
                        placeholder="Örn: Premium Yatay Albüm"
                        className="mt-1"
                      />
                      {form.formState.errors.name && (
                        <p className="mt-1 text-xs text-red-500">
                          {form.formState.errors.name.message}
                        </p>
                      )}
                    </div>
                    <div className="col-span-2">
                      <Label>Kısa Açıklama</Label>
                      <Input
                        {...form.register("short_description")}
                        placeholder="Kart görünümünde gösterilecek açıklama"
                        className="mt-1"
                      />
                    </div>
                    <div className="col-span-2">
                      <Label>Detaylı Açıklama</Label>
                      <Textarea
                        {...form.register("description")}
                        placeholder="Ürün detayları..."
                        className="mt-1"
                        rows={3}
                      />
                    </div>
                  </div>
                </div>

                <Separator />

                {/* CONDITIONAL: Story Book specific fields */}
                {form.watch("product_type") === "story_book" && (
                  <>
                    {/* Section: Template References */}
                    <div className="space-y-4">
                      <div className="flex items-center gap-2 text-sm font-medium text-gray-700">
                        <LayoutGrid className="h-4 w-4 text-purple-600" />
                        Şablon Atamaları
                      </div>
                      <p className="-mt-2 text-xs text-gray-500">
                        Kitap Yapılandırması&apos;nda oluşturulan şablonları bu ürüne atayın
                      </p>

                  <div className="grid grid-cols-1 gap-4">
                    {/* Cover Template */}
                    <div>
                      <Label>Ön Kapak Şablonu</Label>
                      <Controller
                        control={form.control}
                        name="cover_template_id"
                        render={({ field }) => (
                          <Select
                            value={field.value || "none"}
                            onValueChange={(val) => field.onChange(val === "none" ? null : val)}
                          >
                            <SelectTrigger className="mt-1">
                              <SelectValue placeholder="Şablon seçin..." />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="none">— Şablon Yok —</SelectItem>
                              {options.cover_templates.map((t) => (
                                <SelectItem key={t.id} value={t.id}>
                                  {t.name} ({t.page_width_mm}×{t.page_height_mm}mm)
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        )}
                      />
                    </div>

                    {/* Inner Page Template */}
                    <div>
                      <Label>İç Sayfa Şablonu</Label>
                      <Controller
                        control={form.control}
                        name="inner_template_id"
                        render={({ field }) => (
                          <Select
                            value={field.value || "none"}
                            onValueChange={(val) => field.onChange(val === "none" ? null : val)}
                          >
                            <SelectTrigger className="mt-1">
                              <SelectValue placeholder="Şablon seçin..." />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="none">— Şablon Yok —</SelectItem>
                              {options.inner_templates.map((t) => (
                                <SelectItem key={t.id} value={t.id}>
                                  {t.name} ({t.page_width_mm}×{t.page_height_mm}mm)
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        )}
                      />
                    </div>

                    {/* Back Cover Template */}
                    <div>
                      <Label>Arka Kapak Şablonu</Label>
                      <Controller
                        control={form.control}
                        name="back_template_id"
                        render={({ field }) => (
                          <Select
                            value={field.value || "none"}
                            onValueChange={(val) => field.onChange(val === "none" ? null : val)}
                          >
                            <SelectTrigger className="mt-1">
                              <SelectValue placeholder="Şablon seçin..." />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="none">— Şablon Yok —</SelectItem>
                              {options.back_templates.map((t) => (
                                <SelectItem key={t.id} value={t.id}>
                                  {t.name} ({t.page_width_mm}×{t.page_height_mm}mm)
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        )}
                      />
                    </div>

                    {/* AI Config */}
                    <div>
                      <Label>AI Üretim Ayarı</Label>
                      <Controller
                        control={form.control}
                        name="ai_config_id"
                        render={({ field }) => (
                          <Select
                            value={field.value || "none"}
                            onValueChange={(val) => field.onChange(val === "none" ? null : val)}
                          >
                            <SelectTrigger className="mt-1">
                              <SelectValue placeholder="AI ayarı seçin..." />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="none">— AI Ayarı Yok —</SelectItem>
                              {options.ai_configs.map((c) => (
                                <SelectItem key={c.id} value={c.id}>
                                  {c.name} ({c.image_provider})
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        )}
                      />
                    </div>
                  </div>

                  {/* No templates warning */}
                  {options.cover_templates.length === 0 && options.inner_templates.length === 0 && (
                    <div className="rounded-lg border border-amber-200 bg-amber-50 p-4">
                      <div className="flex items-center gap-2 text-amber-800">
                        <AlertCircle className="h-4 w-4" />
                        <span className="text-sm font-medium">Şablon Bulunamadı</span>
                      </div>
                      <p className="mt-1 text-xs text-amber-700">
                        Önce Kitap Yapılandırması sayfasından şablonlar oluşturun.
                      </p>
                    </div>
                  )}
                </div>

                <Separator />
                </>
                )}

                {/* CONDITIONAL: Coloring Book specific fields */}
                {form.watch("product_type") === "coloring_book" && (
                  <>
                    <div className="space-y-4">
                      <div className="flex items-center gap-2 text-sm font-medium text-gray-700">
                        <Palette className="h-4 w-4 text-purple-600" />
                        Boyama Kitabı Ayarları
                      </div>
                      <p className="-mt-2 text-xs text-gray-500">
                        Line-art conversion ayarları
                      </p>

                      <div className="rounded-lg border border-purple-100 bg-purple-50/50 p-4">
                        <Label>Line Art Metodu</Label>
                        <Select defaultValue="canny">
                          <SelectTrigger className="mt-1">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="canny">Canny (Önerilen)</SelectItem>
                            <SelectItem value="opencv">OpenCV</SelectItem>
                            <SelectItem value="sketch">Sketch</SelectItem>
                          </SelectContent>
                        </Select>
                        <p className="mt-1 text-xs text-gray-500">
                          Görsellerden çizgi çıkarma algoritması
                        </p>
                      </div>

                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <Label>Düşük Eşik (Edge Threshold Low)</Label>
                          <Input type="number" defaultValue={80} min={0} max={255} className="mt-1" />
                          <p className="mt-1 text-xs text-gray-500">Daha az detay (0-255)</p>
                        </div>
                        <div>
                          <Label>Yüksek Eşik (Edge Threshold High)</Label>
                          <Input type="number" defaultValue={200} min={0} max={255} className="mt-1" />
                          <p className="mt-1 text-xs text-gray-500">Daha basit şekiller (0-255)</p>
                        </div>
                      </div>
                    </div>

                    <Separator />
                  </>
                )}

                {/* CONDITIONAL: Audio Addon specific fields */}
                {form.watch("product_type") === "audio_addon" && (
                  <>
                    <div className="space-y-4">
                      <div className="flex items-center gap-2 text-sm font-medium text-gray-700">
                        <Headphones className="h-4 w-4 text-purple-600" />
                        Sesli Kitap Eklentisi Ayarları
                      </div>
                      <p className="-mt-2 text-xs text-gray-500">
                        Ses tipi ve özellikleri
                      </p>

                      <div className="rounded-lg border border-blue-100 bg-blue-50/50 p-4">
                        <Label>Ses Tipi</Label>
                        <Select defaultValue="system">
                          <SelectTrigger className="mt-1">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="system">Sistem Sesi</SelectItem>
                            <SelectItem value="cloned">Klonlanmış Ses</SelectItem>
                          </SelectContent>
                        </Select>
                        <p className="mt-1 text-xs text-gray-500">
                          Sistem sesi: Hazır profesyonel seslendirme<br/>
                          Klonlanmış ses: Kişiye özel ses klonlama
                        </p>
                      </div>

                      <div className="rounded-lg border border-amber-100 bg-amber-50 p-4">
                        <div className="flex items-start gap-2">
                          <AlertCircle className="mt-0.5 h-4 w-4 text-amber-600" />
                          <div>
                            <p className="text-sm font-medium text-amber-800">Not:</p>
                            <p className="mt-1 text-xs text-amber-700">
                              Audio addon ürünleri hikaye kitabına eklenti olarak satılır. 
                              Base price buradan yönetilir ve checkout sırasında otomatik eklenir.
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>

                    <Separator />
                  </>
                )}

                {/* Section: Physical Specs - Only for story_book and coloring_book */}
                {(form.watch("product_type") === "story_book" || form.watch("product_type") === "coloring_book") && (
                <div className="space-y-4">
                  <div className="flex items-center gap-2 text-sm font-medium text-gray-700">
                    <Ruler className="h-4 w-4 text-purple-600" />
                    Fiziksel Özellikler
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label>Genişlik (mm)</Label>
                      <Controller
                        control={form.control}
                        name="width_mm"
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
                    <div>
                      <Label>Yükseklik (mm)</Label>
                      <Controller
                        control={form.control}
                        name="height_mm"
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
                  </div>

                  {/* Dimension Calculator */}
                  <DimensionCalculator width={watchWidth || 210} height={watchHeight || 297} />

                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <Label>Varsayılan Sayfa</Label>
                      <Controller
                        control={form.control}
                        name="default_page_count"
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
                    <div>
                      <Label>Min Sayfa</Label>
                      <Controller
                        control={form.control}
                        name="min_page_count"
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
                    <div>
                      <Label>Max Sayfa</Label>
                      <Controller
                        control={form.control}
                        name="max_page_count"
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
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label>Kağıt Tipi</Label>
                      <Controller
                        control={form.control}
                        name="paper_type"
                        render={({ field }) => (
                          <Select value={field.value} onValueChange={field.onChange}>
                            <SelectTrigger className="mt-1">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="Kuşe 170gr">Kuşe 170gr</SelectItem>
                              <SelectItem value="Kuşe 200gr">Kuşe 200gr</SelectItem>
                              <SelectItem value="Mat Kuşe 150gr">Mat Kuşe 150gr</SelectItem>
                              <SelectItem value="Bristol 300gr">Bristol 300gr</SelectItem>
                            </SelectContent>
                          </Select>
                        )}
                      />
                    </div>
                    <div>
                      <Label>Kağıt Yüzeyi</Label>
                      <Controller
                        control={form.control}
                        name="paper_finish"
                        render={({ field }) => (
                          <Select value={field.value} onValueChange={field.onChange}>
                            <SelectTrigger className="mt-1">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="Mat">Mat</SelectItem>
                              <SelectItem value="Parlak">Parlak</SelectItem>
                              <SelectItem value="Saten">Saten</SelectItem>
                            </SelectContent>
                          </Select>
                        )}
                      />
                    </div>
                    <div>
                      <Label>Kapak Tipi</Label>
                      <Controller
                        control={form.control}
                        name="cover_type"
                        render={({ field }) => (
                          <Select value={field.value} onValueChange={field.onChange}>
                            <SelectTrigger className="mt-1">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="Sert Kapak">Sert Kapak</SelectItem>
                              <SelectItem value="Yumuşak Kapak">Yumuşak Kapak</SelectItem>
                              <SelectItem value="Spiralli">Spiralli</SelectItem>
                            </SelectContent>
                          </Select>
                        )}
                      />
                    </div>
                    <div>
                      <Label>Laminasyon</Label>
                      <Controller
                        control={form.control}
                        name="lamination"
                        render={({ field }) => (
                          <Select
                            value={field.value || "none"}
                            onValueChange={(val) => field.onChange(val === "none" ? "" : val)}
                          >
                            <SelectTrigger className="mt-1">
                              <SelectValue placeholder="Seçiniz..." />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="none">Yok</SelectItem>
                              <SelectItem value="Mat">Mat</SelectItem>
                              <SelectItem value="Parlak">Parlak</SelectItem>
                              <SelectItem value="Kadife">Kadife</SelectItem>
                            </SelectContent>
                          </Select>
                        )}
                      />
                    </div>
                  </div>
                </div>

                <Separator />
                )}

                {/* Section: Pricing */}
                <div className="space-y-4">
                  <div className="flex items-center gap-2 text-sm font-medium text-gray-700">
                    <DollarSign className="h-4 w-4 text-purple-600" />
                    Fiyatlandırma
                  </div>

                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <Label>Temel Fiyat (TL) *</Label>
                      <Controller
                        control={form.control}
                        name="base_price"
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
                    <div>
                      <Label>İndirimli Fiyat (TL)</Label>
                      <Controller
                        control={form.control}
                        name="discounted_price"
                        render={({ field }) => (
                          <Input
                            type="number"
                            placeholder="Opsiyonel"
                            value={field.value || ""}
                            onChange={(e) =>
                              field.onChange(e.target.value ? Number(e.target.value) : undefined)
                            }
                            className="mt-1"
                          />
                        )}
                      />
                    </div>
                    <div>
                      <Label>Ek Sayfa Fiyatı</Label>
                      <Controller
                        control={form.control}
                        name="extra_page_price"
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
                  </div>
                </div>

                <Separator />

                {/* Section: Visual Assets */}
                <div className="space-y-4">
                  <div className="flex items-center gap-2 text-sm font-medium text-gray-700">
                    <ImageIcon className="h-4 w-4 text-purple-600" />
                    Görsel Ayarları
                  </div>

                  {/* Thumbnail URL - Card Image */}
                  <div>
                    <Label>Kart Görseli</Label>
                    <p className="mb-2 text-xs text-gray-500">
                      Ürün listesinde gösterilecek kapak görseli
                    </p>
                    <Controller
                      control={form.control}
                      name="thumbnail_url"
                      render={({ field }) => (
                        <SingleImageUploader
                          value={field.value}
                          onChange={(url) => field.onChange(url || "")}
                          label="Kart Görseli Yükle"
                        />
                      )}
                    />
                  </div>

                  {/* Orientation Select */}
                  <div>
                    <Label>Kitap Yönü</Label>
                    <Controller
                      control={form.control}
                      name="orientation"
                      render={({ field }) => (
                        <Select value={field.value || "landscape"} onValueChange={field.onChange}>
                          <SelectTrigger className="mt-1">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="landscape">Yatay (Landscape)</SelectItem>
                            <SelectItem value="portrait">Dikey (Portrait)</SelectItem>
                          </SelectContent>
                        </Select>
                      )}
                    />
                  </div>

                  <Separator className="my-4" />

                  <div className="flex items-center gap-2 text-sm font-medium text-gray-700">
                    <BookOpen className="h-4 w-4 text-purple-600" />
                    Örnek Flipbook Görselleri
                  </div>
                  <p className="-mt-2 text-xs text-gray-500">
                    Ürün sayfasında gösterilecek örnek kitap sayfaları
                  </p>

                  <ImageUploader images={sampleImages} onImagesChange={setSampleImages} />

                  {/* Book Thickness Slider */}
                  <div className="mt-4">
                    <div className="mb-2 flex items-center justify-between">
                      <Label>Kitap Kalınlığı (Görsel)</Label>
                      <span className="text-sm text-gray-500">{bookThickness[0]}px</span>
                    </div>
                    <Slider
                      value={bookThickness}
                      onValueChange={setBookThickness}
                      min={4}
                      max={20}
                      step={1}
                      className="w-full"
                    />
                  </div>

                  {/* Live Flipbook Preview */}
                  {(sampleImages.length > 0 || editingProduct) && (
                    <div className="mt-6 rounded-xl bg-gradient-to-br from-gray-900 to-gray-800 p-6">
                      <div className="mb-4 flex items-center justify-center gap-2">
                        <Eye className="h-4 w-4 text-gray-400" />
                        <span className="text-sm text-gray-400">Canlı Önizleme</span>
                      </div>
                      <FlipbookPreview
                        images={sampleImages}
                        width={watchWidth || 210}
                        height={watchHeight || 297}
                        bookThickness={bookThickness[0]}
                      />
                    </div>
                  )}
                </div>

                <Separator />

                {/* Section: Status */}
                <div className="space-y-4">
                  <div className="flex items-center gap-2 text-sm font-medium text-gray-700">
                    <Settings2 className="h-4 w-4 text-purple-600" />
                    Durum ve Görünürlük
                  </div>

                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium">Aktif (Satışta)</p>
                      <p className="text-sm text-gray-500">Müşteriler bu ürünü görebilir</p>
                    </div>
                    <Controller
                      control={form.control}
                      name="is_active"
                      render={({ field }) => (
                        <Switch checked={field.value} onCheckedChange={field.onChange} />
                      )}
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium">Öne Çıkan</p>
                      <p className="text-sm text-gray-500">Ana sayfada vurgulansın</p>
                    </div>
                    <Controller
                      control={form.control}
                      name="is_featured"
                      render={({ field }) => (
                        <Switch checked={field.value} onCheckedChange={field.onChange} />
                      )}
                    />
                  </div>

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
                          className="mt-1 w-24"
                        />
                      )}
                    />
                  </div>
                </div>
              </>
            )}

            {/* ==================== MARKETING SECTION ==================== */}
            {activeSection === "marketing" && (
              <>
                {/* Promo & Urgency */}
                <div className="space-y-4">
                  <div className="flex items-center gap-2 text-sm font-medium text-gray-700">
                    <Sparkles className="h-4 w-4 text-green-600" />
                    Promosyon & Aciliyet
                  </div>
                  <p className="-mt-2 text-xs text-gray-500">
                    Müşterilerin satın alma kararını hızlandıracak öğeler
                  </p>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label>Promo Rozeti</Label>
                      <Input
                        {...form.register("promo_badge")}
                        placeholder="Örn: %20 İndirim, En Çok Satan"
                        className="mt-1"
                      />
                      <p className="mt-1 text-xs text-gray-400">Ürün kartında gösterilir</p>
                    </div>
                    <div>
                      <Label>Promo Bitiş Tarihi</Label>
                      <Input type="date" {...form.register("promo_end_date")} className="mt-1" />
                      <p className="mt-1 text-xs text-gray-400">Geri sayım için</p>
                    </div>
                  </div>

                  <div className="flex items-center justify-between rounded-lg border border-pink-200 bg-gradient-to-r from-pink-50 to-purple-50 p-4">
                    <div className="flex items-center gap-3">
                      <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-pink-100">
                        <Gift className="h-5 w-5 text-pink-600" />
                      </div>
                      <div>
                        <p className="font-medium text-gray-800">Hediye Paketi Dahil</p>
                        <p className="text-sm text-gray-500">Özel ambalaj seçeneği</p>
                      </div>
                    </div>
                    <Controller
                      control={form.control}
                      name="is_gift_wrapped"
                      render={({ field }) => (
                        <Switch checked={field.value} onCheckedChange={field.onChange} />
                      )}
                    />
                  </div>
                </div>

                <Separator />

                {/* Social Proof */}
                <div className="space-y-4">
                  <div className="flex items-center gap-2 text-sm font-medium text-gray-700">
                    <Star className="h-4 w-4 text-amber-500" />
                    Sosyal Kanıt
                  </div>
                  <p className="-mt-2 text-xs text-gray-500">
                    Güven oluşturan istatistikler ve yorumlar
                  </p>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label>Puan (0-5)</Label>
                      <Controller
                        control={form.control}
                        name="rating"
                        render={({ field }) => (
                          <div className="relative mt-1">
                            <Input
                              type="number"
                              step="0.1"
                              min="0"
                              max="5"
                              placeholder="4.8"
                              value={field.value ?? ""}
                              onChange={(e) =>
                                field.onChange(e.target.value ? parseFloat(e.target.value) : null)
                              }
                            />
                            <Star className="absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 fill-amber-400 text-amber-400" />
                          </div>
                        )}
                      />
                    </div>
                    <div>
                      <Label>Yorum Sayısı</Label>
                      <Controller
                        control={form.control}
                        name="review_count"
                        render={({ field }) => (
                          <div className="relative mt-1">
                            <Input
                              type="number"
                              min="0"
                              placeholder="127"
                              value={field.value ?? ""}
                              onChange={(e) => field.onChange(parseInt(e.target.value) || 0)}
                            />
                            <MessageSquare className="absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
                          </div>
                        )}
                      />
                    </div>
                  </div>

                  <div>
                    <Label>Sosyal Kanıt Metni</Label>
                    <Input
                      {...form.register("social_proof_text")}
                      placeholder="Örn: 500+ mutlu aile bu kitabı seçti!"
                      className="mt-1"
                    />
                  </div>
                </div>

                <Separator />

                {/* Video */}
                <div className="space-y-4">
                  <div className="flex items-center gap-2 text-sm font-medium text-gray-700">
                    <Video className="h-4 w-4 text-red-500" />
                    Tanıtım Videosu
                  </div>

                  <div>
                    <Label>Video URL</Label>
                    <Input
                      {...form.register("video_url")}
                      placeholder="https://youtube.com/watch?v=... veya vimeo.com/..."
                      className="mt-1"
                    />
                    <p className="mt-1 text-xs text-gray-400">YouTube veya Vimeo linki</p>
                  </div>
                </div>

                <Separator />

                {/* Feature List */}
                <div className="space-y-4">
                  <div className="flex items-center gap-2 text-sm font-medium text-gray-700">
                    <ListChecks className="h-4 w-4 text-blue-600" />
                    Ürün Özellikleri
                  </div>
                  <p className="-mt-2 text-xs text-gray-500">
                    Ürün kartında madde işaretleri olarak gösterilir
                  </p>

                  {/* Add new feature */}
                  <div className="flex gap-2">
                    <Input
                      value={newFeature}
                      onChange={(e) => setNewFeature(e.target.value)}
                      placeholder="Yeni özellik ekle..."
                      onKeyDown={(e) => {
                        if (e.key === "Enter") {
                          e.preventDefault();
                          if (newFeature.trim()) {
                            setFeatureList([...featureList, newFeature.trim()]);
                            setNewFeature("");
                          }
                        }
                      }}
                    />
                    <Button
                      type="button"
                      variant="outline"
                      onClick={() => {
                        if (newFeature.trim()) {
                          setFeatureList([...featureList, newFeature.trim()]);
                          setNewFeature("");
                        }
                      }}
                      disabled={!newFeature.trim()}
                    >
                      <Plus className="h-4 w-4" />
                    </Button>
                  </div>

                  {/* Feature list */}
                  {featureList.length > 0 && (
                    <div className="space-y-2">
                      {featureList.map((feature, idx) => (
                        <motion.div
                          key={idx}
                          initial={{ opacity: 0, x: -10 }}
                          animate={{ opacity: 1, x: 0 }}
                          className="group flex items-center gap-2 rounded-lg bg-gray-50 p-2"
                        >
                          <Check className="h-4 w-4 flex-shrink-0 text-green-500" />
                          <span className="flex-1 text-sm">{feature}</span>
                          <button
                            type="button"
                            onClick={() => setFeatureList(featureList.filter((_, i) => i !== idx))}
                            className="p-1 text-gray-400 opacity-0 transition-opacity hover:text-red-500 group-hover:opacity-100"
                          >
                            <X className="h-4 w-4" />
                          </button>
                        </motion.div>
                      ))}
                    </div>
                  )}

                  {/* Suggestion badges */}
                  <div className="flex flex-wrap gap-2">
                    {[
                      "16 Sayfa",
                      "Sert Kapak",
                      "Hediye Paketi Dahil",
                      "Özel Tasarım",
                      "Hızlı Teslimat",
                      "Kaliteli Baskı",
                    ].map((suggestion) => (
                      <button
                        key={suggestion}
                        type="button"
                        onClick={() => {
                          if (!featureList.includes(suggestion)) {
                            setFeatureList([...featureList, suggestion]);
                          }
                        }}
                        disabled={featureList.includes(suggestion)}
                        className="rounded-full bg-blue-50 px-2 py-1 text-xs text-blue-700 hover:bg-blue-100 disabled:cursor-not-allowed disabled:opacity-50"
                      >
                        + {suggestion}
                      </button>
                    ))}
                  </div>
                </div>
              </>
            )}

            {/* ==================== SCENARIOS SECTION ==================== */}
            {activeSection === "scenarios" && (
              <div className="space-y-6">
                <div className="rounded-xl border border-orange-100 bg-orange-50 p-4">
                  <div className="flex items-start gap-3">
                    <BookOpen className="mt-0.5 h-5 w-5 shrink-0 text-orange-500" />
                    <div>
                      <p className="text-sm font-medium text-orange-800">Senaryo Şablon Ayarları</p>
                      <p className="mt-1 text-xs text-orange-600">
                        Bu ürün (fiziksel format) tüm senaryolarla uyumludur. Aşağıda mevcut senaryoları
                        görebilir, her senaryonun pazarlama ayarlarını{" "}
                        <strong>Senaryo Yönetimi</strong> sayfasından düzenleyebilirsiniz.
                      </p>
                    </div>
                  </div>
                </div>

                <div>
                  <div className="mb-3 flex items-center gap-2 text-sm font-medium text-gray-700">
                    <Sparkles className="h-4 w-4 text-purple-500" />
                    Mevcut Senaryolar ({scenariosForProduct.length})
                  </div>

                  {scenariosForProduct.length === 0 ? (
                    <div className="rounded-xl border-2 border-dashed border-gray-200 p-8 text-center">
                      <BookOpen className="mx-auto mb-3 h-10 w-10 text-gray-300" />
                      <p className="text-sm text-gray-500">Henüz senaryo eklenmemiş</p>
                      <p className="mt-1 text-xs text-gray-400">
                        Senaryo Yönetimi sayfasından senaryo ekleyebilirsiniz
                      </p>
                    </div>
                  ) : (
                    <div className="grid grid-cols-2 gap-3">
                      {scenariosForProduct.map((scenario) => (
                        <div
                          key={scenario.id}
                          className="group relative overflow-hidden rounded-xl border bg-white transition-all hover:border-purple-300 hover:shadow-md"
                        >
                          <div className="relative aspect-[4/3] overflow-hidden bg-gray-100">
                            {scenario.thumbnail_url ? (
                              <img
                                src={scenario.thumbnail_url}
                                alt={scenario.name}
                                className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
                                onError={(e) => {
                                  (e.target as HTMLImageElement).style.display = "none";
                                }}
                              />
                            ) : (
                              <div className="flex h-full w-full items-center justify-center">
                                <BookOpen className="h-8 w-8 text-gray-300" />
                              </div>
                            )}
                            {scenario.marketing_badge && (
                              <div className="absolute left-2 top-2 rounded-full bg-orange-500 px-2 py-0.5 text-[10px] font-medium text-white">
                                {scenario.marketing_badge}
                              </div>
                            )}
                          </div>
                          <div className="p-2.5">
                            <p className="truncate text-sm font-medium text-gray-900">{scenario.name}</p>
                            {scenario.tagline && (
                              <p className="mt-0.5 line-clamp-1 text-xs text-gray-500">{scenario.tagline}</p>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                <div className="rounded-xl border border-blue-100 bg-blue-50 p-4">
                  <p className="text-xs text-blue-700">
                    <strong>Arka Plan Şablon Ayarları:</strong> Bu ürünün kapak, iç sayfa ve arka kapak şablonları
                    &quot;Teknik &amp; Baskı&quot; sekmesinden yönetilir. Bu şablonlar tüm senaryolarda ortak kullanılır.
                  </p>
                </div>
              </div>
            )}

            {/* Sticky Footer */}
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
                    <Check className="mr-2 h-4 w-4" />
                    {editingProduct ? "Güncelle" : "Oluştur"}
                  </>
                )}
              </Button>
            </div>
          </form>
        </SheetContent>
      </Sheet>
    </div>
  );
}
