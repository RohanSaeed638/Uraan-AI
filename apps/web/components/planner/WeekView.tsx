"use client";

import { useLocale, useTranslations } from "next-intl";
import { Coffee, Moon } from "lucide-react";

import {
  weekdayNames,
  addDays,
  dateKey,
  dayStatus,
  formatDuration,
  formatTime,
} from "@/lib/planner";
import { cn } from "@/lib/utils";
import { CalendarSchedule, PlannedLesson } from "@/types/api";

import { Card } from "@/components/ui/card";

import DropZone from "./DropZone";
import LessonChip from "./LessonChip";

interface Props {
  schedule: CalendarSchedule;
  weekStart: Date;
  onMove: (lesson: PlannedLesson, date: string) => void;
  onDropLesson: (lessonId: string, date: string) => void;
  onOpenDay: (date: Date) => void;
}

/** Seven days side by side. Each day is one study block with its lessons. */
export default function WeekView({ schedule, weekStart, onMove, onDropLesson, onOpenDay }: Props) {
  const t = useTranslations("planner");
  const tUnit = useTranslations("unit");
  const locale = useLocale();
  const weekdays = weekdayNames(locale);
  const byDate = new Map(schedule.days.map((d) => [d.date, d]));

  return (
    <div className="-mx-1 overflow-x-auto px-1 pb-2">
      <div className="grid min-w-[56rem] grid-cols-7 gap-3">
        {Array.from({ length: 7 }, (_, i) => {
          const date = addDays(weekStart, i);
          const key = dateKey(date);
          const planned = byDate.get(key);
          const status = dayStatus(date, schedule, planned);
          const isToday = key === schedule.today;
          const past = key < schedule.today;

          return (
            <DropZone
              key={key}
              date={key}
              today={schedule.today}
              onDropLesson={onDropLesson}
              className="min-w-0 rounded-3xl"
            >
              <Card
                className={cn(
                  "h-full min-h-56 gap-3 p-3",
                  isToday && "border-brand-gold/70 bg-brand-gold/5",
                  past && !planned && "opacity-60"
                )}
              >
                <button
                  type="button"
                  onClick={() => onOpenDay(date)}
                  className="group flex items-baseline justify-between gap-2 rounded-xl text-start outline-none focus-visible:ring-3 focus-visible:ring-ring/40"
                  aria-label={t("openDay", { day: `${weekdays[i]} ${date.getDate()}` })}
                >
                  <span className="text-xs font-semibold uppercase tracking-wide text-foreground/70 group-hover:text-foreground">
                    {weekdays[i]}
                  </span>
                  <span
                    className={cn(
                      "flex size-7 items-center justify-center rounded-full text-sm font-bold",
                      isToday ? "bg-brand-gold text-[#241a05]" : "group-hover:bg-muted"
                    )}
                  >
                    {date.getDate()}
                  </span>
                </button>

                {planned ? (
                  <>
                    <p className="text-[11px] font-medium text-muted-foreground">
                      {t("range", { start: formatTime(planned.start, locale), end: formatTime(planned.end, locale) })} ·{" "}
                      {formatDuration(planned.minutes, tUnit)}
                    </p>
                    <div className="space-y-1.5">
                      {planned.units.map((lesson) => (
                        <LessonChip
                          key={lesson.id}
                          lesson={lesson}
                          onMove={(l) => onMove(l, key)}
                        />
                      ))}
                    </div>
                  </>
                ) : (
                  <div className="flex flex-1 flex-col items-center justify-center gap-1.5 text-center text-xs text-muted-foreground">
                    {status === "blocked" && (
                      <>
                        <Moon size={16} aria-hidden /> {t("dayOff")}
                      </>
                    )}
                    {status === "rest" && (
                      <>
                        <Coffee size={16} aria-hidden /> {t("restDay")}
                      </>
                    )}
                    {status === "free" && <span>{past ? "" : t("free")}</span>}
                  </div>
                )}
              </Card>
            </DropZone>
          );
        })}
      </div>
    </div>
  );
}
