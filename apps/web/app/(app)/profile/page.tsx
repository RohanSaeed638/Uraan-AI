import Link from "next/link";
import { redirect } from "next/navigation";
import {
  Briefcase,
  Clock,
  Gauge,
  Globe,
  GraduationCap,
  Target,
} from "lucide-react";

import { createClient } from "@/lib/supabase/server";
import { getProfileServer } from "@/lib/server/data";

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Card } from "@/components/ui/card";
import { buttonVariants } from "@/components/ui/button";

const titleCase = (v?: string | null) =>
  v
    ? v
        .replace(/[-_]+/g, " ")
        .replace(/\b\w/g, (c) => c.toUpperCase())
    : "Not set";

export default async function ProfilePage() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) redirect("/login");

  const profile = await getProfileServer();

  const name: string =
    profile?.full_name || user.user_metadata?.full_name || "Student";
  const initials = name
    .split(" ")
    .map((n: string) => n[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();

  const details = [
    { icon: Briefcase, label: "Career path", value: titleCase(profile?.career_slug) },
    { icon: Gauge, label: "Skill level", value: titleCase(profile?.skill_level) },
    {
      icon: GraduationCap,
      label: "Learning style",
      value: titleCase(profile?.learning_style),
    },
    {
      icon: Clock,
      label: "Daily study time",
      value: profile?.daily_hours ? `${profile.daily_hours}h per day` : "Not set",
    },
    {
      icon: Target,
      label: "Target duration",
      value: profile?.target_duration
        ? `${profile.target_duration} months`
        : "Not set",
    },
    { icon: Globe, label: "Language", value: titleCase(profile?.language) },
  ];

  return (
    <div className="mx-auto max-w-3xl">
      <h1 className="font-heading text-3xl font-bold">Profile</h1>
      <p className="mt-1 text-muted-foreground">
        Your personal details and learning preferences.
      </p>

      <Card className="mt-6 flex-row items-center gap-5 p-6">
        <Avatar size="lg" className="size-16">
          <AvatarImage src={user.user_metadata?.avatar_url} />
          <AvatarFallback className="bg-brand-violet text-lg text-white">
            {initials}
          </AvatarFallback>
        </Avatar>
        <div className="min-w-0 flex-1">
          <p className="font-heading truncate text-xl font-bold">{name}</p>
          <p className="truncate text-sm text-muted-foreground">{user.email}</p>
        </div>
        <Link
          href="/settings"
          className={buttonVariants({ variant: "outline", size: "sm" })}
        >
          Edit in Settings
        </Link>
      </Card>

      <h2 className="font-heading mt-8 text-lg font-semibold">
        Learning preferences
      </h2>
      {profile ? (
        <div className="mt-3 grid gap-4 sm:grid-cols-2">
          {details.map(({ icon: Icon, label, value }) => (
            <Card key={label} className="flex-row items-center gap-4 p-5">
              <span className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-brand-violet/10 text-brand-violet">
                <Icon size={18} />
              </span>
              <div className="min-w-0">
                <p className="text-xs text-muted-foreground">{label}</p>
                <p className="truncate font-medium">{value}</p>
              </div>
            </Card>
          ))}
        </div>
      ) : (
        <Card className="mt-3 items-center p-8 text-center">
          <p className="text-sm text-muted-foreground">
            Your learning preferences couldn&apos;t be loaded right now.
          </p>
        </Card>
      )}
    </div>
  );
}
