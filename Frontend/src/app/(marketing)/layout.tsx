import type { Metadata } from "next";
import { Fraunces, Space_Mono, Inter } from "next/font/google";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { DemoVideoButton } from "@/components/DemoVideoButton";
import { ParallaxCurves } from "@/components/ParallaxCurves";

export const metadata: Metadata = {
  title: "Pagebird — Document translation that keeps the document",
  description:
    "Pagebird translates DOCX, PDF, PPTX and InDesign files into 40+ languages and returns them with every column, table, footnote and page break exactly where it was.",
};

const fraunces = Fraunces({
  variable: "--font-fraunces",
  subsets: ["latin"],
  weight: ["500", "600"],
  style: ["normal", "italic"],
});

const spaceMono = Space_Mono({
  variable: "--font-space-mono",
  subsets: ["latin"],
  weight: ["400", "700"],
});

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700", "800"],
});

export default function MarketingLayout({ children }: { children: React.ReactNode }) {
  return (
    <div
      className={`${fraunces.variable} ${spaceMono.variable} ${inter.variable} relative flex min-h-full flex-1 flex-col bg-pb-paper text-pb-ink antialiased`}
    >
      <ParallaxCurves />

      <Header />
      <main className="flex-1">{children}</main>
      <Footer />
      <DemoVideoButton />
    </div>
  );
}
