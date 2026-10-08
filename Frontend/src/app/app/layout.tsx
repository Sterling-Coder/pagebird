import { TrialBanner } from "@/components/app/TrialBanner";
import { AppShell } from "@/components/app/AppShell";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-full flex-col">
      <TrialBanner />
      <AppShell>{children}</AppShell>
    </div>
  );
}
