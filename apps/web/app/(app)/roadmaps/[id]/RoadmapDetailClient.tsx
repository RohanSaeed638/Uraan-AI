"use client";

import { useState } from "react";
import Link from "next/link";
import { useTranslations } from "next-intl";
import { ArrowLeft, Clock, BookOpen, Target } from "lucide-react";

import RoadmapActions from "./RoadmapActions";
import TaskList from "./TaskList";
import { Card } from "@/components/ui/card";
import ProgressRing from "@/components/shared/ProgressRing";

import { Roadmap } from "@/types/roadmap";

interface RoadmapDetailClientProps {
  roadmap: Roadmap;
}

const statusStyles: Record<string, string> = {
  active: "bg-emerald-500/15 text-emerald-500",
  completed: "bg-brand-violet/15 text-violet-700 dark:text-brand-violet-light",
  paused: "bg-amber-500/15 text-amber-500",
  generating: "bg-sky-500/15 text-sky-500",
  failed: "bg-destructive/15 text-destructive",
};

export default function RoadmapDetailClient({
  roadmap: initialRoadmap,
}: RoadmapDetailClientProps) {
  const t = useTranslations("roadmaps.detail");
  const tStatus = useTranslations("status");
  const [roadmap, setRoadmap] = useState<Roadmap>(initialRoadmap);

  function calculateProgress(roadmap: Roadmap) {
    const tasks = roadmap.phases.flatMap((phase) => phase.tasks);
    if (tasks.length === 0) return 0;
    const completed = tasks.filter((task) => task.completed).length;
    return Math.round((completed / tasks.length) * 100);
  }

  const progress = calculateProgress(roadmap);

  const totalHours = roadmap.phases
    .flatMap((phase) => phase.tasks)
    .reduce((total, task) => total + (task.estimated_hours ?? 0), 0);

  function handleRoadmapChange(updatedRoadmap: Roadmap) {
    setRoadmap(updatedRoadmap);
  }

  return (
    <div>
      <Link
        href="/roadmaps"
        className="mb-4 inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft size={14} className="rtl:rotate-180" /> {t("back")}
      </Link>

      {/* Header */}
      <Card className="px-6 sm:px-8">
        <div className="flex flex-col justify-between gap-6 sm:flex-row sm:items-center">
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-3">
              <h1 className="font-heading text-2xl font-bold sm:text-3xl">
                {roadmap.title}
              </h1>
              <span
                className={`shrink-0 rounded-full px-3 py-1 text-xs font-medium ${
                  statusStyles[roadmap.status] ??
                  "bg-muted text-muted-foreground"
                }`}
              >
                {tStatus(roadmap.status)}
              </span>
            </div>
            <p className="mt-3 max-w-2xl leading-7 text-muted-foreground">
              {roadmap.description}
            </p>
          </div>

          <ProgressRing value={progress} size={96} />
        </div>

        {/* Stats */}
        <div className="mt-8 grid gap-4 sm:grid-cols-3">
          <div className="flex items-center gap-3 rounded-2xl border border-border p-4">
            <span className="flex size-10 items-center justify-center rounded-xl bg-brand-violet/10">
              <Target size={18} className="text-brand-violet" />
            </span>
            <div>
              <p className="text-lg font-bold leading-none">{progress}%</p>
              <p className="mt-1 text-xs text-muted-foreground">{t("completion")}</p>
            </div>
          </div>

          <div className="flex items-center gap-3 rounded-2xl border border-border p-4">
            <span className="flex size-10 items-center justify-center rounded-xl bg-brand-gold/15">
              <Clock size={18} className="text-brand-gold" />
            </span>
            <div>
              <p className="text-lg font-bold leading-none">{totalHours}h</p>
              <p className="mt-1 text-xs text-muted-foreground">
                {t("hours")}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3 rounded-2xl border border-border p-4">
            <span className="flex size-10 items-center justify-center rounded-xl bg-sky-500/10">
              <BookOpen size={18} className="text-sky-500" />
            </span>
            <div>
              <p className="text-lg font-bold leading-none">
                {roadmap.phases.length}
              </p>
              <p className="mt-1 text-xs text-muted-foreground">{t("phases")}</p>
            </div>
          </div>
        </div>

        <RoadmapActions roadmap={roadmap} dailyHours={roadmap.daily_hours ?? 2} />
      </Card>

      {/* Tasks */}
      {roadmap.phases.length > 0 && (
        <TaskList roadmap={roadmap} onRoadmapChange={handleRoadmapChange} />
      )}
    </div>
  );
}
