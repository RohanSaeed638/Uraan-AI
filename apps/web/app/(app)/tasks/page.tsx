import { getRoadmapDetails } from "@/lib/server/data";

import TasksClient, { FlatTask } from "./TasksClient";

export default async function TasksPage() {
  const roadmaps = await getRoadmapDetails();

  const tasks: FlatTask[] = roadmaps.flatMap((roadmap) =>
    [...(roadmap.phases ?? [])]
      .sort((a, b) => a.order - b.order)
      .flatMap((phase) =>
        [...(phase.tasks ?? [])]
          .sort((a, b) => a.order - b.order)
          .map((task) => ({
            id: task.id,
            title: task.title,
            completed: task.completed,
            estimatedHours: task.estimated_hours,
            roadmapId: roadmap.id,
            roadmapTitle: roadmap.title,
            phaseTitle: phase.title,
          }))
      )
  );

  return <TasksClient initialTasks={tasks} />;
}
