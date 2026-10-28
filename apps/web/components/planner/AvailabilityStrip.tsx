"use client";

import { useLocale, useTranslations } from "next-intl";
import { Clock, RotateCcw, Sparkles } from "lucide-react";

import { weekdayNames, formatDuration, formatTime, shortDate, parseDate } from "@/lib/planner";
import { cn } from "@/lib/utils";
import { CalendarSchedule } from "@/types/api";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

/** When the plan thinks the learner studies: minutes on each weekday, the
 * usual start time, any blocked days, and what they told the AI. */
export default function AvailabilityStrip({
  schedule,
  onTell,
  onReset,
  resetting,
}: {
  schedule: CalendarSchedule;
  onTell: () => void;
  onReset: () => void;
  resetting: boolean;
}) {
  const t = useTranslations("planner");
  const tUnit = useTranslations("unit");
  const locale = useLocale();
  const weekdays = weekdayNames(locale);
  const { weekday_minutes, blocked_dates, start } = schedule.availability;
  const { note, active } = schedule.preferences;
  const max = Math.max(...weekday_minutes, 1);

  return (
    <Card className="gap-4 p-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="flex items-center gap-2 text-sm font-semibold">
          <Clock size={16} className="text-brand-gold" /> {t("yourTime")}
          <span className="font-normal text-muted-foreground">
            · {t("startsAt", { time: formatTime(start, locale) })}
          </span>
        </p>

        <Button variant="soft" size="sm" className="gap-1.5" onClick={onTell}>
          <Sparkles size={14} /> {t("tellPlanner")}
        </Button>
      </div>

      <ul className="grid grid-cols-7 gap-2" aria-label={t("yourTime")}>
        {weekday_minutes.map((minutes, i) => (
          <li key={i} className="min-w-0 text-center">
            <div className="flex h-12 items-end justify-center">
              <div
                className={cn(
                  "w-full max-w-8 rounded-t-lg",
                  minutes > 0 ? "bg-brand-gold" : "bg-muted"
                )}
                style={{ height: `${Math.max((minutes / max) * 100, 8)}%` }}
                aria-hidden
              />
            </div>
            <p className="mt-1 text-[11px] font-medium">{weekdays[i]}</p>
            <p className="truncate text-[11px] text-muted-foreground">
              {minutes > 0 ? formatDuration(minutes, tUnit) : t("off")}
            </p>
          </li>
        ))}
      </ul>

      {blocked_dates.length > 0 && (
        <p className="text-xs text-muted-foreground">
          {t("blocked", {
            dates: blocked_dates
              .slice(0, 6)
              .map((d) => shortDate(parseDate(d), locale))
              .join(", ") + (blocked_dates.length > 6 ? ` +${blocked_dates.length - 6}` : ""),
          })}
        </p>
      )}

      {active && (
        <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl bg-brand-gold/10 px-4 py-3 text-sm">
          <p className="min-w-0 break-words">
            <span className="font-medium">{t("youTold")}</span> {note}
          </p>
          <Button variant="ghost" size="sm" className="gap-1.5" disabled={resetting} onClick={onReset}>
            <RotateCcw size={13} /> {t("reset")}
          </Button>
        </div>
      )}
    </Card>
  );
}
