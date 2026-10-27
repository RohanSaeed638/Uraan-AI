"use client";

import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { Clock, ExternalLink, BookOpen, ArrowRight } from "lucide-react";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

import { Button } from "@/components/ui/button";

import { RoadmapTask } from "@/types/roadmap";

interface TaskDetailsDialogProps {
  roadmapId: string;
  task: RoadmapTask | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onToggle: (taskId: string, completed: boolean) => void;
}

export default function TaskDetailsDialog({
  roadmapId,
  task,
  open,
  onOpenChange,
}: TaskDetailsDialogProps) {
  const router = useRouter();
  const t = useTranslations("roadmaps.tasks");

  if (!task) {
    return null;
  }

  const hasResources = task.resource_links && task.resource_links.length > 0;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>{task.title}</DialogTitle>
          <DialogDescription>
            {t("dialogText")}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {task.description && (
            <div>
              <h3 className="mb-2 text-sm font-semibold">
                {t("whatToDo")}
              </h3>
              <p className="text-sm leading-6 text-muted-foreground">
                {task.description}
              </p>
            </div>
          )}

          {task.estimated_hours != null && (
            <div className="flex items-center gap-3 rounded-2xl bg-muted/60 p-4">
              <span className="flex size-9 items-center justify-center rounded-xl bg-brand-gold/15">
                <Clock className="h-4 w-4 text-brand-gold" />
              </span>
              <div>
                <p className="text-sm font-medium">{t("estimated")}</p>
                <p className="text-sm text-muted-foreground">
                  {t("hours", { count: task.estimated_hours })}
                </p>
              </div>
            </div>
          )}

          {hasResources && (
            <div>
              <div className="mb-3 flex items-center gap-2">
                <BookOpen className="h-4 w-4 text-brand-violet" />
                <h3 className="text-sm font-semibold">{t("resources")}</h3>
              </div>

              <div className="space-y-2">
                {task.resource_links!.map((url, index) => (
                  <a
                    key={`${url}-${index}`}
                    href={url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center justify-between gap-3 rounded-xl border border-border p-3 text-sm transition-colors hover:bg-muted"
                  >
                    <span className="min-w-0 truncate text-brand-violet">
                      {t("resource", { number: index + 1 })}
                    </span>
                    <ExternalLink className="h-4 w-4 shrink-0 text-muted-foreground" />
                  </a>
                ))}
              </div>
            </div>
          )}

          {!hasResources && (
            <div className="rounded-xl border border-dashed border-border p-4">
              <p className="text-sm text-muted-foreground">
                {t("noResources")}
              </p>
            </div>
          )}

          <div className="border-t border-border pt-5">
            <Button
              className="flex w-full items-center gap-2"
              onClick={() => {
                onOpenChange(false);
                router.push(`/roadmaps/${roadmapId}/task/${task.id}`);
              }}
            >
              {t("start")} <ArrowRight size={15} className="rtl:rotate-180" />
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
