import { redirect } from "next/navigation";

/** Account settings now live on the Profile page. */
export default function AccountSettingsPage() {
  redirect("/app/profile");
}
