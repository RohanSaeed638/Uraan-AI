"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { useTranslations } from "next-intl";
import { toast } from "sonner";
import {
  ArrowLeft,
  ArrowRight,
  Check,
  CheckCircle2,
  Clock,
  ExternalLink,
  Loader2,
} from "lucide-react";

import { api } from "@/lib/api/client";
import { setUnitCompleted } from "@/lib/api/units";
import { formatMinutes, getUnitMeta, isSearchLink, unitLabel } from "@/lib/units";
import { ExerciseDetails, ProjectDetails, RoadmapTask } from "@/types/roadmap";

import ExerciseView from "@/components/lessons/ExerciseView";
import Pill from "@/components/shared/Pill";
import SimpleMarkdown from "@/components/shared/SimpleMarkdown";
import WelcomeBirdIllustration from "@/components/illustrations/WelcomeBirdIllustration";
import { Card } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Button, buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

function embedUrl(url: string): string | null {
  const yt = url.match(
    /(?:youtube\.com\/(?:watch\?v=|embed\/)|youtu\.be\/)([\w-]{11})/
  );
  if (yt) return `https://www.youtube.com/embed/${yt[1]}`;

  const vimeo = url.match(/vimeo\.com\/(\d+)/);
  if (vimeo) return `https://player.vimeo.com/video/${vimeo[1]}`;

  return null;
}

