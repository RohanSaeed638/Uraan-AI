"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import {
  Code2,
  ArrowLeft,
  BookOpen,
  Check,
  CheckCircle2,
  ChevronRight,
  Clock,
  ExternalLink,
  Loader2,
  TriangleAlert,
  FolderKanban,
  PlayCircle,
  Target,
} from "lucide-react";

import { RoadmapTask } from "@/types/roadmap";

import { retryLessons } from "@/lib/api/units";
import { usePendingLessons } from "@/lib/use-pending-lessons";
import { isSearchLink, unitAction, unitColor, unitLabel } from "@/lib/units";

import RecommendedResources from "@/components/resources/RecommendedResources";
import LessonPlanLoader from "./LessonPlanLoader";
import TaskQuiz from "./TaskQuiz";

interface TaskLearningPageProps {
  roadmapId: string;
  task: RoadmapTask;
}

export default function TaskLearningPage({
  roadmapId,
  task,
}: TaskLearningPageProps) {
  const t = useTranslations("learn");
  const tUnit = useTranslations("unit");

  const learningUnits = useMemo(
    () => task.learning_units ?? [],
    [task.learning_units]
  );

  const router = useRouter();
  const writing = usePendingLessons(task.id, learningUnits);
  const isReady = (unit: { status?: string }) => (unit.status ?? "ready") === "ready";

  async function retry() {
    try {
      await retryLessons(task.id);
    } finally {
      router.refresh();
    }
  }

  /*
   * Get all available days.
   */
  const days = useMemo(() => {
    return Array.from(
      new Set(learningUnits.map((unit) => unit.day))
    ).sort((a, b) => a - b);
  }, [learningUnits]);

  /*
   * Start on the first day that isn't completely finished.
   * If everything is completed, start on the last day.
   */
  const initialDay = useMemo(() => {
    if (days.length === 0) {
      return 1;
    }

    const firstIncompleteDay = days.find((day) => {
      const units = learningUnits.filter(
        (unit) => unit.day === day
      );

      return units.some((unit) => !unit.completed);
    });

    return firstIncompleteDay ?? days[days.length - 1];
  }, [days, learningUnits]);

  const [selectedDay, setSelectedDay] =
    useState(initialDay);

  /*
   * Overall task progress.
   */
  const totalUnits = learningUnits.length;

  const completedUnits = learningUnits.filter(
    (unit) => unit.completed
  ).length;

  const progress =
    totalUnits === 0
      ? 0
      : Math.round(
          (completedUnits / totalUnits) * 100
        );

  /*
   * Current day's units.
   */
  const dayUnits = learningUnits.filter(
    (unit) => unit.day === selectedDay
  );

  const dayCompletedUnits = dayUnits.filter(
    (unit) => unit.completed
  ).length;

  const dayMinutes = dayUnits.reduce(
    (total, unit) =>
      total + (unit.estimated_minutes ?? 0),
    0
  );

  /*
   * Find the next incomplete learning unit.
   */
  const nextUnit = useMemo(() => {
    return learningUnits.find(
      (unit) => !unit.completed && isReady(unit)
    );
  }, [learningUnits]);

  /*
   * Determine whether a day is completed.
   */
  const isDayCompleted = (day: number) => {
    const units = learningUnits.filter(
      (unit) => unit.day === day
    );

    return (
      units.length > 0 &&
      units.every((unit) => unit.completed)
    );
  };

  /*
   * Get a friendly label for the learning-unit type.
   */
  const getUnitTypeLabel = (type: string) =>
    type.toLowerCase() === "practice" ? tUnit("type.practice") : unitLabel(type, tUnit);

  /*
   * Get icon for learning-unit type.
   */
  const getUnitIcon = (type: string) => {
    switch (type.toLowerCase()) {
      case "reading":
        return BookOpen;

      case "video":
        return PlayCircle;

      case "project":
        return FolderKanban;

      case "exercise":
        return Code2;

      case "practice":
        return Target;

      default:
        return BookOpen;
    }
  };

  /*
   * A task with no lessons yet: write them, then reload.
   */
  if (learningUnits.length === 0) {
    return (
      <div className="mx-auto max-w-3xl space-y-6 pb-10">
        <Link
          href={`/roadmaps/${roadmapId}`}
          className="inline-flex items-center gap-2 text-sm text-muted-foreground transition-colors hover:text-foreground"
        >
          <ArrowLeft className="h-4 w-4 rtl:rotate-180" />
          {t("back")}
        </Link>

        <section className="rounded-xl border bg-card p-6 md:p-8">
          <h1 className="text-2xl font-bold tracking-tight md:text-3xl">
            {task.title}
          </h1>
          {task.description && (
            <p className="mt-3 leading-7 text-muted-foreground">
              {task.description}
            </p>
          )}
        </section>

        <LessonPlanLoader taskId={task.id} />
      </div>
    );
  }

  /*
   * How many lessons of each kind, shown above the plan.
   */
  const mix = (["reading", "video", "project", "exercise"] as const)
    .map((type) => ({
      type,
      count: learningUnits.filter((u) => u.type.toLowerCase() === type).length,
      minutes: learningUnits
        .filter((u) => u.type.toLowerCase() === type)
        .reduce((sum, u) => sum + (u.estimated_minutes ?? 0), 0),
    }))
    .filter((item) => item.count > 0);

  const furtherReading = (task.resource_links ?? []).filter(Boolean);

  return (
    <div className="mx-auto max-w-7xl space-y-6 pb-10">

      {/* -------------------------------------------------- */}
      {/* Back */}
      {/* -------------------------------------------------- */}

      <Link
        href={`/roadmaps/${roadmapId}`}
        className="
          inline-flex
          items-center
          gap-2
          text-sm
          text-muted-foreground
          transition-colors
          hover:text-foreground
        "
      >
        <ArrowLeft className="h-4 w-4 rtl:rotate-180" />
        {t("back")}
      </Link>

      {/* -------------------------------------------------- */}
      {/* Task Header */}
      {/* -------------------------------------------------- */}

      <section className="rounded-xl border bg-card p-6 md:p-8">

        <div className="flex flex-col gap-6 md:flex-row md:items-start md:justify-between">

          <div className="min-w-0">

            <div className="mb-3 flex items-center gap-2 text-sm text-muted-foreground">
              <span>{t("task")}</span>

              <ChevronRight className="h-4 w-4 rtl:rotate-180" />

              <span>{t("learning")}</span>
            </div>

            <h1 className="text-2xl font-bold tracking-tight md:text-3xl">
              {task.title}
            </h1>

            {task.description && (
              <p className="mt-3 max-w-3xl leading-7 text-muted-foreground">
                {task.description}
              </p>
            )}

          </div>

          {/* Task stats */}

          <div className="flex shrink-0 flex-wrap gap-3">

            <div className="flex items-center gap-2 rounded-lg border bg-background px-3 py-2 text-sm">
              <Clock className="h-4 w-4 text-muted-foreground" />

              <span>
                {t("hours", { count: task.estimated_hours ?? 0 })}
              </span>
            </div>

            <div className="flex items-center gap-2 rounded-lg border bg-background px-3 py-2 text-sm">
              <CheckCircle2 className="h-4 w-4 text-muted-foreground" />

              <span>
                {completedUnits}/{totalUnits}
              </span>
            </div>

          </div>

        </div>

        {/* Progress */}

        <div className="mt-7">

          <div className="mb-2 flex items-center justify-between text-sm">

            <span className="font-medium">
              {t("progress")}
            </span>

            <span className="text-muted-foreground">
              {progress}%
            </span>

          </div>

          <div className="h-2.5 overflow-hidden rounded-full bg-muted">

            <div
              className="h-full rounded-full bg-primary transition-all duration-500"
              style={{
                width: `${progress}%`,
              }}
            />

          </div>

        </div>

      </section>

      {writing.waiting > 0 && (
        <section
          role="status"
          className="flex items-center gap-3 rounded-xl border border-brand-gold/40 bg-brand-gold/10 p-4 text-sm"
        >
          <Loader2 className="h-4 w-4 shrink-0 animate-spin text-brand-gold" />
          <span>{t("writing", { ready: writing.ready, total: writing.total })}</span>
        </section>
      )}

      {writing.failed > 0 && (
        <section
          role="alert"
          className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-destructive/40 bg-destructive/10 p-4 text-sm"
        >
          <span className="flex items-center gap-2 font-medium text-destructive">
            <TriangleAlert className="h-4 w-4" /> {t("writingFailed", { count: writing.failed })}
          </span>
          <button
            type="button"
            onClick={retry}
            className="rounded-lg border px-3 py-1.5 text-sm font-medium transition-colors hover:bg-muted"
          >
            {t("retryWriting")}
          </button>
        </section>
      )}

      {/* -------------------------------------------------- */}
      {/* Continue Learning */}
      {/* -------------------------------------------------- */}

      {/* What this task is made of */}

      <section className="grid gap-3 sm:grid-cols-3">
        {mix.map(({ type, count, minutes }) => {
          const MixIcon = getUnitIcon(type);

          return (
            <div
              key={type}
              className="flex items-center gap-3 rounded-xl border bg-card p-4"
            >
              <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-muted">
                <MixIcon className={`h-5 w-5 ${unitColor(type)}`} />
              </span>
              <div>
                <p className="text-sm font-semibold">
                  {tUnit(`typePlural.${type}`, { count })}
                </p>
                <p className="text-xs text-muted-foreground">{tUnit("min", { count: minutes })}</p>
              </div>
            </div>
          );
        })}
      </section>

      {nextUnit && (
        <section className="rounded-xl border bg-primary/5 p-5">

          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">

            <div className="flex items-start gap-3">

              <div className="rounded-lg bg-primary/10 p-2">
                <PlayCircle className="h-5 w-5 text-primary" />
              </div>

              <div>

                <p className="text-sm font-medium text-primary">
                  {t("continueLearning")}
                </p>

                <h2 className="mt-1 font-semibold">
                  {nextUnit.title}
                </h2>

                <div className="mt-1 flex items-center gap-2 text-sm text-muted-foreground">

                  <span>
                    {tUnit("day", { day: nextUnit.day })}
                  </span>

                  {nextUnit.estimated_minutes != null && (
                    <>
                      <span>•</span>

                      <span>
                        {tUnit("min", { count: nextUnit.estimated_minutes })}
                      </span>
                    </>
                  )}

                </div>

              </div>

            </div>

            <Link
              href={`/roadmaps/${roadmapId}/task/${task.id}/learn/${nextUnit.id}`}
              className="shrink-0 whitespace-nowrap 
                inline-flex
                items-center
                justify-center
                gap-2
                rounded-lg
                bg-primary
                px-4
                py-2
                text-sm
                font-medium
                text-primary-foreground
                transition-opacity
                hover:opacity-90
              "
            >
              {t("continue")}
              <ChevronRight className="h-4 w-4 rtl:rotate-180" />
            </Link>

          </div>

        </section>
      )}

      {/* -------------------------------------------------- */}
      {/* Main Learning Area */}
      {/* -------------------------------------------------- */}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[240px_minmax(0,1fr)]">

        {/* ------------------------------------------------ */}
        {/* Learning Plan Sidebar */}
        {/* ------------------------------------------------ */}

        <aside className="h-fit rounded-xl border bg-card p-4">

          <div className="mb-4 px-2">

            <h2 className="text-sm font-semibold">
              {t("planTitle")}
            </h2>

            <p className="mt-1 text-xs text-muted-foreground">
              {t("days", { count: days.length })}
            </p>

          </div>

          <div className="space-y-1">

            {days.map((day) => {

              const units = learningUnits.filter(
                (unit) => unit.day === day
              );

              const completed = units.filter(
                (unit) => unit.completed
              ).length;

              const completedDay =
                isDayCompleted(day);

              const active =
                selectedDay === day;

              const minutes = units.reduce(
                (total, unit) =>
                  total +
                  (unit.estimated_minutes ?? 0),
                0
              );

              return (
                <button
                  key={day}
                  type="button"
                  onClick={() =>
                    setSelectedDay(day)
                  }
                  className={`
                    w-full
                    rounded-lg
                    p-3
                    text-start
                    transition-colors
                    ${
                      active
                        ? "bg-primary/10 text-primary"
                        : "hover:bg-muted"
                    }
                  `}
                >

                  <div className="flex items-center justify-between gap-2">

                    <div className="flex items-center gap-2">

                      {completedDay ? (
                        <CheckCircle2 className="h-4 w-4 shrink-0" />
                      ) : (
                        <span
                          className={`
                            flex
                            h-4
                            w-4
                            shrink-0
                            items-center
                            justify-center
                            rounded-full
                            border
                            text-[10px]
                            ${
                              active
                                ? "border-primary"
                                : "border-muted-foreground/40"
                            }
                          `}
                        />
                      )}

                      <span className="font-medium">
                        {tUnit("day", { day })}
                      </span>

                    </div>

                    <span className="text-xs text-muted-foreground">
                      {completed}/{units.length}
                    </span>

                  </div>

                  <div className="mt-1 ps-6 text-xs text-muted-foreground">
                    {tUnit("min", { count: minutes })}
                  </div>

                </button>
              );
            })}

          </div>

        </aside>

        {/* ------------------------------------------------ */}
        {/* Current Day */}
        {/* ------------------------------------------------ */}

        <div className="min-w-0 space-y-5">

          {/* Day header */}

          <section className="rounded-xl border bg-card p-6">

            <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">

              <div>

                <p className="text-sm font-medium text-primary">
                  {tUnit("day", { day: selectedDay })}
                </p>

                <h2 className="mt-1 text-2xl font-semibold">
                  {t("sessionTitle")}
                </h2>

                <p className="mt-2 text-sm leading-6 text-muted-foreground">
                  {t("sessionText")}
                </p>

              </div>

              <div className="flex shrink-0 items-center gap-2 rounded-lg bg-muted px-3 py-2 text-sm">

                <Clock className="h-4 w-4" />

                {tUnit("min", { count: dayMinutes })}

              </div>

            </div>

            {/* Day progress */}

            <div className="mt-5">

              <div className="mb-2 flex justify-between text-xs">

                <span className="text-muted-foreground">
                  {t("dayProgress")}
                </span>

                <span>
                  {dayCompletedUnits}/{dayUnits.length}
                </span>

              </div>

              <div className="h-1.5 overflow-hidden rounded-full bg-muted">

                <div
                  className="h-full rounded-full bg-primary transition-all duration-300"
                  style={{
                    width:
                      dayUnits.length === 0
                        ? "0%"
                        : `${
                            (dayCompletedUnits /
                              dayUnits.length) *
                            100
                          }%`,
                  }}
                />

              </div>

            </div>

          </section>

          {/* ------------------------------------------------ */}
          {/* Learning Units */}
          {/* ------------------------------------------------ */}

          <div className="space-y-4">

            {dayUnits.length === 0 ? (

              <div className="rounded-xl border border-dashed bg-card p-10 text-center">

                <BookOpen className="mx-auto h-8 w-8 text-muted-foreground" />

                <h3 className="mt-3 font-semibold">
                  {t("noActivities")}
                </h3>

                <p className="mt-1 text-sm text-muted-foreground">
                  {t("noActivitiesText")}
                </p>

              </div>

            ) : (

              dayUnits.map((unit) => {

                const Icon =
                  getUnitIcon(unit.type);

                return (
                  <article
                    key={unit.id}
                    className={`
                      rounded-xl
                      border
                      bg-card
                      p-5
                      transition-all
                      ${
                        unit.completed
                          ? "opacity-75"
                          : "hover:border-primary/40 hover:shadow-sm"
                      }
                    `}
                  >

                    <div className="flex gap-4">

                      {/* Completion indicator */}

                      <div className="pt-1">

                        {unit.completed ? (
                          <div className="flex h-6 w-6 items-center justify-center rounded-full bg-primary/10">
                            <Check className="h-4 w-4 text-primary" />
                          </div>
                        ) : (
                          <div className="h-6 w-6 rounded-full border-2 border-muted-foreground/30" />
                        )}

                      </div>

                      {/* Content */}

                      <div className="min-w-0 flex-1">

                        <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">

                          <div className="min-w-0">

                            <div className="flex items-center gap-2">

                              <Icon className={`h-4 w-4 ${unitColor(unit.type)}`} />

                              <span className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                                {getUnitTypeLabel(
                                  unit.type
                                )}
                              </span>

                            </div>

                            <h3
                              className={`
                                mt-1
                                text-lg
                                font-semibold
                                ${
                                  unit.completed
                                    ? "line-through"
                                    : ""
                                }
                              `}
                            >
                              {unit.title}
                            </h3>

                          </div>

                          {unit.estimated_minutes != null && (
                            <div className="flex shrink-0 items-center gap-1 text-sm text-muted-foreground">

                              <Clock className="h-4 w-4" />

                              {tUnit("min", { count: unit.estimated_minutes })}

                            </div>
                          )}

                        </div>

                        {unit.description && (
                          <p className="mt-3 max-w-3xl text-sm leading-6 text-muted-foreground">
                            {unit.description}
                          </p>
                        )}

                        {/* Action */}

                        <div className="mt-5 flex flex-wrap items-center gap-3">

                          {isReady(unit) ? (
                          <Link
                            href={`/roadmaps/${roadmapId}/task/${task.id}/learn/${unit.id}`}
                            className="
                              inline-flex
                              items-center
                              gap-2
                              rounded-lg
                              bg-primary
                              px-4
                              py-2
                              text-sm
                              font-medium
                              text-primary-foreground
                              transition-opacity
                              hover:opacity-90
                            "
                          >
                            {unit.completed ? t("review") : unitAction(unit.type, tUnit)}

                            <ChevronRight className="h-4 w-4 rtl:rotate-180" />
                          </Link>
                          ) : (
                            <span className="inline-flex items-center gap-2 rounded-lg bg-muted px-4 py-2 text-sm text-muted-foreground">
                              {unit.status === "failed" ? (
                                <TriangleAlert className="h-4 w-4 text-destructive" />
                              ) : (
                                <Loader2 className="h-4 w-4 animate-spin" />
                              )}
                              {unit.status === "failed" ? t("lessonFailed") : t("lessonWriting")}
                            </span>
                          )}

                          {unit.resource_url && (
                            <a
                              href={unit.resource_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="
                                inline-flex
                                items-center
                                gap-2
                                rounded-lg
                                border
                                px-4
                                py-2
                                text-sm
                                font-medium
                                transition-colors
                                hover:bg-muted
                              "
                            >
                              {isSearchLink(unit.resource_url) ? t("findYoutube") : t("openResource")}
                              <ExternalLink className="h-4 w-4" />
                            </a>
                          )}

                        </div>

                      </div>

                    </div>

                  </article>
                );
              })

            )}

          </div>

          {/* ------------------------------------------------ */}
          {/* Day completed */}
          {/* ------------------------------------------------ */}

          {dayUnits.length > 0 &&
            dayCompletedUnits === dayUnits.length && (
              <section className="rounded-xl border bg-card p-6">

                <div className="flex items-center gap-3">

                  <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10">

                    <CheckCircle2 className="h-5 w-5 text-primary" />

                  </div>

                  <div>

                    <h3 className="font-semibold">
                      {t("dayDone", { day: selectedDay })}
                    </h3>

                    <p className="text-sm text-muted-foreground">
                      {t("dayDoneText")}
                    </p>

                  </div>

                </div>

                {days.includes(selectedDay + 1) && (
                  <button
                    type="button"
                    onClick={() =>
                      setSelectedDay(
                        selectedDay + 1
                      )
                    }
                    className="
                      mt-5
                      inline-flex
                      items-center
                      gap-2
                      rounded-lg
                      border
                      px-4
                      py-2
                      text-sm
                      font-medium
                      transition-colors
                      hover:bg-muted
                    "
                  >
                    {t("toDay", { day: selectedDay + 1 })}

                    <ChevronRight className="h-4 w-4 rtl:rotate-180" />
                  </button>
                )}

              </section>
            )}

        </div>

      </div>

      <RecommendedResources taskId={task.id} />

      {furtherReading.length > 0 && (
        <section className="rounded-xl border bg-card p-6">
          <h2 className="text-sm font-semibold">{t("furtherReading")}</h2>
          <ul className="mt-3 space-y-2">
            {furtherReading.map((url) => (
              <li key={url}>
                <a
                  href={url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 break-all text-sm text-primary hover:underline"
                >
                  {url}
                  <ExternalLink className="h-3.5 w-3.5 shrink-0" />
                </a>
              </li>
            ))}
          </ul>
        </section>
      )}

      {totalUnits > 0 && completedUnits === totalUnits && (
        <TaskQuiz taskId={task.id} />
      )}

    </div>
  );
}