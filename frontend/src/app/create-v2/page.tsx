"use client";

import { useState, useEffect, useCallback, useRef, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import {
  Eye,
  CreditCard,
  PartyPopper,
  User,
  BookOpen,
  Palette,
  Info,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";


import { Button } from "@/components/ui/button";
import { useToast } from "@/hooks/use-toast";

// Existing sub-components (unchanged)
import AdventureSelector from "@/components/AdventureSelector";
import ChildInfoForm from "@/components/ChildInfoForm";
import CustomInputsForm from "@/components/CustomInputsForm";
import VisualsStep from "@/components/VisualsStep";
import AudioSelectionStep from "@/components/AudioSelectionStep";
import CheckoutStep from "@/components/CheckoutStep";
import ImagePreviewStep from "@/components/ImagePreviewStep";

// New components
import StepIndicator from "@/components/create/StepIndicator";
import OrderSummaryPanel from "@/components/create/OrderSummaryPanel";

import {
  API_BASE_URL,
  buildStoryPayload,
  generateStoryV2,
  generatePreviewImages,
  uploadTempImage,
  completeTrial,
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
  GenerationProgress,
} from "@/lib/api";

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

interface ShippingInfo {
  fullName: string;
  email: string;
  phone: string;
  address: string;
  city: string;
  district: string;
  postalCode: string;
  dedicationNote?: string;
}

interface PaymentInfo {
  cardNumber: string;
  cardName: string;
  expiryDate: string;
  cvv: string;
  installments: number;
}

// ─── Step definitions ───────────────────────────────────────────

const STEP_DEFS = [
  { label: "Kahraman", shortLabel: "Kahraman", icon: <User className="h-4 w-4" /> },
  { label: "Macera", shortLabel: "Macera", icon: <BookOpen className="h-4 w-4" /> },
  { label: "Görsel Stil", shortLabel: "Stil", icon: <Palette className="h-4 w-4" /> },
  { label: "Önizleme", shortLabel: "Önizleme", icon: <Eye className="h-4 w-4" /> },
  { label: "Ödeme", shortLabel: "Ödeme", icon: <CreditCard className="h-4 w-4" /> },
];

type SubStep =
  | "hero"       // Child details
  | "adventure"  // Scenario
  | "visuals"    // Photo & Style
  | "reveal"     // Story review
  | "checkout"   // Payment
  | "success";   // Completion


// ─── Main Component ─────────────────────────────────────────────

function CreatePageInner() {
  const searchParams = useSearchParams();
  const preselectedScenarioId = searchParams.get("scenario") ?? "";

  // ─── Navigation state ─────────────────────────────────────────
  const [mainStep, setMainStep] = useState(1);
  const [maxMainStep, setMaxMainStep] = useState(1);
  const [subStep, setSubStep] = useState<SubStep>("hero");

  // ─── Data lists (fetched once) ────────────────────────────────
  const [products, setProducts] = useState<Product[]>([]);
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [, setLearningOutcomes] = useState<LearningOutcomeCategory[]>([]);
  const [visualStyles, setVisualStyles] = useState<VisualStyle[]>([]);

  // ─── Selections ───────────────────────────────────────────────
  const [_selectedProduct, _setSelectedProduct] = useState<string>("");
  const [selectedScenario, setSelectedScenario] = useState<string>(preselectedScenarioId);
  const [selectedStyle, setSelectedStyle] = useState<string>("");
  const [customIdWeight, setCustomIdWeight] = useState<number | null>(null);

  // Boyama kitabı state
  const [coloringBookPrice, setColoringBookPrice] = useState<number>(0);
  const [hasColoringBook, setHasColoringBook] = useState(false);

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
  const [_uploadingPhoto, _setUploadingPhoto] = useState(false);
  const [faceDetected, setFaceDetected] = useState(false);

  // ─── Story ────────────────────────────────────────────────────
  const [loading, setLoading] = useState(false);
  const [storyStructure, setStoryStructure] = useState<StoryStructure | null>(null);

  // ─── Preview ──────────────────────────────────────────────────
  const [_trialId, _setTrialIdRaw] = useState<string | null>(() => {
    if (typeof window !== "undefined") return sessionStorage.getItem("current_trial_id");
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
    if (typeof window !== "undefined") return sessionStorage.getItem("current_trial_token");
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
  const [_voiceSampleUrl, _setVoiceSampleUrl] = useState<string>("");
  const [clonedVoiceId, setClonedVoiceId] = useState<string>("");
  const [isCloningVoice, setIsCloningVoice] = useState(false);

  // ─── Checkout ─────────────────────────────────────────────────
  const [, setParentInfo] = useState({ fullName: "", email: "", phone: "" });
  const [, setDedicationNote] = useState<string>("");
  const [submittingOrder, setSubmittingOrder] = useState(false);
  const [, setOrderComplete] = useState(false);
  const [, setCompletedOrderId] = useState<string | null>(null);

  // ─── Lead / Contact ────────────────────────────────────────────
  const [_leadUserId, _setLeadUserId] = useState<string | null>(null);
  const [_contactInfo, _setContactInfo] = useState<{ firstName: string; lastName: string; phone: string; email: string; userId: string } | null>(null);

  const { toast } = useToast();
  const _paymentCallbackHandled = useRef(false);

  // ─── Navigation Helper ────────────────────────────────────────
  const goToSubStep = (step: SubStep) => {
    setSubStep(step);
    const stepMap: Record<SubStep, number> = {
      hero: 1, adventure: 2, visuals: 3, reveal: 4, checkout: 5, success: 6,
    };
    const m = stepMap[step];
    setMainStep(m);
    setMaxMainStep((prev) => Math.max(prev, m));
  };

  // ─── Init ─────────────────────────────────────────────────────

  useEffect(() => {
    const fetchColoringBookPrice = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/coloring-books/active`);
        if (response.ok) {
          const data = await response.json();
          setColoringBookPrice(data.discounted_price || data.base_price);
        }
      } catch (error) {
        console.error("Failed to fetch coloring book price", error);
      }
    };
    fetchColoringBookPrice();
  }, []);

  useEffect(() => {
    const initializeSession = async () => {
      const storedUserId = localStorage.getItem("lead_user_id");
      if (storedUserId) {
        try {
          const response = await fetch(`${API_BASE_URL}/leads/${storedUserId}`, {
            headers: { "X-User-Id": storedUserId },
          });
          if (response.ok) {
            const data = await response.json();
            _setLeadUserId(data.user_id);
            _setContactInfo({
              firstName: data.first_name,
              lastName: data.last_name,
              phone: data.phone,
              email: data.email,
              userId: data.user_id,
            });
          } else localStorage.removeItem("lead_user_id");
        } catch { localStorage.removeItem("lead_user_id"); }
      }
    };
    initializeSession();
    fetchProducts();
    fetchScenarios();
    fetchLearningOutcomes();
    fetchVisualStyles();
  }, []);

  // Iyzico Callback
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
      const storedHasColoringBook = sessionStorage.getItem("pending_has_coloring_book") === "true";

      setSubmittingOrder(true);
      verifyTrialPayment(callbackTrialId, iyzico_token, storedTrialToken)
        .then(async (verifyResult) => {
          if (!verifyResult.success || !verifyResult.payment_reference) throw new Error(verifyResult.error || "Ödeme doğrulanamadı");
          const data = await completeTrial({
            trial_id: callbackTrialId,
            payment_reference: verifyResult.payment_reference,
            parent_name: storedName,
            parent_email: storedEmail,
            parent_phone: storedPhone || undefined,
            dedication_note: storedDedication || null,
            has_audio_book: storedHasAudio,
            audio_type: storedHasAudio ? storedAudioType : null,
            audio_voice_id: storedHasAudio && storedAudioType === "cloned" ? storedVoiceId : null,
            has_coloring_book: storedHasColoringBook,
          }, storedTrialToken);

          if (data.success) {
            ["pending_trial_id", "pending_trial_token", "pending_parent_name", "pending_parent_email", "pending_parent_phone", "pending_dedication_note", "pending_has_audio", "pending_audio_type", "pending_audio_voice_id", "pending_has_coloring_book"].forEach(k => sessionStorage.removeItem(k));
            setCompletedOrderId(data.order_id || null);
            setOrderComplete(true);
            goToSubStep("success");
          } else throw new Error("Sipariş tamamlanamadı");
        })
        .catch((err) => toast({ title: "Ödeme Hatası", description: err.message, variant: "destructive" }))
        .finally(() => setSubmittingOrder(false));
    } else if (paymentStatus === "failed" || paymentStatus === "error") {
      toast({ title: "Ödeme Başarısız", description: "Lütfen tekrar deneyin.", variant: "destructive" });
      goToSubStep("checkout");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [toast]);

  // ─── Data fetchers ────────────────────────────────────────────
  const fetchProducts = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/products`);
      if (res.ok) setProducts(await res.json());
    } catch (e) { console.error(e); }
  };
  const fetchScenarios = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/scenarios`);
      if (res.ok) setScenarios(await res.json());
    } catch (e) { console.error(e); }
  };
  const fetchLearningOutcomes = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/scenarios/learning-outcomes`);
      if (res.ok) setLearningOutcomes(await res.json());
    } catch (e) { console.error(e); }
  };
  const fetchVisualStyles = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/scenarios/visual-styles`);
      if (res.ok) {
        const data = await res.json();
        setVisualStyles(data);
        if (data.length > 0) setSelectedStyle(data[0].id);
      }
    } catch (e) { console.error(e); }
  };

  // ─── Handlers ─────────────────────────────────────────────────
  const calculateTotalPrice = useCallback((): number => {
    const product = products.find((p) => p.id === _selectedProduct);
    const scenario = scenarios.find((s) => s.id === selectedScenario);
    const basePrice = scenario?.price_override_base ?? product?.base_price ?? 0;
    let total = basePrice;
    if (hasAudioBook) total += audioType === "cloned" ? 300 : 150;
    if (hasColoringBook) total += coloringBookPrice;
    return total;
  }, [products, scenarios, _selectedProduct, selectedScenario, hasAudioBook, audioType, hasColoringBook, coloringBookPrice]);

  const handleAnalyzePhoto = async () => {
    if (!childPhoto) return;
    _setUploadingPhoto(true);
    try {
      const reader = new FileReader();
      const base64 = await new Promise<string>((resolve, reject) => {
        reader.onload = (e) => resolve(e.target?.result as string);
        reader.onerror = reject;
        reader.readAsDataURL(childPhoto);
      });
      const uploadResult = await uploadTempImage(base64.split(",")[1]);
      if (uploadResult.success && uploadResult.url) {
        setFaceDetected(true);
        toast({ title: "✅ Yüz Tespit Edildi", description: "Fotoğraf başarıyla analiz edildi." });
      } else {
        setFaceDetected(false);
        toast({ title: "⚠️ Yüz Tespit Edilemedi", description: "Lütfen daha net, yüzün göründüğü bir fotoğraf deneyin.", variant: "destructive" });
      }
    } catch {
      setFaceDetected(false);
      toast({ title: "Hata", description: "Fotoğraf yüklenirken bir sorun oluştu.", variant: "destructive" });
    } finally {
      _setUploadingPhoto(false);
    }
  };

  const handleMagicWand = async () => {
    setLoading(true);
    setPreviewLoading(true);
    try {
      // 1. Upload photo if present
      let childPhotoUrl: string | undefined;
      if (childPhoto) {
        const reader = new FileReader();
        const base64 = await new Promise<string>((resolve, reject) => {
          reader.onload = (e) => resolve(e.target?.result as string);
          reader.onerror = reject;
          reader.readAsDataURL(childPhoto);
        });
        const uploadResult = await uploadTempImage(base64.split(",")[1]);
        if (uploadResult.success && uploadResult.url) childPhotoUrl = uploadResult.url;
      }

      // 2. Build story payload with correct camelCase params
      const selectedStyleObj = visualStyles.find((s) => s.id === selectedStyle);
      const payload = buildStoryPayload({
        childName: childInfo.name,
        childAge: parseInt(childInfo.age, 10),
        childGender: childInfo.gender,
        childPhotoUrl,
        scenarioId: selectedScenario,
        learningOutcomeNames: [],
        visualStylePromptModifier: selectedStyleObj?.prompt_modifier || "",
        visualStyleId: selectedStyle || undefined,
        pageCount: scenarios.find((s) => s.id === selectedScenario)?.default_page_count ?? 10,
        clothingDescription: childInfo.clothingDescription || undefined,
        customVariables: Object.keys(customVariables).length > 0 ? customVariables : undefined,
      });

      // 3. Generate story text
      const storyData = await generateStoryV2(payload);
      if (!storyData.success || !storyData.story) {
        throw new Error(storyData.error || "Hikaye oluşturulamadı");
      }
      setStoryStructure({ title: storyData.story.title, pages: storyData.story.pages });

      // 4. Generate preview images
      const previewData = await generatePreviewImages({
        child_name: childInfo.name,
        child_age: parseInt(childInfo.age, 10),
        child_gender: childInfo.gender,
        child_photo_url: childPhotoUrl || null,
        story_title: storyData.story.title,
        story_pages: storyData.story.pages,
        scenario_id: selectedScenario,
        visual_style: selectedStyleObj?.prompt_modifier,
        id_weight: customIdWeight ?? selectedStyleObj?.id_weight,
        clothing_description: childInfo.clothingDescription || null,
        parent_name: childInfo.name ? `${childInfo.name}'ın Velisi` : "Misafir Kullanıcı",
        parent_email: "trial@benimmasalim.com",
      });
      if (previewData.trial_id) {
        setTrialId(previewData.trial_id);
        setTrialToken(previewData.trial_token || null);
        await pollPreviewStatus(previewData.trial_id, previewData.trial_token || undefined);
        goToSubStep("reveal");
      } else {
        throw new Error("Önizleme oluşturulamadı");
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Bilinmeyen hata";
      toast({ title: "Sihir Yarım Kaldı", description: message, variant: "destructive" });
    } finally {
      setLoading(false);
    }
  };

  const pollPreviewStatus = async (id: string, token?: string) => {
    const poll = async () => {
      try {
        const status = await getTrialStatus(id, token);
        if (status.generation_progress) setGenerationProgress(status.generation_progress);
        if (status.is_failed) { setPreviewLoading(false); return; }
        if (status.is_preview_ready) {
          const preview = await getTrialPreview(id, token);
          if (preview.success && preview.preview_images) setPreviewImages(preview.preview_images);
          setPreviewLoading(false);
          return;
        }
        setTimeout(poll, 3000);
      } catch { setPreviewLoading(false); }
    };
    await poll();
  };

  const handleVoiceSampleRecorded = async (audioBase64: string) => {
    setIsCloningVoice(true);
    try {
      const res = await fetch(`${API_BASE_URL}/ai/clone-voice-direct`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ voice_name: `${childInfo.name}_voice`, audio_base64: audioBase64 }),
      });
      if (res.ok) {
        const data = await res.json();
        setClonedVoiceId(data.voice_id);
      }
    } finally { setIsCloningVoice(false); }
  };

  const handleSubmitOrder = async (shInfo: ShippingInfo, _paymentInfo: PaymentInfo, promo?: string | null, coloring?: boolean) => {
    setSubmittingOrder(true);
    setParentInfo({ fullName: shInfo.fullName, email: shInfo.email, phone: shInfo.phone });
    setDedicationNote(shInfo.dedicationNote || "");
    const promoCode = promo || "";
    const hasColoring = coloring ?? false;
    try {
      if (!promoCode) {
        const pData = await createTrialPayment(_trialId!, _trialToken || undefined);
        if (pData.payment_url) {
          sessionStorage.setItem("pending_trial_id", _trialId!);
          sessionStorage.setItem("pending_trial_token", _trialToken || "");
          sessionStorage.setItem("pending_parent_name", shInfo.fullName);
          sessionStorage.setItem("pending_parent_email", shInfo.email);
          sessionStorage.setItem("pending_parent_phone", shInfo.phone || "");
          sessionStorage.setItem("pending_dedication_note", shInfo.dedicationNote || "");
          sessionStorage.setItem("pending_has_audio", String(hasAudioBook));
          sessionStorage.setItem("pending_audio_type", audioType);
          sessionStorage.setItem("pending_audio_voice_id", clonedVoiceId);
          sessionStorage.setItem("pending_has_coloring_book", String(hasColoring));
          window.location.href = pData.payment_url;
          return;
        }
      }
      const data = await completeTrial({
        trial_id: _trialId!,
        payment_reference: `promo:${promoCode}`,
        parent_name: shInfo.fullName,
        parent_email: shInfo.email,
        parent_phone: shInfo.phone,
        dedication_note: shInfo.dedicationNote || null,
        promo_code: promoCode,
        has_audio_book: hasAudioBook,
        audio_type: hasAudioBook ? audioType : null,
        audio_voice_id: clonedVoiceId || null,
        has_coloring_book: hasColoring,
      }, _trialToken || undefined);
      if (data.success) { setOrderComplete(true); goToSubStep("success"); }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Bilinmeyen hata";
      toast({ title: "Hata", description: message, variant: "destructive" });
    } finally { setSubmittingOrder(false); }
  };

  // ─── RENDER ───────────────────────────────────────────────────

  const selectedProductObj = products.find(p => p.id === _selectedProduct);
  const basePriceValue = scenarios.find(s => s.id === selectedScenario)?.price_override_base ?? selectedProductObj?.base_price ?? 0;
  const audioAddonPrice = audioType === "cloned" ? 300 : 150;

  return (
    <div className="create-flow relative min-h-screen w-full max-w-[100vw] overflow-x-hidden bg-[#fdf8ff] text-sm touch-manipulation font-outfit">

      {/* Background Decor */}
      <div className="fixed inset-0 pointer-events-none -z-10 overflow-hidden">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] rounded-full bg-purple-200/40 blur-[120px] animate-pulse" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] rounded-full bg-pink-200/40 blur-[120px] animate-pulse" style={{ animationDelay: '1s' }} />
      </div>

      <header className="sticky top-0 z-40 w-full px-4 py-3">
        <div className="mx-auto max-w-lg">
          <div className="rounded-2xl bg-white/70 shadow-sm border border-white/40 backdrop-blur-xl px-4 py-3">
            <StepIndicator
              steps={STEP_DEFS}
              currentStep={mainStep}
              maxReached={maxMainStep}
              onStepClick={(s) => {
                const subMap: Record<number, SubStep> = { 1: "hero", 2: "adventure", 3: "visuals", 4: "reveal", 5: "checkout", 6: "success" };
                if (subMap[s]) goToSubStep(subMap[s]);
              }}
            />
          </div>
        </div>
      </header>

      <main className="mx-auto w-full max-w-5xl px-4 py-2 pb-32">
        <div className="flex flex-col items-center">
          <div className="w-full max-w-2xl">
            <AnimatePresence mode="wait">
              {subStep === "hero" && (
                <motion.div key="sub-hero" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="pb-24">
                  <ChildInfoForm
                    childInfo={childInfo}
                    onUpdate={setChildInfo}
                    onContinue={() => goToSubStep(preselectedScenarioId ? "visuals" : "adventure")}
                    onBack={() => window.history.back()}
                    hideNavButtons
                    hideClothing
                  />
                  {/* Sticky CTA */}
                  <motion.div
                    initial={{ opacity: 0, y: 40 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="fixed bottom-0 left-0 right-0 z-50 bg-white/95 backdrop-blur-md border-t border-gray-100 px-4 py-3"
                  >
                    <div className="mx-auto flex max-w-lg gap-3">
                      <Button variant="ghost" onClick={() => window.history.back()} className="h-12 px-4">Geri</Button>
                      <Button
                        size="lg"
                        className="h-12 flex-1 rounded-xl bg-gradient-to-r from-purple-600 to-pink-500 font-bold shadow-lg shadow-purple-200"
                        onClick={() => goToSubStep(preselectedScenarioId ? "visuals" : "adventure")}
                        disabled={!childInfo.name || !childInfo.age || !childInfo.gender}
                      >
                        {childInfo.name ? `${childInfo.name}'ın Macerasını Seç ✨` : "Macerayı Başlat ✨"}
                      </Button>
                    </div>
                  </motion.div>
                </motion.div>
              )}

              {subStep === "adventure" && (
                <motion.div key="sub-adventure" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="pb-24">
                  <AdventureSelector
                    scenarios={scenarios}
                    selectedScenario={selectedScenario}
                    onSelect={setSelectedScenario}
                    onContinue={() => goToSubStep("visuals")}
                    onBack={() => goToSubStep("hero")}
                    childName={childInfo.name}
                  />
                  {(() => {
                    const sel = scenarios.find(s => s.id === selectedScenario);
                    if (sel?.custom_inputs_schema?.length) return (
                      <div className="mt-4 rounded-2xl border border-gray-200 bg-white p-4 shadow-sm">
                        <CustomInputsForm fields={sel.custom_inputs_schema as unknown as Array<{ key: string; label: string; type: "text" | "number" | "select" | "textarea"; required?: boolean; options?: string[] }>} values={customVariables} onChange={setCustomVariables} />
                      </div>
                    );
                  })()}
                </motion.div>
              )}

              {subStep === "visuals" && (
                <motion.div key="sub-visuals" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="pb-36">
                  <VisualsStep
                    childName={childInfo.name}
                    photoPreview={childPhotoPreview}
                    faceDetected={faceDetected}
                    isAnalyzing={_uploadingPhoto}
                    onPhotoSelect={(f: File) => {
                      setChildPhoto(f);
                      const r = new FileReader();
                      r.onload = (e) => setChildPhotoPreview(e.target?.result as string);
                      r.readAsDataURL(f);
                    }}
                    onClear={() => { setChildPhoto(null); setChildPhotoPreview(""); setFaceDetected(false); }}
                    onAnalyze={handleAnalyzePhoto}
                    visualStyles={visualStyles}
                    selectedStyle={selectedStyle}
                    customIdWeight={customIdWeight}
                    onStyleSelect={setSelectedStyle}
                    onIdWeightChange={setCustomIdWeight}
                    onBack={() => goToSubStep("adventure")}
                    onSubmit={handleMagicWand}
                    isSubmitting={loading}
                  />
                </motion.div>
              )}

              {subStep === "reveal" && (
                <motion.div key="sub-reveal" initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="pb-28">
                  {/* Image Preview */}
                  <ImagePreviewStep
                    childName={childInfo.name} previewImages={previewImages} backCoverImageUrl={previewImages["backcover"]}
                    onApprove={() => goToSubStep("checkout")} onBack={() => goToSubStep("visuals")}
                    isLoading={previewLoading} generationProgress={generationProgress}
                  />

                  {/* ── Ek Seçenekler: Ses + Boyama ── */}
                  <div className="mt-6 space-y-4">
                    {/* Ses Tercihi */}
                    <div className="rounded-3xl overflow-hidden border border-purple-100 shadow-lg bg-gradient-to-br from-purple-50 via-white to-pink-50">
                      <AudioSelectionStep
                        childName={childInfo.name} basePrice={calculateTotalPrice()} selectedOption={hasAudioBook ? audioType : "none"}
                        systemVoice={systemVoice} clonedVoiceId={clonedVoiceId} isCloningVoice={isCloningVoice}
                        onOptionChange={(o) => { if (o === "none") setHasAudioBook(false); else { setHasAudioBook(true); setAudioType(o); } }}
                        onSystemVoiceChange={setSystemVoice} onVoiceRecorded={handleVoiceSampleRecorded}
                        onContinue={() => { }} onBack={() => { }} isTestMode={false} isSubmitting={false} hideNavButtons
                      />
                    </div>

                    {/* Boyama Kitabı Kartı */}
                    <motion.div
                      initial={{ opacity: 0, y: 16 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.15 }}
                      className="rounded-3xl overflow-hidden border border-emerald-200 shadow-lg bg-gradient-to-br from-emerald-50 via-white to-teal-50"
                    >
                      <div className="p-5">
                        <div className="flex items-center gap-3 mb-3">
                          <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-gradient-to-br from-emerald-400 to-teal-500 shadow-md">
                            <span className="text-xl">🎨</span>
                          </div>
                          <div className="flex-1 min-w-0">
                            <h3 className="text-base font-bold text-gray-800">Boyama Kitabı</h3>
                            <p className="text-xs text-gray-500">Bu hikayedeki sahneleri boyasın!</p>
                          </div>
                          {coloringBookPrice > 0 && (
                            <div className="text-right">
                              <span className="text-lg font-bold text-emerald-600">+{coloringBookPrice} ₺</span>
                            </div>
                          )}
                        </div>

                        <div className="flex items-center gap-3 mb-3">
                          <div className="flex-1 grid grid-cols-2 gap-2 text-xs text-gray-500">
                            <span className="flex items-center gap-1">✅ Hikayeden türetilir</span>
                            <span className="flex items-center gap-1">✅ Line-art çizimler</span>
                            <span className="flex items-center gap-1">✅ Ayrı fiziksel kitap</span>
                            <span className="flex items-center gap-1">✅ Yaratıcılık aktivitesi</span>
                          </div>
                        </div>

                        <button
                          type="button"
                          onClick={() => setHasColoringBook(!hasColoringBook)}
                          className={`w-full py-3 rounded-2xl font-bold text-sm transition-all duration-300 ${hasColoringBook
                            ? "bg-emerald-500 text-white shadow-lg shadow-emerald-200"
                            : "bg-white border-2 border-emerald-300 text-emerald-700 hover:bg-emerald-50"
                            }`}
                        >
                          {hasColoringBook ? "✓ Boyama Kitabı Eklendi" : `Boyama Kitabı Ekle · ${coloringBookPrice} ₺`}
                        </button>
                      </div>
                    </motion.div>
                  </div>

                  {/* ── Sticky Bottom: Ödemeye Geç ── */}
                  <div className="fixed bottom-0 left-0 right-0 z-50 bg-white/95 backdrop-blur-md border-t border-gray-100 px-4 py-3">
                    <div className="mx-auto flex max-w-lg gap-3">
                      <button
                        type="button"
                        onClick={() => goToSubStep("visuals")}
                        className="h-12 px-5 rounded-2xl border-2 border-gray-200 text-gray-600 font-semibold text-sm"
                      >
                        ← Geri
                      </button>
                      <motion.button
                        type="button"
                        whileTap={{ scale: 0.98 }}
                        onClick={() => goToSubStep("checkout")}
                        className="h-12 flex-1 rounded-2xl bg-gradient-to-r from-green-500 to-emerald-600 text-white font-bold text-base shadow-lg shadow-green-200 flex items-center justify-center gap-2"
                      >
                        Ödemeye Geç ➔
                      </motion.button>
                    </div>
                  </div>
                </motion.div>
              )}


              {subStep === "checkout" && (
                <div className="w-full max-w-4xl">
                  <CheckoutStep
                    childName={childInfo.name} storyTitle={storyStructure?.title || "Büyülü Hikaye"}
                    coverImageUrl={Object.values(previewImages)[0]} basePrice={basePriceValue} audioPrice={audioAddonPrice}
                    hasAudioBook={hasAudioBook} audioType={audioType} productName={selectedProductObj?.name || "Kitap"}
                    coloringBookPrice={coloringBookPrice} onBack={() => goToSubStep("reveal")}
                    onComplete={handleSubmitOrder} isProcessing={submittingOrder}
                  />
                </div>
              )}

              {subStep === "success" && (
                <motion.div key="sub-success" initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} className="text-center p-12 bg-white/80 backdrop-blur-xl rounded-3xl shadow-2xl">
                  <div className="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-full bg-green-100 text-green-600"><PartyPopper className="h-10 w-10" /></div>
                  <h2 className="text-3xl font-bold mb-4">Sipariş Alındı!</h2>
                  <p className="text-gray-600 mb-8">Hayaller gerçek oluyor. Hazırlanma aşamasını mailinden takip edebilirsin.</p>
                  <Button onClick={() => window.location.href = "/"} size="lg" className="w-full h-14 bg-gray-900 rounded-2xl font-bold">Harika!</Button>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </main>

      {(subStep === "reveal" || subStep === "checkout") && (
        <div className="fixed bottom-0 left-0 right-0 z-50 lg:static lg:mt-6">
          <OrderSummaryPanel
            storyTitle={storyStructure?.title} childName={childInfo.name} basePrice={basePriceValue}
            hasAudioBook={hasAudioBook} audioPrice={audioAddonPrice} hasColoringBook={hasColoringBook}
            coloringBookPrice={coloringBookPrice} productName={selectedProductObj?.name}
            coverImageUrl={selectedProductObj?.thumbnail_url} currentStep={mainStep}
          />
        </div>
      )}

      <div className="fixed bottom-4 left-4 p-3 bg-white/40 backdrop-blur-md rounded-full border border-white/40 shadow-sm hidden md:flex items-center gap-2 group transition-all hover:bg-white/60">
        <Info className="h-4 w-4 text-purple-500" />
        <span className="text-xs font-medium text-gray-600 opacity-0 group-hover:opacity-100 whitespace-nowrap">Yardım</span>
      </div>
    </div>
  );
}

export default function CreatePage() {
  return (
    <Suspense fallback={<div className="flex h-screen items-center justify-center"><div className="h-10 w-10 animate-spin rounded-full border-4 border-purple-500 border-t-transparent" /></div>}>
      <CreatePageInner />
    </Suspense>
  );
}
