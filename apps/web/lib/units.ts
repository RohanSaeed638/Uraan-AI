import { BookOpen, Code2, FolderKanban, PlayCircle, LucideIcon } from "lucide-react";
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

const icons: Record<string, LucideIcon> = {
  reading: BookOpen,
  video: PlayCircle,
  project: FolderKanban,
  exercise: Code2,
};

/** Icon and message key for a lesson type; labels live in messages/*.json under `unit`. */
export function getUnitMeta(type: string) {
  const key = type?.toLowerCase();

  return { key: key in icons ? key : null, icon: icons[key] ?? BookOpen };
}

/** The `unit` translator from next-intl (`useTranslations("unit")` / `getTranslations("unit")`). */
type UnitT = (key: string, values?: Record<string, string | number>) => string;

export function unitLabel(type: string, t: UnitT) {
  const { key } = getUnitMeta(type);

  return key ? t(`type.${key}`) : type;
}

export function unitAction(type: string, t: UnitT) {
  const { key } = getUnitMeta(type);

  return key ? t(`action.${key}`) : t("action.start");
}

export function formatMinutes(total: number, t: UnitT) {
  if (total < 60) return t("minutesShort", { count: total });

  const hours = Math.floor(total / 60);
  const minutes = total % 60;

  return minutes ? t("hoursMinutesShort", { hours, minutes }) : t("hoursShort", { hours });
}

/** A YouTube results page, used when no specific video could be verified. */
export function isSearchLink(url?: string | null) {
  return !!url && url.includes("youtube.com/results");
}

const typeColors: Record<string, string> = {
  reading: "text-sky-600 dark:text-sky-400",
  video: "text-rose-600 dark:text-rose-400",
  project: "text-amber-600 dark:text-amber-400",
  exercise: "text-emerald-600 dark:text-emerald-400",
};

export function unitColor(type: string) {
  return typeColors[type?.toLowerCase()] ?? "text-primary";
}
