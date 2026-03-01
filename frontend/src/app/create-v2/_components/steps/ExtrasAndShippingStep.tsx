"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Headphones, MapPin } from "lucide-react";
import FormField, { FormTextarea } from "../ui/FormField";
import StickyCTA from "../StickyCTA";
import type { ShippingInfo } from "../../_hooks/useOrderDraft";
import {
  validateFullName,
  validateEmail,
  validatePhone,
  validateAddress,
  validateCity,
  validateDedication,
  validateStep4Shipping,
} from "../../_lib/validations";
import { API_BASE_URL } from "@/lib/api";

interface ExtrasAndShippingStepProps {
  childName: string;
  hasAudioBook: boolean;
  audioType: "system" | "cloned";
  clonedVoiceId: string;
  hasColoringBook: boolean;
  coloringBookPrice: number;
  dedicationNote: string;
  shipping: ShippingInfo;
  onAudioChange: (has: boolean, type: "system" | "cloned") => void;
  onColoringBookChange: (has: boolean) => void;
  onDedicationChange: (note: string) => void;
  onShippingFieldChange: (field: keyof ShippingInfo, value: string) => void;
  onContinue: () => void;
  onBack: () => void;
}

interface SavedAddress {
  id: string;
  label: string;
  full_name: string;
  phone: string;
  address_line: string;
  city: string;
  district: string;
  postal_code: string;
  is_default: boolean;
}

