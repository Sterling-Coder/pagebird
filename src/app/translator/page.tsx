import { Hero } from "@/components/Hero";
import { DemoSection } from "@/components/DemoSection";
import { HowItWorks } from "@/components/HowItWorks";
import { FormatsStrip } from "@/components/FormatsStrip";
import { AccuracyBand } from "@/components/AccuracyBand";
import { LanguageGrid } from "@/components/LanguageGrid";
import { CTABand } from "@/components/CTABand";

export default function TranslatorPage() {
  return (
    <>
      <Hero />
      <DemoSection />
      <HowItWorks />
      <FormatsStrip />
      <AccuracyBand />
      <LanguageGrid />
      <CTABand />
    </>
  );
}