export default function UnitViewer({
  roadmapId,
  task,
  initialUnitId,
}: {
  roadmapId: string;
  task: RoadmapTask;
  initialUnitId: string;
}) {
  const t = useTranslations("viewer");
  const tUnit = useTranslations("unit");
  const tLevel = useTranslations("options.skill_level");
  const units = useMemo(
    () =>
      [...(task.learning_units ?? [])].sort(
        (a, b) => a.day - b.day || a.order - b.order
      ),
    [task.learning_units]
  );

  const [index, setIndex] = useState(
    Math.max(0, units.findIndex((u) => u.id === initialUnitId))
  );
  const [done, setDone] = useState<Set<string>>(
    () => new Set(units.filter((u) => u.completed).map((u) => u.id))
  );
  const [taskDone, setTaskDone] = useState(task.completed);
  const [saving, setSaving] = useState(false);
  const [showComplete, setShowComplete] = useState(false);

  const unit = units[index];
  const meta = getUnitMeta(unit.type);
  const Icon = meta.icon;
  const isLast = index === units.length - 1;
  const percent = Math.round((done.size / units.length) * 100);
  const totalMinutes = units.reduce((s, u) => s + (u.estimated_minutes ?? 0), 0);

  function goTo(next: number) {
    setIndex(next);
    setShowComplete(false);
    // keep the URL shareable without remounting (which would reset progress)
    window.history.replaceState(
      null,
      "",
      `/roadmaps/${roadmapId}/task/${task.id}/learn/${units[next].id}`
    );
    window.scrollTo({ top: 0 });
  }

  async function completeAndContinue() {
    if (saving) return;
    setSaving(true);

    const nextDone = new Set(done).add(unit.id);
    setDone(nextDone);

    if (!done.has(unit.id)) {
      try {
        await setUnitCompleted(unit.id, true);
      } catch {
        toast.error(t("syncFailed"));
      }
    }

    setSaving(false);

    if (!isLast) {
      goTo(index + 1);
    } else if (nextDone.size === units.length) {
      setShowComplete(true);
    } else {
      toast.info(t("someUnfinished"));
    }
  }

  async function markTaskComplete() {
    if (saving) return;
    setSaving(true);
    try {
      await api.patch(`/roadmaps/tasks/${task.id}`, { completed: true });
      setTaskDone(true);
      toast.success(t("taskDoneToast"));
    } catch {
      toast.error(t("taskFailed"));
    } finally {
      setSaving(false);
    }
  }

  /* ---------- Task complete screen ---------- */
  if (showComplete) {
    return (
      <div className="mx-auto flex max-w-lg flex-col items-center py-10 text-center">
        <WelcomeBirdIllustration size={110} />
        <h1 className="font-heading mt-2 text-3xl font-bold">
          {taskDone ? t("taskCompleted") : t("allDone")}
        </h1>
        <p className="mt-2 text-muted-foreground">
          {t.rich("finishedIn", {
            task: task.title,
            b: (chunks) => (
              <span className="font-medium text-foreground">{chunks}</span>
            ),
          })}
        </p>

        <div className="mt-8 grid w-full grid-cols-3 gap-3">
          {[
            { label: t("lessons"), value: `${done.size}/${units.length}` },
            { label: t("time"), value: formatMinutes(totalMinutes, tUnit) },
            { label: t("status"), value: taskDone ? t("completed") : t("inReview") },
          ].map(({ label, value }) => (
            <Card key={label} className="items-center gap-1 p-4">
              <p className="text-lg font-bold">{value}</p>
              <p className="text-xs text-muted-foreground">{label}</p>
            </Card>
          ))}
        </div>

        <div className="mt-8 flex w-full flex-col gap-3">
          {!taskDone && (
            <Button size="lg" onClick={markTaskComplete} disabled={saving}>
              {saving ? (
                <Loader2 size={16} className="animate-spin" />
              ) : (
                t("markTask")
              )}
            </Button>
          )}
          <Link
            href="/tasks"
            className={buttonVariants({
              size: "lg",
              variant: taskDone ? "default" : "outline",
            })}
          >
            {t("allTasks")}
          </Link>
          <Link
            href={`/roadmaps/${roadmapId}`}
            className={buttonVariants({ variant: "ghost" })}
          >
            {t("backRoadmap")}
          </Link>
        </div>
      </div>
    );
  }

  /* ---------- Lesson screen ---------- */
  const video = unit.resource_url ? embedUrl(unit.resource_url) : null;
  const isFile = unit.resource_url && /\.(mp4|webm)(\?|$)/i.test(unit.resource_url);
  const searchLink = isSearchLink(unit.resource_url);

  return (
    <div className="mx-auto max-w-3xl">
      <Link
        href={`/roadmaps/${roadmapId}/task/${task.id}`}
        className="mb-4 inline-flex max-w-full items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft size={14} className="shrink-0 rtl:rotate-180" />
        <span className="truncate">{t("backTo", { task: task.title })}</span>
      </Link>

      <div className="mb-6">
        <div className="mb-2 flex items-center justify-between text-xs text-muted-foreground">
          <span>
            {t("lessonOf", { current: index + 1, total: units.length })}
          </span>
          <span>{t("percent", { percent })}</span>
        </div>
        <Progress value={percent} className="h-1.5" />
      </div>

      <div className="flex items-center gap-2 text-sm">
        <span className="inline-flex items-center gap-1.5 rounded-full bg-brand-violet/10 px-3 py-1 font-medium text-brand-gold-deep dark:text-brand-gold">
          <Icon size={14} /> {unitLabel(unit.type, tUnit)}
        </span>
        {unit.estimated_minutes != null && (
          <span className="inline-flex items-center gap-1 text-muted-foreground">
            <Clock size={13} /> {tUnit("min", { count: unit.estimated_minutes })}
          </span>
        )}
        {done.has(unit.id) && (
          <span className="inline-flex items-center gap-1 text-emerald-500">
            <CheckCircle2 size={14} /> {t("completed")}
          </span>
        )}
      </div>

      <h1 className="font-heading mt-3 text-3xl font-bold">{unit.title}</h1>
      {unit.description && (
        <p className="mt-2 text-muted-foreground">{unit.description}</p>
      )}

      {unit.type === "project" && (
        <div className="mt-5 rounded-2xl border border-amber-500/30 bg-amber-500/10 p-4 text-sm">
          <p className="font-semibold text-amber-700 dark:text-amber-400">
            {t("project")}
          </p>
          <p className="mt-1 text-muted-foreground">
            {t("projectText")}
          </p>
          {(() => {
            const meta = unit.details as unknown as ProjectDetails | null;

            if (!meta) return null;

            return (
              <div className="mt-3 space-y-2">
                <div className="flex flex-wrap gap-1.5">
                  {meta.difficulty && (
                    <Pill tone="soft">
                      {["beginner", "intermediate", "advanced"].includes(meta.difficulty)
                        ? tLevel(meta.difficulty)
                        : meta.difficulty}
                    </Pill>
                  )}
                  {meta.skills?.map((skill) => (
                    <Pill key={skill}>{skill}</Pill>
                  ))}
                </div>
                {meta.portfolio_value && (
                  <p className="text-muted-foreground">
                    <span className="font-medium text-foreground">
                      {t("worthShowing")}
                    </span>
                    {meta.portfolio_value}
                  </p>
                )}
              </div>
            );
          })()}
        </div>
      )}

      <div className="mt-6 space-y-6">
        {searchLink && unit.resource_url && (
          <a
            href={unit.resource_url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center justify-between gap-4 rounded-3xl border border-border bg-card p-6 transition hover:bg-muted"
          >
            <span>
              <span className="block font-semibold">{t("findVideo")}</span>
              <span className="mt-1 block text-sm text-muted-foreground">
                {t("findVideoText")}
              </span>
            </span>
            <ExternalLink size={18} className="shrink-0 text-brand-violet" />
          </a>
        )}

        {video && (
          <div className="aspect-video overflow-hidden rounded-3xl border border-border bg-black">
            <iframe
              src={video}
              title={unit.title}
              className="size-full"
              allow="accelerometer; encrypted-media; picture-in-picture"
              allowFullScreen
            />
          </div>
        )}

        {isFile && unit.resource_url && (
          <video
            controls
            src={unit.resource_url}
            className="w-full rounded-3xl border border-border bg-black"
          />
        )}

        {unit.type === "exercise" && unit.details ? (
          <ExerciseView
            problem={unit.content}
            details={unit.details as unknown as ExerciseDetails}
          />
        ) : (
          unit.content && (
            <Card className="p-6 sm:p-8">
              <SimpleMarkdown source={unit.content} />
            </Card>
          )
        )}

        {unit.resource_url && !video && !isFile && !searchLink && (
          <a
            href={unit.resource_url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center justify-between rounded-2xl border border-border p-4 transition hover:bg-muted"
          >
            <span className="font-medium text-brand-gold-deep dark:text-brand-gold">
              {unit.type === "project" ? t("openProject") : t("openResource")}
            </span>
            <ExternalLink size={16} className="text-muted-foreground" />
          </a>
        )}

        {!unit.content && !unit.resource_url && !unit.description && (
          <p className="rounded-2xl border border-dashed border-border p-6 text-center text-sm text-muted-foreground">
            {t("noContent")}
          </p>
        )}
      </div>

      <div className="mt-10 flex items-center justify-between gap-3 border-t border-border pt-6">
        <Button
          variant="outline"
          disabled={index === 0}
          onClick={() => goTo(index - 1)}
          className="gap-1.5"
        >
          <ArrowLeft size={15} className="rtl:rotate-180" /> {t("previous")}
        </Button>

        <div className="flex gap-3">
          {!isLast && (
            <Button
              variant="ghost"
              onClick={() => goTo(index + 1)}
              className={cn(done.has(unit.id) && "hidden")}
            >
              {t("skip")}
            </Button>
          )}
          <Button onClick={completeAndContinue} disabled={saving} className="gap-1.5">
            {saving ? (
              <Loader2 size={15} className="animate-spin" />
            ) : done.has(unit.id) && !isLast ? (
              <>
                {t("next")} <ArrowRight size={15} className="rtl:rotate-180" />
              </>
            ) : (
              <>
                <Check size={15} />
                {isLast ? t("finish") : t("markContinue")}
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}
