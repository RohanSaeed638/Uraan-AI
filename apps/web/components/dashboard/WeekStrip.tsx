import { Check, Flame, Zap } from "lucide-react";
import { getLocale, getTranslations } from "next-intl/server";

import { Card } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { cn } from "@/lib/utils";
import { weekdayNames } from "@/lib/planner";
import type { Gamification } from "@/types/api";

interface Props {
  /** Days with learning done, from the activity endpoint (UTC dates, "YYYY-MM-DD"). */
  activeDates: string[];
  gamification: Gamification | null;
  /** Today in UTC, "YYYY-MM-DD". */
  today: string;
}

const DAY = 86_400_000;

/** Monday to Sunday of this week: which days had learning, today ringed, and the streak and level below. */
export default async function WeekStrip({ activeDates, gamification, today }: Props) {
  const t = await getTranslations("dashboard");
  const locale = await getLocale();
  const names = weekdayNames(locale, "short");

  const todayMs = Date.parse(`${today}T00:00:00Z`);
  const mondayMs = todayMs - ((new Date(todayMs).getUTCDay() + 6) % 7) * DAY;
  const active = new Set(activeDates);

  const days = Array.from({ length: 7 }, (_, i) => {
    const key = new Date(mondayMs + i * DAY).toISOString().slice(0, 10);

    return { key, name: names[i], done: active.has(key), isToday: key === today, future: key > today };
  });
  const activeCount = days.filter((d) => d.done).length;

  return (
    <Card className="justify-between gap-5 p-6">
      <div className="flex items-baseline justify-between gap-3">
        <p className="font-heading text-base font-semibold">{t("thisWeek")}</p>
        <p className="num text-xs text-muted-foreground">{t("activeDays", { count: activeCount })}</p>
      </div>

      <ol className="grid grid-cols-7 gap-1.5" aria-label={t("thisWeek")}>
        {days.map((d) => (
          <li key={d.key} className="flex flex-col items-center gap-2">
            <span
              className={cn(
                "flex size-9 items-center justify-center rounded-full text-xs transition",
                d.done
                  ? "bg-gradient-to-br from-violet-500 to-indigo-600 text-white shadow-md shadow-violet-500/30"
                  : d.isToday
                    ? "border-2 border-brand-violet text-violet-700 dark:text-brand-violet-light"
                    : d.future
                      ? "border border-dashed border-border text-transparent"
                      : "bg-muted text-muted-foreground"
              )}
            >
              {d.done && <Check size={15} strokeWidth={3} aria-hidden />}
              <span className="sr-only">
                {d.name}: {d.done ? t("dayDone") : d.isToday ? t("today") : d.future ? "" : t("dayMissed")}
              </span>
            </span>
            <span className={cn("text-[11px]", d.isToday ? "font-semibold text-foreground" : "text-muted-foreground")}>
              {d.name}
            </span>
          </li>
        ))}
      </ol>

      {gamification && (
        <div className="space-y-4 border-t border-border pt-4">
          <div className="flex items-center justify-between gap-3">
            <p className="flex items-center gap-2 text-sm font-medium">
              <span className="flex size-8 items-center justify-center rounded-lg bg-brand-gold/15">
                <Flame size={16} className="text-brand-gold" aria-hidden />
              </span>
              <span>
                <span className="num text-base font-bold">{gamification.streak_days}</span>{" "}
                <span className="text-muted-foreground">{t("streak")}</span>
              </span>
            </p>
            <p className="num text-xs text-muted-foreground">{t("weekXp", { xp: gamification.weekly_xp })}</p>
          </div>

          <div>
            <div className="mb-1.5 flex items-center justify-between text-xs">
              <span className="flex items-center gap-1.5 font-medium">
                <Zap size={13} className="text-violet-600 dark:text-brand-violet-light" aria-hidden />
                {t("level", { level: gamification.level })}
              </span>
              <span className="num text-muted-foreground">
                {gamification.xp_into_level}/{gamification.xp_per_level} XP
              </span>
            </div>
            <Progress
              value={Math.round((gamification.xp_into_level / gamification.xp_per_level) * 100)}
              className="h-1.5"
            />
          </div>
        </div>
      )}
    </Card>
  );
}
