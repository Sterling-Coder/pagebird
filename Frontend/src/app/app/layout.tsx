import { TrialBanner } from "@/components/app/TrialBanner";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-full flex-col">
      <TrialBanner />
      <div className="flex min-h-0 flex-1">{children}</div>
    </div>
  );
}
