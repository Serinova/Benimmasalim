"use client";

import { useReducer, useEffect, useCallback, useRef } from "react";
import { SESSION_KEY } from "../_lib/constants";
import type { GenerationProgress } from "@/lib/api";

/* ── Shipping / Billing sub-types ── */

export interface ShippingInfo {
  fullName: string;
  email: string;
  phone: string;
  address: string;
  city: string;
  district: string;
  postalCode: string;
  dedicationNote: string;
}

export interface BillingFormData {
  billingType: "individual" | "corporate";
  tcNo: string;  // TCKN — bireysel fatura için
  fullName: string;
  email: string;
  phone: string;
  companyName: string;
  taxId: string;
  taxOffice: string;
  useShippingAddress: boolean;
  address: string;
  city: string;
  district: string;
  postalCode: string;
}

export interface PromoResult {
  valid: boolean;
  discount_amount?: number;
  final_amount?: number;
  promo_summary?: {
    code: string;
    discount_type: string;
    discount_value: number;
    max_discount_amount?: number;
  };
  reason?: string;
}

/* ── Main draft state ── */

export interface OrderDraft {
  childName: string;
  childAge: string;
  childGender: string;
  scenarioId: string;
  customVariables: Record<string, string>;

  photoPreview: string;
  faceDetected: boolean;
  selectedStyle: string;
  kvkkConsent: boolean;
  customIdWeight: number | null;

  trialId: string;
  trialToken: string;
  previewImages: Record<string, string>;
  storyTitle: string;
  storyPages: Array<{ page_number: number; text: string; visual_prompt: string }>;
  generationProgress: GenerationProgress | null;

  hasAudioBook: boolean;
  audioType: "system" | "cloned";
  clonedVoiceId: string;
  hasColoringBook: boolean;
  dedicationNote: string;
  shipping: ShippingInfo;
  promoCode: string;
  promoResult: PromoResult | null;

  billing: BillingFormData;

  currentStep: number;
  maxReachedStep: number;
}

const EMPTY_SHIPPING: ShippingInfo = {
  fullName: "",
  email: "",
  phone: "",
  address: "",
  city: "",
  district: "",
  postalCode: "",
  dedicationNote: "",
};

const EMPTY_BILLING: BillingFormData = {
  billingType: "individual",
  tcNo: "",
  fullName: "",
  email: "",
  phone: "",
  companyName: "",
  taxId: "",
  taxOffice: "",
  useShippingAddress: true,
  address: "",
  city: "",
  district: "",
  postalCode: "",
};

export const INITIAL_DRAFT: OrderDraft = {
  childName: "",
  childAge: "",
  childGender: "erkek",
  scenarioId: "",
  customVariables: {},

  photoPreview: "",
  faceDetected: false,
  selectedStyle: "",
  kvkkConsent: false,
  customIdWeight: null,

  trialId: "",
  trialToken: "",
  previewImages: {},
  storyTitle: "",
  storyPages: [],
  generationProgress: null,

  hasAudioBook: false,
  audioType: "system",
  clonedVoiceId: "",
  hasColoringBook: false,
  dedicationNote: "",
  shipping: { ...EMPTY_SHIPPING },
  promoCode: "",
  promoResult: null,

  billing: { ...EMPTY_BILLING },

  currentStep: 1,
  maxReachedStep: 1,
};

/* ── Actions ── */

export type DraftAction =
  | { type: "SET_FIELD"; field: keyof OrderDraft; value: unknown }
  | { type: "SET_SHIPPING_FIELD"; field: keyof ShippingInfo; value: string }
  | { type: "SET_BILLING_FIELD"; field: keyof BillingFormData; value: unknown }
  | { type: "MERGE"; patch: Partial<OrderDraft> }
  | { type: "GO_TO_STEP"; step: number }
  | { type: "RESET" }
  | { type: "RESTORE"; draft: OrderDraft };

function draftReducer(state: OrderDraft, action: DraftAction): OrderDraft {
  switch (action.type) {
    case "SET_FIELD":
      return { ...state, [action.field]: action.value };
    case "SET_SHIPPING_FIELD":
      return {
        ...state,
        shipping: { ...state.shipping, [action.field]: action.value },
      };
    case "SET_BILLING_FIELD":
      return {
        ...state,
        billing: { ...state.billing, [action.field]: action.value },
      };
    case "MERGE":
      return { ...state, ...action.patch };
    case "GO_TO_STEP":
      return {
        ...state,
        currentStep: action.step,
        maxReachedStep: Math.max(state.maxReachedStep, action.step),
      };
    case "RESET":
      return { ...INITIAL_DRAFT };
    case "RESTORE":
      return action.draft;
    default:
      return state;
  }
}

/* ── Serialization helpers ── */

const SKIP_PERSIST_KEYS: (keyof OrderDraft)[] = [
  "generationProgress",
];

function serializeForStorage(state: OrderDraft): string {
  const cleaned: Record<string, unknown> = {};
  for (const [key, value] of Object.entries(state)) {
    if (SKIP_PERSIST_KEYS.includes(key as keyof OrderDraft)) continue;
    cleaned[key] = value;
  }
  return JSON.stringify(cleaned);
}

function restoreFromStorage(): OrderDraft | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = sessionStorage.getItem(SESSION_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    return { ...INITIAL_DRAFT, ...parsed };
  } catch {
    return null;
  }
}

/* ── Hook ── */

export function useOrderDraft(preselectedScenarioId?: string) {
  const initialized = useRef(false);

  const [draft, dispatch] = useReducer(draftReducer, INITIAL_DRAFT, () => {
    const restored = restoreFromStorage();
    if (restored) return restored;
    const initial = { ...INITIAL_DRAFT };
    if (preselectedScenarioId) initial.scenarioId = preselectedScenarioId;
    return initial;
  });

  useEffect(() => {
    if (!initialized.current) {
      initialized.current = true;
      return;
    }
    try {
      sessionStorage.setItem(SESSION_KEY, serializeForStorage(draft));
    } catch { /* quota exceeded — ignore */ }
  }, [draft]);

  const setField = useCallback(
    <K extends keyof OrderDraft>(field: K, value: OrderDraft[K]) => {
      dispatch({ type: "SET_FIELD", field, value: value as unknown });
    },
    [],
  );

  const setShippingField = useCallback(
    (field: keyof ShippingInfo, value: string) => {
      dispatch({ type: "SET_SHIPPING_FIELD", field, value });
    },
    [],
  );

  const setBillingField = useCallback(
    <K extends keyof BillingFormData>(field: K, value: BillingFormData[K]) => {
      dispatch({ type: "SET_BILLING_FIELD", field, value: value as unknown });
    },
    [],
  );

  const goToStep = useCallback((step: number) => {
    dispatch({ type: "GO_TO_STEP", step });
  }, []);

  const merge = useCallback((patch: Partial<OrderDraft>) => {
    dispatch({ type: "MERGE", patch });
  }, []);

  const reset = useCallback(() => {
    dispatch({ type: "RESET" });
    if (typeof window !== "undefined") sessionStorage.removeItem(SESSION_KEY);
  }, []);

  return {
    draft,
    dispatch,
    setField,
    setShippingField,
    setBillingField,
    goToStep,
    merge,
    reset,
  };
}
