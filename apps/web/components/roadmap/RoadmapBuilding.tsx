"use client";

import { CircleCheck, Loader2 } from "lucide-react";
import { useTranslations } from "next-intl";
import { useEffect, useState } from "react";

import Illustration from "@/components/illustrations/Illustration";
import { cn } from "@/lib/utils";

const STEPS = ["s1", "s2", "s3", "s4", "s5"] as const;
const SECONDS_PER_STEP = 7;

/**
 * What a learner sees while their roadmap is written (about half a minute). The steps tick over on a
 * timer, so it feels alive; the real work finishes whenever it finishes, and the last step keeps
 * going until then. Used by onboarding and by the "generate roadmap" dialog.
 */
export default function RoadmapBuilding({ compact = false, title }: { compact?: boolean; title?: string }) {
  const t = useTranslations("onboarding.generating");
  const [done, setDone] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => setDone((n) => Math.min(n + 1, STEPS.length - 1)), SECONDS_PER_STEP * 1000);

    return () => clearInterval(timer);
  }, []);

  const percent = Math.round(((done + 0.5) / STEPS.length) * 100);

  return (
    <div
      role="status"
      aria-live="polite"
      className={cn("flex flex-col items-center text-center", compact ? "py-2" : "min-h-[70vh] justify-center")}
    >
      <Illustration name="ob-plan" size={compact ? 150 : 220} className="float" priority />

      <h1 className={cn("font-heading font-bold", compact ? "mt-3 text-xl" : "mt-6 text-3xl")}>
        {title ?? t("title")}
      </h1>

      <p className="mt-2 max-w-md text-sm text-muted-foreground sm:text-base">{t("text")}</p>

      <div className="mt-7 w-full max-w-md text-start">
        <div className="mb-5 h-2.5 overflow-hidden rounded-full bg-muted">
          <div
            className="h-full rounded-full bg-brand-gradient transition-[width] duration-1000 ease-out"
            style={{ width: `${percent}%` }}
          />
        </div>

        <ul className="space-y-3 text-sm">
          {STEPS.map((key, index) => {
            const finished = index < done;
            const current = index === done;

            return (
              <li
                key={key}
                className={cn(
                  "flex items-center gap-3 transition-opacity duration-500",
                  finished || current ? "opacity-100" : "opacity-40"
                )}
              >
                {finished ? (
                  <CircleCheck size={18} className="shrink-0 text-emerald-500" aria-hidden />
                ) : current ? (
                  <Loader2 size={18} className="shrink-0 animate-spin text-brand-violet" aria-hidden />
                ) : (
                  <span className="size-[18px] shrink-0 rounded-full border-2 border-border" aria-hidden />
                )}
                <span className={cn(current ? "font-medium text-foreground" : "text-muted-foreground")}>
                  {t(key)}
                </span>
              </li>
            );
          })}
        </ul>

        <p className="mt-6 text-center text-xs text-muted-foreground">{t("wait")}</p>
      </div>
    </div>
  );
}