export default function ExtrasAndShippingStep({
  childName,
  hasAudioBook,
  audioType,
  hasColoringBook,
  coloringBookPrice,
  dedicationNote,
  shipping,
  onAudioChange,
  onColoringBookChange,
  onDedicationChange,
  onShippingFieldChange,
  onContinue,
  onBack,
}: ExtrasAndShippingStepProps) {
  const [touched, setTouched] = useState<Record<string, boolean>>({});
  const [savedAddresses, setSavedAddresses] = useState<SavedAddress[]>([]);

  const touch = (field: string) =>
    setTouched((prev) => ({ ...prev, [field]: true }));

  const canContinue = validateStep4Shipping({
    fullName: shipping.fullName,
    email: shipping.email,
    phone: shipping.phone,
    address: shipping.address,
    city: shipping.city,
  });

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) return;
    fetch(`${API_BASE_URL}/profile/addresses`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((r) => (r.ok ? r.json() : []))
      .then((data) => {
        if (Array.isArray(data)) setSavedAddresses(data);
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (!shipping.fullName && !shipping.email) {
      try {
        const u = JSON.parse(localStorage.getItem("user") || "{}");
        if (u.full_name) onShippingFieldChange("fullName", u.full_name);
        if (u.email) onShippingFieldChange("email", u.email);
        if (u.phone) onShippingFieldChange("phone", u.phone);
      } catch { /* ignore */ }
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const applySavedAddress = (addr: SavedAddress) => {
    onShippingFieldChange("fullName", addr.full_name);
    onShippingFieldChange("phone", addr.phone);
    onShippingFieldChange("address", addr.address_line);
    onShippingFieldChange("city", addr.city);
    onShippingFieldChange("district", addr.district);
    onShippingFieldChange("postalCode", addr.postal_code);
  };

  return (
    <div className="pb-24 space-y-6">
      {/* ── Section: Ekstralar ── */}
      <section aria-label="Ekstralar">
        <div className="flex items-center gap-2 mb-4">
          <Headphones className="h-4 w-4 text-purple-600" />
          <h2 className="text-base sm:text-lg font-bold text-gray-800">
            Kitabınızı Özelleştirin
          </h2>
        </div>

        {/* Audio options */}
        <div className="rounded-2xl border border-gray-100 bg-white shadow-sm overflow-hidden mb-4">
          <div className="px-4 pt-3 pb-2 border-b border-gray-50">
            <p className="text-sm font-bold text-gray-800">Sesli Kitap</p>
            <p className="text-xs text-gray-500">QR kodu okutunca masal başlar</p>
          </div>
          <div className="p-3 space-y-2">
            {[
              { has: false, type: "system" as const, label: "Sadece Kitap", desc: "Sesli kitap olmadan", price: "Sıfır Ekstra", emoji: "📖" },
              { has: true, type: "system" as const, label: "Profesyonel Masalcı", desc: "Pedagojik eğitimli sesler", price: "+150 ₺", emoji: "🎙️" },
              { has: true, type: "cloned" as const, label: "Sizin Sesinizle", desc: "Yapay zeka sesinizi kopyalar", price: "+300 ₺", emoji: "🎤", premium: true },
            ].map((opt) => {
              const isActive = opt.has === hasAudioBook && (!opt.has || opt.type === audioType);
              return (
                <button
                  key={`${opt.has}-${opt.type}`}
                  type="button"
                  onClick={() => onAudioChange(opt.has, opt.type)}
                  className={`
                    w-full flex items-center gap-3 p-3 rounded-xl border-2 transition-all text-left
                    ${isActive
                      ? opt.premium ? "border-amber-400 bg-amber-50" : "border-purple-500 bg-purple-50"
                      : "border-gray-100 bg-gray-50 hover:border-gray-200"}
                  `}
                >
                  <div className={`flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-lg text-base ${isActive ? (opt.premium ? "bg-amber-100" : "bg-purple-100") : "bg-gray-100"}`}>
                    {opt.emoji}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className={`font-bold text-sm ${isActive ? (opt.premium ? "text-amber-900" : "text-purple-800") : "text-gray-700"}`}>{opt.label}</p>
                    <p className="text-xs text-gray-500">{opt.desc}</p>
                  </div>
                  <p className={`text-sm font-bold flex-shrink-0 ${isActive ? (opt.premium ? "text-amber-600" : "text-purple-600") : "text-gray-400"}`}>{opt.price}</p>
                  {isActive && <div className={`flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full text-white text-xs ${opt.premium ? "bg-amber-500" : "bg-purple-500"}`}>✓</div>}
                </button>
              );
            })}
          </div>
        </div>

        {/* Coloring book */}
        <div className="rounded-2xl border border-gray-100 bg-white shadow-sm p-4 mb-4">
          <div className="flex items-center justify-between mb-3">
            <div>
              <p className="text-sm font-bold text-gray-800">Boyama Kitabı</p>
              <p className="text-xs text-gray-500">Hikayedeki sahneleri boyasın!</p>
            </div>
            <span className="text-sm font-black text-emerald-600">+{coloringBookPrice || 150} ₺</span>
          </div>
          <button
            type="button"
            onClick={() => onColoringBookChange(!hasColoringBook)}
            className={`w-full py-3 rounded-xl font-bold text-sm transition-all flex items-center justify-center gap-2 ${
              hasColoringBook
                ? "bg-gradient-to-r from-emerald-500 to-teal-500 text-white shadow-lg shadow-emerald-200"
                : "bg-white border-2 border-emerald-300 text-emerald-700 hover:bg-emerald-50"
            }`}
          >
            {hasColoringBook ? "✓ Boyama Kitabı Eklendi" : `🎨 Boyama Kitabı Ekle · ${coloringBookPrice || 150} ₺`}
          </button>
        </div>

        {/* Dedication */}
        <FormTextarea
          label="İthaf Notu (İsteğe Bağlı)"
          value={dedicationNote}
          onChange={(e) => onDedicationChange(e.target.value)}
          onBlur={() => touch("dedication")}
          placeholder="Örn: Sevgili Uras, bu kitap senin için..."
          maxLength={300}
          rows={2}
          error={touched.dedication ? validateDedication(dedicationNote) : null}
          touched={!!touched.dedication}
          hint={`${dedicationNote.length}/300`}
        />
      </section>

      {/* ── Section: Teslimat ── */}
      <section aria-label="Teslimat bilgileri">
        <div className="flex items-center gap-2 mb-4">
          <MapPin className="h-4 w-4 text-purple-600" />
          <h2 className="text-base sm:text-lg font-bold text-gray-800">
            Teslimat Bilgileri
          </h2>
        </div>

        {savedAddresses.length > 0 && (
          <div className="mb-4 space-y-2">
            <p className="text-xs font-semibold text-gray-500">Kayıtlı Adresler</p>
            {savedAddresses.map((addr) => (
              <button
                key={addr.id}
                type="button"
                onClick={() => applySavedAddress(addr)}
                className="w-full text-left rounded-xl border border-gray-200 bg-white p-3 text-sm hover:border-purple-300 transition-colors"
              >
                <p className="font-semibold text-gray-800">{addr.label || addr.full_name}</p>
                <p className="text-xs text-gray-500 truncate">{addr.address_line}, {addr.city}</p>
              </button>
            ))}
          </div>
        )}

        <div className="space-y-3">
          <FormField
            label="Ad Soyad"
            value={shipping.fullName}
            onChange={(e) => onShippingFieldChange("fullName", e.target.value)}
            onBlur={() => touch("fullName")}
            placeholder="Ad Soyad"
            autoComplete="name"
            error={touched.fullName ? validateFullName(shipping.fullName) : null}
            touched={!!touched.fullName}
          />

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <FormField
              label="E-posta"
              type="email"
              value={shipping.email}
              onChange={(e) => onShippingFieldChange("email", e.target.value)}
              onBlur={() => touch("email")}
              placeholder="ornek@email.com"
              autoComplete="email"
              error={touched.email ? validateEmail(shipping.email) : null}
              touched={!!touched.email}
            />
            <FormField
              label="Telefon"
              type="tel"
              value={shipping.phone}
              onChange={(e) => onShippingFieldChange("phone", e.target.value)}
              onBlur={() => touch("phone")}
              placeholder="05XX XXX XX XX"
              autoComplete="tel"
              error={touched.phone ? validatePhone(shipping.phone) : null}
              touched={!!touched.phone}
            />
          </div>

          <FormField
            label="Adres"
            value={shipping.address}
            onChange={(e) => onShippingFieldChange("address", e.target.value)}
            onBlur={() => touch("address")}
            placeholder="Mahalle, sokak, bina no, daire no"
            autoComplete="street-address"
            error={touched.address ? validateAddress(shipping.address) : null}
            touched={!!touched.address}
          />

          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            <FormField
              label="Şehir"
              value={shipping.city}
              onChange={(e) => onShippingFieldChange("city", e.target.value)}
              onBlur={() => touch("city")}
              placeholder="İstanbul"
              autoComplete="address-level1"
              error={touched.city ? validateCity(shipping.city) : null}
              touched={!!touched.city}
            />
            <FormField
              label="İlçe"
              value={shipping.district}
              onChange={(e) => onShippingFieldChange("district", e.target.value)}
              placeholder="İlçe (isteğe bağlı)"
              autoComplete="address-level2"
            />
            <FormField
              label="Posta Kodu"
              value={shipping.postalCode}
              onChange={(e) => onShippingFieldChange("postalCode", e.target.value)}
              placeholder="34000"
              autoComplete="postal-code"
            />
          </div>
        </div>
      </section>

      <StickyCTA
        primaryLabel={canContinue ? "Ödemeye Geç" : "Bilgileri Tamamlayın"}
        onPrimary={onContinue}
        primaryDisabled={!canContinue}
        secondaryLabel="← Geri"
        onSecondary={onBack}
      />
    </div>
  );
}
