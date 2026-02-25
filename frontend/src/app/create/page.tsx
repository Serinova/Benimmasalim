"use client";

import { useState, useEffect, useCallback, useRef, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import {
  BookOpen,
  Palette,
  Eye,
  CreditCard,
  PartyPopper,
  ChevronLeft,
  Sparkles,
  ShieldCheck,
  Truck,
  Heart,
  Mail,
  Info,
} from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useToast } from "@/hooks/use-toast";

// Existing sub-components (unchanged)
import UserContactForm, { type ContactInfo } from "@/components/UserContactForm";
import AdventureSelector from "@/components/AdventureSelector";
import ProductFormatSelector from "@/components/ProductFormatSelector";
import LearningOutcomeSelector from "@/components/LearningOutcomeSelector";
import ChildInfoForm from "@/components/ChildInfoForm";
import CustomInputsForm from "@/components/CustomInputsForm";
import PhotoUploaderStep from "@/components/PhotoUploaderStep";
import StyleSelectorStep from "@/components/StyleSelectorStep";
import StoryReviewStep from "@/components/StoryReviewStep";
import AudioSelectionStep from "@/components/AudioSelectionStep";
import CheckoutStep from "@/components/CheckoutStep";
import ImagePreviewStep from "@/components/ImagePreviewStep";

// New components
import StepIndicator from "@/components/create/StepIndicator";
import OrderSummaryPanel from "@/components/create/OrderSummaryPanel";

import {
  API_BASE_URL,
  APIError,
  buildStoryPayload,
  generateStoryV2,
  uploadTempImage,
  completeTrial,
  generatePreviewImages,
  getTrialStatus,
  getTrialPreview,
  createTrialPayment,
  verifyTrialPayment,
} from "@/lib/api";
import type {
  Scenario,
  VisualStyle,
  StoryPage,
  LearningOutcomeCategory,
  CustomInputField,
  GenerationProgress,
} from "@/lib/api";
import {
  checkPromptCompliance,
  normalizeClothingDescription,
  validateClothingDescription,
} from "@/lib/compliance";

// ─── Local interfaces ───────────────────────────────────────────

interface Product {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  short_description: string | null;
  cover_width_mm: number | null;
  cover_height_mm: number | null;
  inner_width_mm: number | null;
  inner_height_mm: number | null;
  default_page_count: number;
  base_price: number;
  extra_page_price: number;
  paper_type: string;
  cover_type: string;
  thumbnail_url: string | null;
  is_featured: boolean;
}

interface StoryStructure {
  title: string;
  pages: StoryPage[];
}

// ─── Step definitions ───────────────────────────────────────────

const STEP_DEFS = [
  { label: "Hikayeni Oluştur", shortLabel: "Hikaye", icon: <BookOpen className="h-4 w-4" /> },
  { label: "Stil & Fotoğraf", shortLabel: "Stil", icon: <Palette className="h-4 w-4" /> },
  { label: "İncele & Onayla", shortLabel: "İncele", icon: <Eye className="h-4 w-4" /> },
  { label: "Teslimat & Ödeme", shortLabel: "Ödeme", icon: <CreditCard className="h-4 w-4" /> },
  { label: "Tamamlandı", shortLabel: "Tamam", icon: <PartyPopper className="h-4 w-4" /> },
];

// Sub-steps within each main step
type SubStep =
  // Step 1: Story creation
  | "child-info"
  | "adventure"
  | "learning-outcomes"
  // Step 2: Style & Photo
  | "product"
  | "photo"
  | "style"
  // Step 3: Review
  | "story-review"
  | "contact"
  | "image-preview"
  | "audio"
  // Step 4: Checkout
  | "checkout"
  // Step 5: Success
  | "success";

// ─── Product auto-skip helper ───────────────────────────────────

function ProductAutoSkipOrSelect({
  products,
  selectedProduct,
  onSelect,
  onSkipped,
  onContinue,
  onBack,
}: {
  products: Product[];
  selectedProduct: string;
  onSelect: (id: string) => void;
  onSkipped: () => void;
  onContinue: () => void;
  onBack: () => void;
}) {
  useEffect(() => {
    if (products.length <= 1) {
      if (products.length === 1 && !selectedProduct) {
        onSelect(products[0].id);
      }
      onSkipped();
    }
  }, [products, selectedProduct, onSelect, onSkipped]);

  if (products.length <= 1) return null;

  return (
    <div className="mx-auto max-w-5xl">
      <ProductFormatSelector
        products={products}
        selectedProduct={selectedProduct}
        onSelect={onSelect}
        onContinue={onContinue}
      />
      <div className="mt-4">
        <Button variant="outline" onClick={onBack}>
          <ChevronLeft className="mr-1 h-4 w-4" />
          Geri
        </Button>
      </div>
    </div>
  );
}

// ─── Main Component ─────────────────────────────────────────────

