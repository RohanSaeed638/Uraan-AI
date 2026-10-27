"use client";

import { useTranslations } from "next-intl";
import { CalendarClock, Pin, TriangleAlert } from "lucide-react";

import { getUnitMeta, unitColor } from "@/lib/units";
import { cn } from "@/lib/utils";
import { PlannedLesson } from "@/types/api";

interface Props {
  lesson: PlannedLesson;
  onMove: (lesson: PlannedLesson) => void;
  /** Hide the time (month view is too small for it). */
  compact?: boolean;
  /** Can be picked up and dropped on another day. */
  draggable?: boolean;
  onDragStart?: (lesson: PlannedLesson) => void;
}

/** One lesson on the calendar: a small, draggable card with a Move button for
 * keyboards and touch screens, where dragging is not available. */
export default function LessonChip({
  lesson,
  onMove,
  compact = false,
  draggable = true,
  onDragStart,
}: Props) {
  const t = useTranslations("planner.lesson");
  const meta = getUnitMeta(lesson.type);
  const Icon = meta.icon;

  return (
    <div
      draggable={draggable}
      onDragStart={(e) => {
        e.dataTransfer.setData("text/plain", lesson.id);
        e.dataTransfer.effectAllowed = "move";
        onDragStart?.(lesson);
      }}
      className={cn(
        "group flex items-center gap-1.5 rounded-xl border px-2 py-1.5 text-start text-xs transition",
        draggable && "cursor-grab active:cursor-grabbing",
        lesson.missed
          ? "border-destructive/50 bg-destructive/10"
          : "border-border bg-card hover:border-brand-gold/60 hover:bg-brand-gold/10"
      )}
    >
      <Icon size={13} className={cn("shrink-0", unitColor(lesson.type))} aria-hidden />

      <span className="min-w-0 flex-1">
        <span className="block truncate font-medium" title={lesson.title}>
          {lesson.title}
        </span>
        {!compact && (
          <span className="block truncate text-[11px] text-muted-foreground">
            {lesson.minutes} min
          </span>
        )}
      </span>

      {lesson.missed && (
        <TriangleAlert size={13} className="shrink-0 text-destructive" aria-label={t("missed")} />
      )}
      {lesson.pinned && !lesson.missed && (
        <Pin size={12} className="shrink-0 text-brand-gold" aria-label={t("pinned")} />
      )}

      <button
        type="button"
        onClick={() => onMove(lesson)}
        aria-label={t("move", { title: lesson.title })}
        className="shrink-0 rounded-full p-1 text-muted-foreground opacity-60 transition hover:bg-brand-gold/20 hover:text-foreground hover:opacity-100 focus-visible:opacity-100 group-hover:opacity-100"
      >
        <CalendarClock size={13} />
      </button>
    </div>
  );
}
