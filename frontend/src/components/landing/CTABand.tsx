import Link from "next/link";
import { Button } from "@/components/ui/button";
import { ArrowRight, Sparkles } from "lucide-react";

interface CTABandProps {
  title?: string;
  subtitle?: string;
  data?: { cta_text?: string; cta_url?: string };
}

export default function CTABand({ title, subtitle, data }: CTABandProps) {
  const heading = title ?? "Çocuğunuza Özel Bir Masal Başlatıyor musunuz?";
  const sub = subtitle ?? "Sadece birkaç dakikada çocuğunuza özel, unutulmaz bir hediye çocuk kitabı oluşturun.";
  const ctaText = data?.cta_text ?? "Şimdi Oluştur";
  const ctaUrl = data?.cta_url ?? "/create";

  return (
    <section className="relative overflow-hidden py-20">
      <div className="pointer-events-none absolute inset-0 bg-gradient-to-r from-primary/10 via-purple-500/10 to-primary/10" />
      <div className="container relative text-center">
        <Sparkles className="mx-auto mb-4 h-8 w-8 text-primary" />
        <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">{heading}</h2>
        <p className="mx-auto mt-4 max-w-lg text-lg text-muted-foreground">{sub}</p>
        <Link href={ctaUrl} className="mt-8 inline-block">
          <Button size="lg" className="magic-button gap-2 text-base">
            {ctaText}
            <ArrowRight className="h-4 w-4" />
          </Button>
        </Link>
      </div>
    </section>
  );
}
