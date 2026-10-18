"use client";

import { useState } from "react";
import Link from "next/link";
import { Clock, FolderKanban } from "lucide-react";

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
}

type Filter = "all" | "todo" | "completed";

const tabs: { key: Filter; label: string }[] = [
  { key: "all", label: "All" },
  { key: "todo", label: "To Do" },
  { key: "completed", label: "Completed" },
];

export default function ProjectsClient({ projects }: { projects: Project[] }) {
  const [filter, setFilter] = useState<Filter>("all");

  if (projects.length === 0) {
    return (
      <div className="mx-auto flex max-w-lg flex-col items-center py-20 text-center">
        <span className="flex size-16 items-center justify-center rounded-full bg-brand-violet/10">
          <FolderKanban className="size-7 text-brand-violet" />
        </span>
        <h1 className="font-heading mt-6 text-2xl font-bold">No projects yet</h1>
        <p className="mt-2 text-muted-foreground">
          Hands-on projects from your roadmaps will show up here. Choose
          &ldquo;Reading + Videos + Projects&rdquo; as your learning style to
          get more of them.
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
      <h1 className="font-heading text-3xl font-bold">Projects</h1>
      <p className="mt-1 text-muted-foreground">
        Build real-world projects and showcase your skills.
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
            <span className="ml-1.5 opacity-70">{count(key)}</span>
          </button>
        ))}
      </div>

      <div className="mt-5 grid gap-4 sm:grid-cols-2">
        {visible.map((p) => (
          <Link key={p.id} href={p.href}>
            <Card className="h-full gap-3 px-6 transition hover:border-brand-violet/40 hover:shadow-md">
              <div className="flex items-start justify-between gap-3">
                <span className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-brand-violet/10 text-brand-violet">
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
                  {p.completed ? "Completed" : "Not started"}
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
              <div className="mt-auto flex items-center justify-between text-xs text-muted-foreground">
                <span className="truncate">{p.context}</span>
                {p.minutes != null && (
                  <span className="ml-3 flex shrink-0 items-center gap-1">
                    <Clock size={12} /> {p.minutes} min
                  </span>
                )}
              </div>
            </Card>
          </Link>
        ))}
        {visible.length === 0 && (
          <p className="col-span-full py-10 text-center text-sm text-muted-foreground">
            Nothing here yet.
          </p>
        )}
      </div>
    </div>
  );
}
