"use client";

import { useState, useEffect, useCallback, useRef, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { useToast } from "@/hooks/use-toast";

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
  BillingDataPayload,
} from "@/lib/api";

import { useOrderDraft } from "./_hooks/useOrderDraft";
import type { BillingFormData } from "./_hooks/useOrderDraft";
import { usePromoValidation } from "./_hooks/usePromoValidation";
import { calculatePricing } from "./_lib/pricing";

import WizardShell from "./_components/WizardShell";
import HeroAndAdventureStep from "./_components/steps/HeroAndAdventureStep";
import VisualsAndPhotoStep from "./_components/steps/VisualsAndPhotoStep";
import PreviewStep from "./_components/steps/PreviewStep";
import ExtrasAndShippingStep from "./_components/steps/ExtrasAndShippingStep";
import PaymentStep from "./_components/steps/PaymentStep";
import SuccessScreen from "./_components/SuccessScreen";
import OrderSummaryCard from "./_components/OrderSummaryCard";

/* ── Local types ── */

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

function toBillingPayload(b: BillingFormData): BillingDataPayload {
  return {
    billing_type: b.billingType,
    billing_tc_no: b.billingType === "individual" ? (b.tcNo?.trim() || null) : null,
    billing_full_name: b.fullName || null,
    billing_email: b.email || null,
    billing_phone: b.phone || null,
    billing_company_name: b.billingType === "corporate" ? (b.companyName || null) : null,
    billing_tax_id: b.billingType === "corporate" ? (b.taxId || null) : null,
    billing_tax_office: b.billingType === "corporate" ? (b.taxOffice || null) : null,
    billing_address: !b.useShippingAddress ? { address: b.address, city: b.city, district: b.district, postalCode: b.postalCode } : null,
    use_shipping_address: b.useShippingAddress,
  };
}

/* ── Main Component ── */

