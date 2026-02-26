"use client";

import Link from "next/link";
import Image from "next/image";
import { Star, Clock, Users, ArrowRight, Sparkles, BookOpen } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { ScenarioForHomepage } from "@/lib/homepage";

interface AdventuresProps {
  title?: string;
  subtitle?: string;
  scenarios: ScenarioForHomepage[];
}

function StarRating({ rating, count }: { rating: number; count: number }) {
  return (
    <div className="flex items-center gap-1.5">
      <div className="flex items-center gap-0.5">
        {Array.from({ length: 5 }).map((_, i) => (
          <Star
            key={i}
            className={`h-3.5 w-3.5 ${i < Math.round(rating) ? "fill-amber-400 text-amber-400" : "text-slate-200"
              }`}
          />
        ))}
      </div>
      <span className="text-xs font-medium text-slate-600">{rating.toFixed(1)}</span>
      {count > 0 && (
        <span className="text-xs text-muted-foreground">({count})</span>
      )}
    </div>
  );
}

function ScenarioCard({ scenario }: { scenario: ScenarioForHomepage }) {
  const href = `/create-v2?scenario=${scenario.id}`;

  return (
    <div className="group relative flex flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm transition-all duration-300 hover:-translate-y-1 hover:shadow-xl">
      {/* Badge */}
      {scenario.marketing_badge && (
        <div className="absolute left-3 top-3 z-10">
          <span className="rounded-full bg-gradient-to-r from-purple-600 to-pink-500 px-3 py-1 text-xs font-bold text-white shadow-md">
            {scenario.marketing_badge}
          </span>
        </div>
      )}

      {/* Thumbnail */}
      <div className="relative aspect-[4/3] overflow-hidden bg-gradient-to-br from-purple-100 to-pink-100">
        {scenario.thumbnail_url ? (
          <Image
            src={scenario.thumbnail_url}
            alt={scenario.name}
            fill
            className="object-cover transition-transform duration-500 group-hover:scale-105"
            sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
          />
        ) : (
          <div className="flex h-full items-center justify-center">
            <BookOpen className="h-16 w-16 text-purple-300" />
          </div>
        )}
        {/* Gradient overlay */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/20 to-transparent" />
      </div>

      {/* Content */}
      <div className="flex flex-1 flex-col p-5">
        <h3 className="text-lg font-bold text-slate-900 group-hover:text-purple-700 transition-colors">
          {scenario.name}
        </h3>

        {scenario.tagline && (
          <p className="mt-1 text-sm text-slate-500 line-clamp-2">{scenario.tagline}</p>
        )}

        {/* Meta */}
        <div className="mt-3 flex flex-wrap gap-3 text-xs text-slate-500">
          {scenario.age_range && (
            <span className="flex items-center gap-1">
              <Users className="h-3.5 w-3.5 text-purple-400" />
              {scenario.age_range}
            </span>
          )}
          {scenario.estimated_duration && (
            <span className="flex items-center gap-1">
              <Clock className="h-3.5 w-3.5 text-blue-400" />
              {scenario.estimated_duration}
            </span>
          )}
          {(scenario.total_page_count ?? scenario.default_page_count) && (
            <span className="flex items-center gap-1">
              <BookOpen className="h-3.5 w-3.5 text-emerald-400" />
              {scenario.total_page_count ?? scenario.default_page_count} sayfa
            </span>
          )}
        </div>

        {/* Rating */}
        {scenario.rating && scenario.rating > 0 && (
          <div className="mt-3">
            <StarRating rating={scenario.rating} count={scenario.review_count ?? 0} />
          </div>
        )}

        {/* Features */}
        {scenario.marketing_features && scenario.marketing_features.length > 0 && (
          <ul className="mt-3 space-y-1">
            {scenario.marketing_features.slice(0, 3).map((f) => (
              <li key={f} className="flex items-start gap-1.5 text-xs text-slate-600">
                <span className="mt-0.5 h-1.5 w-1.5 shrink-0 rounded-full bg-purple-400" />
                {f}
              </li>
            ))}
          </ul>
        )}

        {/* Price + CTA */}
        <div className="mt-auto pt-4">
          {scenario.marketing_price_label && (
            <p className="mb-2 text-sm font-semibold text-purple-700">
              {scenario.marketing_price_label}
            </p>
          )}
          <Link href={href} className="block">
            <Button
              size="sm"
              className="w-full gap-2 bg-gradient-to-r from-purple-600 to-pink-500 text-white hover:from-purple-700 hover:to-pink-600"
            >
              <Sparkles className="h-4 w-4" />
              Bu Maceraya Başla
              <ArrowRight className="h-4 w-4" />
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
}

export default function Adventures({ title, subtitle, scenarios }: AdventuresProps) {
  if (!scenarios || scenarios.length === 0) return null;

  return (
    <section id="maceralar" className="scroll-mt-20 bg-gradient-to-b from-white to-purple-50/30 py-20">
      <div className="container">
        {/* Header */}
        <div className="mx-auto mb-12 max-w-2xl text-center">
          <div className="mb-4 inline-flex items-center gap-2 rounded-full bg-purple-100 px-4 py-1.5 text-sm font-medium text-purple-700">
            <Sparkles className="h-4 w-4" />
            Macera Seç, Hikaye Başlasın
          </div>
          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
            {title ?? "Hangi Maceraya Çıkmak İstiyorsunuz?"}
          </h2>
          <p className="mt-4 text-lg text-muted-foreground">
            {subtitle ??
              "Her senaryo çocuğunuza özel, eğitici ve eğlenceli bir hikaye dünyası sunar. Beğendiğinizi seçin, gerisini biz halledelim."}
          </p>
        </div>

        {/* Scenario Grid */}
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {scenarios.map((scenario) => (
            <ScenarioCard key={scenario.id} scenario={scenario} />
          ))}
        </div>

        {/* Bottom CTA */}
        <div className="mt-12 text-center">
          <p className="mb-4 text-sm text-muted-foreground">
            Hangi maceradan başlayacağınıza karar veremediniz mi?
          </p>
          <Link href="/create-v2">
            <Button variant="outline" size="lg" className="gap-2 border-purple-200 text-purple-700 hover:bg-purple-50">
              <BookOpen className="h-5 w-5" />
              Tüm Seçenekleri Gör
            </Button>
          </Link>
        </div>
      </div>
    </section>
  );
}
