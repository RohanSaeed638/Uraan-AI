"use client";

import { useEffect, useState } from "react";
import { useTranslations } from "next-intl";

import { listRoadmapVersions } from "@/lib/api/roadmap-actions";
import { formatDate } from "@/lib/format";
import { apiErrorMessage } from "@/lib/profile-options";
import { RoadmapVersion } from "@/types/roadmap";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

interface Props {
  roadmapId: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onRestore: (version: RoadmapVersion) => Promise<void>;
}

export default function VersionsDialog({
  roadmapId,
  open,
  onOpenChange,
  onRestore,
}: Props) {
  const t = useTranslations("roadmapEngine.versions");

  const [versions, setVersions] = useState<RoadmapVersion[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [restoring, setRestoring] = useState<string | null>(null);
  const [confirming, setConfirming] = useState<string | null>(null);

  useEffect(() => {
    if (!open) return;

    let cancelled = false;

    listRoadmapVersions(roadmapId)
      .then((list) => {
        if (!cancelled) {
          setVersions(list);
          setError(null);
        }
      })
      .catch((err) => {
        if (!cancelled) setError(apiErrorMessage(err, t("loadFailed")));
      });

    return () => {
      cancelled = true;
    };
  }, [open, roadmapId, t]);

  async function restore(version: RoadmapVersion) {
    setRestoring(version.id);
    setError(null);

    try {
      await onRestore(version);
      onOpenChange(false);
    } catch (err) {
      setError(apiErrorMessage(err, t("restoreFailed")));
    } finally {
      setRestoring(null);
      setConfirming(null);
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>{t("title")}</DialogTitle>
          <DialogDescription>{t("description")}</DialogDescription>
        </DialogHeader>

        {error && (
          <p role="alert" className="text-sm text-destructive">
            {error}
          </p>
        )}

        {versions === null && !error && (
          <p className="text-sm text-muted-foreground">{t("loading")}</p>
        )}

        {versions?.length === 0 && (
          <p className="text-sm text-muted-foreground">{t("empty")}</p>
        )}

        <ul className="space-y-3">
          {versions?.map((v) => (
            <li key={v.id} className="rounded-2xl border p-4">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="min-w-0">
                  <p className="font-medium">
                    {t("version", { number: v.version_number })}
                    <span className="ms-2 text-xs font-normal text-muted-foreground">
                      {t(`reason.${v.reason}`)}
                    </span>
                  </p>
                  <p className="mt-0.5 text-xs text-muted-foreground">
                    {formatDate(v.created_at)} ·{" "}
                    {t("summary", {
                      phases: v.phases,
                      tasks: v.tasks,
                      done: v.completed,
                    })}
                  </p>
                </div>

                {confirming === v.id ? (
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      disabled={restoring !== null}
                      onClick={() => restore(v)}
                    >
                      {restoring === v.id ? t("restoring") : t("confirm")}
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      disabled={restoring !== null}
                      onClick={() => setConfirming(null)}
                    >
                      {t("cancel")}
                    </Button>
                  </div>
                ) : (
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={restoring !== null}
                    onClick={() => setConfirming(v.id)}
                  >
                    {t("restore")}
                  </Button>
                )}
              </div>
            </li>
          ))}
        </ul>

        <p className="text-xs text-muted-foreground">{t("note")}</p>
      </DialogContent>
    </Dialog>
  );
}
