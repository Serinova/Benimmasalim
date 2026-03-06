"use client";

import { useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import Image from "next/image";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useToast } from "@/hooks/use-toast";
import { API_BASE_URL } from "@/lib/api";
import { Sparkles, ArrowRight, Eye, EyeOff } from "lucide-react";

export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-purple-600 border-t-transparent" />
        </div>
      }
    >
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
      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      const data = await response.json();

      if (!response.ok) {
        toast({
          title: "Giriş Başarısız",
          description: data.detail || "E-posta veya şifre hatalı.",
          variant: "destructive",
        });
        return;
      }

      if (data.access_token) {
        localStorage.setItem("token", data.access_token);
        if (data.refresh_token) localStorage.setItem("refreshToken", data.refresh_token);
        if (data.user) localStorage.setItem("user", JSON.stringify(data.user));
        toast({ title: "Hoş geldiniz!", description: "Başarıyla giriş yaptınız." });
        router.replace(returnUrl || "/");
      }
    } catch {
      toast({
        title: "Bağlantı Hatası",
        description: "Sunucuya ulaşılamıyor. Lütfen tekrar deneyin.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleGuestContinue = () => {
    const existingToken = localStorage.getItem("token");
    if (!existingToken) {
      router.replace("/create-v2");
      return;
    }
    if (
      window.confirm(
        "Zaten giriş yapılı. Çıkış yapıp misafir olarak devam etmek istiyor musunuz?"
      )
    ) {
      localStorage.removeItem("token");
      localStorage.removeItem("refreshToken");
      localStorage.removeItem("user");
      router.replace("/create-v2");
    }
  };

  return (
    <div className="flex min-h-screen">
      {/* ─── Sol: Marka Paneli ─── */}
      <div className="hidden lg:flex lg:w-[45%] relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-purple-600 via-violet-600 to-indigo-700" />

        {/* Dekoratif daireler */}
        <div className="wizard-blob absolute -top-24 -right-24 h-96 w-96 rounded-full bg-white/5" />
        <div className="wizard-blob animation-delay-1s absolute bottom-10 -left-16 h-64 w-64 rounded-full bg-white/5" />

        <div className="relative z-10 flex flex-col justify-between p-12 text-white">
          <Link href="/" className="flex items-center gap-3" aria-label="Ana Sayfa — Benim Masalım">
            <Image
              src="/logo.png"
              alt="Benim Masalım"
              width={56}
              height={56}
              className="h-14 w-14 rounded-2xl object-contain drop-shadow-lg"
              priority
            />
            <span className="text-2xl font-bold tracking-tight">Benim Masalım</span>
          </Link>

          <div className="space-y-6">
            <div>
              <div className="inline-flex items-center gap-2 rounded-full bg-white/10 px-4 py-1.5 text-sm backdrop-blur-sm">
                <Sparkles className="h-4 w-4" aria-hidden="true" />
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

            {/* Referans yorumu */}
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
            &copy; {new Date().getFullYear()} Benim Masalım. Tüm hakları saklıdır.
          </p>
        </div>
      </div>

      {/* ─── Sağ: Form Paneli ─── */}
      <div className="flex w-full flex-1 items-center justify-center bg-gradient-to-br from-slate-50 to-purple-50/40 p-6 sm:p-10">
        <div className="w-full max-w-md">
          {/* Mobil logo */}
          <div className="mb-8 flex items-center justify-center gap-3 lg:hidden">
            <Image
              src="/logo.png"
              alt="Benim Masalım"
              width={48}
              height={48}
              className="h-12 w-12 rounded-2xl object-contain drop-shadow"
              priority
            />
            <span className="text-2xl font-bold text-slate-900">
              Benim <span className="text-primary">Masalım</span>
            </span>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-8 shadow-xl shadow-purple-500/5">
            <div className="mb-6">
              <h2 className="text-2xl font-bold text-slate-900">Giriş Yap</h2>
              <p className="mt-1 text-sm text-slate-500">
                Hesabınıza giriş yapın veya kayıt olmadan devam edin
              </p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4" aria-label="Giriş formu">
              <div className="space-y-1.5">
                <Label htmlFor="email" className="text-xs font-medium text-slate-700">
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
                  className="h-11 rounded-xl border-slate-200 bg-slate-50/50 transition-colors focus:border-purple-400 focus:bg-white"
                />
              </div>

              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <Label htmlFor="password" className="text-xs font-medium text-slate-700">
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
                    className="h-11 rounded-xl border-slate-200 bg-slate-50/50 pr-10 transition-colors focus:border-purple-400 focus:bg-white"
                  />
                  <button
                    type="button"
                    tabIndex={0}
                    aria-label={showPassword ? "Şifreyi gizle" : "Şifreyi göster"}
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 rounded p-0.5 text-slate-400 hover:text-slate-600 focus:outline-none focus:ring-2 focus:ring-purple-400"
                  >
                    {showPassword ? (
                      <EyeOff className="h-4 w-4" />
                    ) : (
                      <Eye className="h-4 w-4" />
                    )}
                  </button>
                </div>
              </div>

              <Button
                type="submit"
                disabled={loading || !email || !password}
                className="h-11 w-full gap-2 rounded-xl bg-gradient-to-r from-purple-600 to-pink-500 font-semibold text-white hover:from-purple-700 hover:to-pink-600"
              >
                {loading ? (
                  <>
                    <span
                      className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent"
                      aria-hidden="true"
                    />
                    <span className="sr-only">Giriş yapılıyor…</span>
                  </>
                ) : (
                  <>
                    Giriş Yap
                    <ArrowRight className="h-4 w-4" aria-hidden="true" />
                  </>
                )}
              </Button>
            </form>

            <div className="mt-4 flex items-center gap-3">
              <div className="flex-1 border-t border-slate-200" />
              <span className="text-xs text-slate-400">veya</span>
              <div className="flex-1 border-t border-slate-200" />
            </div>

            <Button
              type="button"
              variant="outline"
              onClick={handleGuestContinue}
              className="mt-4 h-11 w-full rounded-xl border-slate-200 text-slate-600 hover:border-purple-200 hover:bg-purple-50 hover:text-purple-700"
            >
              Kayıt Olmadan Devam Et
            </Button>

            <p className="mt-6 text-center text-sm text-slate-500">
              Hesabınız yok mu?{" "}
              <Link
                href="/auth/register"
                className="font-medium text-purple-600 hover:text-purple-700 hover:underline"
              >
                Ücretsiz kaydol
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
