import { UserPlus, Wand2, Package, type LucideIcon } from "lucide-react";

interface StepData {
  number: string;
  icon: string;
  title: string;
  description: string;
}

interface HowItWorksProps {
  title?: string;
  subtitle?: string;
  data?: { steps?: StepData[] };
}

const ICON_MAP: Record<string, LucideIcon> = { UserPlus, Wand2, Package };

const DEFAULT_STEPS: StepData[] = [
  { number: "1", icon: "UserPlus", title: "Bilgileri Girin", description: "Çocuğunuzun adını, fotoğrafını ve hikaye temasını seçin. Sadece birkaç dakika sürer." },
  { number: "2", icon: "Wand2", title: "Hikayenizi İnceleyin", description: "Yapay zeka çocuğunuza özel benzersiz bir hikaye oluşturur. İnceleyip düzenleyebilirsiniz." },
  { number: "3", icon: "Package", title: "Kapınıza Gelsin!", description: "Profesyonel baskı kalitesiyle hazırlanan kitabınız 2-3 iş günü içinde adresinize ulaşır." },
];

export default function HowItWorks({ title, subtitle, data }: HowItWorksProps) {
  const heading = title ?? "Nasıl Çalışır?";
  const sub = subtitle ?? "Üç kolay adımda çocuğunuza özel kişiselleştirilmiş masal kitabı oluşturun.";
  const steps = (data?.steps ?? DEFAULT_STEPS) as StepData[];

  return (
    <section id="nasil-calisir" className="scroll-mt-20 py-20">
      <div className="container">
        <div className="mx-auto mb-16 max-w-2xl text-center">
          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">{heading}</h2>
          <p className="mt-4 text-lg text-muted-foreground">{sub}</p>
        </div>

        <div className="relative mx-auto max-w-4xl">
          <div className="absolute left-1/2 top-12 hidden h-0.5 w-[60%] -translate-x-1/2 bg-gradient-to-r from-primary/20 via-primary/40 to-primary/20 md:block" />

          <div className="grid gap-8 md:grid-cols-3 md:gap-12">
            {steps.map((step) => {
              const Icon = ICON_MAP[step.icon] ?? UserPlus;
              return (
                <div key={step.number} className="relative flex flex-col items-center text-center">
                  <div className="relative mb-6 flex h-20 w-20 items-center justify-center rounded-full bg-primary/10 ring-4 ring-background">
                    <Icon className="h-8 w-8 text-primary" />
                    <span className="absolute -right-1 -top-1 flex h-7 w-7 items-center justify-center rounded-full bg-primary text-xs font-bold text-primary-foreground">
                      {step.number}
                    </span>
                  </div>
                  <h3 className="mb-2 text-xl font-semibold">{step.title}</h3>
                  <p className="text-sm leading-relaxed text-muted-foreground">{step.description}</p>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </section>
  );
}