function CreatePageInner() {
  const searchParams = useSearchParams();
  const preselectedScenarioId = searchParams.get("scenario") ?? "";
  const { toast } = useToast();
  const _paymentCallbackHandled = useRef(false);

  /* ── Draft state (persisted to sessionStorage) ── */
  const {
    draft,
    setField,
    setShippingField,
    setBillingField,
    goToStep,
    merge,
  } = useOrderDraft(preselectedScenarioId);

  /* ── Reference data (fetched once) ── */
  const [products, setProducts] = useState<Product[]>([]);
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [visualStyles, setVisualStyles] = useState<VisualStyle[]>([]);
  const [coloringBookPrice, setColoringBookPrice] = useState<number>(0);

  /* ── Photo (File cannot be serialized) ── */
  const [childPhoto, setChildPhoto] = useState<File | null>(null);
  const [uploadingPhoto, setUploadingPhoto] = useState(false);

  /* ── Generation/loading state ── */
  const [generating, setGenerating] = useState(false);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewError, setPreviewError] = useState<string | null>(null);
  const [submittingOrder, setSubmittingOrder] = useState(false);
  const [completedOrderId, setCompletedOrderId] = useState<string | null>(null);

  /* ── Lead / Contact ── */
  const [leadUserId, setLeadUserId] = useState<string | null>(null);
  const [contactInfo, setContactInfo] = useState<{
    firstName: string;
    lastName: string;
    phone: string;
    email: string;
    userId: string;
  } | null>(null);

  /* ── Promo ── */
  const promo = usePromoValidation();

  /* ── Derived values ── */
  const selectedProductObj = products.find(p => p.slug === "a4-yatay") ?? products[0];
  const selectedScenarioObj = scenarios.find(s => s.id === draft.scenarioId);

  const basePriceValue: number =
    selectedProductObj?.base_price
      ? Number(selectedProductObj.base_price)
      : 1250;

  const breakdown = calculatePricing({
    basePrice: basePriceValue,
    hasAudioBook: draft.hasAudioBook,
    audioType: draft.audioType,
    hasColoringBook: draft.hasColoringBook,
    coloringBookPrice,
    discountAmount: promo.result?.valid ? (promo.result.discount_amount ?? 0) : 0,
    promoCode: promo.result?.valid ? (promo.result.promo_summary?.code ?? draft.promoCode) : null,
  });

  const isFreeOrder = promo.result?.valid === true && (promo.result.final_amount ?? breakdown.total) <= 0;

  /* ── Init: Fetch reference data + session ── */
  useEffect(() => {
    const init = async () => {
      try {
        const userJson = localStorage.getItem("user");
        if (userJson) {
          const user = JSON.parse(userJson);
          if (user.id) setLeadUserId(user.id);
          if (user.full_name || user.email) {
            setContactInfo({
              firstName: user.full_name?.split(" ")[0] || "",
              lastName: user.full_name?.split(" ").slice(1).join(" ") || "",
              phone: user.phone || "",
              email: user.email || "",
              userId: user.id || "",
            });
          }
        } else {
          const storedUserId = localStorage.getItem("lead_user_id");
          if (storedUserId) {
            try {
              const res = await fetch(`${API_BASE_URL}/leads/${storedUserId}`, {
                headers: { "X-User-Id": storedUserId },
              });
              if (res.ok) {
                const data = await res.json();
                setLeadUserId(data.user_id);
                setContactInfo({
                  firstName: data.first_name,
                  lastName: data.last_name,
                  phone: data.phone,
                  email: data.email,
                  userId: data.user_id,
                });
              } else localStorage.removeItem("lead_user_id");
            } catch { localStorage.removeItem("lead_user_id"); }
          }
        }
      } catch { /* ignore */ }
    };

    const fetchAll = async () => {
      const [prodRes, scenRes, styleRes, colorRes] = await Promise.allSettled([
        fetch(`${API_BASE_URL}/products`).then(r => r.ok ? r.json() : []),
        fetch(`${API_BASE_URL}/scenarios`).then(r => r.ok ? r.json() : []),
        fetch(`${API_BASE_URL}/scenarios/visual-styles`).then(r => r.ok ? r.json() : []),
        fetch(`${API_BASE_URL}/coloring-books/active`).then(r => r.ok ? r.json() : null),
      ]);

      if (prodRes.status === "fulfilled") setProducts(prodRes.value);
      if (scenRes.status === "fulfilled") setScenarios(scenRes.value);
      if (styleRes.status === "fulfilled") {
        setVisualStyles(styleRes.value);
        if (styleRes.value.length > 0 && !draft.selectedStyle) {
          setField("selectedStyle", styleRes.value[0].id);
        }
      }
      if (colorRes.status === "fulfilled" && colorRes.value) {
        setColoringBookPrice(colorRes.value.discounted_price || colorRes.value.base_price);
      }
    };

    init();
    fetchAll();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  /* ── Iyzico Callback ── */
  useEffect(() => {
    if (typeof window === "undefined") return;
    const sp = new URLSearchParams(window.location.search);
    const paymentStatus = sp.get("payment");
    const iyzicoToken = sp.get("token");
    const callbackTrialId = sp.get("trialId");

    if (!paymentStatus || _paymentCallbackHandled.current) return;
    _paymentCallbackHandled.current = true;

    if (paymentStatus === "success" && callbackTrialId && iyzicoToken) {
      const storedTrialToken = sessionStorage.getItem("pending_trial_token") || sp.get("tt") || undefined;
      const storedName = sessionStorage.getItem("pending_parent_name") || "";
      const storedEmail = sessionStorage.getItem("pending_parent_email") || "";
      const storedPhone = sessionStorage.getItem("pending_parent_phone") || "";
      const storedDedication = sessionStorage.getItem("pending_dedication_note") || "";
      const storedHasAudio = sessionStorage.getItem("pending_has_audio") === "true";
      const storedAudioType = (sessionStorage.getItem("pending_audio_type") || "system") as "system" | "cloned";
      const storedVoiceId = sessionStorage.getItem("pending_audio_voice_id") || "";
      const storedHasColoringBook = sessionStorage.getItem("pending_has_coloring_book") === "true";
      const storedPromoCode = sessionStorage.getItem("pending_promo_code") || undefined;

      let storedBilling: BillingDataPayload | null = null;
      try {
        const raw = sessionStorage.getItem("pending_billing");
        if (raw) storedBilling = toBillingPayload(JSON.parse(raw) as BillingFormData);
      } catch { /* ignore */ }

      setSubmittingOrder(true);
      verifyTrialPayment(callbackTrialId, iyzicoToken, storedTrialToken)
        .then(async (verifyResult) => {
          if (!verifyResult.success || !verifyResult.payment_reference) {
            throw new Error(verifyResult.error || "Ödeme doğrulanamadı");
          }
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
            promo_code: storedPromoCode,
            billing: storedBilling,
          }, storedTrialToken);

          if (data.success) {
            const pendingKeys = [
              "pending_trial_id", "pending_trial_token", "pending_parent_name",
              "pending_parent_email", "pending_parent_phone", "pending_dedication_note",
              "pending_has_audio", "pending_audio_type", "pending_audio_voice_id",
              "pending_has_coloring_book", "pending_promo_code", "pending_billing",
            ];
            pendingKeys.forEach(k => sessionStorage.removeItem(k));
            setCompletedOrderId(data.order_id || null);
            goToStep(6);
          } else {
            throw new Error("Sipariş tamamlanamadı");
          }
        })
        .catch((err) => {
          toast({ title: "Ödeme Hatası", description: err.message, variant: "destructive" });
          goToStep(5);
        })
        .finally(() => setSubmittingOrder(false));
    } else if (paymentStatus === "failed" || paymentStatus === "error") {
      toast({ title: "Ödeme Başarısız", description: "Lütfen tekrar deneyin.", variant: "destructive" });
      goToStep(5);
    }
  }, [toast, goToStep]);

  /* ── Helpers ── */

  /** Canvas-based image compression. Resizes to maxPx and re-encodes as JPEG.
   *  Returns raw base64 string (no data: prefix). Keeps phones' large photos under limit. */
  const compressImageToBase64 = useCallback(
    (file: File, maxPx = 1600, quality = 0.85): Promise<string> =>
      new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onerror = reject;
        reader.onload = (e) => {
          const img = new Image();
          img.onerror = reject;
          img.onload = () => {
            const scale = Math.min(1, maxPx / Math.max(img.width, img.height));
            const w = Math.round(img.width * scale);
            const h = Math.round(img.height * scale);
            const canvas = document.createElement("canvas");
            canvas.width = w;
            canvas.height = h;
            canvas.getContext("2d")!.drawImage(img, 0, 0, w, h);
            const dataUrl = canvas.toDataURL("image/jpeg", quality);
            resolve(dataUrl.split(",")[1]);
          };
          img.src = e.target?.result as string;
        };
        reader.readAsDataURL(file);
      }),
    []
  );

  /* ── Handlers ── */

  const handleAnalyzePhoto = useCallback(async () => {
    if (!childPhoto) return;
    setUploadingPhoto(true);
    try {
      const base64 = await compressImageToBase64(childPhoto);
      const result = await uploadTempImage(base64);
      if (result.success && result.url) {
        setField("faceDetected", true);
        toast({ title: "Yüz Tespit Edildi", description: "Fotoğraf başarıyla analiz edildi." });
      } else {
        setField("faceDetected", false);
        toast({ title: "Yüz Tespit Edilemedi", description: "Lütfen daha net, yüzün göründüğü bir fotoğraf deneyin.", variant: "destructive" });
      }
    } catch {
      setField("faceDetected", false);
      toast({ title: "Hata", description: "Fotoğraf yüklenirken bir sorun oluştu.", variant: "destructive" });
    } finally {
      setUploadingPhoto(false);
    }
  }, [childPhoto, compressImageToBase64, setField, toast]);

  const handleGeneratePreview = useCallback(async () => {
    if (childPhoto && !draft.faceDetected) {
      toast({ title: "Önce Fotoğrafı Analiz Et", description: "Lütfen fotoğrafı analiz ettirin.", variant: "destructive" });
      return;
    }

    setGenerating(true);
    setPreviewLoading(true);
    setPreviewError(null);

    try {
      let childPhotoUrl: string | undefined;
      if (childPhoto) {
        const base64 = await compressImageToBase64(childPhoto);
        const uploadResult = await uploadTempImage(base64);
        if (uploadResult.success && uploadResult.url) childPhotoUrl = uploadResult.url;
      }

      const selectedStyleObj = visualStyles.find(s => s.id === draft.selectedStyle);
      const payload = buildStoryPayload({
        childName: draft.childName,
        childAge: parseInt(draft.childAge, 10),
        childGender: draft.childGender,
        childPhotoUrl,
        scenarioId: draft.scenarioId,
        learningOutcomeNames: [],
        visualStylePromptModifier: selectedStyleObj?.prompt_modifier || "",
        visualStyleId: draft.selectedStyle || undefined,
        pageCount: selectedScenarioObj?.default_page_count ?? 10,
        customVariables: Object.keys(draft.customVariables).length > 0 ? draft.customVariables : undefined,
      });

      const storyData = await generateStoryV2(payload);
      if (!storyData.success || !storyData.story) {
        throw new Error(storyData.error || "Hikaye oluşturulamadı");
      }

      merge({
        storyTitle: storyData.story.title,
        storyPages: storyData.story.pages,
      });

      const bookProduct = selectedProductObj;
      const bookPrice: number = bookProduct?.base_price ? Number(bookProduct.base_price) : 1250;

      const previewData = await generatePreviewImages({
        child_name: draft.childName,
        child_age: parseInt(draft.childAge, 10),
        child_gender: draft.childGender,
        child_photo_url: childPhotoUrl || null,
        story_title: storyData.story.title,
        story_pages: storyData.story.pages,
        scenario_id: draft.scenarioId,
        visual_style: selectedStyleObj?.prompt_modifier,
        visual_style_name: selectedStyleObj?.display_name || selectedStyleObj?.name,
        id_weight: draft.customIdWeight ?? selectedStyleObj?.id_weight,
        parent_name: contactInfo?.firstName ? `${contactInfo.firstName} ${contactInfo.lastName}`.trim() : (draft.childName ? `${draft.childName}'ın Velisi` : "Misafir Kullanıcı"),
        parent_email: contactInfo?.email || "trial@benimmasalim.com",
        user_id: leadUserId || undefined,
        product_id: bookProduct?.id || null,
        product_name: bookProduct?.name || "A4 YATAY 32 sayfa",
        product_price: bookPrice,
        scenario_name: selectedScenarioObj?.name,
      });

      if (previewData.trial_id) {
        merge({
          trialId: previewData.trial_id,
          trialToken: previewData.trial_token || "",
        });
        sessionStorage.setItem("current_trial_id", previewData.trial_id);
        if (previewData.trial_token) sessionStorage.setItem("current_trial_token", previewData.trial_token);

        await pollPreviewStatus(previewData.trial_id, previewData.trial_token || undefined);
        goToStep(3);
      } else {
        throw new Error("Önizleme oluşturulamadı");
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Bilinmeyen hata";
      setPreviewError(message);
      toast({ title: "Sihir Yarım Kaldı", description: message, variant: "destructive" });
    } finally {
      setGenerating(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [childPhoto, compressImageToBase64, draft, visualStyles, selectedScenarioObj, selectedProductObj, contactInfo, leadUserId, merge, goToStep, toast]);

  const pollPreviewStatus = useCallback(async (id: string, token?: string) => {
    const POLL_MS = 6000; // Match POLLING_INTERVAL_MS from constants
    const poll = async () => {
      try {
        const status = await getTrialStatus(id, token);
        if (status.generation_progress) {
          setField("generationProgress", status.generation_progress);
        }
        if (status.is_failed) {
          setPreviewLoading(false);
          setPreviewError("Önizleme oluşturulamadı. Lütfen tekrar deneyin.");
          return;
        }
        if (status.is_preview_ready) {
          const preview = await getTrialPreview(id, token);
          if (preview.success && preview.preview_images) {
            setField("previewImages", preview.preview_images);
          }
          setPreviewLoading(false);
          return;
        }
        setTimeout(poll, POLL_MS);
      } catch {
        setPreviewLoading(false);
        setPreviewError("Bağlantı hatası. Lütfen tekrar deneyin.");
      }
    };
    await poll();
  }, [setField]);

  const handleSubmitOrder = useCallback(async () => {
    setSubmittingOrder(true);
    const sh = draft.shipping;
    const promoCode = draft.promoCode.trim();
    const billingPayload = toBillingPayload(draft.billing);

    sessionStorage.setItem("pending_billing", JSON.stringify(draft.billing));

    if (!draft.trialId) {
      toast({ title: "Hata", description: "Önce hikayenizi oluşturun.", variant: "destructive" });
      setSubmittingOrder(false);
      return;
    }

    try {
      if (isFreeOrder && promoCode) {
        const data = await completeTrial({
          trial_id: draft.trialId,
          payment_reference: `promo:${promoCode}`,
          parent_name: sh.fullName,
          parent_email: sh.email,
          parent_phone: sh.phone,
          dedication_note: draft.dedicationNote || null,
          promo_code: promoCode,
          has_audio_book: draft.hasAudioBook,
          audio_type: draft.hasAudioBook ? draft.audioType : null,
          audio_voice_id: draft.clonedVoiceId || null,
          has_coloring_book: draft.hasColoringBook,
          billing: billingPayload,
        }, draft.trialToken || undefined);

        if (data.success) {
          setCompletedOrderId(data.order_id || null);
          goToStep(6);
        } else throw new Error("Sipariş tamamlanamadı.");
      } else {
        sessionStorage.setItem("pending_trial_id", draft.trialId);
        sessionStorage.setItem("pending_trial_token", draft.trialToken || "");
        sessionStorage.setItem("pending_parent_name", sh.fullName);
        sessionStorage.setItem("pending_parent_email", sh.email);
        sessionStorage.setItem("pending_parent_phone", sh.phone || "");
        sessionStorage.setItem("pending_dedication_note", draft.dedicationNote || "");
        sessionStorage.setItem("pending_has_audio", String(draft.hasAudioBook));
        sessionStorage.setItem("pending_audio_type", draft.audioType);
        sessionStorage.setItem("pending_audio_voice_id", draft.clonedVoiceId);
        sessionStorage.setItem("pending_has_coloring_book", String(draft.hasColoringBook));
        if (promoCode) sessionStorage.setItem("pending_promo_code", promoCode);
        else sessionStorage.removeItem("pending_promo_code");

        const pData = await createTrialPayment(
          draft.trialId,
          draft.trialToken || undefined,
          promoCode || null,
          billingPayload,
        );

        if (!pData.payment_url) {
          throw new Error("Ödeme sayfası oluşturulamadı. Lütfen tekrar deneyin.");
        }
        window.location.href = pData.payment_url;
        return;
      }
    } catch (err: unknown) {
      const isRateLimit = err instanceof Error && (
        err.message.includes("Çok fazla istek") ||
        (err as { status?: number }).status === 429
      );
      if (isRateLimit) {
        toast({ title: "Çok Fazla İstek", description: "Biraz bekleyip tekrar deneyin.", variant: "destructive" });
      } else {
        const message = err instanceof Error ? err.message : "Bilinmeyen hata";
        toast({ title: "Hata", description: message, variant: "destructive" });
      }
    } finally {
      setSubmittingOrder(false);
    }
  }, [draft, isFreeOrder, goToStep, toast]);

  const handlePromoApply = useCallback(async (code: string) => {
    setField("promoCode", code);
    await promo.validate(code, breakdown.subtotal);
  }, [setField, promo, breakdown.subtotal]);

  const handlePromoClear = useCallback(() => {
    setField("promoCode", "");
    promo.clear();
  }, [setField, promo]);

  /* ── Step navigation ── */
  const handleStepClick = useCallback((step: number) => {
    if (step <= draft.maxReachedStep) goToStep(step);
  }, [draft.maxReachedStep, goToStep]);

  /* ── Step content ── */
  const isSuccess = draft.currentStep === 6;

  // Sipariş tamamlandığında sessionStorage draft'ını temizle
  // Böylece kullanıcı tekrar /create-v2'ye gelince yeni sipariş oluşturabilir
  useEffect(() => {
    if (isSuccess) {
      sessionStorage.removeItem("orderDraft_v2");
    }
  }, [isSuccess]);

  const renderStep = () => {
    if (isSuccess) {
      return <SuccessScreen orderId={completedOrderId} />;
    }

    switch (draft.currentStep) {
      case 1:
        return (
          <HeroAndAdventureStep
            childName={draft.childName}
            childAge={draft.childAge}
            childGender={draft.childGender}
            scenarioId={draft.scenarioId}
            customVariables={draft.customVariables}
            scenarios={scenarios}
            onChildNameChange={(v) => setField("childName", v)}
            onChildAgeChange={(v) => setField("childAge", v)}
            onChildGenderChange={(v) => setField("childGender", v)}
            onScenarioSelect={(v) => setField("scenarioId", v)}
            onCustomVariablesChange={(v) => setField("customVariables", v)}
            onContinue={() => goToStep(2)}
            onBack={() => window.history.back()}
            preselectedScenarioId={preselectedScenarioId}
          />
        );

      case 2:
        return (
          <VisualsAndPhotoStep
            childName={draft.childName}
            photoPreview={draft.photoPreview}
            faceDetected={draft.faceDetected}
            isAnalyzing={uploadingPhoto}
            onPhotoSelect={(f: File) => {
              setChildPhoto(f);
              const r = new FileReader();
              r.onload = (e) => setField("photoPreview", e.target?.result as string);
              r.readAsDataURL(f);
            }}
            onClear={() => {
              setChildPhoto(null);
              merge({ photoPreview: "", faceDetected: false });
            }}
            onAnalyze={handleAnalyzePhoto}
            visualStyles={visualStyles}
            selectedStyle={draft.selectedStyle}
            customIdWeight={draft.customIdWeight}
            onStyleSelect={(v) => setField("selectedStyle", v)}
            onIdWeightChange={(v) => setField("customIdWeight", v)}
            onBack={() => goToStep(1)}
            onSubmit={handleGeneratePreview}
            isSubmitting={generating}
          />
        );

      case 3:
        return (
          <PreviewStep
            childName={draft.childName}
            previewImages={draft.previewImages ?? {}}
            backCoverImageUrl={(draft.previewImages ?? {})["backcover"]}
            isLoading={previewLoading}
            generationProgress={draft.generationProgress}
            errorMessage={previewError}
            onApprove={() => goToStep(4)}
            onBack={() => goToStep(2)}
            onRetry={handleGeneratePreview}
          />
        );

      case 4:
        return (
          <ExtrasAndShippingStep
            childName={draft.childName}
            hasAudioBook={draft.hasAudioBook}
            audioType={draft.audioType}
            clonedVoiceId={draft.clonedVoiceId}
            hasColoringBook={draft.hasColoringBook}
            coloringBookPrice={coloringBookPrice}
            dedicationNote={draft.dedicationNote}
            shipping={draft.shipping}
            onAudioChange={(has, type) => merge({ hasAudioBook: has, audioType: type })}
            onColoringBookChange={(has) => setField("hasColoringBook", has)}
            onDedicationChange={(v) => setField("dedicationNote", v)}
            onShippingFieldChange={setShippingField}
            onContinue={() => goToStep(5)}
            onBack={() => goToStep(3)}
          />
        );

      case 5:
        return (
          <PaymentStep
            childName={draft.childName}
            storyTitle={draft.storyTitle || "Büyülü Hikaye"}
            productName={selectedProductObj?.name || "Kitap"}
            breakdown={breakdown}
            billing={draft.billing}
            promoCode={draft.promoCode}
            promoResult={promo.result}
            promoLoading={promo.loading}
            onBillingFieldChange={setBillingField}
            onPromoApply={handlePromoApply}
            onPromoClear={handlePromoClear}
            onSubmit={handleSubmitOrder}
            onBack={() => goToStep(4)}
            isProcessing={submittingOrder}
            isFreeOrder={isFreeOrder}
          />
        );

      default:
        return null;
    }
  };

  if (isSuccess) {
    return (
      <WizardShell
        currentStep={5}
        maxReached={5}
        onStepClick={() => { }}
      >
        <SuccessScreen orderId={completedOrderId} />
      </WizardShell>
    );
  }

  return (
    <WizardShell
      currentStep={draft.currentStep}
      maxReached={draft.maxReachedStep}
      onStepClick={handleStepClick}
      showSidebar={draft.currentStep >= 4}
      sidebar={
        draft.currentStep >= 4 ? (
          <OrderSummaryCard
            childName={draft.childName}
            storyTitle={draft.storyTitle}
            productName={selectedProductObj?.name}
            breakdown={breakdown}
          />
        ) : undefined
      }
    >
      {renderStep()}
    </WizardShell>
  );
}

export default function CreatePage() {
  return (
    <Suspense
      fallback={
        <div className="flex h-screen items-center justify-center bg-[#fdf8ff]">
          <div className="h-10 w-10 animate-spin rounded-full border-4 border-purple-500 border-t-transparent" />
        </div>
      }
    >
      <CreatePageInner />
    </Suspense>
  );
}
