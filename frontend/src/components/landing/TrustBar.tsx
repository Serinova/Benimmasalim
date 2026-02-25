import { Shield, Lock, Truck, Star, type LucideIcon } from "lucide-react";

interface TrustItem {
  icon: string;
  label: string;
  description: string;
}

interface TrustBarProps {
  data?: { items?: TrustItem[] };
}

const ICON_MAP: Record<string, LucideIcon> = {
  Shield,
  Lock,
  Truck,
  Star,
};

const DEFAULTS: TrustItem[] = [
  { icon: "Shield", label: "KVKK Uyumlu", description: "Veri güvenliği" },
  { icon: "Lock", label: "Güvenli Ödeme", description: "256-bit SSL" },
  { icon: "Truck", label: "Hızlı Teslimat", description: "2-3 iş günü" },
  { icon: "Star", label: "Memnuniyet", description: "4.9/5 puan" },
];

export default function TrustBar({ data }: TrustBarProps) {
  const items = (data?.items ?? DEFAULTS) as TrustItem[];

  return (
    <section className="border-y bg-muted/50" aria-label="Güven göstergeleri">
      <div className="container py-6">
        <ul className="grid grid-cols-2 gap-4 md:grid-cols-4 md:gap-8" role="list">
          {items.map((item) => {
            const Icon = ICON_MAP[item.icon] ?? Shield;
            return (
              <li key={item.label} className="flex items-center gap-3">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary/10" aria-hidden="true">
                  <Icon className="h-5 w-5 text-primary" />
                </div>
                <div>
                  <p className="text-sm font-semibold">{item.label}</p>
                  <p className="text-xs text-muted-foreground">{item.description}</p>
                </div>
              </li>
            );
          })}
        </ul>
      </div>
    </section>
  );
}
