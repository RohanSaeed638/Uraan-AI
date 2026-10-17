import { BookOpen, FolderKanban, PlayCircle, LucideIcon } from "lucide-react";
import { LearningUnit, Roadmap } from "@/types/roadmap";

export interface UnitContext {
  unit: LearningUnit;
  roadmapId: string;
  roadmapTitle: string;
  roadmapStatus: string;
  phaseTitle: string;
  taskId: string;
  taskTitle: string;
}

/** All units across roadmaps, in the order a learner would meet them. */
export function flattenUnits(roadmaps: Roadmap[]): UnitContext[] {
  return roadmaps.flatMap((roadmap) =>
    [...(roadmap.phases ?? [])]
      .sort((a, b) => a.order - b.order)
      .flatMap((phase) =>
        [...(phase.tasks ?? [])]
          .sort((a, b) => a.order - b.order)
          .flatMap((task) =>
            [...(task.learning_units ?? [])]
              .sort((a, b) => a.day - b.day || a.order - b.order)
              .map((unit) => ({
                unit,
                roadmapId: roadmap.id,
                roadmapTitle: roadmap.title,
                roadmapStatus: roadmap.status,
                phaseTitle: phase.title,
                taskId: task.id,
                taskTitle: task.title,
              }))
          )
      )
  );
}

export function unitHref(c: UnitContext) {
  return `/roadmaps/${c.roadmapId}/task/${c.taskId}/learn/${c.unit.id}`;
}

const meta: Record<string, { label: string; icon: LucideIcon }> = {
  reading: { label: "Reading", icon: BookOpen },
  video: { label: "Video", icon: PlayCircle },
  project: { label: "Project", icon: FolderKanban },
};

export function getUnitMeta(type: string) {
  return meta[type?.toLowerCase()] ?? { label: type, icon: BookOpen };
}

export function formatMinutes(total: number) {
  if (total < 60) return `${total}m`;
  const h = Math.floor(total / 60);
  const m = total % 60;
  return m ? `${h}h ${m}m` : `${h}h`;
}
