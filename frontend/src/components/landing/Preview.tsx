"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import Image from "next/image";
import { BookOpen, ChevronLeft, ChevronRight } from "lucide-react";

interface PreviewItem {
  title: string;
  description: string;
  color?: string;
  image?: string;
}

interface PreviewProps {
  title?: string;
  subtitle?: string;
  data?: { items?: PreviewItem[] };
}

const DEFAULT_ITEMS: PreviewItem[] = [
  { title: "Kapak Sayfası", description: "Çocuğunuzun adıyla kişiselleştirilmiş kapak tasarımı", color: "from-purple-100 to-pink-100" },
  { title: "Hikaye Sayfası", description: "Renkli illüstrasyonlarla zenginleştirilmiş sayfalar", color: "from-blue-100 to-cyan-100" },
  { title: "Karakter Sayfası", description: "Çocuğunuzun fotoğrafıyla oluşturulan kahraman", color: "from-amber-100 to-orange-100" },
  { title: "Son Sayfa", description: "Eğitici mesajla biten anlamlı bir kapanış", color: "from-green-100 to-emerald-100" },
];

export default function Preview({ title, subtitle, data }: PreviewProps) {
  const heading = title ?? "Örnek Kitap Sayfaları";
  const sub = subtitle ?? "Her kitap benzersiz ve çocuğunuza özel olarak oluşturulur.";
  const items = (data?.items ?? DEFAULT_ITEMS) as PreviewItem[];

  const scrollRef = useRef<HTMLDivElement>(null);
  const [canScrollLeft, setCanScrollLeft] = useState(false);
  const [canScrollRight, setCanScrollRight] = useState(false);
  const [activeIndex, setActiveIndex] = useState(0);

  const checkScroll = useCallback(() => {
    const el = scrollRef.current;
    if (!el) return;
    setCanScrollLeft(el.scrollLeft > 4);
    setCanScrollRight(el.scrollLeft + el.clientWidth < el.scrollWidth - 4);
    const card = el.querySelector("[data-preview-card]");
    if (card) {
      const cardWidth = card.clientWidth + 24;
      setActiveIndex(Math.round(el.scrollLeft / cardWidth));
    }
  }, []);

  useEffect(() => {
    checkScroll();
    const el = scrollRef.current;
    if (!el) return;
    el.addEventListener("scroll", checkScroll, { passive: true });
    window.addEventListener("resize", checkScroll);
    return () => {
      el.removeEventListener("scroll", checkScroll);
      window.removeEventListener("resize", checkScroll);
    };
  }, [checkScroll, items.length]);

  const scroll = (direction: "left" | "right") => {
    const el = scrollRef.current;
    if (!el) return;
    const cardWidth = el.querySelector("[data-preview-card]")?.clientWidth ?? 280;
    const gap = 24;
    const distance = cardWidth + gap;
    el.scrollBy({ left: direction === "left" ? -distance : distance, behavior: "smooth" });
  };

  return (
    <section id="ornekler" className="scroll-mt-20 py-20">
      <div className="container">
        <div className="mx-auto mb-12 max-w-2xl text-center">
          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">{heading}</h2>
          <p className="mt-4 text-lg text-muted-foreground">{sub}</p>
        </div>

        {/* Carousel container */}
        <div className="relative mx-auto max-w-6xl">
          {/* Left arrow */}
          {canScrollLeft && (
            <button
              onClick={() => scroll("left")}
              className="absolute -left-4 top-1/2 z-10 flex h-10 w-10 -translate-y-1/2 items-center justify-center rounded-full border bg-white shadow-lg transition-all hover:bg-indigo-50 hover:shadow-xl sm:-left-5"
              aria-label="Önceki sayfalar"
            >
              <ChevronLeft className="h-5 w-5 text-slate-700" />
            </button>
          )}

          {/* Right arrow */}
          {canScrollRight && (
            <button
              onClick={() => scroll("right")}
              className="absolute -right-4 top-1/2 z-10 flex h-10 w-10 -translate-y-1/2 items-center justify-center rounded-full border bg-white shadow-lg transition-all hover:bg-indigo-50 hover:shadow-xl sm:-right-5"
              aria-label="Sonraki sayfalar"
            >
              <ChevronRight className="h-5 w-5 text-slate-700" />
            </button>
          )}

          {/* Scrollable row */}
          <div
            ref={scrollRef}
            className="scrollbar-none flex gap-6 overflow-x-auto scroll-smooth px-1 pb-4"
            style={{ scrollSnapType: "x mandatory" }}
          >
            {items.map((page, i) => (
              <div
                key={`${page.title}-${i}`}
                data-preview-card
                className="group w-[260px] flex-shrink-0 overflow-hidden rounded-xl border shadow-sm transition-all hover:shadow-lg sm:w-[280px]"
                style={{ scrollSnapAlign: "start" }}
              >
                {/* Image or gradient placeholder */}
                <div className="relative aspect-[3/4] overflow-hidden">
                  {page.image ? (
                    <Image
                      src={page.image}
                      alt={`${page.title} — örnek kitap sayfası`}
                      fill
                      sizes="(max-width: 640px) 260px, 280px"
                      className="object-cover transition-transform duration-300 group-hover:scale-105"
                      loading="lazy"
                    />
                  ) : (
                    <div
                      className={`flex h-full w-full items-center justify-center bg-gradient-to-br ${page.color ?? "from-slate-100 to-slate-200"}`}
                    >
                      <div className="flex flex-col items-center gap-2 text-primary/30">
                        <BookOpen className="h-10 w-10" />
                        <span className="text-xs font-medium">{page.title}</span>
                      </div>
                    </div>
                  )}
                </div>
                {/* Caption */}
                <div className="p-4">
                  <h3 className="text-sm font-semibold">{page.title}</h3>
                  <p className="mt-1 text-xs text-muted-foreground">{page.description}</p>
                </div>
              </div>
            ))}
          </div>

          {/* Scroll indicators (dots) */}
          {items.length > 1 && (
            <div className="mt-4 flex justify-center gap-1.5" role="tablist" aria-label="Sayfa göstergesi">
              {items.map((item, i) => (
                <button
                  key={`dot-${item.title}-${i}`}
                  role="tab"
                  aria-selected={i === activeIndex}
                  aria-label={`Sayfa ${i + 1}: ${item.title}`}
                  onClick={() => {
                    const el = scrollRef.current;
                    if (!el) return;
                    const card = el.querySelector("[data-preview-card]");
                    if (card) {
                      el.scrollTo({ left: i * (card.clientWidth + 24), behavior: "smooth" });
                    }
                  }}
                  className={`h-2 rounded-full transition-all ${
                    i === activeIndex ? "w-6 bg-primary" : "w-2 bg-slate-300 hover:bg-slate-400"
                  }`}
                />
              ))}
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
