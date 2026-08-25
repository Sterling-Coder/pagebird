import { PricingSection } from "@/components/PricingSection";
import { PricingComparisonTable } from "@/components/PricingComparisonTable";
import { PricingFAQ } from "@/components/PricingFAQ";
import { CTABand } from "@/components/CTABand";

export default function PricingPage() {
  return (
    <>
      <PricingSection variant="full" />
      <PricingComparisonTable />
      <PricingFAQ />
      <CTABand />
    </>
  );
}
