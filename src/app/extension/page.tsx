import { ExtensionHero } from "@/components/ExtensionHero";
import { ExtensionDemo } from "@/components/ExtensionDemo";
import { ExtensionHowItWorks } from "@/components/ExtensionHowItWorks";
import { CTABand } from "@/components/CTABand";
import { Footer } from "@/components/Footer";

export default function ExtensionPage() {
  return (
    <>
      <ExtensionHero />
      <ExtensionDemo />
      <ExtensionHowItWorks />
      <CTABand />
      <Footer />
    </>
  );
}
