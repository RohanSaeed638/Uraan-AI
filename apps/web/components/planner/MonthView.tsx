"use client";

import { useLocale, useTranslations } from "next-intl";

import { weekdayNames, addDays, dateKey, formatDuration, startOfWeek, weekdayIndex } from "@/lib/planner";
import { cn } from "@/lib/utils";
import { CalendarSchedule, PlannedLesson } from "@/types/api";

import { Card } from "@/components/ui/card";

import DropZone from "./DropZone";
import LessonChip from "./LessonChip";

interface Props {
  schedule: CalendarSchedule;
  /** Any date in the month to show. */
  month: Date;
  onMove: (lesson: PlannedLesson, date: string) => void;
  onDropLesson: (lessonId: string, date: string) => void;
  onOpenDay: (date: Date) => void;
}

const MAX_SHOWN = 2;

/** The whole month. Each day shows how full it is and its first lessons; a
 * day is a drop target and opens in the day view when clicked. */
export default function MonthView({ schedule, month, onMove, onDropLesson, onOpenDay }: Props) {
  const t = useTranslations("planner");
  const tUnit = useTranslations("unit");
  const locale = useLocale();
  const byDate = new Map(schedule.days.map((d) => [d.date, d]));

  const first = new Date(month.getFullYear(), month.getMonth(), 1);
  const gridStart = startOfWeek(first);
  const last = new Date(month.getFullYear(), month.getMonth() + 1, 0);
  const weeks = Math.ceil((weekdayIndex(first) + last.getDate()) / 7);

  return (
    <Card className="gap-3 p-3 sm:p-4">
      <div className="grid grid-cols-7 gap-1.5 text-center text-[11px] font-semibold uppercase tracking-wide text-muted-foreground sm:gap-2">
        {weekdayNames(locale).map((d) => (
          <span key={d}>{d}</span>
        ))}
      </div>

      <div className="grid grid-cols-7 gap-1.5 sm:gap-2">
        {Array.from({ length: weeks * 7 }, (_, i) => {
          const date = addDays(gridStart, i);
          const key = dateKey(date);
          const inMonth = date.getMonth() === month.getMonth();
          const planned = byDate.get(key);
          const isToday = key === schedule.today;
          const capacity = schedule.availability.weekday_minutes[weekdayIndex(date)] || 0;
          const fill = planned && capacity > 0 ? Math.min(100, (planned.minutes / capacity) * 100) : planned ? 100 : 0;

          return (
            <DropZone
              key={key}
              date={key}
              today={schedule.today}
              onDropLesson={onDropLesson}
              className="min-w-0 rounded-2xl"
            >
              <div
                className={cn(
                  "flex min-h-24 flex-col gap-1 rounded-2xl border p-1.5 transition sm:min-h-28 sm:p-2",
                  inMonth ? "bg-card" : "bg-muted/30 opacity-50",
                  isToday ? "border-brand-gold/80 bg-brand-gold/5" : "border-border",
                  key < schedule.today && !planned && "opacity-60"
                )}
              >
                <button
                  type="button"
                  onClick={() => onOpenDay(date)}
                  aria-label={t("openDay", { day: `${date.getDate()}` })}
                  className="flex items-center justify-between gap-1 rounded-lg text-start outline-none focus-visible:ring-3 focus-visible:ring-ring/40"
                >
                  <span
                    className={cn(
                      "flex size-6 items-center justify-center rounded-full text-xs font-semibold",
                      isToday && "bg-brand-gold text-[#241a05]"
                    )}
                  >
                    {date.getDate()}
                  </span>
                  {planned && (
                    <span className="hidden text-[10px] text-muted-foreground sm:inline">
                      {formatDuration(planned.minutes, tUnit)}
                    </span>
                  )}
                </button>

                {planned && (
                  <>
                    <div className="h-1 overflow-hidden rounded-full bg-muted">
                      <div className="h-full rounded-full bg-brand-gold" style={{ width: `${fill}%` }} />
                    </div>

                    <div className="hidden space-y-1 sm:block">
                      {planned.units.slice(0, MAX_SHOWN).map((lesson) => (
                        <LessonChip
                          key={lesson.id}
                          lesson={lesson}
                          compact
                          onMove={(l) => onMove(l, key)}
                        />
                      ))}
                      {planned.units.length > MAX_SHOWN && (
                        <button
                          type="button"
                          onClick={() => onOpenDay(date)}
                          className="px-1 text-[11px] font-medium text-brand-gold-deep hover:underline dark:text-brand-gold"
                        >
                          {t("more", { count: planned.units.length - MAX_SHOWN })}
                        </button>
                      )}
                    </div>

                    <p className="text-[10px] text-muted-foreground sm:hidden">
                      {t("lessonCount", { count: planned.units.length })}
                    </p>
                  </>
                )}
              </div>
            </DropZone>
          );
        })}
      </div>
    </Card>
  );
}
