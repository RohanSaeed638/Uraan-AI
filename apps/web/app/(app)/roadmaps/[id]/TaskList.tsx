"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { ChevronDown, Flag } from "lucide-react";

import { TaskCard } from "./TaskCard";
import TaskDetailsDialog from "./TaskDetailsDialog";

import { api } from "@/lib/api/client";
import { Progress } from "@/components/ui/progress";
import { cn } from "@/lib/utils";

import {
  Roadmap,
  RoadmapPhase,
  RoadmapTask,
} from "@/types/roadmap";

/** Tasks under their week heading; older roadmaps with no weeks stay one list. */
function groupByWeek(tasks: RoadmapTask[]) {
  const groups: { week: number | null; tasks: RoadmapTask[] }[] = [];

  for (const task of tasks) {
    const week = task.week ?? null;
    const last = groups[groups.length - 1];

    if (last && last.week === week) {
      last.tasks.push(task);
    } else {
      groups.push({ week, tasks: [task] });
    }
  }

  return groups;
}

interface TaskListProps {
  roadmap: Roadmap;
  onRoadmapChange?: (roadmap: Roadmap) => void;
}

export default function TaskList({
  roadmap: initialRoadmap,
  onRoadmapChange,
}: TaskListProps) {
  const t = useTranslations("roadmaps.tasks");

  /*
   * Local roadmap state.
   *
   * This allows task completion to update
   * immediately without waiting for the API.
   */
  const [roadmap, setRoadmap] =
    useState<Roadmap>(initialRoadmap);

  /*
   * Currently selected task for the details dialog.
   */
  const [selectedTask, setSelectedTask] =
    useState<RoadmapTask | null>(null);

  /*
   * Controls TaskDetailsDialog visibility.
   */
  const [taskDialogOpen, setTaskDialogOpen] =
    useState(false);

  /*
   * Keeps track of which task is currently
   * being updated.
   */
  const [updatingTaskId, setUpdatingTaskId] =
    useState<string | null>(null);

  /*
   * Calculate overall roadmap progress.
   */
  function calculateProgress(
    phases: RoadmapPhase[]
  ): number {
    const tasks = phases.flatMap(
      (phase) => phase.tasks
    );

    if (tasks.length === 0) {
      return 0;
    }

    const completed = tasks.filter(
      (task) => task.completed
    ).length;

    return Math.round(
      (completed / tasks.length) * 100
    );
  }

  /*
   * Calculate progress for a single phase.
   */
  function calculatePhaseProgress(
    phase: RoadmapPhase
  ): number {
    if (phase.tasks.length === 0) {
      return 0;
    }

    const completed = phase.tasks.filter(
      (task) => task.completed
    ).length;

    return Math.round(
      (completed / phase.tasks.length) * 100
    );
  }

  /*
   * Open task details dialog.
   */
  function handleOpenTask(
    task: RoadmapTask
  ) {
    setSelectedTask(task);
    setTaskDialogOpen(true);
  }

  /*
   * Close task details dialog.
   */
  function handleTaskDialogChange(
    open: boolean
  ) {
    setTaskDialogOpen(open);

    if (!open) {
      setSelectedTask(null);
    }
  }

  /*
   * Update task completion.
   *
   * Uses optimistic UI:
   *
   * 1. Update task immediately.
   * 2. Update roadmap progress immediately.
   * 3. Send PATCH request.
   * 4. Roll back if API fails.
   */
  async function updateTask(
    taskId: string,
    completed: boolean
  ) {
    /*
     * Don't allow another task update
     * while one is already being saved.
     */
    if (updatingTaskId) {
      return;
    }

    /*
     * Save current roadmap state so we
     * can restore it if the API fails.
     */
    const previousRoadmap = roadmap;

    /*
     * Create optimistic roadmap state.
     */
    const updatedRoadmap: Roadmap = {
      ...roadmap,

      phases: roadmap.phases.map(
        (phase: RoadmapPhase) => ({
          ...phase,

          tasks: phase.tasks.map(
            (task: RoadmapTask) =>
              task.id === taskId
                ? {
                    ...task,
                    completed,
                  }
                : task
          ),
        })
      ),
    };

    /*
     * Update TaskList immediately.
     */
    setRoadmap(updatedRoadmap);

    /*
     * Update parent RoadmapDetailClient
     * immediately so its overall progress
     * percentage changes live.
     */
    onRoadmapChange?.(updatedRoadmap);

    /*
     * Keep the selected task in sync.
     *
     * This is important because the dialog
     * may currently be open when the user
     * clicks "Mark as complete".
     */
    setSelectedTask((currentTask) => {
      if (!currentTask) {
        return null;
      }

      if (currentTask.id !== taskId) {
        return currentTask;
      }

      return {
        ...currentTask,
        completed,
      };
    });

    try {
      setUpdatingTaskId(taskId);

      /*
       * Persist the change.
       */
      await api.patch(
        `/roadmaps/tasks/${taskId}`,
        {
          completed,
        }
      );
    } catch (error) {
      console.error(
        "Failed to update task:",
        error
      );

      /*
       * Roll back TaskList.
       */
      setRoadmap(previousRoadmap);

      /*
       * Roll back parent progress.
       */
      onRoadmapChange?.(previousRoadmap);

      /*
       * Roll back selected task if
       * the dialog is open.
       */
      setSelectedTask((currentTask) => {
        if (!currentTask) {
          return null;
        }

        if (currentTask.id !== taskId) {
          return currentTask;
        }

        const previousTask =
          previousRoadmap.phases
            .flatMap(
              (phase) => phase.tasks
            )
            .find(
              (task) =>
                task.id === taskId
            );

        return previousTask ?? currentTask;
      });
    } finally {
      setUpdatingTaskId(null);
    }
  }

  return (
    <>
      {/* ============================= */}
      {/* Roadmap Phases */}
      {/* ============================= */}

      <section className="mt-8 space-y-4">
        {roadmap.phases.map((phase: RoadmapPhase, index: number) => {
          const phaseProgress = calculatePhaseProgress(phase);

          const completedTasks = phase.tasks.filter(
            (task) => task.completed
          ).length;

          return (
            <details
              key={phase.id}
              className="group overflow-hidden rounded-3xl border border-border bg-card"
              open={index === 0}
            >
              {/* ============================= */}
              {/* Phase Header */}
              {/* ============================= */}

              <summary className="flex cursor-pointer list-none items-center gap-3 p-4 sm:gap-4 sm:p-6">
                <span
                  className={cn(
                    "flex size-9 shrink-0 items-center justify-center rounded-full text-sm font-semibold",
                    phaseProgress === 100
                      ? "bg-emerald-500/15 text-emerald-500"
                      : "bg-brand-gold/15 text-brand-gold-deep dark:text-brand-gold"
                  )}
                >
                  {index + 1}
                </span>

                <div className="min-w-0 flex-1">
                  <div className="flex items-center justify-between gap-4">
                    <h2 className="font-heading text-base font-semibold sm:text-lg">
                      {phase.title}
                    </h2>

                    <span className="shrink-0 text-sm font-medium text-muted-foreground">
                      {completedTasks}/{phase.tasks.length}
                    </span>
                  </div>

                  <p className="mt-1 line-clamp-1 text-sm text-muted-foreground">
                    {phase.description}
                  </p>

                  <div className="mt-3">
                    <Progress value={phaseProgress} className="h-1.5" />
                  </div>
                </div>

                <ChevronDown className="size-5 shrink-0 text-muted-foreground transition-transform duration-200 group-open:rotate-180" />
              </summary>

              {/* ============================= */}
              {/* Tasks */}
              {/* ============================= */}

              <div className="border-t border-border p-3 sm:p-6">
                {phase.milestones && phase.milestones.length > 0 && (
                  <div className="mb-5 rounded-2xl bg-brand-violet/10 p-4">
                    <p className="flex items-center gap-2 text-sm font-semibold text-brand-violet">
                      <Flag size={14} /> {t("milestones")}
                    </p>
                    <ul className="mt-2 space-y-1 text-sm">
                      {phase.milestones.map((milestone) => (
                        <li key={milestone} className="flex gap-2">
                          <span aria-hidden className="text-brand-violet">&#8226;</span>
                          <span className="min-w-0 break-words">{milestone}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {phase.tasks.length === 0 ? (
                  <p className="text-sm text-muted-foreground">
                    {t("none")}
                  </p>
                ) : (
                  <div className="space-y-5">
                    {groupByWeek(phase.tasks).map((group) => (
                      <div key={group.week ?? "none"} className="space-y-3">
                        {group.week !== null && (
                          <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                            {t("week", { week: group.week })}
                          </h3>
                        )}
                        {group.tasks.map((task: RoadmapTask) => (
                          <TaskCard
                            key={task.id}
                            task={task}
                            loading={updatingTaskId === task.id}
                            onToggle={updateTask}
                            onOpen={handleOpenTask}
                          />
                        ))}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </details>
          );
        })}
      </section>

      {/* ============================= */}
      {/* Task Details Dialog */}
      {/* ============================= */}

      <TaskDetailsDialog
        roadmapId={roadmap.id}
        task={selectedTask}
        open={taskDialogOpen}
        onOpenChange={handleTaskDialogChange}
        onToggle={updateTask}
      />
    </>
  );
}