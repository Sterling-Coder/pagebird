import { Hero } from "@/components/Hero";
import { HandoffSection } from "@/components/HandoffSection";
import { DemoSection } from "@/components/DemoSection";
import { HowItWorks } from "@/components/HowItWorks";
import { FormatsStrip } from "@/components/FormatsStrip";
import { AccuracyBand } from "@/components/AccuracyBand";
import { PricingSection } from "@/components/PricingSection";
import { LanguageGrid } from "@/components/LanguageGrid";
import { CTABand } from "@/components/CTABand";

export default function Home() {
  return (
    <>
      <Hero />
      <HandoffSection />
      <DemoSection />
      <HowItWorks />
      <FormatsStrip />
      <AccuracyBand />
      <PricingSection />
      <LanguageGrid />
      <CTABand />
    </>
  );
}
