import { TrialBanner } from "@/components/app/TrialBanner";
import { AppShell } from "@/components/app/AppShell";
import { Tour } from "@/components/app/Tour";
import { HelpButton } from "@/components/app/HelpButton";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-full flex-col">
      <TrialBanner />
      <AppShell>{children}</AppShell>
      <HelpButton />
      <Tour />
    </div>
  );
}
