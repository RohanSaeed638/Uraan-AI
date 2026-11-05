import { Medal, Swords } from "lucide-react";
import Link from "next/link";
import { getTranslations } from "next-intl/server";

import { Card } from "@/components/ui/card";
import type { AchievementsResult } from "@/lib/api/achievements";

// Two small cards under the roadmaps: the next project ("boss") to beat, and what
// you unlocked lately. (The readiness score has its own card at the top.)
export default async function Highlights({ achievements }: { achievements: AchievementsResult | null }) {
  const t = await getTranslations("dashboard");

  const recent = (achievements?.items ?? [])
    .filter((a) => a.unlocked && a.unlocked_at)
    .sort((a, b) => (b.unlocked_at ?? "").localeCompare(a.unlocked_at ?? ""))
    .slice(0, 3);
  const boss = achievements?.boss ?? null;

  if (!boss && recent.length === 0) return null;

  return (
    <div className="grid gap-4 md:grid-cols-2">
      {boss && (
        <Card className="gap-2 p-6">
          <p className="flex items-center gap-2 text-sm font-semibold">
            <Swords className="size-4 text-violet-700 dark:text-brand-violet-light" aria-hidden />
            {t("upcomingProject")}
          </p>
          <p className="font-medium">{boss.title}</p>
          <p className="text-sm text-muted-foreground">{boss.task_title}</p>
          <p className="text-sm text-muted-foreground">
            {boss.defeated ? t("projectDone") : t("projectDaysLeft", { count: boss.days_left, xp: boss.bonus_xp })}
          </p>
          <Link
            href={`/roadmaps/${boss.roadmap_id}/task/${boss.task_id}/learn/${boss.unit_id}`}
            className="mt-auto text-sm font-medium text-violet-700 hover:underline dark:text-brand-violet-light"
          >
            {t("openProject")}
          </Link>
        </Card>
      )}

      {recent.length > 0 && (
        <Card className="gap-3 p-6">
          <p className="flex items-center gap-2 text-sm font-semibold">
            <Medal className="size-4 text-brand-gold-deep dark:text-brand-gold" aria-hidden />
            {t("recentAchievements")}
          </p>
          <ul className="space-y-2">
            {recent.map((a) => (
              <li key={a.code}>
                <p className="text-sm font-medium">{a.title}</p>
                <p className="text-xs text-muted-foreground">{a.description}</p>
              </li>
            ))}
          </ul>
        </Card>
      )}
    </div>
  );
}
