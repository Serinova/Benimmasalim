"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
  SheetClose,
} from "@/components/ui/sheet";
import { Menu, UserCircle, LogOut, LayoutDashboard } from "lucide-react";

const navLinks = [
  { href: "/#nasil-calisir", label: "Nasıl Çalışır?" },
  { href: "/#ornekler", label: "Örnekler" },
  { href: "/#fiyat", label: "Fiyat" },
  { href: "/#sss", label: "SSS" },
  { href: "/contact", label: "İletişim" },
];

interface UserData {
  role?: string;
  full_name?: string;
  email?: string;
}

export default function Header() {
  const [mounted, setMounted] = useState(false);
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [isAdmin, setIsAdmin] = useState(false);
  const [userName, setUserName] = useState<string | null>(null);
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const syncAuth = () => {
      const token = localStorage.getItem("token");
      const user = localStorage.getItem("user");
      setIsLoggedIn(!!token);
      setIsAdmin(false);
      setUserName(null);
      if (user) {
        try {
          const userData: UserData = JSON.parse(user);
          setIsAdmin(userData.role === "admin");
          if (userData.full_name) {
            setUserName(userData.full_name.split(" ")[0]);
          }
        } catch {
          /* ignore */
        }
      }
    };

    syncAuth();
    setMounted(true);
    window.addEventListener("storage", syncAuth);
    window.addEventListener("auth-change", syncAuth);
    return () => {
      window.removeEventListener("storage", syncAuth);
      window.removeEventListener("auth-change", syncAuth);
    };
  }, []);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 8);
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("refreshToken");
    localStorage.removeItem("user");
    setIsLoggedIn(false);
    setIsAdmin(false);
    setUserName(null);
    window.location.href = "/";
  };

  return (
    <header
      className={`sticky top-0 z-50 w-full transition-all duration-300 ${scrolled
          ? "border-b bg-white/95 shadow-sm backdrop-blur supports-[backdrop-filter]:bg-white/80"
          : "bg-white/0"
        }`}
    >
      <div className="container flex h-20 items-center justify-between">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-3 shrink-0" aria-label="Ana Sayfa — Benim Masalım">
          <Image
            src="/logo.jpg"
            alt="Benim Masalım"
            width={68}
            height={68}
            className="h-16 w-16 object-contain drop-shadow-sm"
            priority
          />
          <span className="text-2xl font-bold text-slate-900">
            Benim <span className="text-primary">Masalım</span>
          </span>
        </Link>

        {/* Desktop Nav */}
        <nav className="hidden items-center gap-5 md:flex" aria-label="Ana menü">
          {navLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="text-sm font-medium text-slate-600 transition-colors hover:text-primary"
            >
              {link.label}
            </Link>
          ))}
        </nav>

        {/* Desktop Actions */}
        <div className="hidden items-center gap-2 md:flex">
          {mounted ? (
            <>
              {isAdmin && (
                <Link href="/admin">
                  <Button variant="ghost" size="sm" className="gap-1.5 text-slate-600">
                    <LayoutDashboard className="h-4 w-4" />
                    Admin
                  </Button>
                </Link>
              )}
              {isLoggedIn ? (
                <>
                  <Link href="/account">
                    <Button variant="ghost" size="sm" className="gap-1.5 text-slate-600">
                      <UserCircle className="h-4 w-4" />
                      {userName ?? "Hesabım"}
                    </Button>
                  </Link>
                  <Button variant="ghost" size="sm" className="gap-1.5 text-slate-500" onClick={handleLogout}>
                    <LogOut className="h-4 w-4" />
                    Çıkış
                  </Button>
                </>
              ) : (
                <Link href="/auth/login">
                  <Button variant="ghost" size="sm">
                    Giriş Yap
                  </Button>
                </Link>
              )}
            </>
          ) : (
            // Skeleton during hydration to prevent layout shift
            <div className="h-8 w-20 animate-pulse rounded-md bg-slate-100" aria-hidden="true" />
          )}
          <Link href="/create-v2">
            <Button size="sm" className="gap-1.5 bg-gradient-to-r from-purple-600 to-pink-500 text-white shadow-sm hover:from-purple-700 hover:to-pink-600">
              Kitap Oluştur
            </Button>
          </Link>
        </div>

        {/* Mobile Nav */}
        <div className="flex items-center gap-2 md:hidden">
          <Link href="/create-v2">
            <Button
              size="sm"
              className="gap-1 bg-gradient-to-r from-purple-600 to-pink-500 text-white text-xs px-3 hover:from-purple-700 hover:to-pink-600"
            >
              Kitap Oluştur
            </Button>
          </Link>
          <Sheet>
            <SheetTrigger asChild>
              <Button variant="ghost" size="icon" aria-label="Menüyü aç" className="h-10 w-10">
                <Menu className="h-5 w-5" />
              </Button>
            </SheetTrigger>
            <SheetContent side="right" className="w-72 pt-8">
              <SheetHeader className="mb-6">
                <SheetTitle className="flex items-center gap-2.5">
                  <Image
                    src="/logo.jpg"
                    alt="Benim Masalım"
                    width={44}
                    height={44}
                    className="h-11 w-11 object-contain"
                  />
                  <span>
                    Benim <span className="text-primary">Masalım</span>
                  </span>
                </SheetTitle>
              </SheetHeader>

              <nav className="flex flex-col gap-1" aria-label="Mobil menü">
                {navLinks.map((link) => (
                  <SheetClose asChild key={link.href}>
                    <Link
                      href={link.href}
                      className="flex h-11 items-center rounded-lg px-3 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50 hover:text-primary"
                    >
                      {link.label}
                    </Link>
                  </SheetClose>
                ))}

                {mounted && isAdmin && (
                  <SheetClose asChild>
                    <Link
                      href="/admin"
                      className="flex h-11 items-center gap-2 rounded-lg px-3 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50"
                    >
                      <LayoutDashboard className="h-4 w-4 text-slate-400" />
                      Admin Panel
                    </Link>
                  </SheetClose>
                )}

                {mounted && isLoggedIn && (
                  <SheetClose asChild>
                    <Link
                      href="/account"
                      className="flex h-11 items-center gap-2 rounded-lg px-3 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50"
                    >
                      <UserCircle className="h-4 w-4 text-slate-400" />
                      {userName ? `${userName} — Hesabım` : "Hesabım"}
                    </Link>
                  </SheetClose>
                )}
              </nav>

              <div className="mt-6 flex flex-col gap-2 border-t pt-6">
                <SheetClose asChild>
                  <Link href="/create-v2" className="block">
                    <Button className="w-full gap-2 bg-gradient-to-r from-purple-600 to-pink-500 text-white hover:from-purple-700 hover:to-pink-600">
                      Kitap Oluştur
                    </Button>
                  </Link>
                </SheetClose>
                {mounted ? (
                  isLoggedIn ? (
                    <Button variant="outline" className="w-full gap-2" onClick={handleLogout}>
                      <LogOut className="h-4 w-4" />
                      Çıkış Yap
                    </Button>
                  ) : (
                    <SheetClose asChild>
                      <Link href="/auth/login" className="block">
                        <Button variant="outline" className="w-full">
                          Giriş Yap
                        </Button>
                      </Link>
                    </SheetClose>
                  )
                ) : null}
              </div>
            </SheetContent>
          </Sheet>
        </div>
      </div>
    </header>
  );
}
