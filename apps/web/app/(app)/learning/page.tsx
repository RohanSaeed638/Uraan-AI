import Link from "next/link";
import { getTranslations } from "next-intl/server";
import PageHeader from "@/components/shared/PageHeader";
import { BookOpen, Clock } from "lucide-react";

import { getProfileServer, getRoadmapDetails } from "@/lib/server/data";
import {
  flattenUnits,
  formatMinutes,
  getUnitMeta,
  unitLabel,
  unitHref,
  UnitContext,
} from "@/lib/units";

import { Card } from "@/components/ui/card";
import { buttonVariants } from "@/components/ui/button";

type Translate = Awaited<ReturnType<typeof getTranslations>>;

function UnitRow({ c, cta, tUnit }: { c: UnitContext; cta: string; tUnit: Translate }) {
  const { icon: Icon } = getUnitMeta(c.unit.type);
  const label = unitLabel(c.unit.type, tUnit);

  return (
    <div className="flex items-center gap-4 border-b border-border px-5 py-4 last:border-b-0">
      <span className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-brand-gold/15 text-brand-gold-deep dark:text-brand-gold">
        <Icon size={18} />
      </span>
      <div className="min-w-0 flex-1">
        <p className="truncate font-medium">{c.unit.title}</p>
        <p className="mt-0.5 truncate text-xs text-muted-foreground">
          {label} · {c.taskTitle} · {c.roadmapTitle}
        </p>
      </div>
      {c.unit.estimated_minutes != null && (
        <span className="hidden shrink-0 items-center gap-1 text-xs text-muted-foreground sm:flex">
          <Clock size={13} /> {tUnit("min", { count: c.unit.estimated_minutes })}
        </span>
      )}
      <Link
        href={unitHref(c)}
        className={buttonVariants({ size: "sm", variant: "outline" })}
      >
        {cta}
      </Link>
    </div>
  );
}

export default async function LearningPage() {
  const t = await getTranslations("learning");
  const tUnit = await getTranslations("unit");

  const [roadmaps, profile] = await Promise.all([
    getRoadmapDetails(),
    getProfileServer(),
  ]);

  const all = flattenUnits(roadmaps);

  // Focus on one roadmap: prefer an active one that still has lessons left.
  const hasPending = (id: string) =>
    all.some((c) => c.roadmapId === id && !c.unit.completed);
  const focus =
    roadmaps.find((r) => r.status === "active" && hasPending(r.id)) ??
    roadmaps.find((r) => hasPending(r.id));

  const pending = focus
    ? all.filter((c) => c.roadmapId === focus.id && !c.unit.completed)
    : [];

  const dailyMinutes = Math.round((profile?.daily_hours ?? 2) * 60);

  const today: UnitContext[] = [];
  let planned = 0;
  for (const c of pending) {
    if (today.length > 0 && planned >= dailyMinutes) break;
    today.push(c);
    planned += c.unit.estimated_minutes ?? 0;
  }
  const upNext = pending.slice(today.length, today.length + 6);

  if (all.length === 0) {
    return (
      <div className="mx-auto flex max-w-lg flex-col items-center py-20 text-center">
        <span className="flex size-16 items-center justify-center rounded-full bg-brand-violet/10">
          <BookOpen className="size-7 text-brand-violet" />
        </span>
        <h1 className="font-heading mt-6 text-2xl font-bold">{t("emptyTitle")}</h1>
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

  return (
    <div className="mx-auto max-w-4xl">
      <PageHeader
        title={t("title")}
        subtitle={
          focus ? (
            t.rich("nextFrom", {
              roadmap: focus.title,
              b: (chunks) => (
                <span className="font-medium text-foreground">{chunks}</span>
              ),
            })
          ) : (
            t("allComplete")
          )
        }
      />

      {today.length === 0 ? (
        <Card className="mt-6 items-center p-10 text-center">
          <p className="font-heading text-xl font-semibold">
            {t("caughtUp")}
          </p>
          <p className="mt-1 text-sm text-muted-foreground">
            {t("caughtUpText")}
          </p>
        </Card>
      ) : (
        <>
          <div className="mt-6 flex items-end justify-between">
            <h2 className="font-heading text-lg font-semibold">
              {t("suggested")}
            </h2>
            <p className="text-sm text-muted-foreground">
              {t("planned", { planned: formatMinutes(planned, tUnit), target: formatMinutes(dailyMinutes, tUnit) })}
            </p>
          </div>
          <Card className="mt-3 gap-0 p-0">
            {today.map((c, i) => (
              <UnitRow key={c.unit.id} c={c} tUnit={tUnit} cta={i === 0 ? t("start") : t("open")} />
            ))}
          </Card>

          {upNext.length > 0 && (
            <>
              <h2 className="font-heading mt-8 text-lg font-semibold">
                {t("comingUp")}
              </h2>
              <Card className="mt-3 gap-0 p-0">
                {upNext.map((c) => (
                  <UnitRow key={c.unit.id} c={c} tUnit={tUnit} cta={t("open")} />
                ))}
              </Card>
            </>
          )}
        </>
      )}
    </div>
  );
}
