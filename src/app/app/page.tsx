import { AppTopBar } from "@/components/app/AppTopBar";
import { AppSubToolbar } from "@/components/app/AppSubToolbar";
import { AppThumbnailRail } from "@/components/app/AppThumbnailRail";
import { AppDocumentPane } from "@/components/app/AppDocumentPane";
import { AppSidebar } from "@/components/app/AppSidebar";

const ORIGINAL = {
  title: "Field Ops Manual — Section 4",
  language: "English",
  sections: [
    {
      heading: "4.1 Deployment overview",
      body: "This section covers the standard rollout sequence for the staging environment, including pre-flight checks and the on-call escalation path.",
    },
    {
      heading: "4.2 Rollback procedure",
      body: "If a deployment fails validation, revert to the last known-good build and notify the on-call engineer within 15 minutes of detection.",
    },
    {
      heading: "4.3 Escalation contacts",
      body: "Critical failures route to the platform on-call rotation. See the escalation diagram on the following page for the full chain.",
    },
  ],
};

const TRANSLATED = {
  title: "現場運用マニュアル — セクション4",
  language: "Japanese",
  sections: [
    {
      heading: "4.1 デプロイの概要",
      body: "このセクションでは、ステージング環境への標準的なロールアウト手順について説明します。事前チェックとオンコール対応フローを含みます。",
    },
    {
      heading: "4.2 ロールバック手順",
      body: "デプロイが検証に失敗した場合は、直前の正常なビルドに戻し、検出から15分以内にオンコールエンジニアに通知してください。",
    },
    {
      heading: "4.3 エスカレーション連絡先",
      body: "重大な障害はプラットフォームのオンコールローテーションに転送されます。完全な連絡フローは次のページのエスカレーション図を参照してください。",
    },
  ],
};

export default function AppWorkspacePage() {
  return (
    <div className="flex h-screen flex-col bg-paper">
      <AppTopBar />
      <AppSubToolbar />
      <div className="flex min-h-0 flex-1">
        <AppThumbnailRail />
        <div className="flex min-w-0 flex-1 divide-x divide-rule overflow-auto">
          <AppDocumentPane content={ORIGINAL} />
          <AppDocumentPane content={TRANSLATED} />
        </div>
        <AppSidebar />
      </div>
    </div>
  );
}
