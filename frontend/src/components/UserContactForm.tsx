"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import {
  User,
  Phone,
  Mail,
  ChevronRight,
  Sparkles,
  ShieldCheck,
  HeartHandshake,
  Loader2,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent } from "@/components/ui/card";
import { useToast } from "@/hooks/use-toast";
import { API_BASE_URL } from "@/lib/api";

// Form validation schema
const contactFormSchema = z.object({
  firstName: z.string().min(1, "Ad zorunludur").max(100, "Ad çok uzun"),
  lastName: z.string().min(1, "Soyad zorunludur").max(100, "Soyad çok uzun"),
  phone: z
    .string()
    .min(10, "Telefon numarası en az 10 karakter olmalı")
    .max(20, "Telefon numarası çok uzun")
    .refine((val) => {
      const cleaned = val.replace(/[^\d+]/g, "");
      return cleaned.length >= 10;
    }, "Geçerli bir telefon numarası girin"),
  email: z.string().email("Geçerli bir email adresi girin").optional().or(z.literal("")),
});

type ContactFormData = z.infer<typeof contactFormSchema>;

interface UserContactFormProps {
  onComplete: (userId: string, contactInfo: ContactInfo) => void;
  initialData?: Partial<ContactInfo>;
}

export interface ContactInfo {
  firstName: string;
  lastName: string;
  phone: string;
  email?: string;
  userId?: string;
}

