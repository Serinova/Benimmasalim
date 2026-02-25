import { Star } from "lucide-react";

interface TestimonialItem {
  name: string;
  badge: string;
  rating: number;
  text: string;
}

interface TestimonialsProps {
  title?: string;
  subtitle?: string;
  data?: { items?: TestimonialItem[] };
}

const DEFAULT_ITEMS: TestimonialItem[] = [
  { name: "Ayşe Y.", badge: "Doğrulanmış Alıcı", rating: 5, text: "Kızımın doğum günü için sipariş verdik. Kitabı görünce gözleri parladı! Kendi adını ve fotoğrafını kitapta görmek onu çok mutlu etti." },
  { name: "Mehmet K.", badge: "Doğrulanmış Alıcı", rating: 5, text: "Yeğenime hediye olarak aldım. Ailesi çok beğendi. Baskı kalitesi beklediğimden çok daha iyi. Herkese tavsiye ederim." },
  { name: "Elif D.", badge: "Doğrulanmış Alıcı", rating: 5, text: "Oğlum her gece bu kitabı okumamı istiyor. Hikaye gerçekten kişiselleştirilmiş, hazır şablon değil. Çok etkileyici bir deneyim." },
];

function StarRating({ rating }: { rating: number }) {
  return (
    <div className="flex gap-0.5" aria-label={`${rating} yıldız`}>
      {Array.from({ length: 5 }).map((_, i) => (
        <Star
          key={i}
          className={`h-4 w-4 ${i < rating ? "fill-amber-400 text-amber-400" : "text-muted-foreground/30"}`}
        />
      ))}
    </div>
  );
}

export default function Testimonials({ title, subtitle, data }: TestimonialsProps) {
  const heading = title ?? "Aileler Ne Diyor?";
  const sub = subtitle ?? "Binlerce aile çocuklarına özel hikaye kitapları ile mutlu.";
  const items = (data?.items ?? DEFAULT_ITEMS) as TestimonialItem[];

  return (
    <section className="bg-muted/30 py-20">
      <div className="container">
        <div className="mx-auto mb-16 max-w-2xl text-center">
          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">{heading}</h2>
          <p className="mt-4 text-lg text-muted-foreground">{sub}</p>
        </div>

        <div className="mx-auto grid max-w-5xl gap-6 md:grid-cols-3">
          {items.map((t) => (
            <article key={t.name} className="flex flex-col rounded-xl border bg-card p-6 shadow-sm">
              <StarRating rating={t.rating} />
              <blockquote className="mt-4 flex-1 text-sm leading-relaxed text-muted-foreground">
                &ldquo;{t.text}&rdquo;
              </blockquote>
              <div className="mt-6 flex items-center gap-3 border-t pt-4">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10 text-sm font-bold text-primary">
                  {t.name.charAt(0)}
                </div>
                <div>
                  <p className="text-sm font-semibold">{t.name}</p>
                  <p className="text-xs text-muted-foreground">{t.badge}</p>
                </div>
              </div>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
