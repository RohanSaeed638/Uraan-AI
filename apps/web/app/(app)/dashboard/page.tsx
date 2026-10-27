import Link from "next/link";
import { getLocale, getTranslations } from "next-intl/server";
import MotivationCard from "@/components/dashboard/MotivationCard";
import ProgressRow from "@/components/dashboard/ProgressRow";
import { ArrowRight, Clock, Flame, ListChecks, Sparkles, Zap } from "lucide-react";

import { createClient } from "@/lib/supabase/server";
import { formatDate } from "@/lib/format";
import { getDashboardSummary, getGamification } from "@/lib/server/data";
import { RoadmapSummary } from "@/types/roadmap";

import { buttonVariants } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import ProgressRing from "@/components/shared/ProgressRing";

async function getRoadmaps(): Promise<RoadmapSummary[]> {
  const supabase = await createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();

  const response = await fetch(
    `${process.env.NEXT_PUBLIC_API_URL}/roadmaps`,
    {
      headers: { Authorization: `Bearer ${session?.access_token}` },
      cache: "no-store",
    }
  );

  const data = await response.json();
  if (!Array.isArray(data)) return [];
  return data;
}

export default async function DashboardPage() {
  const t = await getTranslations("dashboard");
  const tStatus = await getTranslations("status");
  const locale = await getLocale();

  const [roadmaps, summary, gamification] = await Promise.all([
    getRoadmaps(),
    getDashboardSummary(),
    getGamification(),
  ]);

  const active = roadmaps.filter((r) => r.status === "active");
  const current = summary?.current_roadmap ?? null;
  const next = summary?.next_learning ?? null;

  const totalTasksCompleted =
    summary?.stats.completed_tasks ??
    roadmaps.reduce((sum, r) => sum + r.completed_tasks, 0);

  if (roadmaps.length === 0) {
    return (
      <div className="mx-auto flex max-w-lg flex-col items-center py-20 text-center">
        <span className="flex size-16 items-center justify-center rounded-full bg-brand-violet/10">
          <Sparkles className="size-7 text-brand-violet" />
        </span>
        <h1 className="font-heading mt-6 text-2xl font-bold">
          {t("noRoadmaps")}
        </h1>
        <p className="mt-2 text-muted-foreground">
          {t("noRoadmapsText")}
        </p>
        <Link
          href="/roadmaps"
          className={buttonVariants({ size: "lg", className: "mt-7" })}
        >
          {t("create")}
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <MotivationCard />

      <ProgressRow />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[minmax(0,1fr)_320px]">
        {current && (
          <Card className="overflow-hidden">
            <div className="flex flex-col items-start justify-between gap-6 px-6 sm:flex-row sm:items-center">
              <div className="min-w-0">
                <p className="text-xs font-semibold uppercase tracking-wide text-brand-gold">
                  {t("currentRoadmap")}
                </p>
                <h2 className="font-heading mt-1 text-2xl font-bold">
                  {current.title}
                </h2>
                <p className="mt-1 text-sm text-muted-foreground">
                  {t("tasksProgress", { done: current.completed_tasks, total: current.total_tasks })}
                </p>
                {next && (
                  <p className="mt-3 text-sm">
                    <span className="text-muted-foreground">{t("upNext")}</span>
                    {next.learning_unit_title}
                  </p>
                )}
                <Link
                  href={
                    next
                      ? `/roadmaps/${next.roadmap_id}/task/${next.task_id}/learn/${next.learning_unit_id}`
                      : `/roadmaps/${current.id}`
                  }
                  className={buttonVariants({ className: "mt-5 gap-2" })}
                >
                  {t("continue")} <ArrowRight size={15} className="rtl:rotate-180" />
                </Link>
              </div>
              <ProgressRing
                value={Math.round(current.completion_percentage)}
                size={104}
              />
            </div>
          </Card>
        )}

        <Card className="justify-center p-6">
          <p className="text-sm font-semibold">{t("quickStats")}</p>
          <div className="mt-4 flex flex-col gap-4">
            <div className="flex items-center gap-3">
              <span className="flex size-9 items-center justify-center rounded-xl bg-brand-violet/10">
                <ListChecks size={16} className="text-brand-violet" />
              </span>
              <div>
                <p className="text-lg font-bold leading-none">
                  {totalTasksCompleted}
                </p>
                <p className="text-xs text-muted-foreground">
                  {t("tasksCompleted")}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <span className="flex size-9 items-center justify-center rounded-xl bg-brand-gold/15">
                <ListChecks size={16} className="text-brand-gold" />
              </span>
              <div>
                <p className="text-lg font-bold leading-none">
                  {active.length}
                </p>
                <p className="text-xs text-muted-foreground">
                  {t("activeRoadmaps")}
                </p>
              </div>
            </div>
            {gamification && (
              <>
                <div className="flex items-center gap-3">
                  <span className="flex size-9 items-center justify-center rounded-xl bg-brand-gold/15">
                    <Flame size={16} className="text-brand-gold" />
                  </span>
                  <div>
                    <p className="text-lg font-bold leading-none">
                      {gamification.streak_days}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {t("streak")}
                      {gamification.active_today ? t("doneToday") : ""}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <span className="flex size-9 items-center justify-center rounded-xl bg-brand-violet/10">
                    <Zap size={16} className="text-brand-violet" />
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="text-lg font-bold leading-none">
                      {t("level", { level: gamification.level })}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {t("xpToNext", { current: gamification.xp_into_level, total: gamification.xp_per_level })}
                    </p>
                    <Progress
                      value={Math.round(
                        (gamification.xp_into_level /
                          gamification.xp_per_level) *
                          100
                      )}
                      className="mt-1.5 h-1.5"
                    />
                  </div>
                </div>
              </>
            )}
          </div>
        </Card>
      </div>

      <div>
        <div className="mb-4 flex items-center justify-between">
          <h3 className="font-heading text-lg font-semibold">
            {t("yourRoadmaps")}
          </h3>
          <Link
            href="/roadmaps"
            className="flex items-center gap-1 text-sm font-medium text-brand-gold-deep dark:text-brand-gold hover:underline"
          >
            {t("viewAll")} <ArrowRight size={13} className="rtl:rotate-180" />
          </Link>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {roadmaps.slice(0, 3).map((roadmap) => (
            <Card key={roadmap.id} className="gap-3 px-5">
              <div className="flex items-start justify-between gap-3">
                <p className="line-clamp-2 min-w-0 font-medium">{roadmap.title}</p>
                <span className="shrink-0 rounded-full bg-brand-violet/10 px-2.5 py-0.5 text-xs font-medium text-brand-gold-deep dark:text-brand-gold">
                  {tStatus(roadmap.status)}
                </span>
              </div>
              <Progress value={roadmap.progress} />
              <div className="flex items-center justify-between text-xs text-muted-foreground">
                <span className="flex items-center gap-1">
                  <Clock size={12} />
                  {t("updated", { date: formatDate(roadmap.updated_at, undefined, locale) })}
                </span>
                <span>{roadmap.progress}%</span>
              </div>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}
