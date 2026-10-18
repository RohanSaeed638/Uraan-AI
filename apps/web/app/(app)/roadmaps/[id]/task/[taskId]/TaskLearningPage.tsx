"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  BookOpen,
  Check,
  CheckCircle2,
  ChevronRight,
  Clock,
  ExternalLink,
  FolderKanban,
  PlayCircle,
  Target,
} from "lucide-react";

import { RoadmapTask } from "@/types/roadmap";

import TaskQuiz from "./TaskQuiz";

interface TaskLearningPageProps {
  roadmapId: string;
  task: RoadmapTask;
}

export default function TaskLearningPage({
  roadmapId,
  task,
}: TaskLearningPageProps) {
  const learningUnits = useMemo(
    () => task.learning_units ?? [],
    [task.learning_units]
  );

  /*
   * Get all available days.
   */
  const days = useMemo(() => {
    return Array.from(
      new Set(learningUnits.map((unit) => unit.day))
    ).sort((a, b) => a - b);
  }, [learningUnits]);
  console.log("days",days);
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
      (unit) => !unit.completed
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
  const getUnitTypeLabel = (type: string) => {
    switch (type.toLowerCase()) {
      case "reading":
        return "Reading";

      case "video":
        return "Video";

      case "project":
        return "Project";

      case "practice":
        return "Practice";

      default:
        return type;
    }
  };

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

      case "practice":
        return Target;

      default:
        return BookOpen;
    }
  };

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
        <ArrowLeft className="h-4 w-4" />
        Back to roadmap
      </Link>

      {/* -------------------------------------------------- */}
      {/* Task Header */}
      {/* -------------------------------------------------- */}

      <section className="rounded-xl border bg-card p-6 md:p-8">

        <div className="flex flex-col gap-6 md:flex-row md:items-start md:justify-between">

          <div className="min-w-0">

            <div className="mb-3 flex items-center gap-2 text-sm text-muted-foreground">
              <span>Task</span>

              <ChevronRight className="h-4 w-4" />

              <span>Learning</span>
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
                {task.estimated_hours ?? 0} hours
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
              Learning progress
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

      {/* -------------------------------------------------- */}
      {/* Continue Learning */}
      {/* -------------------------------------------------- */}

      {nextUnit && (
        <section className="rounded-xl border bg-primary/5 p-5">

          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">

            <div className="flex items-start gap-3">

              <div className="rounded-lg bg-primary/10 p-2">
                <PlayCircle className="h-5 w-5 text-primary" />
              </div>

              <div>

                <p className="text-sm font-medium text-primary">
                  Continue learning
                </p>

                <h2 className="mt-1 font-semibold">
                  {nextUnit.title}
                </h2>

                <div className="mt-1 flex items-center gap-2 text-sm text-muted-foreground">

                  <span>
                    Day {nextUnit.day}
                  </span>

                  {nextUnit.estimated_minutes != null && (
                    <>
                      <span>•</span>

                      <span>
                        {nextUnit.estimated_minutes} min
                      </span>
                    </>
                  )}

                </div>

              </div>

            </div>

            <button
              type="button"
              className="
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
              Continue
              <ChevronRight className="h-4 w-4" />
            </button>

          </div>

        </section>
      )}

      {/* -------------------------------------------------- */}
      {/* Main Learning Area */}
      {/* -------------------------------------------------- */}

      <div className="grid gap-6 lg:grid-cols-[240px_minmax(0,1fr)]">

        {/* ------------------------------------------------ */}
        {/* Learning Plan Sidebar */}
        {/* ------------------------------------------------ */}

        <aside className="h-fit rounded-xl border bg-card p-4">

          <div className="mb-4 px-2">

            <h2 className="text-sm font-semibold">
              Your learning plan
            </h2>

            <p className="mt-1 text-xs text-muted-foreground">
              {days.length}{" "}
              {days.length === 1 ? "day" : "days"}
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
                    text-left
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
                        Day {day}
                      </span>

                    </div>

                    <span className="text-xs text-muted-foreground">
                      {completed}/{units.length}
                    </span>

                  </div>

                  <div className="mt-1 pl-6 text-xs text-muted-foreground">
                    {minutes} min
                  </div>

                </button>
              );
            })}

          </div>

        </aside>

        {/* ------------------------------------------------ */}
        {/* Current Day */}
        {/* ------------------------------------------------ */}

        <main className="min-w-0 space-y-5">

          {/* Day header */}

          <section className="rounded-xl border bg-card p-6">

            <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">

              <div>

                <p className="text-sm font-medium text-primary">
                  Day {selectedDay}
                </p>

                <h2 className="mt-1 text-2xl font-semibold">
                  Today&apos;s learning session
                </h2>

                <p className="mt-2 text-sm leading-6 text-muted-foreground">
                  Complete the activities below to
                  continue progressing through this task.
                </p>

              </div>

              <div className="flex shrink-0 items-center gap-2 rounded-lg bg-muted px-3 py-2 text-sm">

                <Clock className="h-4 w-4" />

                {dayMinutes} min

              </div>

            </div>

            {/* Day progress */}

            <div className="mt-5">

              <div className="mb-2 flex justify-between text-xs">

                <span className="text-muted-foreground">
                  Day progress
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
                  No learning activities yet
                </h3>

                <p className="mt-1 text-sm text-muted-foreground">
                  Learning material for this day
                  hasn&apos;t been generated yet.
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

                          <div>

                            <div className="flex items-center gap-2">

                              <Icon className="h-4 w-4 text-primary" />

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

                              {unit.estimated_minutes} min

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
                            {unit.completed
                              ? "Review"
                              : "Start"}

                            <ChevronRight className="h-4 w-4" />
                          </Link>

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
                              Resource

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
                      Day {selectedDay} completed
                    </h3>

                    <p className="text-sm text-muted-foreground">
                      Great work. You&apos;re ready to
                      continue to the next part.
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
                    Continue to Day{" "}
                    {selectedDay + 1}

                    <ChevronRight className="h-4 w-4" />
                  </button>
                )}

              </section>
            )}

        </main>

      </div>

      {totalUnits > 0 && completedUnits === totalUnits && (
        <TaskQuiz taskId={task.id} />
      )}

    </div>
  );
}