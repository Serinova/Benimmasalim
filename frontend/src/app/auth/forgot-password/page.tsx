"use client";

import { useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useToast } from "@/hooks/use-toast";
import { forgotPassword } from "@/lib/api";
import { BookOpen, ArrowLeft, Mail, CheckCircle } from "lucide-react";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);
  const { toast } = useToast();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      await forgotPassword(email);
      setSent(true);
    } catch (error) {
      toast({
        title: "Hata",
        description: error instanceof Error ? error.message : "Bir hata oluştu",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-gray-50 to-purple-50/30 p-6">
      <div className="w-full max-w-md">
        <div className="mb-8 flex items-center justify-center gap-2">
          <BookOpen className="h-6 w-6 text-purple-600" />
          <span className="text-xl font-bold text-purple-800">Benim Masalım</span>
        </div>

        <div className="rounded-2xl border bg-white p-8 shadow-xl shadow-purple-500/5">
          {sent ? (
            <div className="text-center space-y-4">
              <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-green-100">
                <CheckCircle className="h-8 w-8 text-green-600" />
              </div>
              <h2 className="text-xl font-bold text-gray-900">Email Gönderildi</h2>
              <p className="text-sm text-gray-600">
                Eğer <strong>{email}</strong> adresi kayıtlıysa, şifre sıfırlama linki gönderildi.
                Lütfen email kutunuzu kontrol edin.
              </p>
              <p className="text-xs text-gray-400">
                Link 15 dakika geçerlidir. Spam klasörünü de kontrol etmeyi unutmayın.
              </p>
              <Link href="/auth/login">
                <Button variant="outline" className="mt-4 w-full rounded-xl">
                  <ArrowLeft className="mr-2 h-4 w-4" />
                  Giriş Sayfasına Dön
                </Button>
              </Link>
            </div>
          ) : (
            <>
              <div className="mb-6">
                <h2 className="text-2xl font-bold text-gray-900">Şifremi Unuttum</h2>
                <p className="mt-1 text-sm text-gray-500">
                  Email adresinizi girin, şifre sıfırlama linki gönderelim.
                </p>
              </div>

              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="space-y-1.5">
                  <Label htmlFor="email" className="text-xs font-medium text-gray-700">
                    E-posta Adresi
                  </Label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
                    <Input
                      id="email"
                      type="email"
                      placeholder="ornek@email.com"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      required
                      className="h-11 rounded-xl border-gray-200 bg-gray-50/50 pl-10 transition-colors focus:border-purple-400 focus:bg-white"
                    />
                  </div>
                </div>

                <Button
                  type="submit"
                  className="h-11 w-full rounded-xl bg-gradient-to-r from-purple-600 to-violet-600 text-sm font-semibold shadow-lg shadow-purple-500/25"
                  disabled={loading}
                >
                  {loading ? (
                    <span className="flex items-center gap-2">
                      <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                      Gönderiliyor...
                    </span>
                  ) : (
                    "Sıfırlama Linki Gönder"
                  )}
                </Button>
              </form>

              <div className="mt-6 text-center">
                <Link
                  href="/auth/login"
                  className="inline-flex items-center gap-1 text-sm text-purple-600 hover:text-purple-700 hover:underline"
                >
                  <ArrowLeft className="h-3 w-3" />
                  Giriş sayfasına dön
                </Link>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
