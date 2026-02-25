"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  CreditCard,
  Truck,
  Shield,
  Lock,
  Check,
  ChevronLeft,
  ChevronRight,
  Package,
  Calendar,
  Clock,
  Heart,
  FileText,
  MapPin,
  Phone,
  User,
  Mail,
  Building,
  Rocket,
  Ticket,
  X,
  Loader2,
} from "lucide-react";
import Image from "next/image";
import { Button } from "@/components/ui/button";
import { API_BASE_URL } from "@/lib/api";

interface CheckoutStepProps {
  childName: string;
  storyTitle: string;
  coverImageUrl: string | null;
  basePrice: number;
  audioPrice: number;
  hasAudioBook: boolean;
  audioType: "system" | "cloned";
  productName: string;
  initialShipping?: { fullName: string; email: string; phone: string };
  onComplete: (shippingInfo: ShippingInfo, paymentInfo: PaymentInfo, promoCode?: string | null) => void;
  onBack: () => void;
  isProcessing?: boolean;
  orderId?: string; // Order ID for promo code apply
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

interface PromoResult {
  valid: boolean;
  reason?: string;
  discount_amount?: number;
  subtotal_amount?: number;
  final_amount?: number;
  promo_summary?: {
    code: string;
    discount_type: string;
    discount_value: number;
    max_discount_amount: number | null;
  };
}

type CheckoutStage = "shipping" | "payment" | "success";

// Trust Badge Component
function TrustBadge({ icon: Icon, text }: { icon: React.ElementType; text: string }) {
  return (
    <div className="flex items-center gap-2 text-sm text-gray-500">
      <Icon className="h-4 w-4" />
      <span>{text}</span>
    </div>
  );
}

// Success Celebration Component
function SuccessCelebration({
  childName,
  storyTitle,
  onNewOrder,
}: {
  childName: string;
  storyTitle: string;
  onNewOrder: () => void;
}) {
  const particles = 80;
  const colors = ["#ef4444", "#f97316", "#eab308", "#22c55e", "#3b82f6", "#8b5cf6", "#ec4899"];

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="fixed inset-0 z-50 flex items-center justify-center"
      style={{
        background: "linear-gradient(135deg, #1e1b4b 0%, #312e81 50%, #3730a3 100%)",
      }}
    >
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        {[...Array(particles)].map((_, i) => (
          <motion.div
            key={i}
            initial={{ x: "50%", y: "-10%", rotate: 0, scale: 0 }}
            animate={{
              x: `${Math.random() * 100}%`,
              y: "110%",
              rotate: Math.random() * 720 - 360,
              scale: [0, 1, 1, 0.5],
            }}
            transition={{
              duration: 3 + Math.random() * 2,
              delay: Math.random() * 0.5,
              ease: "easeOut",
            }}
            className="absolute h-3 w-3"
            style={{
              backgroundColor: colors[i % colors.length],
              borderRadius: Math.random() > 0.5 ? "50%" : "0",
            }}
          />
        ))}
      </div>

      <motion.div
        initial={{ scale: 0.8, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ delay: 0.3, type: "spring" }}
        className="relative z-10 max-w-lg px-6 text-center"
      >
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ delay: 0.5, type: "spring", stiffness: 200 }}
          className="mx-auto mb-8 flex h-24 w-24 items-center justify-center rounded-full bg-gradient-to-br from-green-400 to-emerald-500 shadow-2xl shadow-green-500/30"
        >
          <Check className="h-12 w-12 text-white" strokeWidth={3} />
        </motion.div>

        <motion.div initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.7 }}>
          <h1 className="mb-4 text-4xl font-bold text-white">Tebrikler! 🎉</h1>
          <p className="mb-2 text-xl text-purple-200">Siparişiniz başarıyla oluşturuldu</p>
          <p className="text-purple-300">
            &ldquo;{storyTitle}&rdquo; kitabı {childName} için hazırlanıyor
          </p>
        </motion.div>

        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.9 }}
          className="mt-8 rounded-2xl bg-white/10 p-6 text-left backdrop-blur"
        >
          <div className="mb-4 flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-green-500/20">
              <Truck className="h-5 w-5 text-green-400" />
            </div>
            <div>
              <p className="font-medium text-white">Tahmini Teslimat</p>
              <p className="text-sm text-green-400">3-5 iş günü içinde kapınızda</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-purple-500/20">
              <Mail className="h-5 w-5 text-purple-400" />
            </div>
            <div>
              <p className="font-medium text-white">Sipariş Detayları</p>
              <p className="text-sm text-purple-300">E-posta adresinize gönderildi</p>
            </div>
          </div>
        </motion.div>

        <motion.button
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 1.1 }}
          onClick={onNewOrder}
          className="mt-8 rounded-xl bg-white px-8 py-4 font-semibold text-purple-700 transition-colors hover:bg-purple-50"
        >
          Yeni Hikaye Oluştur
        </motion.button>
      </motion.div>
    </motion.div>
  );
}

