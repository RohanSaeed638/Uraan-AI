// "use client";

// import { useState } from "react";
// import { ChevronDown } from "lucide-react";

// import { TaskCard } from "./TaskCard";
// import { api } from "@/lib/api/client";

// import {
//   Roadmap,
//   RoadmapPhase,
//   RoadmapTask,
// } from "@/types/roadmap";

// interface TaskListProps {
//   roadmap: Roadmap;
//   onRoadmapChange?: (roadmap: Roadmap) => void;
// }

// export default function TaskList({
//   roadmap,
//   onRoadmapChange,
// }: TaskListProps) {
//   const [updatingTaskId, setUpdatingTaskId] =
//     useState<string | null>(null);

//   function calculatePhaseProgress(
//     phase: RoadmapPhase
//   ) {
//     if (phase.tasks.length === 0) {
//       return 0;
//     }

//     const completed = phase.tasks.filter(
//       (task) => task.completed
//     ).length;

//     return Math.round(
//       (completed / phase.tasks.length) * 100
//     );
//   }

//   async function updateTask(
//     taskId: string,
//     completed: boolean
//   ) {
//     if (updatingTaskId) {
//       return;
//     }

//     const previousRoadmap = roadmap;

//     // Optimistic update
//     const updatedRoadmap: Roadmap = {
//       ...roadmap,

//       phases: roadmap.phases.map(
//         (phase: RoadmapPhase) => ({
//           ...phase,

//           tasks: phase.tasks.map(
//             (task: RoadmapTask) =>
//               task.id === taskId
//                 ? {
//                     ...task,
//                     completed,
//                   }
//                 : task
//           ),
//         })
//       ),
//     };

//     // Immediately update parent
//     onRoadmapChange?.(updatedRoadmap);

//     try {
//       setUpdatingTaskId(taskId);

//       await api.patch(
//         `/roadmaps/tasks/${taskId}`,
//         {
//           completed,
//         }
//       );
//     } catch (error) {
//       console.error(
//         "Failed to update task:",
//         error
//       );

//       // Rollback
//       onRoadmapChange?.(previousRoadmap);
//     } finally {
//       setUpdatingTaskId(null);
//     }
//   }

//   return (
//     <section className="mt-10 space-y-5">
//       {roadmap.phases.map(
//         (phase: RoadmapPhase) => {
//           const phaseProgress =
//             calculatePhaseProgress(phase);

//           const completedTasks =
//             phase.tasks.filter(
//               (task) => task.completed
//             ).length;

//           return (
//             <details
//               key={phase.id}
//               className="group rounded-xl border bg-card"
//             >
//               <summary
//                 className="
//                   flex
//                   cursor-pointer
//                   list-none
//                   items-center
//                   justify-between
//                   gap-6
//                   p-6
//                 "
//               >
//                 <div className="min-w-0 flex-1">
//                   <div className="flex items-center justify-between gap-4">
//                     <h2 className="text-xl font-semibold">
//                       {phase.title}
//                     </h2>

//                     <span className="text-sm font-medium text-muted-foreground">
//                       {completedTasks}/
//                       {phase.tasks.length}
//                     </span>
//                   </div>

//                   <p className="mt-2 text-sm text-muted-foreground">
//                     {phase.description}
//                   </p>

//                   {/* Phase progress */}
//                   <div className="mt-4">
//                     <div className="mb-1 flex justify-between text-xs text-muted-foreground">
//                       <span>
//                         Phase progress
//                       </span>

//                       <span>
//                         {phaseProgress}%
//                       </span>
//                     </div>

//                     <div className="h-2 overflow-hidden rounded-full bg-muted">
//                       <div
//                         className="
//                           h-full
//                           rounded-full
//                           bg-primary
//                           transition-all
//                           duration-300
//                         "
//                         style={{
//                           width: `${phaseProgress}%`,
//                         }}
//                       />
//                     </div>
//                   </div>
//                 </div>

//                 <ChevronDown
//                   className="
//                     h-5
//                     w-5
//                     shrink-0
//                     transition-transform
//                     group-open:rotate-180
//                   "
//                 />
//               </summary>

//               <div className="border-t p-6">
//                 <div className="space-y-4">
//                   {phase.tasks.map(
//                     (task: RoadmapTask) => (
//                       <TaskCard
//                         key={task.id}
//                         task={task}
//                         loading={
//                           updatingTaskId === task.id
//                         }
//                         onToggle={updateTask}
//                       />
//                     )
//                   )}
//                 </div>
//               </div>
//             </details>
//           );
//         }
//       )}
//     </section>
//   );
// }

