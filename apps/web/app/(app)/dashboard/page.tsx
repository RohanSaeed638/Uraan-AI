import { API_BASE } from "@/lib/api-base";
import Link from "next/link";
import { getLocale, getTranslations } from "next-intl/server";
import MotivationCard from "@/components/dashboard/MotivationCard";
import ProgressRow from "@/components/dashboard/ProgressRow";
import { ArrowRight, Clock, Sparkles } from "lucide-react";

import { createClient } from "@/lib/supabase/server";
import { formatDate } from "@/lib/format";
import {
  getAchievementsServer,
  getActivity,
  getDashboardSummary,
  getGamification,
} from "@/lib/server/data";
import ContinueHero from "@/components/dashboard/ContinueHero";
import Highlights from "@/components/dashboard/Highlights";
import WeekStrip from "@/components/dashboard/WeekStrip";
import { RoadmapSummary } from "@/types/roadmap";

import { buttonVariants } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";

async function getRoadmaps(): Promise<RoadmapSummary[]> {
  const supabase = await createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();

  const response = await fetch(
    `${API_BASE}/roadmaps`,
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

  const [roadmaps, summary, gamification, achievements, activity] = await Promise.all([
    getRoadmaps(),
    getDashboardSummary(),
    getGamification(),
    getAchievementsServer(),
    getActivity(),
  ]);

  const current = summary?.current_roadmap ?? null;
  const next = summary?.next_learning ?? null;
  const today = new Date().toISOString().slice(0, 10);

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
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[minmax(0,1fr)_340px]">
        {current ? (
          <ContinueHero roadmap={current} next={next} />
        ) : (
          <Card className="justify-center p-8">
            <p className="font-heading text-xl font-semibold">{t("noRoadmaps")}</p>
            <p className="mt-2 text-muted-foreground">{t("noRoadmapsText")}</p>
          </Card>
        )}

        <WeekStrip
          activeDates={(activity?.days ?? []).filter((d) => d.count > 0).map((d) => d.date)}
          gamification={gamification}
          today={today}
        />
      </div>

      <MotivationCard />

      <ProgressRow />

      <div>
        <div className="mb-4 flex items-center justify-between">
          <h3 className="font-heading text-lg font-semibold">
            {t("yourRoadmaps")}
          </h3>
          <Link
            href="/roadmaps"
            className="flex items-center gap-1 text-sm font-medium text-violet-700 hover:underline dark:text-brand-violet-light"
          >
            {t("viewAll")} <ArrowRight size={13} className="rtl:rotate-180" />
          </Link>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {roadmaps.slice(0, 3).map((roadmap) => (
            <Card key={roadmap.id} className="card-lift gap-3 px-5">
              <div className="flex items-start justify-between gap-3">
                <p className="line-clamp-2 min-w-0 font-medium">{roadmap.title}</p>
                <span className="shrink-0 rounded-full bg-brand-violet/10 px-2.5 py-0.5 text-xs font-medium text-violet-700 dark:text-brand-violet-light">
                  {tStatus(roadmap.status)}
                </span>
              </div>
              <Progress value={roadmap.progress} />
              <div className="flex items-center justify-between text-xs text-muted-foreground">
                <span className="flex items-center gap-1">
                  <Clock size={12} />
                  {t("updated", { date: formatDate(roadmap.updated_at, undefined, locale) })}
                </span>
                <span className="num">{roadmap.progress}%</span>
              </div>
            </Card>
          ))}
        </div>
      </div>

      <Highlights achievements={achievements} />
    </div>
  );
}
