"use client";

import { useState } from "react";
import PageHeader from "@/components/shared/PageHeader";
import FilterChips from "@/components/shared/FilterChips";
import Link from "next/link";
import { useTranslations } from "next-intl";
import { Clock, FolderKanban } from "lucide-react";

import Pill from "@/components/shared/Pill";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";

export interface Project {
  id: string;
  title: string;
  description: string | null;
  minutes: number | null;
  completed: boolean;
  context: string;
  href: string;
  difficulty?: "beginner" | "intermediate" | "advanced" | null;
  skills?: string[];
  portfolioValue?: string | null;
}

type Filter = "all" | "todo" | "completed";

const tabs: Filter[] = ["all", "todo", "completed"];

export default function ProjectsClient({ projects }: { projects: Project[] }) {
  const t = useTranslations("projects");
  const tFilters = useTranslations("filters");
  const tLevel = useTranslations("options.skill_level");
  const tUnit = useTranslations("unit");
  const [filter, setFilter] = useState<Filter>("all");

  if (projects.length === 0) {
    return (
      <div className="mx-auto flex max-w-lg flex-col items-center py-20 text-center">
        <span className="flex size-16 items-center justify-center rounded-full bg-brand-violet/10">
          <FolderKanban className="size-7 text-brand-violet" />
        </span>
        <h1 className="font-heading mt-6 text-2xl font-bold">{t("emptyTitle")}</h1>
        <p className="mt-2 text-muted-foreground">
          {t("emptyText")}
        </p>
      </div>
    );
  }

  const count = (f: Filter) =>
    projects.filter((p) =>
      f === "all" ? true : f === "todo" ? !p.completed : p.completed
    ).length;

  const visible = projects.filter((p) =>
    filter === "all" ? true : filter === "todo" ? !p.completed : p.completed
  );

  return (
    <div className="mx-auto max-w-5xl">
      <PageHeader title={t("title")} subtitle={t("subtitle")} />

      <FilterChips
        className="mt-6"
        label={tFilters("status")}
        value={filter}
        onChange={setFilter}
        options={tabs.map((key) => ({ value: key, label: tFilters(key), count: count(key) }))}
      />

      <div className="mt-5 grid gap-4 sm:grid-cols-2">
        {visible.map((p) => (
          <Link key={p.id} href={p.href}>
            <Card className="card-lift h-full gap-3 px-6">
              <div className="flex items-start justify-between gap-3">
                <span className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-brand-gold/15 text-brand-gold-deep dark:text-brand-gold">
                  <FolderKanban size={18} />
                </span>
                <span
                  className={cn(
                    "rounded-full px-3 py-1 text-xs font-medium",
                    p.completed
                      ? "bg-emerald-500/15 text-emerald-500"
                      : "bg-muted text-muted-foreground"
                  )}
                >
                  {p.completed ? t("completed") : t("notStarted")}
                </span>
              </div>
              <div>
                <h3 className="font-semibold">{p.title}</h3>
                {p.description && (
                  <p className="mt-1 line-clamp-2 text-sm text-muted-foreground">
                    {p.description}
                  </p>
                )}
              </div>
              {(p.difficulty || (p.skills && p.skills.length > 0)) && (
                <div className="flex flex-wrap gap-1.5">
                  {p.difficulty && (
                    <Pill tone="soft">{tLevel(p.difficulty)}</Pill>
                  )}
                  {p.skills?.slice(0, 3).map((skill) => (
                    <Pill key={skill}>{skill}</Pill>
                  ))}
                </div>
              )}
              {p.portfolioValue && (
                <p className="line-clamp-2 text-xs text-muted-foreground">
                  <span className="font-medium text-foreground">{t("why")}</span>
                  {p.portfolioValue}
                </p>
              )}
              <div className="mt-auto flex items-center justify-between text-xs text-muted-foreground">
                <span className="truncate">{p.context}</span>
                {p.minutes != null && (
                  <span className="ms-3 flex shrink-0 items-center gap-1">
                    <Clock size={12} /> {tUnit("min", { count: p.minutes })}
                  </span>
                )}
              </div>
            </Card>
          </Link>
        ))}
        {visible.length === 0 && (
          <p className="col-span-full py-10 text-center text-sm text-muted-foreground">
            {tFilters("nothing")}
          </p>
        )}
      </div>
    </div>
  );
}
