"use client";

import { useState, useMemo } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useToast } from "@/hooks/use-toast";
import { API_BASE_URL } from "@/lib/api";
import {
  Check,
  X,
  Eye,
  EyeOff,
  BookOpen,
  Sparkles,
  ArrowRight,
  ShieldCheck,
  Package,
  Star,
} from "lucide-react";

/* ───────── Password strength ───────── */
interface PasswordRule {
  label: string;
  test: (pw: string) => boolean;
}

const PASSWORD_RULES: PasswordRule[] = [
  { label: "En az 8 karakter", test: (pw) => pw.length >= 8 },
  { label: "Büyük harf (A-Z)", test: (pw) => /[A-ZÇĞİÖŞÜ]/.test(pw) },
  { label: "Küçük harf (a-z)", test: (pw) => /[a-zçğıöşü]/.test(pw) },
  { label: "Rakam (0-9)", test: (pw) => /\d/.test(pw) },
  {
    label: "Özel karakter (!@#$%...)",
    test: (pw) => /[^a-zA-ZçğıöşüÇĞİÖŞÜ0-9\s]/.test(pw),
  },
];

/* ───────── Benefit items ───────── */
const BENEFITS = [
  {
    icon: Package,
    title: "Sipariş Takibi",
    desc: "Kitabınızın üretim ve kargo durumunu anlık takip edin.",
  },
  {
    icon: Star,
    title: "Kişiye Özel Deneyim",
    desc: "Çocuğunuzun adı ve fotoğrafıyla benzersiz masallar.",
  },
  {
    icon: ShieldCheck,
    title: "Güvenli Alışveriş",
    desc: "256-bit SSL şifreleme ile güvenli ödeme.",
  },
];

