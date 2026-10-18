import { redirect } from "next/navigation";

import { createClient } from "@/lib/supabase/server";
import { getGamification, getProfileServer } from "@/lib/server/data";

import ProfileClient from "./ProfileClient";

export default async function ProfilePage() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) redirect("/login");

  const [profile, gamification] = await Promise.all([
    getProfileServer(),
    getGamification(),
  ]);

  return (
    <ProfileClient
      profile={profile}
      gamification={gamification}
      account={{
        email: user.email ?? "",
        fallbackName: (user.user_metadata?.full_name as string) ?? "Student",
        avatarUrl: (user.user_metadata?.avatar_url as string) ?? null,
      }}
    />
  );
}
