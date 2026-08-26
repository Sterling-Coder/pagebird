import { AppNavRail } from "@/components/app/AppNavRail";
import { AppTopBar } from "@/components/app/AppTopBar";
import { TranslateWorkspace } from "@/components/app/TranslateWorkspace";
import { AppSidebar } from "@/components/app/AppSidebar";

export default function AppWorkspacePage() {
  return (
    <div className="flex h-screen bg-paper">
      <AppNavRail />
      <div className="flex min-w-0 flex-1 flex-col">
        <AppTopBar />
        <div className="flex min-h-0 flex-1">
          <TranslateWorkspace />
          <AppSidebar />
        </div>
      </div>
    </div>
  );
}