"use client";

import { useState } from "react";
import { ChevronDown } from "lucide-react";

import { TaskCard } from "./TaskCard";
import TaskDetailsDialog from "./TaskDetailsDialog";

import { api } from "@/lib/api/client";

import {
  Roadmap,
  RoadmapPhase,
  RoadmapTask,
} from "@/types/roadmap";

interface TaskListProps {
  roadmap: Roadmap;
  onRoadmapChange?: (roadmap: Roadmap) => void;
}

export default function TaskList({
  roadmap: initialRoadmap,
  onRoadmapChange,
}: TaskListProps) {
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

      <section className="mt-10 space-y-5">
        {roadmap.phases.map(
          (phase: RoadmapPhase) => {
            const phaseProgress =
              calculatePhaseProgress(
                phase
              );

            const completedTasks =
              phase.tasks.filter(
                (task) =>
                  task.completed
              ).length;

            return (
              <details
                key={phase.id}
                className="
                  group
                  rounded-xl
                  border
                  bg-card
                "
              >
                {/* ============================= */}
                {/* Phase Header */}
                {/* ============================= */}

                <summary
                  className="
                    flex
                    cursor-pointer
                    list-none
                    items-center
                    justify-between
                    gap-6
                    p-6
                  "
                >
                  <div
                    className="
                      min-w-0
                      flex-1
                    "
                  >
                    {/* Title + task count */}

                    <div
                      className="
                        flex
                        items-center
                        justify-between
                        gap-4
                      "
                    >
                      <h2
                        className="
                          text-xl
                          font-semibold
                        "
                      >
                        {phase.title}
                      </h2>

                      <span
                        className="
                          shrink-0
                          text-sm
                          font-medium
                          text-muted-foreground
                        "
                      >
                        {completedTasks}/
                        {phase.tasks.length}
                      </span>
                    </div>

                    {/* Phase description */}

                    <p
                      className="
                        mt-2
                        text-sm
                        text-muted-foreground
                      "
                    >
                      {phase.description}
                    </p>

                    {/* ============================= */}
                    {/* Phase Progress */}
                    {/* ============================= */}

                    <div className="mt-4">
                      <div
                        className="
                          mb-1
                          flex
                          justify-between
                          text-xs
                          text-muted-foreground
                        "
                      >
                        <span>
                          Phase progress
                        </span>

                        <span>
                          {phaseProgress}%
                        </span>
                      </div>

                      <div
                        className="
                          h-2
                          overflow-hidden
                          rounded-full
                          bg-muted
                        "
                      >
                        <div
                          className="
                            h-full
                            rounded-full
                            bg-primary
                            transition-all
                            duration-300
                          "
                          style={{
                            width: `${phaseProgress}%`,
                          }}
                        />
                      </div>
                    </div>
                  </div>

                  {/* Expand/collapse icon */}

                  <ChevronDown
                    className="
                      h-5
                      w-5
                      shrink-0
                      transition-transform
                      duration-200
                      group-open:rotate-180
                    "
                  />
                </summary>

                {/* ============================= */}
                {/* Tasks */}
                {/* ============================= */}

                <div
                  className="
                    border-t
                    p-6
                  "
                >
                  {phase.tasks.length === 0 ? (
                    <p
                      className="
                        text-sm
                        text-muted-foreground
                      "
                    >
                      No tasks available for
                      this phase.
                    </p>
                  ) : (
                    <div className="space-y-4">
                      {phase.tasks.map(
                        (
                          task: RoadmapTask
                        ) => (
                          <TaskCard
                            key={task.id}
                            task={task}
                            loading={
                              updatingTaskId ===
                              task.id
                            }
                            onToggle={
                              updateTask
                            }
                            onOpen={
                              handleOpenTask
                            }
                          />
                        )
                      )}
                    </div>
                  )}
                </div>
              </details>
            );
          }
        )}
      </section>

      {/* ============================= */}
      {/* Task Details Dialog */}
      {/* ============================= */}

      <TaskDetailsDialog
        task={selectedTask}
        open={taskDialogOpen}
        onOpenChange={
          handleTaskDialogChange
        }
        onToggle={updateTask}
      />
    </>
  );
}