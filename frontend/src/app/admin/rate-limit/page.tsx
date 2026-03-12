"use client";

import { useState } from "react";
import { Gauge, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useToast } from "@/hooks/use-toast";
import { useAdminAuth } from "@/hooks/use-admin-auth";
import { adminResetRateLimits } from "@/lib/api";

export default function RateLimitPage() {
  const [loading, setLoading] = useState(false);
  const { toast } = useToast();

  useAdminAuth();

  const handleReset = async () => {
    setLoading(true);
    try {
      const res = await adminResetRateLimits();
      if (res.ok) {
        toast({
          title: "Rate limitler sıfırlandı",
          description: res.deleted_keys != null
            ? `${res.deleted_keys} sayaç silindi.`
            : res.message,
        });
      } else {
        toast({
          title: "Hata",
          description: res.message || "Sıfırlama başarısız.",
          variant: "destructive",
        });
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : "İstek başarısız.";
      toast({
        title: "Hata",
        description: msg,
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Rate Limit</h1>
        <p className="mt-1 text-slate-500">
          Hikaye oluşturma ve diğer endpoint’ler için IP bazlı sayaçları yönetin.
        </p>
      </div>

      <Card className="border-0 shadow-sm">
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="rounded-lg bg-amber-100 p-2.5">
              <Gauge className="h-6 w-6 text-amber-600" />
            </div>
            <div>
              <CardTitle className="text-lg">Tüm rate limitleri sıfırla</CardTitle>
              <CardDescription>
                Tüm IP’ler için hikaye oluşturma ve diğer endpoint sayaçlarını sıfırlar. Misafir
                kullanıcılar yeniden deneme kotasına kavuşur.
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <Button
            onClick={handleReset}
            disabled={loading}
            className="gap-2"
          >
            {loading ? (
              <>
                <RefreshCw className="h-4 w-4 animate-spin" />
                Sıfırlanıyor...
              </>
            ) : (
              <>
                <RefreshCw className="h-4 w-4" />
                Rate limitleri sıfırla
              </>
            )}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
