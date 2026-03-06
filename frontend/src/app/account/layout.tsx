"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";
import Image from "next/image";
import { Package, Users, Settings, LogOut, Plus, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";

const NAV_ITEMS = [
  { href: "/account", label: "Siparişlerim", icon: Package, exact: true },
  { href: "/account/children", label: "Çocuklarım", icon: Users },
  { href: "/account/profile", label: "Profil", icon: Settings },
];

export default function AccountLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [userName, setUserName] = useState<string>("");
  const [authChecked, setAuthChecked] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
      router.replace(`/auth/login?returnUrl=${encodeURIComponent(pathname)}`);
      return;
    }
    try {
      const user = JSON.parse(localStorage.getItem("user") || "{}");
      setUserName(user.full_name || user.email || "");
    } catch {
      /* ignore */
    }
    setAuthChecked(true);
  }, [router, pathname]);

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("refreshToken");
    localStorage.removeItem("user");
    window.dispatchEvent(new Event("auth-change"));
    router.replace("/");
  };

  const isActive = (href: string, exact?: boolean) => {
    if (exact) return pathname === href;
    return pathname.startsWith(href);
  };

  if (!authChecked) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50">
        <Loader2 className="h-6 w-6 animate-spin text-purple-500" aria-label="Yükleniyor" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Top header */}
      <header className="sticky top-0 z-30 border-b bg-white/95 backdrop-blur-sm">
        <div className="mx-auto flex h-14 max-w-5xl items-center justify-between px-4">
          <Link href="/" className="flex items-center gap-2.5" aria-label="Ana Sayfa — Benim Masalım">
            <Image
              src="/logo.png"
              alt="Benim Masalım"
              width={44}
              height={44}
              className="h-11 w-11 object-contain"
            />
            <span className="hidden text-base font-bold text-slate-900 sm:inline">
              Benim <span className="text-primary">Masalım</span>
            </span>
          </Link>

          <div className="flex items-center gap-2">
            {userName && (
              <span className="hidden text-sm text-slate-600 sm:inline">
                Merhaba, <strong className="font-semibold">{userName.split(" ")[0]}</strong>
              </span>
            )}
            <Link href="/create-v2">
              <Button size="sm" className="h-9 gap-1.5 rounded-lg bg-gradient-to-r from-purple-600 to-pink-500 text-xs text-white hover:from-purple-700 hover:to-pink-600">
                <Plus className="h-3.5 w-3.5" aria-hidden="true" />
                Yeni Kitap
              </Button>
            </Link>
            <button
              onClick={handleLogout}
              aria-label="Çıkış Yap"
              className="flex h-9 w-9 items-center justify-center rounded-lg text-slate-400 hover:bg-slate-100 hover:text-slate-600 focus:outline-none focus:ring-2 focus:ring-purple-400"
            >
              <LogOut className="h-4 w-4" aria-hidden="true" />
            </button>
          </div>
        </div>
      </header>

      {/* Tab navigation — desktop/tablet only; mobile uses bottom nav */}
      <nav className="sticky top-14 z-20 hidden border-b bg-white sm:block" aria-label="Hesap menüsü">
        <div className="mx-auto flex max-w-5xl gap-0 overflow-x-auto scrollbar-none px-4">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const active = isActive(item.href, item.exact);
            return (
              <Link
                key={item.href}
                href={item.href}
                aria-current={active ? "page" : undefined}
                className={`flex h-12 items-center gap-1.5 whitespace-nowrap border-b-2 px-4 text-sm font-medium transition-colors ${
                  active
                    ? "border-purple-600 text-purple-700"
                    : "border-transparent text-slate-500 hover:border-slate-200 hover:text-slate-700"
                }`}
              >
                <Icon className="h-4 w-4" aria-hidden="true" />
                {item.label}
              </Link>
            );
          })}
        </div>
      </nav>

      {/* Content — bottom padding for mobile nav */}
      <main
        className="mx-auto max-w-5xl px-4 py-6"
        style={{ paddingBottom: "calc(5rem + env(safe-area-inset-bottom, 0px))" }}
      >
        {children}
      </main>

      {/* Mobile bottom nav — 44px tap targets */}
      <nav
        className="fixed bottom-0 left-0 right-0 z-30 border-t bg-white sm:hidden"
        aria-label="Mobil hesap menüsü"
        style={{ paddingBottom: "env(safe-area-inset-bottom, 0px)" }}
      >
        <div className="flex justify-around">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const active = isActive(item.href, item.exact);
            return (
              <Link
                key={item.href}
                href={item.href}
                aria-label={item.label}
                aria-current={active ? "page" : undefined}
                className={`flex min-h-[3rem] flex-1 flex-col items-center justify-center gap-0.5 py-2 text-xs font-medium transition-colors ${
                  active ? "text-purple-600" : "text-slate-400 hover:text-slate-600"
                }`}
              >
                <Icon className="h-5 w-5" aria-hidden="true" />
                {item.label}
              </Link>
            );
          })}
        </div>
      </nav>
    </div>
  );
}
