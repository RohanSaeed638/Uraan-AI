import Link from "next/link";
import { getTranslations } from "next-intl/server";
import PageHeader from "@/components/shared/PageHeader";
import { BookOpen, CheckSquare, Clock, TrendingUp } from "lucide-react";

import { getProgressOverview } from "@/lib/server/data";
import { formatMinutes } from "@/lib/units";

import { Card } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import ProgressRing from "@/components/shared/ProgressRing";
import { buttonVariants } from "@/components/ui/button";

const pct = (done: number, total: number) =>
  total === 0 ? 0 : Math.round((done / total) * 100);

export default async function ProgressPage() {
  const t = await getTranslations("progress");
  const tUnit = await getTranslations("unit");
  const overview = await getProgressOverview();

  const rows = overview?.roadmap_progress ?? [];

  const tasksDone = overview?.tasks.completed ?? 0;
  const tasksTotal = overview?.tasks.total ?? 0;
  const unitsDone = overview?.learning_units.completed ?? 0;
  const unitsTotal = overview?.learning_units.total ?? 0;
  const minutes = Math.round(
    (overview?.estimated_completed_learning_hours ?? 0) * 60
  );

  if (rows.length === 0) {
    return (
      <div className="mx-auto flex max-w-lg flex-col items-center py-20 text-center">
        <span className="flex size-16 items-center justify-center rounded-full bg-brand-violet/10">
          <TrendingUp className="size-7 text-brand-violet" />
        </span>
        <h1 className="font-heading mt-6 text-2xl font-bold">
          {t("emptyTitle")}
        </h1>
        <p className="mt-2 text-muted-foreground">
          {t("emptyText")}
        </p>
        <Link
          href="/roadmaps"
          className={buttonVariants({ size: "lg", className: "mt-7" })}
        >
          {t("goRoadmaps")}
        </Link>
      </div>
    );
  }

  const stats = [
    { icon: CheckSquare, label: t("tasksCompleted"), value: `${tasksDone}/${tasksTotal}` },
    { icon: BookOpen, label: t("lessonsCompleted"), value: `${unitsDone}/${unitsTotal}` },
    { icon: Clock, label: t("time"), value: formatMinutes(minutes, tUnit) },
  ];

  return (
    <div className="mx-auto max-w-5xl">
      <PageHeader title={t("title")} subtitle={t("subtitle")} />

      <div className="mt-6 grid gap-4 md:grid-cols-[auto_1fr]">
        <Card className="items-center justify-center p-6">
          <ProgressRing value={pct(tasksDone, tasksTotal)} size={120} />
          <p className="mt-2 text-sm text-muted-foreground">{t("overall")}</p>
        </Card>

        <div className="grid gap-4 sm:grid-cols-3">
          {stats.map(({ icon: Icon, label, value }) => (
            <Card key={label} className="justify-center gap-2 p-5">
              <span className="flex size-9 items-center justify-center rounded-xl bg-brand-gold/15 text-brand-gold-deep dark:text-brand-gold">
                <Icon size={17} />
              </span>
              <p className="text-2xl font-bold leading-none">{value}</p>
              <p className="text-xs text-muted-foreground">{label}</p>
            </Card>
          ))}
        </div>
      </div>

      <h2 className="font-heading mt-10 text-lg font-semibold">{t("byRoadmap")}</h2>
      <div className="mt-3 space-y-4">
        {rows.map((r) => (
          <Card key={r.roadmap_id} className="gap-4 px-6">
            <div className="flex items-center justify-between gap-4">
              <Link
                href={`/roadmaps/${r.roadmap_id}`}
                className="font-semibold hover:text-brand-gold-deep dark:hover:text-brand-gold"
              >
                {r.title}
              </Link>
              <span className="shrink-0 text-sm font-medium">
                {Math.round(r.completion_percentage)}%
              </span>
            </div>
            <Progress value={Math.round(r.completion_percentage)} />

            <div className="grid gap-x-8 gap-y-3 sm:grid-cols-2">
              {r.phases.map((phase) => (
                <div key={phase.phase_id}>
                  <div className="mb-1 flex justify-between text-xs text-muted-foreground">
                    <span className="truncate pe-3">{phase.title}</span>
                    <span>
                      {phase.completed_tasks}/{phase.total_tasks}
                    </span>
                  </div>
                  <Progress
                    value={Math.round(phase.completion_percentage)}
                    className="h-1.5"
                  />
                </div>
              ))}
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
