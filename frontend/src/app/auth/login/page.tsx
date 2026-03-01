"use client";

import { useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useToast } from "@/hooks/use-toast";
import { API_BASE_URL } from "@/lib/api";
import { BookOpen, Sparkles, ArrowRight, Eye, EyeOff } from "lucide-react";

const HEALTH_URL = API_BASE_URL.replace(/\/api\/v1\/?$/, "") + "/health";

export default function LoginPage() {
  return (
    <Suspense fallback={<div className="flex min-h-screen items-center justify-center"><div className="h-6 w-6 animate-spin rounded-full border-2 border-purple-600 border-t-transparent" /></div>}>
      <LoginContent />
    </Suspense>
  );
}

function LoginContent() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const router = useRouter();
  const searchParams = useSearchParams();
  const returnUrl = searchParams.get("returnUrl");
  const { toast } = useToast();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      // Quick health check (3s)
      const healthController = new AbortController();
      const healthTimeout = setTimeout(() => healthController.abort(), 3000);
      try {
        await fetch(HEALTH_URL, { signal: healthController.signal });
      } catch {
        clearTimeout(healthTimeout);
        toast({
          title: "Sunucu erişilemiyor",
          description: "Sunucu şu anda yanıt vermiyor. Lütfen daha sonra tekrar deneyin.",
          variant: "destructive",
        });
        setLoading(false);
        return;
      }
      clearTimeout(healthTimeout);

      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 60000);

      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        let detail = "Giriş başarısız";
        if (response.status === 401) {
          detail = "E-posta veya şifre hatalı.";
        } else if (response.status === 429) {
          detail = "Çok fazla deneme yaptınız. Lütfen birkaç dakika bekleyin.";
        } else if (typeof error?.detail === "string") {
          detail = error.detail;
        }
        throw new Error(detail);
      }

      const data = await response.json().catch(() => ({}));
      const token = data?.access_token;
      const user = data?.user;

      if (!token) {
        throw new Error("Sunucu geçersiz yanıt döndü. Tekrar deneyin.");
      }

      localStorage.setItem("token", token);
      if (data?.refresh_token) {
        localStorage.setItem("refreshToken", data.refresh_token);
      }
      localStorage.setItem("user", JSON.stringify(user ?? { role: "user" }));
      window.dispatchEvent(new Event("auth-change"));

      toast({ title: "Hoş geldiniz! 👋", description: "Giriş yapıldı!" });

      if (user?.role === "admin") {
        router.replace("/admin");
      } else if (returnUrl && returnUrl.startsWith("/") && !returnUrl.startsWith("//")) {
        router.replace(returnUrl);
      } else {
        router.replace("/account");
      }
    } catch (error) {
      const isNetworkError =
        error instanceof TypeError &&
        (error.message === "Failed to fetch" || error.message.includes("Load failed"));
      const isAbort = error instanceof Error && error.name === "AbortError";
      const message = isAbort
        ? "Sunucu yanıt vermedi. Lütfen daha sonra tekrar deneyin."
        : isNetworkError
          ? "Sunucuya bağlanılamadı. Lütfen internet bağlantınızı kontrol edin."
          : error instanceof Error
            ? error.message
            : "Giriş yapılamadı";
      toast({ title: "Hata", description: message, variant: "destructive" });
    } finally {
      setLoading(false);
    }
  };

  const handleGuestContinue = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("refreshToken");
    localStorage.removeItem("user");
    router.replace("/create-v2");
  };

  return (
    <div className="flex min-h-screen">
      {/* ─── Left: Branding Panel ─── */}
      <div className="hidden lg:flex lg:w-[45%] relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-purple-600 via-violet-600 to-indigo-700" />

        {/* Animated circles */}
        <div className="absolute -top-24 -right-24 h-96 w-96 rounded-full bg-white/5 animate-pulse" />
        <div className="absolute bottom-10 -left-16 h-64 w-64 rounded-full bg-white/5 animate-pulse" style={{ animationDelay: "1.5s" }} />
        <div className="absolute top-1/2 right-1/4 h-40 w-40 rounded-full bg-white/5 animate-pulse" style={{ animationDelay: "0.5s" }} />

        {/* Content */}
        <div className="relative z-10 flex flex-col justify-between p-12 text-white">
          <Link href="/" className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white/20 backdrop-blur-sm">
              <BookOpen className="h-5 w-5" />
            </div>
            <span className="text-xl font-bold tracking-tight">Benim Masalım</span>
          </Link>

          <div className="space-y-6">
            <div>
              <div className="inline-flex items-center gap-2 rounded-full bg-white/10 px-4 py-1.5 text-sm backdrop-blur-sm">
                <Sparkles className="h-4 w-4" />
                Tekrar hoş geldiniz
              </div>
              <h1 className="mt-6 text-4xl font-bold leading-tight">
                Masalınız <br />
                <span className="text-purple-200">sizi bekliyor</span>
              </h1>
              <p className="mt-4 max-w-sm text-lg text-purple-100/80">
                Hesabınıza giriş yaparak kitaplarınızı yönetin ve yeni masallar oluşturun.
              </p>
            </div>

            {/* Testimonial */}
            <div className="max-w-sm rounded-2xl bg-white/10 p-5 backdrop-blur-sm">
              <p className="text-sm italic text-purple-100/90">
                &ldquo;Kızım kitabı görünce çok sevindi! Kendi ismini ve
                fotoğrafını görünce gözleri parladı.&rdquo;
              </p>
              <p className="mt-3 text-xs font-semibold text-purple-200">
                — Ayşe Y., İstanbul
              </p>
            </div>
          </div>

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
              <h2 className="text-2xl font-bold text-gray-900">Giriş Yap</h2>
              <p className="mt-1 text-sm text-gray-500">
                Hesabınıza giriş yapın veya kayıt olmadan devam edin
              </p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-1.5">
                <Label htmlFor="email" className="text-xs font-medium text-gray-700">
                  E-posta
                </Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="ornek@email.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  autoComplete="username"
                  required
                  className="h-11 rounded-xl border-gray-200 bg-gray-50/50 transition-colors focus:border-purple-400 focus:bg-white"
                />
              </div>

              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <Label htmlFor="password" className="text-xs font-medium text-gray-700">
                    Şifre
                  </Label>
                  <Link
                    href="/auth/forgot-password"
                    className="text-xs text-purple-500 hover:text-purple-700 hover:underline"
                  >
                    Şifremi Unuttum
                  </Link>
                </div>
                <div className="relative">
                  <Input
                    id="password"
                    type={showPassword ? "text" : "password"}
                    placeholder="••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    autoComplete="current-password"
                    required
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
              </div>

              <Button
                type="submit"
                className="h-11 w-full rounded-xl bg-gradient-to-r from-purple-600 to-violet-600 text-sm font-semibold shadow-lg shadow-purple-500/25 transition-all hover:shadow-xl hover:shadow-purple-500/30 hover:brightness-110"
                disabled={loading}
              >
                {loading ? (
                  <span className="flex items-center gap-2">
                    <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                    Giriş yapılıyor...
                  </span>
                ) : (
                  <span className="flex items-center gap-2">
                    Giriş Yap
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

            {/* Guest + Register */}
            <div className="space-y-3">
              <Button
                type="button"
                variant="outline"
                className="h-10 w-full rounded-xl border-gray-200 text-sm text-gray-600 hover:border-purple-200 hover:text-purple-700"
                onClick={handleGuestContinue}
              >
                Kayıt Olmadan Devam Et
              </Button>
              <p className="text-center text-xs text-gray-500">
                Hesabınız yok mu?{" "}
                <Link href="/auth/register" className="font-semibold text-purple-600 hover:text-purple-700 hover:underline">
                  Ücretsiz Kayıt Ol
                </Link>
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
