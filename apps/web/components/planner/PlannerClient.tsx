"use client";

import { useState } from "react";
import Link from "next/link";
import { useLocale, useTranslations } from "next-intl";
import { toast } from "sonner";
import {
  CalendarDays,
  ChevronLeft,
  ChevronRight,
  Sparkles,
  TriangleAlert,
  X,
} from "lucide-react";

import {
  moveLesson,
  optimiseSchedule,
  resetSchedulePreferences,
  unpinLesson,
} from "@/lib/api/calendar";
import {
  monthName,
  addDays,
  dateKey,
  parseDate,
  shortDate,
  startOfWeek,
} from "@/lib/planner";
import { apiErrorMessage } from "@/lib/profile-options";
import { CalendarSchedule, PlannedLesson } from "@/types/api";

import EmptyState from "@/components/shared/EmptyState";
import FilterChips from "@/components/shared/FilterChips";
import PageHeader from "@/components/shared/PageHeader";
import { Button, buttonVariants } from "@/components/ui/button";

import AvailabilityStrip from "./AvailabilityStrip";
import DayView from "./DayView";
import FeedCard from "./FeedCard";
import MonthView from "./MonthView";
import MoveDialog from "./MoveDialog";
import OptimiseDialog from "./OptimiseDialog";
import WeekView from "./WeekView";

type View = "day" | "week" | "month";

interface Props {
  initial: CalendarSchedule | null;
  initialToken: string | null;
  apiUrl: string;
}