export default function RegisterPage() {
  const [formData, setFormData] = useState({
    email: "",
    password: "",
    confirmPassword: "",
    full_name: "",
    phone: "",
  });
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const router = useRouter();
  const { toast } = useToast();

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const ruleResults = useMemo(
    () => PASSWORD_RULES.map((r) => r.test(formData.password)),
    [formData.password]
  );
  const allRulesPassed = ruleResults.every(Boolean);
  const passwordsMatch =
    formData.confirmPassword.length > 0 &&
    formData.password === formData.confirmPassword;

  const strengthScore = ruleResults.filter(Boolean).length;
  const strengthPercent = (strengthScore / PASSWORD_RULES.length) * 100;
  const strengthColor =
    strengthPercent <= 20
      ? "bg-red-500"
      : strengthPercent <= 60
        ? "bg-amber-500"
        : strengthPercent < 100
          ? "bg-blue-500"
          : "bg-green-500";

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!allRulesPassed) {
      toast({
        title: "Şifre Kuralları",
        description: "Lütfen tüm şifre kurallarını karşılayın.",
        variant: "destructive",
      });
      return;
    }

    if (formData.password !== formData.confirmPassword) {
      toast({
        title: "Hata",
        description: "Şifreler eşleşmiyor",
        variant: "destructive",
      });
      return;
    }

    setLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: formData.email,
          password: formData.password,
          full_name: formData.full_name,
          phone: formData.phone || undefined,
        }),
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        let detail = "Kayıt başarısız";
        if (typeof error?.detail === "string") {
          detail = error.detail;
        } else if (Array.isArray(error?.detail) && error.detail.length > 0) {
          detail = error.detail
            .map((d: { msg?: string }) => d.msg || "")
            .filter(Boolean)
            .join(", ");
        }
        throw new Error(detail);
      }

      const data = await response.json();

      if (data?.access_token) {
        localStorage.setItem("token", data.access_token);
      }
      if (data?.refresh_token) {
        localStorage.setItem("refreshToken", data.refresh_token);
      }
      if (data?.user) {
        localStorage.setItem("user", JSON.stringify(data.user));
      } else {
        localStorage.setItem(
          "user",
          JSON.stringify({
            email: formData.email,
            full_name: formData.full_name,
            role: "user",
          })
        );
      }

      window.dispatchEvent(new Event("auth-change"));

      toast({
        title: "Hoş geldiniz! 🎉",
        description: "Hesabınız oluşturuldu, giriş yapıldı.",
      });

      router.replace("/account");
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Kayıt işlemi başarısız";
      toast({ title: "Hata", description: message, variant: "destructive" });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen">
      {/* ─── Left: Branding Panel ─── */}
      <div className="hidden lg:flex lg:w-[45%] relative overflow-hidden">
        {/* Gradient background */}
        <div className="absolute inset-0 bg-gradient-to-br from-purple-600 via-violet-600 to-indigo-700" />

        {/* Animated circles */}
        <div className="absolute -top-24 -left-24 h-96 w-96 rounded-full bg-white/5 animate-pulse" />
        <div className="absolute bottom-20 -right-20 h-72 w-72 rounded-full bg-white/5 animate-pulse" style={{ animationDelay: "1s" }} />
        <div className="absolute top-1/3 left-1/4 h-48 w-48 rounded-full bg-white/5 animate-pulse" style={{ animationDelay: "2s" }} />

        {/* Content */}
        <div className="relative z-10 flex flex-col justify-between p-12 text-white">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white/20 backdrop-blur-sm">
              <BookOpen className="h-5 w-5" />
            </div>
            <span className="text-xl font-bold tracking-tight">Benim Masalım</span>
          </Link>

          {/* Hero */}
          <div className="space-y-8">
            <div>
              <div className="inline-flex items-center gap-2 rounded-full bg-white/10 px-4 py-1.5 text-sm backdrop-blur-sm">
                <Sparkles className="h-4 w-4" />
                Ücretsiz hesap
              </div>
              <h1 className="mt-6 text-4xl font-bold leading-tight">
                Çocuğunuzun <br />
                <span className="text-purple-200">masalını oluşturun</span>
              </h1>
              <p className="mt-4 max-w-sm text-lg text-purple-100/80">
                Kayıt olun, kişiye özel masal kitabı oluşturun ve siparişlerinizi
                kolayca takip edin.
              </p>
            </div>

            {/* Benefits */}
            <div className="space-y-4">
              {BENEFITS.map((b) => (
                <div key={b.title} className="flex items-start gap-3">
                  <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-white/10">
                    <b.icon className="h-4 w-4" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold">{b.title}</p>
                    <p className="text-xs text-purple-200/70">{b.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Footer */}
          <p className="text-xs text-purple-300/60">
            © 2025 Benim Masalım. Tüm hakları saklıdır.
          </p>
        </div>
      </div>

      {/* ─── Right: Form Panel ─── */}
      <div className="flex w-full flex-1 items-center justify-center bg-gradient-to-br from-gray-50 to-purple-50/30 p-6 sm:p-10">
        <div className="w-full max-w-md">
          {/* Mobile logo */}
          <div className="mb-8 flex items-center justify-center gap-2 lg:hidden">
            <BookOpen className="h-6 w-6 text-purple-600" />
            <span className="text-xl font-bold text-purple-800">Benim Masalım</span>
          </div>

          <div className="rounded-2xl border bg-white p-8 shadow-xl shadow-purple-500/5">
            <div className="mb-6">
              <h2 className="text-2xl font-bold text-gray-900">Hesap Oluştur</h2>
              <p className="mt-1 text-sm text-gray-500">
                Hızlıca kayıt olun ve masalınızı oluşturmaya başlayın
              </p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Ad Soyad */}
              <div className="space-y-1.5">
                <Label htmlFor="full_name" className="text-xs font-medium text-gray-700">
                  Ad Soyad
                </Label>
                <Input
                  id="full_name"
                  name="full_name"
                  placeholder="Adınız Soyadınız"
                  value={formData.full_name}
                  onChange={handleChange}
                  autoComplete="name"
                  required
                  className="h-11 rounded-xl border-gray-200 bg-gray-50/50 transition-colors focus:border-purple-400 focus:bg-white"
                />
              </div>

              {/* Email */}
              <div className="space-y-1.5">
                <Label htmlFor="email" className="text-xs font-medium text-gray-700">
                  E-posta
                </Label>
                <Input
                  id="email"
                  name="email"
                  type="email"
                  placeholder="ornek@email.com"
                  value={formData.email}
                  onChange={handleChange}
                  autoComplete="email"
                  required
                  className="h-11 rounded-xl border-gray-200 bg-gray-50/50 transition-colors focus:border-purple-400 focus:bg-white"
                />
              </div>

              {/* Telefon */}
              <div className="space-y-1.5">
                <Label htmlFor="phone" className="text-xs font-medium text-gray-700">
                  Telefon <span className="text-gray-400">(opsiyonel)</span>
                </Label>
                <Input
                  id="phone"
                  name="phone"
                  type="tel"
                  placeholder="05XX XXX XX XX"
                  value={formData.phone}
                  onChange={handleChange}
                  autoComplete="tel"
                  className="h-11 rounded-xl border-gray-200 bg-gray-50/50 transition-colors focus:border-purple-400 focus:bg-white"
                />
              </div>

              {/* Şifre */}
              <div className="space-y-1.5">
                <Label htmlFor="password" className="text-xs font-medium text-gray-700">
                  Şifre
                </Label>
                <div className="relative">
                  <Input
                    id="password"
                    name="password"
                    type={showPassword ? "text" : "password"}
                    placeholder="••••••••"
                    value={formData.password}
                    onChange={handleChange}
                    autoComplete="new-password"
                    required
                    minLength={8}
                    className="h-11 rounded-xl border-gray-200 bg-gray-50/50 pr-10 transition-colors focus:border-purple-400 focus:bg-white"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"
                    tabIndex={-1}
                    aria-label={showPassword ? "Şifreyi gizle" : "Şifreyi göster"}
                  >
                    {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>

                {/* Strength bar + rules */}
                {formData.password.length > 0 && (
                  <div className="mt-2 space-y-2">
                    {/* Strength bar */}
                    <div className="flex items-center gap-2">
                      <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-gray-100">
                        <div
                          className={`h-full rounded-full transition-all duration-500 ${strengthColor}`}
                          style={{ width: `${strengthPercent}%` }}
                        />
                      </div>
                      <span className="text-[10px] font-medium text-gray-400 w-8 text-right">
                        {strengthScore}/{PASSWORD_RULES.length}
                      </span>
                    </div>

                    {/* Rules list */}
                    <div className="grid grid-cols-2 gap-x-3 gap-y-1">
                      {PASSWORD_RULES.map((rule, i) => (
                        <div
                          key={rule.label}
                          className={`flex items-center gap-1.5 text-[11px] transition-colors ${ruleResults[i] ? "text-green-600" : "text-gray-400"
                            }`}
                        >
                          {ruleResults[i] ? (
                            <Check className="h-3 w-3 shrink-0" />
                          ) : (
                            <X className="h-3 w-3 shrink-0" />
                          )}
                          <span className="leading-tight">{rule.label}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Şifre Tekrar */}
              <div className="space-y-1.5">
                <Label htmlFor="confirmPassword" className="text-xs font-medium text-gray-700">
                  Şifre Tekrar
                </Label>
                <div className="relative">
                  <Input
                    id="confirmPassword"
                    name="confirmPassword"
                    type={showConfirm ? "text" : "password"}
                    placeholder="••••••••"
                    value={formData.confirmPassword}
                    onChange={handleChange}
                    autoComplete="new-password"
                    required
                    className="h-11 rounded-xl border-gray-200 bg-gray-50/50 pr-10 transition-colors focus:border-purple-400 focus:bg-white"
                  />
                  <button
                    type="button"
                    onClick={() => setShowConfirm(!showConfirm)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"
                    tabIndex={-1}
                    aria-label={showConfirm ? "Şifreyi gizle" : "Şifreyi göster"}
                  >
                    {showConfirm ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
                {formData.confirmPassword.length > 0 && (
                  <p className={`mt-1 text-xs ${passwordsMatch ? "text-green-600" : "text-red-500"}`}>
                    {passwordsMatch ? "✓ Şifreler eşleşiyor" : "✗ Şifreler eşleşmiyor"}
                  </p>
                )}
              </div>

              {/* Submit */}
              <Button
                type="submit"
                className="h-11 w-full rounded-xl bg-gradient-to-r from-purple-600 to-violet-600 text-sm font-semibold shadow-lg shadow-purple-500/25 transition-all hover:shadow-xl hover:shadow-purple-500/30 hover:brightness-110"
                disabled={loading || !allRulesPassed || !passwordsMatch}
              >
                {loading ? (
                  <span className="flex items-center gap-2">
                    <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                    Oluşturuluyor...
                  </span>
                ) : (
                  <span className="flex items-center gap-2">
                    Hesap Oluştur
                    <ArrowRight className="h-4 w-4" />
                  </span>
                )}
              </Button>
            </form>

            {/* Divider */}
            <div className="relative my-6">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-gray-200" />
              </div>
              <div className="relative flex justify-center">
                <span className="bg-white px-3 text-xs text-gray-400">veya</span>
              </div>
            </div>

            {/* Guest + Login links */}
            <div className="space-y-3">
              <Link href="/create-v2" className="block">
                <Button
                  type="button"
                  variant="outline"
                  className="h-10 w-full rounded-xl border-gray-200 text-sm text-gray-600 hover:border-purple-200 hover:text-purple-700"
                >
                  Kayıt olmadan devam et
                </Button>
              </Link>
              <p className="text-center text-xs text-gray-500">
                Zaten hesabınız var mı?{" "}
                <Link href="/auth/login" className="font-semibold text-purple-600 hover:text-purple-700 hover:underline">
                  Giriş Yap
                </Link>
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
