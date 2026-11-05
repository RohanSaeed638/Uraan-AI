"use client";

import { useState } from "react";
import PageHeader from "@/components/shared/PageHeader";
import FilterChips from "@/components/shared/FilterChips";
import Link from "next/link";
import { useTranslations } from "next-intl";
import { toast } from "sonner";
import { CheckSquare, Clock } from "lucide-react";

import { api } from "@/lib/api/client";
import { Checkbox } from "@/components/ui/checkbox";
import { Card } from "@/components/ui/card";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export interface FlatTask {
  id: string;
  title: string;
  completed: boolean;
  estimatedHours: number;
  roadmapId: string;
  roadmapTitle: string;
  phaseTitle: string;
}

type Filter = "all" | "todo" | "completed";

const tabs: Filter[] = ["all", "todo", "completed"];

export default function TasksClient({
  initialTasks,
}: {
  initialTasks: FlatTask[];
}) {
  const t = useTranslations("tasks");
  const tFilters = useTranslations("filters");
  const [tasks, setTasks] = useState(initialTasks);
  const [filter, setFilter] = useState<Filter>("all");
  const [pendingId, setPendingId] = useState<string | null>(null);

  const counts: Record<Filter, number> = {
    all: tasks.length,
    todo: tasks.filter((task) => !task.completed).length,
    completed: tasks.filter((task) => task.completed).length,
  };

  const visible = tasks.filter((task) =>
    filter === "all" ? true : filter === "todo" ? !task.completed : task.completed
  );

  async function toggle(taskId: string, completed: boolean) {
    if (pendingId) return;

    const previous = tasks;
    setPendingId(taskId);
    setTasks((current) =>
      current.map((task) => (task.id === taskId ? { ...task, completed } : task))
    );

    try {
      await api.patch(`/roadmaps/tasks/${taskId}`, { completed });
    } catch {
      setTasks(previous);
      toast.error(t("failed"));
    } finally {
      setPendingId(null);
    }
  }

  if (tasks.length === 0) {
    return (
      <div className="mx-auto flex max-w-lg flex-col items-center py-20 text-center">
        <span className="flex size-16 items-center justify-center rounded-full bg-brand-violet/10">
          <CheckSquare className="size-7 text-brand-violet" />
        </span>
        <h1 className="font-heading mt-6 text-2xl font-bold">{t("emptyTitle")}</h1>
        <p className="mt-2 text-muted-foreground">
          {t("emptyText")}
        </p>
        <Link
          href="/roadmaps"
          className={buttonVariants({ size: "lg", className: "mt-7" })}
        >
          {t("goRoadmaps")}
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl">
      <PageHeader title={t("title")} subtitle={t("subtitle")} />

      <FilterChips
        className="mt-6"
        label={tFilters("status")}
        value={filter}
        onChange={setFilter}
        options={tabs.map((key) => ({ value: key, label: tFilters(key), count: counts[key] }))}
      />

      <Card className="mt-5 gap-0 p-0">
        {visible.length === 0 ? (
          <p className="p-8 text-center text-sm text-muted-foreground">
            {tFilters("nothing")}
          </p>
        ) : (
          visible.map((task) => (
            <div
              key={task.id}
              className="flex items-center gap-4 border-b border-border px-5 py-4 last:border-b-0"
            >
              <Checkbox
                aria-label={task.title}
                checked={task.completed}
                disabled={pendingId === task.id}
                onCheckedChange={(checked) => toggle(task.id, checked === true)}
              />

              <Link
                href={`/roadmaps/${task.roadmapId}/task/${task.id}`}
                className="min-w-0 flex-1"
              >
                <p
                  className={cn(
                    "truncate font-medium",
                    task.completed && "text-muted-foreground line-through"
                  )}
                >
                  {task.title}
                </p>
                <p className="mt-0.5 truncate text-xs text-muted-foreground">
                  {task.roadmapTitle} · {task.phaseTitle}
                </p>
              </Link>

              {task.estimatedHours != null && (
                <span className="flex shrink-0 items-center gap-1 text-xs text-muted-foreground">
                  <Clock size={13} /> {t("hours", { count: task.estimatedHours })}
                </span>
              )}
            </div>
          ))
        )}
      </Card>
    </div>
  );
}
