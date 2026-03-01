"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";
import { BookOpen, Package, Users, Settings, LogOut, Plus, Loader2 } from "lucide-react";
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
      <div className="flex min-h-screen items-center justify-center bg-gray-50">
        <Loader2 className="h-6 w-6 animate-spin text-purple-500" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <meta name="robots" content="noindex, nofollow" />
      {/* Top header */}
      <header className="sticky top-0 z-30 border-b bg-white/95 backdrop-blur-sm">
        <div className="mx-auto flex h-14 max-w-5xl items-center justify-between px-4">
          <Link href="/" className="flex items-center gap-2">
            <BookOpen className="h-5 w-5 text-purple-600" />
            <span className="text-base font-bold text-purple-800 hidden sm:inline">Benim Masalım</span>
          </Link>

          <div className="flex items-center gap-2">
            {userName && (
              <span className="text-sm text-gray-600 hidden sm:inline">
                Merhaba, <strong>{userName.split(" ")[0]}</strong>
              </span>
            )}
            <Link href="/create-v2">
              <Button size="sm" className="h-8 rounded-lg bg-purple-600 text-xs hover:bg-purple-700">
                <Plus className="mr-1 h-3 w-3" />
                Yeni Kitap
              </Button>
            </Link>
            <button
              onClick={handleLogout}
              className="flex h-8 w-8 items-center justify-center rounded-lg text-gray-400 hover:bg-gray-100 hover:text-gray-600"
              title="Çıkış Yap"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        </div>
      </header>

      {/* Tab navigation */}
      <nav className="sticky top-14 z-20 border-b bg-white">
        <div className="mx-auto flex max-w-5xl gap-0 overflow-x-auto px-4">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const active = isActive(item.href, item.exact);
            return (
              <Link
                key={item.href}
                href={item.href}
                aria-label={item.label}
                aria-current={active ? "page" : undefined}
                className={`flex items-center gap-1.5 whitespace-nowrap border-b-2 px-4 py-3 text-sm font-medium transition-colors ${
                  active
                    ? "border-purple-600 text-purple-700"
                    : "border-transparent text-gray-500 hover:border-gray-200 hover:text-gray-700"
                }`}
              >
                <Icon className="h-4 w-4" />
                {item.label}
              </Link>
            );
          })}
        </div>
      </nav>

      {/* Content */}
      <main className="mx-auto max-w-5xl px-4 py-6">{children}</main>

      {/* Mobile bottom nav */}
      <nav className="fixed bottom-0 left-0 right-0 z-30 border-t bg-white sm:hidden">
        <div className="flex justify-around py-2">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const active = isActive(item.href, item.exact);
            return (
              <Link
                key={item.href}
                href={item.href}
                aria-label={item.label}
                aria-current={active ? "page" : undefined}
                className={`flex flex-col items-center gap-0.5 px-3 py-1 text-xs ${
                  active ? "text-purple-600" : "text-gray-400"
                }`}
              >
                <Icon className="h-5 w-5" />
                {item.label}
              </Link>
            );
          })}
        </div>
      </nav>
    </div>
  );
}
