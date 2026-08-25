import { ExtensionHero } from "@/components/ExtensionHero";
import { ExtensionDemo } from "@/components/ExtensionDemo";
import { ExtensionHowItWorks } from "@/components/ExtensionHowItWorks";
import { CTABand } from "@/components/CTABand";

export default function ExtensionPage() {
  return (
    <>
      <ExtensionHero />
      <ExtensionDemo />
      <ExtensionHowItWorks />
      <CTABand />
    </>
  );
}
