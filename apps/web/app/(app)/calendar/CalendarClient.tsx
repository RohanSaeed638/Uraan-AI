"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { CalendarDays, ChevronLeft, ChevronRight, Copy, RefreshCw } from "lucide-react";
import { toast } from "sonner";

import { api } from "@/lib/api";
import { CalendarSchedule } from "@/types/api";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

const WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

/** Parses a YYYY-MM-DD string as a local date (no timezone shift). */
function parseDate(value: string) {
  const [y, m, d] = value.split("-").map(Number);
  return new Date(y, m - 1, d);
}

function key(date: Date) {
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  return `${date.getFullYear()}-${m}-${d}`;
}

export default function CalendarClient({
  schedule,
  initialToken,
  apiUrl,
}: {
  schedule: CalendarSchedule | null;
  initialToken: string | null;
  apiUrl: string;
}) {
  const today = schedule ? parseDate(schedule.today) : new Date();
  const [cursor, setCursor] = useState(
    new Date(today.getFullYear(), today.getMonth(), 1)
  );
  const [token, setToken] = useState(initialToken);
  const [busy, setBusy] = useState(false);

  const days = useMemo(() => schedule?.days ?? [], [schedule]);
  const byDate = useMemo(
    () => new Map(days.map((d) => [d.date, d])),
    [days]
  );

  const feedUrl = token ? `${apiUrl}/calendar/feed/${token}.ics` : null;

  // Monday-first month grid.
  const first = cursor;
  const offset = (first.getDay() + 6) % 7;
  const daysInMonth = new Date(
    first.getFullYear(),
    first.getMonth() + 1,
    0
  ).getDate();
  const cells = [
    ...Array.from({ length: offset }, () => null),
    ...Array.from(
      { length: daysInMonth },
      (_, i) => new Date(first.getFullYear(), first.getMonth(), i + 1)
    ),
  ];

  async function copy() {
    if (!feedUrl) return;
    try {
      await navigator.clipboard.writeText(feedUrl);
      toast.success("Calendar link copied.");
    } catch {
      toast.error("Couldn't copy. Select the link and copy it manually.");
    }
  }

  async function regenerate() {
    if (
      !window.confirm(
        "Create a new link? Calendars using the old link will stop updating."
      )
    ) {
      return;
    }
    setBusy(true);
    try {
      const { data } = await api.post<{ token: string }>(
        "/calendar/subscription/regenerate"
      );
      setToken(data.token);
      toast.success("New calendar link created.");
    } catch {
      toast.error("Couldn't create a new link.");
    } finally {
      setBusy(false);
    }
  }

  const upcoming = days.slice(0, 14);

  return (
    <div className="mx-auto max-w-5xl">
      <h1 className="font-heading text-3xl font-bold">Calendar</h1>
      <p className="mt-1 text-muted-foreground">
        Your remaining study days, one per day starting today. Fall behind and
        the plan shifts forward.
      </p>

      {days.length === 0 ? (
        <div className="mx-auto mt-16 flex max-w-sm flex-col items-center text-center">
          <span className="flex size-16 items-center justify-center rounded-full bg-brand-violet/10">
            <CalendarDays className="size-7 text-brand-violet" />
          </span>
          <h2 className="font-heading mt-5 text-xl font-bold">
            Nothing scheduled
          </h2>
          <p className="mt-2 text-sm text-muted-foreground">
            Open a task in your roadmap to generate its daily lessons and they
            will appear here.
          </p>
        </div>
      ) : (
        <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-[minmax(0,1fr)_320px]">
          <Card className="p-5">
            <div className="flex items-center justify-between">
              <p className="font-semibold">
                {cursor.toLocaleDateString("en-US", {
                  month: "long",
                  year: "numeric",
                })}
              </p>
              <div className="flex gap-1">
                <Button
                  size="icon"
                  variant="ghost"
                  aria-label="Previous month"
                  onClick={() =>
                    setCursor(
                      new Date(cursor.getFullYear(), cursor.getMonth() - 1, 1)
                    )
                  }
                >
                  <ChevronLeft size={16} />
                </Button>
                <Button
                  size="icon"
                  variant="ghost"
                  aria-label="Next month"
                  onClick={() =>
                    setCursor(
                      new Date(cursor.getFullYear(), cursor.getMonth() + 1, 1)
                    )
                  }
                >
                  <ChevronRight size={16} />
                </Button>
              </div>
            </div>

            <div className="mt-4 grid grid-cols-7 gap-1 text-center text-xs text-muted-foreground">
              {WEEKDAYS.map((d) => (
                <span key={d}>{d}</span>
              ))}
            </div>
            <div className="mt-1 grid grid-cols-7 gap-1">
              {cells.map((date, i) => {
                if (!date) return <span key={`blank-${i}`} />;
                const entry = byDate.get(key(date));
                const isToday = key(date) === key(today);

                return (
                  <div
                    key={key(date)}
                    className={cn(
                      "flex aspect-square flex-col items-center justify-center rounded-xl text-sm",
                      entry && "bg-brand-violet/10 font-semibold text-brand-violet",
                      isToday && "ring-2 ring-brand-gold"
                    )}
                    title={entry ? entry.units[0].task_title : undefined}
                  >
                    {date.getDate()}
                    {entry && (
                      <span className="mt-0.5 size-1 rounded-full bg-brand-violet" />
                    )}
                  </div>
                );
              })}
            </div>
          </Card>

          <Card className="gap-3 p-5">
            <p className="font-semibold">Subscribe</p>
            <p className="text-xs text-muted-foreground">
              Add this link to Google Calendar, Apple Calendar or Outlook as a
              subscribed calendar. It updates itself and uses your reminder
              time from Settings.
            </p>
            {feedUrl ? (
              <>
                <Input readOnly value={feedUrl} className="text-xs" />
                <div className="flex gap-2">
                  <Button size="sm" className="gap-2" onClick={copy}>
                    <Copy size={14} /> Copy link
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    className="gap-2"
                    disabled={busy}
                    onClick={regenerate}
                  >
                    <RefreshCw size={14} /> New link
                  </Button>
                </div>
              </>
            ) : (
              <p className="text-sm text-muted-foreground">
                Couldn&apos;t load your calendar link. Refresh the page.
              </p>
            )}
            <p className="text-[11px] text-muted-foreground">
              Anyone with the link can see your study plan. Create a new link
              to revoke it.
            </p>
          </Card>

          <Card className="gap-0 p-0 lg:col-span-2">
            <p className="border-b px-5 py-3 font-semibold">Next study days</p>
            {upcoming.map((d) => {
              const date = parseDate(d.date);
              return (
                <div
                  key={d.date}
                  className="flex items-start gap-4 border-b px-5 py-3.5 last:border-b-0"
                >
                  <div className="w-14 shrink-0 text-center">
                    <p className="text-xs uppercase text-muted-foreground">
                      {date.toLocaleDateString("en-US", { weekday: "short" })}
                    </p>
                    <p className="text-lg font-bold leading-tight">
                      {date.getDate()}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {date.toLocaleDateString("en-US", { month: "short" })}
                    </p>
                  </div>
                  <div className="min-w-0 flex-1">
                    <Link
                      href={`/roadmaps/${schedule?.roadmap_id}/task/${d.units[0].task_id}`}
                      className="block truncate font-medium hover:text-brand-violet"
                    >
                      {d.units[0].task_title}
                    </Link>
                    <ul className="mt-1 space-y-0.5 text-xs text-muted-foreground">
                      {d.units.map((u) => (
                        <li key={u.id} className={cn(u.completed && "line-through")}>
                          {u.title}
                          {u.estimated_minutes ? ` · ${u.estimated_minutes} min` : ""}
                        </li>
                      ))}
                    </ul>
                  </div>
                  <span className="shrink-0 text-xs text-muted-foreground">
                    {d.total_estimated_minutes} min
                  </span>
                </div>
              );
            })}
          </Card>
        </div>
      )}
    </div>
  );
}
