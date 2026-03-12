"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { ShieldCheck, Lock, CreditCard, Globe } from "lucide-react";
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
  childName: _childName,
  storyTitle: _storyTitle,
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

  const tcNoValid = billing.tcNo
    ? validateTcNo(billing.tcNo).valid
    : !isCorporate;
  const canSubmit = termsAccepted && corporateValid && tcNoValid;

  return (
    <div className="pb-24 space-y-5">
      {/* ── Header ── */}
      <header>
        <p className="text-[10px] sm:text-xs font-bold text-violet-500 uppercase tracking-wider mb-0.5">
          Adım 5
        </p>
        <h2 className="text-lg sm:text-xl font-bold text-slate-800">
          Güvenli Ödeme
        </h2>
        <p className="text-xs sm:text-sm text-slate-500 mt-1">
          Ödemeniz küresel ödeme altyapısı Iyzico tarafından güvenle işlenir.
        </p>
      </header>

      {/* ── Iyzico Trust Banner ── */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        className="rounded-2xl border border-blue-100 bg-gradient-to-r from-blue-50 to-indigo-50 p-4"
      >
        <div className="flex items-start gap-3">
          <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-xl bg-blue-100 text-blue-600">
            <Globe className="h-5 w-5" />
          </div>
          <div>
            <p className="text-sm font-bold text-blue-900 mb-1">
              🔒 Kart bilgileriniz tamamen güvende
            </p>
            <p className="text-xs text-blue-700 leading-relaxed">
              Ödemeniz <strong>Iyzico</strong> küresel ödeme altyapısı ile işlenir.
              Kart bilgileriniz Benim Masalım sunucularına <strong>hiçbir şekilde iletilmez</strong>.
              Tüm veriler PCI DSS sertifikalı, 256-bit SSL şifreleme ile korunur.
            </p>
          </div>
        </div>
        {/* Payment logos */}
        <div className="flex items-center gap-3 mt-3 ml-13">
          <div className="flex items-center gap-1.5 text-[10px] text-slate-500">
            <CreditCard className="h-3.5 w-3.5" /> Visa
          </div>
          <div className="flex items-center gap-1.5 text-[10px] text-slate-500">
            <CreditCard className="h-3.5 w-3.5" /> Mastercard
          </div>
          <div className="flex items-center gap-1.5 text-[10px] text-slate-500">
            <ShieldCheck className="h-3.5 w-3.5" /> PCI DSS
          </div>
          <div className="flex items-center gap-1.5 text-[10px] text-slate-500">
            <Lock className="h-3.5 w-3.5" /> SSL
          </div>
        </div>
      </motion.div>

      {/* ── Order Summary Card ── */}
      <section className="rounded-2xl border border-slate-100 bg-white shadow-sm overflow-hidden">
        <div className="px-4 pt-3.5 pb-2.5 border-b border-slate-50">
          <span className="text-sm font-semibold text-slate-700">Sipariş Özeti</span>
        </div>
        <div className="p-4 space-y-2">
          {/* Base price */}
          <div className="flex justify-between text-sm">
            <span className="text-slate-600">{productName || "Kitap"}</span>
            <span className="font-semibold text-slate-800">{formatPrice(breakdown.basePrice)} ₺</span>
          </div>
          {/* Audio */}
          {breakdown.audioPrice > 0 && (
            <div className="flex justify-between text-sm">
              <span className="text-slate-600">Sesli Kitap</span>
              <span className="font-semibold text-slate-800">+{formatPrice(breakdown.audioPrice)} ₺</span>
            </div>
          )}
          {/* Coloring book */}
          {breakdown.coloringBookPrice > 0 && (
            <div className="flex justify-between text-sm">
              <span className="text-slate-600">Boyama Kitabı</span>
              <span className="font-semibold text-slate-800">+{formatPrice(breakdown.coloringBookPrice)} ₺</span>
            </div>
          )}
          {/* Discount */}
          {breakdown.discount > 0 && (
            <div className="flex justify-between text-sm text-emerald-600">
              <span>İndirim {breakdown.promoCode && `(${breakdown.promoCode})`}</span>
              <span className="font-semibold">-{formatPrice(breakdown.discount)} ₺</span>
            </div>
          )}
          {/* Divider */}
          <div className="border-t border-slate-100 pt-2 mt-1 flex items-center justify-between">
            <span className="text-sm font-bold text-slate-800">Toplam</span>
            <span className="text-lg font-black text-violet-700">
              {formatPrice(breakdown.total)} ₺
            </span>
          </div>
        </div>
      </section>

      {/* ── Billing Form ── */}
      <section className="rounded-2xl border border-slate-100 bg-white shadow-sm overflow-hidden">
        <div className="px-4 pt-3.5 pb-2.5 border-b border-slate-50">
          <span className="text-sm font-semibold text-slate-700">Fatura Bilgileri</span>
        </div>
        <div className="p-4 space-y-4">
          {/* Billing type toggle */}
          <div className="grid grid-cols-2 gap-2">
            {(["individual", "corporate"] as const).map((type) => (
              <button
                key={type}
                type="button"
                onClick={() => onBillingFieldChange("billingType", type)}
                className={`
                  py-2.5 rounded-xl border-2 text-sm font-semibold transition-all
                  ${billing.billingType === type
                    ? "border-violet-500 bg-violet-50 text-violet-700"
                    : "border-slate-200 bg-white text-slate-600 hover:border-slate-300"
                  }
                `}
              >
                {type === "individual" ? "Bireysel" : "Kurumsal"}
              </button>
            ))}
          </div>

          {/* Corporate fields */}
          {isCorporate && (
            <div className="space-y-3 rounded-xl border border-slate-100 bg-slate-50/50 p-4">
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

          {/* TC No */}
          {!isCorporate && (
            <div className="rounded-xl border border-slate-100 bg-slate-50/50 p-4">
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
              <p className="mt-1.5 text-[11px] text-slate-400">
                Fatura isterseniz TC kimlik numaranızı girin. Boş bırakabilirsiniz.
              </p>
            </div>
          )}

          {/* Billing address */}
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={billing.useShippingAddress}
              onChange={(e) => onBillingFieldChange("useShippingAddress", e.target.checked)}
              className="h-4 w-4 rounded border-slate-300 text-violet-600 focus:ring-violet-500"
            />
            <span className="text-sm text-slate-600">Fatura adresi teslimat adresiyle aynı</span>
          </label>

          {!billing.useShippingAddress && (
            <div className="space-y-3 rounded-xl border border-slate-100 bg-slate-50/50 p-4">
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
        </div>
      </section>

      {/* ── Promo Code ── */}
      <section className="rounded-2xl border border-slate-100 bg-white shadow-sm p-4">
        <PromoCodeInput
          onApply={onPromoApply}
          onClear={onPromoClear}
          loading={promoLoading}
          appliedCode={promoResult?.valid ? (promoResult.promo_summary?.code || promoCode) : null}
          discountAmount={promoResult?.discount_amount || 0}
          error={promoResult && !promoResult.valid ? (promoResult.reason || "Geçersiz kupon") : null}
        />
      </section>

      {/* ── Terms ── */}
      <div className="space-y-3">
        <label className="flex items-start gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={termsAccepted}
            onChange={(e) => setTermsAccepted(e.target.checked)}
            className="mt-0.5 h-4 w-4 rounded border-slate-300 text-violet-600 focus:ring-violet-500"
          />
          <span className="text-xs text-slate-600 leading-relaxed">
            <a href="/terms" target="_blank" className="text-violet-600 underline">Kullanım koşullarını</a> ve{" "}
            <a href="/distance-sales" target="_blank" className="text-violet-600 underline">mesafeli satış sözleşmesini</a> okudum, kabul ediyorum.
          </span>
        </label>

        <TrustBadges variant="grid" />
      </div>

      <StickyCTA
        primaryLabel={
          isProcessing
            ? "İşleniyor..."
            : isFreeOrder
              ? "Siparişi Tamamla 🎉"
              : `🔒 Güvenle Öde · ${formatPrice(breakdown.total)} ₺`
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
