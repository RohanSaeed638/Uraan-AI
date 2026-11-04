import { ArrowRight, BookOpen, Clock } from "lucide-react";
import Link from "next/link";
import { getTranslations } from "next-intl/server";

import ProgressRing from "@/components/shared/ProgressRing";
import { buttonVariants } from "@/components/ui/button";

interface Props {
  roadmap: { id: string; title: string; completed_tasks: number; total_tasks: number; completion_percentage: number };
  next: {
    roadmap_id: string;
    task_id: string;
    learning_unit_id: string;
    task_title: string;
    learning_unit_title: string;
    estimated_minutes: number | null;
  } | null;
}

/** The one thing to do next, as large as it deserves: the next lesson and a single big button. */
export default async function ContinueHero({ roadmap, next }: Props) {
  const t = await getTranslations("dashboard");

  const href = next
    ? `/roadmaps/${next.roadmap_id}/task/${next.task_id}/learn/${next.learning_unit_id}`
    : `/roadmaps/${roadmap.id}`;

  return (
    <section
      aria-label={t("heroEyebrow")}
      className="relative isolate overflow-hidden rounded-4xl bg-gradient-to-br from-violet-700 via-violet-600 to-indigo-800 p-7 text-white shadow-xl shadow-violet-900/25 sm:p-9"
    >
      <div
        aria-hidden
        className="absolute inset-0 -z-10 [background-image:radial-gradient(circle,rgba(255,255,255,0.20)_1px,transparent_1.6px)] [background-size:22px_22px] [mask-image:radial-gradient(ellipse_70%_90%_at_85%_20%,black,transparent)]"
      />
      <div aria-hidden className="absolute -end-20 -top-24 -z-10 size-72 rounded-full bg-amber-300/30 blur-3xl" />
      <div aria-hidden className="absolute -bottom-28 start-10 -z-10 size-72 rounded-full bg-fuchsia-400/25 blur-3xl" />

      <div className="flex flex-col gap-8 sm:flex-row sm:items-center sm:justify-between">
        <div className="min-w-0">
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-violet-200">{t("heroEyebrow")}</p>

          <h2 className="font-heading mt-3 text-2xl font-bold leading-snug sm:text-3xl">
            {next ? next.learning_unit_title : roadmap.title}
          </h2>

          <p className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-violet-100">
            <span className="inline-flex items-center gap-1.5">
              <BookOpen size={14} aria-hidden />
              {next ? next.task_title : t("heroNoNext")}
            </span>
            {next?.estimated_minutes ? (
              <span className="inline-flex items-center gap-1.5">
                <Clock size={14} aria-hidden />
                {t("minutes", { count: next.estimated_minutes })}
              </span>
            ) : null}
          </p>

          <p className="mt-1 truncate text-sm text-violet-200/80">{roadmap.title}</p>

          <Link
            href={href}
            className={buttonVariants({
              size: "lg",
              className:
                "mt-7 h-12 gap-2 bg-white px-7 text-base text-violet-800 shadow-lg shadow-violet-950/20 transition hover:-translate-y-0.5 hover:bg-violet-50",
            })}
          >
            {next ? t("continue") : t("openRoadmap")} <ArrowRight size={16} className="rtl:rotate-180" aria-hidden />
          </Link>
        </div>

        <div className="flex shrink-0 flex-col items-center gap-2">
          <ProgressRing value={Math.round(roadmap.completion_percentage)} size={124} strokeWidth={9} tone="onDark" />
          <p className="num text-xs text-violet-100">
            {t("tasksOf", { done: roadmap.completed_tasks, total: roadmap.total_tasks })}
          </p>
        </div>
      </div>
    </section>
  );
}
