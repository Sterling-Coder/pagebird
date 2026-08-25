import { TranslatorHero } from "@/components/TranslatorHero";
import { DemoSection } from "@/components/DemoSection";
import { HowItWorks } from "@/components/HowItWorks";
import { FormatsStrip } from "@/components/FormatsStrip";
import { AccuracyBand } from "@/components/AccuracyBand";
import { LanguageGrid } from "@/components/LanguageGrid";
import { CTABand } from "@/components/CTABand";
import { Footer } from "@/components/Footer";

export default function TranslatorPage() {
  return (
    <>
      <TranslatorHero />
      <DemoSection />
      <HowItWorks />
      <FormatsStrip />
      <AccuracyBand />
      <LanguageGrid />
      <CTABand />
      <Footer />
    </>
  );
}
