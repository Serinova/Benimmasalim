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
  { name: "AyÅŸe Y.", badge: "DoÄŸrulanmÄ±ÅŸ AlÄ±cÄ±", rating: 5, text: "KÄ±zÄ±mÄ±n doÄŸum gÃ¼nÃ¼ iÃ§in sipariÅŸ verdik. KitabÄ± gÃ¶rÃ¼nce gÃ¶zleri parladÄ±! Kendi adÄ±nÄ± ve fotoÄŸrafÄ±nÄ± kitapta gÃ¶rmek onu Ã§ok mutlu etti." },
  { name: "Mehmet K.", badge: "DoÄŸrulanmÄ±ÅŸ AlÄ±cÄ±", rating: 5, text: "YeÄŸenime hediye olarak aldÄ±m. Ailesi Ã§ok beÄŸendi. BaskÄ± kalitesi beklediÄŸimden Ã§ok daha iyi. Herkese tavsiye ederim." },
  { name: "Elif D.", badge: "DoÄŸrulanmÄ±ÅŸ AlÄ±cÄ±", rating: 5, text: "OÄŸlum her gece bu kitabÄ± okumamÄ± istiyor. Hikaye gerÃ§ekten kiÅŸiselleÅŸtirilmiÅŸ, hazÄ±r ÅŸablon deÄŸil. Ã‡ok etkileyici bir deneyim." },
];

function StarRating({ rating }: { rating: number }) {
  return (
    <div className="flex gap-0.5" aria-label={`${rating} yÄ±ldÄ±z`}>
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
  const sub = subtitle ?? "Binlerce aile Ã§ocuklarÄ±na Ã¶zel hikaye kitaplarÄ± ile mutlu.";
  const items = (data?.items ?? DEFAULT_ITEMS) as TestimonialItem[];

  return (
    <section className="bg-white py-20 md:py-28">
      <div className="container">
        <div className="mx-auto mb-16 max-w-2xl text-center">
          <h2 className="text-3xl font-extrabold tracking-tight text-slate-900 sm:text-4xl">{heading}</h2>
          <p className="mt-4 text-lg text-slate-500">{sub}</p>
        </div>

        <div className="mx-auto grid max-w-5xl gap-5 md:grid-cols-3">
          {items.map((t) => (
            <article key={t.name} className="flex flex-col rounded-2xl border border-slate-200 bg-slate-50 p-6 shadow-sm">
              <StarRating rating={t.rating} />
              <p className="mt-4 flex-1 text-sm leading-relaxed text-slate-700">&ldquo;{t.text}&rdquo;</p>
              <div className="mt-4 border-t border-slate-200 pt-4">
                <p className="text-sm font-bold text-slate-900">{t.name}</p>
                <p className="text-xs text-emerald-600">{t.badge}</p>
              </div>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
