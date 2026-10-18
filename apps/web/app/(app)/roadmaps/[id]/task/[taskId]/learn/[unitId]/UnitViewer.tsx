"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
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
import { formatMinutes, getUnitMeta, isSearchLink } from "@/lib/units";
import { RoadmapTask } from "@/types/roadmap";

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
        toast.error(
          "Couldn't sync this lesson to the server — progress is saved for this session only."
        );
      }
    }

    setSaving(false);

    if (!isLast) {
      goTo(index + 1);
    } else if (nextDone.size === units.length) {
      setShowComplete(true);
    } else {
      toast.info("Some earlier lessons in this task are still unfinished.");
    }
  }

  async function markTaskComplete() {
    if (saving) return;
    setSaving(true);
    try {
      await api.patch(`/roadmaps/tasks/${task.id}`, { completed: true });
      setTaskDone(true);
      toast.success("Task marked as complete");
    } catch {
      toast.error("Couldn't update the task. Please try again.");
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
          {taskDone ? "Task Completed! 🎉" : "All lessons done! 🎉"}
        </h1>
        <p className="mt-2 text-muted-foreground">
          You&apos;ve finished every lesson in{" "}
          <span className="font-medium text-foreground">{task.title}</span>.
        </p>

        <div className="mt-8 grid w-full grid-cols-3 gap-3">
          {[
            { label: "Lessons", value: `${done.size}/${units.length}` },
            { label: "Time", value: formatMinutes(totalMinutes) },
            { label: "Status", value: taskDone ? "Completed" : "In review" },
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
                "Mark task as complete"
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
            View all tasks
          </Link>
          <Link
            href={`/roadmaps/${roadmapId}`}
            className={buttonVariants({ variant: "ghost" })}
          >
            Back to roadmap
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
        <ArrowLeft size={14} className="shrink-0" />
        <span className="truncate">Back to {task.title}</span>
      </Link>

      <div className="mb-6">
        <div className="mb-2 flex items-center justify-between text-xs text-muted-foreground">
          <span>
            Lesson {index + 1} of {units.length}
          </span>
          <span>{percent}% complete</span>
        </div>
        <Progress value={percent} className="h-1.5" />
      </div>

      <div className="flex items-center gap-2 text-sm">
        <span className="inline-flex items-center gap-1.5 rounded-full bg-brand-violet/10 px-3 py-1 font-medium text-brand-violet">
          <Icon size={14} /> {meta.label}
        </span>
        {unit.estimated_minutes != null && (
          <span className="inline-flex items-center gap-1 text-muted-foreground">
            <Clock size={13} /> {unit.estimated_minutes} min
          </span>
        )}
        {done.has(unit.id) && (
          <span className="inline-flex items-center gap-1 text-emerald-500">
            <CheckCircle2 size={14} /> Completed
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
            Hands-on project
          </p>
          <p className="mt-1 text-muted-foreground">
            Build this yourself, tick off each requirement, then mark the
            lesson complete. Keep the result: it can go in your portfolio.
          </p>
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
              <span className="block font-semibold">Find a video on YouTube</span>
              <span className="mt-1 block text-sm text-muted-foreground">
                We couldn&apos;t confirm a specific video, so this opens a
                search for this lesson. Pick a recent, well-rated result and
                follow along with the notes below.
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

        {unit.content && (
          <Card className="p-6 sm:p-8">
            <SimpleMarkdown source={unit.content} />
          </Card>
        )}

        {unit.resource_url && !video && !isFile && !searchLink && (
          <a
            href={unit.resource_url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center justify-between rounded-2xl border border-border p-4 transition hover:bg-muted"
          >
            <span className="font-medium text-brand-violet">
              Open {unit.type === "project" ? "project resources" : "the resource"}
            </span>
            <ExternalLink size={16} className="text-muted-foreground" />
          </a>
        )}

        {!unit.content && !unit.resource_url && !unit.description && (
          <p className="rounded-2xl border border-dashed border-border p-6 text-center text-sm text-muted-foreground">
            No content has been attached to this lesson yet.
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
          <ArrowLeft size={15} /> Previous
        </Button>

        <div className="flex gap-3">
          {!isLast && (
            <Button
              variant="ghost"
              onClick={() => goTo(index + 1)}
              className={cn(done.has(unit.id) && "hidden")}
            >
              Skip
            </Button>
          )}
          <Button onClick={completeAndContinue} disabled={saving} className="gap-1.5">
            {saving ? (
              <Loader2 size={15} className="animate-spin" />
            ) : done.has(unit.id) && !isLast ? (
              <>
                Next <ArrowRight size={15} />
              </>
            ) : (
              <>
                <Check size={15} />
                {isLast ? "Finish" : "Mark complete & continue"}
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}
