"use client";

import Link from "next/link";
import { useTranslations } from "next-intl";
import { Swords, Trophy } from "lucide-react";

import { Boss } from "@/lib/api/achievements";

import { buttonVariants } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

/** This month's boss project: one project lesson picked for you, worth bonus
 * XP if you finish it before the month ends. */
export default function BossCard({ boss }: { boss: Boss | null }) {
  const t = useTranslations("boss");

  if (!boss) {
    return (
      <Card className="gap-2 p-6">
        <p className="flex items-center gap-2 text-sm font-semibold">
          <Swords size={16} className="text-muted-foreground" /> {t("title")}
        </p>
        <p className="text-sm text-muted-foreground">{t("none")}</p>
      </Card>
    );
  }

  return (
    <Card className="gap-3 border-amber-500/30 bg-amber-500/5 p-6">
      <div className="flex items-center justify-between gap-3">
        <p className="flex items-center gap-2 text-sm font-semibold">
          {boss.defeated ? (
            <Trophy size={16} className="text-amber-500" />
          ) : (
            <Swords size={16} className="text-amber-500" />
          )}
          {t("title")}
        </p>
        <span className="rounded-full bg-amber-500/15 px-2.5 py-0.5 text-xs font-medium text-amber-600 dark:text-amber-400">
          {t("bonus", { xp: boss.bonus_xp })}
        </span>
      </div>

      <div className="min-w-0">
        <p className="font-heading break-words text-lg font-bold">{boss.title}</p>
        <p className="mt-0.5 break-words text-sm text-muted-foreground">
          {boss.task_title}
        </p>
      </div>

      {boss.defeated ? (
        <p className="text-sm font-medium text-emerald-600 dark:text-emerald-400">
          {t("defeated")}
        </p>
      ) : (
        <div className="flex flex-wrap items-center justify-between gap-3">
          <p className="text-sm text-muted-foreground">
            {t("daysLeft", { count: boss.days_left })}
          </p>
          <Link
            href={`/roadmaps/${boss.roadmap_id}/task/${boss.task_id}/learn/${boss.unit_id}`}
            className={buttonVariants({ size: "sm" })}
          >
            {t("fight")}
          </Link>
        </div>
      )}
    </Card>
  );
}