export default function UserContactForm({ onComplete, initialData }: UserContactFormProps) {
  const [submitting, setSubmitting] = useState(false);
  const { toast } = useToast();

  const form = useForm<ContactFormData>({
    resolver: zodResolver(contactFormSchema),
    defaultValues: {
      firstName: initialData?.firstName || "",
      lastName: initialData?.lastName || "",
      phone: initialData?.phone || "",
      email: initialData?.email || "",
    },
  });

  // Reset form when initialData changes (e.g., after session restore)
  useEffect(() => {
    if (initialData) {
      form.reset({
        firstName: initialData.firstName || "",
        lastName: initialData.lastName || "",
        phone: initialData.phone || "",
        email: initialData.email || "",
      });
    }
  }, [initialData, form]);

  const onSubmit = async (data: ContactFormData) => {
    setSubmitting(true);
    try {
      const response = await fetch(`${API_BASE_URL}/leads/capture`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          first_name: data.firstName,
          last_name: data.lastName,
          phone: data.phone,
          email: data.email || null,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Bir hata oluştu");
      }

      const result = await response.json();

      // Store user_id in localStorage for session persistence
      localStorage.setItem("lead_user_id", result.user_id);

      toast({
        title: "Başarılı",
        description: result.message,
      });

      // Record KVKK disclosure consent in backend (fire-and-forget)
      if (data.email) {
        fetch(`${API_BASE_URL}/consent/record`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            email: data.email,
            consent_type: "KVKK_DISCLOSURE",
            action: "given",
            consent_version: "1.0",
            source: "UserContactForm",
          }),
        }).catch(() => {});
      }

      onComplete(result.user_id, {
        firstName: data.firstName,
        lastName: data.lastName,
        phone: data.phone,
        email: data.email,
        userId: result.user_id,
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : "Bilinmeyen hata";
      toast({
        title: "Hata",
        description: message,
        variant: "destructive",
      });
    } finally {
      setSubmitting(false);
    }
  };

  // Format phone number as user types
  const formatPhoneNumber = (value: string) => {
    // Remove non-digits
    const digits = value.replace(/\D/g, "");

    // Format as (5XX) XXX XX XX for Turkish numbers
    if (digits.startsWith("0")) {
      const cleaned = digits.slice(1);
      if (cleaned.length <= 3) return `(${cleaned}`;
      if (cleaned.length <= 6) return `(${cleaned.slice(0, 3)}) ${cleaned.slice(3)}`;
      if (cleaned.length <= 8)
        return `(${cleaned.slice(0, 3)}) ${cleaned.slice(3, 6)} ${cleaned.slice(6)}`;
      return `(${cleaned.slice(0, 3)}) ${cleaned.slice(3, 6)} ${cleaned.slice(6, 8)} ${cleaned.slice(8, 10)}`;
    }

    if (digits.startsWith("5")) {
      if (digits.length <= 3) return `(${digits}`;
      if (digits.length <= 6) return `(${digits.slice(0, 3)}) ${digits.slice(3)}`;
      if (digits.length <= 8)
        return `(${digits.slice(0, 3)}) ${digits.slice(3, 6)} ${digits.slice(6)}`;
      return `(${digits.slice(0, 3)}) ${digits.slice(3, 6)} ${digits.slice(6, 8)} ${digits.slice(8, 10)}`;
    }

    return value;
  };

  return (
    <div className="mx-auto max-w-2xl space-y-4">
      {/* Hero Section */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center"
      >
        <div className="mb-4 inline-flex items-center gap-2 rounded-full bg-gradient-to-r from-purple-100 via-pink-100 to-orange-100 px-4 py-2">
          <HeartHandshake className="h-4 w-4 text-purple-600" />
          <span className="text-sm font-medium text-purple-700">Kişisel Destek</span>
        </div>

        <h1 className="mb-2 bg-gradient-to-r from-purple-600 via-pink-500 to-orange-400 bg-clip-text text-2xl font-bold text-transparent md:text-3xl">
          Sizi Tanıyalım
        </h1>

        <p className="mx-auto max-w-lg text-gray-600">
          Hikaye oluşturma sürecinde size en iyi desteği sağlayabilmemiz için iletişim bilgilerinize
          ihtiyacımız var.
        </p>
      </motion.div>

      {/* Benefits */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.1 }}
        className="grid grid-cols-1 gap-4 md:grid-cols-3"
      >
        <Card className="border-purple-100 bg-purple-50/50">
          <CardContent className="flex items-center gap-3 p-4">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-purple-100">
              <ShieldCheck className="h-5 w-5 text-purple-600" />
            </div>
            <div>
              <p className="text-sm font-medium text-purple-900">Güvenli</p>
              <p className="text-xs text-purple-600">Bilgileriniz güvende</p>
            </div>
          </CardContent>
        </Card>

        <Card className="border-pink-100 bg-pink-50/50">
          <CardContent className="flex items-center gap-3 p-4">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-pink-100">
              <Phone className="h-5 w-5 text-pink-600" />
            </div>
            <div>
              <p className="text-sm font-medium text-pink-900">7/24 Destek</p>
              <p className="text-xs text-pink-600">Her an yanınızdayız</p>
            </div>
          </CardContent>
        </Card>

        <Card className="border-orange-100 bg-orange-50/50">
          <CardContent className="flex items-center gap-3 p-4">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-orange-100">
              <Sparkles className="h-5 w-5 text-orange-600" />
            </div>
            <div>
              <p className="text-sm font-medium text-orange-900">Kişiselleştirilmiş</p>
              <p className="text-xs text-orange-600">Size özel deneyim</p>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Form Card */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
      >
        <Card className="border-2 border-purple-200 shadow-lg">
          <CardContent className="p-6">
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-5">
              {/* Name Fields */}
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <div>
                  <Label htmlFor="firstName" className="mb-2 flex items-center gap-2">
                    <User className="h-4 w-4 text-purple-500" />
                    Ad <span className="text-red-500">*</span>
                  </Label>
                  <Input
                    id="firstName"
                    {...form.register("firstName")}
                    placeholder="Adınız"
                    className={`h-12 ${form.formState.errors.firstName ? "border-red-500" : ""}`}
                  />
                  {form.formState.errors.firstName && (
                    <p className="mt-1 text-xs text-red-500">
                      {form.formState.errors.firstName.message}
                    </p>
                  )}
                </div>

                <div>
                  <Label htmlFor="lastName" className="mb-2 flex items-center gap-2">
                    <User className="h-4 w-4 text-purple-500" />
                    Soyad <span className="text-red-500">*</span>
                  </Label>
                  <Input
                    id="lastName"
                    {...form.register("lastName")}
                    placeholder="Soyadınız"
                    className={`h-12 ${form.formState.errors.lastName ? "border-red-500" : ""}`}
                  />
                  {form.formState.errors.lastName && (
                    <p className="mt-1 text-xs text-red-500">
                      {form.formState.errors.lastName.message}
                    </p>
                  )}
                </div>
              </div>

              {/* Phone Field */}
              <div>
                <Label htmlFor="phone" className="mb-2 flex items-center gap-2">
                  <Phone className="h-4 w-4 text-purple-500" />
                  Telefon Numarası <span className="text-red-500">*</span>
                </Label>
                <Input
                  id="phone"
                  type="tel"
                  {...form.register("phone")}
                  onChange={(e) => {
                    const formatted = formatPhoneNumber(e.target.value);
                    form.setValue("phone", formatted);
                  }}
                  placeholder="(5XX) XXX XX XX"
                  className={`h-12 ${form.formState.errors.phone ? "border-red-500" : ""}`}
                />
                {form.formState.errors.phone && (
                  <p className="mt-1 text-xs text-red-500">{form.formState.errors.phone.message}</p>
                )}
                <p className="mt-1 text-xs text-gray-500">
                  Hikaye oluşturma sürecinde size ulaşabilmemiz için gerekli
                </p>
              </div>

              {/* Email Field */}
              <div>
                <Label htmlFor="email" className="mb-2 flex items-center gap-2">
                  <Mail className="h-4 w-4 text-purple-500" />
                  E-posta <span className="text-xs text-gray-400">(opsiyonel)</span>
                </Label>
                <Input
                  id="email"
                  type="email"
                  {...form.register("email")}
                  placeholder="ornek@email.com"
                  className={`h-12 ${form.formState.errors.email ? "border-red-500" : ""}`}
                />
                {form.formState.errors.email && (
                  <p className="mt-1 text-xs text-red-500">{form.formState.errors.email.message}</p>
                )}
              </div>

              {/* KVKK Consent */}
              <div className="rounded-lg border border-gray-200 bg-gray-50 p-3">
                <label className="flex cursor-pointer items-start gap-3">
                  <input
                    type="checkbox"
                    {...form.register("kvkkConsent" as never)}
                    required
                    className="mt-0.5 h-4 w-4 rounded border-gray-300 text-purple-600 accent-purple-600"
                  />
                  <span className="text-xs leading-relaxed text-gray-600">
                    <ShieldCheck className="mr-1 inline h-4 w-4 text-green-500" />
                    Kişisel verilerimin{" "}
                    <a
                      href="/kvkk"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="font-medium text-purple-600 underline"
                    >
                      KVKK Aydınlatma Metni
                    </a>{" "}
                    kapsamında işlenmesini kabul ediyorum.
                  </span>
                </label>
              </div>

              {/* Submit Button */}
              <Button
                type="submit"
                disabled={submitting}
                className="h-14 w-full bg-gradient-to-r from-purple-600 via-pink-500 to-orange-400 text-lg font-bold shadow-lg shadow-purple-200 hover:from-purple-700 hover:via-pink-600 hover:to-orange-500"
              >
                {submitting ? (
                  <>
                    <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                    Kaydediliyor...
                  </>
                ) : (
                  <>
                    Devam Et
                    <ChevronRight className="ml-2 h-5 w-5" />
                  </>
                )}
              </Button>
            </form>
          </CardContent>
        </Card>
      </motion.div>

      {/* Footer Note */}
      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.3 }}
        className="text-center text-sm text-gray-500"
      >
        Herhangi bir sorunuz mu var?{" "}
        <a href="tel:+905551234567" className="text-purple-600 hover:underline">
          Bizi arayın
        </a>
      </motion.p>
    </div>
  );
}