// Clean Input Component
function CleanInput({
  id,
  label,
  type = "text",
  value,
  onChange,
  onFocus: externalOnFocus,
  onBlur: externalOnBlur,
  icon: Icon,
  placeholder,
  required,
  maxLength,
}: {
  id: string;
  label: string;
  type?: string;
  value: string;
  onChange: (value: string) => void;
  onFocus?: () => void;
  onBlur?: () => void;
  icon?: React.ElementType;
  placeholder?: string;
  required?: boolean;
  maxLength?: number;
}) {
  const [isFocused, setIsFocused] = useState(false);

  const handleFocus = () => {
    setIsFocused(true);
    externalOnFocus?.();
  };

  const handleBlur = () => {
    setIsFocused(false);
    externalOnBlur?.();
  };

  return (
    <div className="space-y-1.5">
      <label htmlFor={id} className="block text-sm font-medium text-gray-700">
        {label}
        {required && <span className="ml-0.5 text-red-500">*</span>}
      </label>
      <div
        className={`
        relative rounded-xl border-2 bg-white transition-all duration-200
        ${isFocused ? "border-purple-500 shadow-md shadow-purple-500/10" : "border-gray-200"}
      `}
      >
        {Icon && (
          <div className="absolute left-3.5 top-1/2 z-10 -translate-y-1/2">
            <Icon
              className={`h-5 w-5 transition-colors ${isFocused ? "text-purple-500" : "text-gray-400"}`}
            />
          </div>
        )}
        <input
          id={id}
          type={type}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onFocus={handleFocus}
          onBlur={handleBlur}
          placeholder={placeholder || label}
          maxLength={maxLength}
          className={`
            w-full bg-transparent py-3 text-gray-800 outline-none placeholder:text-gray-400
            ${Icon ? "pl-11 pr-4" : "px-4"}
          `}
          required={required}
        />
      </div>
    </div>
  );
}