function CreatePageInner() {
  const searchParams = useSearchParams();
  // If ?scenario=ID is in URL, start at child-info (scenario pre-selected)
  // Otherwise start at adventure (scenario selection)
  const preselectedScenarioId = searchParams.get("scenario") ?? "";

  // ─── Navigation state ─────────────────────────────────────────
  const [mainStep, setMainStep] = useState(1);
  const [maxMainStep, setMaxMainStep] = useState(1);
  const [subStep, setSubStep] = useState<SubStep>(
    preselectedScenarioId ? "child-info" : "adventure"
  );

  // ─── Data lists (fetched once) ────────────────────────────────
  const [products, setProducts] = useState<Product[]>([]);
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [scenariosLoadError, setScenariosLoadError] = useState<string | null>(null);
  const [learningOutcomes, setLearningOutcomes] = useState<LearningOutcomeCategory[]>([]);
  const [visualStyles, setVisualStyles] = useState<VisualStyle[]>([]);

  // ─── Selections ───────────────────────────────────────────────
  const [selectedProduct, setSelectedProduct] = useState<string>("");
  const [selectedScenario, setSelectedScenario] = useState<string>(preselectedScenarioId);
  const [selectedOutcomes, setSelectedOutcomes] = useState<string[]>([]);
  const [selectedStyle, setSelectedStyle] = useState<string>("");
  const [customIdWeight, setCustomIdWeight] = useState<number | null>(null);
  const [, setExpandedCategories] = useState<string[]>([]);

  // ─── Child info ───────────────────────────────────────────────
  const [childInfo, setChildInfo] = useState({
    name: "",
    age: "",
    gender: "erkek",
    clothingDescription: "",
  });
  const [customVariables, setCustomVariables] = useState<Record<string, string>>({});

  // ─── Photo ────────────────────────────────────────────────────
  const [childPhoto, setChildPhoto] = useState<File | null>(null);
  const [childPhotoPreview, setChildPhotoPreview] = useState<string>("");
  const [uploadingPhoto, setUploadingPhoto] = useState(false);
  const [faceDetected, setFaceDetected] = useState(false);
  const [additionalPhotos, setAdditionalPhotos] = useState<string[]>([]);
  const [, setAdditionalPhotoFiles] = useState<File[]>([]);

  // ─── Story ────────────────────────────────────────────────────
  const [loading, setLoading] = useState(false);
  const [storyStructure, setStoryStructure] = useState<StoryStructure | null>(null);
  const [storyMetadata, setStoryMetadata] = useState<{ clothing_description?: string } | null>(null);

  // ─── Preview ──────────────────────────────────────────────────
  const [_trialId, _setTrialIdRaw] = useState<string | null>(() => {
    if (typeof window !== "undefined") {
      return sessionStorage.getItem("current_trial_id");
    }
    return null;
  });
  const setTrialId = (id: string | null) => {
    _setTrialIdRaw(id);
    if (typeof window !== "undefined") {
      if (id) sessionStorage.setItem("current_trial_id", id);
      else sessionStorage.removeItem("current_trial_id");
    }
  };
  const [_trialToken, _setTrialTokenRaw] = useState<string | null>(() => {
    if (typeof window !== "undefined") {
      return sessionStorage.getItem("current_trial_token");
    }
    return null;
  });
  const setTrialToken = (token: string | null) => {
    _setTrialTokenRaw(token);
    if (typeof window !== "undefined") {
      if (token) sessionStorage.setItem("current_trial_token", token);
      else sessionStorage.removeItem("current_trial_token");
    }
  };
  const [previewImages, setPreviewImages] = useState<Record<string, string>>({});
  const [previewLoading, setPreviewLoading] = useState(false);
  const [generationProgress, setGenerationProgress] = useState<GenerationProgress | null>(null);

  // ─── Audio ────────────────────────────────────────────────────
  const [hasAudioBook, setHasAudioBook] = useState(false);
  const [audioType, setAudioType] = useState<"system" | "cloned">("system");
  const [systemVoice, setSystemVoice] = useState<"female" | "male">("female");
  const [voiceSampleUrl, setVoiceSampleUrl] = useState<string>("");
  const [clonedVoiceId, setClonedVoiceId] = useState<string>("");
  const [isCloningVoice, setIsCloningVoice] = useState(false);

  // ─── Checkout ─────────────────────────────────────────────────
  const [parentInfo, setParentInfo] = useState({ fullName: "", email: "", phone: "" });
  const [dedicationNote, setDedicationNote] = useState<string>("");
  const [submittingOrder, setSubmittingOrder] = useState(false);
  const [, setOrderComplete] = useState(false);

  // ─── Lead / Contact ────────────────────────────────────────────
  const [leadUserId, setLeadUserId] = useState<string | null>(null);
  const [contactInfo, setContactInfo] = useState<ContactInfo | null>(null);

  const { toast } = useToast();

  const _paymentCallbackHandled = useRef(false);

  // ─── Init ─────────────────────────────────────────────────────

  useEffect(() => {
    const initializeSession = async () => {
      const storedUserId = localStorage.getItem("lead_user_id");
      if (storedUserId) {
        await restoreLeadSession(storedUserId);
      }
    };

    initializeSession();
    fetchProducts();
    fetchScenarios();
    fetchLearningOutcomes();
    fetchVisualStyles();
  }, []);

  // ─── Handle Iyzico payment callback ──────────────────────────
  useEffect(() => {
    if (typeof window === "undefined") return;
    const sp = new URLSearchParams(window.location.search);
    const paymentStatus = sp.get("payment");
    const iyzico_token = sp.get("token");
    const callbackTrialId = sp.get("trialId");

    if (!paymentStatus || _paymentCallbackHandled.current) return;
    _paymentCallbackHandled.current = true;

    if (paymentStatus === "success" && callbackTrialId && iyzico_token) {
      const storedTrialToken = sessionStorage.getItem("pending_trial_token") || undefined;
      const storedName = sessionStorage.getItem("pending_parent_name") || "";
      const storedEmail = sessionStorage.getItem("pending_parent_email") || "";
      const storedPhone = sessionStorage.getItem("pending_parent_phone") || "";
      const storedDedication = sessionStorage.getItem("pending_dedication_note") || "";
      const storedHasAudio = sessionStorage.getItem("pending_has_audio") === "true";
      const storedAudioType = (sessionStorage.getItem("pending_audio_type") || "system") as "system" | "cloned";
      const storedVoiceId = sessionStorage.getItem("pending_audio_voice_id") || "";

      setSubmittingOrder(true);

      verifyTrialPayment(callbackTrialId, iyzico_token, storedTrialToken)
        .then(async (verifyResult) => {
          if (!verifyResult.success || !verifyResult.payment_reference) {
            throw new Error(verifyResult.error || "Ödeme doğrulanamadı");
          }
          const data = await completeTrial(
            {
              trial_id: callbackTrialId,
              payment_reference: verifyResult.payment_reference,
              parent_name: storedName,
              parent_email: storedEmail,
              parent_phone: storedPhone || undefined,
              dedication_note: storedDedication || null,
              has_audio_book: storedHasAudio,
              audio_type: storedHasAudio ? storedAudioType : null,
              audio_voice_id: storedHasAudio && storedAudioType === "cloned" ? storedVoiceId : null,
            },
            storedTrialToken,
          );
          if (data.success) {
            sessionStorage.removeItem("pending_trial_id");
            sessionStorage.removeItem("pending_trial_token");
            sessionStorage.removeItem("pending_parent_name");
            sessionStorage.removeItem("pending_parent_email");
            sessionStorage.removeItem("pending_parent_phone");
            sessionStorage.removeItem("pending_dedication_note");
            sessionStorage.removeItem("pending_has_audio");
            sessionStorage.removeItem("pending_audio_type");
            sessionStorage.removeItem("pending_audio_voice_id");
            setOrderComplete(true);
            goToMainStep(5, "success");
          } else {
            throw new Error("Sipariş tamamlanamadı");
          }
        })
        .catch((err) => {
          toast({
            title: "Ödeme Hatası",
            description: err instanceof Error ? err.message : "Ödeme tamamlanamadı. Destek ile iletişime geçin.",
            variant: "destructive",
          });
        })
        .finally(() => setSubmittingOrder(false));

    } else if (paymentStatus === "failed") {
      toast({
        title: "Ödeme Başarısız",
        description: "Ödeme tamamlanamadı. Lütfen tekrar deneyin.",
        variant: "destructive",
      });
      goToMainStep(4, "checkout");
    } else if (paymentStatus === "error") {
      toast({
        title: "Ödeme Hatası",
        description: "Ödeme işleminde bir hata oluştu. Lütfen tekrar deneyin.",
        variant: "destructive",
      });
      goToMainStep(4, "checkout");
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Restore saved lead session
  const restoreLeadSession = async (userId: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/leads/${userId}`, {
        headers: { "X-User-Id": userId },
      });
      if (response.ok) {
        const data = await response.json();
        setLeadUserId(data.user_id);
        setContactInfo({
          firstName: data.first_name,
          lastName: data.last_name,
          phone: data.phone,
          email: data.email,
          userId: data.user_id,
        });
      } else {
        localStorage.removeItem("lead_user_id");
      }
    } catch {
      localStorage.removeItem("lead_user_id");
    }
  };

  const handleLeadCapture = (userId: string, info: ContactInfo) => {
    setLeadUserId(userId);
    setContactInfo(info);
  };

  // Auto-select first product if only one exists
  useEffect(() => {
    if (products.length === 1 && !selectedProduct) {
      setSelectedProduct(products[0].id);
    }
  }, [products, selectedProduct]);

  // When scenarios load and a scenario was pre-selected via URL, apply its custom inputs defaults
  useEffect(() => {
    if (preselectedScenarioId && scenarios.length > 0) {
      const scenario = scenarios.find((s) => s.id === preselectedScenarioId);
      if (scenario?.custom_inputs_schema) {
        const defaults: Record<string, string> = {};
        scenario.custom_inputs_schema.forEach((field: CustomInputField) => {
          if (field.default) defaults[field.key] = field.default;
        });
        setCustomVariables(defaults);
      }
    }
  // Only run once when scenarios first load
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [scenarios]);

  // ─── Data fetchers ────────────────────────────────────────────

  const fetchProducts = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/products`);
      if (res.ok) setProducts(await res.json());
    } catch (e) {
      console.error("Failed to fetch products:", e);
    }
  };

  const fetchScenarios = async () => {
    setScenariosLoadError(null);
    const tryFetch = async (url: string): Promise<Scenario[] | null> => {
      try {
        const res = await fetch(url, { credentials: "omit" });
        if (!res.ok) return null;
        const data = await res.json();
        return Array.isArray(data) ? data : null;
      } catch {
        return null;
      }
    };
    try {
      let data: Scenario[] | null = null;
      if (API_BASE_URL.startsWith("http")) {
        data = await tryFetch(`${API_BASE_URL}/scenarios`);
      }
      if (data == null) {
        data = await tryFetch("/api/v1/scenarios");
      }
      if (data != null) {
        setScenarios(data);
      } else {
        setScenariosLoadError("Macera listesi yüklenemedi. Lütfen tekrar deneyin.");
      }
    } catch (e) {
      console.error("Failed to fetch scenarios:", e);
      setScenariosLoadError("Macera listesi yüklenemedi. Bağlantıyı kontrol edip tekrar deneyin.");
    }
  };

  const fetchLearningOutcomes = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/scenarios/learning-outcomes`);
      if (res.ok) {
        const data = await res.json();
        setLearningOutcomes(data);
        if (data.length > 0) setExpandedCategories([data[0].category]);
      }
    } catch (e) {
      console.error("Failed to fetch learning outcomes:", e);
    }
  };

  const fetchVisualStyles = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/scenarios/visual-styles`);
      if (res.ok) {
        const data = await res.json();
        setVisualStyles(data);
        if (data.length > 0) setSelectedStyle(data[0].id);
      }
    } catch (e) {
      console.error("Failed to fetch visual styles:", e);
    }
  };

  // ─── Helpers ──────────────────────────────────────────────────

  const getSelectedOutcomeNames = useCallback((): string[] => {
    const names: string[] = [];
    learningOutcomes.forEach((cat) => {
      cat.items.forEach((item) => {
        if (selectedOutcomes.includes(item.id)) names.push(item.name);
      });
    });
    return names;
  }, [learningOutcomes, selectedOutcomes]);

  const getSelectedStylePrompt = useCallback((): string => {
    const style = visualStyles.find((s) => s.id === selectedStyle);
    return style?.prompt_modifier || style?.name || "";
  }, [visualStyles, selectedStyle]);

  const calculateTotalPrice = useCallback((): number => {
    const product = products.find((p) => p.id === selectedProduct);
    const scenario = scenarios.find((s) => s.id === selectedScenario);
    // Scenario price override takes priority over product base price
    const basePrice = scenario?.price_override_base ?? product?.base_price ?? 0;
    let total = basePrice;
    if (hasAudioBook) total += audioType === "cloned" ? 300 : 150;
    return total;
  }, [products, scenarios, selectedProduct, selectedScenario, hasAudioBook, audioType]);

  // ─── Navigation ───────────────────────────────────────────────

  const goToMainStep = (step: number, sub?: SubStep) => {
    setMainStep(step);
    setMaxMainStep((prev) => Math.max(prev, step));
    if (sub) setSubStep(sub);
  };

  // ─── Photo handlers ───────────────────────────────────────────

  const handleAnalyzePhoto = async () => {
    if (!childPhoto) return;
    setUploadingPhoto(true);
    try {
      await new Promise((resolve) => setTimeout(resolve, 1500));
      setFaceDetected(true);
      toast({ title: "Başarılı", description: "Yüz tespit edildi! Devam edebilirsiniz." });
    } catch {
      toast({ title: "Hata", description: "Yüz tespit edilemedi.", variant: "destructive" });
    } finally {
      setUploadingPhoto(false);
    }
  };

  // ─── Story generation ─────────────────────────────────────────

  const handleGenerateStory = async () => {
    if (!selectedScenario) {
      const description =
        scenarios.length === 0
          ? "Henüz macera eklenmemiş. Yönetici panelinden Senaryo & İçerik bölümüne macera eklenmesi gerekiyor."
          : "Lütfen bir macera seçin.";
      toast({ title: "Hata", description, variant: "destructive" });
      return;
    }

    setLoading(true);
    try {
      const selectedProductObj = products.find((p) => p.id === selectedProduct);
      const selectedScenarioObj = scenarios.find((s) => s.id === selectedScenario);

      if (selectedProductObj && (!selectedProductObj.default_page_count || selectedProductObj.default_page_count < 4)) {
        toast({
          title: "Hata",
          description: "Seçilen ürünün sayfa sayısı ayarı eksik. Lütfen farklı bir ürün seçin veya yöneticinize başvurun.",
          variant: "destructive",
        });
        setLoading(false);
        return;
      }
      // Öncelik: linked_product_page_count > scenario.default_page_count > product > 16
      const pageCount =
        (selectedScenarioObj?.linked_product_page_count && selectedScenarioObj.linked_product_page_count >= 4
          ? selectedScenarioObj.linked_product_page_count
          : null) ??
        (selectedScenarioObj?.default_page_count && selectedScenarioObj.default_page_count >= 4
          ? selectedScenarioObj.default_page_count
          : null) ??
        selectedProductObj?.default_page_count ??
        16;
      const age = Math.min(12, Math.max(2, parseInt(String(childInfo.age), 10) || 7));

      const payload = buildStoryPayload({
        childName: childInfo.name,
        childAge: age,
        childGender: childInfo.gender,
        scenarioId: selectedScenario,
        learningOutcomeNames: getSelectedOutcomeNames(),
        visualStylePromptModifier: getSelectedStylePrompt(),
        visualStyleId: selectedStyle,
        pageCount,
        clothingDescription: normalizeClothingDescription(childInfo.clothingDescription),
        customVariables,
      });

      const clothingErr = validateClothingDescription(payload.clothing_description || "");
      if (clothingErr) {
        toast({ title: "Kıyafet Hatası", description: clothingErr, variant: "destructive" });
        return;
      }

      const data = await generateStoryV2(payload);

      if (data.success && data.story) {
        setStoryStructure(data.story);
        setStoryMetadata(data.metadata ?? null);

        const scenario = scenarios.find((s) => s.id === selectedScenario);
        const warnings = checkPromptCompliance(data.story.pages, scenario?.flags?.no_family);
        if (warnings.length > 0) {
          console.warn("[V2 Compliance]", warnings);
          toast({ title: "Uyarı", description: warnings[0], variant: "destructive" });
        }

        toast({
          title: "Başarılı",
          description: `"${data.story.title}" hikayesi oluşturuldu! (${data.story.pages.length} sayfa)`,
        });
        goToMainStep(3, "story-review");
      } else {
        throw new Error(data.error || "Hikaye oluşturulamadı");
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : "Hikaye oluşturulamadı";
      toast({ title: "Hata", description: message, variant: "destructive" });
    } finally {
      setLoading(false);
    }
  };

  // ─── Preview image generation ─────────────────────────────────

  const handleGeneratePreview = async (freshContact?: ContactInfo) => {
    if (!storyStructure) return;

    // Use freshly passed contact info, existing state, or checkout info
    const ci = freshContact || contactInfo;
    const effectiveName = ci
      ? `${ci.firstName} ${ci.lastName}`
      : parentInfo.fullName || "Kullanıcı";
    const effectiveEmail = ci?.email || parentInfo.email || "";
    const effectivePhone = ci?.phone || parentInfo.phone || "";

    if (!effectiveEmail) {
      toast({
        title: "Hata",
        description: "Önizleme oluşturmak için e-posta adresi gerekli.",
        variant: "destructive",
      });
      setSubStep("contact");
      return;
    }

    setPreviewLoading(true);
    setPreviewImages({});
    setSubStep("image-preview");

    try {
      let childPhotoUrl: string | null = null;
      if (childPhotoPreview) {
        if (childPhotoPreview.startsWith("http")) {
          childPhotoUrl = childPhotoPreview;
        } else {
          try {
            const uploadData = await uploadTempImage(childPhotoPreview);
            if (uploadData.success && uploadData.url) childPhotoUrl = uploadData.url;
          } catch {
            /* leave null */
          }
        }
      }

      const selectedStyleObj = visualStyles.find((s) => s.id === selectedStyle);

      const data = await generatePreviewImages({
        user_id: leadUserId || ci?.userId || null,
        parent_name: effectiveName,
        parent_email: effectiveEmail,
        parent_phone: effectivePhone,
        child_name: childInfo.name,
        child_age: Number.parseInt(childInfo.age) || 7,
        child_gender: childInfo.gender,
        child_photo_url: childPhotoUrl,
        product_id: selectedProduct || null,
        product_name: products.find((p) => p.id === selectedProduct)?.name,
        product_price: calculateTotalPrice(),
        story_title: storyStructure.title,
        story_pages: storyStructure.pages.map((p) => ({
          page_number: p.page_number,
          text: p.text,
          visual_prompt: p.visual_prompt,
          ...(p.v3_composed ? { v3_composed: true, negative_prompt: p.negative_prompt || "" } : {}),
          ...(p.page_type ? { page_type: p.page_type } : {}),
          ...(p.composer_version ? { composer_version: p.composer_version } : {}),
          ...(p.pipeline_version ? { pipeline_version: p.pipeline_version } : {}),
        })),
        scenario_id: selectedScenario || null,
        scenario_name: scenarios.find((s) => s.id === selectedScenario)?.name || null,
        visual_style: getSelectedStylePrompt(),
        visual_style_name: selectedStyleObj?.name ?? selectedStyleObj?.display_name ?? null,
        learning_outcomes:
          getSelectedOutcomeNames().length > 0 ? getSelectedOutcomeNames() : null,
        clothing_description:
          normalizeClothingDescription(
            storyMetadata?.clothing_description || childInfo.clothingDescription
          ) || undefined,
        id_weight: selectedStyleObj?.id_weight || null,
      });

      if (data.success && data.trial_id) {
        setTrialId(data.trial_id);
        setTrialToken(data.trial_token ?? null);
        await pollPreviewStatus(data.trial_id, data.trial_token ?? undefined);
      } else {
        throw new Error("Önizleme oluşturulamadı");
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : "Önizleme oluşturulamadı";
      toast({ title: "Hata", description: message, variant: "destructive" });
      setPreviewLoading(false);
    }
  };

  const pollPreviewStatus = async (id: string, token?: string) => {
    const MAX_DURATION_MS = 15 * 60 * 1000;
    const BASE_INTERVAL = 3000;
    const MAX_INTERVAL = 15000;
    const MAX_NET_RETRIES = 5;
    const MAX_429_RETRIES = 10;
    const startTime = Date.now();
    let interval = BASE_INTERVAL;
    let netErrors = 0;
    let rateLimitErrors = 0;

    const poll = async () => {
      try {
        const status = await getTrialStatus(id, token);
        netErrors = 0;
        rateLimitErrors = 0;
        if (status.generation_progress) setGenerationProgress(status.generation_progress);

        if (status.is_failed) {
          setGenerationProgress(null);
          setPreviewLoading(false);
          toast({
            title: "Oluşturulamadı",
            description:
              status.generation_progress?.message ||
              "Hikaye oluşturulurken bir hata oluştu. Lütfen tekrar deneyin.",
            variant: "destructive",
          });
          return;
        }

        if (status.is_preview_ready) {
          const preview = await getTrialPreview(id, token);
          if (preview.success && preview.preview_images) {
            const images: Record<string, string> = {};
            for (const [key, url] of Object.entries(preview.preview_images)) {
              images[key] = url;
            }
            setPreviewImages(images);
          }
          setGenerationProgress(null);
          setPreviewLoading(false);
          return;
        }

        if (Date.now() - startTime >= MAX_DURATION_MS) {
          toast({
            title: "Zaman Aşımı",
            description: "Görseller hazırlanamadı, lütfen tekrar deneyin.",
            variant: "destructive",
          });
          setGenerationProgress(null);
          setPreviewLoading(false);
          return;
        }

        interval = Math.min(interval * 1.3, MAX_INTERVAL);
        setTimeout(poll, interval);
      } catch (err: unknown) {
        const isRateLimit =
          err instanceof APIError && err.status === 429;

        if (isRateLimit) {
          rateLimitErrors++;
          if (rateLimitErrors >= MAX_429_RETRIES) {
            setGenerationProgress(null);
            setPreviewLoading(false);
            toast({
              title: "Çok Fazla İstek",
              description: "Sunucu yoğun. Lütfen birkaç dakika bekleyip tekrar deneyin.",
              variant: "destructive",
            });
            return;
          }
          const retryAfter = Math.min(interval * 2 * rateLimitErrors, 30000);
          setTimeout(poll, retryAfter);
          return;
        }

        netErrors++;
        if (netErrors >= MAX_NET_RETRIES) {
          setGenerationProgress(null);
          setPreviewLoading(false);
          toast({
            title: "Bağlantı Hatası",
            description: "Sunucuya ulaşılamıyor. Lütfen internet bağlantınızı kontrol edin.",
            variant: "destructive",
          });
          return;
        }
        const retryDelay = Math.min(interval * 2, MAX_INTERVAL);
        setTimeout(poll, retryDelay);
      }
    };

    await poll();
  };

  // ─── Submit order ─────────────────────────────────────────────

  const handleSubmitOrder = async (
    testParentInfo?: { fullName: string; email: string; phone: string },
    overrideDedicationNote?: string,
    promoCode?: string
  ) => {
    const orderParentInfo = testParentInfo || parentInfo;

    if (!storyStructure || !orderParentInfo.email || !orderParentInfo.fullName) {
      toast({
        title: "Hata",
        description: "Eksik bilgi: E-posta veya isim gerekli",
        variant: "destructive",
      });
      return;
    }

    setSubmittingOrder(true);
    try {
      if (!_trialId) {
        throw new Error("Trial bulunamadı — lütfen önizleme adımından tekrar başlayın");
      }

      // Capture lead at checkout time
      if (!leadUserId) {
        try {
          const leadRes = await fetch(`${API_BASE_URL}/leads/capture`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              first_name: orderParentInfo.fullName.split(" ")[0],
              last_name: orderParentInfo.fullName.split(" ").slice(1).join(" ") || "",
              phone: orderParentInfo.phone || "",
              email: orderParentInfo.email,
            }),
          });
          if (leadRes.ok) {
            const leadData = await leadRes.json();
            setLeadUserId(leadData.user_id);
            localStorage.setItem("lead_user_id", leadData.user_id);
          }
        } catch {
          // Non-blocking: lead capture failure shouldn't stop order
        }
      }

      if (!promoCode) {
        // Paid order: initiate Iyzico checkout → redirect to payment page
        const paymentData = await createTrialPayment(_trialId, _trialToken ?? undefined);
        if (!paymentData.success || !paymentData.payment_url) {
          throw new Error("Ödeme sayfası oluşturulamadı. Lütfen tekrar deneyin.");
        }
        // Save order info to sessionStorage so we can resume after payment callback
        sessionStorage.setItem("pending_trial_id", _trialId);
        sessionStorage.setItem("pending_trial_token", _trialToken ?? "");
        sessionStorage.setItem("pending_parent_name", orderParentInfo.fullName);
        sessionStorage.setItem("pending_parent_email", orderParentInfo.email);
        sessionStorage.setItem("pending_parent_phone", orderParentInfo.phone || "");
        sessionStorage.setItem("pending_dedication_note", (overrideDedicationNote ?? dedicationNote) || "");
        sessionStorage.setItem("pending_has_audio", String(hasAudioBook));
        sessionStorage.setItem("pending_audio_type", hasAudioBook ? (audioType ?? "") : "");
        sessionStorage.setItem("pending_audio_voice_id", hasAudioBook && audioType === "cloned" ? (clonedVoiceId ?? "") : "");
        window.location.href = paymentData.payment_url;
        return;
      }

      const data = await completeTrial(
        {
          trial_id: _trialId,
          payment_reference: `promo:${promoCode}`,
          parent_name: orderParentInfo.fullName,
          parent_email: orderParentInfo.email,
          parent_phone: orderParentInfo.phone || undefined,
          dedication_note: (overrideDedicationNote ?? dedicationNote) || null,
          promo_code: promoCode,
          has_audio_book: hasAudioBook,
          audio_type: hasAudioBook ? audioType : null,
          audio_voice_id: hasAudioBook && audioType === "cloned" ? clonedVoiceId : null,
          voice_sample_url: hasAudioBook && audioType === "cloned" ? voiceSampleUrl : null,
        },
        _trialToken ?? undefined,
      );

      if (data.success) {
        setOrderComplete(true);
        goToMainStep(5, "success");
      } else {
        throw new Error("Sipariş tamamlanamadı");
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : "Sipariş gönderilemedi";
      toast({ title: "Hata", description: message, variant: "destructive" });
    } finally {
      setSubmittingOrder(false);
    }
  };

  // ─── Audio handlers ───────────────────────────────────────────

  const handleVoiceSampleRecorded = async (audioBase64: string) => {
    setIsCloningVoice(true);
    try {
      toast({ title: "Ses klonlanıyor...", description: "Bu işlem 30-60 saniye sürebilir." });
      const cloneResponse = await fetch(`${API_BASE_URL}/ai/clone-voice-direct`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          voice_name: `${childInfo.name || "ebeveyn"}_voice`,
          audio_base64: audioBase64,
        }),
      });
      if (cloneResponse.ok) {
        const cloneData = await cloneResponse.json();
        setClonedVoiceId(cloneData.voice_id);
        setVoiceSampleUrl("cloned");
        toast({ title: "Başarılı!", description: "Sesiniz başarıyla klonlandı." });
      } else {
        const errorData = await cloneResponse.json();
        throw new Error(errorData.detail || "Klonlama başarısız");
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : "Ses işleme sırasında hata oluştu";
      toast({ title: "Hata", description: message, variant: "destructive" });
      setVoiceSampleUrl("");
      setClonedVoiceId("");
    } finally {
      setIsCloningVoice(false);
    }
  };

  // ─── Derived state ────────────────────────────────────────────

  const selectedProductObj = products.find((p) => p.id === selectedProduct);
  const basePrice = selectedProductObj?.base_price ?? 0;
  const audioAddonPrice = audioType === "cloned" ? 300 : 150;

  // ─── Render helpers ───────────────────────────────────────────

  const renderTrustBar = () => (
    <div className="flex flex-wrap items-center justify-center gap-4 py-3 text-xs text-gray-500 sm:gap-6 sm:text-sm">
      <span className="flex items-center gap-1.5">
        <ShieldCheck className="h-4 w-4 text-green-500" />
        Güvenli Ödeme
      </span>
      <span className="flex items-center gap-1.5">
        <Truck className="h-4 w-4 text-blue-500" />
        Ücretsiz Kargo
      </span>
      <span className="flex items-center gap-1.5">
        <Heart className="h-4 w-4 text-pink-500" />
        Mutluluk Garantisi
      </span>
    </div>
  );

  // ─── RENDER ───────────────────────────────────────────────────

  return (
    <div className="create-flow min-h-screen w-full max-w-[100vw] overflow-x-hidden bg-gradient-to-b from-purple-50/80 via-white to-pink-50/50 text-sm touch-manipulation">
      {/* Header with step indicator */}
      <header className="sticky top-0 z-30 w-full border-b border-gray-100 bg-white/90 backdrop-blur-md">
        <div className="mx-auto w-full max-w-6xl px-3 py-2 sm:px-4">
          <StepIndicator
            steps={STEP_DEFS}
            currentStep={mainStep}
            maxReached={maxMainStep}
            onStepClick={(s) => {
              if (s < mainStep) {
                // Navigate back to first sub-step of that main step
                const firstSubs: Record<number, SubStep> = {
                  1: "child-info",
                  2: "product",
                  3: "story-review",
                  4: "checkout",
                  5: "success",
                };
                goToMainStep(s, firstSubs[s]);
              }
            }}
          />
        </div>
      </header>

      <main className="mx-auto w-full min-w-0 max-w-6xl px-3 py-4 sm:px-4">
        <div className="grid min-w-0 gap-4 lg:grid-cols-3">
          {/* Main content area */}
          <div className="min-w-0 lg:col-span-2">
            {/* ════════════════════════════════════════════════════════════ */}
            {/* STEP 1: Hikayeni Oluştur (Child + Adventure + Outcomes)    */}
            {/* ════════════════════════════════════════════════════════════ */}
            {mainStep === 1 && (
              <>
                {/* Sub-step 1a: Child info */}
                {subStep === "child-info" && (
                  <div className="space-y-4 pb-20 min-h-0 sm:pb-6">
                    <div className="text-center">
                      <h1 className="text-base font-bold text-gray-800 sm:text-lg md:text-xl">
                        <Sparkles className="mr-1.5 inline h-4 w-4 text-purple-500 sm:h-5 sm:w-5" />
                        Hikayeye Başlayalım!
                      </h1>
                      <p className="mt-1 text-sm text-gray-600">
                        Çocuğunuzun bilgilerini girin, gerisini biz halledelim.
                      </p>
                    </div>

                    <div className="mx-auto w-full min-w-0 max-w-2xl px-2 sm:px-0">
                      <ChildInfoForm
                        childInfo={childInfo}
                        onUpdate={setChildInfo}
                        onContinue={() => setSubStep("learning-outcomes")}
                        onBack={() => setSubStep("adventure")}
                        scenarioName={scenarios.find((s) => s.id === selectedScenario)?.name}
                        hideClothing
                      />

                      {/* Custom inputs if scenario already selected */}
                      {(() => {
                        const sel = scenarios.find((s) => s.id === selectedScenario);
                        if (sel?.custom_inputs_schema?.length) {
                          return (
                            <Card className="mt-3 border-purple-200 bg-gradient-to-br from-purple-50 to-pink-50">
                              <CardContent className="p-4 pt-4">
                                <CustomInputsForm
                                  fields={sel.custom_inputs_schema}
                                  values={customVariables}
                                  onChange={setCustomVariables}
                                />
                              </CardContent>
                            </Card>
                          );
                        }
                        return null;
                      })()}
                    </div>

                    {/* Privacy reassurance */}
                    <div className="mx-auto max-w-md rounded-lg border border-blue-100 bg-blue-50/50 p-2.5 text-center text-xs text-blue-700">
                      <Info className="mr-1 inline h-3 w-3" />
                      Bilgileriniz yalnızca kitap oluşturmak için kullanılır ve KVKK kapsamında korunur.
                    </div>
                  </div>
                )}

                {/* Sub-step 1b: Adventure selection */}
                {subStep === "adventure" && (
                  <Card className="border-0 bg-transparent shadow-none">
                    <CardContent className="p-0">
                      {scenariosLoadError && (
                        <div className="mb-3 flex flex-col items-center gap-2 rounded-lg border border-amber-200 bg-amber-50 p-3 text-center">
                          <p className="text-xs text-amber-800">{scenariosLoadError}</p>
                          <Button variant="outline" size="sm" onClick={() => fetchScenarios()}>
                            Tekrar dene
                          </Button>
                        </div>
                      )}
                      <AdventureSelector
                        scenarios={scenarios}
                        selectedScenario={selectedScenario}
                        onSelect={(scenarioId) => {
                          setSelectedScenario(scenarioId);
                          const scenario = scenarios.find((s) => s.id === scenarioId);
                          if (scenario?.custom_inputs_schema) {
                            const defaults: Record<string, string> = {};
                            scenario.custom_inputs_schema.forEach((field: CustomInputField) => {
                              if (field.default) defaults[field.key] = field.default;
                            });
                            setCustomVariables(defaults);
                          } else {
                            setCustomVariables({});
                          }
                        }}
                        onContinue={() => setSubStep("child-info")}
                        onBack={() => {}}
                        childName={childInfo.name || undefined}
                      />
                    </CardContent>
                  </Card>
                )}

                {/* Sub-step 1c: Learning outcomes */}
                {subStep === "learning-outcomes" && (
                  <div className="mx-auto max-w-4xl">
                    <LearningOutcomeSelector
                      selectedOutcomes={selectedOutcomes}
                      onSelect={setSelectedOutcomes}
                      onContinue={() => goToMainStep(2, "product")}
                      onBack={() => setSubStep("adventure")}
                    />
                  </div>
                )}
              </>
            )}

            {/* ════════════════════════════════════════════════════════════ */}
            {/* STEP 2: Stil & Fotoğraf (Product + Photo + Style)          */}
            {/* ════════════════════════════════════════════════════════════ */}
            {mainStep === 2 && (
              <div className="text-sm touch-manipulation min-h-0">
                {/* Sub-step 2a: Product selection */}
                {subStep === "product" && (
                  <div className="mx-auto max-w-5xl px-1 sm:px-0">
                    <ProductAutoSkipOrSelect
                      products={products}
                      selectedProduct={selectedProduct}
                      onSelect={setSelectedProduct}
                      onSkipped={() => setSubStep("photo")}
                      onContinue={() => setSubStep("photo")}
                      onBack={() => goToMainStep(1, "learning-outcomes")}
                    />
                  </div>
                )}

                {/* Sub-step 2b: Photo upload */}
                {subStep === "photo" && (
                  <div className="mx-auto max-w-4xl px-1 sm:px-0">
                    <PhotoUploaderStep
                      childName={childInfo.name}
                      photoPreview={childPhotoPreview}
                      additionalPhotos={additionalPhotos}
                      onPhotoSelect={(file) => {
                        setChildPhoto(file);
                        setFaceDetected(false);
                        setAdditionalPhotos([]);
                        setAdditionalPhotoFiles([]);
                        const reader = new FileReader();
                        reader.onload = (e) => setChildPhotoPreview(e.target?.result as string);
                        reader.readAsDataURL(file);
                      }}
                      onAdditionalPhotoSelect={(files) => {
                        files.forEach((file) => {
                          const reader = new FileReader();
                          reader.onload = (e) =>
                            setAdditionalPhotos((prev) =>
                              [...prev, e.target?.result as string].slice(0, 4)
                            );
                          reader.readAsDataURL(file);
                        });
                        setAdditionalPhotoFiles((prev) => [...prev, ...files].slice(0, 4));
                      }}
                      onRemoveAdditionalPhoto={(index) => {
                        setAdditionalPhotos((prev) => prev.filter((_, i) => i !== index));
                        setAdditionalPhotoFiles((prev) => prev.filter((_, i) => i !== index));
                      }}
                      onAnalyze={handleAnalyzePhoto}
                      isAnalyzing={uploadingPhoto}
                      faceDetected={faceDetected}
                      onContinue={() => setSubStep("style")}
                      onBack={() => {
                        if (products.length > 1) setSubStep("product");
                        else goToMainStep(1, "learning-outcomes");
                      }}
                      onClear={() => {
                        setChildPhoto(null);
                        setChildPhotoPreview("");
                        setFaceDetected(false);
                        setAdditionalPhotos([]);
                        setAdditionalPhotoFiles([]);
                      }}
                      parentEmail={contactInfo?.email || parentInfo.email}
                    />

                    {/* Photo privacy note */}
                    <div className="mt-3 rounded-lg border border-green-100 bg-green-50/50 p-2.5 text-center text-xs text-green-700">
                      <ShieldCheck className="mr-1 inline h-3 w-3" />
                      Fotoğraflar yalnızca kitap illüstrasyonu için kullanılır.
                      Teslimat sonrası 30 gün içinde otomatik silinir (KVKK).
                    </div>
                  </div>
                )}

                {/* Sub-step 2c: Visual style → triggers story generation */}
                {subStep === "style" && (
                  <div className="mx-auto max-w-5xl px-1 pb-24 sm:px-0">
                    <StyleSelectorStep
                      visualStyles={visualStyles}
                      selectedStyle={selectedStyle}
                      onSelect={(styleId) => {
                        setSelectedStyle(styleId);
                        setCustomIdWeight(null);
                      }}
                      onContinue={handleGenerateStory}
                      onBack={() => setSubStep("photo")}
                      childName={childInfo.name}
                      customIdWeight={customIdWeight}
                      onIdWeightChange={setCustomIdWeight}
                      isLoading={loading}
                    />
                    {loading && (
                      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
                        <div className="mx-4 max-w-sm rounded-xl bg-white p-5 text-center shadow-2xl">
                          <div className="relative mx-auto mb-3 h-12 w-12">
                            <div className="absolute inset-0 rounded-full border-2 border-purple-200" />
                            <div className="absolute inset-0 animate-spin rounded-full border-2 border-purple-600 border-t-transparent" />
                          </div>
                          <h3 className="mb-1.5 text-lg font-bold text-gray-800">
                            Hikaye Oluşturuluyor
                          </h3>
                          <p className="text-sm text-gray-600">
                            Yapay zeka <strong>{childInfo.name}</strong> için özel bir hikaye yazıyor...
                          </p>
                          <p className="mt-2 text-xs text-gray-400">
                            Bu işlem 30-60 saniye sürebilir
                          </p>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}

            {/* ════════════════════════════════════════════════════════════ */}
            {/* STEP 3: İncele & Onayla (Story + Preview + Audio)          */}
            {/* ════════════════════════════════════════════════════════════ */}
            {mainStep === 3 && (
              <>
                {/* Sub-step 3a: Story review */}
                {subStep === "story-review" && storyStructure && (
                  <StoryReviewStep
                    storyStructure={storyStructure}
                    childName={childInfo.name}
                    onUpdateStory={setStoryStructure}
                    onRegenerateStory={handleGenerateStory}
                    onApproveAndContinue={() => {
                      if (contactInfo?.email) {
                        handleGeneratePreview(contactInfo);
                      } else {
                        setSubStep("contact");
                      }
                    }}
                    onBack={() => goToMainStep(2, "style")}
                    isRegenerating={loading}
                  />
                )}

                {/* Sub-step 3a½: Contact capture (required before preview) */}
                {subStep === "contact" && storyStructure && (
                  <div className="space-y-3">
                    <div className="mx-auto max-w-md rounded-lg border border-blue-100 bg-blue-50/50 p-2.5 text-center text-xs text-blue-700">
                      <Mail className="mr-1 inline h-4 w-4" />
                      Önizleme görsellerini oluşturabilmemiz için iletişim bilgilerinize ihtiyacımız var.
                      Kitabınız hazır olduğunda sizi bilgilendireceğiz.
                    </div>
                    <UserContactForm
                      onComplete={(userId, info) => {
                        if (!info.email) {
                          toast({
                            title: "E-posta Gerekli",
                            description: "Önizleme oluşturmak ve kitabınız hakkında bilgilendirilmek için e-posta adresi zorunludur.",
                            variant: "destructive",
                          });
                          return;
                        }
                        handleLeadCapture(userId, info);
                        handleGeneratePreview(info);
                      }}
                      initialData={contactInfo ?? undefined}
                    />
                    <div className="text-center">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setSubStep("story-review")}
                        className="text-gray-500"
                      >
                        <ChevronLeft className="mr-1 h-4 w-4" />
                        Hikayeye Dön
                      </Button>
                    </div>
                  </div>
                )}

                {/* Sub-step 3b: Image preview */}
                {subStep === "image-preview" && storyStructure && (
                  <ImagePreviewStep
                    childName={childInfo.name}
                    previewImages={previewImages}
                    backCoverImageUrl={previewImages["backcover"] ?? null}
                    onApprove={() => setSubStep("audio")}
                    onBack={() => setSubStep("story-review")}
                    isLoading={previewLoading}
                    generationProgress={generationProgress}
                  />
                )}

                {/* Sub-step 3c: Audio selection */}
                {subStep === "audio" && storyStructure && (
                  <AudioSelectionStep
                    childName={childInfo.name}
                    basePrice={basePrice}
                    selectedOption={!hasAudioBook ? "none" : audioType}
                    systemVoice={systemVoice}
                    clonedVoiceId={clonedVoiceId}
                    isCloningVoice={isCloningVoice}
                    onOptionChange={(option) => {
                      if (option === "none") {
                        setHasAudioBook(false);
                      } else {
                        setHasAudioBook(true);
                        setAudioType(option);
                      }
                    }}
                    onSystemVoiceChange={setSystemVoice}
                    onVoiceRecorded={handleVoiceSampleRecorded}
                    onContinue={() => {
                      if (hasAudioBook && audioType === "cloned" && !clonedVoiceId) {
                        toast({
                          title: "Uyarı",
                          description: "Ses klonlama tamamlanmadı. Sistem sesi kullanılacak.",
                        });
                        setAudioType("system");
                      }
                      goToMainStep(4, "checkout");
                    }}
                    onBack={() => setSubStep("image-preview")}
                    isTestMode={false}
                    isSubmitting={submittingOrder}
                  />
                )}
              </>
            )}

            {/* ════════════════════════════════════════════════════════════ */}
            {/* STEP 4: Teslimat & Ödeme (Checkout)                        */}
            {/* ════════════════════════════════════════════════════════════ */}
            {mainStep === 4 && subStep === "checkout" && storyStructure && (
              <CheckoutStep
                childName={childInfo.name}
                storyTitle={storyStructure.title}
                coverImageUrl={
                  Object.values(previewImages).length > 0
                    ? Object.values(previewImages)[0]
                    : null
                }
                basePrice={basePrice}
                audioPrice={audioAddonPrice}
                hasAudioBook={hasAudioBook}
                audioType={audioType}
                productName={selectedProductObj?.name || "Kişisel Hikaye Kitabı"}
                initialShipping={
                  contactInfo
                    ? {
                        fullName: `${contactInfo.firstName} ${contactInfo.lastName}`.trim(),
                        email: contactInfo.email || "",
                        phone: contactInfo.phone || "",
                      }
                    : undefined
                }
                onComplete={(shippingInfo, _paymentInfo, promoCode) => {
                  const pi = {
                    fullName: shippingInfo.fullName,
                    email: shippingInfo.email,
                    phone: shippingInfo.phone,
                  };
                  setParentInfo(pi);
                  setDedicationNote(shippingInfo.dedicationNote || "");
                  handleSubmitOrder(pi, shippingInfo.dedicationNote || "", promoCode ?? undefined);
                }}
                onBack={() => goToMainStep(3, "audio")}
                isProcessing={submittingOrder}
              />
            )}

            {/* ════════════════════════════════════════════════════════════ */}
            {/* STEP 5: Tamamlandı (Success)                               */}
            {/* ════════════════════════════════════════════════════════════ */}
            {mainStep === 5 && subStep === "success" && (
              <div className="mx-auto max-w-2xl">
                <Card className="border-0 bg-gradient-to-br from-green-50 to-emerald-50 shadow-xl">
                  <CardContent className="space-y-4 p-5 text-center">
                    <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-br from-green-400 to-emerald-500 shadow-lg">
                      <svg className="h-9 w-9 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                    </div>

                    <div className="space-y-1">
                      <h2 className="text-xl font-bold text-gray-800">
                        Siparişiniz Alındı! 🎉
                      </h2>
                      <p className="text-sm text-gray-600">Kitabınız hazırlanıyor...</p>
                    </div>

                    <div className="space-y-3 rounded-lg border border-green-200 bg-white/80 p-4 backdrop-blur">
                      <div className="flex items-center justify-center gap-2 text-gray-700">
                        <Mail className="h-5 w-5 text-green-500" />
                        <span className="text-sm font-medium">
                          {parentInfo.email || contactInfo?.email || "E-posta adresinize"}
                        </span>
                      </div>
                      <p className="text-xs text-gray-600">
                        Kitabınız hazır olduğunda <strong>e-posta</strong> ile bilgilendirileceksiniz.
                        İnceleyip onayladıktan sonra baskıya gönderilecektir.
                      </p>
                    </div>

                    <div className="grid grid-cols-2 gap-3 text-xs">
                      <div className="rounded-lg border border-green-200 bg-white p-3">
                        <Truck className="mx-auto mb-1 h-5 w-5 text-green-500" />
                        <p className="font-medium text-gray-700">Tahmini Teslimat</p>
                        <p className="text-green-600">3-5 iş günü</p>
                      </div>
                      <div className="rounded-lg border border-blue-200 bg-white p-3">
                        <ShieldCheck className="mx-auto mb-1 h-5 w-5 text-blue-500" />
                        <p className="font-medium text-gray-700">Fotoğraflar</p>
                        <p className="text-blue-600">Güvenle silinecek</p>
                      </div>
                    </div>

                    {storyStructure && (
                      <div className="border-t border-green-200 pt-3">
                        <p className="mb-1 text-xs text-gray-500">Hazırlanan hikaye:</p>
                        <div className="flex items-center justify-center gap-1.5">
                          <span className="text-lg">📚</span>
                          <span className="text-sm font-semibold text-gray-700">{storyStructure.title}</span>
                        </div>
                        <p className="mt-0.5 text-xs text-gray-500">
                          {storyStructure.pages.length} sayfa &bull; {childInfo.name} için
                        </p>
                      </div>
                    )}

                    <div className="pt-3">
                      <Button
                        variant="outline"
                        onClick={() => {
                          setMainStep(1);
                          setMaxMainStep(1);
                          setSubStep("child-info");
                          setStoryStructure(null);
                          setOrderComplete(false);
                          setPreviewImages({});
                          setTrialId(null);
                          setTrialToken(null);
                        }}
                        className="text-gray-600 hover:text-gray-800"
                      >
                        Yeni Hikaye Oluştur
                      </Button>
                    </div>
                  </CardContent>
                </Card>

                <div className="mt-3 rounded-lg border border-blue-100 bg-blue-50/50 p-3 text-center text-xs text-blue-700">
                  Bu sayfayı güvenle kapatabilirsiniz. Kitabınız hazır olduğunda
                  e-posta ile bilgilendirileceksiniz.
                </div>
              </div>
            )}
          </div>

          {/* Right sidebar: Order Summary (not shown on step 5) */}
          {mainStep < 5 && (
            <div className="hidden lg:block">
              <OrderSummaryPanel
                productName={selectedProductObj?.name}
                basePrice={basePrice}
                hasAudioBook={hasAudioBook}
                audioPrice={audioAddonPrice}
                audioType={audioType}
                childName={childInfo.name || undefined}
                storyTitle={storyStructure?.title}
                coverImageUrl={
                  Object.values(previewImages).length > 0
                    ? Object.values(previewImages)[0]
                    : null
                }
                currentStep={mainStep}
              />
            </div>
          )}
        </div>

        {/* Trust bar at bottom */}
        {mainStep < 5 && renderTrustBar()}
      </main>

      {/* Mobile-only order summary bottom bar */}
      {mainStep >= 2 && mainStep < 5 && basePrice > 0 && (
        <div className="lg:hidden">
          <OrderSummaryPanel
            productName={selectedProductObj?.name}
            basePrice={basePrice}
            hasAudioBook={hasAudioBook}
            audioPrice={audioAddonPrice}
            audioType={audioType}
            childName={childInfo.name || undefined}
            storyTitle={storyStructure?.title}
            coverImageUrl={
              Object.values(previewImages).length > 0
                ? Object.values(previewImages)[0]
                : null
            }
            currentStep={mainStep}
          />
        </div>
      )}

      {/* Bottom padding for mobile sticky bar */}
      {mainStep >= 2 && mainStep < 5 && <div className="h-16 lg:hidden" />}
    </div>
  );
}

export default function CreatePage() {
  return (
    <Suspense fallback={<div className="flex min-h-screen items-center justify-center"><div className="h-8 w-8 animate-spin rounded-full border-4 border-purple-600 border-t-transparent" /></div>}>
      <CreatePageInner />
    </Suspense>
  );
}
