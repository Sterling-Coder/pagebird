import { HomeHero } from "@/components/HomeHero";
import { ProductTeaserGrid } from "@/components/ProductTeaserGrid";
import { HandoffSection } from "@/components/HandoffSection";
import { PricingSection } from "@/components/PricingSection";
import { CTABand } from "@/components/CTABand";

export default function Home() {
  return (
    <>
      <HomeHero />
      <ProductTeaserGrid />
      <HandoffSection />
      <PricingSection variant="teaser" />
      <CTABand />
    </>
  );
}
