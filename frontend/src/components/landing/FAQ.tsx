"use client";

import * as Accordion from "@radix-ui/react-accordion";
import { ChevronDown } from "lucide-react";
import { cn } from "@/lib/utils";
import { DEFAULT_FAQ_ITEMS, type FAQItem } from "@/lib/homepage-defaults";

interface FAQProps {
  title?: string;
  subtitle?: string;
  data?: { items?: FAQItem[] };
}

export default function FAQ({ title, subtitle, data }: FAQProps) {
  const heading = title ?? "Sıkça Sorulan Sorular";
  const sub = subtitle ?? "Merak ettiğiniz her şeyin yanıtı burada.";
  const items = (data?.items ?? DEFAULT_FAQ_ITEMS) as FAQItem[];

  return (
    <section id="sss" className="scroll-mt-20 bg-muted/30 py-20">
      <div className="container">
        <div className="mx-auto mb-16 max-w-2xl text-center">
          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">{heading}</h2>
          <p className="mt-4 text-lg text-muted-foreground">{sub}</p>
        </div>

        <div className="mx-auto max-w-2xl">
          <Accordion.Root type="single" collapsible className="space-y-3">
            {items.map((item, index) => (
              <Accordion.Item key={index} value={`faq-${index}`} className="overflow-hidden rounded-lg border bg-card shadow-sm">
                <Accordion.Header>
                  <Accordion.Trigger
                    className={cn(
                      "flex w-full items-center justify-between px-6 py-4 text-left text-sm font-semibold transition-all hover:bg-accent/50",
                      "[&[data-state=open]>svg]:rotate-180"
                    )}
                  >
                    {item.question}
                    <ChevronDown className="h-4 w-4 shrink-0 text-muted-foreground transition-transform duration-200" />
                  </Accordion.Trigger>
                </Accordion.Header>
                <Accordion.Content className="overflow-hidden data-[state=closed]:animate-accordion-up data-[state=open]:animate-accordion-down">
                  <div className="px-6 pb-4 text-sm leading-relaxed text-muted-foreground">{item.answer}</div>
                </Accordion.Content>
              </Accordion.Item>
            ))}
          </Accordion.Root>
        </div>
      </div>
    </section>
  );
}
