import { intlLocale } from "@/lib/format";
import { formatMinutes } from "@/lib/units";
import { CalendarDay, CalendarSchedule } from "@/types/api";

/** The Intl locale for the app language. Dates here read day-month, as in the English planner. */
function dateLocale(locale: string) {
  return locale === "en" ? "en-GB" : intlLocale(locale);
}

// A Monday and a January in UTC: names come from Intl, so every language is covered.
const MONDAY = Date.UTC(2024, 0, 1);

/** Monday-first weekday names ("Mon" or "Monday"). */
export function weekdayNames(locale: string, style: "short" | "long" = "short"): string[] {
  const format = new Intl.DateTimeFormat(dateLocale(locale), { weekday: style, timeZone: "UTC" });

  return Array.from({ length: 7 }, (_, i) => format.format(MONDAY + i * 86_400_000));
}

export function monthName(month: number, locale: string, style: "short" | "long" = "long"): string {
  return new Intl.DateTimeFormat(dateLocale(locale), { month: style, timeZone: "UTC" }).format(
    Date.UTC(2024, month, 1)
  );
}

/** "2026-11-03" as a local date (no timezone shift). */
export function parseDate(value: string): Date {
  const [y, m, d] = value.split("-").map(Number);

  return new Date(y, m - 1, d);
}

export function dateKey(date: Date): string {
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");

  return `${date.getFullYear()}-${m}-${d}`;
}

export function addDays(date: Date, days: number): Date {
  const next = new Date(date);
  next.setDate(next.getDate() + days);

  return next;
}

/** Monday of the week that contains `date`. */
export function startOfWeek(date: Date): Date {
  return addDays(new Date(date.getFullYear(), date.getMonth(), date.getDate()), -((date.getDay() + 6) % 7));
}

/** Index 0-6, Monday first. */
export function weekdayIndex(date: Date): number {
  return (date.getDay() + 6) % 7;
}

/** "19:00:00" -> "7:00 PM" */
export function formatTime(value: string, locale: string): string {
  const [h, m] = value.split(":").map(Number);

  // 12-hour clock for every language (en-GB would print 19:00).
  const time = new Intl.DateTimeFormat(locale === "ur" ? "ur" : "en-US", {
    hour: "numeric",
    minute: "2-digit",
    timeZone: "UTC",
  }).format(Date.UTC(2024, 0, 1, h, m));

  // Inside right-to-left text the clock would read "AM 9:00": keep it as one left-to-right piece.
  return locale === "ur" ? `\u2066${time}\u2069` : time;
}

/** "Fri, 7 Nov" */
export function shortDate(date: Date, locale: string): string {
  return new Intl.DateTimeFormat(dateLocale(locale), {
    weekday: "short",
    day: "numeric",
    month: "short",
    timeZone: "UTC",
  }).format(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()));
}

/** 90 -> "1h 30m", 30 -> "30m". `t` is the `unit` translator. */
export function formatDuration(minutes: number, t: Parameters<typeof formatMinutes>[1]): string {
  return formatMinutes(minutes, t);
}

export type DayStatus = "planned" | "free" | "rest" | "blocked";

/** Why a day has nothing on it: nothing left to place, a day the learner has
 * no study time on, or a day they blocked. */
export function dayStatus(
  date: Date,
  schedule: CalendarSchedule,
  planned: CalendarDay | undefined
): DayStatus {
  if (planned) return "planned";
  if (schedule.availability.blocked_dates.includes(dateKey(date))) return "blocked";
  if (schedule.availability.weekday_minutes[weekdayIndex(date)] === 0) return "rest";

  return "free";
}
