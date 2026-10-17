"use client";

import { useState } from "react";
import Link from "next/link";
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

const tabs: { key: Filter; label: string }[] = [
  { key: "all", label: "All" },
  { key: "todo", label: "To Do" },
  { key: "completed", label: "Completed" },
];

export default function TasksClient({
  initialTasks,
}: {
  initialTasks: FlatTask[];
}) {
  const [tasks, setTasks] = useState(initialTasks);
  const [filter, setFilter] = useState<Filter>("all");
  const [pendingId, setPendingId] = useState<string | null>(null);

  const counts: Record<Filter, number> = {
    all: tasks.length,
    todo: tasks.filter((t) => !t.completed).length,
    completed: tasks.filter((t) => t.completed).length,
  };

  const visible = tasks.filter((t) =>
    filter === "all" ? true : filter === "todo" ? !t.completed : t.completed
  );

  async function toggle(taskId: string, completed: boolean) {
    if (pendingId) return;

    const previous = tasks;
    setPendingId(taskId);
    setTasks((current) =>
      current.map((t) => (t.id === taskId ? { ...t, completed } : t))
    );

    try {
      await api.patch(`/roadmaps/tasks/${taskId}`, { completed });
    } catch {
      setTasks(previous);
      toast.error("Couldn't update the task. Please try again.");
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
        <h1 className="font-heading mt-6 text-2xl font-bold">No tasks yet</h1>
        <p className="mt-2 text-muted-foreground">
          Tasks appear here once you&apos;ve generated a roadmap.
        </p>
        <Link
          href="/roadmaps"
          className={buttonVariants({ size: "lg", className: "mt-7" })}
        >
          Go to My Roadmaps
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl">
      <h1 className="font-heading text-3xl font-bold">Tasks</h1>
      <p className="mt-1 text-muted-foreground">
        Every task across your roadmaps, in one place.
      </p>

      <div className="mt-6 flex gap-2">
        {tabs.map(({ key, label }) => (
          <button
            key={key}
            onClick={() => setFilter(key)}
            className={cn(
              "rounded-full px-4 py-1.5 text-sm font-medium transition",
              filter === key
                ? "bg-brand-violet text-white"
                : "bg-muted text-muted-foreground hover:text-foreground"
            )}
          >
            {label}
            <span className="ml-1.5 opacity-70">{counts[key]}</span>
          </button>
        ))}
      </div>

      <Card className="mt-5 gap-0 p-0">
        {visible.length === 0 ? (
          <p className="p-8 text-center text-sm text-muted-foreground">
            Nothing here yet.
          </p>
        ) : (
          visible.map((task) => (
            <div
              key={task.id}
              className="flex items-center gap-4 border-b border-border px-5 py-4 last:border-b-0"
            >
              <Checkbox
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
                  <Clock size={13} /> {task.estimatedHours}h
                </span>
              )}
            </div>
          ))
        )}
      </Card>
    </div>
  );
}
