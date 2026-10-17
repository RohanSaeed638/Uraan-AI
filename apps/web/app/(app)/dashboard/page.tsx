import Link from "next/link";
import { ArrowRight, Clock, Flame, ListChecks, Sparkles } from "lucide-react";

import { createClient } from "@/lib/supabase/server";
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
  const roadmaps = await getRoadmaps();

  const active = roadmaps.filter((r) => r.status === "active");
  const current =
    active.sort(
      (a, b) =>
        new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
    )[0] ?? roadmaps[0];

  const totalTasksCompleted = roadmaps.reduce(
    (sum, r) => sum + r.completed_tasks,
    0
  );

  if (roadmaps.length === 0) {
    return (
      <div className="mx-auto flex max-w-lg flex-col items-center py-20 text-center">
        <span className="flex size-16 items-center justify-center rounded-full bg-brand-violet/10">
          <Sparkles className="size-7 text-brand-violet" />
        </span>
        <h1 className="font-heading mt-6 text-2xl font-bold">
          No roadmaps yet
        </h1>
        <p className="mt-2 text-muted-foreground">
          Start your journey by creating a new roadmap or exploring
          recommended learning paths.
        </p>
        <Link
          href="/roadmaps"
          className={buttonVariants({ size: "lg", className: "mt-7" })}
        >
          + Create New Roadmap
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="grid gap-6 lg:grid-cols-[1fr_320px]">
        {current && (
          <Card className="overflow-hidden">
            <div className="flex flex-col items-start justify-between gap-6 p-2 sm:flex-row sm:items-center">
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-brand-gold">
                  Current Roadmap
                </p>
                <h2 className="font-heading mt-1 text-2xl font-bold">
                  {current.title}
                </h2>
                <p className="mt-1 text-sm text-muted-foreground">
                  {current.completed_tasks} / {current.total_tasks} tasks
                  complete
                </p>
                <Link
                  href={`/roadmaps/${current.id}`}
                  className={buttonVariants({ className: "mt-5 gap-2" })}
                >
                  Continue Learning <ArrowRight size={15} />
                </Link>
              </div>
              <ProgressRing value={current.progress} size={104} />
            </div>
          </Card>
        )}

        <Card className="justify-center p-6">
          <p className="text-sm font-semibold">Quick Stats</p>
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
                  Tasks completed
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <span className="flex size-9 items-center justify-center rounded-xl bg-brand-gold/15">
                <Flame size={16} className="text-brand-gold" />
              </span>
              <div>
                <p className="text-lg font-bold leading-none">
                  {active.length}
                </p>
                <p className="text-xs text-muted-foreground">
                  Active roadmaps
                </p>
              </div>
            </div>
          </div>
        </Card>
      </div>

      <div>
        <div className="mb-4 flex items-center justify-between">
          <h3 className="font-heading text-lg font-semibold">
            Your Roadmaps
          </h3>
          <Link
            href="/roadmaps"
            className="flex items-center gap-1 text-sm font-medium text-brand-violet hover:underline"
          >
            View all <ArrowRight size={13} />
          </Link>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {roadmaps.slice(0, 3).map((roadmap) => (
            <Card key={roadmap.id} className="gap-3">
              <div className="flex items-center justify-between">
                <p className="font-medium">{roadmap.title}</p>
                <span className="rounded-full bg-brand-violet/10 px-2.5 py-0.5 text-xs font-medium text-brand-violet">
                  {roadmap.status}
                </span>
              </div>
              <Progress value={roadmap.progress} />
              <div className="flex items-center justify-between text-xs text-muted-foreground">
                <span className="flex items-center gap-1">
                  <Clock size={12} />
                  Updated {new Date(roadmap.updated_at).toLocaleDateString()}
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
