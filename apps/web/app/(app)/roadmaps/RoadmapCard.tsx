"use client";

import Link from "next/link";
import { useLocale, useTranslations } from "next-intl";
import { Clock, ArrowRight } from "lucide-react";

import { RoadmapSummary } from "@/types/roadmap";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

import { Progress } from "@/components/ui/progress";
import { buttonVariants } from "@/components/ui/button";
import { formatDate } from "@/lib/format";

interface Props {
  roadmap: RoadmapSummary;
}

const statusStyles: Record<string, string> = {
  active: "bg-emerald-500/15 text-emerald-500",
  completed: "bg-brand-violet/15 text-violet-700 dark:text-brand-violet-light",
  paused: "bg-amber-500/15 text-amber-500",
  generating: "bg-sky-500/15 text-sky-500",
  failed: "bg-destructive/15 text-destructive",
};

export default function RoadmapCard({ roadmap }: Props) {
  const t = useTranslations("roadmaps.card");
  const tStatus = useTranslations("status");
  const locale = useLocale();

  return (
    <Card className="card-lift">
      <CardHeader>
        <div className="flex items-start justify-between gap-3">
          <CardTitle className="line-clamp-2 min-w-0">{roadmap.title}</CardTitle>
          <span
            className={`shrink-0 rounded-full px-3 py-1 text-xs font-medium ${
              statusStyles[roadmap.status] ?? "bg-muted text-muted-foreground"
            }`}
          >
            {tStatus(roadmap.status)}
          </span>
        </div>
      </CardHeader>

      <CardContent className="space-y-5">
        <p className="line-clamp-2 text-sm text-muted-foreground">
          {roadmap.description}
        </p>

        <Progress value={roadmap.progress} />

        <div className="flex justify-between text-sm text-muted-foreground">
          <span>
            {t("tasks", { done: roadmap.completed_tasks, total: roadmap.total_tasks })}
          </span>
          <span>{roadmap.progress}%</span>
        </div>

        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Clock size={14} />
            {t("updated", { date: formatDate(roadmap.updated_at, undefined, locale) })}
          </div>

          <Link
            href={`/roadmaps/${roadmap.id}`}
            className={buttonVariants({ className: "gap-1.5" })}
          >
            {t("continue")} <ArrowRight size={15} className="rtl:rotate-180" />
          </Link>
        </div>
      </CardContent>
    </Card>
  );
}
