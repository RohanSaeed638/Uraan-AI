import { createClient } from "@/lib/supabase/server";
import { redirect } from "next/navigation";

import { getUserSettings } from "@/lib/server/data";

import SettingsClient from "./SettingsClient";
import { isTabKey } from "./tabs";

export default async function SettingsPage({
  searchParams,
}: {
  searchParams: Promise<{ tab?: string }>;
}) {
  const { tab } = await searchParams;
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect("/login");
  }

  const settings = await getUserSettings();

  return (
    <SettingsClient
      user={user}
      settings={settings}
      initialTab={isTabKey(tab) ? tab : "account"}
    />
  );
}
