import { HomeHero } from "@/components/HomeHero";
import { ProductTeaserGrid } from "@/components/ProductTeaserGrid";
import { HandoffSection } from "@/components/HandoffSection";
import { CTABand } from "@/components/CTABand";
import { Footer } from "@/components/Footer";

export default function Home() {
  return (
    <>
      <HomeHero />
      <ProductTeaserGrid />
      <HandoffSection />
      <CTABand />
      <Footer />
    </>
  );
}
