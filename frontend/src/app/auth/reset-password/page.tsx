"use client";

import { useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useToast } from "@/hooks/use-toast";
import { resetPassword } from "@/lib/api";
import { BookOpen, Eye, EyeOff, CheckCircle, ArrowRight } from "lucide-react";

const PASSWORD_RULES = [
  { label: "En az 8 karakter", test: (v: string) => v.length >= 8 },
  { label: "Büyük harf (A-Z)", test: (v: string) => /[A-Z]/.test(v) },
  { label: "Küçük harf (a-z)", test: (v: string) => /[a-z]/.test(v) },
  { label: "Rakam (0-9)", test: (v: string) => /\d/.test(v) },
  { label: "Özel karakter (!@#$...)", test: (v: string) => /[!@#$%^&*(),.?":{}|<>_\-+=[\]~`]/.test(v) },
];

function ResetPasswordForm() {
  const searchParams = useSearchParams();
  const token = searchParams.get("token") || "";
  // Güvenlik: Email URL'de taşınmıyor (phishing vektörü önlemek için)
  // Kullanıcı email adresini form üzerinden kendisi giriyor

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const router = useRouter();
  const { toast } = useToast();

  const passedRules = PASSWORD_RULES.filter((r) => r.test(password)).length;
  const strengthPercent = (passedRules / PASSWORD_RULES.length) * 100;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (password !== confirmPassword) {
      toast({ title: "Hata", description: "Şifreler eşleşmiyor", variant: "destructive" });
      return;
    }

    if (passedRules < PASSWORD_RULES.length) {
      toast({ title: "Hata", description: "Şifre tüm gereksinimleri karşılamalıdır", variant: "destructive" });
      return;
    }

    setLoading(true);
    try {
      await resetPassword(token, email, password);
      setSuccess(true);
    } catch (error) {
      toast({
        title: "Hata",
        description: error instanceof Error ? error.message : "Şifre sıfırlama başarısız",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  if (!token) {
    return (
      <div className="text-center space-y-4">
        <h2 className="text-xl font-bold text-gray-900">Geçersiz Link</h2>
        <p className="text-sm text-gray-600">
          Şifre sıfırlama linki geçersiz veya eksik. Lütfen emailinizdeki linki tekrar tıklayın.
        </p>
        <Link href="/auth/forgot-password">
          <Button className="mt-4 rounded-xl">Yeni Link Talep Et</Button>
        </Link>
      </div>
    );
  }

  if (success) {
    return (
      <div className="text-center space-y-4">
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-green-100">
          <CheckCircle className="h-8 w-8 text-green-600" />
        </div>
        <h2 className="text-xl font-bold text-gray-900">Şifre Değiştirildi</h2>
        <p className="text-sm text-gray-600">
          Şifreniz başarıyla değiştirildi. Yeni şifrenizle giriş yapabilirsiniz.
        </p>
        <Button
          onClick={() => router.push("/auth/login")}
          className="mt-4 w-full rounded-xl bg-gradient-to-r from-purple-600 to-violet-600"
        >
          Giriş Yap
          <ArrowRight className="ml-2 h-4 w-4" />
        </Button>
      </div>
    );
  }

  return (
    <>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Yeni Şifre Belirle</h2>
        <p className="mt-1 text-sm text-gray-500">Email adresinizi ve yeni şifrenizi girin.</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="space-y-1.5">
          <Label htmlFor="email" className="text-xs font-medium text-gray-700">
            Email Adresi
          </Label>
          <Input
            id="email"
            type="email"
            placeholder="ornek@email.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            className="h-11 rounded-xl border-gray-200 bg-gray-50/50"
          />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="password" className="text-xs font-medium text-gray-700">
            Yeni Şifre
          </Label>
          <div className="relative">
            <Input
              id="password"
              type={showPassword ? "text" : "password"}
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="h-11 rounded-xl border-gray-200 bg-gray-50/50 pr-10"
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
              tabIndex={-1}
            >
              {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          </div>

          {/* Strength meter */}
          {password.length > 0 && (
            <div className="space-y-2 mt-2">
              <div className="h-1.5 w-full rounded-full bg-gray-100 overflow-hidden">
                <div
                  className="h-full rounded-full transition-all duration-300"
                  style={{
                    width: `${strengthPercent}%`,
                    backgroundColor:
                      strengthPercent < 40 ? "#ef4444" : strengthPercent < 80 ? "#f59e0b" : "#22c55e",
                  }}
                />
              </div>
              <div className="grid grid-cols-2 gap-1">
                {PASSWORD_RULES.map((rule) => (
                  <span
                    key={rule.label}
                    className={`text-xs ${rule.test(password) ? "text-green-600" : "text-gray-400"}`}
                  >
                    {rule.test(password) ? "✓" : "○"} {rule.label}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="confirm" className="text-xs font-medium text-gray-700">
            Şifre Tekrar
          </Label>
          <Input
            id="confirm"
            type="password"
            placeholder="••••••••"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            required
            className="h-11 rounded-xl border-gray-200 bg-gray-50/50"
          />
          {confirmPassword && password !== confirmPassword && (
            <p className="text-xs text-red-500">Şifreler eşleşmiyor</p>
          )}
        </div>

        <Button
          type="submit"
          className="h-11 w-full rounded-xl bg-gradient-to-r from-purple-600 to-violet-600 text-sm font-semibold shadow-lg shadow-purple-500/25"
          disabled={loading || passedRules < PASSWORD_RULES.length || password !== confirmPassword}
        >
          {loading ? (
            <span className="flex items-center gap-2">
              <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
              Değiştiriliyor...
            </span>
          ) : (
            "Şifremi Değiştir"
          )}
        </Button>
      </form>
    </>
  );
}

export default function ResetPasswordPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-gray-50 to-purple-50/30 p-6">
      <div className="w-full max-w-md">
        <div className="mb-8 flex items-center justify-center gap-2">
          <BookOpen className="h-6 w-6 text-purple-600" />
          <span className="text-xl font-bold text-purple-800">Benim Masalım</span>
        </div>
        <div className="rounded-2xl border bg-white p-8 shadow-xl shadow-purple-500/5">
          <Suspense fallback={<div className="text-center py-8 text-gray-400">Yükleniyor...</div>}>
            <ResetPasswordForm />
          </Suspense>
        </div>
      </div>
    </div>
  );
}
