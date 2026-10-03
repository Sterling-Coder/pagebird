import type { Metadata } from "next";
import { Fraunces, Space_Mono, Inter, Share_Tech_Mono } from "next/font/google";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { DemoVideoButton } from "@/components/DemoVideoButton";

export const metadata: Metadata = {
  title: "Pagebirdy — Document translation that keeps the document",
  description:
    "Pagebirdy translates InDesign (IDML) files into 40+ languages and returns them with every font, column, table, footnote and page break exactly where it was — plus PDF, subtitles and more.",
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

const shareTechMono = Share_Tech_Mono({
  variable: "--font-share-tech-mono",
  subsets: ["latin"],
  weight: ["400"],
});

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700", "800"],
});

export default function MarketingLayout({ children }: { children: React.ReactNode }) {
  return (
    <div
      className={`${fraunces.variable} ${spaceMono.variable} ${shareTechMono.variable} ${inter.variable} relative flex min-h-screen shrink-0 flex-col bg-pb-bg text-pb-text antialiased`}
    >
      {/* Full-page vertical grid lines — fixed overlay like giga.ai */}
      <div className="pointer-events-none fixed inset-0 z-10" aria-hidden="true">
        <div className="mx-auto grid h-full max-w-[1100px] grid-cols-4 px-8 lg:grid-cols-8 lg:px-14">
          {Array.from({ length: 8 }).map((_, i) => (
            <div
              key={i}
              style={{
                borderLeft: "1px solid rgba(255,255,255,0.04)",
                borderRight: i === 7 ? "1px solid rgba(255,255,255,0.04)" : undefined,
              }}
            />
          ))}
        </div>
      </div>

      <Header />
      <main className="relative z-0 flex-1">{children}</main>
      <Footer />
      <DemoVideoButton />
    </div>
  );
}
