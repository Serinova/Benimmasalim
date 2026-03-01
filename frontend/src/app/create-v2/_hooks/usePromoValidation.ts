"use client";

import { useState, useCallback, useRef } from "react";
import { API_BASE_URL } from "@/lib/api";
import type { PromoResult } from "./useOrderDraft";

export function usePromoValidation() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<PromoResult | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const validate = useCallback(async (code: string, subtotal: number) => {
    const trimmed = code.trim().toUpperCase();
    if (!trimmed) {
      setResult(null);
      return null;
    }

    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/payments/validate-promo`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code: trimmed, subtotal }),
        signal: controller.signal,
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        const r: PromoResult = {
          valid: false,
          reason: errData.detail || "Kupon kodu geçersiz",
        };
        setResult(r);
        return r;
      }

      const data = await res.json();
      const r: PromoResult = {
        valid: data.valid,
        discount_amount: data.discount_amount,
        final_amount: data.final_amount,
        promo_summary: data.promo_summary,
        reason: data.reason,
      };
      setResult(r);
      return r;
    } catch (err) {
      if ((err as Error).name === "AbortError") return null;
      const r: PromoResult = {
        valid: false,
        reason: "Bağlantı hatası, tekrar deneyin",
      };
      setResult(r);
      return r;
    } finally {
      setLoading(false);
    }
  }, []);

  const clear = useCallback(() => {
    abortRef.current?.abort();
    setResult(null);
  }, []);

  return { validate, clear, loading, result };
}
