"use client";

import { Clock, ExternalLink, Loader2 } from "lucide-react";

import { Checkbox } from "@/components/ui/checkbox";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

import { RoadmapTask } from "@/types/roadmap";

interface TaskCardProps {
  task: RoadmapTask;
  loading?: boolean;
  onToggle: (taskId: string, completed: boolean) => void;
  onOpen: (task: RoadmapTask) => void;
}

export function TaskCard({
  task,
  loading = false,
  onToggle,
  onOpen,
}: TaskCardProps) {
  const resourceLink = task.resource_links?.[0];

  return (
    <Card
      onClick={() => onOpen(task)}
      className={cn(
        "cursor-pointer p-0 transition-all hover:border-brand-violet/40 hover:shadow-sm",
        task.completed && "opacity-60"
      )}
    >
      <CardContent className="flex gap-4 p-5">
        <div className="pt-1" onClick={(event) => event.stopPropagation()}>
          {loading ? (
            <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
          ) : (
            <Checkbox
              checked={task.completed}
              disabled={loading}
              onCheckedChange={(checked) => {
                onToggle(task.id, checked === true);
              }}
            />
          )}
        </div>

        <div className="min-w-0 flex-1 space-y-2">
          <div className="flex items-start justify-between gap-4">
            <h4
              className={cn(
                "font-medium transition-all",
                task.completed && "text-muted-foreground line-through"
              )}
            >
              {task.title}
            </h4>

            {task.estimated_hours != null && (
              <div className="flex shrink-0 items-center gap-1 whitespace-nowrap text-xs text-muted-foreground">
                <Clock className="h-3.5 w-3.5" />
                {task.estimated_hours}h
              </div>
            )}
          </div>

          {task.description && (
            <p className="line-clamp-2 text-sm leading-6 text-muted-foreground">
              {task.description}
            </p>
          )}

          {resourceLink && (
            <a
              href={resourceLink}
              target="_blank"
              rel="noopener noreferrer"
              onClick={(event) => event.stopPropagation()}
              className="inline-flex items-center gap-1 text-sm font-medium text-brand-violet hover:underline"
            >
              Open resource
              <ExternalLink className="h-3 w-3" />
            </a>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
