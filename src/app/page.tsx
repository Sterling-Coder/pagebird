import { Hero } from "@/components/Hero";
import { ProductTeaserGrid } from "@/components/ProductTeaserGrid";
import { HandoffSection } from "@/components/HandoffSection";
import { CTABand } from "@/components/CTABand";
import { Footer } from "@/components/Footer";

export default function Home() {
  return (
    <>
      <Hero />
      <ProductTeaserGrid />
      <HandoffSection />
      <CTABand />
      <Footer />
    </>
  );
}
