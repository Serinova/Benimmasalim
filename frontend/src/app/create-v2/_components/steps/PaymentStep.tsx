"use client";

import { useState } from "react";
import { CreditCard } from "lucide-react";
import FormField from "../ui/FormField";
import TrustBadges from "../ui/TrustBadges";
import StickyCTA from "../StickyCTA";
import PromoCodeInput from "../ui/PromoCodeInput";
import type { BillingFormData, PromoResult } from "../../_hooks/useOrderDraft";
import type { PriceBreakdown } from "../../_lib/pricing";
import { validateTaxId, validateCompanyName, validateTcNo } from "../../_lib/validations";
import { formatPrice } from "../../_lib/pricing";

interface PaymentStepProps {
  childName: string;
  storyTitle: string;
  productName: string;
  breakdown: PriceBreakdown;
  billing: BillingFormData;
  promoCode: string;
  promoResult: PromoResult | null;
  promoLoading: boolean;
  onBillingFieldChange: <K extends keyof BillingFormData>(field: K, value: BillingFormData[K]) => void;
  onPromoApply: (code: string) => Promise<void>;
  onPromoClear: () => void;
  onSubmit: () => void;
  onBack: () => void;
  isProcessing: boolean;
  isFreeOrder: boolean;
}

export default function PaymentStep({
  childName,
  storyTitle,
  productName,
  breakdown,
  billing,
  promoCode,
  promoResult,
  promoLoading,
  onBillingFieldChange,
  onPromoApply,
  onPromoClear,
  onSubmit,
  onBack,
  isProcessing,
  isFreeOrder,
}: PaymentStepProps) {
  const [touched, setTouched] = useState<Record<string, boolean>>({});
  const [termsAccepted, setTermsAccepted] = useState(false);

  const touch = (field: string) =>
    setTouched((prev) => ({ ...prev, [field]: true }));

  const isCorporate = billing.billingType === "corporate";

  const corporateValid = !isCorporate || (
    validateCompanyName(billing.companyName).valid &&
    validateTaxId(billing.taxId).valid
  );

  // TC No is optional for individuals — empty string is valid
  const tcNoValid = billing.tcNo
    ? validateTcNo(billing.tcNo).valid
    : !isCorporate; // empty is OK for individuals
  const canSubmit = termsAccepted && corporateValid && tcNoValid;

  return (
    <div className="pb-24">
      <div className="mb-5">
        <p className="text-[10px] sm:text-xs font-semibold text-purple-500 uppercase tracking-wider mb-0.5">
          Adım 5
        </p>
        <h2 className="text-lg sm:text-xl font-bold text-gray-800">
          Ödeme
        </h2>
      </div>

      <div className="flex flex-col lg:flex-row lg:gap-6">
        {/* Left: Billing form */}
        <div className="flex-1 space-y-5">
          {/* Billing type toggle */}
          <div>
            <label className="block text-[13px] font-semibold text-gray-600 mb-2">
              Fatura Tipi
            </label>
            <div className="grid grid-cols-2 gap-2">
              {(["individual", "corporate"] as const).map((type) => (
                <button
                  key={type}
                  type="button"
                  onClick={() => onBillingFieldChange("billingType", type)}
                  className={`
                    py-2.5 rounded-xl border-2 text-sm font-semibold transition-all
                    ${billing.billingType === type
                      ? "border-purple-500 bg-purple-50 text-purple-700"
                      : "border-gray-200 bg-white text-gray-600 hover:border-gray-300"}
                  `}
                >
                  {type === "individual" ? "Bireysel" : "Kurumsal"}
                </button>
              ))}
            </div>
          </div>

          {/* Corporate fields */}
          {isCorporate && (
            <div className="space-y-3 rounded-xl border border-gray-100 bg-gray-50/50 p-4">
              <FormField
                label="Şirket Ünvanı"
                value={billing.companyName}
                onChange={(e) => onBillingFieldChange("companyName", e.target.value)}
                onBlur={() => touch("companyName")}
                placeholder="Şirket Ünvanı"
                error={touched.companyName ? validateCompanyName(billing.companyName) : null}
                touched={!!touched.companyName}
              />
              <div className="grid grid-cols-2 gap-3">
                <FormField
                  label="Vergi Numarası"
                  value={billing.taxId}
                  onChange={(e) => onBillingFieldChange("taxId", e.target.value.replace(/\D/g, ""))}
                  onBlur={() => touch("taxId")}
                  placeholder="10-11 haneli"
                  maxLength={11}
                  error={touched.taxId ? validateTaxId(billing.taxId) : null}
                  touched={!!touched.taxId}
                />
                <FormField
                  label="Vergi Dairesi"
                  value={billing.taxOffice}
                  onChange={(e) => onBillingFieldChange("taxOffice", e.target.value)}
                  placeholder="Vergi Dairesi"
                />
              </div>
            </div>
          )}

          {/* Individual: TC no */}
          {!isCorporate && (
            <div className="rounded-xl border border-gray-100 bg-gray-50/50 p-4">
              <FormField
                label="T.C. Kimlik No (Fatura için, opsiyonel)"
                value={billing.tcNo}
                onChange={(e) => onBillingFieldChange("tcNo", e.target.value.replace(/\D/g, "").slice(0, 11))}
                onBlur={() => touch("tcNo")}
                placeholder="11 haneli TC kimlik numaranız"
                maxLength={11}
                error={touched.tcNo && billing.tcNo ? validateTcNo(billing.tcNo) : null}
                touched={!!touched.tcNo}
              />
              <p className="mt-1.5 text-[11px] text-gray-400">
                Fatura isterseniz TC kimlik numaranızı girin. Boş bırakabilirsiniz.
              </p>
            </div>
          )}

          {/* Billing address toggle */}
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={billing.useShippingAddress}
              onChange={(e) => onBillingFieldChange("useShippingAddress", e.target.checked)}
              className="h-4 w-4 rounded border-gray-300 text-purple-600 focus:ring-purple-500"
            />
            <span className="text-sm text-gray-600">Fatura adresi teslimat adresiyle aynı</span>
          </label>

          {!billing.useShippingAddress && (
            <div className="space-y-3 rounded-xl border border-gray-100 bg-gray-50/50 p-4">
              <FormField
                label="Fatura Adresi"
                value={billing.address}
                onChange={(e) => onBillingFieldChange("address", e.target.value)}
                placeholder="Fatura adresi"
              />
              <div className="grid grid-cols-2 gap-3">
                <FormField
                  label="Şehir"
                  value={billing.city}
                  onChange={(e) => onBillingFieldChange("city", e.target.value)}
                  placeholder="Şehir"
                />
                <FormField
                  label="Posta Kodu"
                  value={billing.postalCode}
                  onChange={(e) => onBillingFieldChange("postalCode", e.target.value)}
                  placeholder="Posta kodu"
                />
              </div>
            </div>
          )}

          {/* Terms */}
          <div className="space-y-2">
            <label className="flex items-start gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={termsAccepted}
                onChange={(e) => setTermsAccepted(e.target.checked)}
                className="mt-0.5 h-4 w-4 rounded border-gray-300 text-purple-600 focus:ring-purple-500"
              />
              <span className="text-xs text-gray-600 leading-relaxed">
                <a href="/terms" target="_blank" className="text-purple-600 underline">Kullanım koşullarını</a> ve{" "}
                <a href="/distance-sales" target="_blank" className="text-purple-600 underline">mesafeli satış sözleşmesini</a> okudum, kabul ediyorum.
              </span>
            </label>
          </div>
          {/* Promo code */}
          <PromoCodeInput
            onApply={onPromoApply}
            onClear={onPromoClear}
            loading={promoLoading}
            appliedCode={promoResult?.valid ? (promoResult.promo_summary?.code || promoCode) : null}
            discountAmount={promoResult?.discount_amount || 0}
            error={promoResult && !promoResult.valid ? (promoResult.reason || "Geçersiz kupon") : null}
          />

          <TrustBadges />
        </div>
      </div>

      <StickyCTA
        primaryLabel={
          isProcessing
            ? "İşleniyor..."
            : isFreeOrder
              ? "Siparişi Tamamla"
              : `Güvenli Ödemeye Geç (${formatPrice(breakdown.total)} ₺)`
        }
        onPrimary={onSubmit}
        primaryDisabled={!canSubmit}
        primaryLoading={isProcessing}
        secondaryLabel="← Geri"
        onSecondary={onBack}
      />
    </div>
  );
}
