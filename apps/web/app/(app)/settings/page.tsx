import { createClient } from "@/lib/supabase/server";
import { redirect } from "next/navigation";

import { getUserSettings } from "@/lib/server/data";

import SettingsClient from "./SettingsClient";

export default async function SettingsPage() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect("/login");
  }

  const settings = await getUserSettings();

  return <SettingsClient user={user} settings={settings} />;
}
