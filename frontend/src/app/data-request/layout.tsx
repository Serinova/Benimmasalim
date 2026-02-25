import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "KVKK Veri Talebi",
  description:
    "Benim Masalım — KVKK kapsamındaki haklarınızı kullanmak için veri talebi formu.",
};

export default function DataRequestLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
