"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useToast } from "@/hooks/use-toast";
import { API_BASE_URL } from "@/lib/api";

const HEALTH_URL = API_BASE_URL.replace(/\/api\/v1\/?$/, "") + "/health";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();
  const { toast } = useToast();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      // Önce backend erişilebilir mi kısa kontrol (3 sn)
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
      const timeoutMs = 60000; // 60 sn — DB yavaşsa yetmesi için
      const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

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

      toast({ title: "Başarılı", description: "Giriş yapıldı!" });

      if (user?.role === "admin") {
        router.replace("/admin");
      } else {
        router.replace("/create-v2");
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

  const handleGuestLogin = async () => {
    setLoading(true);
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 15000);
      const response = await fetch(`${API_BASE_URL}/auth/guest`, {
        method: "POST",
        signal: controller.signal,
      });
      clearTimeout(timeoutId);

      if (!response.ok) throw new Error("Misafir girişi başarısız");

      const data = await response.json().catch(() => ({}));
      const token = data?.access_token;
      if (token) {
        localStorage.setItem("token", token);
        localStorage.setItem("user", JSON.stringify({ role: "guest" }));
        router.replace("/create-v2");
      } else {
        throw new Error("Sunucu geçersiz yanıt döndü.");
      }
    } catch (error) {
      const isAbort = error instanceof Error && error.name === "AbortError";
      const isNetworkError =
        error instanceof TypeError &&
        (error.message === "Failed to fetch" || error.message.includes("Load failed"));
      const message = isAbort
        ? "İstek zaman aşımına uğradı. Lütfen tekrar deneyin."
        : isNetworkError
          ? "Sunucuya bağlanılamadı. Lütfen internet bağlantınızı kontrol edin."
          : error instanceof Error
            ? error.message
            : "Misafir girişi yapılamadı";
      toast({ title: "Hata", description: message, variant: "destructive" });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-purple-50 to-pink-50 p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl font-bold text-purple-800">Giriş Yap</CardTitle>
          <CardDescription>Hesabınıza giriş yapın veya misafir olarak devam edin</CardDescription>
        </CardHeader>
        <form onSubmit={handleSubmit}>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">E-posta</Label>
              <Input
                id="email"
                type="email"
                placeholder="ornek@email.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoComplete="username"
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Şifre</Label>
              <Input
                id="password"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
                required
              />
            </div>
          </CardContent>
          <CardFooter className="flex flex-col gap-3">
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? "Giriş yapılıyor..." : "Giriş Yap"}
            </Button>
            <Button
              type="button"
              variant="outline"
              className="w-full"
              onClick={handleGuestLogin}
              disabled={loading}
            >
              Misafir Olarak Devam Et
            </Button>
            <p className="text-center text-sm text-gray-600">
              Hesabınız yok mu?{" "}
              <Link href="/auth/register" className="text-purple-600 hover:underline">
                Kayıt Ol
              </Link>
            </p>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
}