export default function PlannerClient({ initial, initialToken, apiUrl }: Props) {
  const t = useTranslations("planner");
  const locale = useLocale();

  const [schedule, setSchedule] = useState<CalendarSchedule | null>(initial);
  const [view, setView] = useState<View>("week");
  // Start on the week with the next lessons, so a weekend visit isn't an empty grid.
  const [cursor, setCursor] = useState(() => {
    const today = initial?.today ?? dateKey(new Date());
    const weekEnd = dateKey(addDays(startOfWeek(parseDate(today)), 6));
    const hasThisWeek = initial?.days.some((d) => d.date >= today && d.date <= weekEnd);
    const next = initial?.days.find((d) => d.date > today);

    return parseDate(!hasThisWeek && next ? next.date : today);
  });
  const [moving, setMoving] = useState<{ lesson: PlannedLesson; date: string } | null>(null);
  const [optimiseOpen, setOptimiseOpen] = useState(false);
  const [resetting, setResetting] = useState(false);
  const [summary, setSummary] = useState<string | null>(null);

  if (!schedule) {
    return (
      <div className="mx-auto max-w-5xl">
        <PageHeader title={t("title")} subtitle={t("subtitle")} />
        <EmptyState
          icon={CalendarDays}
          title={t("loadFailed")}
          text={t("loadFailedText")}
        />
      </div>
    );
  }

  const today = parseDate(schedule.today);
  const todayKey = schedule.today;

  const missed = schedule.days.flatMap((d) =>
    d.units.filter((u) => u.missed).map((u) => ({ lesson: u, date: d.date }))
  );

  function show(next: CalendarSchedule, message?: string) {
    setSchedule(next);

    if (message) toast.success(message);
  }

  async function doMove(lessonId: string, date: string) {
    try {
      show(await moveLesson(lessonId, date), t("moved", { date: shortDate(parseDate(date), locale) }));
      setMoving(null);
    } catch (err) {
      toast.error(apiErrorMessage(err, t("moveFailed")));
      throw err;
    }
  }

  async function doUnpin(lessonId: string) {
    try {
      show(await unpinLesson(lessonId), t("unpinned"));
      setMoving(null);
    } catch (err) {
      toast.error(apiErrorMessage(err, t("moveFailed")));
      throw err;
    }
  }

  // Dropping a lesson on the day it is already on does nothing.
  function onDropLesson(lessonId: string, date: string) {
    const from = schedule!.days.find((d) => d.units.some((u) => u.id === lessonId));

    if (!from || from.date === date) return;

    doMove(lessonId, date).catch(() => {});
  }

  async function doOptimise(request: string) {
    const result = await optimiseSchedule(request);

    setSchedule(result);
    setSummary(result.summary ?? null);
  }

  async function doReset() {
    setResetting(true);

    try {
      show(await resetSchedulePreferences(), t("resetDone"));
      setSummary(null);
    } catch (err) {
      toast.error(apiErrorMessage(err, t("moveFailed")));
    } finally {
      setResetting(false);
    }
  }

  // ---- navigation -----------------------------------------------------------------------------

  function step(direction: -1 | 1) {
    if (view === "week") setCursor(addDays(cursor, 7 * direction));
    else if (view === "day") setCursor(addDays(cursor, direction));
    else setCursor(new Date(cursor.getFullYear(), cursor.getMonth() + direction, 1));
  }

  function rangeLabel() {
    if (view === "month") return `${monthName(cursor.getMonth(), locale)} ${cursor.getFullYear()}`;

    if (view === "day") return `${shortDate(cursor, locale)} ${cursor.getFullYear()}`;

    const start = startOfWeek(cursor);

    return t("rangeDates", { start: shortDate(start, locale), end: shortDate(addDays(start, 6), locale) });
  }

  function openDay(date: Date) {
    setCursor(date);
    setView("day");
  }

  const hasPlan = schedule.roadmap_id !== null;
  const nothingLeft = hasPlan && schedule.days.length === 0 && schedule.unscheduled === 0;

  return (
    <div className="mx-auto max-w-6xl space-y-5">
      <PageHeader
        title={t("title")}
        subtitle={t("subtitle")}
        actions={
          hasPlan && (
            <Button className="gap-2" onClick={() => setOptimiseOpen(true)}>
              <Sparkles size={16} /> {t("optimise.open")}
            </Button>
          )
        }
      />

      {!hasPlan ? (
        <EmptyState
          icon={CalendarDays}
          title={t("noPlan")}
          text={t("noPlanText")}
          action={
            <Link href="/roadmaps" className={buttonVariants()}>
              {t("goRoadmaps")}
            </Link>
          }
        />
      ) : (
        <>
          {summary && (
            <div
              role="status"
              className="flex items-start justify-between gap-3 rounded-2xl border border-brand-gold/40 bg-brand-gold/10 px-4 py-3 text-sm"
            >
              <p className="flex min-w-0 gap-2">
                <Sparkles size={16} className="mt-0.5 shrink-0 text-brand-gold" />
                <span className="break-words">{summary}</span>
              </p>
              <button
                type="button"
                aria-label={t("dismiss")}
                onClick={() => setSummary(null)}
                className="shrink-0 rounded-full p-1 text-muted-foreground hover:bg-muted"
              >
                <X size={14} />
              </button>
            </div>
          )}

          {missed.length > 0 && (
            <div
              role="alert"
              className="rounded-2xl border border-destructive/40 bg-destructive/10 px-4 py-3 text-sm"
            >
              <p className="flex items-center gap-2 font-medium text-destructive">
                <TriangleAlert size={16} /> {t("missedTitle", { count: missed.length })}
              </p>
              <ul className="mt-2 space-y-1.5">
                {missed.map(({ lesson, date }) => (
                  <li key={lesson.id} className="flex flex-wrap items-center justify-between gap-2">
                    <span className="min-w-0 break-words">
                      {lesson.title}{" "}
                      <span className="text-muted-foreground">({shortDate(parseDate(date), locale)})</span>
                    </span>
                    <Button size="sm" variant="outline" onClick={() => setMoving({ lesson, date })}>
                      {t("reschedule")}
                    </Button>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {schedule.unscheduled > 0 && (
            <p className="rounded-2xl border border-border bg-muted/40 px-4 py-3 text-sm">
              {t("unscheduled", { count: schedule.unscheduled })}
            </p>
          )}

          <AvailabilityStrip
            schedule={schedule}
            onTell={() => setOptimiseOpen(true)}
            onReset={doReset}
            resetting={resetting}
          />

          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-1">
              <Button variant="outline" size="icon" aria-label={t("previous")} onClick={() => step(-1)}>
                <ChevronLeft size={16} className="rtl:rotate-180" />
              </Button>
              <Button variant="outline" size="icon" aria-label={t("next")} onClick={() => step(1)}>
                <ChevronRight size={16} className="rtl:rotate-180" />
              </Button>
              <Button variant="soft" size="sm" className="ms-1" onClick={() => setCursor(today)}>
                {t("today")}
              </Button>
              <p className="ms-3 text-sm font-semibold sm:text-base" aria-live="polite">
                {rangeLabel()}
              </p>
            </div>

            <FilterChips
              label={t("view")}
              variant="segmented"
              size="sm"
              value={view}
              onChange={setView}
              options={[
                { value: "day", label: t("views.day") },
                { value: "week", label: t("views.week") },
                { value: "month", label: t("views.month") },
              ]}
            />
          </div>

          {nothingLeft ? (
            <EmptyState icon={CalendarDays} title={t("allDone")} text={t("allDoneText")} />
          ) : view === "week" ? (
            <WeekView
              schedule={schedule}
              weekStart={startOfWeek(cursor)}
              onMove={(lesson, date) => setMoving({ lesson, date })}
              onDropLesson={onDropLesson}
              onOpenDay={openDay}
            />
          ) : view === "month" ? (
            <MonthView
              schedule={schedule}
              month={cursor}
              onMove={(lesson, date) => setMoving({ lesson, date })}
              onDropLesson={onDropLesson}
              onOpenDay={openDay}
            />
          ) : (
            <DayView
              schedule={schedule}
              day={cursor}
              onMove={(lesson, date) => setMoving({ lesson, date })}
              onDropLesson={onDropLesson}
            />
          )}

          <p className="text-xs text-muted-foreground">{t("dragHint")}</p>
        </>
      )}

      <FeedCard initialToken={initialToken} apiUrl={apiUrl} />

      <MoveDialog
        key={moving?.lesson.id ?? "none"}
        lesson={moving?.lesson ?? null}
        today={todayKey}
        currentDate={moving?.date ?? null}
        onClose={() => setMoving(null)}
        onMove={doMove}
        onUnpin={doUnpin}
      />

      <OptimiseDialog
        key={schedule.preferences.note ?? "new"}
        open={optimiseOpen}
        onOpenChange={setOptimiseOpen}
        initial={schedule.preferences.note ?? ""}
        onSubmit={doOptimise}
      />
    </div>
  );
}