export default function CheckoutStep({
  childName,
  storyTitle,
  coverImageUrl,
  basePrice,
  audioPrice,
  hasAudioBook,
  audioType,
  productName,
  initialShipping,
  onComplete,
  onBack,
  isProcessing = false,
  orderId: _orderId,
}: CheckoutStepProps) {
  const [stage, setStage] = useState<CheckoutStage>("shipping");
  const [cartTimer, setCartTimer] = useState(15 * 60);

  // Shipping form state — pre-fill from contactInfo if available
  const [shipping, setShipping] = useState<ShippingInfo>({
    fullName: initialShipping?.fullName || "",
    email: initialShipping?.email || "",
    phone: initialShipping?.phone || "",
    address: "",
    city: "",
    district: "",
    postalCode: "",
    dedicationNote: "",
  });

  // Payment form state (setPayment reserved for future controlled inputs)
  const [payment, _setPayment] = useState<PaymentInfo>({
    cardNumber: "",
    cardName: "",
    expiryDate: "",
    cvv: "",
    installments: 1,
  });

  // Legal acknowledgment state
  const [termsAccepted, setTermsAccepted] = useState(false);

  // Promo code state
  const [promoInput, setPromoInput] = useState("");
  const [promoResult, setPromoResult] = useState<PromoResult | null>(null);
  const [promoLoading, setPromoLoading] = useState(false);
  const [appliedPromo, setAppliedPromo] = useState<PromoResult | null>(null);

  // Cart timer countdown
  useEffect(() => {
    const timer = setInterval(() => {
      setCartTimer((prev) => Math.max(0, prev - 1));
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const formatTimer = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  // Calculate totals (with promo)
  const shippingCost = 0;
  const rawTotal = basePrice + (hasAudioBook ? audioPrice : 0) + shippingCost;
  const discountAmount = appliedPromo?.valid ? (appliedPromo.discount_amount ?? 0) : 0;
  const totalPrice = Math.max(rawTotal - discountAmount, 0);
  const isFreeOrder = totalPrice === 0 && appliedPromo?.valid;

  // Estimated delivery date
  const getEstimatedDelivery = () => {
    const date = new Date();
    let daysAdded = 0;
    while (daysAdded < 3) {
      date.setDate(date.getDate() + 1);
      const dayOfWeek = date.getDay();
      if (dayOfWeek !== 0 && dayOfWeek !== 6) {
        daysAdded++;
      }
    }
    return date.toLocaleDateString("tr-TR", {
      weekday: "long",
      day: "numeric",
      month: "long",
    });
  };

  // Validate shipping
  const isShippingValid =
    shipping.fullName.length > 2 &&
    shipping.email.includes("@") &&
    shipping.phone.length >= 10 &&
    shipping.address.length > 5 &&
    shipping.city.length > 1;

  // Handle form submission — card data is collected on iyzico side (PCI compliant)
  const handleSubmit = () => {
    const promoCodeToSend = appliedPromo?.valid ? appliedPromo.promo_summary?.code ?? null : null;
    onComplete(shipping, payment, promoCodeToSend);
  };

  // ─── Promo Code API ───────────────────────────────────────────

  const _getAuthHeaders = () => {
    const token = localStorage.getItem("token");
    return {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    };
  };

  const handleApplyPromo = async () => {
    if (!promoInput.trim()) return;

    setPromoLoading(true);
    setPromoResult(null);

    try {
      const response = await fetch(`${API_BASE_URL}/payments/validate-promo`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          code: promoInput.trim().toUpperCase(),
          subtotal: rawTotal,
        }),
      });

      if (response.ok) {
        const data: PromoResult = await response.json();
        setPromoResult(data);
        if (data.valid) {
          setAppliedPromo(data);
        }
      } else {
        const err = await response.json().catch(() => null);
        setPromoResult({
          valid: false,
          reason: err?.detail || "Kupon kodu doğrulanamadı",
        });
      }
    } catch {
      setPromoResult({ valid: false, reason: "Bağlantı hatası" });
    } finally {
      setPromoLoading(false);
    }
  };

  const handleRemovePromo = () => {
    setAppliedPromo(null);
    setPromoResult(null);
    setPromoInput("");
  };

  // Show success screen
  if (stage === "success") {
    return (
      <SuccessCelebration
        childName={childName}
        storyTitle={storyTitle}
        onNewOrder={() => setStage("shipping")}
      />
    );
  }

  return (
    <div className="bg-gray-50">
      <div className="mx-auto max-w-6xl px-3 py-4">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-4 text-center"
        >
          <h1 className="mb-1 text-2xl font-bold text-gray-800">Siparişi Tamamla</h1>
          <p className="text-sm text-gray-500">
            {childName} için özel hazırlanan kitabınız neredeyse hazır!
          </p>
        </motion.div>

        {/* Progress Steps */}
        <div className="mb-4 flex items-center justify-center gap-3">
          {(isFreeOrder ? ["Teslimat"] : ["Teslimat", "Ödeme"]).map((step, idx) => (
            <div key={step} className="flex items-center">
              <div
                className={`
                flex h-8 w-8 items-center justify-center rounded-full text-sm font-medium transition-all
                ${
                  (idx === 0 && stage === "shipping") || (idx === 1 && stage === "payment")
                    ? "bg-purple-600 text-white"
                    : idx === 0 && stage === "payment"
                      ? "bg-green-500 text-white"
                      : "bg-gray-200 text-gray-500"
                }
              `}
              >
                {idx === 0 && stage === "payment" ? <Check className="h-4 w-4" /> : idx + 1}
              </div>
              <span
                className={`ml-2 text-sm ${
                  (idx === 0 && stage === "shipping") || (idx === 1 && stage === "payment")
                    ? "font-medium text-purple-600"
                    : "text-gray-500"
                }`}
              >
                {step}
              </span>
              {idx < (isFreeOrder ? 0 : 1) && <ChevronRight className="mx-4 h-5 w-5 text-gray-300" />}
            </div>
          ))}
        </div>

        {/* Main Content */}
        <div className="grid gap-5 lg:grid-cols-5">
          {/* Left Column - Form */}
          <div className="lg:col-span-3">
            <AnimatePresence mode="wait">
              {/* Shipping Form */}
              {stage === "shipping" && (
                <motion.div
                  key="shipping"
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 20 }}
                  className="space-y-4"
                >
                  {/* Dedication Note — prominent section at top */}
                  <div className="rounded-xl border-2 border-amber-200 bg-gradient-to-br from-amber-50 to-orange-50 p-4 shadow-sm">
                    <div className="mb-3 flex items-center gap-2">
                      <div className="flex h-8 w-8 items-center justify-center rounded-full bg-amber-100">
                        <Heart className="h-4 w-4 text-amber-600" />
                      </div>
                      <div>
                        <h2 className="text-base font-semibold text-amber-900">Karşılama Sayfası Notu</h2>
                        <p className="text-sm text-amber-700">
                          Kapaktan sonraki özel sayfada görünecek mesaj
                        </p>
                      </div>
                    </div>

                    {/* Default message info */}
                    <div className="mb-3 rounded-lg border border-amber-200 bg-white/60 p-3">
                      <p className="text-xs font-medium text-amber-600 mb-1">Hikayeye özel mesaj:</p>
                      <p className="text-sm text-amber-800">
                        Boş bırakırsanız, hikayeye uygun kişiselleştirilmiş bir karşılama metni otomatik kullanılır.
                      </p>
                    </div>

                    <textarea
                      id="dedicationNote"
                      value={shipping.dedicationNote || ""}
                      onChange={(e) =>
                        setShipping({ ...shipping, dedicationNote: e.target.value })
                      }
                      placeholder={`Kendi notunuzu yazmak isterseniz buraya yazın... Örn: "Sevgili ${childName}, bu macera senin için!"`}
                      maxLength={300}
                      rows={3}
                      className="w-full resize-none rounded-lg border border-amber-300 bg-white px-4 py-3 text-sm text-gray-800 placeholder:text-amber-400 focus:border-amber-500 focus:outline-none focus:ring-2 focus:ring-amber-400/30"
                    />
                    <div className="mt-2 flex items-center justify-between">
                      <p className="text-xs text-amber-600">
                        Boş bırakırsanız hikayeye özel mesaj kullanılır.
                      </p>
                      <p className="text-xs text-amber-500">
                        {(shipping.dedicationNote || "").length}/300
                      </p>
                    </div>
                  </div>

                  {/* Shipping Form */}
                  <div className="rounded-xl bg-white p-4 shadow-sm">
                  <div className="mb-4 flex items-center gap-2">
                    <div className="flex h-8 w-8 items-center justify-center rounded-full bg-purple-100">
                      <Truck className="h-4 w-4 text-purple-600" />
                    </div>
                    <div>
                      <h2 className="text-base font-semibold text-gray-800">Teslimat Adresi</h2>
                      <p className="text-xs text-gray-500">Kitabınızı nereye gönderelim?</p>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <div className="grid gap-4 md:grid-cols-2">
                      <CleanInput
                        id="fullName"
                        label="Ad Soyad"
                        value={shipping.fullName}
                        onChange={(v) => setShipping({ ...shipping, fullName: v })}
                        icon={User}
                        required
                      />
                      <CleanInput
                        id="phone"
                        label="Telefon"
                        type="tel"
                        value={shipping.phone}
                        onChange={(v) => setShipping({ ...shipping, phone: v })}
                        icon={Phone}
                        placeholder="05XX XXX XX XX"
                        required
                      />
                    </div>

                    <CleanInput
                      id="email"
                      label="E-posta"
                      type="email"
                      value={shipping.email}
                      onChange={(v) => setShipping({ ...shipping, email: v })}
                      icon={Mail}
                      placeholder="ornek@email.com"
                      required
                    />

                    <CleanInput
                      id="address"
                      label="Adres"
                      value={shipping.address}
                      onChange={(v) => setShipping({ ...shipping, address: v })}
                      icon={MapPin}
                      placeholder="Mahalle, Sokak, Bina No, Daire"
                      required
                    />

                    <div className="grid gap-4 md:grid-cols-3">
                      <CleanInput
                        id="city"
                        label="İl"
                        value={shipping.city}
                        onChange={(v) => setShipping({ ...shipping, city: v })}
                        icon={Building}
                        required
                      />
                      <CleanInput
                        id="district"
                        label="İlçe"
                        value={shipping.district}
                        onChange={(v) => setShipping({ ...shipping, district: v })}
                      />
                      <CleanInput
                        id="postalCode"
                        label="Posta Kodu"
                        value={shipping.postalCode}
                        onChange={(v) => setShipping({ ...shipping, postalCode: v })}
                        maxLength={5}
                      />
                    </div>
                  </div>

                  </div>{/* end shipping form card */}

                  {/* Actions */}
                  <div className="mt-8 flex items-center gap-4">
                    <Button variant="outline" onClick={onBack}>
                      <ChevronLeft className="mr-2 h-4 w-4" />
                      Geri
                    </Button>

                    {isFreeOrder ? (
                      /* Free order: skip payment, submit directly */
                      <motion.button
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                        onClick={handleSubmit}
                        disabled={!isShippingValid || isProcessing}
                        className={`
                          flex flex-1 items-center justify-center gap-3 rounded-xl px-8 py-4 font-semibold text-white transition-all
                          ${
                            isShippingValid && !isProcessing
                              ? "bg-gradient-to-r from-green-500 to-emerald-600 shadow-lg shadow-green-500/30 hover:shadow-green-500/50"
                              : "cursor-not-allowed bg-gray-300"
                          }
                        `}
                      >
                        {isProcessing ? (
                          <>
                            <Loader2 className="h-5 w-5 animate-spin" />
                            <span>İşleniyor...</span>
                          </>
                        ) : (
                          <>
                            <Rocket className="h-5 w-5" />
                            <span>Ücretsiz Siparişi Tamamla</span>
                          </>
                        )}
                      </motion.button>
                    ) : (
                      <Button
                        onClick={() => setStage("payment")}
                        disabled={!isShippingValid}
                        className="flex-1 bg-purple-600 hover:bg-purple-700"
                      >
                        Ödemeye Geç
                        <ChevronRight className="ml-2 h-4 w-4" />
                      </Button>
                    )}
                  </div>
                </motion.div>
              )}

              {/* Free order on payment stage: promo applied after reaching payment */}
              {stage === "payment" && isFreeOrder && (
                <motion.div
                  key="free-complete"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="space-y-4"
                >
                  <div className="rounded-xl border-2 border-green-200 bg-green-50 p-6 text-center">
                    <div className="mx-auto mb-3 flex h-14 w-14 items-center justify-center rounded-full bg-green-100">
                      <Ticket className="h-7 w-7 text-green-600" />
                    </div>
                    <h3 className="text-lg font-bold text-green-700">Kupon Uygulandı!</h3>
                    <p className="mt-1 text-sm text-green-600">
                      Promosyon kodunuz sayesinde siparişiniz ücretsiz. Ödeme gerekmez.
                    </p>
                  </div>

                  <div className="flex items-center gap-3">
                    <Button variant="outline" onClick={() => setStage("shipping")}>
                      <ChevronLeft className="mr-2 h-4 w-4" />
                      Geri
                    </Button>
                    <motion.button
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      onClick={handleSubmit}
                      disabled={!isShippingValid || isProcessing}
                      className={`
                        flex flex-1 items-center justify-center gap-3 rounded-xl px-8 py-4 font-semibold text-white transition-all
                        ${
                          isShippingValid && !isProcessing
                            ? "bg-gradient-to-r from-green-500 to-emerald-600 shadow-lg shadow-green-500/30 hover:shadow-green-500/50"
                            : "cursor-not-allowed bg-gray-300"
                        }
                      `}
                    >
                      {isProcessing ? (
                        <>
                          <Loader2 className="h-5 w-5 animate-spin" />
                          <span>İşleniyor...</span>
                        </>
                      ) : (
                        <>
                          <Rocket className="h-5 w-5" />
                          <span>Ücretsiz Siparişi Tamamla</span>
                        </>
                      )}
                    </motion.button>
                  </div>
                </motion.div>
              )}

              {/* Payment Step — Iyzico redirect (card data collected on Iyzico side for PCI compliance) */}
              {stage === "payment" && !isFreeOrder && (
                <motion.div
                  key="payment"
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  className="space-y-4"
                >
                  <div className="rounded-xl bg-white p-6 shadow-sm">
                    <div className="mb-5 flex items-center gap-2">
                      <div className="flex h-8 w-8 items-center justify-center rounded-full bg-purple-100">
                        <CreditCard className="h-4 w-4 text-purple-600" />
                      </div>
                      <div>
                        <h2 className="text-base font-semibold text-gray-800">Güvenli Ödeme</h2>
                        <p className="text-xs text-gray-500">iyzico altyapısı ile güvenli ödeme</p>
                      </div>
                    </div>

                    {/* Iyzico redirect info */}
                    <div className="rounded-xl border-2 border-purple-100 bg-gradient-to-br from-purple-50 to-indigo-50 p-5 text-center">
                      <div className="mx-auto mb-3 flex h-14 w-14 items-center justify-center rounded-full bg-purple-100">
                        <Shield className="h-7 w-7 text-purple-600" />
                      </div>
                      <h3 className="mb-2 text-lg font-semibold text-gray-800">
                        Güvenli Ödeme Sayfası
                      </h3>
                      <p className="mb-3 text-sm text-gray-600">
                        Siparişi onayladığınızda iyzico güvenli ödeme sayfasına yönlendirileceksiniz.
                        Kart bilgileriniz bizim sunucularımızda saklanmaz.
                      </p>

                      {/* Accepted cards & iyzico logo */}
                      <div className="mb-4 flex flex-col items-center gap-3">
                        <Image
                          src="/images/payment/iyzico_ile_ode_colored.svg"
                          alt="iyzico ile öde"
                          width={120}
                          height={40}
                          className="h-10 w-auto"
                        />
                        <Image
                          src="/images/payment/logo_band_colored.svg"
                          alt="Visa, Mastercard, Troy ile güvenli ödeme"
                          width={215}
                          height={16}
                          className="h-4 w-auto"
                        />
                      </div>
                    </div>

                    {/* Trust Signals */}
                    <div className="mt-4 flex flex-wrap items-center justify-center gap-4 border-t border-gray-100 pt-4">
                      <TrustBadge icon={Lock} text="SSL Güvenli" />
                      <TrustBadge icon={Shield} text="256-Bit Şifreleme" />
                      <TrustBadge icon={FileText} text="KVKK Uyumlu" />
                      <TrustBadge icon={FileText} text="E-Fatura" />
                    </div>

                    {/* Legal Acknowledgment */}
                    <div className="mt-4 rounded-lg border border-gray-200 bg-gray-50 p-4">
                      <label className="flex cursor-pointer items-start gap-3">
                        <input
                          type="checkbox"
                          checked={termsAccepted}
                          onChange={(e) => setTermsAccepted(e.target.checked)}
                          className="mt-0.5 h-4 w-4 shrink-0 rounded border-gray-300 text-purple-600 focus:ring-purple-500"
                        />
                        <span className="text-xs leading-relaxed text-gray-600">
                          <a
                            href="/distance-sales"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="font-medium text-purple-600 underline hover:text-purple-800"
                          >
                            Mesafeli Satış Sözleşmesi
                          </a>
                          &apos;ni,{" "}
                          <a
                            href="/privacy"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="font-medium text-purple-600 underline hover:text-purple-800"
                          >
                            Gizlilik Politikası
                          </a>
                          &apos;nı ve{" "}
                          <a
                            href="/delivery"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="font-medium text-purple-600 underline hover:text-purple-800"
                          >
                            Teslimat ve İade Şartları
                          </a>
                          &apos;nı okudum ve kabul ediyorum.
                        </span>
                      </label>
                    </div>

                    {/* Actions */}
                    <div className="mt-5 flex items-center gap-3">
                      <Button variant="outline" onClick={() => setStage("shipping")}>
                        <ChevronLeft className="mr-2 h-4 w-4" />
                        Geri
                      </Button>
                      <motion.button
                        whileHover={{ scale: termsAccepted ? 1.02 : 1 }}
                        whileTap={{ scale: termsAccepted ? 0.98 : 1 }}
                        onClick={handleSubmit}
                        disabled={isProcessing || !termsAccepted}
                        className={`
                          flex flex-1 items-center justify-center gap-3 rounded-xl px-8 py-4 font-semibold text-white transition-all
                          ${
                            !isProcessing && termsAccepted
                              ? "bg-gradient-to-r from-green-500 to-emerald-600 shadow-lg shadow-green-500/30 hover:shadow-green-500/50"
                              : "cursor-not-allowed bg-gray-300"
                          }
                        `}
                      >
                        {isProcessing ? (
                          <>
                            <Loader2 className="h-5 w-5 animate-spin" />
                            <span>Ödeme sayfasına yönlendiriliyor...</span>
                          </>
                        ) : (
                          <>
                            <Rocket className="h-5 w-5" />
                            <span>Ödemeye Geç ({totalPrice} TL)</span>
                          </>
                        )}
                      </motion.button>
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Right Column - Order Summary (Sticky) */}
          <div className="lg:col-span-2">
            <div className="sticky top-4 space-y-4">
              {/* Book Preview */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
                className="rounded-xl bg-white p-4 shadow-sm"
              >
                <div className="relative mb-4 aspect-[1.414/1] overflow-hidden rounded-xl bg-gradient-to-br from-purple-100 to-pink-100 shadow-lg">
                  {coverImageUrl ? (
                    <img src={coverImageUrl} alt="Kitap Kapağı" className="h-full w-full object-cover" />
                  ) : (
                    <div className="flex h-full w-full items-center justify-center bg-gradient-to-br from-purple-200 via-pink-100 to-orange-100">
                      <Package className="h-12 w-12 text-purple-300" />
                    </div>
                  )}
                  <div className="absolute inset-y-0 left-0 w-3 bg-gradient-to-r from-amber-900/30 via-amber-800/20 to-transparent" />
                  <div className="absolute inset-x-0 bottom-0 h-3 bg-gradient-to-t from-black/15 to-transparent" />
                  <div className="absolute inset-y-0 right-0 w-2 bg-gradient-to-l from-black/10 to-transparent" />
                </div>
                <h3 className="text-center font-semibold text-gray-800">
                  &ldquo;{storyTitle}&rdquo;
                </h3>
                <p className="mt-1 text-center text-sm text-gray-500">
                  {childName} için özel hazırlandı
                </p>
              </motion.div>

              {/* Order Summary */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
                className="rounded-xl bg-white p-4 shadow-sm"
              >
                <h3 className="mb-3 font-semibold text-gray-800">Sipariş Özeti</h3>

                <div className="space-y-3 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">{productName}</span>
                    <span className="font-medium">{basePrice} TL</span>
                  </div>

                  {hasAudioBook && (
                    <div className="flex justify-between">
                      <span className="text-gray-600">
                        Sesli Kitap ({audioType === "cloned" ? "Klonlanmış Ses" : "Profesyonel Ses"})
                      </span>
                      <span className="font-medium">{audioPrice} TL</span>
                    </div>
                  )}

                  <div className="flex justify-between text-green-600">
                    <span>Kargo</span>
                    <span className="font-medium">ÜCRETSİZ</span>
                  </div>

                  {/* Promo discount line */}
                  {appliedPromo?.valid && (
                    <div className="flex justify-between text-green-600">
                      <span className="flex items-center gap-1">
                        <Ticket className="h-3.5 w-3.5" />
                        Kupon ({appliedPromo.promo_summary?.code})
                      </span>
                      <span className="font-medium">-{discountAmount} TL</span>
                    </div>
                  )}

                  <div className="mt-3 flex justify-between border-t pt-3 text-lg">
                    <span className="font-semibold">Toplam</span>
                    <div className="text-right">
                      {discountAmount > 0 && (
                        <span className="mr-2 text-sm text-gray-400 line-through">{rawTotal} TL</span>
                      )}
                      <span className="font-bold text-purple-600">
                        {totalPrice === 0 ? "ÜCRETSİZ" : `${totalPrice} TL`}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Promo Code Input */}
                <div className="mt-4 border-t pt-4">
                  {appliedPromo?.valid ? (
                    /* Applied promo badge */
                    <div className="flex items-center justify-between rounded-xl border-2 border-green-200 bg-green-50 p-3">
                      <div className="flex items-center gap-2">
                        <Ticket className="h-4 w-4 text-green-600" />
                        <span className="text-sm font-medium text-green-700">
                          {appliedPromo.promo_summary?.code}
                        </span>
                        <span className="text-xs text-green-600">
                          (
                          {appliedPromo.promo_summary?.discount_type === "PERCENT"
                            ? `%${appliedPromo.promo_summary?.discount_value}`
                            : `${appliedPromo.promo_summary?.discount_value} TL`}
                          )
                        </span>
                      </div>
                      <button
                        onClick={handleRemovePromo}
                        className="text-green-600 hover:text-red-500 transition-colors"
                        title="Kuponu kaldır"
                      >
                        <X className="h-4 w-4" />
                      </button>
                    </div>
                  ) : (
                    /* Promo input */
                    <div>
                      <div className="flex gap-2">
                        <div className="relative flex-1">
                          <Ticket className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
                          <input
                            type="text"
                            placeholder="Kupon kodu"
                            value={promoInput}
                            onChange={(e) => setPromoInput(e.target.value.toUpperCase())}
                            onKeyDown={(e) => {
                              if (e.key === "Enter") handleApplyPromo();
                            }}
                            className="w-full rounded-xl border-2 border-gray-200 bg-white py-2.5 pl-9 pr-3 text-sm outline-none transition-all focus:border-purple-500"
                            maxLength={50}
                          />
                        </div>
                        <Button
                          onClick={handleApplyPromo}
                          disabled={!promoInput.trim() || promoLoading}
                          size="sm"
                          className="rounded-xl px-4"
                        >
                          {promoLoading ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                          ) : (
                            "Uygula"
                          )}
                        </Button>
                      </div>
                      {promoResult && !promoResult.valid && (
                        <p className="mt-2 text-xs text-red-500">{promoResult.reason}</p>
                      )}
                    </div>
                  )}
                </div>
              </motion.div>

              {/* Delivery & Guarantees */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.4 }}
                className="space-y-4 rounded-2xl bg-white p-6 shadow-sm"
              >
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-full bg-green-100">
                    <Calendar className="h-5 w-5 text-green-600" />
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Tahmini Teslimat</p>
                    <p className="font-medium text-green-600">{getEstimatedDelivery()}</p>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-full bg-pink-100">
                    <Heart className="h-5 w-5 text-pink-500" />
                  </div>
                  <div>
                    <p className="font-medium text-gray-800">%100 Mutluluk Garantisi</p>
                    <p className="text-sm text-gray-500">Beğenmezseniz iade</p>
                  </div>
                </div>

                <div className="flex items-center gap-3 border-t pt-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-full bg-amber-100">
                    <Clock className="h-5 w-5 text-amber-600" />
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Sepet rezervasyonu</p>
                    <p className="font-mono font-medium text-amber-600">{formatTimer(cartTimer)}</p>
                  </div>
                </div>
              </motion.div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
