import Link from "next/link";
import { BookOpen, Clock } from "lucide-react";

import { getProfileServer, getRoadmapDetails } from "@/lib/server/data";
import {
  flattenUnits,
  formatMinutes,
  getUnitMeta,
  unitHref,
  UnitContext,
} from "@/lib/units";

import { Card } from "@/components/ui/card";
import { buttonVariants } from "@/components/ui/button";

function UnitRow({ c, cta }: { c: UnitContext; cta: string }) {
  const { icon: Icon, label } = getUnitMeta(c.unit.type);

  return (
    <div className="flex items-center gap-4 border-b border-border px-5 py-4 last:border-b-0">
      <span className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-brand-violet/10 text-brand-violet">
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
          <Clock size={13} /> {c.unit.estimated_minutes} min
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
        <h1 className="font-heading mt-6 text-2xl font-bold">No lessons yet</h1>
        <p className="mt-2 text-muted-foreground">
          Lessons appear here once you have a roadmap with learning units.
        </p>
        <Link
          href="/roadmaps"
          className={buttonVariants({ size: "lg", className: "mt-7" })}
        >
          Go to My Roadmaps
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl">
      <h1 className="font-heading text-3xl font-bold">Learning</h1>
      <p className="mt-1 text-muted-foreground">
        {focus ? (
          <>
            Your next lessons from{" "}
            <span className="font-medium text-foreground">{focus.title}</span>.
          </>
        ) : (
          "Every lesson is complete."
        )}
      </p>

      {today.length === 0 ? (
        <Card className="mt-6 items-center p-10 text-center">
          <p className="font-heading text-xl font-semibold">
            You&apos;re all caught up 🎉
          </p>
          <p className="mt-1 text-sm text-muted-foreground">
            Every lesson across your roadmaps is complete.
          </p>
        </Card>
      ) : (
        <>
          <div className="mt-6 flex items-end justify-between">
            <h2 className="font-heading text-lg font-semibold">
              Suggested for today
            </h2>
            <p className="text-sm text-muted-foreground">
              {formatMinutes(planned)} planned · target{" "}
              {formatMinutes(dailyMinutes)}/day
            </p>
          </div>
          <Card className="mt-3 gap-0 p-0">
            {today.map((c, i) => (
              <UnitRow key={c.unit.id} c={c} cta={i === 0 ? "Start" : "Open"} />
            ))}
          </Card>

          {upNext.length > 0 && (
            <>
              <h2 className="font-heading mt-8 text-lg font-semibold">
                Coming up
              </h2>
              <Card className="mt-3 gap-0 p-0">
                {upNext.map((c) => (
                  <UnitRow key={c.unit.id} c={c} cta="Open" />
                ))}
              </Card>
            </>
          )}
        </>
      )}
    </div>
  );
}
