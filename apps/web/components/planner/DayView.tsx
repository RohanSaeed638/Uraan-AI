"use client";

import Link from "next/link";
import { useLocale, useTranslations } from "next-intl";
import { CalendarClock, Coffee, Moon, Pin, Sparkles, TriangleAlert } from "lucide-react";

import {
  weekdayNames,
  monthName,
  dateKey,
  dayStatus,
  formatDuration,
  formatTime,
  weekdayIndex,
} from "@/lib/planner";
import { getUnitMeta, unitColor } from "@/lib/units";
import { cn } from "@/lib/utils";
import { CalendarSchedule, PlannedLesson } from "@/types/api";

import EmptyState from "@/components/shared/EmptyState";
import Pill from "@/components/shared/Pill";
import { Button, buttonVariants } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

import DropZone from "./DropZone";

interface Props {
  schedule: CalendarSchedule;
  day: Date;
  onMove: (lesson: PlannedLesson, date: string) => void;
  onDropLesson: (lessonId: string, date: string) => void;
}

/** One day as a timeline: when each lesson starts, what it is, and how to open
 * or move it. */
export default function DayView({ schedule, day, onMove, onDropLesson }: Props) {
  const t = useTranslations("planner");
  const tUnit = useTranslations("unit");
  const locale = useLocale();
  const key = dateKey(day);
  const planned = schedule.days.find((d) => d.date === key);
  const status = dayStatus(day, schedule, planned);
  const heading = `${weekdayNames(locale, "long")[weekdayIndex(day)]}, ${day.getDate()} ${monthName(day.getMonth(), locale)}`;

  return (
    <DropZone date={key} today={schedule.today} onDropLesson={onDropLesson} className="rounded-3xl">
      <Card className="gap-5 p-5 sm:p-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="font-heading text-xl font-bold">{heading}</h2>
            {planned && (
              <p className="text-sm text-muted-foreground">
                {t("range", { start: formatTime(planned.start, locale), end: formatTime(planned.end, locale) })} ·{" "}
                {formatDuration(planned.minutes, tUnit)}
              </p>
            )}
          </div>
          {key === schedule.today && <Pill tone="gold">{t("today")}</Pill>}
        </div>

        {!planned ? (
          <EmptyState
            icon={status === "blocked" ? Moon : status === "rest" ? Coffee : Sparkles}
            title={
              status === "blocked"
                ? t("dayOff")
                : status === "rest"
                  ? t("restDay")
                  : key < schedule.today
                    ? t("nothingThen")
                    : t("freeDay")
            }
            text={status === "free" && key >= schedule.today ? t("dropHere") : undefined}
            className="border-0 p-6"
          />
        ) : (
          <ol className="space-y-3">
            {planned.units.map((lesson) => {
              const Icon = getUnitMeta(lesson.type).icon;

              return (
                <li key={lesson.id} className="flex gap-3 sm:gap-4">
                  <div className="w-16 shrink-0 pt-3 text-end text-xs font-medium text-muted-foreground">
                    {formatTime(lesson.start, locale)}
                  </div>

                  <div
                    draggable
                    onDragStart={(e) => {
                      e.dataTransfer.setData("text/plain", lesson.id);
                      e.dataTransfer.effectAllowed = "move";
                    }}
                    className={cn(
                      "flex min-w-0 flex-1 cursor-grab flex-col gap-2 rounded-2xl border p-3.5 transition sm:flex-row sm:items-center",
                      "border-s-4 active:cursor-grabbing",
                      lesson.missed
                        ? "border-destructive/50 border-s-destructive bg-destructive/5"
                        : "border-border border-s-brand-gold bg-card hover:border-brand-gold/60"
                    )}
                  >
                    <div className="flex min-w-0 flex-1 items-start gap-3">
                      <span className={cn("mt-0.5 shrink-0", unitColor(lesson.type))}>
                        <Icon size={18} />
                      </span>
                      <div className="min-w-0">
                        <p className="break-words font-medium">{lesson.title}</p>
                        <p className="truncate text-xs text-muted-foreground">
                          {lesson.task_title} · {lesson.minutes} min
                        </p>
                        {lesson.missed && (
                          <p className="mt-1 flex items-center gap-1 text-xs font-medium text-destructive">
                            <TriangleAlert size={12} /> {t("missed")}
                          </p>
                        )}
                        {lesson.pinned && !lesson.missed && (
                          <p className="mt-1 flex items-center gap-1 text-xs text-brand-gold-deep dark:text-brand-gold">
                            <Pin size={12} /> {t("pinned")}
                          </p>
                        )}
                      </div>
                    </div>

                    <div className="flex shrink-0 gap-2">
                      <Link
                        href={`/roadmaps/${schedule.roadmap_id}/task/${lesson.task_id}/learn/${lesson.id}`}
                        className={buttonVariants({ size: "sm" })}
                      >
                        {t("open")}
                      </Link>
                      <Button variant="outline" size="sm" className="gap-1.5" onClick={() => onMove(lesson, key)}>
                        <CalendarClock size={14} /> {t("moveButton")}
                      </Button>
                    </div>
                  </div>
                </li>
              );
            })}
          </ol>
        )}
      </Card>
    </DropZone>
  );
}
