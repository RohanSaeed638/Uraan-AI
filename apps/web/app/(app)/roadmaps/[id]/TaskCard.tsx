import { Checkbox } from "@/components/ui/checkbox";
import { Card, CardContent } from "@/components/ui/card";
import { Clock, ExternalLink } from "lucide-react";

import { RoadmapTask } from "@/types/roadmap";
import { api } from "@/lib/api/client";
import { useState } from "react";

interface TaskCardProps {
  task: RoadmapTask;
  loading?: boolean;
  onToggle: (taskId: string, completed: boolean) => void;
}

export function TaskCard({
  task,
  loading = false,
  onToggle
}: TaskCardProps) {
    
  return (
    <Card className="transition-colors hover:border-primary/50">
      <CardContent className="flex gap-4 p-4">
        <Checkbox
          checked={task.completed}
          disabled={loading}
          onCheckedChange={(checked) => {
            onToggle(task.id, checked === true);
          }}
          className="mt-1"
        />

        <div className="flex-1 space-y-2">
          <div className="flex items-start justify-between gap-4">
            <h4
              className={`font-medium ${
                task.completed
                  ? "line-through text-muted-foreground"
                  : ""
              }`}
            >
              {task.title}
            </h4>

            {task.estimated_hours && (
              <div className="flex items-center gap-1 text-sm text-muted-foreground whitespace-nowrap">
                <Clock className="h-4 w-4" />
                {task.estimated_hours} hrs
              </div>
            )}
          </div>

          {task.description && (
            <p className="text-sm text-muted-foreground">
              {task.description}
            </p>
          )}

          {task.resource_url && (
            <a
              href={task.resource_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-sm text-primary hover:underline"
            >
              Resource
              <ExternalLink className="h-3 w-3" />
            </a>
          )}
        </div>
      </CardContent>
    </Card>
  );
}