"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { motion, AnimatePresence } from "framer-motion";
import {
  Plus,
  Pencil,
  Trash2,
  Copy,
  ArrowLeft,
  X,
  Upload,
  Image as ImageIcon,
  CheckCircle2,
  AlertCircle,
  Eye,
  EyeOff,
  RotateCw,
  Settings2,
  FileText,
  Wand2,
  LayoutGrid,
  GripVertical,
  Variable,
  Type,
  Hash,
  List,
  AlignLeft,
  HelpCircle,
  TrendingUp,
  Star,
  Video,
  Settings,
  DollarSign,
  Layout,
  BookOpen,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { API_BASE_URL } from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { useToast } from "@/hooks/use-toast";

// ============ TYPES ============

// Custom Input Field Schema
interface CustomInputField {
  key: string; // Variable key used in templates, e.g., "spaceship_name"
  label: string; // Display label for users, e.g., "Uzay Gemisi Adı"
  type: "text" | "number" | "select" | "textarea";
  default?: string;
  options?: string[]; // For "select" type
  required?: boolean;
  placeholder?: string;
  help_text?: string;
}

interface Scenario {
  id: string;
  name: string;
  description: string | null;
  thumbnail_url: string;
  // V2: Story-only fields
  story_prompt_tr: string | null;
  location_en: string | null;
  default_page_count: number | null;
  flags: Record<string, boolean> | null;
  // Legacy (kept for compat, hidden from UI)
  cover_prompt_template: string;
  page_prompt_template: string;
  ai_prompt_template?: string | null;
  // Dynamic Variables / Custom Inputs
  custom_inputs_schema?: CustomInputField[];
  available_variables?: string[];
  // Media
  gallery_images: string[];
  // Marketing Fields
  marketing_video_url?: string | null;
  marketing_gallery?: string[];
  marketing_price_label?: string | null;
  marketing_features?: string[];
  marketing_badge?: string | null;
  age_range?: string | null;
  estimated_duration?: string | null;
  tagline?: string | null;
  rating?: number | null;
  review_count?: number;
  // Book Structure (marketing display)
  story_page_count?: number | null;
  cover_count?: number | null;
  greeting_page_count?: number | null;
  back_info_page_count?: number | null;
  total_page_count?: number | null;
  // Outfit Design (scenario-specific, gender-specific)
  outfit_girl?: string | null;
  outfit_boy?: string | null;
  // Product Link & Override Settings
  linked_product_id?: string | null;
  linked_product_name?: string | null;
  price_override_base?: number | null;
  price_override_extra_page?: number | null;
  cover_template_id_override?: string | null;
  inner_template_id_override?: string | null;
  back_template_id_override?: string | null;
  ai_config_id_override?: string | null;
  paper_type_override?: string | null;
  paper_finish_override?: string | null;
  cover_type_override?: string | null;
  lamination_override?: string | null;
  orientation_override?: string | null;
  min_page_count_override?: number | null;
  max_page_count_override?: number | null;
  // Display
  is_active: boolean;
  display_order: number;
  created_at: string | null;
}

// ============ FORM SCHEMA (V2) ============
const scenarioSchema = z.object({
  name: z.string().min(1, "Senaryo adı zorunludur"),
  description: z.string().optional(),
  // V2: Story-only fields
  story_prompt_tr: z.string().optional(),
  location_en: z.string().optional(),
  default_page_count: z.number().min(2).max(30).optional(),
  no_family: z.boolean(),
  // Display
  is_active: z.boolean(),
  display_order: z.number(),
});

type ScenarioFormData = z.infer<typeof scenarioSchema>;

// ============ GALLERY IMAGE UPLOADER ============
function GalleryImageUploader({
  images,
  onImagesChange,
}: {
  images: string[];
  onImagesChange: (images: string[]) => void;
}) {
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFiles = useCallback(
    (files: FileList | null) => {
      if (!files) return;

      Array.from(files).forEach((file) => {
        if (file.type.startsWith("image/")) {
          const reader = new FileReader();
          reader.onload = (e) => {
            const result = e.target?.result as string;
            onImagesChange([...images, result]);
          };
          reader.readAsDataURL(file);
        }
      });
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

  const removeImage = (index: number) => {
    onImagesChange(images.filter((_, i) => i !== index));
  };

  return (
    <div className="space-y-3">
      <div
        onClick={() => fileInputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        className={`
          cursor-pointer rounded-xl border-2 border-dashed p-4 text-center transition-all
          ${
            isDragging
              ? "border-purple-500 bg-purple-50"
              : "border-gray-300 hover:border-purple-400 hover:bg-purple-50/50"
          }
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
        <ImageIcon
          className={`mx-auto mb-2 h-8 w-8 ${isDragging ? "text-purple-500" : "text-gray-400"}`}
        />
        <p className="text-sm text-gray-600">Galeri görselleri ekleyin</p>
        <p className="mt-1 text-xs text-gray-400">Sürükle & Bırak veya Tıkla</p>
      </div>

      {images.length > 0 && (
        <div className="grid grid-cols-4 gap-2">
          {images.map((img, idx) => (
            <div
              key={idx}
              className="group relative aspect-video overflow-hidden rounded-lg border bg-gray-50"
            >
              <img src={img} alt={`Gallery ${idx + 1}`} className="h-full w-full object-cover" />
              <button
                type="button"
                onClick={() => removeImage(idx)}
                className="absolute right-1 top-1 rounded-full bg-red-500 p-1 text-white opacity-0 transition-opacity group-hover:opacity-100"
              >
                <X className="h-3 w-3" />
              </button>
              <div className="absolute bottom-1 left-1 rounded bg-black/60 px-1.5 py-0.5 text-[10px] text-white">
                {idx + 1}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ============ VARIABLE MANAGER COMPONENT ============
function VariableManager({
  variables,
  onVariablesChange,
}: {
  variables: CustomInputField[];
  onVariablesChange: (variables: CustomInputField[]) => void;
}) {
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const [newField, setNewField] = useState<Partial<CustomInputField>>({
    key: "",
    label: "",
    type: "text",
    required: true,
  });
  const [showAddForm, setShowAddForm] = useState(false);

  const inputTypeOptions = [
    { value: "text", label: "Metin", icon: Type },
    { value: "number", label: "Sayı", icon: Hash },
    { value: "select", label: "Seçenek", icon: List },
    { value: "textarea", label: "Uzun Metin", icon: AlignLeft },
  ];

  const addVariable = () => {
    if (!newField.key || !newField.label) return;

    // Sanitize key (remove spaces, special chars)
    const sanitizedKey = newField.key
      .toLowerCase()
      .replace(/\s+/g, "_")
      .replace(/[^a-z0-9_]/g, "");

    const field: CustomInputField = {
      key: sanitizedKey,
      label: newField.label,
      type: (newField.type as CustomInputField["type"]) || "text",
      default: newField.default || undefined,
      options: newField.type === "select" ? newField.options || [] : undefined,
      required: newField.required ?? true,
      placeholder: newField.placeholder || undefined,
      help_text: newField.help_text || undefined,
    };

    onVariablesChange([...variables, field]);
    setNewField({ key: "", label: "", type: "text", required: true });
    setShowAddForm(false);
  };

  const updateVariable = (index: number, updates: Partial<CustomInputField>) => {
    const updated = [...variables];
    updated[index] = { ...updated[index], ...updates };
    onVariablesChange(updated);
  };

  const removeVariable = (index: number) => {
    onVariablesChange(variables.filter((_, i) => i !== index));
  };

  const moveVariable = (index: number, direction: "up" | "down") => {
    const newIndex = direction === "up" ? index - 1 : index + 1;
    if (newIndex < 0 || newIndex >= variables.length) return;

    const updated = [...variables];
    [updated[index], updated[newIndex]] = [updated[newIndex], updated[index]];
    onVariablesChange(updated);
  };

  return (
    <div className="space-y-4">
      {/* Existing Variables */}
      {variables.length > 0 && (
        <div className="space-y-2">
          {variables.map((variable, index) => (
            <div
              key={variable.key}
              className="rounded-lg border bg-white p-3 transition-colors hover:border-purple-300"
            >
              {editingIndex === index ? (
                // Edit Mode
                <div className="space-y-3">
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <Label className="text-xs">Değişken Anahtarı</Label>
                      <Input
                        value={variable.key}
                        onChange={(e) =>
                          updateVariable(index, {
                            key: e.target.value
                              .toLowerCase()
                              .replace(/\s+/g, "_")
                              .replace(/[^a-z0-9_]/g, ""),
                          })
                        }
                        className="mt-1 font-mono text-sm"
                        placeholder="favorite_toy"
                      />
                    </div>
                    <div>
                      <Label className="text-xs">Kullanıcı Etiketi</Label>
                      <Input
                        value={variable.label}
                        onChange={(e) => updateVariable(index, { label: e.target.value })}
                        className="mt-1"
                        placeholder="En Sevdiği Oyuncak"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <Label className="text-xs">Tür</Label>
                      <select
                        value={variable.type}
                        onChange={(e) =>
                          updateVariable(index, {
                            type: e.target.value as CustomInputField["type"],
                          })
                        }
                        className="mt-1 h-9 w-full rounded-md border border-input bg-background px-3 text-sm"
                      >
                        {inputTypeOptions.map((opt) => (
                          <option key={opt.value} value={opt.value}>
                            {opt.label}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <Label className="text-xs">Varsayılan</Label>
                      <Input
                        value={variable.default || ""}
                        onChange={(e) => updateVariable(index, { default: e.target.value })}
                        className="mt-1"
                        placeholder="Varsayılan değer"
                      />
                    </div>
                  </div>

                  {variable.type === "select" && (
                    <div>
                      <Label className="text-xs">Seçenekler (virgülle ayırın)</Label>
                      <Input
                        value={(variable.options || []).join(", ")}
                        onChange={(e) =>
                          updateVariable(index, {
                            options: e.target.value
                              .split(",")
                              .map((s) => s.trim())
                              .filter(Boolean),
                          })
                        }
                        className="mt-1"
                        placeholder="Seçenek 1, Seçenek 2, Seçenek 3"
                      />
                    </div>
                  )}

                  <div className="flex items-center gap-4">
                    <label className="flex items-center gap-2 text-sm">
                      <input
                        type="checkbox"
                        checked={variable.required ?? true}
                        onChange={(e) => updateVariable(index, { required: e.target.checked })}
                        className="rounded"
                      />
                      Zorunlu
                    </label>
                  </div>

                  <div className="flex gap-2">
                    <Button
                      type="button"
                      size="sm"
                      onClick={() => setEditingIndex(null)}
                      className="bg-purple-600 hover:bg-purple-700"
                    >
                      <CheckCircle2 className="mr-1 h-3 w-3" />
                      Tamam
                    </Button>
                  </div>
                </div>
              ) : (
                // Display Mode
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="flex flex-col gap-1">
                      <button
                        type="button"
                        onClick={() => moveVariable(index, "up")}
                        disabled={index === 0}
                        className="text-gray-400 hover:text-gray-600 disabled:opacity-30"
                      >
                        <GripVertical className="h-3 w-3" />
                      </button>
                    </div>

                    <div className="flex items-center gap-2">
                      {inputTypeOptions.find((t) => t.value === variable.type)?.icon && (
                        <div className="flex h-8 w-8 items-center justify-center rounded bg-purple-100">
                          {(() => {
                            const IconComp =
                              inputTypeOptions.find((t) => t.value === variable.type)?.icon || Type;
                            return <IconComp className="h-4 w-4 text-purple-600" />;
                          })()}
                        </div>
                      )}
                      <div>
                        <div className="flex items-center gap-2">
                          <code className="rounded bg-purple-50 px-1.5 py-0.5 font-mono text-sm text-purple-600">
                            {`{${variable.key}}`}
                          </code>
                          {!variable.required && (
                            <Badge variant="outline" className="text-[10px]">
                              Opsiyonel
                            </Badge>
                          )}
                        </div>
                        <p className="mt-0.5 text-xs text-gray-500">{variable.label}</p>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-1">
                    <Button
                      type="button"
                      size="sm"
                      variant="ghost"
                      onClick={() => setEditingIndex(index)}
                      className="h-7 w-7 p-0"
                    >
                      <Pencil className="h-3 w-3" />
                    </Button>
                    <Button
                      type="button"
                      size="sm"
                      variant="ghost"
                      onClick={() => removeVariable(index)}
                      className="h-7 w-7 p-0 text-red-500 hover:bg-red-50 hover:text-red-700"
                    >
                      <Trash2 className="h-3 w-3" />
                    </Button>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Add New Variable Form */}
      {showAddForm ? (
        <div className="space-y-3 rounded-lg border-2 border-dashed border-purple-300 bg-purple-50/50 p-4">
          <div className="flex items-center gap-2 text-sm font-medium text-purple-700">
            <Variable className="h-4 w-4" />
            Yeni Değişken Ekle
          </div>

          <div className="grid grid-cols-2 gap-2">
            <div>
              <Label className="text-xs">Değişken Anahtarı *</Label>
              <Input
                value={newField.key || ""}
                onChange={(e) =>
                  setNewField({
                    ...newField,
                    key: e.target.value
                      .toLowerCase()
                      .replace(/\s+/g, "_")
                      .replace(/[^a-z0-9_]/g, ""),
                  })
                }
                className="mt-1 font-mono text-sm"
                placeholder="favorite_toy"
              />
              <p className="mt-0.5 text-[10px] text-gray-400">
                Promptta {`{${newField.key || "key"}}`} olarak kullanılır
              </p>
            </div>
            <div>
              <Label className="text-xs">Kullanıcı Etiketi *</Label>
              <Input
                value={newField.label || ""}
                onChange={(e) => setNewField({ ...newField, label: e.target.value })}
                className="mt-1"
                placeholder="En Sevdiği Oyuncak"
              />
              <p className="mt-0.5 text-[10px] text-gray-400">Kullanıcının göreceği etiket</p>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-2">
            <div>
              <Label className="text-xs">Tür</Label>
              <select
                value={newField.type || "text"}
                onChange={(e) =>
                  setNewField({ ...newField, type: e.target.value as CustomInputField["type"] })
                }
                className="mt-1 h-9 w-full rounded-md border border-input bg-background px-3 text-sm"
              >
                {inputTypeOptions.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <Label className="text-xs">Varsayılan</Label>
              <Input
                value={newField.default || ""}
                onChange={(e) => setNewField({ ...newField, default: e.target.value })}
                className="mt-1"
                placeholder="Opsiyonel"
              />
            </div>
            <div>
              <Label className="text-xs">Placeholder</Label>
              <Input
                value={newField.placeholder || ""}
                onChange={(e) => setNewField({ ...newField, placeholder: e.target.value })}
                className="mt-1"
                placeholder="İpucu metni"
              />
            </div>
          </div>

          {newField.type === "select" && (
            <div>
              <Label className="text-xs">Seçenekler (virgülle ayırın)</Label>
              <Input
                value={(newField.options || []).join(", ")}
                onChange={(e) =>
                  setNewField({
                    ...newField,
                    options: e.target.value
                      .split(",")
                      .map((s) => s.trim())
                      .filter(Boolean),
                  })
                }
                className="mt-1"
                placeholder="Kedi, Köpek, Kuş"
              />
            </div>
          )}

          <div className="flex items-center gap-4">
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={newField.required ?? true}
                onChange={(e) => setNewField({ ...newField, required: e.target.checked })}
                className="rounded"
              />
              Zorunlu Alan
            </label>
          </div>

          <div className="flex gap-2">
            <Button
              type="button"
              size="sm"
              variant="outline"
              onClick={() => {
                setShowAddForm(false);
                setNewField({ key: "", label: "", type: "text", required: true });
              }}
            >
              İptal
            </Button>
            <Button
              type="button"
              size="sm"
              onClick={addVariable}
              disabled={!newField.key || !newField.label}
              className="bg-purple-600 hover:bg-purple-700"
            >
              <Plus className="mr-1 h-3 w-3" />
              Ekle
            </Button>
          </div>
        </div>
      ) : (
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={() => setShowAddForm(true)}
          className="w-full border-dashed hover:border-purple-400 hover:bg-purple-50"
        >
          <Plus className="mr-2 h-4 w-4" />
          Yeni Değişken Ekle
        </Button>
      )}

      {/* Usage hint */}
      {variables.length > 0 && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-3">
          <div className="flex items-start gap-2">
            <HelpCircle className="mt-0.5 h-4 w-4 shrink-0 text-amber-600" />
            <div className="text-xs text-amber-800">
              <p className="font-medium">Kullanım:</p>
              <p className="mt-1">
                Bu değişkenleri prompt şablonlarında{" "}
                <code className="rounded bg-amber-100 px-1">{`{değişken_adı}`}</code> formatında
                kullanabilirsiniz.
              </p>
              <div className="mt-2 flex flex-wrap gap-1">
                {variables.map((v) => (
                  <Badge key={v.key} variant="outline" className="bg-white font-mono text-[10px]">
                    {`{${v.key}}`}
                  </Badge>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ============ SCENARIO CARD PREVIEW ============
function ScenarioPreview({ scenario }: { scenario: Partial<Scenario> }) {
  return (
    <div className="relative overflow-hidden rounded-xl bg-gradient-to-br from-purple-600 to-pink-500">
      {/* Thumbnail */}
      <div className="relative aspect-[4/3]">
        {scenario.thumbnail_url ? (
          <img
            src={scenario.thumbnail_url}
            alt={scenario.name || "Preview"}
            className="h-full w-full object-cover"
          />
        ) : (
          <div className="flex h-full w-full items-center justify-center bg-purple-200">
            <ImageIcon className="h-12 w-12 text-purple-400" />
          </div>
        )}
      </div>

      {/* Content */}
      <div className="bg-white p-3">
        <h3 className="font-bold text-gray-900">{scenario.name || "Senaryo Adı"}</h3>
        <p className="mt-1 line-clamp-2 text-sm text-gray-500">
          {scenario.description || "Açıklama..."}
        </p>

        {/* Gallery preview */}
        {scenario.gallery_images && scenario.gallery_images.length > 0 && (
          <div className="mt-2 flex gap-1">
            {scenario.gallery_images.slice(0, 3).map((img, i) => (
              <div key={i} className="h-8 w-8 overflow-hidden rounded">
                <img src={img} alt={`Gallery ${i}`} className="h-full w-full object-cover" />
              </div>
            ))}
            {scenario.gallery_images.length > 3 && (
              <span className="flex items-center text-xs text-gray-400">
                +{scenario.gallery_images.length - 3}
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// ============ PRODUCT TYPE (for dropdown) ============
interface ProductOption {
  id: string;
  name: string;
  base_price: number;
  extra_page_price: number;
  default_page_count: number;
  min_page_count: number;
  max_page_count: number;
  paper_type: string;
  paper_finish: string;
  cover_type: string;
  lamination: string | null;
  orientation: string;
  cover_template_id: string | null;
  inner_template_id: string | null;
  back_template_id: string | null;
  ai_config_id: string | null;
}

// ============ MAIN PAGE COMPONENT ============
export default function AdminScenariosPage() {
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [products, setProducts] = useState<ProductOption[]>([]);
  const [loading, setLoading] = useState(true);
  const [isEditorOpen, setIsEditorOpen] = useState(false);
  const [editingScenario, setEditingScenario] = useState<Scenario | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);

  // Image states
  const [thumbnailPreview, setThumbnailPreview] = useState<string | null>(null);
  const [thumbnailBase64, setThumbnailBase64] = useState<string>("");
  const [galleryImages, setGalleryImages] = useState<string[]>([]);

  // Marketing states
  const [marketingGallery, setMarketingGallery] = useState<string[]>([]);
  const [marketingFeatures, setMarketingFeatures] = useState<string[]>([]);
  const [marketingVideoUrl, setMarketingVideoUrl] = useState<string>("");
  const [marketingPriceLabel, setMarketingPriceLabel] = useState<string>("");
  const [marketingBadge, setMarketingBadge] = useState<string>("");
  const [ageRange, setAgeRange] = useState<string>("");
  const [estimatedDuration, setEstimatedDuration] = useState<string>("");
  const [tagline, setTagline] = useState<string>("");
  const [rating, setRating] = useState<string>("");
  const [reviewCount, setReviewCount] = useState<string>("");
  const [newFeatureInput, setNewFeatureInput] = useState<string>("");
  const [activeTab, setActiveTab] = useState<"content" | "marketing" | "overrides">("content");
  // Book structure states
  const [storyPageCount, setStoryPageCount] = useState<string>("");
  const [coverCount, setCoverCount] = useState<string>("2");
  const [greetingPageCount, setGreetingPageCount] = useState<string>("2");
  const [backInfoPageCount, setBackInfoPageCount] = useState<string>("1");
  // Outfit design states
  const [outfitGirl, setOutfitGirl] = useState<string>("");
  const [outfitBoy, setOutfitBoy] = useState<string>("");
  // Product link & override states
  const [linkedProductId, setLinkedProductId] = useState<string>("");
  const [priceOverrideBase, setPriceOverrideBase] = useState<string>("");
  const [priceOverrideExtraPage, setPriceOverrideExtraPage] = useState<string>("");
  const [coverTemplateIdOverride, setCoverTemplateIdOverride] = useState<string>("");
  const [innerTemplateIdOverride, setInnerTemplateIdOverride] = useState<string>("");
  const [backTemplateIdOverride, setBackTemplateIdOverride] = useState<string>("");
  const [aiConfigIdOverride, setAiConfigIdOverride] = useState<string>("");
  const [paperTypeOverride, setPaperTypeOverride] = useState<string>("");
  const [paperFinishOverride, setPaperFinishOverride] = useState<string>("");
  const [coverTypeOverride, setCoverTypeOverride] = useState<string>("");
  const [laminationOverride, setLaminationOverride] = useState<string>("");
  const [orientationOverride, setOrientationOverride] = useState<string>("");
  const [minPageCountOverride, setMinPageCountOverride] = useState<string>("");
  const [maxPageCountOverride, setMaxPageCountOverride] = useState<string>("");

  // Custom inputs (dynamic variables)
  const [customInputs, setCustomInputs] = useState<CustomInputField[]>([]);

  const router = useRouter();
  const { toast } = useToast();
  const thumbnailInputRef = useRef<HTMLInputElement>(null);

  const form = useForm<ScenarioFormData>({
    resolver: zodResolver(scenarioSchema),
    defaultValues: {
      name: "",
      description: "",
      story_prompt_tr: "",
      location_en: "",
      default_page_count: 6,
      no_family: false,
      is_active: true,
      display_order: 0,
    },
  });

  const watchedValues = form.watch();

  useEffect(() => {
    checkAuth();
    fetchScenarios();
    fetchProducts();
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

  const getAuthHeaders = () => {
    const token = localStorage.getItem("token");
    return {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    };
  };

  const fetchScenarios = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/admin/scenarios?include_inactive=true`, {
        headers: getAuthHeaders(),
      });
      if (response.status === 401) {
        router.push("/auth/login");
        return;
      }
      if (response.ok) {
        const data = await response.json();
        setScenarios(data);
      }
    } catch (error) {
      toast({ title: "Hata", description: "Senaryolar yüklenemedi", variant: "destructive" });
    } finally {
      setLoading(false);
    }
  };

  const fetchProducts = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/admin/products`, {
        headers: getAuthHeaders(),
      });
      if (response.ok) {
        const data = await response.json();
        setProducts(data);
      }
    } catch {
      // Non-critical; products list is optional
    }
  };

  const openEditor = (scenario?: Scenario) => {
    if (scenario) {
      setEditingScenario(scenario);
      form.reset({
        name: scenario.name,
        description: scenario.description || "",
        story_prompt_tr: scenario.story_prompt_tr || "",
        location_en: scenario.location_en || "",
        default_page_count: scenario.default_page_count ?? 6,
        no_family: scenario.flags?.no_family ?? false,
        is_active: scenario.is_active,
        display_order: scenario.display_order,
      });
      setThumbnailPreview(scenario.thumbnail_url);
      setGalleryImages(scenario.gallery_images || []);
      setCustomInputs(scenario.custom_inputs_schema || []);
      // Marketing fields
      setMarketingGallery(scenario.marketing_gallery || []);
      setMarketingFeatures(scenario.marketing_features || []);
      setMarketingVideoUrl(scenario.marketing_video_url || "");
      setMarketingPriceLabel(scenario.marketing_price_label || "");
      setMarketingBadge(scenario.marketing_badge || "");
      setAgeRange(scenario.age_range || "");
      setEstimatedDuration(scenario.estimated_duration || "");
      setTagline(scenario.tagline || "");
      setRating(scenario.rating != null ? String(scenario.rating) : "");
      setReviewCount(scenario.review_count != null ? String(scenario.review_count) : "");
      // Book structure fields
      setStoryPageCount(scenario.story_page_count != null ? String(scenario.story_page_count) : "");
      setCoverCount(scenario.cover_count != null ? String(scenario.cover_count) : "2");
      setGreetingPageCount(scenario.greeting_page_count != null ? String(scenario.greeting_page_count) : "2");
      setBackInfoPageCount(scenario.back_info_page_count != null ? String(scenario.back_info_page_count) : "1");
      // Outfit design fields
      setOutfitGirl(scenario.outfit_girl || "");
      setOutfitBoy(scenario.outfit_boy || "");
      // Product link & override fields
      setLinkedProductId(scenario.linked_product_id || "");
      setPriceOverrideBase(scenario.price_override_base != null ? String(scenario.price_override_base) : "");
      setPriceOverrideExtraPage(scenario.price_override_extra_page != null ? String(scenario.price_override_extra_page) : "");
      setCoverTemplateIdOverride(scenario.cover_template_id_override || "");
      setInnerTemplateIdOverride(scenario.inner_template_id_override || "");
      setBackTemplateIdOverride(scenario.back_template_id_override || "");
      setAiConfigIdOverride(scenario.ai_config_id_override || "");
      setPaperTypeOverride(scenario.paper_type_override || "");
      setPaperFinishOverride(scenario.paper_finish_override || "");
      setCoverTypeOverride(scenario.cover_type_override || "");
      setLaminationOverride(scenario.lamination_override || "");
      setOrientationOverride(scenario.orientation_override || "");
      setMinPageCountOverride(scenario.min_page_count_override != null ? String(scenario.min_page_count_override) : "");
      setMaxPageCountOverride(scenario.max_page_count_override != null ? String(scenario.max_page_count_override) : "");
    } else {
      setEditingScenario(null);
      form.reset({
        name: "",
        description: "",
        story_prompt_tr: "",
        location_en: "",
        default_page_count: 6,
        no_family: false,
        is_active: true,
        display_order: scenarios.length,
      });
      setThumbnailPreview(null);
      setThumbnailBase64("");
      setGalleryImages([]);
      setCustomInputs([]);
      // Reset marketing fields
      setMarketingGallery([]);
      setMarketingFeatures([]);
      setMarketingVideoUrl("");
      setMarketingPriceLabel("");
      setMarketingBadge("");
      setAgeRange("");
      setEstimatedDuration("");
      setTagline("");
      setRating("");
      setReviewCount("");
      // Reset book structure fields
      setStoryPageCount("");
      setCoverCount("2");
      setGreetingPageCount("2");
      setBackInfoPageCount("1");
      // Reset outfit design fields
      setOutfitGirl("");
      setOutfitBoy("");
      // Reset product link & override fields
      setLinkedProductId("");
      setPriceOverrideBase("");
      setPriceOverrideExtraPage("");
      setCoverTemplateIdOverride("");
      setInnerTemplateIdOverride("");
      setBackTemplateIdOverride("");
      setAiConfigIdOverride("");
      setPaperTypeOverride("");
      setPaperFinishOverride("");
      setCoverTypeOverride("");
      setLaminationOverride("");
      setOrientationOverride("");
      setMinPageCountOverride("");
      setMaxPageCountOverride("");
    }
    setActiveTab("content");
    setIsEditorOpen(true);
  };

  const closeEditor = () => {
    setIsEditorOpen(false);
    setEditingScenario(null);
    setThumbnailPreview(null);
    setThumbnailBase64("");
    setGalleryImages([]);
    setCustomInputs([]);
    setMarketingGallery([]);
    setMarketingFeatures([]);
    setMarketingVideoUrl("");
    setMarketingPriceLabel("");
    setMarketingBadge("");
    setAgeRange("");
    setEstimatedDuration("");
    setTagline("");
    setRating("");
    setReviewCount("");
    setPriceOverrideBase("");
    setPriceOverrideExtraPage("");
    setCoverTemplateIdOverride("");
    setInnerTemplateIdOverride("");
    setBackTemplateIdOverride("");
    setActiveTab("content");
    form.reset();
  };

  const handleThumbnailChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (ev) => {
        const base64 = ev.target?.result as string;
        setThumbnailBase64(base64);
        setThumbnailPreview(base64);
      };
      reader.readAsDataURL(file);
    }
  };

  const onSubmit = async (data: ScenarioFormData) => {
    try {
      const payload: Record<string, unknown> = {
        name: data.name,
        description: data.description || null,
        // V2 story-only fields
        story_prompt_tr: data.story_prompt_tr || null,
        location_en: data.location_en || null,
        default_page_count: data.default_page_count ?? 6,
        flags: { no_family: data.no_family ?? false },
        // Other
        custom_inputs_schema: customInputs.length > 0 ? customInputs : null,
        gallery_images: galleryImages,
        is_active: data.is_active,
        display_order: data.display_order,
        // Marketing fields
        marketing_video_url: marketingVideoUrl || null,
        marketing_gallery: marketingGallery,
        marketing_price_label: marketingPriceLabel || null,
        marketing_features: marketingFeatures,
        marketing_badge: marketingBadge || null,
        age_range: ageRange || null,
        estimated_duration: estimatedDuration || null,
        tagline: tagline || null,
        rating: rating ? parseFloat(rating) : null,
        review_count: reviewCount ? parseInt(reviewCount, 10) : 0,
        // Book structure fields
        story_page_count: storyPageCount ? parseInt(storyPageCount, 10) : null,
        cover_count: coverCount ? parseInt(coverCount, 10) : 2,
        greeting_page_count: greetingPageCount ? parseInt(greetingPageCount, 10) : 2,
        back_info_page_count: backInfoPageCount ? parseInt(backInfoPageCount, 10) : 1,
        // Outfit design fields
        outfit_girl: outfitGirl || null,
        outfit_boy: outfitBoy || null,
        // Product link & override fields
        linked_product_id: linkedProductId || null,
        price_override_base: priceOverrideBase ? parseFloat(priceOverrideBase) : null,
        price_override_extra_page: priceOverrideExtraPage ? parseFloat(priceOverrideExtraPage) : null,
        cover_template_id_override: coverTemplateIdOverride || null,
        inner_template_id_override: innerTemplateIdOverride || null,
        back_template_id_override: backTemplateIdOverride || null,
        ai_config_id_override: aiConfigIdOverride || null,
        paper_type_override: paperTypeOverride || null,
        paper_finish_override: paperFinishOverride || null,
        cover_type_override: coverTypeOverride || null,
        lamination_override: laminationOverride || null,
        orientation_override: orientationOverride || null,
        min_page_count_override: minPageCountOverride ? parseInt(minPageCountOverride, 10) : null,
        max_page_count_override: maxPageCountOverride ? parseInt(maxPageCountOverride, 10) : null,
      };

      if (thumbnailBase64) {
        payload.thumbnail_base64 = thumbnailBase64;
      }

      const url = editingScenario
        ? `${API_BASE_URL}/admin/scenarios/${editingScenario.id}`
        : `${API_BASE_URL}/admin/scenarios`;

      const response = await fetch(url, {
        method: editingScenario ? "PATCH" : "POST",
        headers: getAuthHeaders(),
        body: JSON.stringify(payload),
      });

      if (response.ok) {
        toast({
          title: "Başarılı",
          description: editingScenario ? "Senaryo güncellendi" : "Senaryo oluşturuldu",
        });
        closeEditor();
        fetchScenarios();
      } else {
        const error = await response.json();
        throw new Error(error.detail || "Hata oluştu");
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : "Bilinmeyen hata";
      toast({ title: "Hata", description: message, variant: "destructive" });
    }
  };

  const handleDelete = async (scenarioId: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/admin/scenarios/${scenarioId}`, {
        method: "DELETE",
        headers: getAuthHeaders(),
      });

      if (response.ok) {
        toast({ title: "Başarılı", description: "Senaryo silindi" });
        fetchScenarios();
      }
    } catch (error) {
      toast({ title: "Hata", description: "Silme başarısız", variant: "destructive" });
    } finally {
      setDeleteConfirm(null);
    }
  };

  const handleDuplicate = async (scenarioId: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/admin/scenarios/${scenarioId}/duplicate`, {
        method: "POST",
        headers: getAuthHeaders(),
      });

      if (response.ok) {
        toast({ title: "Başarılı", description: "Senaryo kopyalandı" });
        fetchScenarios();
      }
    } catch (error) {
      toast({ title: "Hata", description: "Kopyalama başarısız", variant: "destructive" });
    }
  };

  const toggleActive = async (scenario: Scenario) => {
    try {
      const response = await fetch(`${API_BASE_URL}/admin/scenarios/${scenario.id}`, {
        method: "PATCH",
        headers: getAuthHeaders(),
        body: JSON.stringify({ is_active: !scenario.is_active }),
      });

      if (response.ok) {
        toast({ title: "Başarılı", description: "Durum güncellendi" });
        fetchScenarios();
      }
    } catch (error) {
      toast({ title: "Hata", description: "Güncelleme başarısız", variant: "destructive" });
    }
  };

  // Preview data for the form
  const previewData: Partial<Scenario> = {
    name: watchedValues.name,
    description: watchedValues.description,
    thumbnail_url: thumbnailPreview || "",
    gallery_images: galleryImages,
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header */}
      <header className="sticky top-0 z-40 border-b bg-white shadow-sm">
        <div className="mx-auto flex max-w-[1600px] items-center justify-between px-6 py-4">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="sm" onClick={() => router.push("/admin")}>
              <ArrowLeft className="mr-1 h-4 w-4" />
              Geri
            </Button>
            <div>
              <h1 className="flex items-center gap-2 text-2xl font-bold text-gray-900">
                <Wand2 className="h-6 w-6 text-purple-600" />
                Senaryo Yönetimi
              </h1>
              <p className="mt-0.5 text-sm text-gray-500">
                Hikaye temalarını, videoları ve promosyonları yönetin
              </p>
            </div>
          </div>
          <Button onClick={() => openEditor()} className="bg-purple-600 hover:bg-purple-700">
            <Plus className="mr-2 h-4 w-4" />
            Yeni Senaryo
          </Button>
        </div>
      </header>

      <main className="mx-auto max-w-[1600px] px-6 py-8">
        {/* Stats */}
        <div className="mb-8 grid grid-cols-3 gap-4">
          {[
            { label: "Toplam", value: scenarios.length, icon: LayoutGrid, color: "purple" },
            {
              label: "Aktif",
              value: scenarios.filter((s) => s.is_active).length,
              icon: Eye,
              color: "green",
            },
            {
              label: "Pasif",
              value: scenarios.filter((s) => !s.is_active).length,
              icon: EyeOff,
              color: "gray",
            },
          ].map((stat) => (
            <Card key={stat.label} className="border-0 shadow-sm">
              <CardContent className="flex items-center gap-4 p-4">
                <div
                  className={`h-12 w-12 rounded-xl bg-${stat.color}-100 flex items-center justify-center`}
                >
                  <stat.icon className={`h-6 w-6 text-${stat.color}-600`} />
                </div>
                <div>
                  <p className="text-2xl font-bold">{stat.value}</p>
                  <p className="text-sm text-gray-500">{stat.label}</p>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Scenarios Grid */}
        {loading ? (
          <div className="py-12 text-center">
            <RotateCw className="mx-auto mb-4 h-8 w-8 animate-spin text-purple-600" />
            <p className="text-gray-500">Yükleniyor...</p>
          </div>
        ) : scenarios.length === 0 ? (
          <Card className="border-2 border-dashed">
            <CardContent className="py-16 text-center">
              <Wand2 className="mx-auto mb-4 h-16 w-16 text-gray-300" />
              <h3 className="mb-2 text-xl font-semibold text-gray-700">Henüz senaryo yok</h3>
              <p className="mb-6 text-gray-500">İlk hikaye senaryonuzu oluşturun</p>
              <Button onClick={() => openEditor()} className="bg-purple-600 hover:bg-purple-700">
                <Plus className="mr-2 h-4 w-4" />
                İlk Senaryoyu Oluştur
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4">
            {scenarios.map((scenario) => (
              <Card
                key={scenario.id}
                className={`group overflow-hidden transition-all hover:shadow-lg ${!scenario.is_active ? "opacity-60" : ""}`}
              >
                <CardContent className="p-0">
                  {/* Thumbnail */}
                  <div className="relative aspect-[4/3] overflow-hidden bg-gradient-to-br from-purple-100 to-pink-100">
                    {scenario.thumbnail_url ? (
                      <img
                        src={scenario.thumbnail_url}
                        alt={scenario.name}
                        className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
                      />
                    ) : (
                      <div className="flex h-full w-full items-center justify-center">
                        <Wand2 className="h-16 w-16 text-purple-300" />
                      </div>
                    )}

                    {/* Top badges */}
                    <div className="absolute left-2 top-2 flex flex-wrap gap-1">
                      {!scenario.is_active && (
                        <Badge variant="secondary" className="shadow-sm">
                          <EyeOff className="mr-1 h-3 w-3" />
                          Pasif
                        </Badge>
                      )}
                      {scenario.marketing_badge && (
                        <Badge className="bg-orange-500 text-white shadow-sm">
                          {scenario.marketing_badge}
                        </Badge>
                      )}
                    </div>

                    {/* Quick Actions */}
                    <div className="absolute right-2 top-2 flex gap-1 opacity-0 transition-opacity group-hover:opacity-100">
                      <Button
                        size="sm"
                        variant="secondary"
                        className="h-8 w-8 bg-white/90 p-0 shadow-sm hover:bg-white"
                        onClick={() => openEditor(scenario)}
                      >
                        <Pencil className="h-3.5 w-3.5" />
                      </Button>
                      <Button
                        size="sm"
                        variant="secondary"
                        className="h-8 w-8 bg-white/90 p-0 shadow-sm hover:bg-white"
                        onClick={() => handleDuplicate(scenario.id)}
                      >
                        <Copy className="h-3.5 w-3.5" />
                      </Button>
                    </div>
                  </div>

                  {/* Info */}
                  <div className="p-4">
                    <div className="mb-2 flex items-start justify-between">
                      <div className="min-w-0 flex-1">
                        <h3 className="truncate font-semibold text-gray-900">{scenario.name}</h3>
                        <p className="line-clamp-1 text-sm text-gray-500">
                          {scenario.description || "Açıklama yok"}
                        </p>
                      </div>
                    </div>

                    {/* Stats row */}
                    <div className="mb-3 flex flex-wrap items-center gap-3 text-xs text-gray-400">
                      {scenario.gallery_images?.length > 0 && (
                        <span className="flex items-center gap-1">
                          <ImageIcon className="h-3 w-3" />
                          {scenario.gallery_images.length} görsel
                        </span>
                      )}
                      {scenario.marketing_video_url && (
                        <span className="flex items-center gap-1 text-purple-500">
                          <FileText className="h-3 w-3" />
                          Video
                        </span>
                      )}
                      {scenario.age_range && (
                        <span className="flex items-center gap-1 text-blue-500">
                          {scenario.age_range}
                        </span>
                      )}
                      {scenario.rating != null && (
                        <span className="flex items-center gap-1 text-yellow-500">
                          ★ {scenario.rating}
                        </span>
                      )}
                      {scenario.linked_product_name && (
                        <span className="flex items-center gap-1 rounded-full bg-indigo-100 px-2 py-0.5 text-indigo-700">
                          <Settings className="h-3 w-3" />
                          {scenario.linked_product_name}
                        </span>
                      )}
                      {scenario.total_page_count != null && (
                        <span className="flex items-center gap-1 rounded-full bg-amber-100 px-2 py-0.5 text-amber-700">
                          <BookOpen className="h-3 w-3" />
                          {scenario.total_page_count} sayfa
                        </span>
                      )}
                      <span className="flex items-center gap-1">
                        <GripVertical className="h-3 w-3" />#{scenario.display_order}
                      </span>
                    </div>

                    {/* Actions */}
                    <div className="flex items-center gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        className="flex-1 text-xs"
                        onClick={() => openEditor(scenario)}
                      >
                        <Pencil className="mr-1 h-3 w-3" />
                        Düzenle
                      </Button>
                      <Button
                        size="sm"
                        variant={scenario.is_active ? "outline" : "default"}
                        className="text-xs"
                        onClick={() => toggleActive(scenario)}
                      >
                        {scenario.is_active ? (
                          <EyeOff className="h-3 w-3" />
                        ) : (
                          <Eye className="h-3 w-3" />
                        )}
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        className="text-red-500 hover:bg-red-50 hover:text-red-700"
                        onClick={() => setDeleteConfirm(scenario.id)}
                      >
                        <Trash2 className="h-3 w-3" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
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
                <h3 className="mb-2 text-lg font-semibold">Senaryoyu Sil</h3>
                <p className="mb-6 text-sm text-gray-500">
                  Bu senaryo pasif duruma alınacak. Emin misiniz?
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
        <SheetContent className="w-full overflow-y-auto sm:max-w-3xl">
          <SheetHeader className="mb-6">
            <SheetTitle className="flex items-center gap-2">
              <Settings2 className="h-5 w-5 text-purple-600" />
              {editingScenario ? "Senaryoyu Düzenle" : "Yeni Senaryo Oluştur"}
            </SheetTitle>
            <SheetDescription>
              Hikaye teması, medya içerikleri ve pazarlama ayarlarını yapılandırın
            </SheetDescription>
          </SheetHeader>

          {/* Tab Navigation */}
          <div className="mb-6 flex gap-1 rounded-xl border bg-gray-50 p-1">
            <button
              type="button"
              onClick={() => setActiveTab("content")}
              className={`flex-1 rounded-lg px-4 py-2 text-sm font-medium transition-all ${
                activeTab === "content"
                  ? "bg-white text-purple-700 shadow-sm"
                  : "text-gray-500 hover:text-gray-700"
              }`}
            >
              <FileText className="mr-1.5 inline h-4 w-4" />
              İçerik & Hikaye
            </button>
            <button
              type="button"
              onClick={() => setActiveTab("marketing")}
              className={`flex-1 rounded-lg px-4 py-2 text-sm font-medium transition-all ${
                activeTab === "marketing"
                  ? "bg-white text-orange-600 shadow-sm"
                  : "text-gray-500 hover:text-gray-700"
              }`}
            >
              <TrendingUp className="mr-1.5 inline h-4 w-4" />
              Pazarlama
            </button>
            <button
              type="button"
              onClick={() => setActiveTab("overrides")}
              className={`flex-1 rounded-lg px-4 py-2 text-sm font-medium transition-all ${
                activeTab === "overrides"
                  ? "bg-white text-blue-600 shadow-sm"
                  : "text-gray-500 hover:text-gray-700"
              }`}
            >
              <Settings className="mr-1.5 inline h-4 w-4" />
              Ürün Bağlantısı
            </button>
          </div>

          <div className="grid gap-6 lg:grid-cols-5">
            {/* Form */}
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6 lg:col-span-3">
              {/* ===== CONTENT TAB ===== */}
              {activeTab === "content" && <>

              {/* Basic Info */}
              <div className="space-y-4">
                <div className="flex items-center gap-2 text-sm font-medium text-gray-700">
                  <FileText className="h-4 w-4 text-purple-600" />
                  Temel Bilgiler
                </div>

                <div>
                  <Label>Senaryo Adı *</Label>
                  <Input
                    {...form.register("name")}
                    placeholder="Örn: Kapadokya Macerası"
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
                    placeholder="Senaryo hakkında kısa açıklama"
                    rows={2}
                    className="mt-1"
                  />
                </div>

                {/* Thumbnail */}
                <div>
                  <Label>Kapak Görseli</Label>
                  <div className="mt-1 flex items-start gap-4">
                    <div
                      onClick={() => thumbnailInputRef.current?.click()}
                      className="flex h-24 w-32 cursor-pointer items-center justify-center overflow-hidden rounded-lg border-2 border-dashed border-gray-300 bg-gray-100 transition-colors hover:border-purple-400"
                    >
                      {thumbnailPreview ? (
                        <img
                          src={thumbnailPreview}
                          alt="Thumbnail"
                          className="h-full w-full object-cover"
                        />
                      ) : (
                        <Upload className="h-6 w-6 text-gray-400" />
                      )}
                    </div>
                    <input
                      ref={thumbnailInputRef}
                      type="file"
                      accept="image/*"
                      onChange={handleThumbnailChange}
                      className="hidden"
                    />
                    <div className="text-xs text-gray-500">
                      <p>PNG, JPG (max 5MB)</p>
                      <p>Önerilen: 800×600px</p>
                    </div>
                  </div>
                </div>
              </div>

              <Separator />

              {/* Media */}
              <div className="space-y-4">
                <div className="flex items-center gap-2 text-sm font-medium text-gray-700">
                  <ImageIcon className="h-4 w-4 text-purple-600" />
                  Galeri Görselleri
                </div>
                <GalleryImageUploader images={galleryImages} onImagesChange={setGalleryImages} />
              </div>

              <Separator />

              {/* Dynamic Variables / Custom Inputs */}
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-sm font-medium text-gray-700">
                    <Variable className="h-4 w-4 text-purple-600" />
                    Dinamik Değişkenler
                  </div>
                  {customInputs.length > 0 && (
                    <Badge variant="secondary" className="text-xs">
                      {customInputs.length} değişken
                    </Badge>
                  )}
                </div>

                <p className="text-xs text-gray-500">
                  Kullanıcıların hikaye oluştururken dolduracağı özel alanlar tanımlayın. Bu
                  değişkenleri prompt şablonlarında kullanabilirsiniz.
                </p>

                <VariableManager variables={customInputs} onVariablesChange={setCustomInputs} />
              </div>

              <Separator />

              {/* V2: Story Prompt & Settings */}
              <div className="space-y-4">
                <div className="flex items-center gap-2 text-sm font-medium text-gray-700">
                  <Wand2 className="h-4 w-4 text-purple-600" />
                  Hikaye Promptu (V2)
                </div>

                <div className="space-y-4 rounded-lg border border-purple-100 bg-gradient-to-r from-purple-50 to-pink-50 p-4">
                  <div>
                    <Label>Hikaye Yazım Promptu (TR)</Label>
                    <p className="mb-1 mt-0.5 text-xs text-gray-500">
                      Gemini&apos;ye gönderilecek hikaye talimatları. Sadece hikaye dünyası ve kurgu
                      ile ilgili olmalı, görsel stil içermemeli.
                    </p>
                    <Textarea
                      {...form.register("story_prompt_tr")}
                      placeholder="Örn: Bu hikayede çocuk Kapadokya'daki peri bacalarında maceraya çıkar. Her sayfada farklı bir vadide keşif yapar..."
                      rows={5}
                      className="bg-white font-mono text-sm"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label>Lokasyon (EN)</Label>
                      <p className="mb-1 mt-0.5 text-xs text-gray-500">
                        Görsel promptlarda kullanılacak İngilizce lokasyon
                      </p>
                      <Input
                        {...form.register("location_en")}
                        placeholder="Cappadocia"
                        className="mt-1"
                      />
                    </div>
                    <div>
                      <Label>AI Üretim Sayfa Sayısı</Label>
                      <p className="mb-1 mt-0.5 text-xs text-gray-500">
                        Hikaye üretiminde kaç sayfa oluşturulacak (2-30). Bağlı üründen otomatik gelir, buradan override edilebilir.
                      </p>
                      <Controller
                        control={form.control}
                        name="default_page_count"
                        render={({ field }) => (
                          <Input
                            type="number"
                            min={2}
                            max={30}
                            {...field}
                            value={field.value ?? 6}
                            onChange={(e) => field.onChange(Number(e.target.value))}
                            className="mt-1"
                          />
                        )}
                      />
                    </div>
                  </div>

                  {/* Flags */}
                  <div className="flex items-center justify-between rounded-lg border bg-white p-3">
                    <div>
                      <Label>Ailesiz Senaryo</Label>
                      <p className="mt-0.5 text-xs text-gray-500">
                        Aktifse hikayede anne, baba, kardeş gibi aile bireyleri yer almaz
                      </p>
                    </div>
                    <Controller
                      control={form.control}
                      name="no_family"
                      render={({ field }) => (
                        <Switch checked={field.value} onCheckedChange={field.onChange} />
                      )}
                    />
                  </div>

                  <div className="flex items-start gap-2 rounded bg-white/50 p-2 text-xs text-purple-600">
                    <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
                    <span>
                      Kapak ve iç sayfa görsel şablonları artık /admin/prompts sayfasından yönetilir
                      (COVER_TEMPLATE, INNER_TEMPLATE).
                    </span>
                  </div>
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

              </> /* end content tab */}

              {/* ===== MARKETING TAB ===== */}
              {activeTab === "marketing" && (
                <div className="space-y-6">
                  {/* Tagline & Badge */}
                  <div className="space-y-4">
                    <div className="flex items-center gap-2 text-sm font-medium text-gray-700">
                      <TrendingUp className="h-4 w-4 text-orange-500" />
                      Kart Bilgileri
                    </div>

                    <div>
                      <Label>Kısa Slogan (Tagline)</Label>
                      <Input
                        value={tagline}
                        onChange={(e) => setTagline(e.target.value)}
                        placeholder="Örn: Sihirli balonlarla gökyüzünde bir macera"
                        className="mt-1"
                      />
                      <p className="mt-1 text-xs text-gray-400">Senaryo kartında başlığın altında görünür</p>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label>Rozet Metni</Label>
                        <Input
                          value={marketingBadge}
                          onChange={(e) => setMarketingBadge(e.target.value)}
                          placeholder="Örn: Yeni! veya En Çok Tercih"
                          className="mt-1"
                        />
                      </div>
                      <div>
                        <Label>Fiyat Etiketi</Label>
                        <Input
                          value={marketingPriceLabel}
                          onChange={(e) => setMarketingPriceLabel(e.target.value)}
                          placeholder="Örn: 299 TL'den başlayan"
                          className="mt-1"
                        />
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label>Hedef Yaş Aralığı</Label>
                        <Input
                          value={ageRange}
                          onChange={(e) => setAgeRange(e.target.value)}
                          placeholder="Örn: 3-8 yaş"
                          className="mt-1"
                        />
                      </div>
                      <div>
                        <Label>Tahmini Süre</Label>
                        <Input
                          value={estimatedDuration}
                          onChange={(e) => setEstimatedDuration(e.target.value)}
                          placeholder="Örn: 15 dakika"
                          className="mt-1"
                        />
                      </div>
                    </div>
                  </div>

                  <Separator />

                  {/* Social Proof */}
                  <div className="space-y-4">
                    <div className="flex items-center gap-2 text-sm font-medium text-gray-700">
                      <Star className="h-4 w-4 text-yellow-500" />
                      Sosyal Kanıt
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label>Puan (0-5)</Label>
                        <Input
                          type="number"
                          min="0"
                          max="5"
                          step="0.1"
                          value={rating}
                          onChange={(e) => setRating(e.target.value)}
                          placeholder="Örn: 4.9"
                          className="mt-1"
                        />
                      </div>
                      <div>
                        <Label>Değerlendirme Sayısı</Label>
                        <Input
                          type="number"
                          min="0"
                          value={reviewCount}
                          onChange={(e) => setReviewCount(e.target.value)}
                          placeholder="Örn: 1247"
                          className="mt-1"
                        />
                      </div>
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
                        value={marketingVideoUrl}
                        onChange={(e) => setMarketingVideoUrl(e.target.value)}
                        placeholder="https://www.youtube.com/embed/..."
                        className="mt-1"
                      />
                      <p className="mt-1 text-xs text-gray-400">
                        YouTube embed URL veya doğrudan video linki. Senaryo detay panelinde oynatılır.
                      </p>
                    </div>

                    {marketingVideoUrl && (
                      <div className="aspect-video overflow-hidden rounded-xl border">
                        <iframe
                          src={marketingVideoUrl}
                          className="h-full w-full"
                          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                          allowFullScreen
                        />
                      </div>
                    )}
                  </div>

                  <Separator />

                  {/* Features */}
                  <div className="space-y-4">
                    <div className="flex items-center gap-2 text-sm font-medium text-gray-700">
                      <CheckCircle2 className="h-4 w-4 text-green-500" />
                      Özellik Listesi
                    </div>
                    <p className="text-xs text-gray-500">
                      Senaryo detay panelinde &quot;Kitabın İçinde&quot; bölümünde gösterilir.
                    </p>

                    {marketingFeatures.length > 0 && (
                      <div className="space-y-2">
                        {marketingFeatures.map((feature, idx) => (
                          <div
                            key={idx}
                            className="flex items-center gap-2 rounded-lg border bg-green-50 px-3 py-2"
                          >
                            <CheckCircle2 className="h-4 w-4 shrink-0 text-green-500" />
                            <span className="flex-1 text-sm text-gray-700">{feature}</span>
                            <button
                              type="button"
                              onClick={() =>
                                setMarketingFeatures(marketingFeatures.filter((_, i) => i !== idx))
                              }
                              className="text-red-400 hover:text-red-600"
                            >
                              <X className="h-4 w-4" />
                            </button>
                          </div>
                        ))}
                      </div>
                    )}

                    <div className="flex gap-2">
                      <Input
                        value={newFeatureInput}
                        onChange={(e) => setNewFeatureInput(e.target.value)}
                        placeholder="Örn: Çocuğunuzun adı 12 kez geçiyor"
                        onKeyDown={(e) => {
                          if (e.key === "Enter") {
                            e.preventDefault();
                            if (newFeatureInput.trim()) {
                              setMarketingFeatures([...marketingFeatures, newFeatureInput.trim()]);
                              setNewFeatureInput("");
                            }
                          }
                        }}
                      />
                      <Button
                        type="button"
                        variant="outline"
                        onClick={() => {
                          if (newFeatureInput.trim()) {
                            setMarketingFeatures([...marketingFeatures, newFeatureInput.trim()]);
                            setNewFeatureInput("");
                          }
                        }}
                      >
                        <Plus className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>

                  <Separator />

                  {/* Marketing Gallery */}
                  <div className="space-y-4">
                    <div className="flex items-center gap-2 text-sm font-medium text-gray-700">
                      <ImageIcon className="h-4 w-4 text-purple-500" />
                      Pazarlama Galerisi
                    </div>
                    <p className="text-xs text-gray-500">
                      Senaryo detay panelinde &quot;Kitaptan Kareler&quot; bölümünde gösterilir. İçerik galerisinden ayrıdır.
                    </p>
                    <GalleryImageUploader
                      images={marketingGallery}
                      onImagesChange={setMarketingGallery}
                    />
                  </div>

                  <Separator />

                  {/* Book Structure */}
                  <div className="space-y-4">
                    <div className="flex items-center gap-2 text-sm font-semibold text-gray-700">
                      <BookOpen className="h-4 w-4 text-amber-600" />
                      Kitap Yapısı
                    </div>
                    <p className="text-xs text-gray-500">
                      Müşteriye gösterilecek kitap sayfa dökümü. Toplam sayfa otomatik hesaplanır.
                      <br />
                      Örnek: 22 hikaye + 2 kapak + 2 karşılama + 1 arka bilgi = <strong>27 sayfa</strong>
                    </p>

                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label>Hikaye Sayfası Sayısı</Label>
                        <p className="mb-1 mt-0.5 text-xs text-gray-400">AI üretilen sayfa sayısı (ör. 22)</p>
                        <Input
                          type="number"
                          min="1"
                          max="100"
                          value={storyPageCount}
                          onChange={(e) => setStoryPageCount(e.target.value)}
                          placeholder="22"
                          className="mt-1"
                        />
                      </div>
                      <div>
                        <Label>Kapak Sayısı</Label>
                        <p className="mb-1 mt-0.5 text-xs text-gray-400">Ön + arka kapak (varsayılan 2)</p>
                        <Input
                          type="number"
                          min="1"
                          max="4"
                          value={coverCount}
                          onChange={(e) => setCoverCount(e.target.value)}
                          placeholder="2"
                          className="mt-1"
                        />
                      </div>
                      <div>
                        <Label>Karşılama Sayfası Sayısı</Label>
                        <p className="mb-1 mt-0.5 text-xs text-gray-400">İthaf + senaryo giriş (varsayılan 2)</p>
                        <Input
                          type="number"
                          min="0"
                          max="10"
                          value={greetingPageCount}
                          onChange={(e) => setGreetingPageCount(e.target.value)}
                          placeholder="2"
                          className="mt-1"
                        />
                      </div>
                      <div>
                        <Label>Arka Bilgi Sayfası</Label>
                        <p className="mb-1 mt-0.5 text-xs text-gray-400">Eğitici arka sayfa (varsayılan 1)</p>
                        <Input
                          type="number"
                          min="0"
                          max="5"
                          value={backInfoPageCount}
                          onChange={(e) => setBackInfoPageCount(e.target.value)}
                          placeholder="1"
                          className="mt-1"
                        />
                      </div>
                    </div>

                    {/* Toplam sayfa hesaplama */}
                    {storyPageCount && (
                      <div className="rounded-lg border border-amber-200 bg-amber-50 p-3">
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-gray-600">Toplam Sayfa:</span>
                          <span className="text-lg font-bold text-amber-700">
                            {(parseInt(storyPageCount || "0", 10) || 0) +
                              (parseInt(coverCount || "2", 10) || 2) +
                              (parseInt(greetingPageCount || "2", 10) || 2) +
                              (parseInt(backInfoPageCount || "1", 10) || 1)} sayfa
                          </span>
                        </div>
                        <div className="mt-1 text-xs text-gray-500">
                          {storyPageCount} hikaye + {coverCount || 2} kapak + {greetingPageCount || 2} karşılama + {backInfoPageCount || 1} arka bilgi
                        </div>
                      </div>
                    )}
                  </div>

                  {/* ── Kıyafet Tasarımı ── */}
                  <div className="rounded-lg border border-purple-100 bg-purple-50 p-4 space-y-4">
                    <div className="flex items-center gap-2 text-sm font-semibold text-purple-800">
                      <span>👗</span>
                      Karakter Kıyafeti (Görsel Üretim)
                    </div>
                    <p className="text-xs text-purple-600">
                      Her sayfada çocuğun aynı kıyafeti giymesi için senaryo bazlı kıyafet tanımı.
                      İngilizce yazın — AI görsel üretiminde doğrudan kullanılır.
                    </p>
                    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                      <div>
                        <Label className="text-purple-700">Kız Kıyafeti</Label>
                        <textarea
                          value={outfitGirl}
                          onChange={(e) => setOutfitGirl(e.target.value)}
                          placeholder="örn: dusty rose linen explorer dress, wide-brim straw hat, brown leather ankle boots"
                          rows={3}
                          className="mt-1 w-full rounded-md border border-purple-200 bg-white px-3 py-2 text-sm text-gray-800 placeholder-gray-400 focus:border-purple-400 focus:outline-none focus:ring-1 focus:ring-purple-400"
                        />
                      </div>
                      <div>
                        <Label className="text-purple-700">Erkek Kıyafeti</Label>
                        <textarea
                          value={outfitBoy}
                          onChange={(e) => setOutfitBoy(e.target.value)}
                          placeholder="örn: khaki explorer shirt, rolled-up canvas pants, brown leather boots, small backpack"
                          rows={3}
                          className="mt-1 w-full rounded-md border border-purple-200 bg-white px-3 py-2 text-sm text-gray-800 placeholder-gray-400 focus:border-purple-400 focus:outline-none focus:ring-1 focus:ring-purple-400"
                        />
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* ===== OVERRIDES TAB ===== */}
              {activeTab === "overrides" && (
                <div className="space-y-6">
                  {/* ── Linked Product Selector ── */}
                  <div className="rounded-lg border border-indigo-100 bg-indigo-50 p-4 space-y-3">
                    <div className="flex items-center gap-2 text-sm font-semibold text-indigo-800">
                      <Settings className="h-4 w-4" />
                      Bağlı Ürün (Temel Ayarlar)
                    </div>
                    <p className="text-xs text-indigo-600">
                      Bir ürün seçince o ürünün tüm üretim ayarları (kağıt, kapak, şablon, fiyat, sayfa sayısı)
                      bu senaryoya otomatik uygulanır. İstediğiniz alanları aşağıdan override edebilirsiniz.
                    </p>
                    <div>
                      <Label className="text-indigo-700">Ürün Seç</Label>
                      <select
                        value={linkedProductId}
                        onChange={(e) => {
                          const pid = e.target.value;
                          setLinkedProductId(pid);
                          if (pid) {
                            const p = products.find((x) => x.id === pid);
                            if (p) {
                              // Auto-fill override fields from product (user can then customize)
                              setPriceOverrideBase("");
                              setPriceOverrideExtraPage("");
                              setCoverTemplateIdOverride(p.cover_template_id || "");
                              setInnerTemplateIdOverride(p.inner_template_id || "");
                              setBackTemplateIdOverride(p.back_template_id || "");
                              setAiConfigIdOverride(p.ai_config_id || "");
                              setPaperTypeOverride("");
                              setPaperFinishOverride("");
                              setCoverTypeOverride("");
                              setLaminationOverride("");
                              setOrientationOverride("");
                              setMinPageCountOverride("");
                              setMaxPageCountOverride("");
                            }
                          }
                        }}
                        className="mt-1 w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                      >
                        <option value="">— Ürün seçilmedi (override alanları kullanılır) —</option>
                        {products.map((p) => (
                          <option key={p.id} value={p.id}>
                            {p.name} — {p.base_price}₺ / {p.default_page_count} sayfa / {p.paper_type}
                          </option>
                        ))}
                      </select>
                    </div>

                    {/* Show selected product summary */}
                    {linkedProductId && (() => {
                      const p = products.find((x) => x.id === linkedProductId);
                      if (!p) return null;
                      return (
                        <div className="mt-2 rounded-md border border-indigo-200 bg-white p-3 text-xs text-gray-700 grid grid-cols-2 gap-1">
                          <span className="font-medium text-gray-500">Taban Fiyat:</span><span>{p.base_price}₺</span>
                          <span className="font-medium text-gray-500">Ekstra Sayfa:</span><span>{p.extra_page_price}₺</span>
                          <span className="font-medium text-gray-500">Sayfa Sayısı:</span><span>{p.default_page_count} ({p.min_page_count}–{p.max_page_count})</span>
                          <span className="font-medium text-gray-500">Kağıt:</span><span>{p.paper_type} / {p.paper_finish}</span>
                          <span className="font-medium text-gray-500">Kapak:</span><span>{p.cover_type}{p.lamination ? ` / ${p.lamination}` : ""}</span>
                          <span className="font-medium text-gray-500">Yön:</span><span>{p.orientation}</span>
                        </div>
                      );
                    })()}
                  </div>

                  <div className="rounded-lg border border-amber-100 bg-amber-50 p-3 text-xs text-amber-700">
                    Aşağıdaki alanlar boş bırakılırsa bağlı ürünün değerleri kullanılır.
                    Doldurulursa bu senaryo için o değer geçerli olur.
                  </div>

                  {/* Price Overrides */}
                  <div className="space-y-3">
                    <div className="flex items-center gap-2 text-sm font-medium text-gray-700">
                      <DollarSign className="h-4 w-4 text-green-600" />
                      Fiyat Override
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label>Taban Fiyat (₺)</Label>
                        <Input
                          type="number"
                          min="0"
                          step="0.01"
                          value={priceOverrideBase}
                          onChange={(e) => setPriceOverrideBase(e.target.value)}
                          placeholder={linkedProductId ? (products.find(p=>p.id===linkedProductId)?.base_price?.toString() ?? "Ürün fiyatı") : "Ürün fiyatını kullan"}
                          className="mt-1"
                        />
                      </div>
                      <div>
                        <Label>Ekstra Sayfa Fiyatı (₺)</Label>
                        <Input
                          type="number"
                          min="0"
                          step="0.01"
                          value={priceOverrideExtraPage}
                          onChange={(e) => setPriceOverrideExtraPage(e.target.value)}
                          placeholder={linkedProductId ? (products.find(p=>p.id===linkedProductId)?.extra_page_price?.toString() ?? "Ürün fiyatı") : "Ürün fiyatını kullan"}
                          className="mt-1"
                        />
                      </div>
                    </div>
                  </div>

                  <Separator />

                  {/* Page Count Overrides */}
                  <div className="space-y-3">
                    <div className="flex items-center gap-2 text-sm font-medium text-gray-700">
                      <Layout className="h-4 w-4 text-blue-600" />
                      Sayfa Sayısı Override
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label>Min Sayfa</Label>
                        <Input
                          type="number"
                          min="4"
                          value={minPageCountOverride}
                          onChange={(e) => setMinPageCountOverride(e.target.value)}
                          placeholder={linkedProductId ? (products.find(p=>p.id===linkedProductId)?.min_page_count?.toString() ?? "") : ""}
                          className="mt-1"
                        />
                      </div>
                      <div>
                        <Label>Max Sayfa</Label>
                        <Input
                          type="number"
                          min="4"
                          value={maxPageCountOverride}
                          onChange={(e) => setMaxPageCountOverride(e.target.value)}
                          placeholder={linkedProductId ? (products.find(p=>p.id===linkedProductId)?.max_page_count?.toString() ?? "") : ""}
                          className="mt-1"
                        />
                      </div>
                    </div>
                  </div>

                  <Separator />

                  {/* Physical Settings Overrides */}
                  <div className="space-y-3">
                    <div className="flex items-center gap-2 text-sm font-medium text-gray-700">
                      <Settings className="h-4 w-4 text-orange-600" />
                      Fiziksel Ayarlar Override
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label>Kağıt Türü</Label>
                        <Input
                          value={paperTypeOverride}
                          onChange={(e) => setPaperTypeOverride(e.target.value)}
                          placeholder={linkedProductId ? (products.find(p=>p.id===linkedProductId)?.paper_type ?? "Kuşe 170gr") : "Kuşe 170gr"}
                          className="mt-1"
                        />
                      </div>
                      <div>
                        <Label>Kağıt Yüzeyi</Label>
                        <Input
                          value={paperFinishOverride}
                          onChange={(e) => setPaperFinishOverride(e.target.value)}
                          placeholder={linkedProductId ? (products.find(p=>p.id===linkedProductId)?.paper_finish ?? "Mat") : "Mat"}
                          className="mt-1"
                        />
                      </div>
                      <div>
                        <Label>Kapak Türü</Label>
                        <Input
                          value={coverTypeOverride}
                          onChange={(e) => setCoverTypeOverride(e.target.value)}
                          placeholder={linkedProductId ? (products.find(p=>p.id===linkedProductId)?.cover_type ?? "Sert Kapak") : "Sert Kapak"}
                          className="mt-1"
                        />
                      </div>
                      <div>
                        <Label>Laminasyon</Label>
                        <Input
                          value={laminationOverride}
                          onChange={(e) => setLaminationOverride(e.target.value)}
                          placeholder={linkedProductId ? (products.find(p=>p.id===linkedProductId)?.lamination ?? "—") : "—"}
                          className="mt-1"
                        />
                      </div>
                      <div>
                        <Label>Yön (orientation)</Label>
                        <select
                          value={orientationOverride}
                          onChange={(e) => setOrientationOverride(e.target.value)}
                          className="mt-1 w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none"
                        >
                          <option value="">— Ürün değerini kullan —</option>
                          <option value="landscape">Yatay (landscape)</option>
                          <option value="portrait">Dikey (portrait)</option>
                        </select>
                      </div>
                    </div>
                  </div>

                  <Separator />

                  {/* Template Overrides */}
                  <div className="space-y-3">
                    <div className="flex items-center gap-2 text-sm font-medium text-gray-700">
                      <Layout className="h-4 w-4 text-purple-600" />
                      Şablon Override (Template UUID)
                    </div>
                    <p className="text-xs text-gray-500">
                      Boş bırakırsanız bağlı ürünün şablonu kullanılır.
                    </p>
                    <div className="space-y-3">
                      <div>
                        <Label>Kapak Şablonu ID</Label>
                        <Input
                          value={coverTemplateIdOverride}
                          onChange={(e) => setCoverTemplateIdOverride(e.target.value)}
                          placeholder={linkedProductId ? (products.find(p=>p.id===linkedProductId)?.cover_template_id ?? "UUID") : "UUID"}
                          className="mt-1 font-mono text-xs"
                        />
                      </div>
                      <div>
                        <Label>İç Sayfa Şablonu ID</Label>
                        <Input
                          value={innerTemplateIdOverride}
                          onChange={(e) => setInnerTemplateIdOverride(e.target.value)}
                          placeholder={linkedProductId ? (products.find(p=>p.id===linkedProductId)?.inner_template_id ?? "UUID") : "UUID"}
                          className="mt-1 font-mono text-xs"
                        />
                      </div>
                      <div>
                        <Label>Arka Kapak Şablonu ID</Label>
                        <Input
                          value={backTemplateIdOverride}
                          onChange={(e) => setBackTemplateIdOverride(e.target.value)}
                          placeholder={linkedProductId ? (products.find(p=>p.id===linkedProductId)?.back_template_id ?? "UUID") : "UUID"}
                          className="mt-1 font-mono text-xs"
                        />
                      </div>
                      <div>
                        <Label>AI Config ID</Label>
                        <Input
                          value={aiConfigIdOverride}
                          onChange={(e) => setAiConfigIdOverride(e.target.value)}
                          placeholder={linkedProductId ? (products.find(p=>p.id===linkedProductId)?.ai_config_id ?? "UUID") : "UUID"}
                          className="mt-1 font-mono text-xs"
                        />
                      </div>
                    </div>
                  </div>
                </div>
              )}

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
                      {editingScenario ? "Güncelle" : "Oluştur"}
                    </>
                  )}
                </Button>
              </div>
            </form>

            {/* Preview */}
            <div className="space-y-4 lg:col-span-2">
              <div className="sticky top-4">
                <div className="mb-3 flex items-center gap-2 text-sm font-medium text-gray-700">
                  <Eye className="h-4 w-4 text-purple-600" />
                  Canlı Önizleme
                </div>
                <ScenarioPreview scenario={previewData} />

                {/* V2 Stats */}
                <div className="mt-4 rounded-lg border bg-gray-50 p-3">
                  <p className="mb-2 text-xs font-medium text-gray-700">V2 Ayarları</p>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-gray-500">Lokasyon:</span>
                      <span className="font-mono text-purple-600">
                        {watchedValues.location_en || "—"}
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-gray-500">Sayfa:</span>
                      <span className="font-mono text-blue-600">
                        {watchedValues.default_page_count ?? 6}
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-gray-500">Ailesiz:</span>
                      <span
                        className={`font-mono ${watchedValues.no_family ? "text-red-600" : "text-green-600"}`}
                      >
                        {watchedValues.no_family ? "Evet" : "Hayır"}
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-gray-500">Prompt:</span>
                      <span className="font-mono text-purple-600">
                        {watchedValues.story_prompt_tr?.length || 0} karakter
                      </span>
                    </div>
                  </div>
                </div>

                {/* Gallery preview */}
                {galleryImages.length > 0 && (
                  <div className="mt-4">
                    <p className="mb-2 text-xs text-gray-500">
                      Galeri: {galleryImages.length} görsel
                    </p>
                    <div className="grid grid-cols-4 gap-1">
                      {galleryImages.slice(0, 4).map((img, idx) => (
                        <div key={idx} className="aspect-square overflow-hidden rounded">
                          <img src={img} alt="" className="h-full w-full object-cover" />
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </SheetContent>
      </Sheet>
    </div>
  );
}
