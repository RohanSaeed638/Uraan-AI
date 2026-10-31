import Link from "next/link";
import { getTranslations } from "next-intl/server";
import PageHeader from "@/components/shared/PageHeader";
import FilterChips from "@/components/shared/FilterChips";
import { Trophy } from "lucide-react";

import { getLeaderboard } from "@/lib/server/data";
import { LeaderboardPeriod } from "@/types/api";

import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";

const periods: { key: LeaderboardPeriod; label: "weekly" | "allTime" }[] = [
  { key: "weekly", label: "weekly" },
  { key: "all_time", label: "allTime" },
];

export default async function LeaderboardPage({
  searchParams,
}: {
  searchParams: Promise<{ period?: string }>;
}) {
  const { period: raw } = await searchParams;
  const t = await getTranslations("leaderboard");
  const period: LeaderboardPeriod = raw === "all_time" ? "all_time" : "weekly";

  const board = await getLeaderboard(period);

  return (
    <div className="mx-auto max-w-3xl">
      <PageHeader title={t("title")} subtitle={t("subtitle")} />

      <FilterChips
        className="mt-6"
        label={t("period")}
        value={period}
        options={periods.map(({ key, label }) => ({
          value: key,
          label: t(label),
          href: `/leaderboard?period=${key}`,
        }))}
      />

      {board && (
        <Card className="mt-6 gap-1 p-5">
          <p className="text-sm font-semibold">{t("standing")}</p>
          {board.me.on_leaderboard ? (
            <p className="text-sm text-muted-foreground">
              {board.me.rank
                ? t("rank", { rank: board.me.rank, xp: board.me.xp })
                : t("noRank")}
            </p>
          ) : (
            <p className="text-sm text-muted-foreground">
              {t.rich("hidden", {
                xp: board.me.xp,
                link: (chunks) => (
                  <Link
                    href="/settings"
                    className="font-medium text-brand-gold-deep dark:text-brand-gold hover:underline"
                  >
                    {chunks}
                  </Link>
                ),
              })}
            </p>
          )}
        </Card>
      )}

      {!board || board.entries.length === 0 ? (
        <div className="mx-auto mt-16 flex max-w-sm flex-col items-center text-center">
          <span className="flex size-16 items-center justify-center rounded-full bg-brand-violet/10">
            <Trophy className="size-7 text-brand-violet" />
          </span>
          <h2 className="font-heading mt-5 text-xl font-bold">
            {t("emptyTitle")}
          </h2>
          <p className="mt-2 text-sm text-muted-foreground">
            {t("emptyText")}
          </p>
        </div>
      ) : (
        <Card className="mt-6 gap-0 p-0">
          {board.entries.map((entry) => (
            <div
              key={entry.rank}
              className={cn(
                "flex items-center gap-4 border-b border-border px-5 py-3.5 last:border-b-0",
                entry.is_me && "bg-brand-violet/5"
              )}
            >
              <span className="w-8 text-center text-sm font-bold text-muted-foreground">
                {entry.rank}
              </span>
              <div className="min-w-0 flex-1">
                <p className="truncate font-medium">
                  {entry.display_name}
                  {entry.is_me && (
                    <span className="ms-2 text-xs font-normal text-violet-700 dark:text-brand-violet-light">
                      {t("you")}
                    </span>
                  )}
                </p>
                <p className="text-xs text-muted-foreground">
                  {t("level", { level: entry.level })}
                </p>
              </div>
              <span className="text-sm font-semibold">{t("xp", { xp: entry.xp })}</span>
            </div>
          ))}
        </Card>
      )}
    </div>
  );
}
