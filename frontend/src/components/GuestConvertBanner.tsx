"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useToast } from "@/hooks/use-toast";
import { convertGuest } from "@/lib/api";
import { UserPlus, Eye, EyeOff, X } from "lucide-react";

interface GuestConvertBannerProps {
  onConverted?: () => void;
}

export default function GuestConvertBanner({ onConverted }: GuestConvertBannerProps) {
  const [expanded, setExpanded] = useState(false);
  const [dismissed, setDismissed] = useState(() => {
    if (typeof window !== "undefined") {
      return localStorage.getItem("guest_banner_dismissed") === "1";
    }
    return false;
  });
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const { toast } = useToast();

  if (dismissed) return null;

  const handleDismiss = () => {
    setDismissed(true);
    localStorage.setItem("guest_banner_dismissed", "1");
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (password.length < 8 || !/[A-Z]/.test(password) || !/[a-z]/.test(password) || !/\d/.test(password)) {
      toast({
        title: "Zayıf şifre",
        description: "Şifre en az 8 karakter, büyük harf, küçük harf ve rakam içermelidir.",
        variant: "destructive",
      });
      return;
    }

    setLoading(true);

    try {
      const data = await convertGuest(email, password, fullName);
      localStorage.setItem("token", data.access_token);
      if (data.refresh_token) localStorage.setItem("refreshToken", data.refresh_token);
      localStorage.setItem("user", JSON.stringify(data.user));
      localStorage.removeItem("guest_banner_dismissed");
      window.dispatchEvent(new Event("auth-change"));

      toast({ title: "Hesap oluşturuldu!", description: "Artık tüm siparişlerinizi takip edebilirsiniz." });
      onConverted?.();
    } catch (error) {
      const msg = error instanceof Error ? error.message : "Hesap oluşturulamadı";
      toast({ title: "Hata", description: msg, variant: "destructive" });
    } finally {
      setLoading(false);
    }
  };

  if (!expanded) {
    return (
      <div className="relative rounded-xl border-2 border-purple-200 bg-gradient-to-r from-purple-50 to-violet-50 p-4">
        <button
          onClick={handleDismiss}
          className="absolute right-2 top-2 text-gray-400 hover:text-gray-600"
          aria-label="Kapat"
        >
          <X className="h-4 w-4" />
        </button>
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-purple-100">
            <UserPlus className="h-5 w-5 text-purple-600" />
          </div>
          <div className="flex-1">
            <p className="text-sm font-semibold text-purple-900">Hesabınızı oluşturun</p>
            <p className="text-xs text-purple-700/70">
              Tüm siparişlerinizi tek yerden takip edin, tekrar sipariş verin.
            </p>
          </div>
          <Button
            size="sm"
            className="shrink-0 rounded-lg bg-purple-600 text-xs hover:bg-purple-700"
            onClick={() => setExpanded(true)}
          >
            Oluştur
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-xl border-2 border-purple-200 bg-white p-5 shadow-sm">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-base font-semibold text-gray-900">Hesap Oluştur</h3>
        <button onClick={() => setExpanded(false)} className="text-gray-400 hover:text-gray-600">
          <X className="h-4 w-4" />
        </button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-3">
        <div>
          <Label className="text-xs text-gray-600">Ad Soyad</Label>
          <Input
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            placeholder="Ad Soyad"
            required
            minLength={2}
            className="mt-1 h-10 rounded-lg text-sm"
          />
        </div>
        <div>
          <Label className="text-xs text-gray-600">E-posta</Label>
          <Input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="ornek@email.com"
            required
            className="mt-1 h-10 rounded-lg text-sm"
          />
        </div>
        <div>
          <Label className="text-xs text-gray-600">Şifre</Label>
          <div className="relative mt-1">
            <Input
              type={showPassword ? "text" : "password"}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="En az 8 karakter"
              required
              minLength={8}
              className="h-10 rounded-lg pr-10 text-sm"
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400"
              tabIndex={-1}
            >
              {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          </div>
        </div>
        <Button
          type="submit"
          className="h-10 w-full rounded-lg bg-purple-600 text-sm font-semibold hover:bg-purple-700"
          disabled={loading}
        >
          {loading ? "Oluşturuluyor..." : "Hesabımı Oluştur"}
        </Button>
      </form>
    </div>
  );
}
