"use client";

import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { Clock, ArrowRight } from "lucide-react";

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
              <span className="flex size-9 items-center justify-center rounded-xl bg-brand-violet/15">
                <Clock className="h-4 w-4 text-violet-600 dark:text-brand-violet-light" />
              </span>
              <div>
                <p className="text-sm font-medium">{t("estimated")}</p>
                <p className="text-sm text-muted-foreground">
                  {t("hours", { count: task.estimated_hours })}
                </p>
              </div>
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
