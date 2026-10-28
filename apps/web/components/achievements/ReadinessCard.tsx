"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { ArrowRight } from "lucide-react";

import { getReadiness, ReadinessKey } from "@/lib/api/achievements";

import ProgressRing from "@/components/shared/ProgressRing";
import { Card } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";

/** The 0 to 100 career readiness score, what makes it up, and what to do next.
 * `compact` is the dashboard version: ring, level and the top tips. */
export default function ReadinessCard({ compact = false }: { compact?: boolean }) {
  const t = useTranslations("readiness");

  const query = useQuery({
    queryKey: ["readiness"],
    queryFn: getReadiness,
    staleTime: 60_000,
    retry: false,
  });

  if (query.isError) return null;

  if (!query.data) {
    return <Card className="min-h-40 animate-pulse p-6" aria-busy />;
  }

  const { score, level, components, tips } = query.data;
  const shownTips = compact ? tips.slice(0, 2) : tips;

  return (
    <Card className="gap-5 p-6">
      <div className="flex items-center gap-5">
        <div className="relative shrink-0">
          <ProgressRing value={score} size={compact ? 92 : 112} showValue={false} />
          <span
            className="absolute inset-0 flex items-center justify-center font-heading text-xl font-bold"
            aria-hidden
          >
            {score}
          </span>
        </div>

        <div className="min-w-0">
          <p className="text-xs font-semibold uppercase tracking-wide text-brand-gold">
            {t("title")}
          </p>
          <p className="font-heading text-xl font-bold">
            {t("scoreOf", { score })}
          </p>
          <p className="text-sm text-muted-foreground">{t(`levels.${level}`)}</p>
        </div>
      </div>

      {!compact && (
        <ul className="space-y-3">
          {components.map((c) => (
            <li key={c.key}>
              <div className="flex items-center justify-between text-sm">
                <span>{t(`parts.${c.key}`)}</span>
                <span className="text-muted-foreground">
                  {t("points", { points: c.points, weight: c.weight })}
                </span>
              </div>
              <Progress value={Math.round(c.value * 100)} className="mt-1.5 h-1.5" />
            </li>
          ))}
        </ul>
      )}

      {shownTips.length > 0 && (
        <div>
          <p className="text-sm font-semibold">{t("nextSteps")}</p>
          <ul className="mt-2 space-y-2">
            {shownTips.map((tip) => (
              <li key={tip.key}>
                <Link
                  href={tip.href}
                  className="group flex items-center justify-between gap-3 rounded-2xl border px-4 py-2.5 text-sm transition hover:bg-muted"
                >
                  <span className="min-w-0 break-words">
                    {t(`tips.${tip.action}`, { count: tip.count })}
                  </span>
                  <ArrowRight
                    size={14}
                    className="rtl:rotate-180 shrink-0 text-muted-foreground transition group-hover:translate-x-0.5"
                  />
                </Link>
              </li>
            ))}
          </ul>
        </div>
      )}

      {tips.length === 0 && (
        <p className="text-sm text-muted-foreground">{t("allDone")}</p>
      )}
    </Card>
  );
}

export type { ReadinessKey };
