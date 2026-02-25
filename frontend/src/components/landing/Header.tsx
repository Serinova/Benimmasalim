"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
  SheetClose,
} from "@/components/ui/sheet";
import { BookOpen, Menu } from "lucide-react";

const navLinks = [
  { href: "#nasil-calisir", label: "Nasıl Çalışır?" },
  { href: "#ornekler", label: "Örnekler" },
  { href: "#fiyat", label: "Fiyat" },
  { href: "#sss", label: "SSS" },
  { href: "/contact", label: "İletişim" },
];

export default function Header() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [isAdmin, setIsAdmin] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem("token");
    const user = localStorage.getItem("user");
    setIsLoggedIn(!!token);
    if (user) {
      try {
        const userData = JSON.parse(user);
        setIsAdmin(userData.role === "admin");
      } catch {
        /* ignore */
      }
    }
  }, []);

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    setIsLoggedIn(false);
    setIsAdmin(false);
  };

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-16 items-center justify-between">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2" aria-label="Ana Sayfa">
          <BookOpen className="h-6 w-6 text-primary" />
          <span className="text-xl font-bold">Benim Masalım</span>
        </Link>

        {/* Desktop Nav */}
        <nav className="hidden items-center gap-6 md:flex" aria-label="Ana menü">
          {navLinks.map((link) =>
            link.href.startsWith("/") ? (
              <Link
                key={link.href}
                href={link.href}
                className="text-sm font-medium text-muted-foreground transition-colors hover:text-primary"
              >
                {link.label}
              </Link>
            ) : (
              <a
                key={link.href}
                href={link.href}
                className="text-sm font-medium text-muted-foreground transition-colors hover:text-primary"
              >
                {link.label}
              </a>
            )
          )}
          {isAdmin && (
            <Link href="/admin" className="text-sm font-medium text-muted-foreground hover:text-primary">
              Admin
            </Link>
          )}
          {isLoggedIn ? (
            <Button variant="ghost" size="sm" onClick={handleLogout}>
              Çıkış Yap
            </Button>
          ) : (
            <Link href="/auth/login">
              <Button variant="ghost" size="sm">
                Giriş Yap
              </Button>
            </Link>
          )}
          <Link href="/create">
            <Button size="sm">Kitap Oluştur</Button>
          </Link>
        </nav>

        {/* Mobile Nav */}
        <div className="flex items-center gap-2 md:hidden">
          <Link href="/create">
            <Button size="sm">Kitap Oluştur</Button>
          </Link>
          <Sheet>
            <SheetTrigger asChild>
              <Button variant="ghost" size="icon" aria-label="Menüyü aç">
                <Menu className="h-5 w-5" />
              </Button>
            </SheetTrigger>
            <SheetContent side="right" className="w-72">
              <SheetHeader>
                <SheetTitle className="flex items-center gap-2">
                  <BookOpen className="h-5 w-5 text-primary" />
                  Benim Masalım
                </SheetTitle>
              </SheetHeader>
              <nav className="mt-8 flex flex-col gap-4" aria-label="Mobil menü">
                {navLinks.map((link) => (
                  <SheetClose asChild key={link.href}>
                    {link.href.startsWith("/") ? (
                      <Link
                        href={link.href}
                        className="rounded-md px-3 py-2 text-base font-medium transition-colors hover:bg-accent"
                      >
                        {link.label}
                      </Link>
                    ) : (
                      <a
                        href={link.href}
                        className="rounded-md px-3 py-2 text-base font-medium transition-colors hover:bg-accent"
                      >
                        {link.label}
                      </a>
                    )}
                  </SheetClose>
                ))}
                {isAdmin && (
                  <SheetClose asChild>
                    <Link
                      href="/admin"
                      className="rounded-md px-3 py-2 text-base font-medium transition-colors hover:bg-accent"
                    >
                      Admin Panel
                    </Link>
                  </SheetClose>
                )}
                <div className="mt-4 border-t pt-4">
                  {isLoggedIn ? (
                    <Button variant="outline" className="w-full" onClick={handleLogout}>
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
                  )}
                </div>
              </nav>
            </SheetContent>
          </Sheet>
        </div>
      </div>
    </header>
  );
}
