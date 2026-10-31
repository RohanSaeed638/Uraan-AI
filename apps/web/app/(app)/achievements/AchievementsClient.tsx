"use client";

import { useQuery } from "@tanstack/react-query";
import PageHeader from "@/components/shared/PageHeader";
import { useTranslations } from "next-intl";
import { Lock } from "lucide-react";

import { AchievementItem, getAchievements } from "@/lib/api/achievements";
import { formatDate } from "@/lib/format";
import { cn } from "@/lib/utils";
import { Gamification } from "@/types/api";

import AchievementIcon from "@/components/achievements/AchievementIcon";
import BossCard from "@/components/achievements/BossCard";
import ReadinessCard from "@/components/achievements/ReadinessCard";
import { Card } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";

const CATEGORIES = ["learning", "streak", "projects", "practice", "career"] as const;

function Badge({ item }: { item: AchievementItem }) {
  const t = useTranslations("achievements");
  const percent = Math.round((item.current / item.target) * 100);

  return (
    <Card
      className={cn(
        "h-full gap-3 p-5",
        item.unlocked ? "border-brand-violet/40" : "opacity-80"
      )}
    >
      <div className="flex items-start gap-3">
        <span
          className={cn(
            "flex size-11 shrink-0 items-center justify-center rounded-2xl",
            item.unlocked
              ? "bg-brand-gradient text-white"
              : "bg-muted text-muted-foreground"
          )}
        >
          {item.unlocked ? <AchievementIcon name={item.icon} /> : <Lock size={18} />}
        </span>

        <div className="min-w-0">
          <p className="font-heading break-words font-semibold leading-snug">{t.has(`items.${item.code}.title`) ? t(`items.${item.code}.title`) : item.title}</p>
          <p className="mt-0.5 break-words text-sm text-muted-foreground">
            {t.has(`items.${item.code}.description`) ? t(`items.${item.code}.description`) : item.description}
          </p>
        </div>
      </div>

      <div className="mt-auto">
        {item.unlocked ? (
          <p className="text-xs text-emerald-600 dark:text-emerald-400">
            {t("unlockedOn", {
              date: item.unlocked_at ? formatDate(item.unlocked_at) : "",
              xp: item.xp_reward,
            })}
          </p>
        ) : (
          <>
            <Progress value={percent} className="h-1.5" />
            <p className="mt-1.5 text-xs text-muted-foreground">
              {t("progress", { current: Math.floor(item.current), target: item.target, xp: item.xp_reward })}
            </p>
          </>
        )}
      </div>
    </Card>
  );
}

export default function AchievementsClient({
  gamification,
}: {
  gamification: Gamification | null;
}) {
  const t = useTranslations("achievements");

  const query = useQuery({
    queryKey: ["achievements"],
    queryFn: getAchievements,
    staleTime: 30_000,
  });

  const data = query.data;

  return (
    <div className="mx-auto max-w-6xl space-y-8">
      <div>
        <PageHeader title={t("title")} subtitle={t("subtitle")} />
      </div>

      {gamification && (
        <Card className="gap-4 p-6">
          <div className="flex flex-wrap items-end justify-between gap-3">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-brand-gold">
                {t("careerTitle")}
              </p>
              <p className="font-heading text-3xl font-bold">
                {t(`titles.${gamification.career_title}`)}
              </p>
            </div>
            <p className="text-sm text-muted-foreground">
              {t("levelXp", { level: gamification.level, xp: gamification.xp })}
            </p>
          </div>

          {gamification.next_career_title ? (
            <div>
              <Progress
                value={Math.round(gamification.title_progress * 100)}
                className="h-2"
              />
              <p className="mt-2 text-sm text-muted-foreground">
                {t("toNextTitle", {
                  xp: gamification.xp_to_next_title ?? 0,
                  title: t(`titles.${gamification.next_career_title}`),
                })}
              </p>
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">{t("topTitle")}</p>
          )}
        </Card>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        <ReadinessCard />
        <BossCard boss={data?.boss ?? null} />
      </div>

      {query.isError && (
        <Card className="items-center p-8 text-center text-sm text-muted-foreground">
          {t("loadError")}
        </Card>
      )}

      {data && (
        <>
          <p className="text-sm text-muted-foreground" aria-live="polite">
            {t("count", { unlocked: data.unlocked_count, total: data.total })}
          </p>

          {CATEGORIES.map((category) => {
            const items = data.items.filter((i) => i.category === category);

            if (items.length === 0) return null;

            return (
              <section key={category} aria-labelledby={`cat-${category}`}>
                <h2 id={`cat-${category}`} className="font-heading text-lg font-semibold">
                  {t(`categories.${category}`)}
                </h2>
                <div className="mt-3 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                  {items.map((item) => (
                    <Badge key={item.code} item={item} />
                  ))}
                </div>
              </section>
            );
          })}
        </>
      )}
    </div>
  );
}
